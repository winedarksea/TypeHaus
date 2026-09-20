"""A wall penetration is cut at the same station in every layer of the wall.

``geometry_walls.layer_solids`` slices each layer's own thin-rectangle edge, and an
opening's station is an absolute distance along the WALL axis. A layer mitred at a corner
neither starts nor ends where the axis does, so mapping the station as a fraction of the
axis length put the cut somewhere else in every layer — by inches, differently per layer.

Two consequences, and the second is why the hydrants drew nothing: the elevation projector
groups a wall's layers into ONE candidate, so the drawn hole is the intersection of the
per-layer holes. A 2'-6" window survived as a narrower hole; the 2 1/2" frost-free wall
hydrant penetrations (``AO-M-PORCH-HYD``, ``AO-S-BALC-HYD``) did not overlap at all and the
cladding read unbroken across both.
"""

from __future__ import annotations

import math

import pytest

from typehaus.emit.draw.elevation_project import collect_candidates, view_for
from typehaus.resolve.geometry_walls import layer_solids

_HYDRANT_PENETRATIONS = (("AO-M-PORCH-HYD", "W-M-S1"), ("AO-S-BALC-HYD", "W-S-S1"))


def _along(wall, point) -> float:
    (x0, y0), (x1, y1) = wall.axis
    dx, dy = x1 - x0, y1 - y0
    run = math.hypot(dx, dy) or 1.0
    return ((point[0] - x0) * dx + (point[1] - y0) * dy) / run


def _opening(model, tag):
    return next(op for op in model.openings if op.tag == tag)


@pytest.mark.parametrize(("opening_tag", "wall_tag"), _HYDRANT_PENETRATIONS)
def test_every_layer_is_cut_at_the_openings_own_station(catlin_model, opening_tag, wall_tag):
    wall = catlin_model.wall(wall_tag)
    opening = _opening(catlin_model, opening_tag)
    mid_along = opening.center_along_m
    mid_z = wall.base_ref_z_m + opening.sill_m + opening.height_m / 2.0
    hosted = [op for op in catlin_model.openings if op.host_wall == wall_tag]
    for layer in wall.body_layers():
        if not layer.polygon:
            continue
        band = layer.band(wall) if layer.is_banded else None
        for solid in layer_solids(wall, layer.polygon, hosted, band=band):
            ring = getattr(solid, "ring", None)
            if ring is None:
                continue
            alongs = [_along(wall, point) for point in ring]
            if not (min(alongs) < mid_along < max(alongs)):
                continue
            assert not (solid.z0_m < mid_z < solid.z1_m), (
                f"{layer.name} of {wall_tag} covers {opening_tag}'s centre")


@pytest.mark.parametrize(("opening_tag", "wall_tag"), _HYDRANT_PENETRATIONS)
def test_the_hydrant_penetration_reaches_the_elevation(catlin_model, opening_tag, wall_tag):
    """The drawn wall carries a hole at the penetration, not just the window openings."""
    wall = catlin_model.wall(wall_tag)
    opening = _opening(catlin_model, opening_tag)
    view = view_for("south")
    candidate = next(item for item in collect_candidates(catlin_model, view)
                     if item.tag == wall_tag and item.family == "body")
    silhouette = candidate.silhouette(view)
    u_lo = view.u_of(*wall.axis[0]) + opening.center_along_m - opening.width_m / 2.0
    z_lo = wall.base_ref_z_m + opening.sill_m
    holes = [ring for part in getattr(silhouette, "geoms", (silhouette,))
             for ring in part.interiors]
    matched = [ring for ring in holes
               if abs(min(u for u, _z in ring.coords) - u_lo) < 1e-3
               and abs(min(z for _u, z in ring.coords) - z_lo) < 1e-3]
    assert len(matched) == 1, f"{opening_tag} draws no hole in {wall_tag}"
    ring = matched[0]
    width = max(u for u, _z in ring.coords) - min(u for u, _z in ring.coords)
    height = max(z for _u, z in ring.coords) - min(z for _u, z in ring.coords)
    assert width == pytest.approx(opening.width_m, abs=1e-4)
    assert height == pytest.approx(opening.height_m, abs=1e-4)
