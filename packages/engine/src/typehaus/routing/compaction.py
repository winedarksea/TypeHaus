"""A short Z-jog redrawn as a 45-degree pair, after the search — the way a plumber draws it.

The lattice is orthogonal, which is what keeps the Manhattan heuristic admissible; a
diagonal edge would break it. So a route that steps sideways a few inches and carries on
comes back as two 90s, and a plumber lays two 45s: one less sweep each, and shorter. Each
level jog whose middle leg is under ``RouteCost.offset_jog_max_in``, between two legs
running the same way, is rewritten as a pair, ``B' = B - u j/2`` and ``C' = C + u j/2``, so
the diagonal makes ``j`` along and ``j`` across. ``accept`` re-grades the candidate
(obstacles, slope, member windows); a pair that fails keeps its jog.
``houses/catlin/notes/mep_drain_routing_basis.md`` §10 works one by hand.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

Point = tuple[float, float, float]

#: Plan lengths under this are one point.
_TOL_M = 0.0015875


def compact_offsets(points: Sequence[Point], max_jog_m: float,
                    accept: Callable[[list[Point], int], bool]) -> tuple[list[Point], int]:
    """``(points, pairs made)``. ``accept(candidate, i)`` grades a pair at vertex ``i``."""
    out = list(points)
    made = 0
    i = 1
    while i + 2 < len(out):
        a, b, c, d = out[i - 1], out[i], out[i + 1], out[i + 2]
        jog = _jog(a, b, c, d, max_jog_m)
        if jog is None:
            i += 1
            continue
        ux, uy, half = jog
        candidate = [*out[:i], (b[0] - ux * half, b[1] - uy * half, b[2]),
                     (c[0] + ux * half, c[1] + uy * half, c[2]), *out[i + 2:]]
        if accept(candidate, i):
            out = candidate
            made += 1
            i += 2
        else:
            i += 1
    return out, made


def _jog(a: Point, b: Point, c: Point, d: Point,
         max_jog_m: float) -> tuple[float, float, float] | None:
    """``(ux, uy, j/2)`` when ``a-b-c-d`` is a short level jog between parallel legs."""
    first, middle, last = _plan(a, b), _plan(b, c), _plan(c, d)
    if None in (first, middle, last):
        return None
    (fx, fy, fl), (mx, my, ml), (lx, ly, ll) = first, middle, last
    if abs(b[2] - c[2]) > 0.25 * ml + _TOL_M:
        return None  # not a level jog: a drop or a riser is its own fitting
    if ml > max_jog_m or abs(fx * mx + fy * my) > 1e-6 or fx * lx + fy * ly < 1 - 1e-6:
        return None  # not perpendicular, or the legs do not carry on the same way
    half = ml / 2.0
    if fl < half + _TOL_M or ll < half + _TOL_M:
        return None  # a leg too short to give up j/2
    return fx, fy, half


def _plan(a: Point, b: Point) -> tuple[float, float, float] | None:
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    if length < _TOL_M:
        return None
    return (b[0] - a[0]) / length, (b[1] - a[1]) / length, length


def segment_clear(space, model, a: Point, b: Point) -> bool:
    """Whether a diagonal leg meets no prism, cuts no wall member and keeps every window.

    Prisms are already inflated by radius + clearance, so the leg's centreline is tested,
    against each one whose band its own z range enters. A wall member it would cut is a
    refusal (an oblique bore is not a plumber's hole), and a floor crossing must sit inside
    that floor's member window (``resolve/mep_crossings``) — the same readings the checks
    grade.
    """
    from shapely.geometry import LineString, Polygon

    from typehaus.resolve.mep_bore_geometry import leg_crossings as wall_cuts
    from typehaus.resolve.mep_crossings import leg_crossings as floor_crossings
    from typehaus.resolve.mep_crossings import member_window

    line = LineString([a[:2], b[:2]])
    low, high = sorted((a[2], b[2]))
    for prism in (*space.hard, *space.banded):
        if prism.applies is not None or prism.z1_m < low or prism.z0_m > high:
            continue  # an axis-bound wall strip: the members below grade the wall
        if prism.footprint.buffer(-_TOL_M).intersects(line):
            return False
    reach = line.buffer(space.radius_m + 0.1)
    for wall in model.walls:
        if not wall.members or not any(len(ly.polygon) >= 3 and reach.intersects(
                Polygon(ly.polygon)) for ly in wall.layers if ly.function == "structure"):
            continue
        if wall_cuts(wall, a[:2], b[:2], a[2], b[2], space.radius_m):
            return False
    for floor in model.floors:
        window = member_window(floor)
        for crossing in floor_crossings(floor, a[:2], b[:2], a[2], b[2]):
            if window is None or not (window.z0_m + space.radius_m <= crossing.z_m
                                      <= window.z1_m - space.radius_m):
                return False
    return True
