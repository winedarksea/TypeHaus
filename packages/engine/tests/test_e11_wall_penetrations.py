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
from typehaus.emit.draw.elevation_project import project_solids
from typehaus.resolve.geometry_walls import cuts_layer, layer_solids

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
    """Every layer the bore REACHES is cut at its own station, and no other is.

    Both hydrant holes are BLIND from the yard since 2026-09-20 (``RoughOpening.depth`` /
    ``depth_from``): the barrel lands on its seat inside the stud cavity and nothing pierces
    the room side, which is what closes the 6.25 sq in of over-cut board per hydrant that
    ``plan/mep_supply.py`` used to document as deliberate. So the rule is no longer "every
    layer" flat — it is ``cuts_layer``, the same reading the geometry, the section and the
    take-off all make.
    """
    wall = catlin_model.wall(wall_tag)
    opening = _opening(catlin_model, opening_tag)
    mid_along = opening.center_along_m
    mid_z = wall.base_ref_z_m + opening.sill_m + opening.height_m / 2.0
    hosted = [op for op in catlin_model.openings if op.host_wall == wall_tag]
    reached = 0
    for layer in wall.body_layers():
        if not layer.polygon:
            continue
        if not cuts_layer(wall, layer.name, opening):
            continue  # inboard of the bore's back: this layer is whole, and should be
        reached += 1
        band = layer.band(wall) if layer.is_banded else None
        for solid in layer_solids(wall, layer.polygon, hosted, band=band,
                                  layer_name=layer.name):
            ring = getattr(solid, "ring", None)
            if ring is None:
                continue
            alongs = [_along(wall, point) for point in ring]
            if not (min(alongs) < mid_along < max(alongs)):
                continue
            assert not (solid.z0_m < mid_z < solid.z1_m), (
                f"{layer.name} of {wall_tag} covers {opening_tag}'s centre")
    # The bore has to get all the way to the stud cavity or the barrel cannot pass: cladding,
    # girt, vent gap, foam, sheathing and stud is six on both walls. A depth that stopped
    # short would leave this at five and pass every assertion above it vacuously.
    assert reached == 6, f"{opening_tag} reaches {reached} layer(s) of {wall_tag}, not 6"
    # ...and the room-side finish is NOT among them, which is the whole point of the depth.
    inboard = [layer.name for layer in wall.body_layers()
               if not cuts_layer(wall, layer.name, opening)]
    assert inboard, f"{opening_tag} cuts every layer of {wall_tag} — it is not blind"


@pytest.mark.parametrize(("opening_tag", "wall_tag"), _HYDRANT_PENETRATIONS)
def test_the_hydrant_penetration_reaches_the_elevation(catlin_model, opening_tag, wall_tag):
    """The CLADDING is cut at the penetration — and the wall's SILHOUETTE is not.

    Both statements are new on 2026-09-20 and they are the two halves of one fact. A wall
    elevation's body candidate is the union of every layer's projection, so it shows a hole
    only where NO layer covers the station. A blind bore leaves the room-side board whole by
    design, and that board projects into the same 2 1/2" square — so the silhouette closes,
    correctly: from the yard the wall really is solid behind that hole, and what a viewer
    sees is a recess, not daylight.

    ** WHAT THIS COSTS, SAID PLAINLY: ** the south elevation no longer punches these two
    holes, and the penetration reaches that drawing through the hydrant's own symbol and its
    escutcheon rather than through a void in the wall. That is the right drawing — a 2 1/2"
    bore 13 1/4" deep is not a window — but it IS a thing that changed and was not obvious.
    The hole in the outermost layer is what this test pins instead, because that is the part
    of the statement the geometry still owes.
    """
    wall = catlin_model.wall(wall_tag)
    opening = _opening(catlin_model, opening_tag)
    view = view_for("south")
    candidate = next(item for item in collect_candidates(catlin_model, view)
                     if item.tag == wall_tag and item.family == "body")
    silhouette = candidate.silhouette(view)
    u_lo = view.u_of(*wall.axis[0]) + opening.center_along_m - opening.width_m / 2.0
    z_lo = wall.base_ref_z_m + opening.sill_m

    def _hole_at(geometry) -> object | None:
        rings = [ring for part in getattr(geometry, "geoms", (geometry,))
                 for ring in part.interiors]
        matched = [ring for ring in rings
                   if abs(min(u for u, _z in ring.coords) - u_lo) < 1e-3
                   and abs(min(z for _u, z in ring.coords) - z_lo) < 1e-3]
        assert len(matched) <= 1, f"{opening_tag} draws {len(matched)} holes in {wall_tag}"
        return matched[0] if matched else None

    # The outermost layer — the one a viewer is looking AT — really is cut.
    outer = wall.body_layers()[-1]
    assert cuts_layer(wall, outer.name, opening)
    cut = project_solids(tuple(layer_solids(wall, outer.polygon,
                                            [op for op in catlin_model.openings
                                             if op.host_wall == wall_tag],
                                            band=outer.band(wall) if outer.is_banded else None,
                                            layer_name=outer.name)), view)
    ring = _hole_at(cut)
    assert ring is not None, f"{opening_tag} draws no hole in {wall_tag}'s {outer.name}"
    width = max(u for u, _z in ring.coords) - min(u for u, _z in ring.coords)
    height = max(z for _u, z in ring.coords) - min(z for _u, z in ring.coords)
    assert width == pytest.approx(opening.width_m, abs=1e-4)
    assert height == pytest.approx(opening.height_m, abs=1e-4)

    # ...and the whole-wall silhouette does NOT, because the room-side board stands behind it.
    assert _hole_at(silhouette) is None, (
        f"{opening_tag} punches {wall_tag}'s silhouette — it is a blind bore, so the board "
        "behind it should close the projection")


def test_model_json_tells_the_viewer_which_layers_a_blind_opening_cuts(catlin_model):
    """The React viewer cuts wall layers itself, so a blind opening must carry its layers.

    Without ``cut_layers`` it cut the firebox pocket through W-M-E1's sheathing, foam, girt
    and cladding to the east yard.
    """
    from typehaus.server.model_json import model_to_dict

    payload = {o["tag"]: o for o in model_to_dict(catlin_model)["openings"]}
    wall = catlin_model.wall("W-M-E1")
    niche = _opening(catlin_model, "AO-M-FIRE-NICHE")
    cut = payload["AO-M-FIRE-NICHE"]["cut_layers"]
    assert cut == [ly.name for ly in wall.layers if cuts_layer(wall, ly.name, niche)]
    assert {"sheathing", "outer-girt", "cladding"}.isdisjoint(cut)
    assert payload["WIN-M-LIV-E1"]["cut_layers"] is None  # a through hole cuts everything
