"""Which walls bound a room, and over what run — the room→wall query, derived once.

No authored relation ties a Room to its walls (rooms claim a polygonized face by seed;
walls only know their nodes). A wall bounds a room when its own layer body
(:func:`~typehaus.resolve.wall_faces.wall_body`) touches the room's clear face — which
is the finish face, so the two meet within float noise — and the *shared run* is the
clear-face boundary lying on that body, projected onto the wall axis.
"""

from __future__ import annotations

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import linemerge

from typehaus.resolve.model import ResolvedModel, ResolvedRoom, ResolvedWall
from typehaus.resolve.wall_faces import wall_body

# A clear face is cut from the wall bodies, so a bounding body touches it to float noise;
# 1 cm is the plan's stated tolerance and far short of the next wall over.
_TOUCH_M = 0.01
# Shared runs shorter than this are corner artifacts — the 1 cm of a perpendicular
# neighbour's face the touch band catches — not walls a finish runs along.
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
    edge = face.exterior
    out: list[tuple[ResolvedWall, tuple[float, float]]] = []
    for wall in model.walls:
        if wall.storey != room.storey:
            continue
        axis = LineString(wall.axis)
        if axis.length <= 0.0:
            continue
        if getattr(wall, "layers", None):
            body = wall_body(wall, wall.z0_m, wall.z1_m)
        else:  # a layerless stand-in: its axis at its stated thickness
            body = axis.buffer(getattr(wall, "thickness_m", 0.0) / 2.0, cap_style="flat")
        if body.is_empty or body.distance(face) > _TOUCH_M:
            continue
        shared = edge.intersection(body.buffer(_TOUCH_M))
        if shared.geom_type == "MultiLineString":
            shared = linemerge(shared)  # rejoin a run the ring's start point split
        segments = getattr(shared, "geoms", (shared,))
        for segment in segments:
            if segment.geom_type != "LineString" or segment.length <= 0.0:
                continue
            stations = [axis.project(Point(c)) for c in segment.coords]
            lo, hi = min(stations), max(stations)
            if hi - lo > _MIN_RUN_M:
                out.append((wall, (lo, hi)))
    return out
