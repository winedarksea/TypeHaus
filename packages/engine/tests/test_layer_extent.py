"""Vertically banded assembly layers — ``Layer.extent``.

An ``Assembly`` is a type: many walls share one and it knows none of their elevations. So a
layer that runs only part-way up a wall states its ends against a *datum* — the wall's own
base or top, or finished grade — and the wall resolves it. ``GRADE`` is the datum that makes
"above grade vs below grade" expressible on a type at all, which is what catlin's
above-grade foundation protection panel needs.

These tests hold the chain end to end on the real house: the resolved band, the solid that
is cut from it, the square feet that are ordered, and the IFC part it exports as.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import inch

_M_TO_FT = 3.280839895
_PANEL = "protection-panel"
_BANDED_WALLS = ("W-B-N1", "W-B-N2", "W-B-N3", "W-B-E1", "W-B-E2", "W-B-W1", "W-B-W2")


def _panel(wall):
    return next(ly for ly in wall.layers if ly.name == _PANEL)


def test_the_panel_band_runs_from_six_inches_under_grade_to_the_wall_top(catlin_model):
    grade_m = catlin_model.plan.project.site.grade.meters
    for tag in _BANDED_WALLS:
        wall = catlin_model.wall(tag)
        layer = _panel(wall)
        assert layer.is_banded
        z0, z1 = layer.band(wall)
        assert z0 == pytest.approx(grade_m - inch(6).meters)
        assert z1 == pytest.approx(wall.z1_m)
        # 3'-0" of panel over a 9'-0" wall — the point of banding it.
        assert (z1 - z0) * _M_TO_FT == pytest.approx(3.0, abs=1e-6)


def test_the_south_wall_keeps_a_full_height_parge_and_no_band(catlin_model):
    """The sunken garden exposes W-B-S* from -9'-0" to 0'-0", which is not a grade band."""
    for tag in ("W-B-S1", "W-B-S2", "W-B-S3"):
        wall = catlin_model.wall(tag)
        assert wall.assembly == "CATLIN_BASEMENT_12_GARDEN"
        parge = next(ly for ly in wall.layers if ly.name == "parge")
        assert not parge.is_banded
        assert parge.band(wall) == (wall.z0_m, wall.z1_m)
        assert not any(ly.name == _PANEL for ly in wall.layers)


def test_both_basement_assemblies_stand_the_same_distance_off_the_concrete(catlin_model):
    """N-B-BRICK-W/-E are authored at inch(-4.55) — the sum of everything outboard of the
    concrete face. The panel is the same 1/2" as the parge it replaces precisely so that
    number never moved, and the brick veneer never moved with it."""
    def outboard_in(tag):
        wall = catlin_model.wall(tag)
        return sum(ly.thickness_m for ly in wall.depth_layers()
                   if ly.name != "concrete") / inch(1).meters

    assert outboard_in("W-B-N1") == pytest.approx(4.55, abs=1e-6)
    assert outboard_in("W-B-S1") == pytest.approx(4.55, abs=1e-6)


def test_the_solid_is_cut_to_the_band_not_to_the_wall(catlin_model):
    """One clamp in ``layer_solids`` is what makes the band real in glTF, in IFC and in
    ``geometry_build`` at once — all three come through it."""
    from typehaus.resolve.geometry_walls import layer_solids

    wall = catlin_model.wall("W-B-N1")
    layer = _panel(wall)
    openings = [o for o in catlin_model.openings if o.host_wall == wall.tag]
    band = layer.band(wall)
    solids = layer_solids(wall, layer.polygon, openings, band=band)
    assert solids
    assert min(s.z0_m for s in solids) == pytest.approx(band[0])
    assert max(s.z1_m for s in solids) == pytest.approx(band[1])
    # The unbanded call still spans the whole wall, so nothing else moved.
    whole = layer_solids(wall, layer.polygon, openings)
    assert min(s.z0_m for s in whole) == pytest.approx(wall.z0_m)


def test_the_takeoff_bills_the_band_and_not_the_wall(catlin_model):
    """324 SF: 108 LF of N/E/W perimeter x 3'-0". Billing the wall's face instead would
    order the panel for every buried foot of foam it never reaches — which is exactly what
    the parge coat it replaced was doing, over 1,394 SF house-wide."""
    from typehaus.takeoff.envelope import envelope_layer_takeoff

    rows = {row["material"]: row for row in envelope_layer_takeoff(catlin_model)}
    panel = rows["foundation-protection-panel"]
    assert panel["net_area_sqft"] == pytest.approx(324.0, abs=1.0)
    # The parge survives only on the south wall (and the porch railing's CMU back face).
    assert rows["stucco"]["net_area_sqft"] < 500.0


def test_a_banded_layer_exports_as_an_aggregated_ifc_part(catlin_model, tmp_path):
    """``IfcMaterialLayerSet`` has no vertical variation and its thicknesses must sum to the
    wall's — so a partial layer cannot be a member of one. It goes out the way Revit sends a
    vertically compound wall: ``IfcBuildingElementPart`` bodies under ``IfcRelAggregates``."""
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc import emit_ifc

    model = ifcopenshell.open(str(emit_ifc(catlin_model, tmp_path / "banded.ifc")))

    parts = {p.Name: p for p in model.by_type("IfcBuildingElementPart")}
    assert f"W-B-N1:{_PANEL}" in parts
    assert not any(name.startswith("W-B-S") for name in parts)

    part = parts[f"W-B-N1:{_PANEL}"]
    parents = [rel.RelatingObject for rel in model.by_type("IfcRelAggregates")
               if part in (rel.RelatedObjects or ())]
    assert [p.Name for p in parents] == ["W-B-N1"]
    materials = [rel.RelatingMaterial for rel in model.by_type("IfcRelAssociatesMaterial")
                 if part in (rel.RelatedObjects or ())]
    assert [m.Name for m in materials] == ["foundation-protection-panel"]

    # And it is *not* also a layer of the wall type's set, which would double-describe it
    # and make the set thicker than the geometry it belongs to.
    layer_set = next(s for s in model.by_type("IfcMaterialLayerSet")
                     if s.LayerSetName == "CATLIN_BASEMENT_12")
    assert _PANEL not in [ly.Name for ly in layer_set.MaterialLayers]
