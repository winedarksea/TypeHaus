"""Device listing facts the NEC grades (lane E of decision #120's residue).

* ``electrical.spd_nominal_discharge`` — 230.67(E) and 215.18(E): the service SPD and each
  feeder panel's plug-on have an In of 10 kA or more; 215.18(C) the plug-on is Type 1 or 2.
  Only the SPDs those sections require are graded (a voluntary branch-circuit SPD is not).
* ``electrical.outdoor_receptacle_wr`` — 406.9(A)(1)(c)/(B)(1)(d): an outdoor 125/250 V
  nonlocking receptacle is listed weather-resistant; (B)(1)(a)-(b): in a wet location its
  hood is an extra-duty in-use cover. Outdoors is "in no room" (``electrical_code._room_of``);
  the model cannot say damp from wet, so a WR one without an in-use cover is UNKNOWN. Indoor
  damp rooms (a plant room) are not located by the model and are not graded.
* ``electrical.controlled_receptacle`` — 406.11(D): a receptacle a smart relay, occupancy
  sensor or timer switches carries the "controlled" marking. A plain wall switch (or a dimmer)
  is the 210.70 exception's wall switch and is out of scope.
* ``electrical.panel_sccr`` — 408.6: each panel's label SCCR at least the available fault
  current authored on the service equipment's type; UNKNOWN until both are known.
"""

from __future__ import annotations

from typehaus.checks._authoring import by_result
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import DeviceKind
from typehaus.model.nec import NEC, cite

_SPD_CID = "electrical.spd_nominal_discharge"
_WR_CID = "electrical.outdoor_receptacle_wr"
_CTRL_CID = "electrical.controlled_receptacle"
_SCCR_CID = "electrical.panel_sccr"
_MIN_IN_KA = 10.0
# ``ElectricalDeviceType.control`` values that switch a load with no hand on the switch.
_AUTOMATIC = frozenset({"smart", "occupancy", "timer"})
_RECEPTACLES = frozenset({DeviceKind.RECEPTACLE, DeviceKind.RECEPTACLE_GFCI,
                          DeviceKind.RECEPTACLE_240})


def _types(ctx: CheckContext) -> dict:
    return {t.tag: t for t in ctx.plan.library.electrical_device_types}


def _devices(ctx: CheckContext) -> list:
    return [e for e in ctx.plan.all_elements() if e.element_kind == "ElectricalDevice"]


def _grade_in(cid: str, what: str, dtype, code: str, *, need_class: bool) -> Finding:
    """One SPD's In (and, for a plug-on, its 215.18(C) Type) against the 10 kA floor."""
    if dtype is None:
        return by_result(cid, Result.UNKNOWN, f"{what}: no product type is named, so its In "
                         "and listing are unknown", (what,), code,
                         "name the SPD's catalog type (spd_type_ref on a plug-on circuit)")
    name = dtype.tag
    if need_class and dtype.spd_class not in ("1", "2"):
        state = "states no UL 1449 Type" if dtype.spd_class is None \
            else f"is spd_class {dtype.spd_class!r}"
        result = Result.UNKNOWN if dtype.spd_class is None else Result.FAIL
        return by_result(cid, result, f"{what} ({name}) {state}; 215.18(C) wants Type 1 or 2",
                         (what, name), code)
    rated = dtype.spd_nominal_discharge_ka
    listing = f", {dtype.spd_listing}" if dtype.spd_listing else ""
    if rated is None:
        return by_result(cid, Result.UNKNOWN, f"{what} ({name}{listing}): In is not published "
                         "or not authored; 10 kA or more is required", (what, name), code,
                         "author spd_nominal_discharge_ka from the UL 1449 label or sheet")
    if rated < _MIN_IN_KA:
        return by_result(cid, Result.FAIL, f"{what} ({name}{listing}): In {rated:g} kA is under "
                         "the 10 kA floor", (what, name), code,
                         "choose an SPD marked In 10 kA or more")
    return by_result(cid, Result.PASS, f"{what} ({name}{listing}): In {rated:g} kA, at least "
                     "10 kA", (what, name), code)


@check(Tier.CODE, _SPD_CID)
def spd_nominal_discharge(ctx: CheckContext) -> list[Finding]:
    """230.67(E)/215.18(E): every required SPD has an In of 10 kA or more."""
    from typehaus.checks.mep.electrical_grounding import grounding
    from typehaus.checks.mep.electrical_grounding_bonds import service_spds

    types = _types(ctx)
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    by_device = {e.tag: e for e in _devices(ctx)}
    out: list[Finding] = []
    graded: set[str] = set()
    root = grounding(ctx).root
    for tag in service_spds(ctx, root) if root is not None else ():
        if tag in circuits:
            continue  # a plug-on in the service equipment: graded below with its panel
        device = by_device.get(tag)
        out.append(_grade_in(_SPD_CID, tag, types.get(getattr(device, "type_ref", None) or ""),
                             cite(NEC.SERVICE_SPD_RATING), need_class=False))
        graded.add(tag)
    for circuit in sorted((c for c in circuits.values() if c.spd), key=lambda c: c.tag):
        out.append(_grade_in(_SPD_CID, circuit.tag, types.get(circuit.spd_type_ref or ""),
                             cite(NEC.FEEDER_SPD_RATING, NEC.SERVICE_SPD_RATING),
                             need_class=True))
        graded.add(circuit.tag)
    if not graded:
        return [by_result(_SPD_CID, Result.NOT_APPLICABLE, "no SPD at the service and no SPD "
                          "circuit in any panel", (), cite(NEC.SERVICE_SPD_RATING))]
    return out


def _outdoor_receptacles(ctx: CheckContext) -> list:
    """Receptacles whose host face or point looks into no resolved room."""
    from shapely.geometry import Point

    from typehaus.checks.mep.electrical_code import _room_of
    from typehaus.resolve.placeables import placed_xy
    from typehaus.resolve.room_lookup import axis_polygon, axis_ring

    rooms: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(axis_ring(room)) >= 3:
            rooms.setdefault(room.storey, []).append((room, axis_polygon(room)))
    by_tag = {room.tag: room for room in ctx.model.rooms}
    out = []
    for storey in ctx.plan.storeys:
        for device in ctx.plan.storey_elements(storey.tag):
            if device.element_kind != "ElectricalDevice" or device.kind not in _RECEPTACLES:
                continue
            xy = placed_xy(ctx.model, device)
            if xy is None:
                continue
            if _room_of(ctx.model, device, Point(xy), rooms.get(storey.tag, ()), by_tag) is None:
                out.append(device)
    return sorted(out, key=lambda d: d.tag)


@check(Tier.CODE, _WR_CID)
def outdoor_receptacle_wr(ctx: CheckContext) -> list[Finding]:
    """406.9(A)(1)(c)/(B)(1): outdoor receptacles are WR, under an in-use hood where wet."""
    code = cite(NEC.DAMP_RECEPTACLE, NEC.WET_RECEPTACLE)
    types = _types(ctx)
    found = _outdoor_receptacles(ctx)
    if not found:
        return [by_result(_WR_CID, Result.NOT_APPLICABLE, "no receptacle stands outside every "
                          "resolved room", (), code)]
    out: list[Finding] = []
    for device in found:
        dtype = types.get(device.type_ref or "")
        if dtype is not None and dtype.deadfront:
            continue  # a blank-face GFCI is no receptacle
        name = getattr(dtype, "tag", device.type_ref)
        tags = (device.tag, name) if name else (device.tag,)
        wr = getattr(dtype, "weather_resistant", None)
        hood = getattr(dtype, "in_use_cover", None)
        if wr is False:
            out.append(by_result(_WR_CID, Result.FAIL, f"{device.tag} is outdoors and {name} is "
                                 "not weather-resistant", tags, code,
                                 "use a listed WR receptacle"))
        elif wr is None:
            out.append(by_result(_WR_CID, Result.UNKNOWN, f"{device.tag} is outdoors and {name} "
                                 "does not state weather-resistant", tags, code,
                                 "author weather_resistant from the product listing"))
        elif hood:
            out.append(by_result(_WR_CID, Result.PASS, f"{device.tag} ({name}): WR, extra-duty "
                                 "in-use cover", tags, code))
        else:
            out.append(by_result(_WR_CID, Result.UNKNOWN, f"{device.tag} ({name}) is WR with no "
                                 "in-use cover stated: enough where damp, not where wet "
                                 "((B)(1)(a)-(b)); the model cannot tell damp from wet", tags,
                                 code, "an extra-duty in-use hood, or confirm a damp location"))
    return out


@check(Tier.ADVISORY, _CTRL_CID)
def controlled_receptacle(ctx: CheckContext) -> list[Finding]:
    """406.11(D): an automatically controlled receptacle carries the 'controlled' marking."""
    code = cite(NEC.CONTROLLED_RECEPTACLE)
    types = _types(ctx)
    devices = {e.tag: e for e in _devices(ctx)}
    out: list[Finding] = []
    for device in sorted(devices.values(), key=lambda d: d.tag):
        if device.kind not in _RECEPTACLES:
            continue
        auto = sorted(s for s in device.controlled_by
                      if getattr(types.get(getattr(devices.get(s), "type_ref", None) or ""),
                                 "control", None) in _AUTOMATIC)
        if not auto:
            continue
        dtype = types.get(device.type_ref or "")
        marked = getattr(dtype, "controlled_marking", None)
        tags = (device.tag, *auto)
        via = ", ".join(auto)
        if marked:
            out.append(by_result(_CTRL_CID, Result.PASS, f"{device.tag} is switched by {via} and "
                                 f"{dtype.tag} carries the 'controlled' marking", tags, code))
        elif marked is False:
            out.append(by_result(_CTRL_CID, Result.FAIL, f"{device.tag} is switched by {via} and "
                                 f"{dtype.tag} has no 'controlled' marking", tags, code,
                                 "use a receptacle marked 'controlled' on its face"))
        else:
            out.append(by_result(_CTRL_CID, Result.UNKNOWN, f"{device.tag} is switched by "
                                 f"automatic control {via}; {device.type_ref} does not state "
                                 "the 'controlled' symbol and word on its face", tags, code,
                                 "a receptacle marked 'controlled', or a plain wall switch"))
    if not out:
        return [by_result(_CTRL_CID, Result.NOT_APPLICABLE, "no receptacle is switched by a "
                          "relay, occupancy sensor or timer", (), code)]
    return out


@check(Tier.CODE, _SCCR_CID)
def panel_sccr(ctx: CheckContext) -> list[Finding]:
    """408.6: each panel's label SCCR is at least the available fault current."""
    code = cite(NEC.SWITCHBOARD_SCCR)
    types = _types(ctx)
    devices = _devices(ctx)
    panels = sorted((e for e in devices if e.kind is DeviceKind.PANEL), key=lambda e: e.tag)
    if not panels:
        return [by_result(_SCCR_CID, Result.NOT_APPLICABLE, "no panel in the plan", (), code)]
    supply = [(e.tag, getattr(types.get(e.type_ref or ""), "available_fault_current_a", None))
              for e in devices if e.kind is DeviceKind.METER]
    fault = max((a for _, a in supply if a is not None), default=None)
    out: list[Finding] = []
    for panel in panels:
        rating = getattr(types.get(panel.type_ref or ""), "sccr_a", None)
        if rating is None:
            out.append(by_result(_SCCR_CID, Result.UNKNOWN, f"{panel.tag}: {panel.type_ref} "
                                 "states no short-circuit current rating", (panel.tag,), code,
                                 "author sccr_a from the panel's label"))
        elif fault is None:
            out.append(by_result(_SCCR_CID, Result.UNKNOWN, f"{panel.tag}: SCCR {rating:,} A, "
                                 "but no available fault current is authored at the service "
                                 "(the utility's figure, 408.6(1))", (panel.tag,), code,
                                 "author available_fault_current_a on the meter-main's type"))
        elif rating < fault:
            out.append(by_result(_SCCR_CID, Result.FAIL, f"{panel.tag}: SCCR {rating:,} A is under "
                                 f"the {fault:,} A available", (panel.tag,), code,
                                 "a higher-rated panel, or series-rated breakers"))
        else:
            out.append(by_result(_SCCR_CID, Result.PASS, f"{panel.tag}: label SCCR {rating:,} A "
                                 f"against {fault:,} A available (the field mark rests on the "
                                 "installed breakers, 408.6(2))", (panel.tag,), code))
    return out
