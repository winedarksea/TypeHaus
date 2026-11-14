"""``electrical.bath_receptacle_zone`` — 2026 NEC 406.9(C)(1): no receptacle in a tub/shower zone.
Also ``bath_hvac_zone`` (440.8) and ``bath_luminaire_zone`` (410.10(D), 422.18(B)).

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


_LUM_CID = "electrical.bath_luminaire_zone"
_ZONE_FORMS = {"track": "lighting track", "pendant": "a pendant",
               "chandelier": "a cord-, chain- or cable-hung luminaire",
               "ceiling_fan_light": "a ceiling-suspended (paddle) fan"}


@check(Tier.ADVISORY, _LUM_CID)
def bath_luminaire_zone(ctx: CheckContext) -> list[Finding]:
    """410.10(D) and 422.18(B): luminaires and paddle fans in and over a tub or shower.

    (D)(1)/422.18(B): no track, pendant, chain/cable/cord-hung luminaire or paddle fan within
    3 ft (plan) and 8 ft above the rim or threshold, in the tub's own room: a luminaire in
    another room (``room_owning``) is behind a wall and out of the zone (PASS), one whose room
    is unresolved stays UNKNOWN. (D)(2): a
    luminaire inside the tub or shower outline up to 8 ft is marked damp, or wet where spray
    reaches it, which the model cannot say, so a damp-only one is UNKNOWN. The rim is the body
    top for a ``-TUB``, the pan floor for a shower (conservative). A luminaire's reach is its
    footprint; a ``LightRun`` strip is not lighting track and is not graded.
    """
    from shapely.geometry import Point, Polygon

    from typehaus.checks._authoring import advisory
    from typehaus.findings import Result
    from typehaus.model.electrical import luminaire_types
    from typehaus.resolve.room_lookup import room_owning

    code = cite(NEC.BATH_LUMINAIRE_ZONE, NEC.PADDLE_FAN_BATH_ZONE)
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    types = luminaire_types(ctx.plan.library)
    wet = [e for e in ctx.plan.all_elements() if e.element_kind == "Fixture"
           and e.tag.rsplit("-", 1)[-1] in _WET and e.tag in objects]
    lights = [e for e in ctx.plan.all_elements() if e.element_kind == "ElectricalDevice"
              and e.kind is DeviceKind.LIGHT and e.tag in objects and e.type_ref in types]
    if not wet or not lights:
        return [not_applicable(_LUM_CID, "no tub or shower, or no luminaire, is authored",
                               code=code)]
    out: list[Finding] = []
    for fixture in sorted(wet, key=lambda e: e.tag):
        fobj = objects[fixture.tag]
        body = Polygon(fobj.footprint)
        rim = fobj.body_z1_m if fixture.tag.endswith("-TUB") else fobj.body_z0_m
        there = room_owning(ctx.model, fobj.storey,
                            tuple(body.representative_point().coords)[0])
        for light in sorted(lights, key=lambda e: e.tag):
            lobj = objects[light.tag]
            if lobj.storey != fobj.storey or lobj.body_z0_m >= rim + _VERTICAL_M \
                    or lobj.body_z1_m <= rim:
                continue
            shape = (Polygon(lobj.footprint) if len(lobj.footprint) >= 3
                     else Point(lobj.position))
            gap = body.distance(shape)
            product = types[light.type_ref]
            form = product.form.value
            here = room_owning(ctx.model, lobj.storey, lobj.position)
            if gap <= _ZONE_M and form in _ZONE_FORMS and (here is None or there is None):
                out.append(unknown(
                    _LUM_CID, f"{light.tag} is {_ZONE_FORMS[form]} {gap / 0.3048:.1f} ft from "
                              f"{fixture.tag} in plan; the model cannot resolve whose room "
                              "each stands in, so it cannot say a wall separates them",
                    (light.tag, fixture.tag), code=code,
                    fix="place the luminaire and the tub in rooms"))
                continue
            if here is not None and there is not None and here.tag != there.tag:
                if gap <= _ZONE_M and form in _ZONE_FORMS:
                    out.append(passed(
                        _LUM_CID, f"{light.tag} is in {here.tag}, separated from the tub's room "
                                  f"{there.tag}: outside the {fixture.tag} zone",
                        (light.tag, fixture.tag), code=code))
                continue  # another room is behind a wall: not in the zone
            if gap <= _ZONE_M and form in _ZONE_FORMS and product.voltage <= 30:
                out.append(advisory(
                    _LUM_CID, f"{light.tag} is {_ZONE_FORMS[form]} {gap / 0.3048:.1f} ft from "
                              f"{fixture.tag} in the same room and reaches below 8 ft over its "
                              f"rim; it runs at {product.voltage} V. 410.10(D)(1) bars it with "
                              "no voltage limit, and 410.150(C)(9) bars track there (the "
                              "(C)(8) 30 V carve-out is for mounting height only)",
                    (light.tag, fixture.tag), Result.FAIL,
                    code=cite(NEC.BATH_LUMINAIRE_ZONE, NEC.LIGHTING_TRACK_LOCATIONS),
                    fix="move it out of the 3 ft x 8 ft zone, or use a fixed luminaire"))
            elif gap <= _ZONE_M and form in _ZONE_FORMS:
                out.append(advisory(
                    _LUM_CID, f"{light.tag} is {_ZONE_FORMS[form]} {gap / 0.3048:.1f} ft from "
                              f"{fixture.tag} in plan, in the tub's room, and reaches below 8 ft "
                              "over its rim; the zone is all-encompassing within the room",
                    (light.tag, fixture.tag), Result.FAIL, code=code,
                    fix="use a fixed, non-suspended luminaire, or move it out of the zone"))
            elif body.intersects(shape) and not product.wet_rated:
                what = "damp only; wet if shower spray reaches it" if product.damp_rated \
                    else "neither damp nor wet rated"
                out.append(unknown(
                    _LUM_CID, f"{light.tag} is within {fixture.tag}'s outline up to 8 ft "
                              f"({what}); the model cannot say whether spray reaches it",
                    (light.tag, fixture.tag), code=cite(NEC.BATH_LUMINAIRE_DAMP),
                    fix="specify a wet-rated type, or state the spray exposure"))
    if not out:
        out.append(passed(_LUM_CID, f"no suspended luminaire or fan stands in the zone of "
                                    f"{len(wet)} tubs and showers, and every luminaire over "
                                    "one is wet rated", tuple(e.tag for e in wet), code=code))
    return out
