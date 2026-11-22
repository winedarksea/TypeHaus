"""Drop a near-fitting hanger whose strap would pass through another duct, when that fitting
is already held: the leg beyond it is hung within ``support_near_fitting`` by a clear strap.

SMACNA asks for a support within 2 ft of each fitting, not one on each side of it. Nothing
else moves: a clashing strap whose end is not held stays, for the clash audit to report.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.sweep import clean_path

Point3 = tuple[float, float, float]
Segment = tuple[Point3, Point3]

#: A strap leg must stand this far off another duct's surface.
STRAP_CLEARANCE_M = 0.25 * M_PER_IN
_SLOP_M = 1e-4


def other_ducts(model: Any) -> list[tuple[str, list[Segment], float]]:
    """(tag, centreline segments, radius) per duct; a rectangle's radius is its half-diagonal."""
    out = []
    for duct in model.ducts:
        if len(duct.path) < 2 or len(duct.z_m) != len(duct.path):
            continue
        path = clean_path([(x, y, z) for (x, y), z in zip(duct.path, duct.z_m, strict=True)])
        radius = (duct.diameter_m / 2.0 if duct.diameter_m is not None
                  else math.hypot(duct.width_m, duct.depth_m) / 2.0)
        out.append((duct.tag, list(zip(path, path[1:], strict=False)), radius))
    return out


def end_is_held(duct: Any, legs: list[Segment], per_leg: list[list[Point3]], i: int, k: int,
                near: float, over: Callable, others: list) -> bool:
    """Whether leg ``i``'s end station ``k`` clashes and the next hung leg holds its fitting."""
    def clashes(leg: int, point: Point3) -> bool:
        _, drop = over(point[:2], point[2] + duct.depth_m / 2.0)
        return strap_clashes(point, *legs[leg], duct, point[2] + duct.depth_m / 2.0 + drop,
                             others)

    pts = per_leg[i]
    if len(pts) < 2 or k not in (0, len(pts) - 1) or not clashes(i, pts[k]):
        return False
    j, end = (i - 1, legs[i][0]) if k == 0 else (i + 1, legs[i][1])
    if not 0 <= j < len(legs) or not per_leg[j]:
        return False
    q = min(per_leg[j], key=lambda p: math.dist(p, end))
    return math.dist(q, end) <= near + _SLOP_M and not clashes(j, q)


def strap_clashes(point: Point3, a: Point3, b: Point3, duct: Any, top_z: float,
                  others: list[tuple[str, list[Segment], float]]) -> bool:
    """Whether either vertical strap leg at ``point`` comes within reach of another duct."""
    plan = math.dist(a[:2], b[:2])
    across = ((b[1] - a[1]) / plan, -(b[0] - a[0]) / plan)
    half = duct.width_m / 2.0
    legs = [((point[0] + s * half * across[0], point[1] + s * half * across[1], point[2]),
             (point[0] + s * half * across[0], point[1] + s * half * across[1], top_z))
            for s in (-1.0, 1.0)]
    for tag, segments, radius in others:
        if tag == duct.tag:
            continue
        reach = radius + STRAP_CLEARANCE_M
        if any(_seg_dist(leg, seg) < reach for leg in legs for seg in segments):
            return True
    return False


def _seg_dist(p: Segment, q: Segment) -> float:
    """Closest distance between two 3D segments."""
    (p0, p1), (q0, q1) = p, q
    d1 = [p1[i] - p0[i] for i in range(3)]
    d2 = [q1[i] - q0[i] for i in range(3)]
    r = [p0[i] - q0[i] for i in range(3)]
    a, e, f = _dot(d1, d1), _dot(d2, d2), _dot(d2, r)
    if a <= 1e-12 and e <= 1e-12:
        return math.dist(p0, q0)
    if a <= 1e-12:
        s, t = 0.0, min(max(f / e, 0.0), 1.0)
    else:
        c = _dot(d1, r)
        if e <= 1e-12:
            s, t = min(max(-c / a, 0.0), 1.0), 0.0
        else:
            b = _dot(d1, d2)
            denom = a * e - b * b
            s = min(max((b * f - c * e) / denom, 0.0), 1.0) if denom > 1e-12 else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                s, t = min(max(-c / a, 0.0), 1.0), 0.0
            elif t > 1.0:
                s, t = min(max((b - c) / a, 0.0), 1.0), 1.0
    return math.dist([p0[i] + d1[i] * s for i in range(3)],
                     [q0[i] + d2[i] * t for i in range(3)])


def _dot(u: list[float], v: list[float]) -> float:
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]
