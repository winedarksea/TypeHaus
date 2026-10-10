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
    out: list[tuple[ResolvedWall, tuple[float, float]]] = []
    for wall, segment in _shared_segments(model, room, Polygon(room.clear_face).exterior):
        axis = LineString(wall.axis)
        stations = [axis.project(Point(c)) for c in segment.coords]
        lo, hi = min(stations), max(stations)
        if hi - lo > _MIN_RUN_M:
            out.append((wall, (lo, hi)))
    return out


def bounding_wall_arcs(
    model: ResolvedModel, room: ResolvedRoom, ring: list, body_of=None
) -> list[tuple[ResolvedWall, tuple[float, float]]]:
    """As :func:`bounding_walls`, but each shared run as an arc ``(s0, s1)`` along ``ring``.

    ``ring`` is the caller's copy of the room's clear face (its orientation and start are
    the caller's), and ``s`` is metres along it. An arc crossing the ring's seam comes back
    as two. Each arc reaches ``_TOUCH_M`` past the run's true ends, round a corner.
    ``body_of(wall)`` lets a caller asking for many rooms reuse its wall bodies.
    """
    from typehaus.resolve.room_perimeter import cyclic_span

    if len(ring) < 3:
        return []
    boundary = LineString(list(ring) + [ring[0]])
    out: list[tuple[ResolvedWall, tuple[float, float]]] = []
    for wall, segment in _shared_segments(model, room, boundary, body_of):
        if segment.length <= _MIN_RUN_M:
            continue
        offsets = sorted(boundary.project(Point(c)) for c in segment.coords)
        out.extend((wall, span) for span in cyclic_span(offsets, boundary.length))
    return out


def _shared_segments(model: ResolvedModel, room: ResolvedRoom, edge, body_of=None):
    """``(wall, LineString)`` for each stretch of ``edge`` lying on a wall's layer body."""
    face = Polygon(room.clear_face)
    for wall in model.walls:
        if wall.storey != room.storey:
            continue
        axis = LineString(wall.axis)
        if axis.length <= 0.0:
            continue
        if getattr(wall, "layers", None):
            body = (body_of(wall) if body_of is not None
                    else wall_body(wall, wall.z0_m, wall.z1_m))
        else:  # a layerless stand-in: its axis at its stated thickness
            body = axis.buffer(getattr(wall, "thickness_m", 0.0) / 2.0, cap_style="flat")
        if body.is_empty or body.distance(face) > _TOUCH_M:
            continue
        shared = edge.intersection(body.buffer(_TOUCH_M))
        if shared.geom_type == "MultiLineString":
            shared = linemerge(shared)  # rejoin a run the ring's start point split
        for segment in getattr(shared, "geoms", (shared,)):
            if segment.geom_type == "LineString" and segment.length > 0.0:
                yield wall, segment
