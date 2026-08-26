"""Version-robust GEOS overlay wrappers.

GEOS's noder is not equally forgiving across versions, and the engine runs on two of them:
``.venv`` carries Shapely 2.1.2 / GEOS 3.13.1, while the published web app runs the engine
under Pyodide 0.26.2, whose Shapely is 2.0.2 / **GEOS 3.12.1**
(``ui/src/engine/pyodide/worker.ts``). GEOS 3.13 hardened OverlayNG's noding; 3.12 raises
``TopologyException: found non-noded intersection`` on inputs 3.13 absorbs — including the
mitred basement corner at the NW node of ``houses/catlin``, where unioning the wall bodies
made 3.12's noder manufacture a zero-length ``LINESTRING (A, A)`` out of rings that carry no
duplicate vertex of their own. The house is fine; the noder is not.

The cure is to give the overlay an explicit fixed-precision grid, which routes GEOS through
its snap-rounding noder instead of the floating-point one. ``grid_size`` needs only
GEOS >= 3.9, so it works on both stacks, and one micron is 4e-5 in — orders of magnitude
below any modelling tolerance. It is measured to be free on this model: unioning the wall
layer polygons of every catlin storey gives the same area with and without the grid to
within 6e-14 m2.

Do **not** reach for ``buffer(0)`` instead: it silently drops slivers, and a wall layer
losing a sliver is a takeoff error.
"""

from __future__ import annotations

from typing import Any

import shapely
from shapely.geometry import GeometryCollection

#: One micron, in meters. See the module docstring for why this is safe.
GRID_SIZE_M = 1e-6


def union_all(geometries: Any) -> Any:
    """``unary_union`` on a fixed-precision grid — safe on GEOS 3.12 as well as 3.13."""
    items = list(geometries)
    if not items:
        return GeometryCollection()
    return shapely.union_all(items, grid_size=GRID_SIZE_M)


def difference(geometry: Any, other: Any) -> Any:
    """``a.difference(b)`` on the same fixed-precision grid as :func:`union_all`."""
    return shapely.difference(geometry, other, grid_size=GRID_SIZE_M)


def intersection(geometry: Any, other: Any) -> Any:
    """``a.intersection(b)`` on the same fixed-precision grid as :func:`union_all`."""
    return shapely.intersection(geometry, other, grid_size=GRID_SIZE_M)
