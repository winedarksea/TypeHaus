"""The 2026 NEC 120.82 optional-method service load — split from ``takeoff/electrical.py``.

Connected VA per circuit, the 120.82 term each circuit lands in, load-management credits and
the demand estimate ``electrical.service_load`` / ``panel_feeder_load`` and E-601 read.
``takeoff/electrical`` re-exports every public name, so imports from there still work.
"""

from __future__ import annotations

from typehaus.model.nec import NEC, cite
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.lighting import line_voltage_run_va, nec_floor_area_ft2

# 2026 NEC 120.82 (optional method, was 220.82) constants for the service-load summary.
# 120.82(B): 2 VA/ft2 general lighting (was 3) and the first 8,000 VA at 100% (was 10 kVA),
# per NFPA 70 A2025 CMP-2 second draft, Annex D2(a)/(b), SR-7961/7964; EC&M (Austin,
# 2026-05-19) gives the same 2 VA/ft2 for 120.41. Read 2026-11-07, not the printed text.
GENERAL_LIGHTING_VA_PER_FT2 = 2.0
SMALL_APPLIANCE_AND_LAUNDRY_VA = 4500.0  # 2 x 1500 small-appliance + 1500 laundry
FIRST_8KVA = 8000.0
REMAINDER_DEMAND_FACTOR = 0.4
# 120.82(C), item numbers contested: electric space heating is taken at 65% of nameplate when there are
# fewer than four separately controlled units, 40% at four or more.
SEPARATELY_CONTROLLED_UNIT_THRESHOLD = 4
RESISTANCE_HEAT_FACTOR_FEW = 0.65
RESISTANCE_HEAT_FACTOR_MANY = 0.40
# 120.82(C)(3): a heat pump's compressor at 100% and its supplemental electric heat at 65%.
SUPPLEMENTAL_HEAT_FACTOR = 0.65
_BTUH_PER_W = 3.412


def _circuit_consumers(model: ResolvedModel) -> dict[str, list]:
    by_circuit: dict[str, list] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            ref = getattr(element, "circuit", None)
            if ref:
                by_circuit.setdefault(ref, []).append(element)
    return by_circuit


def _connected_va(model: ResolvedModel, circuit, consumers: list) -> float:
    """Authored ``load_va`` if the circuit states one; otherwise what is on it.

    Devices bill their type's ``load_va``. A line-voltage ``LightRun`` has no ``load_va`` —
    it is watts per foot over a length — so its VA is indexed by tag from the *resolved*
    runs (the authored element carries a ``path``, not a length). A 24V run is not on a
    circuit at all; its PSU is, and the PSU is a device counted above.
    """
    if circuit.load_va is not None:
        return float(circuit.load_va)
    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    run_va = line_voltage_run_va(model)
    return sum(
        float(types[element.type_ref].load_va or 0.0)
        for element in consumers
        if element.element_kind == "ElectricalDevice" and element.type_ref in types
    ) + sum(
        run_va.get(element.tag, 0.0)
        for element in consumers
        if element.element_kind == "LightRun"
    )


_HEAT_PUMP_KINDS = frozenset({"heat_pump", "indoor_head", "ducted_air_handler"})


def _is_heat_pump(circuit, consumers: list) -> bool:
    """A circuit feeding the heat-pump system NEC 120.82(C)(2) takes at 100%.

    Typed, not name-matched: an ``Equipment`` of an HVAC kind on the circuit is the modeled
    answer. A name match on the description is fragile — a renamed unit would silently drop
    the heating term to zero and land it in the fixed-appliance bucket (B)(3), which (B)
    explicitly excludes heating loads from.
    """
    return any(
        element.element_kind == "Equipment"
        and getattr(getattr(element, "kind", None), "value", None) in _HEAT_PUMP_KINDS
        for element in consumers
    )


def _supplemental_va(model: ResolvedModel, consumers: list) -> float:
    """Nameplate W of the resistance heat a heat-pump circuit carries (a heat kit).

    Read off ``EquipmentType.resistance_heating_btuh``; an element with none states nothing.
    """
    types = {t.tag: t for t in model.plan.library.equipment_types}
    return sum(
        float(getattr(types.get(element.type_ref), "resistance_heating_btuh", None) or 0.0)
        for element in consumers if element.element_kind == "Equipment"
    ) / _BTUH_PER_W


def _is_resistance_heat(circuit, consumers: list) -> bool:
    """Fixed electric space heating — the loads NEC 120.82(C) governs, not (B)(3).

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


# The service size, when the model states none. 200A is the ordinary residential service and
# the fallback when no device states ``service_amps``; the summary says which of the two it
# used.
DEFAULT_SERVICE_AMPS = 200.0


def _bucket(model: ResolvedModel, circuit, consumers: list) -> str:
    """Which NEC 120.82 term a circuit's connected load lands in.

    Split out of ``service_load_summary`` so the load-management credit can be taken in the
    same bucket the load was counted in. Crediting an interlocked pair of appliances at 100%
    of their connected excess — which is what subtracting the credit straight off the demand
    did — overstates the saving by a factor of 2.5, because that excess only ever reached
    the demand through 120.82(B)'s 40% remainder factor.
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
    because that is the piece of equipment whose rating *is* the service size.
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


def _credit_refusal(model: ResolvedModel, management, members, consumers) -> str:
    """Why this group earns no credit, or "" when it earns one.

    The rules are the bases ``LoadManagement`` names, and each is refused on its own terms
    rather than on a blanket "unlisted" — a reader has to be able to see which requirement
    was missed. (2026 120.82(C)(3) carries no compressor/supplemental-heat interlock credit.)
    """
    if management.strategy == "noncoincident":
        if not management.source.strip():
            return (f"{cite(NEC.NONCOINCIDENT)} counts noncoincident loads once only where "
                    "something makes them exclusive; no source recorded")
        return ""
    if management.strategy == "pcs":
        if not management.listing.strip():
            return (f"{NEC.EDITION} {NEC.PCS_LISTING} / {NEC.PCS_SETPOINT}: a PCS in a load "
                    "calculation must be listed (UL 3141); none recorded")
        return ""
    return f"unknown strategy {management.strategy!r}"


def load_management_credits(
        model: ResolvedModel, *, circuit_tags: frozenset[str] | None = None,
) -> list[dict[str, object]]:
    """Per-``LoadManagement`` connected excess, resolved into the buckets it came from.

    A controller guarantees its group never draws more than ``max_simultaneous_va``
    together, so the group's connected excess over that ceiling never reaches the service.
    Where a group spans buckets the excess is removed from each circuit in proportion to its
    share of the group's connected load — exact for the homogeneous groups anyone actually
    builds (all EV, all resistance, all fixed appliance), and stated rather than hidden for
    the mixed case.

    ``credited`` is the gate: a group whose basis does not hold reports its excess and a
    ``refusal``, and ``service_load_summary`` leaves that excess in the demand. A credit
    the code does not name and no listing backs is not a credit.
    """
    consumers = _circuit_consumers(model)
    circuits = {c.tag: c for c in model.plan.library.circuits
                if circuit_tags is None or c.tag in circuit_tags}
    out: list[dict[str, object]] = []
    for management in model.plan.library.load_managements:
        known = {c.tag for c in model.plan.library.circuits}
        missing = [tag for tag in management.managed_circuits if tag not in known]
        members = [circuits[tag] for tag in management.managed_circuits if tag in circuits]
        if circuit_tags is not None and not members:
            continue  # this group reaches no circuit in the subset
        group_va = sum(_connected_va(model, c, consumers.get(c.tag, [])) for c in members)
        excess = max(0.0, group_va - management.max_simultaneous_va)
        refusal = _credit_refusal(model, management, members, consumers)
        by_bucket: dict[str, float] = {}
        if excess > 0 and group_va > 0 and not refusal:
            for circuit in members:
                va = _connected_va(model, circuit, consumers.get(circuit.tag, []))
                share = excess * (va / group_va)
                by_bucket[_bucket(model, circuit, consumers.get(circuit.tag, []))] = (
                    by_bucket.get(_bucket(model, circuit, consumers.get(circuit.tag, [])), 0.0)
                    + share)
        out.append({
            "tag": management.tag, "strategy": management.strategy,
            "listing": management.listing, "source": management.source,
            "managed_circuits": list(management.managed_circuits),
            "missing_circuits": missing,
            "group_va": group_va, "cap_va": management.max_simultaneous_va,
            "excess_va": excess, "by_bucket": by_bucket,
            "credited": not refusal, "refusal": refusal,
        })
    return out


def service_load_summary(
        model: ResolvedModel, *, circuit_tags: frozenset[str] | None = None,
) -> dict[str, object]:
    """NEC 120.82 optional-method estimate against the authored service and panel bus.

    Labeled an estimate on the sheet: general lighting from resolved conditioned floor
    area, fixed appliances from the authored circuits, EV already at its continuous
    rating (the device types carry 80% of breaker), PV excluded (a source, not a load).

    The heating/cooling term is 120.82(C)'s *selection*, not a sum: heat pumps at 100%
    (C)(2), their supplemental heat kit at 65% (C)(3), against electric resistance space
    heating at 65%/40% (C)(5)/(6), largest wins.
    Adding them would be double-counting a house that cannot run both flat out — and
    would also mean a 1.5 kW bench heater in an unconditioned garage landing in the
    fixed-appliance bucket (B)(3), which (B) explicitly excludes heating loads from.

    Only a *credited* ``LoadManagement`` is applied, and in the bucket each managed circuit
    was counted in: an interlock over two fixed appliances saves 40% of its connected
    excess, not 100% of it, because that is the only rate at which the excess ever reached
    the demand. A refused group's excess stays in the demand.

    ``circuit_tags`` narrows the whole calculation to a subset — the per-panel feeder
    estimate. The general-lighting allowance follows the subset's ``general`` circuits, so
    a panel hosting none of them carries none of it.
    """
    floor_area_ft2 = nec_floor_area_ft2(model)
    general_va = GENERAL_LIGHTING_VA_PER_FT2 * floor_area_ft2 + SMALL_APPLIANCE_AND_LAUNDRY_VA

    consumers = _circuit_consumers(model)
    scope = [c for c in model.plan.library.circuits
             if circuit_tags is None or c.tag in circuit_tags]
    if circuit_tags is not None and not any(
            _bucket(model, c, consumers.get(c.tag, [])) == "general" for c in scope):
        general_va = 0.0
    connected: dict[str, float] = {}
    resistance_heat_units = 0
    supplemental_va = 0.0
    for circuit in scope:
        bucket = _bucket(model, circuit, consumers.get(circuit.tag, []))
        if bucket in ("source", "general"):
            continue  # a source is not a load; general is the 2 VA/ft2 allowance above
        va = _connected_va(model, circuit, consumers.get(circuit.tag, []))
        connected[bucket] = connected.get(bucket, 0.0) + va
        if bucket == "resistance_heat":
            resistance_heat_units += 1
        elif bucket == "heat_pump":
            supplemental_va += min(va, _supplemental_va(model, consumers.get(circuit.tag, [])))
    # The part of the heat-pump bucket that is supplemental heat counts at 65%, not 100%.
    supplemental_relief = supplemental_va * (1.0 - SUPPLEMENTAL_HEAT_FACTOR)

    credits = load_management_credits(model, circuit_tags=circuit_tags)
    managed: dict[str, float] = {}
    for credit in credits:
        for bucket, va in credit["by_bucket"].items():  # type: ignore[union-attr]
            managed[bucket] = managed.get(bucket, 0.0) + va

    def available(bucket: str) -> float:
        return max(0.0, connected.get(bucket, 0.0) - managed.get(bucket, 0.0))

    heat_pump_va = max(0.0, connected.get("heat_pump", 0.0) - supplemental_relief)
    resistance_heat_va = connected.get("resistance_heat", 0.0)
    appliance_va = connected.get("appliance", 0.0)
    ev_va = connected.get("ev", 0.0)

    resistance_factor = (RESISTANCE_HEAT_FACTOR_MANY
                         if resistance_heat_units >= SEPARATELY_CONTROLLED_UNIT_THRESHOLD
                         else RESISTANCE_HEAT_FACTOR_FEW)

    def demand(managed_applied: bool) -> float:
        appliance = available("appliance") if managed_applied else appliance_va
        heat_pump = (max(0.0, available("heat_pump") - supplemental_relief)
                     if managed_applied else heat_pump_va)
        resistance = available("resistance_heat") if managed_applied else resistance_heat_va
        ev = available("ev") if managed_applied else ev_va
        base = general_va + appliance
        return (min(base, FIRST_8KVA)
                + max(base - FIRST_8KVA, 0.0) * REMAINDER_DEMAND_FACTOR
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
        "method": f"{NEC.EDITION} {NEC.OPTIONAL_DWELLING} optional method (estimate)",
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
