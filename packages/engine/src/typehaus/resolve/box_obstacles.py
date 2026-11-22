"""Level and raked wall members a nail-on box must seat clear of, and the ones it cuts.

A backing band, liner furring or resilient channel is cut round a box
(``resolve/box_cuts.py``), so it never moves one. Any other member that is not upright (a
raked plate, a tee block, a door block) is an obstacle over the stations where it crosses
the box's band and depth.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_members import member_box

Point = tuple[float, float]
_TOL_M = 0.125 * M_PER_IN


def cut_at_boxes(member: Any) -> bool:
    """A backing band or strapping (liner furring, resilient channel): cut, never seated on."""
    return member.child_key.startswith("backing-") or member.category == "strapping"


def _span(points: list[Point], axis: Point, origin: Point = (0.0, 0.0)) -> tuple[float, float]:
    values = [(x - origin[0]) * axis[0] + (y - origin[1]) * axis[1] for x, y in points]
    return min(values), max(values)


def _band_t(member: Any, z0: float, z1: float) -> tuple[float, float] | None:
    """The member's parameter range whose section overlaps the band ``z0..z1``."""
    lo_a, hi_a = member.z0_m, member.z1_m
    lo_b = member.z0_end_m if member.z0_end_m is not None else lo_a
    hi_b = member.z1_end_m if member.z1_end_m is not None else hi_a
    t0, t1 = 0.0, 1.0
    # bottom(t) < z1 - tol and top(t) > z0 + tol, each linear in t.
    for a, b, bound, below in ((lo_a, lo_b, z1 - _TOL_M, True), (hi_a, hi_b, z0 + _TOL_M, False)):
        slope = b - a
        if abs(slope) < 1e-12:
            if (a >= bound) if below else (a <= bound):
                return None
            continue
        t = (bound - a) / slope
        if (slope > 0) == below:
            t1 = min(t1, t)
        else:
            t0 = max(t0, t)
    return (t0, t1) if t1 > t0 else None


def level_obstacles(wall: Any, face_point: Point, tangent: Point, normal: Point,
                    z0: float, z1: float, depth: float) -> list[tuple[float, float]]:
    """Station spans along ``tangent`` of the non-upright members a box must clear."""
    spans = []
    for member in wall.members:
        if member.p0 == member.p1 or member.plan_outline is not None or cut_at_boxes(member):
            continue
        band = _band_t(member, z0, z1)
        if band is None:
            continue
        solid = member_box(member)
        if solid is None:
            continue
        ring = [(x, y) for x, y, _z in solid.corners_bottom]
        n_lo, n_hi = _span(ring, normal, face_point)
        if min(n_hi, 0.0) - max(n_lo, -depth) <= _TOL_M:
            continue
        (ax, ay), (bx, by) = member.p0, member.p1
        run = math.hypot(bx - ax, by - ay)
        if abs(((bx - ax) * tangent[0] + (by - ay) * tangent[1]) / run) < 0.99:
            spans.append(_span(ring, tangent))  # across the wall: its own thickness
            continue
        ends = [(ax + (bx - ax) * t, ay + (by - ay) * t) for t in band]
        spans.append(_span(ends, tangent))
    return spans
