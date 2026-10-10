"""A room's perimeter as an arc-length coordinate, and the things that break it.

Shared by ``checks/mep/electrical.receptacle_spacing`` (NEC wall space) and
``resolve/interior_trim.py`` (base runs). It lives in ``resolve`` because a resolver may not
import ``checks``. A ring is the room's ``clear_face``; ``s`` is metres along it from its
first vertex. Every interval builder returns linear ``(s0, s1)`` pairs; an arc crossing the
ring's seam comes back as two.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from typehaus.resolve.geometry import opening_center
from typehaus.resolve.intervals import merge as _merge_intervals

# How close to the room boundary a thing must sit to belong to that stretch of it.
NEAR_WALL_M = 0.5
# How far a cabinet's base may sit above the floor and still meet the floor line.
FLOOR_CONTACT_M = 6 * 0.0254


def perimeter_length(ring: list) -> float:
    return sum(
        ((ring[(i + 1) % len(ring)][0] - ring[i][0]) ** 2
         + (ring[(i + 1) % len(ring)][1] - ring[i][1]) ** 2) ** 0.5
        for i in range(len(ring)))


def perimeter_position(ring: list, point: tuple) -> tuple[float, float]:
    """(arc-length coordinate of the nearest boundary point, distance to the boundary)."""
    best_s, best_d = 0.0, float("inf")
    s = 0.0
    for index in range(len(ring)):
        (x0, y0), (x1, y1) = ring[index], ring[(index + 1) % len(ring)]
        ex, ey = x1 - x0, y1 - y0
        length = (ex * ex + ey * ey) ** 0.5
        if length < 1e-9:
            continue
        t = max(0.0, min(1.0, ((point[0] - x0) * ex + (point[1] - y0) * ey) / (length * length)))
        px, py = x0 + ex * t, y0 + ey * t
        d = ((point[0] - px) ** 2 + (point[1] - py) ** 2) ** 0.5
        if d < best_d:
            best_s, best_d = s + t * length, d
        s += length
    return best_s, best_d


def point_at(ring: list, s: float) -> tuple[float, float]:
    total = 0.0
    for index in range(len(ring)):
        (x0, y0), (x1, y1) = ring[index], ring[(index + 1) % len(ring)]
        length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if total + length >= s or index == len(ring) - 1:
            t = 0.0 if length < 1e-9 else (s - total) / length
            return (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
        total += length
    return ring[0]


def cyclic_span(offsets: list[float], perimeter: float) -> list[tuple[float, float]]:
    """The shortest arc of a closed ring covering ``offsets``, as 1 or 2 linear intervals.

    The covered arc is the complement of the LARGEST gap between consecutive offsets, taken
    cyclically. Where that arc crosses the ring's seam it comes back as two intervals, which
    is what every caller wants anyway — they are merged into a flat list of breaks.
    """
    if not offsets:
        return []
    if len(offsets) == 1 or perimeter <= 0:
        return [(offsets[0], offsets[0])]
    gaps = [(offsets[i + 1] - offsets[i], i) for i in range(len(offsets) - 1)]
    gaps.append((perimeter - offsets[-1] + offsets[0], len(offsets) - 1))
    _, widest = max(gaps)
    start = offsets[(widest + 1) % len(offsets)]
    end = offsets[widest]
    if start <= end:
        return [(start, end)]
    return [(start, perimeter), (0.0, end)]


def merged_intervals(intervals: list[tuple[float, float]],
                     perimeter: float) -> list[tuple[float, float]]:
    """Clamp the breaks to the ring, sort them, and union any that overlap.

    Pairing each break's end with the next break's start only describes the space between
    them while the breaks are disjoint: a doorway opening straight onto a stair well would
    otherwise manufacture a negative-length stretch between the two.
    """
    return _merge_intervals([(max(0.0, a), min(perimeter, b)) for a, b in intervals])


def door_intervals(model, ring: list, storey_tag: str,
                   half_width: Callable[[object], float | None] | None = None,
                   hosts: set[str] | None = None) -> list[tuple[float, float]]:
    """Perimeter intervals occupied by door openings on walls near this ring.

    ``half_width(opening)`` widens or narrows the break (a casing past the rough opening, a
    bookcase door's factory frame); ``None`` from it skips the door. ``hosts`` limits the
    doors to those walls. Default: the rough opening on any wall within ``NEAR_WALL_M``.
    """
    walls = {w.tag: w for w in model.walls if w.storey == storey_tag}
    intervals = []
    for opening in model.openings:
        if not opening.is_door:
            continue
        host = walls.get(opening.host_wall)
        if host is None or (hosts is not None and host.tag not in hosts):
            continue
        center = opening_center(host, opening) or host.axis[0]
        s, d = perimeter_position(ring, center)
        if d <= NEAR_WALL_M:
            half = opening.width_m / 2.0 if half_width is None else half_width(opening)
            if half is not None:
                intervals.append((s - half, s + half))
    return intervals


def fronting_intervals(ring: list, polygons: Iterable, reach_m: float
                       ) -> list[tuple[float, float]]:
    """Perimeter intervals lying within ``reach_m`` of any of ``polygons``.

    Intersected rather than projected, so a box standing near a corner breaks only the wall
    it actually fronts, never the one it merely faces.
    """
    from shapely.geometry import LineString, Point

    boundary = LineString(list(ring) + [ring[0]])
    intervals: list[tuple[float, float]] = []
    for polygon in polygons:
        if not polygon.is_valid or polygon.is_empty:
            continue
        fronting = boundary.intersection(polygon.buffer(reach_m))
        for piece in getattr(fronting, "geoms", (fronting,)):
            if piece.is_empty or piece.length <= 0:
                continue
            # Cyclic: a piece crossing the ring's seam projects near 0 AND near the full
            # length, and min..max would then swallow the whole room.
            offsets = sorted(boundary.project(Point(coord)) for coord in piece.coords)
            intervals.extend(cyclic_span(offsets, boundary.length))
    return intervals


def floor_opening_intervals(plan, ring: list, storey_tag: str,
                            ledge_m: float) -> list[tuple[float, float]]:
    """Perimeter intervals where the boundary fronts a floor opening rather than floor.

    A chase is boxed and decked over — there is floor on it, so it breaks nothing. Only an
    opening you could step into takes the floor line away. ``ledge_m`` is how much floor may
    survive between the well edge and the wall face and still count as floor.
    """
    from shapely.geometry import Polygon

    wells = [Polygon([point.xy_m for point in element.outline])
             for element in plan.storey_elements(storey_tag)
             if element.element_kind == "FloorOpening" and element.purpose.value != "chase"]
    return fronting_intervals(ring, wells, ledge_m)


def fixed_cabinet_intervals(model, plan, ring: list, storey_tag: str,
                            include: Callable[[object], bool]) -> list[tuple[float, float]]:
    """Perimeter intervals occupied by floor-standing cabinets whose type ``include`` admits.

    The predicate is the caller's: NEC wall space breaks only at counterless cabinets, a
    base run at every fixed one. A carcass counts when it stands in this room (its centroid
    is inside the ring), within ``NEAR_WALL_M`` of the boundary, and within
    ``FLOOR_CONTACT_M`` of the storey floor.
    """
    from shapely.geometry import LineString, Point, Polygon

    boundary = LineString(list(ring) + [ring[0]])
    room_area = Polygon(ring)
    floor_z = next((s.elevation.meters for s in plan.storeys if s.tag == storey_tag), 0.0)
    types = {t.tag: t for t in plan.library.furniture_types}
    intervals: list[tuple[float, float]] = []
    for item in model.canvas_objects:
        if item.storey != storey_tag or item.type_ref is None:
            continue
        item_type = types.get(item.type_ref)
        if item_type is None or not include(item_type):
            continue
        # An upper cabinet is also a fixed cabinet, but it does not reach the floor line.
        if item.z_m - floor_z > FLOOR_CONTACT_M:
            continue
        carcass = Polygon(item.footprint)
        if not carcass.is_valid or carcass.is_empty:
            continue
        if carcass.distance(boundary) > NEAR_WALL_M:
            continue
        # NEAR_WALL_M reaches through a partition: a closet frame behind the wall is not
        # this room's cabinet. Ownership by geometry: the carcass stands in this room.
        if not room_area.contains(carcass.centroid):
            continue
        # Projected rather than buffered: a buffer wide enough to reach the boundary would
        # also run that far past each end of the carcass and swallow the wall either side.
        #
        # ** THE ARC IS CHOSEN CYCLICALLY, NOT AS min..max. ** A cabinet on the wall holding
        # the ring's START projects some corners near 0 and the rest near the full length;
        # min..max then reports the interval the cabinet does NOT occupy (catlin's attic
        # studio: a 21'-8" plinth claimed 57 ft of an 80 ft ring and hid an 11 ft gap).
        offsets = sorted(boundary.project(Point(coord))
                         for coord in carcass.exterior.coords)
        intervals.extend(cyclic_span(offsets, boundary.length))
    return intervals
