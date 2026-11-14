"""``electrical.bath_receptacle_zone`` — 2026 NEC 406.9(C)(1): no receptacle in a tub/shower zone.

The zone is 3 ft in plan from the tub or shower stall's outside edge, up to 8 ft above its
rim, and stops at a floor, wall, ceiling, room door, window or fixed barrier. Here a tub or
shower is a ``Fixture`` tagged ``-SH``, ``-TUB`` or ``-TUBSH``; a receptacle in the same room
within 3 ft of its footprint is in the zone unless a fixed barrier (a glass panel counts only
if the model says so, which it cannot) or Exceptions 1-4 apply, so it reads UNKNOWN, never
FAIL. One in another room (by ``room_owning``) is separated by a wall or door and is skipped.
Heights are not read (receptacles stand well under 8 ft). Switches (404.6(C), 406.9(C)(2))
concern the tub or shower space itself and are not graded.
"""

from __future__ import annotations

from typehaus.checks._authoring import not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import DeviceKind
from typehaus.model.nec import NEC, cite

_CID = "electrical.bath_receptacle_zone"
_ZONE_M = 0.9
_WET = ("SH", "TUB", "TUBSH")
_KINDS = frozenset({DeviceKind.RECEPTACLE, DeviceKind.RECEPTACLE_GFCI,
                    DeviceKind.RECEPTACLE_240})


@check(Tier.ADVISORY, _CID)
def bath_receptacle_zone(ctx: CheckContext) -> list[Finding]:
    """Each receptacle within 3 ft of a tub or shower in its own room is reported."""
    from shapely.geometry import Point, Polygon

    from typehaus.resolve.room_lookup import room_owning

    code = cite(NEC.BATH_ZONE)
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    wet = [e for e in ctx.plan.all_elements() if e.element_kind == "Fixture"
           and e.tag.rsplit("-", 1)[-1] in _WET and e.tag in objects]
    if not wet:
        return [not_applicable(_CID, "no tub or shower fixture is authored", code=code)]
    out: list[Finding] = []
    receptacles = [e for e in ctx.plan.all_elements()
                   if e.element_kind == "ElectricalDevice" and e.kind in _KINDS
                   and e.tag in objects]
    for fixture in sorted(wet, key=lambda e: e.tag):
        fobj = objects[fixture.tag]
        body = Polygon(fobj.footprint)
        for rc in sorted(receptacles, key=lambda e: e.tag):
            robj = objects[rc.tag]
            if robj.storey != fobj.storey:
                continue
            gap = body.distance(Point(robj.position))
            if gap > _ZONE_M:
                continue
            here = room_owning(ctx.model, robj.storey, robj.position)
            centre = tuple(body.representative_point().coords)[0]
            there = room_owning(ctx.model, fobj.storey, centre)
            if here is not None and there is not None and here.tag != there.tag:
                continue  # across a wall or door
            out.append(unknown(
                _CID, f"{rc.tag} is {gap / 0.3048:.1f} ft from {fixture.tag} in plan, inside the "
                      "3 ft zone unless a fixed barrier, wall, door or Exception 1-4 separates "
                      "them; the model cannot tell", (rc.tag, fixture.tag), code=code,
                fix="confirm the barrier, or move the receptacle outside the zone"))
    if not out:
        out.append(passed(_CID, "no receptacle stands within 3 ft of a tub or shower in its "
                                "own room", tuple(e.tag for e in wet), code=code))
    return out


_AC_CID = "electrical.bath_hvac_zone"
_AC_KINDS = frozenset({"indoor_head", "ducted_air_handler", "heat_pump"})
_VERTICAL_M = 2.5


@check(Tier.ADVISORY, _AC_CID)
def bath_hvac_zone(ctx: CheckContext) -> list[Finding]:
    """440.8: no air-conditioning equipment within 3 ft (plan) and 8 ft (above the rim) of a tub
    or shower. The zone is all-encompassing: a wall does not end it, unlike 406.9(C). The rim is
    read as the top of the fixture body, which over-states a stall's threshold (conservative).
    """
    from shapely.geometry import Polygon

    from typehaus.checks._authoring import advisory
    from typehaus.findings import Result

    code = cite(NEC.HVAC_BATH_ZONE)
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    wet = [e for e in ctx.plan.all_elements() if e.element_kind == "Fixture"
           and e.tag.rsplit("-", 1)[-1] in _WET and e.tag in objects]
    units = [e for e in ctx.plan.all_elements() if e.element_kind == "Equipment"
             and getattr(getattr(e, "kind", None), "value", "") in _AC_KINDS and e.tag in objects]
    if not wet or not units:
        return [not_applicable(_AC_CID, "no tub or shower, or no air-conditioning equipment, "
                                        "is authored", code=code)]
    out: list[Finding] = []
    for fixture in sorted(wet, key=lambda e: e.tag):
        fobj = objects[fixture.tag]
        body = Polygon(fobj.footprint)
        top = fobj.body_z1_m + _VERTICAL_M
        for unit in sorted(units, key=lambda e: e.tag):
            uobj = objects[unit.tag]
            if uobj.storey != fobj.storey:
                continue
            gap = body.distance(Polygon(uobj.footprint))
            if gap <= _ZONE_M and uobj.body_z0_m < top:
                out.append(advisory(
                    _AC_CID, f"{unit.tag} is {gap / 0.3048:.1f} ft from {fixture.tag} in plan and "
                             "starts below 8 ft over its rim: inside the 440.8 zone",
                    (unit.tag, fixture.tag), Result.FAIL, code=code,
                    fix="move the unit out of the 3 ft by 8 ft zone"))
    if not out:
        out.append(passed(_AC_CID, f"none of {len(units)} heat-pump units stands within 3 ft of "
                                   f"any of {len(wet)} tubs or showers",
                          tuple(e.tag for e in units), code=code))
    return out
