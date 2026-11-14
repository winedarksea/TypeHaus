"""``electrical.stair_lighting_control`` — 2026 NEC 210.70(A)(2)(3), stair lighting control.

An interior stair with six or more risers between floor levels has a wall switch or listed
control at each floor level (and each landing level with a stair entry). Read here as: some
luminaire that names the stair (``serves_stair`` on an ``ElectricalDevice`` or ``LightRun``)
is controlled by a switch on the storey of each end, within ``_SWITCH_REACH_M`` in plan of
that end's nosing. One luminaire must answer at both ends: (A)(2)(4) speaks of the (3)
lighting's "every control location", so a light switched only upstairs plus another switched
only downstairs is two lights each with one control, not stair lighting with two.

Not graded: landing levels with a stair entry (no such landing is modelled), the exception
for remote, central or automatic control (a luminaire with no wall switch is UNKNOWN), and
(A)(2)(4) dimmers (no dimmer type is modelled). The reach is the engine's reading; the code
gives no distance.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.nec import NEC, cite
from typehaus.resolve.placeables import placed_xy
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

_CID = "electrical.stair_lighting_control"
_MIN_RISERS = 6
_SWITCH_REACH_M = 10 * 0.3048  # engine reading: "at" a floor level, from the end nosing


def _ends(stair) -> list[tuple[str, tuple[float, float]]]:
    """(storey, plan point) of the foot and head nosings."""
    from typehaus.resolve.stairs.walkline import stair_walk_stations

    route = stair_walk_stations(stair)
    if len(route) < 2:
        return []
    mid = [((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0) for a, b, _ in (route[0], route[-1])]
    return [(stair.storey, mid[0]), (stair.to_storey, mid[1])]


@check(Tier.CODE, _CID)
def stair_lighting_control(ctx: CheckContext) -> list[Finding]:
    """Each interior stair of 6+ risers has its lighting switched at every floor level."""
    from shapely.geometry import Point

    code = cite(NEC.STAIR_SWITCHES)
    storey_of: dict[str, str] = {}
    elements: dict[str, object] = {}
    lights: dict[str, list] = {}
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            storey_of[element.tag] = storey.tag
            elements[element.tag] = element
            stair_tag = getattr(element, "serves_stair", None)
            if stair_tag and element.element_kind in ("ElectricalDevice", "LightRun"):
                lights.setdefault(stair_tag, []).append(element)
    rooms: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(axis_ring(room)) >= 3:
            rooms.setdefault(room.storey, []).append(axis_polygon(room))

    out: list[Finding] = []
    for stair in sorted(ctx.model.stairs, key=lambda s: s.tag):
        if stair.riser_count < _MIN_RISERS:
            continue
        ends = _ends(stair)
        if not ends or not any(poly.contains(Point(xy)) for storey, xy in ends
                               for poly in rooms.get(storey, ())):
            continue  # exterior, or no resolved walk line
        served = lights.get(stair.tag, [])
        if not served:
            out.append(unknown(_CID, f"{stair.tag} ({stair.riser_count} risers): no luminaire "
                                     "names it in `serves_stair`, so its lighting control "
                                     "cannot be graded", (stair.tag,), code=code,
                               fix=f"set serves_stair=\"{stair.tag}\" on the lights over it"))
            continue
        graded = [(_reach(ctx, light, ends, elements, storey_of), light.tag)
                  for light in served]
        full = [(tag, r) for r, tag in graded if all(s == "near" for s, _ in r)]
        if full:
            tag, reach = full[0]
            where = ", ".join(f"{sw} on {storey}" for (_, sw), (storey, _) in zip(
                reach, ends, strict=True))
            out.append(passed(_CID, f"{stair.tag}: {tag} is switched at both floor levels "
                                    f"({where})", (stair.tag, tag), code=code))
            continue
        detail = "; ".join(f"{tag}: " + ", ".join(
            f"{storey} {_say(state, sw)}" for (state, sw), (storey, _) in zip(
                reach, ends, strict=True)) for reach, tag in graded)
        if any(all(s != "none" for s, _ in r) for r, _ in graded):
            out.append(unknown(_CID, f"{stair.tag}: a switch for its lighting stands on each "
                                     f"level but more than {_SWITCH_REACH_M / 0.3048:.0f} ft "
                                     f"from the stair end ({detail})", (stair.tag,), code=code))
        else:
            out.append(failed(
                _CID, f"{stair.tag} ({stair.riser_count} risers): no luminaire that lights it "
                      f"is switched at every floor level ({detail}); "
                      f"{NEC.STAIR_SWITCHES} wants a control at each", (stair.tag,),
                code=code,
                fix="add a 3-way so one of its lights is switched at both ends"))
    if not out:
        out.append(not_applicable(_CID, "no interior stair has six or more risers", code=code))
    return out


def _reach(ctx: CheckContext, light, ends, elements, storey_of
           ) -> list[tuple[str, str | None]]:
    """Per end: ("near" | "far" | "none", nearest switch tag on that storey)."""
    switches = [elements[tag] for tag in getattr(light, "controlled_by", ())
                if tag in elements]
    out: list[tuple[str, str | None]] = []
    for storey, (x, y) in ends:
        here = []
        for switch in switches:
            if storey_of.get(switch.tag) != storey:
                continue
            xy = placed_xy(ctx.model, switch)
            if xy is not None:
                here.append((math.hypot(xy[0] - x, xy[1] - y), switch.tag))
        if not here:
            out.append(("none", None))
        else:
            gap, tag = min(here)
            out.append(("near" if gap <= _SWITCH_REACH_M else "far", tag))
    return out


def _say(state: str, switch: str | None) -> str:
    return {"near": f"by {switch}", "far": f"only by {switch}, beyond reach",
            "none": "no switch"}[state]
