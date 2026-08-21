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


# W-B-S2 carries the sauna's liner variant of the same outboard stack since 2026-08-18, so
# the assembly tag differs per segment; everything the parge assertions say is unchanged.
_SOUTH_ASSEMBLIES = {
    "W-B-S1": "CATLIN_BASEMENT_12_GARDEN",
    "W-B-S2": "SAUNA_LINER_ON_BASEMENT_12_GARDEN",
    "W-B-S3": "CATLIN_BASEMENT_12_GARDEN",
}


def test_the_south_wall_keeps_a_full_height_parge_and_no_band(catlin_model):
    """The sunken garden exposes W-B-S* from -9'-0" to 0'-0", which is not a grade band."""
    for tag, assembly in _SOUTH_ASSEMBLIES.items():
        wall = catlin_model.wall(tag)
        assert wall.assembly == assembly
        parge = next(ly for ly in wall.layers if ly.name == "parge")
        assert not parge.is_banded
        assert parge.band(wall) == (wall.z0_m, wall.z1_m)
        assert not any(ly.name == _PANEL for ly in wall.layers)


def test_the_sauna_liner_stops_at_the_room_ceiling_not_the_wall_top(catlin_model):
    """W-B-S2 is a 9'-0" foundation wall bounding a 7'-6" room. The liner is banded off
    WALL_TOP so the takeoff does not buy basswood, furring and foil-faced polyiso for the
    1'-6" of concrete above the sauna's ceiling."""
    wall = catlin_model.wall("W-B-S2")
    for name in ("tg-liner", "liner-furring", "foil-polyiso"):
        layer = next(ly for ly in wall.layers if ly.name == name)
        assert layer.is_banded
        z0, z1 = layer.band(wall)
        assert z0 == pytest.approx(wall.z0_m)
        assert z1 == pytest.approx(wall.z1_m - inch(18).meters)
        assert (z1 - z0) * _M_TO_FT == pytest.approx(7.5, abs=1e-6)


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
    # No south segment gets a protection panel — the sunken garden is not a grade band.
    assert not any(name.endswith(_PANEL) for name in parts if name.startswith("W-B-S"))
    # W-B-S2's sauna liner is the other banded stack in the house, and it exports the same
    # way: three parts stopping at the sauna's 7'-6" ceiling, not at the wall's 9'-0" top.
    assert {n for n in parts if n.startswith("W-B-S")} == {
        "W-B-S2:tg-liner", "W-B-S2:liner-furring", "W-B-S2:foil-polyiso"}

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


# --- Layer.slot: the regions of ONE row ------------------------------------------------
#
# A band alone says "this layer covers only part of the wall". A *slot* says the further
# thing that two bands are the same row of the stack and share one slice of the wall's
# depth. Without it the only spelling for a split row was several layers, and the stack walk
# charged the wall for every one: catlin's four-colour brick wythe would stand 18 1/8" out
# of the sunken garden where 3 5/8" of brick does.

_WYTHE_IN = 3.625
_VENEER_REGIONS = ("brick-plinth", "brick-band-lo", "brick-field-lo",
                   "brick-band-hi", "brick-field-hi")


def test_a_split_row_is_one_slice_of_the_wall_depth(catlin_model):
    """The bug the slot exists for: five brick regions, one wythe."""
    wall = catlin_model.wall("W-B-BRICK")
    regions = [ly for ly in wall.layers if ly.name in _VENEER_REGIONS]
    assert [ly.name for ly in regions] == list(_VENEER_REGIONS)
    assert all(ly.slot == "wythe" for ly in regions)

    # One depth position between them: the wall is the 1" air gap plus ONE 3 5/8" wythe.
    assert wall.thickness_m * 39.3700787 == pytest.approx(1.0 + _WYTHE_IN, abs=1e-6)
    assert [ly.name for ly in wall.depth_layers()] == ["air-gap", "brick-plinth"]

    # And they resolve onto the identical strip in plan — same polygon, different elevations.
    first = regions[0].polygon
    for region in regions[1:]:
        assert region.polygon == first, f"{region.name} left the wythe's strip"


def test_the_veneer_bands_tile_the_wall_without_overlap(catlin_model):
    """Bottom to top, each region starts where the last one stopped."""
    wall = catlin_model.wall("W-B-BRICK")
    bands = [ly.band(wall) for ly in wall.layers if ly.name in _VENEER_REGIONS]
    assert bands[0][0] == pytest.approx(wall.z0_m)
    assert bands[-1][1] == pytest.approx(wall.z1_m)
    for (_lower, top), (bottom, _upper) in zip(bands, bands[1:], strict=False):
        assert bottom == pytest.approx(top), "a gap or an overlap in the wythe"
    # The registers are two courses; the plinth is 2'-0". Course = 2 2/3" nominal.
    heights_in = [(z1 - z0) * 39.3700787 for z0, z1 in bands]
    assert heights_in[0] == pytest.approx(24.0, abs=1e-3)
    assert heights_in[1] == pytest.approx(5.333, abs=1e-2)
    assert heights_in[3] == pytest.approx(5.333, abs=1e-2)


def _assembly_findings(assembly):
    """``integrity.assembly_layers`` over a one-assembly plan built round ``assembly``."""
    import typehaus.checks.integrity  # noqa: F401 - registers the integrity checks
    from typehaus.checks.registry import (
        CheckContext,
        JurisdictionProfile,
        Preferences,
        registered,
    )

    class _Library:
        assemblies = (assembly,)

        @staticmethod
        def resolve_assembly(tag):
            return assembly if tag == assembly.tag else None

    class _Plan:
        library = _Library()

    fn = next(fn for cid, fn in registered() if cid == "integrity.assembly_layers")
    return fn(CheckContext(
        plan=_Plan(), model=None, preferences=Preferences(),
        profile=JurisdictionProfile(name="t", edition="t", effective_date="t",
                                    irc_base="t", coverage_statement="t")))


#: The one depth every region of the test slot shares, unless a test deliberately differs.
_SLOT_THICKNESS = inch(4.0)


def _slot_assembly(*, second_thickness=None, second_extent="above", tag="SPLIT"):
    second_thickness = _SLOT_THICKNESS if second_thickness is None else second_thickness
    from typehaus.model.assembly import Assembly, Layer, LayerBound, LayerExtent
    from typehaus.model.enums import LayerDatum, LayerFunction

    def band(bottom_in, top_in=None):
        return LayerExtent(
            bottom=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(bottom_in)),
            top=None if top_in is None
            else LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(top_in)))

    second = {"above": band(24.0), "overlapping": band(12.0, 30.0),
              "overlapping-open": band(12.0), "none": None}[second_extent]
    return Assembly(tag=tag, layers=(
        Layer(name="lower", material_ref="brick", thickness=_SLOT_THICKNESS,
              function=LayerFunction.STRUCTURE, slot="wythe", extent=band(0.0, 24.0)),
        Layer(name="upper", material_ref="white-brick", thickness=second_thickness,
              function=LayerFunction.STRUCTURE, slot="wythe", extent=second),
    ))


def test_a_well_formed_slot_reports_nothing():
    assert _assembly_findings(_slot_assembly()) == []


def test_a_slot_whose_regions_disagree_about_thickness_is_an_error():
    """The first region is the one that pays, so a thicker sibling is silently clipped."""
    findings = _assembly_findings(_slot_assembly(second_thickness=inch(6.0)))
    assert [f.check_id for f in findings] == ["integrity.assembly_layers"]
    assert "one row has one depth" in findings[0].message


def test_a_slot_region_with_no_extent_is_an_error():
    """It would claim the whole wall and draw over every sibling."""
    findings = _assembly_findings(_slot_assembly(second_extent="none"))
    assert [f.check_id for f in findings] == ["integrity.assembly_layers"]
    assert "claims the whole wall" in findings[0].message


def test_two_regions_of_a_slot_may_not_overlap():
    """Different materials, so the older same-material band rule cannot catch this — and
    differing materials is the entire point of splitting a row."""
    findings = _assembly_findings(_slot_assembly(second_extent="overlapping"))
    assert [f.check_id for f in findings] == ["integrity.assembly_layers"]
    assert "overlapping bands" in findings[0].message


def test_an_open_topped_region_still_refuses_to_overlap():
    """The top region of a row is naturally authored `top=None` — "run it out to the wall
    top" — which is the only way to say it on a type that many walls share. Reading that as
    "no comparable band" would let the one overlap most likely to be authored straight
    through."""
    findings = _assembly_findings(_slot_assembly(second_extent="overlapping-open"))
    assert [f.check_id for f in findings] == ["integrity.assembly_layers"]
    assert "overlapping bands" in findings[0].message
