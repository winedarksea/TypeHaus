"""Fixture setout on the enlarged bath plans (I2-005/006): what the plumber sets out from.

Per drained fixture, read off the resolved model, not a table: the side strings from its
setout point (the floor drain where the drain is under the fixture — a WC flange, a tub or
shower drain — else the centreline) to the nearest finish face or obstruction each way
(UPC 402.5's "centre to any side wall or obstruction"), the drain to the finish wall behind
(the WC rough-in), and the clear floor in front of a WC or lav. Obstructions are the
other fixtures (a lav over a wall-hung WC still obstructs it) and the casework standing in the
fixture's own height band; a towel bar or a paper holder is not one.
"""

from __future__ import annotations

import math

from shapely.geometry import LineString, Point, Polygon

from typehaus.emit.draw._shared import to_in
from typehaus.emit.draw.scene import ArchDimension, NamedPoint
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.stone_pieces import inches_text

_KINDS = frozenset({"Fixture", "Appliance", "Furniture"})
#: Below this plan area (m², ~72 sq in) a wall-hung piece is an accessory, not an obstruction.
_MIN_OBSTACLE_M2 = 72 * M_PER_IN**2
_RAY_M = 5.0
_MIN_STRING_M = 1.0 * M_PER_IN
#: Past these the far side string and the front clear are a room width, not a setout.
_FAR_SIDE_M = 36 * M_PER_IN
_FRONT_M = 48 * M_PER_IN
#: How far past its own body a drain's back wall may stand and still be its rough-in wall.
_BACK_SLACK_M = 3.0 * M_PER_IN


def setout_nodes(model: ResolvedModel, rooms: tuple[str, ...]) -> list[ArchDimension]:
    from typehaus.model import Service
    from typehaus.resolve.mep_sleeves import expected_port_point

    faces = {room.tag: Polygon(room.clear_face) for room in model.rooms
             if room.tag in rooms and room.clear_face and len(room.clear_face) >= 3}
    placed = [obj for obj in model.canvas_objects
              if obj.room in faces and obj.kind in _KINDS and len(obj.footprint) >= 3]
    types = {t.tag: t for t in model.plan.library.fixture_types}
    out: list[ArchDimension] = []
    clears: dict[str, set[str | None]] = {}
    for fixture in placed:
        if fixture.kind != "Fixture":
            continue
        drain = expected_port_point(model, fixture.tag, Service.DRAIN)
        theta = math.radians(fixture.rotation_degrees or 0.0)
        if drain is None or abs(math.sin(2 * theta)) > 1e-3:
            continue  # undrained (a filler), or off-axis: the writer draws H/V strings only
        back = (-math.sin(theta), math.cos(theta))
        side = (math.cos(theta), math.sin(theta))
        body = Polygon(fixture.footprint)
        # Under the body, not on its face: a wall-drained lav's drain sits on its back edge.
        floor_drain = body.buffer(-M_PER_IN).contains(Point(drain[:2]))
        origin = tuple(drain[:2]) if floor_drain else tuple(fixture.position)
        walls = faces[fixture.room].exterior
        obstacles = [Polygon(obj.footprint) for obj in placed
                     if obj.room == fixture.room and obj.tag != fixture.tag
                     and not Polygon(obj.footprint).intersection(body).area > 1e-6  # its filler
                     and (obj.kind != "Furniture" or (_same_band(obj, fixture) and Polygon(
                         obj.footprint).area >= _MIN_OBSTACLE_M2))
                     and not Polygon(obj.footprint).buffer(1e-4).contains(Point(origin))]
        # The footprint is centred on ``position`` (the symbol frame), so it reaches as far
        # forward as back.
        reach = max((p[0] - fixture.position[0]) * back[0]
                    + (p[1] - fixture.position[1]) * back[1] for p in fixture.footprint)
        aft = ((origin[0] - fixture.position[0]) * back[0]
               + (origin[1] - fixture.position[1]) * back[1])
        rough = (_string(origin, back, walls, [], f"{fixture.tag}-back",
                         limit=reach - aft + _BACK_SLACK_M)  # to a wall it stands against
                 if floor_drain else [])
        out += rough
        # A side string measures the lateral station only, so where a rough-in string leaves
        # the drain it runs halfway to the front instead and their labels clear.
        ahead = (reach + aft) / 2.0 if rough else 0.0
        start = (origin[0] - back[0] * ahead, origin[1] - back[1] * ahead)
        # The nearer side always (one reference per axis); the farther only while it is
        # still a clearance a reader checks, not a string across the room.
        sides = sorted((_string(start, (sign * side[0], sign * side[1]), walls, obstacles,
                                f"{fixture.tag}-side{int(sign)}") for sign in (1.0, -1.0)),
                       key=lambda found: _length(found[0]) if found else math.inf)
        out += sides[0] + [d for d in sides[1] if _length(d) <= _FAR_SIDE_M]
        if floor_drain and Service.WATER_HOT in getattr(types.get(fixture.type_ref or ""),
                                                        "needs", ()):
            continue  # a tub or shower: its front clear is no setout (a WC has no hot water)
        front = (fixture.position[0] - back[0] * reach, fixture.position[1] - back[1] * reach)
        clear = _string(front, (-back[0], -back[1]), walls, obstacles,
                        f"{fixture.tag}-front", clear=True, limit=_FRONT_M)
        # Two fixtures facing across one clear floor print it once.
        seen = clears.setdefault(fixture.room, set())
        out += [d for d in clear if d.text not in seen]
        seen.update(d.text for d in clear)
    return out


def _length(dimension: ArchDimension) -> float:
    return math.dist(dimension.p0, dimension.p1) * M_PER_IN


def _same_band(obj, fixture) -> bool:
    if None in (obj.body_z0_m, obj.body_z1_m, fixture.body_z0_m, fixture.body_z1_m):
        return True
    return obj.body_z0_m < fixture.body_z1_m - 1e-6 and obj.body_z1_m > fixture.body_z0_m + 1e-6


def _string(start, direction, walls, obstacles, key: str, clear: bool = False,
            limit: float = _RAY_M) -> list[ArchDimension]:
    """One string from ``start`` to the first face along ``direction``; none if it is
    shorter than an inch (the fixture is against that face)."""
    ray = LineString([start, (start[0] + direction[0] * _RAY_M,
                              start[1] + direction[1] * _RAY_M)])
    hits = [_nearest(start, ray.intersection(edge)) for edge in
            (walls, *(item.exterior for item in obstacles))]
    hits = [hit for hit in hits if hit is not None and hit[0] > 1e-6]
    if not hits:
        return []
    distance, end = min(hits)
    if distance < _MIN_STRING_M or distance > limit:
        return []
    p0, p1 = to_in(start), to_in(end)
    # Inches, the way a rough-in is read (12", 15"), and short enough for a 15" string.
    text = inches_text(round(distance / M_PER_IN * 16) / 16) + (" CLR" if clear else "")
    return [ArchDimension(ends=(NamedPoint(xy=p0, name=f"{key}-0"),
                                NamedPoint(xy=p1, name=f"{key}-1")),
                          p0=p0, p1=p1, offset=0.0, text=text)]


def _nearest(start, geometry):
    if geometry.is_empty:
        return None
    points = [geometry] if geometry.geom_type == "Point" else [
        Point(c) for part in getattr(geometry, "geoms", [geometry]) for c in part.coords]
    points = [p for p in points if p.distance(Point(start)) > 1e-6]  # a face run along
    if not points:
        return None
    best = min(points, key=lambda p: p.distance(Point(start)))
    return best.distance(Point(start)), (best.x, best.y)
