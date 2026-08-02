"""Which walls bound a room, and over what run — the room→wall query, derived once.

No authored relation ties a Room to its walls (rooms claim a polygonized face by seed;
walls only know their nodes), so every consumer that needed the answer has re-derived it
with its own shapely probe and its own slop — ``fire_separation._separating_walls``,
``_wall_is_exterior``, ``energy._stands_between_conditioned_rooms``. This module hosts the
predicate for new consumers (``resolve/paneling.py`` first): a wall bounds a room when its
axis lies within half its own thickness (plus slop) of the room's face, and the *shared
run* is the axis clipped to that neighbourhood — so a long wall that borders the room for
only part of its length contributes only that part.

The existing probes are left in place; migrating them is worthwhile but separate.
"""

from __future__ import annotations

from shapely.geometry import LineString, Point, Polygon

from typehaus.resolve.model import ResolvedModel, ResolvedRoom, ResolvedWall

# Generous enough to absorb the clear-face lining inset (a uniform approximation,
# resolve/rooms.py::_lining_inset) plus polygonize jitter; small enough not to claim the
# parallel wall one stud bay over.
_BOUNDING_SLOP_M = 0.08
# Extra clip margin past the wall's own offset when deriving the shared run. Small on
# purpose: at offset d the clip disk reaches only ~sqrt(2·d·slop) past a face corner
# (about an inch), where clipping at the membership reach ran ~5" past every corner.
_CLIP_SLOP_M = 0.02
# Shared runs shorter than this are corner artifacts — the ~1" of a collinear neighbour
# wall the clip disk still catches past a face corner — not walls a finish runs along.
_MIN_RUN_M = 0.05


def bounding_walls(
    model: ResolvedModel, room: ResolvedRoom
) -> list[tuple[ResolvedWall, tuple[float, float]]]:
    """Walls sharing a face with ``room``, each with its shared (u0, u1) axis interval.

    Intervals are metres along the wall axis from its start node. A wall bordering the
    room in disjoint stretches (a T-junction splitting its far side) yields one entry per
    stretch. Order follows ``model.walls``.
    """
    if len(room.clear_face) < 3:
        return []
    face = Polygon(room.clear_face)
    out: list[tuple[ResolvedWall, tuple[float, float]]] = []
    for wall in model.walls:
        if wall.storey != room.storey:
            continue
        axis = LineString(wall.axis)
        if axis.length <= 0.0:
            continue
        reach = wall.thickness_m / 2.0 + _BOUNDING_SLOP_M
        offset = axis.distance(face)
        if offset > reach:
            continue
        # Clip with the wall's *actual* offset from the face (its half-thickness-ish
        # lining inset), not the membership reach: clipping with the full reach ran every
        # interval ~reach past each corner and picked up stub runs from collinear
        # neighbour walls, inflating a wainscot's perimeter by a couple of lineal feet.
        shared = axis.intersection(face.buffer(offset + _CLIP_SLOP_M))
        segments = (
            shared.geoms if shared.geom_type in ("MultiLineString", "GeometryCollection")
            else (shared,)
        )
        for segment in segments:
            if segment.geom_type != "LineString" or segment.length <= 0.0:
                continue
            coords = list(segment.coords)
            u0 = axis.project(Point(coords[0]))
            u1 = axis.project(Point(coords[-1]))
            lo, hi = sorted((u0, u1))
            if hi - lo > _MIN_RUN_M:
                out.append((wall, (lo, hi)))
    return out
