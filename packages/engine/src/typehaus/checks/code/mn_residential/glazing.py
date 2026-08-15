"""R308.4 safety glazing in hazardous locations.

The most-missed item on a window order, and the most expensive one to discover late: the
unit is installed, the inspector reads the etch in the corner, and it comes back out.

The section is a list of *locations*, every one of which is geometry this model already
resolves — in a door, beside a door, low and large near a walking surface, around a tub,
near a stair. What geometry cannot know is whether the unit that landed there was ordered
tempered, and that is precisely what ``WindowType.tempered`` states. So the rule derives
applicability and reads compliance, which is the split that makes it honest: it will never
invent a hazardous location, and it will never assume ordinary glass is safety glass.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import Occupancy
from typehaus.quantities import inch
from typehaus.resolve.geometry import opening_center

_ARC_OF_DOOR = inch(24)  # R308.4.2: within a 24" arc of either vertical door edge
_DOOR_ARC_MAX_SILL = inch(60)  # ...with the bottom edge below 60" above the floor
_LARGE_PANE_SF = 9.0  # R308.4.3
_LARGE_PANE_MAX_SILL = inch(18)  # ...bottom edge below 18"
_LARGE_PANE_MIN_HEAD = inch(36)  # ...top edge above 36"
_WET_MAX_SILL = inch(60)  # R308.4.5: glazing in a wet area below 60" above the floor
_STAIR_REACH = inch(60)  # R308.4.6/.7: within 60" of a stair or landing
_SF_PER_M2 = 10.7639

# R308.4.5 wet locations: bathtubs, showers, saunas, steam rooms, hot tubs. Read off the
# room, since the model puts the tub in a room rather than giving the tub a glazing wall.
_WET_OCCUPANCIES = {Occupancy.BATHROOM.value}


@check(Tier.CODE, "code.R308_4_safety_glazing")
def safety_glazing(ctx: CheckContext) -> list[Finding]:
    """R308.4 — glazing in a hazardous location is tempered or laminated.

    One finding per unit that lands in a hazardous location, naming *which* clause put it
    there. A unit in no hazardous location gets no finding at all — a house does not need a
    line per window saying an ordinary bedroom window may be ordinary glass.
    """
    from shapely.geometry import LineString, Point, Polygon

    cid = "code.R308_4_safety_glazing"
    window_types = {t.tag: t for t in ctx.plan.library.window_types}
    door_types = {t.tag: t for t in ctx.plan.library.door_types}
    storeys = {s.tag: s for s in ctx.plan.storeys}
    rooms: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(room.clear_face) >= 3:
            rooms.setdefault(room.storey, []).append((room, Polygon(room.clear_face)))

    out: list[Finding] = []

    # R308.4.1 — glazing in a door. No location test: every glazed door leaf, always.
    for opening in ctx.model.openings:
        if not opening.is_door:
            continue
        door_type = door_types.get(opening.type_ref)
        if door_type is None or not door_type.glazed:
            continue
        if door_type.tempered:
            out.append(_pass(cid, f"glazed door {opening.tag} is safety glazed", "R308.4.1"))
        else:
            out.append(_fail(cid, f"glazed door {opening.tag} ({door_type.tag}) is not "
                             "safety glazed; R308.4.1 requires it of all glazing in doors",
                             (opening.tag,), "R308.4.1"))

    # Everything else is a window in a location. Group the doors per wall once so the
    # 24"-arc test is a scan rather than a cross product.
    doors_by_wall: dict[str, list] = {}
    for opening in ctx.model.openings:
        if opening.is_door:
            doors_by_wall.setdefault(opening.host_wall, []).append(opening)
    stair_lines = _stair_lines(ctx, LineString)

    for opening in ctx.model.openings:
        if opening.is_door or opening.type_ref is None:
            continue
        window_type = window_types.get(opening.type_ref)
        wall = ctx.model.wall(opening.host_wall)
        storey = storeys.get(wall.storey) if wall else None
        if window_type is None or wall is None or storey is None:
            out.append(_unknown(cid, f"{opening.tag} resolves no window type, host wall and "
                                "storey, so its hazardous-location status cannot be decided",
                                (opening.tag,), "R308.4"))
            continue
        reasons = _hazard_reasons(ctx, opening, wall, storey, window_type,
                                  doors_by_wall.get(opening.host_wall, ()),
                                  rooms.get(wall.storey, ()), stair_lines, Point)
        if not reasons:
            continue
        clause = reasons[0][0]
        why = "; ".join(text for _clause, text in reasons)
        if window_type.tempered:
            out.append(_pass(cid, f"{opening.tag} is safety glazed — {why}", clause))
        else:
            out.append(_fail(cid, f"{opening.tag} ({window_type.tag}) sits in a hazardous "
                             f"location ({why}) with ordinary glazing; R308.4 requires "
                             "tempered or laminated glass", (opening.tag,), clause))
    if not out:
        return [_pass(cid, "no glazing sits in an R308.4 hazardous location", "R308.4")]
    return out


def _stair_lines(ctx: CheckContext, line_type):
    """Plan lines of every stair walking surface — treads, winders and landings."""
    out = []
    for stair in ctx.model.stairs:
        for member in stair.members:
            if member.category in ("tread", "winder", "landing"):
                if member.p0 != member.p1:
                    out.append((line_type([member.p0, member.p1]), stair.tag, member.z1_m))
    return out


def _hazard_reasons(ctx, opening, wall, storey, window_type, wall_doors, storey_rooms,
                    stair_lines, point_type):
    """Every R308.4 clause that makes this opening's location hazardous."""
    reasons: list[tuple[str, str]] = []
    sill = opening.sill_m
    head = sill + opening.height_m
    area_sf = opening.width_m * opening.height_m * _SF_PER_M2

    # R308.4.2 — within a 24" arc of a door edge, bottom below 60".
    if sill < _DOOR_ARC_MAX_SILL.meters:
        for door in wall_doors:
            gap = (abs(opening.center_along_m - door.center_along_m)
                   - (opening.width_m + door.width_m) / 2.0)
            if gap <= _ARC_OF_DOOR.meters:
                reasons.append(("R308.4.2", f"within 24\" of door {door.tag}"))
                break

    # R308.4.3 — a pane over 9 sf, bottom under 18", top over 36".
    if (area_sf > _LARGE_PANE_SF and sill < _LARGE_PANE_MAX_SILL.meters
            and head > _LARGE_PANE_MIN_HEAD.meters):
        reasons.append(("R308.4.3", f"{area_sf:.0f} sf pane with its sill "
                        f"{sill / .0254:.0f}\" above the floor"))

    # R308.4.5 — a wet location, bottom under 60" above the standing surface.
    if sill < _WET_MAX_SILL.meters:
        point = opening_center(wall, opening)
        if point is not None:
            centre = point_type(*point)
            for room, poly in storey_rooms:
                if (room.occupancy in _WET_OCCUPANCIES
                        and poly.distance(centre) <= wall.thickness_m / 2.0 + 0.15):
                    reasons.append(("R308.4.5", f"a wet location ({room.tag}) with its sill "
                                    f"{sill / .0254:.0f}\" above the floor"))
                    break

    # R308.4.6/.7 — within 60" of a stair, landing or ramp walking surface.
    if stair_lines:
        point = opening_center(wall, opening)
        if point is not None:
            centre = point_type(*point)
            floor_z = storey.elevation.meters
            for line, stair_tag, tread_z in stair_lines:
                # Only a tread near this storey's floor plane is beside this window; a
                # flight two storeys down is 60" away in plan and nowhere near in space.
                if abs(tread_z - floor_z) > 3.0:
                    continue
                if line.distance(centre) <= _STAIR_REACH.meters:
                    reasons.append(("R308.4.7", f"within 60\" of stair {stair_tag}"))
                    break
    return reasons
