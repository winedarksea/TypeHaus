"""General plan-polygon triangulation for the prisms a fan cannot fill.

``_MeshBuilder.add_prism`` fans from vertex 0, which is exact only when every fan triangle is
counter-clockwise; the rectangle-strip path cuts only axis-aligned holes. Everything else — a
concave L/U outline, a round planting void, a polygon hole in the earth sheet — comes here and
is cut with ``shapely.constrained_delaunay_triangles`` (Shapely >= 2.1, GEOS >= 3.10).

Pyodide 0.26.2 ships Shapely 2.0.2 without it (``resolve/overlay.py``); there ``HAS_CDT`` is
False and callers keep their legacy fan / hole-less prism rather than fail.
"""

from __future__ import annotations

from collections.abc import Sequence

import shapely
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from typehaus.resolve.overlay import difference, union_all

HAS_CDT = hasattr(shapely, "constrained_delaunay_triangles")

_FAN_EPS_M2 = 1e-12  # a collinear vertex makes a zero-area fan triangle, which is harmless

XY = tuple[float, float]


def fan_is_exact(ring: list[XY]) -> bool:
    """Does a fan from ``ring[0]`` tile this CCW ring exactly?

    Signed fan areas always sum to the polygon's; if none is negative no point is covered
    twice or missed, so the fan is a true triangulation (true of every convex ring).
    """
    x0, y0 = ring[0]
    for (x1, y1), (x2, y2) in zip(ring[1:-1], ring[2:], strict=False):
        if (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0) < -_FAN_EPS_M2:
            return False
    return True


def polygon_parts(ring: Sequence[XY], voids: Sequence[Sequence[XY]] = ()) -> list[Polygon]:
    """``ring`` minus every void, as oriented polygons (shell CCW, holes CW).

    A void may overlap another or cross the outline (a notch); the overlay resolves both.
    Empty when the ring is not a usable polygon, so the caller can fall back.
    """
    shell = Polygon(ring)
    if not shell.is_valid or shell.area <= 0.0:
        return []
    cut = [Polygon(v) for v in voids if len(v) >= 3]
    cut = [p if p.is_valid else shapely.make_valid(p) for p in cut]
    geom = difference(shell, union_all(cut)) if cut else shell
    parts = getattr(geom, "geoms", [geom])
    return [orient(p, sign=1.0) for p in parts
            if p.geom_type == "Polygon" and p.area > 0.0]


def triangles(polygon: Polygon) -> list[tuple[XY, XY, XY]]:
    """The polygon's constrained Delaunay triangles, each counter-clockwise in plan."""
    out = []
    for tri in shapely.constrained_delaunay_triangles(polygon).geoms:
        a, b, c = tri.exterior.coords[:3]
        if (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]) < 0:
            b, c = c, b
        out.append((a, b, c))
    return out
