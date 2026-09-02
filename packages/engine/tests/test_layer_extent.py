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
        # 2'-2 9/16" of panel over an 8'-0" wall — the point of banding it. Grade is
        # -2'-10"; the band starts 6" under it. The wall stops at the -13 7/16" bearing
        # seat, not at 0'-0".
        assert (z1 - z0) * _M_TO_FT == pytest.approx((34.0 + 6.0 - 13.4375) / 12.0, abs=1e-6)


# The assembly tag differs per segment, which is the point of listing them rather than one
# tag. W-B-S1 and W-B-S4 are outside the excavation, 6'-4" of fill with 2'-2 9/16" standing
# out of it, which is an ordinary grade band and takes the same GRADE-banded protection
# panel the N/E/W walls carry. The four in between (W-B-S2/S3 and their -FR framed
# siblings, a curb below and a stud wall above) are inside the court, where the XPS sits in
# W-B-BRICK's ventilated cavity and buys no skin at all.
_SOUTH_BANDED = {
    "W-B-S1": "CATLIN_BASEMENT_8",
    "W-B-S4": "CATLIN_BASEMENT_8",
}
_SOUTH_COURT = {
    "W-B-S2": "SAUNA_LINER_ON_GARDEN_CURB",
    "W-B-S2-FR": "SAUNA_LINER_ON_GARDEN_FRAMED",
    "W-B-S3": "CATLIN_GARDEN_CURB_6",
    "W-B-S3-FR": "CATLIN_GARDEN_FRAMED_2X6",
}
_SOUTH_ASSEMBLIES = {**_SOUTH_BANDED, **_SOUTH_COURT}


def test_the_south_wall_carries_no_parge_and_bands_only_its_buried_ends(catlin_model):
    """The court walls' XPS is not exposed at all — it is inside W-B-BRICK's ventilated
    cavity, with no UV and no impact on it — so it needs no finish. The only genuinely
    exposed south foam is on the two ends, where the exposure IS a grade band. So: no parge
    anywhere in this house, a GRADE-banded panel on W-B-S1/S4, and nothing outboard of
    ``xps-b`` on the four court segments.
    """
    for tag, assembly in _SOUTH_ASSEMBLIES.items():
        wall = catlin_model.wall(tag)
        assert wall.assembly == assembly
        assert not any(ly.name == "parge" for ly in wall.layers), tag

    for tag in _SOUTH_BANDED:
        wall = catlin_model.wall(tag)
        panel = next(ly for ly in wall.layers if ly.name == _PANEL)
        assert panel.is_banded, tag
        assert panel.band(wall) != (wall.z0_m, wall.z1_m), tag

    for tag in _SOUTH_COURT:
        wall = catlin_model.wall(tag)
        assert not any(ly.name == _PANEL for ly in wall.layers), tag
        names = [ly.name for ly in wall.layers]
        assert names[-1] == "xps-b", tag


def test_the_sauna_liner_stops_at_the_room_ceiling_not_the_wall_top(catlin_model):
    """The sauna's south wall runs past the room's 7'-6" ceiling to the bearing seat, and
    the liner is banded off WALL_TOP so the takeoff does not buy basswood, furring and
    foil-faced polyiso for the wall above the ceiling. The offset is 6" — the wall stops on
    the bearing seat rather than at 0'-0". What is pinned is the CEILING, at 7'-6" over the
    slab.

    The wall is W-B-S2-FR: the south face is a 2x6 stud wall on a 7 1/4" curb. The band did
    not have to move with it, and that is the interesting part — a ``LayerExtent`` is
    measured off the wall TOP, and the top did not move. What did move is the wall's base,
    so the banded run is 7'-6" less the curb, and the curb (W-B-S2, checked below) carries
    the missing 7 1/4" unbanded.
    """
    wall = catlin_model.wall("W-B-S2-FR")
    curb = catlin_model.wall("W-B-S2")
    for name in ("shiplap-liner", "liner-furring", "foil-polyiso"):
        layer = next(ly for ly in wall.layers if ly.name == name)
        assert layer.is_banded
        z0, z1 = layer.band(wall)
        assert z0 == pytest.approx(wall.z0_m)
        assert z1 == pytest.approx(wall.z0_m + inch(82.75).meters)
        # The curb's own liner is NOT banded: it runs the curb's full 7 1/4", because a
        # strip of bare concrete at the bottom of a sauna wall is a hole in the hot side's
        # vapour control (`building_science.humid_room_liner` said so when it was authored
        # without one). The two together are the room's 7'-6".
        below = next(ly for ly in curb.layers if ly.name == name)
        assert not below.is_banded
        assert (z1 - z0 + curb.z1_m - curb.z0_m) * _M_TO_FT == pytest.approx(7.5, abs=1e-6)


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
    """276 SF: the perimeter's banded run x 2'-2 9/16". Billing the wall's face instead
    would order the panel for every buried foot of foam it never reaches — which is exactly
    what the parge coat it replaced was doing, over 1,394 SF house-wide."""
    from typehaus.takeoff.envelope import envelope_layer_takeoff

    rows = {row["material"]: row for row in envelope_layer_takeoff(catlin_model)}
    panel = rows["foundation-protection-panel"]
    assert panel["net_area_sqft"] == pytest.approx(276.3, abs=1.0)
    # The parge survives nowhere: `Material(tag="stucco")` is still in library/materials.py
    # — this house simply has no instance of it.
    assert "stucco" not in rows


def test_a_banded_layer_exports_as_an_aggregated_ifc_part(catlin_ifc_path):
    """``IfcMaterialLayerSet`` has no vertical variation and its thicknesses must sum to the
    wall's — so a partial layer cannot be a member of one. It goes out the way Revit sends a
    vertically compound wall: ``IfcBuildingElementPart`` bodies under ``IfcRelAggregates``."""
    ifcopenshell = pytest.importorskip("ifcopenshell")

    model = ifcopenshell.open(str(catlin_ifc_path))

    parts = {p.Name: p for p in model.by_type("IfcBuildingElementPart")}
    assert f"W-B-N1:{_PANEL}" in parts
    # Only the south segments outside the excavation get a panel: W-B-S1 and W-B-S4 are
    # backfilled 6'-4" with 2'-2 9/16" out of the ground, which is a grade band. The four
    # inside the court are not — their XPS is in W-B-BRICK's ventilated cavity — and they
    # carry no skin at all, so there is nothing for the exporter to aggregate.
    south_banded = {name for name in parts
                    if name.startswith("W-B-S") and name.endswith(_PANEL)}
    assert south_banded == {f"W-B-S1:{_PANEL}", f"W-B-S4:{_PANEL}"}
    # The sauna's south liner is the other banded stack in the house, and it exports the
    # same way: three parts stopping at the room's 7'-6" ceiling, not at the wall's top.
    # W-B-S2-FR's south face is a framed wall on a curb; the curb's own liner is unbanded
    # (it runs the curb's full 7 1/4"), so only the framed wall's three layers are partial
    # and only they aggregate.
    assert {n for n in parts if n.startswith("W-B-S")} == {
        "W-B-S1:protection-panel", "W-B-S4:protection-panel",
        "W-B-S2-FR:shiplap-liner", "W-B-S2-FR:liner-furring", "W-B-S2-FR:foil-polyiso"}

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
                     if s.LayerSetName == "CATLIN_BASEMENT_8")
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
    # The registers are two courses; the plinth is 12 courses, 2'-8". Course = 2 2/3"
    # nominal.
    heights_in = [(z1 - z0) * 39.3700787 for z0, z1 in bands]
    assert heights_in[0] == pytest.approx(32.0, abs=1e-3)
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


# --- the band follows the wall when the wall moves ---------------------------------------
#
# ``resolve_storey_walls`` freezes every extent into absolute ``ResolvedLayer.z0_m/z1_m``,
# and ``extend_walls_to_platform`` grows a stacked wall *after* that (pipeline.py: the lift
# runs in the same stage, but after every storey has resolved). A band pinned to the
# pre-lift top is a layer that stops a joist depth below the wall it belongs to — including
# a ``top=None`` band, whose whole meaning is "run it out to the wall top" and which resolves
# to a number rather than staying open. Latent on catlin only because ``CATLIN_EXT_2X6``
# bands nothing.


def _lift_plan():
    """Two framed storeys with a 13 3/8" joist band between them, and a banded cladding."""
    import uuid

    from typehaus.model import (
        Assembly, Building, FramingSpec, Layer, LayerBound, LayerDatum, LayerExtent,
        LayerFunction, Library, Material, Node, PlanModel, Project, Site, Storey, Wall,
        degF, ft, inch, pt,
    )

    assembly = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        # "From grade, and run it out" — the open-topped band.
        Layer(name="siding", material_ref="wood", thickness=inch(0.5),
              function=LayerFunction.CLADDING,
              extent=LayerExtent(bottom=LayerBound(datum=LayerDatum.GRADE))),
        # And one measured down from the wall's own top.
        Layer(name="frieze", material_ref="wood", thickness=inch(0.75),
              function=LayerFunction.FINISH,
              extent=LayerExtent(bottom=LayerBound(datum=LayerDatum.WALL_TOP,
                                                   offset=inch(-6)))),
    ))
    project = Project(
        name="Lift", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000b1"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15)),
        building=Building(name="Lift"),
    )
    # main tops out at 9'-0"; second starts 13 3/8" above it (mudsill + 11 7/8" rim).
    main = Storey(uid="STMAIN0002", tag="main", elevation=ft(0), default_ceiling_height=ft(9))
    second = Storey(uid="STSEC00002", tag="second",
                    elevation=ft(9) + inch(13.375), default_ceiling_height=ft(8))
    corners = (pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)))
    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),),
        assemblies=(assembly,)), storeys=(main, second))

    def _storey(prefix: str, top, stacks_on: bool):
        nodes = tuple(
            Node(uid=f"N{prefix}{i:08d}", tag=f"N-{prefix}-{i}", position=position)
            for i, position in enumerate(corners, 1)
        )
        walls = tuple(
            Wall(uid=f"W{prefix}{i:08d}", tag=f"W-{prefix}-{i}",
                 start_node=f"N-{prefix}-{start}", end_node=f"N-{prefix}-{end}",
                 assembly="EXT", top=top,
                 **({"stacks_on": f"W-M-{i}"} if stacks_on else {}))
            for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1)
        )
        return (*nodes, *walls)

    return (plan.with_elements("main", _storey("M", ft(9), False))
                .with_elements("second", _storey("S", ft(8), True)))


def test_a_banded_layer_follows_the_wall_up_the_platform_lift():
    from typehaus.quantities import ft
    from typehaus.resolve import resolve

    model, _findings = resolve(_lift_plan())
    lower = model.wall("W-M-1")
    assert lower.plate_top_z_m is not None, "fixture regression: W-M-1 was not lifted"
    assert lower.plate_top_z_m == pytest.approx(ft(9).meters)
    assert lower.z1_m == pytest.approx((ft(9) + inch(13.375)).meters)

    siding = next(ly for ly in lower.layers if ly.name == "siding")
    assert siding.band(lower)[1] == pytest.approx(lower.z1_m), \
        "an open-topped band stopped at the pre-lift wall top"
    assert siding.band(lower)[0] == pytest.approx(0.0)  # grade

    # A WALL_TOP-relative band re-datums too: 6" below the *new* top, not the old one.
    frieze = next(ly for ly in lower.layers if ly.name == "frieze")
    assert frieze.band(lower)[0] == pytest.approx(lower.z1_m - inch(6).meters)

    # The unlifted wall above is unchanged, and still carries the recipe beside the answer.
    upper = model.wall("W-S-1")
    assert upper.plate_top_z_m is None
    assert next(ly for ly in upper.layers if ly.name == "siding").band(upper)[1] == \
        pytest.approx(upper.z1_m)
    assert siding.band_spec == (("grade", 0.0), None)
