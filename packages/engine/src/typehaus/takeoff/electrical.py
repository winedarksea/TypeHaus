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

# NEC 220.82 (optional method) constants for the service-load summary.
GENERAL_LIGHTING_VA_PER_FT2 = 3.0
SMALL_APPLIANCE_AND_LAUNDRY_VA = 4500.0  # 2 x 1500 small-appliance + 1500 laundry
FIRST_10KVA = 10000.0
REMAINDER_DEMAND_FACTOR = 0.4


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
    """
    floor_area_ft2 = sum(room.area_m2 for room in model.rooms if room.conditioned) * _M2_TO_FT2
    general_va = GENERAL_LIGHTING_VA_PER_FT2 * floor_area_ft2 + SMALL_APPLIANCE_AND_LAUNDRY_VA

    consumers = _circuit_consumers(model)
    hvac_va = 0.0
    ev_va = 0.0
    appliance_va = 0.0
    for circuit in model.plan.library.circuits:
        va = _connected_va(model, circuit, consumers.get(circuit.tag, []))
        description = circuit.description.lower()
        if "minisplit" in description:
            hvac_va += va  # heating/cooling at 100% (220.82(C))
        elif "ev charging" in description:
            ev_va += va  # already continuous (125% of plug load = 80% of breaker basis)
        elif "pv " in description or description.startswith("pv") or "backfeed" in description:
            continue  # a source, not a load
        elif ("lighting" in description or "general receptacles" in description
              or "small-appliance" in description or "laundry" in description):
            continue  # covered by the 3 VA/ft2 + 4500 VA general allowance above
        else:
            appliance_va += va

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
        "hvac_va": round(hvac_va, 0),
        "ev_va": round(ev_va, 0),
        "demand_va": round(demand_va, 0),
        "demand_amps": round(amps, 1),
        "service_amps": 200,
        "panel_rating_amps": 225,
        "within_service": amps <= 200.0,
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
    return [
        {"component": "Shelly Pro 4PM 4-channel DIN relay", "count": relays, "basis": basis},
        {"component": "24V DIN-rail power supply", "count": 1,
         "basis": "one 24V bus for LED backup lighting + PoE (notes lines 13-15)"},
        {"component": "DIN-rail 24V UPS module", "count": 1,
         "basis": "backup light/network ride-through (notes line 14)"},
    ]
