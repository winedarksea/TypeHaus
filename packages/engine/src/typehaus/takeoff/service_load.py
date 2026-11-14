"""The 2026 NEC 120.82 optional-method service load — split from ``takeoff/electrical.py``.

Connected VA per circuit, the 120.82 term each circuit lands in, load-management credits and
the demand estimate ``electrical.service_load`` / ``panel_feeder_load`` and E-601 read.
``takeoff/electrical`` re-exports every public name, so imports from there still work.
"""

from __future__ import annotations

from collections import Counter

from typehaus.model.nec import NEC, cite
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.lighting import line_voltage_run_va, nec_floor_area_ft2

# 2026 NEC 120.82 (optional method, was 220.82), read in the printed code 2026-11-13.
# (A): the sum of (B), (C) and (D); permitted only where the service conductors are >= 100 A.
OPTIONAL_METHOD_MIN_AMPS = 100.0
# (B): (1) 2 VA/ft2 of 120.5(C) floor area; (2) 1,500 VA per 20 A small-appliance and
# laundry circuit; (3)/(4) nameplates. First 8,000 VA of the sum at 100%, the rest at 40%.
GENERAL_LIGHTING_VA_PER_FT2 = 2.0
SMALL_APPLIANCE_OR_LAUNDRY_VA = 1500.0
# 210.11(C)(1)/(2) minimums: required whether or not the plan authors them.
MIN_SMALL_APPLIANCE_CIRCUITS = 2
MIN_LAUNDRY_CIRCUITS = 1
FIRST_8KVA = 8000.0
REMAINDER_DEMAND_FACTOR = 0.4
# (C): the largest of six. (1) cooling 100%; (2) heat pump without supplemental 100%;
# (3) compressor 100% + supplemental 65%, the compressor left out where it is prevented from
# running with the supplemental heat; (4) space heating 65% under four separately controlled
# units, (5) 40% at four or more; (6) thermal storage at 100% (not modelled).
SEPARATELY_CONTROLLED_UNIT_THRESHOLD = 4
RESISTANCE_HEAT_FACTOR_FEW = 0.65
RESISTANCE_HEAT_FACTOR_MANY = 0.40
SUPPLEMENTAL_HEAT_FACTOR = 0.65
_BTUH_PER_W = 3.412
# (D) EVSE at its nameplate (120.57), 7,200 VA only where no nameplate is authored.
EVSE_DEFAULT_VA = 7200.0
# 120.7(B): a PCS control setting is at most 80% of the monitored OCPD's rating.
PCS_MAX_SETTING_FRACTION = 0.8
SERVICE_VOLTS = 240.0


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
    if _evse_unrated(model, circuit, consumers):
        return EVSE_DEFAULT_VA
    return _listed_va(model, consumers)


def _listed_va(model: ResolvedModel, consumers: list) -> float:
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


def _evse_unrated(model: ResolvedModel, circuit, consumers: list) -> bool:
    """An EV circuit with no authored nameplate load: 120.57 takes 7,200 VA."""
    return (circuit.load_va is None and _bucket(model, circuit, consumers) == "ev"
            and not _listed_va(model, consumers))


_HEAT_PUMP_KINDS = frozenset({"heat_pump", "indoor_head", "ducted_air_handler"})


def _is_heat_pump(circuit, consumers: list) -> bool:
    """A circuit feeding the heat-pump system NEC 120.82(C)(1)-(3) selects among.

    Typed, not name-matched: an ``Equipment`` of an HVAC kind on the circuit is the modeled
    answer. A renamed unit must not drop out of (C) into (B)(3)'s fixed appliances, which
    would count it at 40% instead of selecting it whole. A heat kit staged with an air
    handler's blower (``blower_interlock_ref``) is (C)(3)'s supplemental heat even on a
    circuit of its own.
    """
    for element in consumers:
        if element.element_kind != "Equipment":
            continue
        kind = getattr(getattr(element, "kind", None), "value", None)
        if kind in _HEAT_PUMP_KINDS or (
                kind == "space_heater" and getattr(element, "blower_interlock_ref", None)):
            return True
    return False


def _supplemental_va(model: ResolvedModel, consumers: list) -> float:
    """Nameplate W of the resistance heat a heat-pump circuit carries (a heat kit).

    Read off ``EquipmentType.resistance_heating_btuh``; an element with none states nothing.
    """
    types = {t.tag: t for t in model.plan.library.equipment_types}
    return sum(
        float(getattr(types.get(element.type_ref), "resistance_heating_btuh", None) or 0.0)
        for element in consumers if element.element_kind == "Equipment"
    ) / _BTUH_PER_W


def _locked_out_compressors(model: ResolvedModel) -> frozenset[str]:
    """Compressor tags some resistance heat names in ``compressor_lockout_ref``."""
    return frozenset(
        ref for storey in model.plan.storeys
        for element in model.plan.storey_elements(storey.tag)
        if (ref := getattr(element, "compressor_lockout_ref", None)))


def _is_compressor(element, locked: frozenset[str]) -> bool:
    return (element.element_kind == "Equipment" and element.tag in locked
            and getattr(getattr(element, "kind", None), "value", None) == "heat_pump")


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
    if "small-appliance" in description:
        return "small_appliance"
    if "laundry" in description:
        return "laundry"
    if "lighting" in description or "general receptacles" in description:
        return "general"
    return "appliance"


# Buckets (B)(1)/(B)(2) price per square foot or per circuit, not by connected VA.
_ALLOWANCE_BUCKETS = frozenset({"source", "general", "small_appliance", "laundry"})


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
    was missed. (120.82(C)(3)'s compressor interlock is not a group: ``compressor_lockout_ref``.)
    """
    if management.strategy == "noncoincident":
        if not (management.source.strip() or management.listing.strip()):
            return (f"{cite(NEC.NONCOINCIDENT)} counts noncoincident loads once only where "
                    "they are unlikely to run together (1) or listed equipment prevents it "
                    "(2); neither a source nor a listing recorded")
        return ""
    if management.strategy == "pcs":
        if not management.listing.strip():
            return (f"{NEC.EDITION} {NEC.PCS_LISTING} / {NEC.PCS_SETPOINT}: a PCS in a load "
                    "calculation must be listed (UL 3141); none recorded")
        amps = management.monitored_ocpd_amps
        if amps is not None and management.max_simultaneous_va > (
                PCS_MAX_SETTING_FRACTION * amps * SERVICE_VOLTS):
            return (f"{NEC.EDITION} {NEC.PCS_CONTROL_SETTING}: the PCS setting must not exceed "
                    f"{PCS_MAX_SETTING_FRACTION:.0%} of the monitored {amps:.0f} A OCPD "
                    f"({PCS_MAX_SETTING_FRACTION * amps * SERVICE_VOLTS:.0f} VA at "
                    f"{SERVICE_VOLTS:.0f} V); {management.max_simultaneous_va:.0f} VA is set")
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

    A ``noncoincident`` group never counts below its single largest member (120.6): an
    authored ceiling under that is raised to it, one above it is kept.
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
        member_va = [_connected_va(model, c, consumers.get(c.tag, [])) for c in members]
        group_va = sum(member_va)
        cap_va = management.max_simultaneous_va
        if management.strategy == "noncoincident":
            cap_va = max(cap_va, max(member_va, default=0.0))
        excess = max(0.0, group_va - cap_va)
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
            "group_va": group_va, "cap_va": cap_va,
            "excess_va": excess, "by_bucket": by_bucket,
            "credited": not refusal, "refusal": refusal,
        })
    return out


def general_demand_va(general_va: float) -> float:
    """120.82(B): the first 8 kVA of the general loads at 100%, the remainder at 40%."""
    return (min(general_va, FIRST_8KVA)
            + max(general_va - FIRST_8KVA, 0.0) * REMAINDER_DEMAND_FACTOR)


def hvac_selection(*, cooling_va: float, heat_pump_va: float, supplemental: bool,
                   resistance_va: float, resistance_units: int) -> tuple[float, str]:
    """120.82(C): the largest selection, and the item it is. A tie goes to the earlier entry.

    ``heat_pump_va`` already holds supplemental heat at 65% and no locked-out compressor.
    """
    few = resistance_units < SEPARATELY_CONTROLLED_UNIT_THRESHOLD
    options = (
        (heat_pump_va, NEC.OPTIONAL_HEAT_PUMP_SUPPLEMENTAL if supplemental
         else NEC.OPTIONAL_HEAT_PUMP),
        (cooling_va, NEC.OPTIONAL_COOLING),
        (resistance_va * (RESISTANCE_HEAT_FACTOR_FEW if few else RESISTANCE_HEAT_FACTOR_MANY),
         NEC.OPTIONAL_RESISTANCE_FEW if few else NEC.OPTIONAL_RESISTANCE_MANY),
    )
    return max(options, key=lambda option: option[0])


def service_load_summary(
        model: ResolvedModel, *, circuit_tags: frozenset[str] | None = None,
) -> dict[str, object]:
    """NEC 120.82 optional-method estimate against the authored service and panel bus.

    Labeled an estimate on the sheet: (B)(1) from resolved floor area, (B)(2) per counted
    circuit (never fewer than 210.11(C)'s two small-appliance and one laundry for the whole
    house), fixed appliances from the authored circuits, EV at 100% (D; nameplate, else 7,200 VA), PV excluded
    (a source, not a load).

    (C) is a *selection*, not a sum (``hvac_selection``): cooling, the heat pumps with
    their supplemental heat at 65%, or resistance space heating at 65%/40%, largest wins.
    A compressor some heat kit names in ``compressor_lockout_ref`` is left out of the
    heating selection, never the cooling one.

    Only a *credited* ``LoadManagement`` is applied, and in the bucket each managed circuit
    was counted in: an interlock over two fixed appliances saves 40% of its connected
    excess, not 100% of it, because that is the only rate at which the excess ever reached
    the demand. A refused group's excess stays in the demand.

    ``circuit_tags`` narrows the whole calculation to a subset — the per-panel feeder
    estimate. (B)(1) follows the subset's ``general`` circuits and (B)(2) counts only the
    subset's own, with no minimum.
    """
    floor_area_ft2 = nec_floor_area_ft2(model)
    consumers = _circuit_consumers(model)
    scope = [c for c in model.plan.library.circuits
             if circuit_tags is None or c.tag in circuit_tags]
    buckets = {c.tag: _bucket(model, c, consumers.get(c.tag, [])) for c in scope}
    counts = Counter(buckets.values())
    small_appliance, laundry = counts["small_appliance"], counts["laundry"]
    lighting_va = GENERAL_LIGHTING_VA_PER_FT2 * floor_area_ft2
    if circuit_tags is None:
        small_appliance = max(small_appliance, MIN_SMALL_APPLIANCE_CIRCUITS)
        laundry = max(laundry, MIN_LAUNDRY_CIRCUITS)
    elif not counts["general"]:
        lighting_va = 0.0
    general_va = lighting_va + SMALL_APPLIANCE_OR_LAUNDRY_VA * (small_appliance + laundry)

    locked = _locked_out_compressors(model)
    connected: dict[str, float] = {}
    ev_default: list[str] = []  # EV circuits counted at the 120.57 default, no nameplate
    resistance_heat_units = 0
    supplemental_va = 0.0
    locked_compressor_va = 0.0
    for circuit in scope:
        bucket = buckets[circuit.tag]
        if bucket in _ALLOWANCE_BUCKETS:
            continue
        on = consumers.get(circuit.tag, [])
        va = _connected_va(model, circuit, on)
        connected[bucket] = connected.get(bucket, 0.0) + va
        if bucket == "ev" and _evse_unrated(model, circuit, on):
            ev_default.append(circuit.tag)
        if bucket == "resistance_heat":
            resistance_heat_units += 1
        elif bucket == "heat_pump":
            kit = min(va, _supplemental_va(model, on))
            supplemental_va += kit
            if any(_is_compressor(element, locked) for element in on):
                locked_compressor_va += va - kit

    credits = load_management_credits(model, circuit_tags=circuit_tags)
    managed: dict[str, float] = {}
    for credit in credits:
        for bucket, va in credit["by_bucket"].items():  # type: ignore[union-attr]
            managed[bucket] = managed.get(bucket, 0.0) + va

    def available(bucket: str, managed_applied: bool) -> float:
        credit = managed.get(bucket, 0.0) if managed_applied else 0.0
        return max(0.0, connected.get(bucket, 0.0) - credit)

    def hvac(managed_applied: bool) -> tuple[float, str]:
        heat_pump = available("heat_pump", managed_applied)
        return hvac_selection(
            cooling_va=max(0.0, heat_pump - supplemental_va),
            heat_pump_va=max(0.0, heat_pump - supplemental_va * (1 - SUPPLEMENTAL_HEAT_FACTOR)
                             - locked_compressor_va),
            supplemental=supplemental_va > 0,
            resistance_va=available("resistance_heat", managed_applied),
            resistance_units=resistance_heat_units)

    def demand(managed_applied: bool) -> float:
        return (general_demand_va(general_va + available("appliance", managed_applied))
                + hvac(managed_applied)[0] + available("ev", managed_applied))

    heat_pump_total = connected.get("heat_pump", 0.0)
    cooling_va = max(0.0, heat_pump_total - supplemental_va)
    heat_pump_va = max(0.0, heat_pump_total - supplemental_va * (1 - SUPPLEMENTAL_HEAT_FACTOR)
                       - locked_compressor_va)
    resistance_heat_va = connected.get("resistance_heat", 0.0)
    resistance_factor = (RESISTANCE_HEAT_FACTOR_MANY
                         if resistance_heat_units >= SEPARATELY_CONTROLLED_UNIT_THRESHOLD
                         else RESISTANCE_HEAT_FACTOR_FEW)
    hvac_va, hvac_item = hvac(False)
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
        "optional_method_applies": service_amps >= OPTIONAL_METHOD_MIN_AMPS,
        "floor_area_ft2": round(floor_area_ft2, 0),
        "general_lighting_va": round(general_va, 0),
        "small_appliance_circuits": small_appliance,
        "laundry_circuits": laundry,
        "fixed_appliance_va": round(connected.get("appliance", 0.0), 0),
        "heat_pump_va": round(heat_pump_va, 0),
        "cooling_va": round(cooling_va, 0),
        "resistance_heat_va": round(resistance_heat_va, 0),
        "resistance_heat_units": resistance_heat_units,
        "resistance_heat_factor": resistance_factor,
        "hvac_va": round(hvac_va, 0),
        "hvac_selection": hvac_item,
        "ev_va": round(connected.get("ev", 0.0), 0),
        "ev_default_circuits": ev_default,
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
