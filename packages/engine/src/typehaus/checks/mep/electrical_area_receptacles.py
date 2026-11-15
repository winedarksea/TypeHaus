"""2026 NEC 210.52(E)(1), (F), (H) and (I): outdoor, laundry, hallway, foyer receptacles.

* (E)(1) ``electrical.outdoor_front_back_receptacles``: a one- or two-family dwelling has a
  receptacle at the front and one at the back, readily accessible from grade and at most
  6 1/2 ft above it. The front faces the authored street frontage (``Site.streets``);
  "at the front" is read as the frontmost quarter of the dwelling's depth along that
  direction, or beyond it, and "at the back" the rearmost quarter. Height is measured to
  the box bottom from the lowest exterior grade beside it (``local_grade_elevation_m``);
  "readily accessible" is not graded beyond that.
* (F) ``electrical.laundry_receptacle``: a receptacle in every area set aside for laundry —
  a laundry room, or a room holding a washer or dryer (by the engine's plan symbols).
* (H) ``electrical.hallway_receptacle``: a hallway 10 ft or longer down its centreline gets
  one. The centreline is the long side of the rectangle with the room's area and perimeter,
  which is exact for a straight hall and close for an L.

Each counts a 210.52 receptacle (``_counts_toward_210_52``: unswitched, 125 V, at most
5 1/2 ft for (F)/(H)/(I); (E) keeps its own 6 1/2 ft).

* (I) ``electrical.foyer_receptacle``: a FOYER room over 60 sq ft (its clear-face area) has
  a receptacle on every wall space of 3 ft or more. Doorways, wells you could step into and
  windows reaching the floor break the wall line; nothing else does (the paraphrase names
  only "the like" of those).
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.mep.electrical import _counts_toward_210_52
from typehaus.checks.mep.electrical_code import _room_of
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import Occupancy
from typehaus.model.nec import NEC, cite
from typehaus.resolve.placeables import placed_xy
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

_FT = 0.3048
_OUTDOOR_MAX_M = 6.5 * _FT  # (E)(1)
_HALLWAY_MIN_M = 10 * _FT  # (H)
_FOYER_MIN_M2 = 60 * _FT * _FT  # (I)
_FOYER_WALL_SPACE_M = 3 * _FT  # (I)
_WINDOW_TO_FLOOR_M = 6 * 0.0254  # (I): a sidelight sill this low reaches the floor
_FOYER_WELL_LEDGE_M = 12 * 0.0254  # the receptacle_spacing ledge: no floor line past a well
_END_BAND = 0.25  # (E)(1): the frontmost / rearmost quarter of the dwelling's depth
_GRADE_PROBE_M = 0.3  # the ground beside a wall receptacle
_LAUNDRY_SYMBOLS = frozenset({"washer", "dryer", "washer-dryer-stacked"})


def _receptacles(ctx: CheckContext, *, height_limit: bool = True):
    """(element, storey, plan point, room or None) for every counting receptacle."""
    from shapely.geometry import Point

    rooms: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(axis_ring(room)) >= 3:
            rooms.setdefault(room.storey, []).append((room, axis_polygon(room)))
    by_tag = {room.tag: room for room in ctx.model.rooms}
    out = []
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            if (element.element_kind != "ElectricalDevice"
                    or not _counts_toward_210_52(ctx, element, height_limit=height_limit)):
                continue
            xy = placed_xy(ctx.model, element)
            if xy is None:
                continue
            room = _room_of(ctx.model, element, Point(xy), rooms.get(storey.tag, ()), by_tag)
            out.append((element, storey.tag, xy, room))
    return out


@check(Tier.CODE, "electrical.laundry_receptacle")
def laundry_receptacle(ctx: CheckContext) -> list[Finding]:
    """210.52(F): each laundry area has a receptacle."""
    cid, code = "electrical.laundry_receptacle", cite(NEC.LAUNDRY_RECEPTACLE)
    symbols = {t.tag: getattr(t, "plan_symbol", None) for t in ctx.plan.library.appliance_types}
    areas: dict[str, list[str]] = {r.tag: [] for r in ctx.model.rooms
                                   if r.occupancy == Occupancy.LAUNDRY.value}
    for obj in ctx.model.canvas_objects:
        if obj.kind == "Appliance" and symbols.get(obj.type_ref or "") in _LAUNDRY_SYMBOLS:
            if obj.room is None:
                return [unknown(cid, f"laundry appliance {obj.tag} resolves to no room",
                                (obj.tag,), code=code)]
            areas.setdefault(obj.room, []).append(obj.tag)
    if not areas:
        return [not_applicable(cid, "no laundry room and no washer or dryer is modelled",
                               code=code)]
    found: dict[str, list[str]] = {}
    for element, _storey, _xy, room in _receptacles(ctx):
        if room is not None and room.tag in areas:
            found.setdefault(room.tag, []).append(element.tag)
    out: list[Finding] = []
    for tag, appliances in sorted(areas.items()):
        held = f" (holds {', '.join(sorted(appliances))})" if appliances else ""
        if found.get(tag):
            out.append(passed(cid, f"laundry area {tag}{held}: "
                                   f"{', '.join(sorted(found[tag]))}", (tag,), code=code))
        else:
            out.append(failed(cid, f"laundry area {tag}{held} has no 125 V receptacle",
                              (tag, *appliances), code=code,
                              fix="add a receptacle in the laundry area"))
    return out


def _centreline_m(polygon) -> float:
    """Long side of the rectangle with this polygon's area and perimeter."""
    quarter = polygon.length / 4.0
    return quarter + math.sqrt(max(quarter * quarter - polygon.area, 0.0))


@check(Tier.CODE, "electrical.hallway_receptacle")
def hallway_receptacle(ctx: CheckContext) -> list[Finding]:
    """210.52(H): a hallway 10 ft or longer has a receptacle."""
    cid, code = "electrical.hallway_receptacle", cite(NEC.HALLWAY_RECEPTACLE)
    halls = [r for r in ctx.model.rooms if r.occupancy == Occupancy.HALLWAY.value]
    if not halls:
        return [not_applicable(cid, "no room is a hallway", code=code)]
    found: dict[str, list[str]] = {}
    for element, _storey, _xy, room in _receptacles(ctx):
        if room is not None:
            found.setdefault(room.tag, []).append(element.tag)
    out: list[Finding] = []
    for hall in halls:
        if len(axis_ring(hall)) < 3:
            out.append(unknown(cid, f"{hall.tag}: boundary is unresolved", (hall.tag,),
                               code=code))
            continue
        length = _centreline_m(axis_polygon(hall))
        label = f"{hall.tag} ({length / _FT:.1f} ft down its centreline)"
        if found.get(hall.tag):
            out.append(passed(cid, f"{label}: {', '.join(sorted(found[hall.tag]))}",
                              (hall.tag,), code=code))
        elif length < _HALLWAY_MIN_M:
            out.append(not_applicable(cid, f"{label} is under 10 ft", (hall.tag,),
                                      code=code))
        else:
            out.append(failed(cid, f"{label} has no receptacle", (hall.tag,),
                              code=code, fix="add a receptacle in the hall"))
    return out


def _foyer_breaks(ctx: CheckContext, ring: list, room) -> list[tuple[float, float]]:
    """Doorways, wells and floor-length windows: (I)'s "not wall space"."""
    from typehaus.resolve import room_perimeter
    from typehaus.resolve.geometry import opening_center

    walls = {w.tag: w for w in ctx.model.walls if w.storey == room.storey}
    hosts = {o.host_wall for o in ctx.model.openings if o.host_wall in walls
             and (o.is_passage or o.sill_m <= _WINDOW_TO_FLOOR_M)}
    windows = [o for o in ctx.model.openings if o.host_wall in hosts and not o.is_passage
               and o.sill_m <= _WINDOW_TO_FLOOR_M]
    out = room_perimeter.door_intervals(ctx.model, ring, room.storey, hosts=hosts)
    for opening in windows:
        center = opening_center(walls[opening.host_wall], opening)
        if center is None:
            continue
        s, d = room_perimeter.perimeter_position(ring, center)
        if d <= room_perimeter.NEAR_WALL_M:
            out.append((s - opening.width_m / 2.0, s + opening.width_m / 2.0))
    out += room_perimeter.floor_opening_intervals(ctx.plan, ring, room.storey,
                                                  _FOYER_WELL_LEDGE_M)
    return room_perimeter.merged_intervals(out, room_perimeter.perimeter_length(ring))


@check(Tier.CODE, "electrical.foyer_receptacle")
def foyer_receptacle(ctx: CheckContext) -> list[Finding]:
    """210.52(I): a foyer over 60 sq ft has a receptacle on each wall space of 3 ft or more."""
    from typehaus.checks.mep.electrical_wall_space import floor_line_ring
    from typehaus.resolve import room_perimeter

    cid, code = "electrical.foyer_receptacle", cite(NEC.FOYER_RECEPTACLE)
    foyers = [r for r in ctx.model.rooms if r.occupancy == Occupancy.FOYER.value]
    if not foyers:
        return [not_applicable(cid, "no room is a foyer", code=code)]
    stations: dict[str, list[tuple[str, tuple]]] = {}
    for element, _storey, xy, room in _receptacles(ctx):
        if room is not None:
            stations.setdefault(room.tag, []).append((element.tag, xy))
    out: list[Finding] = []
    for foyer in foyers:
        area_sf = foyer.area_m2 / (_FT * _FT)
        if foyer.area_m2 <= _FOYER_MIN_M2:
            out.append(not_applicable(cid, f"{foyer.tag} is {area_sf:.1f} sq ft, not over 60",
                                      (foyer.tag,), code=code))
            continue
        ring = floor_line_ring(ctx.model, foyer)
        if len(ring) < 3:
            out.append(unknown(cid, f"{foyer.tag}: boundary is unresolved", (foyer.tag,),
                               code=code))
            continue
        perimeter = room_perimeter.perimeter_length(ring)
        breaks = _foyer_breaks(ctx, ring, foyer)
        placed = []
        for tag, xy in stations.get(foyer.tag, ()):
            s, d = room_perimeter.perimeter_position(ring, xy)
            if d <= room_perimeter.NEAR_WALL_M:
                placed.append((tag, s))
        spaces = ([(hi, (breaks[(i + 1) % len(breaks)][0]
                         + (perimeter if i + 1 == len(breaks) else 0.0)))
                   for i, (_lo, hi) in enumerate(breaks)] if breaks else [(0.0, perimeter)])
        bare = []
        for lo, hi in spaces:
            if hi - lo < _FOYER_WALL_SPACE_M:
                continue
            if not any(lo <= s <= hi or lo <= s + perimeter <= hi for _t, s in placed):
                mid = room_perimeter.point_at(ring, ((lo + hi) / 2.0) % perimeter)
                bare.append(f"{(hi - lo) / _FT:.1f} ft near ({mid[0] / _FT:.1f}', "
                            f"{mid[1] / _FT:.1f}')")
        label = f"{foyer.tag} ({area_sf:.1f} sq ft)"
        if bare:
            out.append(failed(cid, f"{label}: wall space with no receptacle: "
                                   f"{'; '.join(bare)}", (foyer.tag,), code=code,
                              fix="add a receptacle on each wall space of 3 ft or more"))
        else:
            held = ", ".join(sorted(t for t, _s in placed)) or "no wall space of 3 ft"
            out.append(passed(cid, f"{label}: {held}", (foyer.tag,), code=code))
    return out


@check(Tier.CODE, "electrical.outdoor_front_back_receptacles")
def outdoor_front_back_receptacles(ctx: CheckContext) -> list[Finding]:
    """210.52(E)(1): a receptacle at the front and back, at most 6 1/2 ft above grade."""
    from typehaus.checks.mep.electrical_outdoor import _dwelling_storeys
    from typehaus.resolve.overlay import union_all
    from typehaus.resolve.site_earth import local_grade_elevation_m

    cid, code = "electrical.outdoor_front_back_receptacles", cite(NEC.OUTDOOR_FRONT_BACK)
    dwelling = _dwelling_storeys(ctx)
    footprint = union_all([axis_polygon(r) for r in ctx.model.rooms
                           if r.storey in dwelling and len(axis_ring(r)) >= 3])
    front = _front_direction(ctx, footprint)
    if footprint.is_empty or front is None:
        return [unknown(cid, "no street frontage is authored (Site.streets), so the "
                             "dwelling's front and back cannot be told apart", code=code)]
    cx, cy = footprint.centroid.x, footprint.centroid.y
    depth = [(x - cx) * front[0] + (y - cy) * front[1]
             for x, y in footprint.convex_hull.exterior.coords]
    lo, hi = min(depth), max(depth)  # band off the depth range: the centroid can sit off-centre
    ahead, behind = hi - (hi - lo) * _END_BAND, lo + (hi - lo) * _END_BAND
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    sides: dict[str, list[str]] = {"front": [], "back": []}
    high: dict[str, list[str]] = {"front": [], "back": []}
    for element, storey, (x, y), room in _receptacles(ctx, height_limit=False):
        obj = objects.get(element.tag)
        if room is not None or storey not in dwelling or obj is None:
            continue
        along = (x - cx) * front[0] + (y - cy) * front[1]
        side = "front" if along >= ahead else "back" if along <= behind else None
        if side is None:
            continue
        probe = [(x - _GRADE_PROBE_M, y - _GRADE_PROBE_M), (x + _GRADE_PROBE_M, y - _GRADE_PROBE_M),
                 (x + _GRADE_PROBE_M, y + _GRADE_PROBE_M), (x - _GRADE_PROBE_M, y + _GRADE_PROBE_M)]
        grade, _ = local_grade_elevation_m(ctx.model, probe)
        above = obj.z_m - grade
        (sides if above <= _OUTDOOR_MAX_M else high)[side].append(
            f"{element.tag} {above / _FT:.1f} ft above grade")
    out: list[Finding] = []
    for side in ("front", "back"):
        if sides[side]:
            out.append(passed(cid, f"{side}: {'; '.join(sorted(sides[side]))}", code=code))
        else:
            seen = f" (only {'; '.join(sorted(high[side]))})" if high[side] else ""
            out.append(failed(cid, f"no outdoor receptacle at the dwelling's {side} within "
                                   f"6 1/2 ft of grade{seen}", (), code=code,
                              fix=f"add a GFCI receptacle on the {side} wall"))
    return out


def _front_direction(ctx: CheckContext, footprint) -> tuple[float, float] | None:
    """Unit vector from the dwelling toward its first street frontage's parcel edge."""
    site = ctx.plan.project.site
    streets = site.streets
    parcel = [point.xy_m for point in site.parcel]
    if not streets or len(parcel) < 3 or footprint.is_empty:
        return None
    edge = streets[0].edge
    (ax, ay), (bx, by) = parcel[edge % len(parcel)], parcel[(edge + 1) % len(parcel)]
    mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
    dx, dy = mx - footprint.centroid.x, my - footprint.centroid.y
    length = math.hypot(dx, dy)
    return None if length < 1e-9 else (dx / length, dy / length)
