"""Panel schedule, service-load summary, and backup components — derived, never hand-summed.

Circuits are authored (``Library.circuits``); everything here is a projection of them plus
the devices/equipment that reference them. Connected VA prefers the authored
``Circuit.load_va``; when unset it is summed from the referencing devices' typed
``ElectricalDeviceType.load_va`` — a circuit with neither reports 0 and the schedule shows
it, which is the honest state, not an estimate.
"""

from __future__ import annotations

import math

from typehaus.model.enums import BackupTier
from typehaus.quantities import M_PER_IN
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


_HEAT_PUMP_KINDS = frozenset({"heat_pump", "indoor_head", "ducted_air_handler"})


def _is_heat_pump(circuit, consumers: list) -> bool:
    """A circuit feeding the heat-pump system NEC 220.82(C)(2) takes at 100%.

    Typed, not name-matched: an ``Equipment`` of an HVAC kind on the circuit is the modeled
    answer. This used to look for "minisplit" in the description, which silently dropped the
    whole heating term to zero the day the units were renamed — and put them in the
    fixed-appliance bucket (B)(3), which (B) explicitly excludes heating loads from.
    """
    return any(
        element.element_kind == "Equipment"
        and getattr(getattr(element, "kind", None), "value", None) in _HEAT_PUMP_KINDS
        for element in consumers
    )


def _is_resistance_heat(circuit, consumers: list) -> bool:
    """Fixed electric space heating — the loads NEC 220.82(C) governs, not (B)(3).

    Typed first: an ``Equipment`` of kind ``space_heater`` on the circuit is the modeled
    answer. Radiant floor has no placeable to read (a ``FloorHeat`` zone carries no
    ``circuit``; its thermostat is a SWITCH like any other), so those fall back to the
    description — the one name-match left in this function, and the reason the heat-pump
    branch above no longer has one.
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
            "backup": circuit.backup_tier is not None,
            "backup_tier": circuit.backup_tier.value if circuit.backup_tier else "",
            "panel": circuit.panel_ref,
            "source": circuit.source,
            "connected_va": round(_connected_va(model, circuit, served), 0),
            "devices": sorted(element.tag for element in served),
        })
    return rows


# The service size, when the model states none. 200A is the ordinary residential service and
# the number this summary was hard-coded to before ``ElectricalDeviceType.service_amps``
# existed; it is now a *fallback*, and the summary says which of the two it used.
DEFAULT_SERVICE_AMPS = 200.0


def _bucket(model: ResolvedModel, circuit, consumers: list) -> str:
    """Which NEC 220.82 term a circuit's connected load lands in.

    Split out of ``service_load_summary`` so the load-management credit can be taken in the
    same bucket the load was counted in. Crediting an interlocked pair of appliances at 100%
    of their connected excess — which is what subtracting the credit straight off the demand
    did — overstates the saving by a factor of 2.5, because that excess only ever reached
    the demand through 220.82(B)'s 40% remainder factor.
    """
    if circuit.source:
        return "source"
    description = circuit.description.lower()
    if _is_heat_pump(circuit, consumers):
        return "heat_pump"
    if _is_resistance_heat(circuit, consumers):
        return "resistance_heat"
    if "ev charging" in description:
        return "ev"
    if ("lighting" in description or "general receptacles" in description
            or "small-appliance" in description or "laundry" in description):
        return "general"
    return "appliance"


def _service_amps(model: ResolvedModel) -> tuple[float, str]:
    """The service ampacity this house states, and where it came from.

    Authored on the service-entrance product — the meter socket or the main disconnect —
    because that is the piece of equipment whose rating *is* the service size. It used to be
    the literal ``200`` in the returned dict, which meant a house could not say it had a
    400A service and the 220.82 comparison silently graded every plan against 200A.
    """
    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    best: tuple[float, str] | None = None
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "ElectricalDevice":
                continue
            if getattr(element.kind, "value", None) not in ("meter", "panel"):
                continue
            product = types.get(getattr(element, "type_ref", "") or "")
            amps = getattr(product, "service_amps", None)
            if amps is None:
                continue
            # A meter socket is the service; a panel that states one is the main disconnect
            # behind it. Where both speak, the meter wins — and the smaller of two panels
            # never does, so the max is taken among panels only after the meter is missed.
            if getattr(element.kind, "value", None) == "meter":
                return float(amps), element.tag
            if best is None or float(amps) > best[0]:
                best = (float(amps), element.tag)
    if best is not None:
        return best
    return DEFAULT_SERVICE_AMPS, "default"


def load_management_credits(model: ResolvedModel) -> list[dict[str, object]]:
    """Per-``LoadManagement`` connected excess, resolved into the buckets it came from.

    A controller guarantees its group never draws more than ``max_simultaneous_va``
    together, so the group's connected excess over that ceiling never reaches the service.
    Where a group spans buckets the excess is removed from each circuit in proportion to its
    share of the group's connected load — exact for the homogeneous groups anyone actually
    builds (all EV, all resistance, all fixed appliance), and stated rather than hidden for
    the mixed case.
    """
    consumers = _circuit_consumers(model)
    circuits = {c.tag: c for c in model.plan.library.circuits}
    out: list[dict[str, object]] = []
    for management in model.plan.library.load_managements:
        missing = [tag for tag in management.managed_circuits if tag not in circuits]
        members = [circuits[tag] for tag in management.managed_circuits if tag in circuits]
        group_va = sum(_connected_va(model, c, consumers.get(c.tag, [])) for c in members)
        excess = max(0.0, group_va - management.max_simultaneous_va)
        by_bucket: dict[str, float] = {}
        if excess > 0 and group_va > 0:
            for circuit in members:
                va = _connected_va(model, circuit, consumers.get(circuit.tag, []))
                share = excess * (va / group_va)
                by_bucket[_bucket(model, circuit, consumers.get(circuit.tag, []))] = (
                    by_bucket.get(_bucket(model, circuit, consumers.get(circuit.tag, [])), 0.0)
                    + share)
        out.append({
            "tag": management.tag, "strategy": management.strategy,
            "managed_circuits": list(management.managed_circuits),
            "missing_circuits": missing,
            "group_va": group_va, "cap_va": management.max_simultaneous_va,
            "excess_va": excess, "by_bucket": by_bucket,
        })
    return out


def service_load_summary(model: ResolvedModel) -> dict[str, object]:
    """NEC 220.82-style optional-method estimate against the authored service and panel bus.

    Labeled an estimate on the sheet: general lighting from resolved conditioned floor
    area, fixed appliances from the authored circuits, EV already at its continuous
    rating (the device types carry 80% of breaker), PV excluded (a source, not a load).

    The heating/cooling term is 220.82(C)'s *selection*, not a sum: heat pumps at 100%
    (C)(2) against electric resistance space heating at 65%/40% (C)(4)/(5), largest wins.
    Adding them would be double-counting a house that cannot run both flat out — and
    would also mean a 1.5 kW bench heater in an unconditioned garage landing in the
    fixed-appliance bucket (B)(3), which (B) explicitly excludes heating loads from.

    Authored ``LoadManagement`` is applied here rather than by the caller, and in the bucket
    each managed circuit was counted in: an interlock over two fixed appliances saves 40% of
    its connected excess, not 100% of it, because that is the only rate at which the excess
    ever reached the demand.
    """
    floor_area_ft2 = sum(room.area_m2 for room in model.rooms if room.conditioned) * _M2_TO_FT2
    general_va = GENERAL_LIGHTING_VA_PER_FT2 * floor_area_ft2 + SMALL_APPLIANCE_AND_LAUNDRY_VA

    consumers = _circuit_consumers(model)
    connected: dict[str, float] = {}
    resistance_heat_units = 0
    for circuit in model.plan.library.circuits:
        bucket = _bucket(model, circuit, consumers.get(circuit.tag, []))
        if bucket in ("source", "general"):
            continue  # a source is not a load; general is the 3 VA/ft2 allowance above
        va = _connected_va(model, circuit, consumers.get(circuit.tag, []))
        connected[bucket] = connected.get(bucket, 0.0) + va
        if bucket == "resistance_heat":
            resistance_heat_units += 1

    credits = load_management_credits(model)
    managed: dict[str, float] = {}
    for credit in credits:
        for bucket, va in credit["by_bucket"].items():  # type: ignore[union-attr]
            managed[bucket] = managed.get(bucket, 0.0) + va

    def available(bucket: str) -> float:
        return max(0.0, connected.get(bucket, 0.0) - managed.get(bucket, 0.0))

    heat_pump_va = connected.get("heat_pump", 0.0)
    resistance_heat_va = connected.get("resistance_heat", 0.0)
    appliance_va = connected.get("appliance", 0.0)
    ev_va = connected.get("ev", 0.0)

    resistance_factor = (RESISTANCE_HEAT_FACTOR_MANY
                         if resistance_heat_units >= SEPARATELY_CONTROLLED_UNIT_THRESHOLD
                         else RESISTANCE_HEAT_FACTOR_FEW)

    def demand(managed_applied: bool) -> float:
        appliance = available("appliance") if managed_applied else appliance_va
        heat_pump = available("heat_pump") if managed_applied else heat_pump_va
        resistance = available("resistance_heat") if managed_applied else resistance_heat_va
        ev = available("ev") if managed_applied else ev_va
        base = general_va + appliance
        return (min(base, FIRST_10KVA)
                + max(base - FIRST_10KVA, 0.0) * REMAINDER_DEMAND_FACTOR
                + max(heat_pump, resistance * resistance_factor) + ev)

    unmanaged_demand_va = demand(False)
    demand_va = demand(True)
    service_amps, service_source = _service_amps(model)
    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    bus = [getattr(types.get(getattr(e, "type_ref", "") or ""), "bus_amps", None)
           for storey in model.plan.storeys
           for e in model.plan.storey_elements(storey.tag)
           if e.element_kind == "ElectricalDevice"
           and getattr(e.kind, "value", None) == "panel"]
    panel_rating = max([b for b in bus if b is not None], default=None)
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
        "hvac_va": round(max(heat_pump_va, resistance_heat_va * resistance_factor), 0),
        "ev_va": round(ev_va, 0),
        "unmanaged_demand_va": round(unmanaged_demand_va, 0),
        "load_management_credit_va": round(unmanaged_demand_va - demand_va, 0),
        "load_management": credits,
        "demand_va": round(demand_va, 0),
        "demand_amps": round(amps, 1),
        "service_amps": service_amps,
        "service_amps_source": service_source,
        "panel_rating_amps": panel_rating,
        "within_service": amps <= service_amps,
    }


def conduit_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of *power* raceway by EMT trade size — developed length (plan + riser).

    Data and spare raceways are billed by ``takeoff/data.py`` instead. Same pipe, different
    order: comms may not share a raceway with power (NEC 800.133/725), so the two are pulled
    by different trades on different days, and merging 40 ft of 3/4" power with 40 ft of 3/4"
    data into one 80 ft row would produce a line nobody can buy against.
    """
    groups: dict[float, dict[str, object]] = {}
    for run in model.conduits:
        if run.service in ("data", None):
            continue
        row = groups.setdefault(run.trade_size_m, {
            "trade_size_in": round(run.trade_size_m / M_PER_IN, 2),
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

    Only power raceways are counted. A data raceway carries no branch circuit, and a capped
    spare carries nothing at all — billing THHN against either would buy wire for pipe that
    will never hold it.
    """
    power_runs = [run for run in model.conduits if run.service not in ("data", None)]
    total_ft = sum(run.length_m * 3.280839895013123 for run in power_runs)
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
        pull_ft = total_ft / max(len(power_runs), 1) + _MAKEUP_ALLOWANCE_FT
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
    """The array as installed: module count, total DC watts, per-product and per-string.

    Watts are summed from the resolved panels (the authored ``SolarPanel.watts`` carried
    through resolve), never a hand-typed total; the mounting kits are billed by the
    hardware take-off like every other modeled connector.

    The per-string rollup carries both Voc sums. ``voc_cold_v`` is the one that sizes
    conductors and gates the 690.12 grouping — a string that sums under the rated Voc
    limit can still be over it on a January morning — and either sum is None when any
    module in the string doesn't declare that voltage, because a partial sum of a series
    string is not a smaller string, it is a wrong number.
    """
    by_string: dict[str, dict[str, object]] = {}
    for panel in model.solar_panels:
        row = by_string.setdefault(panel.string or "(unstrung)", {
            "string": panel.string, "panels": 0, "watts": 0.0,
            "voc_v": 0.0, "voc_cold_v": 0.0, "voc_known": True, "voc_cold_known": True,
            "rsd_modules": 0, "tags": []})
        row["panels"] = int(row["panels"]) + 1
        row["watts"] = float(row["watts"]) + panel.watts
        if panel.voc is None:
            row["voc_known"] = False
        else:
            row["voc_v"] = float(row["voc_v"]) + panel.voc
        if panel.voc_cold is None:
            row["voc_cold_known"] = False
        else:
            row["voc_cold_v"] = float(row["voc_cold_v"]) + panel.voc_cold
        if panel.rsd:
            row["rsd_modules"] = int(row["rsd_modules"]) + 1
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(panel.tag)

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
        "rsd_transmitters": sum(1 for panel in model.solar_panels if panel.rsd),
        "by_product": [
            {"product": row["product"], "panels": int(row["panels"]),
             "watts": round(float(row["watts"]), 0), "tags": sorted(row["tags"])}
            for row in (by_product[key] for key in sorted(by_product))
        ],
        "by_string": [
            {"string": row["string"], "panels": int(row["panels"]),
             "watts": round(float(row["watts"]), 0),
             "voc_v": round(float(row["voc_v"]), 1) if row["voc_known"] else None,
             "voc_cold_v": (round(float(row["voc_cold_v"]), 1)
                            if row["voc_cold_known"] else None),
             "rsd_modules": int(row["rsd_modules"]), "tags": sorted(row["tags"])}
            for row in (by_string[key] for key in sorted(by_string))
        ],
    }


def backup_equipment(model: ResolvedModel) -> dict[str, list]:
    """The placed pieces of the backup microgrid, by role: batteries, inverters, panels.

    One place to ask "is there an ESS here", so the takeoff, the autonomy calc and the
    R327 checks all agree on the answer instead of each re-scanning the storeys.
    """
    batteries, inverters = [], []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "Equipment":
                continue
            kind = getattr(getattr(element, "kind", None), "value", None)
            if kind == "battery":
                batteries.append(element)
            elif kind == "inverter":
                inverters.append(element)
    return {"batteries": batteries, "inverters": inverters}


def backup_component_rows(model: ResolvedModel) -> list[dict[str, object]]:
    """The backup microgrid's bill of components: the placed inverter and battery
    modules, the backup subpanel they feed, and the DIN gear that sheds the SHED tier.

    Derived twice over — the storage/inverter rows from placed ``Equipment`` (so a second
    battery module is a placement, not an edit here), the switching rows from the
    ``SHED``-tier circuits (so re-tiering a circuit re-counts the relays). The ALWAYS_ON
    tier deliberately contributes no switching hardware: that is what the tier *means*.
    Empty when nothing is placed and nothing is tiered.
    """
    circuits = model.plan.library.circuits
    shed = [c for c in circuits if c.backup_tier is BackupTier.SHED]
    always_on = [c for c in circuits if c.backup_tier is BackupTier.ALWAYS_ON]
    placed = backup_equipment(model)
    if not (shed or always_on or placed["batteries"] or placed["inverters"]):
        return []

    types = {t.tag: t for t in model.plan.library.equipment_types}
    device_types = {t.tag: t for t in model.plan.library.electrical_device_types}
    rows: list[dict[str, object]] = []

    for element in sorted(placed["inverters"], key=lambda e: e.tag):
        product = types.get(element.type_ref or "")
        kw = getattr(product, "inverter_kw_continuous", None) if product else None
        rows.append({
            "component": (product.name if product is not None else "hybrid inverter"),
            "count": 1,
            "basis": (f"{element.tag}"
                      + (f" — {kw:g} kW continuous AC" if kw else "")),
        })
    battery_kwh = 0.0
    for element in sorted(placed["batteries"], key=lambda e: e.tag):
        product = types.get(element.type_ref or "")
        kwh = getattr(product, "storage_kwh", None) if product else None
        battery_kwh += float(kwh or 0.0)
        rows.append({
            "component": (product.name if product is not None else "battery module"),
            "count": 1,
            "basis": (f"{element.tag}"
                      + (f" — {kwh:g} kWh" if kwh else " — capacity not declared")),
        })

    # The backup subpanel: whichever panel the tiered circuits are homed to, when that is
    # not the same panel the rest of the house is on.
    backup_panels = sorted({c.panel_ref for c in (*always_on, *shed)})
    main_panels = sorted({c.panel_ref for c in circuits if c.backup_tier is None})
    for panel_ref in backup_panels:
        if panel_ref in main_panels:
            continue
        spaces = getattr(device_types.get(_panel_type_ref(model, panel_ref) or ""),
                         "spaces", None)
        rows.append({
            "component": f"backup subpanel {panel_ref}", "count": 1,
            "basis": (f"{len(always_on) + len(shed)} backup circuits"
                      + (f", {spaces}-space enclosure" if spaces else "")),
        })

    if shed:
        relay_circuits = [c for c in shed
                          if c.breaker_amps <= RELAY_CHANNEL_AMPS and c.poles == 1]
        contactor_circuits = [c for c in shed
                              if c.breaker_amps > RELAY_CHANNEL_AMPS or c.poles == 2]
        if relay_circuits:
            rows.append({
                "component": "Shelly Pro 4PM 4-channel DIN relay",
                "count": math.ceil(len(relay_circuits) / BACKUP_CIRCUITS_PER_RELAY),
                "basis": (f"{len(relay_circuits)} shed-tier circuit"
                          f"{'s' if len(relay_circuits) != 1 else ''} "
                          f"({', '.join(c.tag for c in relay_circuits)}) at "
                          f"{BACKUP_CIRCUITS_PER_RELAY} channels per relay"),
            })
        if contactor_circuits:
            rows.append({
                "component": "DIN contactor (relay-driven)",
                "count": len(contactor_circuits),
                "basis": (f"shed-tier circuits over the {RELAY_CHANNEL_AMPS}A relay "
                          f"channel or 2-pole "
                          f"({', '.join(c.tag for c in contactor_circuits)})"),
            })
        # One relay channel drives however many contactors there are; a shed tier made
        # entirely of contactor circuits still needs the relay that commands them.
        if contactor_circuits and not relay_circuits:
            rows.append({
                "component": "Shelly Pro 4PM 4-channel DIN relay", "count": 1,
                "basis": "one relay to drive the shed-tier contactor coils",
            })

    rsd = sum(1 for panel in model.solar_panels if panel.rsd)
    if rsd:
        rows.append({
            "component": "SunSpec rapid-shutdown transmitter (module level)",
            "count": rsd,
            "basis": f"{rsd} modules carrying rsd=True (690.12; EG4 sends the keep-alive)",
        })

    rows.extend([
        {"component": "24V DIN-rail power supply", "count": 1,
         "basis": "one 24V bus for LED backup lighting + PoE (notes lines 13-15)"},
        {"component": "DIN-rail 24V UPS module", "count": 1,
         "basis": "backup light/network ride-through (notes line 14)"},
    ])
    return rows


def _panel_type_ref(model: ResolvedModel, panel_tag: str) -> str | None:
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind == "ElectricalDevice" and element.tag == panel_tag:
                return element.type_ref
    return None
