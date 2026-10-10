"""Where a wall-mounted rail meets its wall: the finish face nearest a point, at a height.

One reading for the resolver (brackets, returns) and the checks (R311.7.8.2 clearance,
R311.7.1 projection), so the arm that is drawn and the gap that is graded cannot disagree.

Two things the bracket search used to get wrong, and why this module measures as it does:

* **Storey.** A stair's rails are filed on the storey the stair arrives at, but the wall
  beside the flight belongs to the storey below. Walls are filtered by z, not storey.
* **Face.** The face is read off the wall's layer polygons (``wall_faces.wall_body``), not
  as axis ± thickness/2 — a wall aligned by a face has no layer at its centreline offset.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import Point
from shapely.ops import nearest_points

from typehaus.quantities import inch
from typehaus.resolve.geometry import Vec
from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.resolve.wall_faces import wall_body

#: How far from a rail a wall may be and still be the thing it mounts to.
REACH_M = inch(9).meters
#: |cos| between rail and wall axis above which the wall runs alongside the rail. A wall the
#: rail dies into end-on is not the one it is fastened to, nor the one clearance is to.
_PARALLEL_DOT = 0.9
#: Half-height of the slice the layer bodies are read over.
_SLICE_M = 0.001


@dataclass(frozen=True)
class WallContact:
    """The nearest finish face: which wall, how far, and the point on it."""

    wall_tag: str
    distance_m: float
    face_point: Vec


def nearest_wall_face(model: ResolvedModel, point: Vec, z: float, *,
                      along: tuple[Vec, ...] = (),
                      reach_m: float = REACH_M) -> WallContact | None:
    """The nearest wall finish face to ``point`` at elevation ``z``, within ``reach_m``.

    ``along`` holds the rail's direction(s) at ``point``; when given, only walls parallel to
    one of them count.
    """
    here = Point(point)
    best: WallContact | None = None
    for wall in model.walls:
        if not (wall.z0_m - 1e-6 <= z <= wall.z1_m + 1e-6):
            continue
        if along and not _parallel(wall, along):
            continue
        if _axis_distance(wall, point) > reach_m + wall_half_span(wall):
            continue
        body = wall_body(wall, z - _SLICE_M, z + _SLICE_M)
        if body.is_empty:
            continue
        gap = body.distance(here)
        if gap > reach_m or (best is not None and gap >= best.distance_m):
            continue
        face = nearest_points(body, here)[0]
        best = WallContact(wall.tag, gap, (face.x, face.y))
    return best


def wall_half_span(wall: ResolvedWall) -> float:
    """How far the layer stack may sit from the axis — the full thickness, either way."""
    return sum(layer.thickness_m for layer in wall.layers) if wall.layers else 0.0


def _parallel(wall: ResolvedWall, along: tuple[Vec, ...]) -> bool:
    (x0, y0), (x1, y1) = wall.axis
    run = math.hypot(x1 - x0, y1 - y0)
    if run < 1e-9:
        return False
    ux, uy = (x1 - x0) / run, (y1 - y0) / run
    for dx, dy in along:
        d = math.hypot(dx, dy)
        if d > 1e-9 and abs(ux * dx + uy * dy) / d >= _PARALLEL_DOT:
            return True
    return False


def _axis_distance(wall: ResolvedWall, point: Vec) -> float:
    (x0, y0), (x1, y1) = wall.axis
    dx, dy = x1 - x0, y1 - y0
    run2 = dx * dx + dy * dy
    if run2 < 1e-18:
        return math.hypot(point[0] - x0, point[1] - y0)
    t = max(0.0, min(1.0, ((point[0] - x0) * dx + (point[1] - y0) * dy) / run2))
    return math.hypot(point[0] - (x0 + dx * t), point[1] - (y0 + dy * t))
