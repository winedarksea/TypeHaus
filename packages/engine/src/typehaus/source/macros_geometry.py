"""Pure plan-frame geometry primitives for the macro layer — no PlanModel, no PatchOps.

Split out of :mod:`typehaus.source.macros` so the macro modules that need a distance, a
projection, or a containment test share one implementation instead of three. Nothing here
knows what a macro is; the only model import is for the two element types ``_collinear``
reads. That is deliberate: these belong in ``resolve/geometry.py`` eventually, and keeping
them free of macro imports is what will make that move a rename.
"""

from __future__ import annotations

from typehaus.model.elements import Node, Wall

# Collinearity tolerance for heal/merge (cross-product of unit axes), dimensionless.
COLLINEAR_TOL = 1e-3


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    """Even-odd ray cast; polygon is a list of (x_m, y_m) in the plan frame."""
    x, y = point
    inside = False
    n = len(polygon)
    for i in range(n):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            x_cross = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < x_cross:
                inside = not inside
    return inside


def _dist(p: tuple[float, float], q: tuple[float, float]) -> float:
    return ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5


def _project_param(
    a: tuple[float, float], b: tuple[float, float], p: tuple[float, float]
) -> float:
    abx, aby = b[0] - a[0], b[1] - a[1]
    denom = abx * abx + aby * aby
    if denom == 0:
        return 0.0
    return ((p[0] - a[0]) * abx + (p[1] - a[1]) * aby) / denom


def _collinear(w1: Wall, w2: Wall, shared: str, by_tag: dict[str, Node]) -> bool:
    def other(w: Wall) -> str:
        return w.end_node if w.start_node == shared else w.start_node

    s = by_tag.get(shared)
    e1, e2 = by_tag.get(other(w1)), by_tag.get(other(w2))
    if s is None or e1 is None or e2 is None:
        return False
    (sx, sy) = s.position.xy_m
    v1 = (e1.position.xy_m[0] - sx, e1.position.xy_m[1] - sy)
    v2 = (e2.position.xy_m[0] - sx, e2.position.xy_m[1] - sy)
    l1 = (v1[0] ** 2 + v1[1] ** 2) ** 0.5
    l2 = (v2[0] ** 2 + v2[1] ** 2) ** 0.5
    if l1 == 0 or l2 == 0:
        return False
    cross = (v1[0] * v2[1] - v1[1] * v2[0]) / (l1 * l2)
    return abs(cross) < COLLINEAR_TOL
