"""The published web app runs an older GEOS than ``.venv``; overlays must survive both.

``ui/src/engine/pyodide/worker.ts`` pins Pyodide 0.26.2, whose Shapely is **2.0.2 / GEOS
3.12.1**, while the dev venv carries Shapely 2.1.2 / GEOS 3.13.1. GEOS 3.13 hardened
OverlayNG's noding, so 3.12 raised

    TopologyException: found non-noded intersection between
    LINESTRING (-0.05207 11.0249, -0.10287 11.0757) and
    LINESTRING (-0.10287 11.0757, -0.10287 11.0757)

while unioning the basement wall bodies for ``gross_area_sf`` — a *fatal* Pyodide error that
killed the worker, so the app never rendered. The degenerate ``LINESTRING (A, A)`` is
manufactured by 3.12's own floating-point noder: the input rings (the mitred ``xps-b`` bands
of ``W-B-N3`` and ``W-B-W1`` at the NW corner) carry no duplicate vertex, and this file
asserts that.

None of this reproduces on GEOS 3.13.1, which is exactly why it shipped green. So the tests
here guard the *fix* rather than the throw: that the overlay goes through the fixed-precision
helper, and that the grid costs nothing.
"""

from __future__ import annotations

import inspect

import pytest
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

from typehaus.resolve import overlay
from typehaus.server import space_summary

# The two mitred ``xps-b`` bands at the NW basement corner of ``houses/catlin``, verbatim from
# the resolved model. Their shared 45-degree edge is what GEOS 3.12 could not node.
NW_CORNER_BANDS = (
    [(-0.10287, 11.07567), (3.048, 11.07567), (3.048, 11.02487), (-0.05207, 11.02487)],
    [(-0.10287, 5.4864), (-0.10287, 11.07567), (-0.05207, 11.02487), (-0.05207, 5.4864)],
)


def test_grid_size_is_a_micron() -> None:
    """One micron is 4e-5 in — below any modelling tolerance, and enough for the noder."""
    assert overlay.GRID_SIZE_M == 1e-6


def test_union_all_of_nothing_is_empty() -> None:
    assert overlay.union_all([]).is_empty


def test_nw_corner_bands_carry_no_duplicate_vertex() -> None:
    """The house is not the problem — pin that, so a future reader does not go hunting."""
    for ring in NW_CORNER_BANDS:
        for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
            assert (a[0], a[1]) != (b[0], b[1])
        assert Polygon(ring).is_valid


def test_nw_corner_bands_union_to_one_valid_polygon() -> None:
    merged = overlay.union_all([Polygon(ring) for ring in NW_CORNER_BANDS])
    assert merged.geom_type == "Polygon"
    assert merged.is_valid
    plain = unary_union([Polygon(ring) for ring in NW_CORNER_BANDS])
    assert merged.area == pytest.approx(plain.area, abs=1e-12)


def test_gross_area_goes_through_the_robust_overlay() -> None:
    """The regression guard.

    A bare ``shapely.ops.unary_union`` here is invisible on GEOS 3.13.1 and fatal on 3.12,
    so no runtime assertion in this venv can catch a revert. Read the source instead.
    """
    source = inspect.getsource(space_summary._exterior_shells_by_storey)
    code = "\n".join(line for line in source.splitlines()
                     if not line.lstrip().startswith("#"))
    assert "typehaus.resolve.overlay import union_all" in code
    assert "unary_union" not in code


def test_the_grid_is_free_on_every_catlin_storey(catlin_model) -> None:
    """Snap-rounding must not move a single reported square foot."""
    per_storey: dict[str, list[Polygon]] = {}
    for wall in catlin_model.walls:
        for layer in wall.layers:
            if layer.polygon and len(layer.polygon) >= 3:
                per_storey.setdefault(wall.storey, []).append(Polygon(layer.polygon))
    assert per_storey, "no wall bodies to union"
    for storey, bodies in per_storey.items():
        buffed = [body.buffer(0) for body in bodies]
        gridded = shapely.union_all(buffed, grid_size=overlay.GRID_SIZE_M).area
        plain = unary_union(buffed).area
        # One square millimetre. Snap-rounding to a micron grid can move a vertex by up to
        # half a micron, so over ~900 polygons per storey the areas differ in the 8th
        # decimal place of a square metre — 1e-8 m2 is 1e-7 sq ft, and the takeoff rounds
        # to 0.1 sq ft. A mm2 is still four orders of magnitude below anything that could
        # change a reported number, so this stays a real assertion and not a rubber stamp.
        assert gridded == pytest.approx(plain, abs=1e-6), storey


def test_no_resolved_layer_ring_has_consecutive_duplicate_vertices(catlin_model) -> None:
    """The whole-model sweep: a zero-length edge in a wall band is a noder trap anywhere."""
    offenders = []
    for wall in catlin_model.walls:
        for index, layer in enumerate(wall.layers):
            ring = list(layer.polygon)
            if len(ring) < 2:
                continue
            for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
                if abs(a[0] - b[0]) <= 1e-9 and abs(a[1] - b[1]) <= 1e-9:
                    offenders.append((wall.tag, index, a))
                    break
    assert not offenders
