"""Panel schedule, service-load summary, and backup components — derived, never hand-summed.

Circuits are authored (``Library.circuits``); everything here is a projection of them plus
the devices/equipment that reference them. Connected VA prefers the authored
``Circuit.load_va``; when unset it is summed from the referencing devices' typed
``ElectricalDeviceType.load_va`` — a circuit with neither reports 0 and the schedule shows
it, which is the honest state, not an estimate.
"""

from __future__ import annotations

import math

from typehaus.resolve.model import ResolvedModel

_M2_TO_FT2 = 10.7639104167

# One Shelly Pro 4PM switches four circuits; the DIN rail carries one 24V PSU and one UPS
# regardless of relay count (electrical_notes.md lines 10-15).
BACKUP_CIRCUITS_PER_RELAY = 4
# A Pro 4PM channel is rated 16A at 120V — a backup circuit breakered above that, or any
# 2-pole one, switches through a relay-driven DIN contactor instead (notes line 10:
# "Smart Relays (Shelly Pro 4PM) and contactors").
RELAY_CHANNEL_AMPS = 16

# NEC 220.82 (optional method) constants for the service-load summary.
GENERAL_LIGHTING_VA_PER_FT2 = 3.0
SMALL_APPLIANCE_AND_LAUNDRY_VA = 4500.0  # 2 x 1500 small-appliance + 1500 laundry
FIRST_10KVA = 10000.0
REMAINDER_DEMAND_FACTOR = 0.4
# 220.82(C)(4)/(5): electric space heating is taken at 65% of nameplate when there are
# fewer than four separately controlled units, 40% at four or more.
SEPARATELY_CONTROLLED_UNIT_THRESHOLD = 4
RESISTANCE_HEAT_FACTOR_FEW = 0.65
RESISTANCE_HEAT_FACTOR_MANY = 0.40


def _circuit_consumers(model: ResolvedModel) -> dict[str, list]:
    by_circuit: dict[str, list] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            ref = getattr(element, "circuit", None)
            if ref:
                by_circuit.setdefault(ref, []).append(element)
    return by_circuit


def _connected_va(model: ResolvedModel, circuit, consumers: list) -> float:
    if circuit.load_va is not None:
        return float(circuit.load_va)
    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    return sum(
        float(types[element.type_ref].load_va or 0.0)
        for element in consumers
        if element.element_kind == "ElectricalDevice" and element.type_ref in types
    )


def _is_resistance_heat(circuit, consumers: list) -> bool:
    """Fixed electric space heating — the loads NEC 220.82(C) governs, not (B)(3).

    Typed first: an ``Equipment`` of kind ``space_heater`` on the circuit is the modeled
    answer. Radiant floor has no placeable to read (a ``FloorHeat`` zone carries no
    ``circuit``; its thermostat is a SWITCH like any other), so those fall back to the
    description, which is the same shape the ``minisplit`` branch already relies on.
    """
    for element in consumers:
        kind = getattr(element, "kind", None)
        if element.element_kind == "Equipment" and getattr(kind, "value", None) == "space_heater":
            return True
    return "radiant floor heat" in circuit.description.lower()


def panel_schedule(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per authored circuit: breaker, poles, NEMA, protection, load, consumers."""
    consumers = _circuit_consumers(model)
    rows = []
    for circuit in model.plan.library.circuits:
        served = consumers.get(circuit.tag, [])
        rows.append({
            "circuit": circuit.tag,
            "description": circuit.description,
            "breaker_amps": circuit.breaker_amps,
            "poles": circuit.poles,
            "volts": 240 if circuit.poles == 2 else 120,
            "nema": circuit.nema or "",
            "gfci": circuit.gfci,
            "backup": circuit.backup,
            "connected_va": round(_connected_va(model, circuit, served), 0),
            "devices": sorted(element.tag for element in served),
        })
    return rows


def service_load_summary(model: ResolvedModel) -> dict[str, object]:
    """NEC 220.82-style optional-method estimate against the 200A service / 225A panel.

    Labeled an estimate on the sheet: general lighting from resolved conditioned floor
    area, fixed appliances from the authored circuits, EV already at its continuous
    rating (the device types carry 80% of breaker), PV excluded (a source, not a load).

    The heating/cooling term is 220.82(C)'s *selection*, not a sum: heat pumps at 100%
    (C)(2) against electric resistance space heating at 65%/40% (C)(4)/(5), largest wins.
    Adding them would be double-counting a house that cannot run both flat out — and
    would also mean a 1.5 kW bench heater in an unconditioned garage landing in the
    fixed-appliance bucket (B)(3), which (B) explicitly excludes heating loads from.
    """
    floor_area_ft2 = sum(room.area_m2 for room in model.rooms if room.conditioned) * _M2_TO_FT2
    general_va = GENERAL_LIGHTING_VA_PER_FT2 * floor_area_ft2 + SMALL_APPLIANCE_AND_LAUNDRY_VA

    consumers = _circuit_consumers(model)
    heat_pump_va = 0.0
    resistance_heat_va = 0.0
    resistance_heat_units = 0
    ev_va = 0.0
    appliance_va = 0.0
    for circuit in model.plan.library.circuits:
        va = _connected_va(model, circuit, consumers.get(circuit.tag, []))
        description = circuit.description.lower()
        if "minisplit" in description:
            heat_pump_va += va  # 220.82(C)(2)
        elif _is_resistance_heat(circuit, consumers.get(circuit.tag, [])):
            resistance_heat_va += va
            resistance_heat_units += 1
        elif "ev charging" in description:
            ev_va += va  # already continuous (125% of plug load = 80% of breaker basis)
        elif "pv " in description or description.startswith("pv") or "backfeed" in description:
            continue  # a source, not a load
        elif ("lighting" in description or "general receptacles" in description
              or "small-appliance" in description or "laundry" in description):
            continue  # covered by the 3 VA/ft2 + 4500 VA general allowance above
        else:
            appliance_va += va

    resistance_factor = (RESISTANCE_HEAT_FACTOR_MANY
                         if resistance_heat_units >= SEPARATELY_CONTROLLED_UNIT_THRESHOLD
                         else RESISTANCE_HEAT_FACTOR_FEW)
    hvac_va = max(heat_pump_va, resistance_heat_va * resistance_factor)

    base = general_va + appliance_va
    demand_va = (min(base, FIRST_10KVA)
                 + max(base - FIRST_10KVA, 0.0) * REMAINDER_DEMAND_FACTOR
                 + hvac_va + ev_va)
    amps = demand_va / 240.0
    return {
        "method": "NEC 220.82 optional method (estimate)",
        "floor_area_ft2": round(floor_area_ft2, 0),
        "general_lighting_va": round(general_va, 0),
        "fixed_appliance_va": round(appliance_va, 0),
        "heat_pump_va": round(heat_pump_va, 0),
        "resistance_heat_va": round(resistance_heat_va, 0),
        "resistance_heat_units": resistance_heat_units,
        "resistance_heat_factor": resistance_factor,
        "hvac_va": round(hvac_va, 0),
        "ev_va": round(ev_va, 0),
        "demand_va": round(demand_va, 0),
        "demand_amps": round(amps, 1),
        "service_amps": 200,
        "panel_rating_amps": 225,
        "within_service": amps <= 200.0,
    }


def conduit_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of raceway by EMT trade size — developed length (plan + riser)."""
    groups: dict[float, dict[str, object]] = {}
    for run in model.conduits:
        row = groups.setdefault(run.trade_size_m, {
            "trade_size_in": round(run.trade_size_m * 39.37007874015748, 2),
            "runs": 0, "length_m": 0.0, "tags": []})
        row["runs"] = int(row["runs"]) + 1
        row["length_m"] = float(row["length_m"]) + run.length_m
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(run.tag)
    return [
        {"trade_size_in": row["trade_size_in"], "runs": int(row["runs"]),
         "length_ft": round(float(row["length_m"]) * 3.280839895013123, 1),
         "tags": sorted(row["tags"])}
        for row in (groups[key] for key in sorted(groups))
    ]


# Conductors per raceway, by circuit poles. A 1-pole branch pulls two current-carrying
# conductors plus a ground; a 2-pole pulls three plus a ground. Both are counted as
# individual conductors because that is how THHN is bought — by the foot, per colour.
_CONDUCTORS_PER_CIRCUIT = {1: 3, 2: 4}
# Pull length is the raceway's developed length plus an allowance at each end for making up
# in the panel and at the device. 10 ft is the conventional residential allowance.
_MAKEUP_ALLOWANCE_FT = 10.0


def conductor_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Conductor lineal feet — what ``conduit_takeoff`` deliberately does not bill.

    Raceway and wire are two different orders and ``conduit_takeoff`` covers only the first,
    so an estimate built on it buys the pipe and none of the wire. This is an *estimate* and
    says so: a conduit run carries no circuit assignment in the model, so it is priced as the
    total raceway length times the conductors a branch circuit of each pole count needs,
    rather than pulled circuit by circuit. The panel schedule is what says which circuits
    exist; the raceway is what says how far they run.
    """
    total_ft = sum(run.length_m * 3.280839895013123 for run in model.conduits)
    if total_ft <= 0.0:
        return []
    by_poles: dict[int, int] = {}
    for circuit in model.plan.library.circuits:
        by_poles[circuit.poles] = by_poles.get(circuit.poles, 0) + 1
    rows = []
    for poles in sorted(by_poles):
        circuits = by_poles[poles]
        per = _CONDUCTORS_PER_CIRCUIT.get(poles)
        if per is None:
            continue
        pull_ft = total_ft / max(len(model.conduits), 1) + _MAKEUP_ALLOWANCE_FT
        rows.append({
            "poles": poles,
            "circuits": circuits,
            "conductors_per_circuit": per,
            "mean_pull_ft": round(pull_ft, 1),
            "length_ft": round(pull_ft * per * circuits, 1),
            "basis": "estimate: mean raceway run + 10 ft make-up, per conductor",
        })
    return rows


def electrical_device_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Devices counted by kind + product type — what the electrician's order reads."""
    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    groups: dict[tuple[str, str], dict[str, object]] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "ElectricalDevice":
                continue
            product = types.get(element.type_ref or "")
            key = (element.kind.value, element.type_ref or "(untyped)")
            row = groups.setdefault(key, {
                "kind": element.kind.value, "type": element.type_ref or "(untyped)",
                "name": product.name if product is not None else "",
                "nema": (product.nema or "") if product is not None else "",
                "count": 0})
            row["count"] = int(row["count"]) + 1
    return [groups[key] for key in sorted(groups)]


def solar_takeoff(model: ResolvedModel) -> dict[str, object]:
    """The array as installed: module count, total DC watts, and per-product rollup.

    Watts are summed from the resolved panels (the authored ``SolarPanel.watts`` carried
    through resolve), never a hand-typed total; the mounting kits are billed by the
    hardware take-off like every other modeled connector.
    """
    by_product: dict[str, dict[str, object]] = {}
    for panel in model.solar_panels:
        row = by_product.setdefault(panel.product or "(unspecified module)", {
            "product": panel.product, "panels": 0, "watts": 0.0, "tags": []})
        row["panels"] = int(row["panels"]) + 1
        row["watts"] = float(row["watts"]) + panel.watts
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(panel.tag)
    return {
        "panels": len(model.solar_panels),
        "total_watts": round(sum(panel.watts for panel in model.solar_panels), 0),
        "by_product": [
            {"product": row["product"], "panels": int(row["panels"]),
             "watts": round(float(row["watts"]), 0), "tags": sorted(row["tags"])}
            for row in (by_product[key] for key in sorted(by_product))
        ],
    }


def backup_component_rows(model: ResolvedModel) -> list[dict[str, object]]:
    """DIN-rail components derived from the backup-flagged circuits: ceil(n/4) Shelly Pro
    4PM relays, one 24V PSU, one DIN UPS. Empty when nothing is flagged for backup."""
    backup = [circuit for circuit in model.plan.library.circuits if circuit.backup]
    if not backup:
        return []
    relays = math.ceil(len(backup) / BACKUP_CIRCUITS_PER_RELAY)
    basis = (f"{len(backup)} backup circuits ({', '.join(c.tag for c in backup)}) at "
             f"{BACKUP_CIRCUITS_PER_RELAY} channels per relay")
    contactor_circuits = [c for c in backup
                          if c.breaker_amps > RELAY_CHANNEL_AMPS or c.poles == 2]
    rows: list[dict[str, object]] = [
        {"component": "Shelly Pro 4PM 4-channel DIN relay", "count": relays, "basis": basis},
    ]
    if contactor_circuits:
        rows.append({
            "component": "DIN contactor (relay-driven)", "count": len(contactor_circuits),
            "basis": (f"backup circuits over the {RELAY_CHANNEL_AMPS}A relay channel or "
                      f"2-pole ({', '.join(c.tag for c in contactor_circuits)})"),
        })
    rows.extend([
        {"component": "24V DIN-rail power supply", "count": 1,
         "basis": "one 24V bus for LED backup lighting + PoE (notes lines 13-15)"},
        {"component": "DIN-rail 24V UPS module", "count": 1,
         "basis": "backup light/network ride-through (notes line 14)"},
    ])
    return rows
