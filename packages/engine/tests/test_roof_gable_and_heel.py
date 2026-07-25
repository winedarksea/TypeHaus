"""Truss-roof gable ends, raised-heel closure, and derived eave/rake trim (→ B2).

One synthetic 20'x14' truss-roofed building exercises the whole roof edge:
* the deck plane is lifted by the raised heel *before* ``ToRoof`` walls rake to it;
* the end truss stations are gable-end drop trusses with outlookers and a barge rafter;
* every exterior wall's weather skin carries up to the roof underside;
* ``Roof.eave_trim`` derives two fascia layers and a soffit on all four edges.
"""

from __future__ import annotations

import math
import uuid

import pytest
from shapely.geometry import Point, Polygon

from typehaus.model import (
    Assembly, Building, EaveGutter, EaveSoffit, EaveTrim, Fascia, FasciaBoard, FramingSpec,
    Layer, LayerFunction, Library, Material, Node, PlanModel, Project, Roof, RoofForm, Site,
    Storey, ToRoof, TrimKind, Wall, degF, ft, inch, pt,
)
from typehaus.quantities import Pitch
from typehaus.resolve import resolve
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import rect_between
from typehaus.emit.gltf.emitter import is_roof_framing_member
from typehaus.resolve.roof_geometry import roof_height_at

HEEL = inch(9.25)
CHORD = "2x4"
PLATE_TOP_FT = 9.0
# The bearing walls run along x, so the ridge runs along x at mid-y and the gable ends are
# the x=0 / x=20' walls.
RIDGE_DIRECTION = "x"
OVERHANG = inch(16)

_EAVE_TRIM = EaveTrim(
    fascia=(FasciaBoard(material="spf", thickness=inch(1.5), depth=inch(5.5)),
            FasciaBoard(material="pvc-cellular", thickness=inch(1), depth=inch(6))),
    soffit_material="pvc-cellular", soffit_thickness=inch(0.5), soffit_vented=True,
)


def _plan(*, gable_top=None, eave_trim=_EAVE_TRIM, extra_elements=(),
          roof_layers=(), overhang=OVERHANG) -> PlanModel:
    """A 20'x14' box with a raised-heel truss roof.

    The east gable is split at the ridge into two ``ToRoof`` segments; the west gable stays
    a flat 9' wall, so one plan covers both the raked-wall path and the closure path.
    """
    wall_assembly = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="sheathing", material_ref="wood", thickness=inch(1.5),
              function=LayerFunction.SHEATHING),
        Layer(name="cladding", material_ref="wood", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ))
    roof_assembly = Assembly(tag="TRUSS_ROOF", layers=(
        Layer(name="truss", material_ref="wood", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member=CHORD, roof_frame="truss", heel_height=HEEL,
                                  chord_member=CHORD, web_member=CHORD)),
        *roof_layers,
    ))
    project = Project(
        name="Gable", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000b2"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Gable"),
    )
    storey = Storey(uid="STMAIN0001", tag="main", elevation=ft(0),
                    default_ceiling_height=ft(PLATE_TOP_FT))
    nodes = (
        Node(uid="N000000001", tag="N-SW", position=pt(ft(0), ft(0))),
        Node(uid="N000000002", tag="N-SE", position=pt(ft(20), ft(0))),
        Node(uid="N000000003", tag="N-NE", position=pt(ft(20), ft(14))),
        Node(uid="N000000004", tag="N-NW", position=pt(ft(0), ft(14))),
        Node(uid="N000000005", tag="N-E-RIDGE", position=pt(ft(20), ft(7))),
    )
    top = ToRoof(roof_ref="RF") if gable_top is None else gable_top
    walls = (
        Wall(uid="W000000001", tag="W-S", start_node="N-SW", end_node="N-SE",
             assembly="EXT", top=ft(PLATE_TOP_FT)),
        Wall(uid="W000000002", tag="W-E1", start_node="N-SE", end_node="N-E-RIDGE",
             assembly="EXT", top=top),
        Wall(uid="W000000003", tag="W-E2", start_node="N-E-RIDGE", end_node="N-NE",
             assembly="EXT", top=top),
        Wall(uid="W000000004", tag="W-N", start_node="N-NE", end_node="N-NW",
             assembly="EXT", top=ft(PLATE_TOP_FT)),
        Wall(uid="W000000005", tag="W-W", start_node="N-NW", end_node="N-SW",
             assembly="EXT", top=ft(PLATE_TOP_FT)),
    )
    roof = Roof(uid="RF00000001", tag="RF", form=RoofForm.GABLE, pitch=Pitch(4, 12),
                bearing_refs=("W-S", "W-N"), assembly="TRUSS_ROOF", overhang=overhang,
                ridge_direction=RIDGE_DIRECTION, eave_trim=eave_trim)
    library = Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.2),),
        assemblies=(wall_assembly, roof_assembly),
    )
    return PlanModel(project=project, library=library, storeys=(storey,)).with_elements(
        "main", [*nodes, *walls, roof, *extra_elements])


@pytest.fixture(scope="module")
def resolved():
    model, _findings = resolve(_plan())
    return model


def _roof(model):
    return model.roofs[0]


def _members(model, category):
    return [member for member in _roof(model).members if member.category == category]


# --- 1. pipeline ordering: the heel lift happens before ToRoof walls rake ------------------

def test_truss_roof_plane_is_lifted_by_the_raised_heel(resolved):
    """The top-chord underside clears plate top + heel over the bearing wall."""
    roof = _roof(resolved)
    bearing = next(wall for wall in resolved.walls if wall.tag == "W-S")
    chord_depth = cross_section(CHORD).depth_m
    underside = roof_height_at(roof, bearing.axis[0]) - chord_depth
    assert underside == pytest.approx(bearing.z1_m + HEEL.meters, abs=1e-9)


def test_to_roof_wall_reaches_the_lifted_plane_not_the_pre_lift_one(resolved):
    """Regression: the lift used to run two stages *after* the walls raked to the plane,
    so a gable wall stopped a heel-plus-chord below the roof it was supposed to meet."""
    roof = _roof(resolved)
    for tag in ("W-E1", "W-E2"):
        wall = next(w for w in resolved.walls if w.tag == tag)
        assert wall.top_z0_m == pytest.approx(roof_height_at(roof, wall.axis[0]))
        assert wall.top_z1_m == pytest.approx(roof_height_at(roof, wall.axis[1]))
    # The segment ending at the ridge node reaches the ridge itself.
    at_ridge = next(w for w in resolved.walls if w.tag == "W-E1")
    assert at_ridge.top_z1_m == pytest.approx(roof.ridge_z_m)
    # ... and that is strictly above the unlifted plate-top-derived plane.
    plate_top = next(w for w in resolved.walls if w.tag == "W-S").z1_m
    assert roof.eave_z_m > plate_top + 1e-6


# --- 2. gable-end truss + rake framing -----------------------------------------------------

def test_gable_ends_are_drop_trusses_with_studs_not_fink_webs(resolved):
    keys = {member.child_key for member in _roof(resolved).members}
    ends = ("truss-000", f"truss-{len([k for k in keys if k.endswith('-bc')]) - 1:03d}")
    for end in ends:
        assert any(key.startswith(f"{end}-gable-stud-") for key in keys), end
        assert not any(key.startswith(f"{end}-web-") or key.startswith(f"{end}-king")
                       for key in keys), end
    # Interior stations keep the Fink pattern.
    assert any(key.startswith("truss-001-web-") for key in keys)


def test_gable_studs_stop_under_the_dropped_top_chord(resolved):
    roof = _roof(resolved)
    chord_depth = cross_section(CHORD).depth_m
    drop = cross_section("2x4").depth_m  # outlooker depth
    for stud in (m for m in _roof(resolved).members
                 if m.category == "stud" and "gable-stud" in m.child_key):
        expected = roof_height_at(roof, stud.p0) - drop - chord_depth
        assert stud.z1_m == pytest.approx(expected, abs=1e-9)
        assert stud.z1_m > stud.z0_m


def test_rake_overhang_carries_outlookers_and_a_barge_rafter(resolved):
    roof = _roof(resolved)
    outlookers = _members(resolved, "outlooker")
    barges = _members(resolved, "barge_rafter")
    assert outlookers, "a 16in rake overhang must be framed"
    assert len(barges) == 4  # two roof halves at each of the two gable ends
    minx = min(point[0] for point in roof.footprint)
    maxx = max(point[0] for point in roof.footprint)
    reach = {round(min(m.p0[0], m.p1[0]), 6) for m in outlookers} | \
            {round(max(m.p0[0], m.p1[0]), 6) for m in outlookers}
    assert round(minx, 6) in reach and round(maxx, 6) in reach
    for barge in barges:
        assert barge.z1_end_m == pytest.approx(roof.ridge_z_m)


# --- 3. wall → roof closure (raised heel + gable end) --------------------------------------

def _closures(model, wall_tag):
    return [m for m in _roof(model).members if m.child_key.startswith(f"{wall_tag}-closure-")]


def test_eave_wall_skin_carries_up_through_the_raised_heel(resolved):
    """The TODO's daylight band: the wall stopped at the plate, the roof started a heel up."""
    roof = _roof(resolved)
    chord_depth = cross_section(CHORD).depth_m
    wall = next(w for w in resolved.walls if w.tag == "W-S")
    closures = _closures(resolved, "W-S")
    assert {m.category for m in closures} == {"sheathing", "cladding"}
    # The band runs plate top → top-chord underside over the wall's own axis.
    underside = roof_height_at(roof, wall.axis[0]) - chord_depth
    for member in closures:
        assert member.z0_m == pytest.approx(wall.z1_m)
        assert member.z1_m == pytest.approx(underside, abs=1e-6)
        assert member.z1_m - member.z0_m == pytest.approx(HEEL.meters, abs=1e-6)


def test_gable_wall_closure_splits_at_the_ridge_and_reaches_the_peak(resolved):
    roof = _roof(resolved)
    chord_depth = cross_section(CHORD).depth_m
    closures = _closures(resolved, "W-W")
    # Two segments (one per roof plane) x two skin layers.
    assert {m.child_key.split("-closure-")[1].split("-")[0] for m in closures} == {"0", "1"}
    peak = max(max(m.z1_m, m.z1_end_m or m.z1_m) for m in closures)
    assert peak == pytest.approx(roof.ridge_z_m - chord_depth, abs=1e-6)


def test_a_wall_already_raked_to_the_roof_gets_no_closure(resolved):
    assert _closures(resolved, "W-E1") == []
    assert _closures(resolved, "W-E2") == []


# --- 4. derived eave / rake fascia + soffit ------------------------------------------------

def test_two_fascia_layers_and_a_soffit_on_every_roof_edge(resolved):
    fascia = _members(resolved, "fascia")
    soffit = _members(resolved, "soffit")
    # Two level eaves + two rakes split at the ridge = six runs.
    assert len(fascia) == 6 * 2
    assert len(soffit) == 6
    assert {m.connection for m in fascia} == {"eave-trim:spf", "eave-trim:pvc-cellular"}
    assert {m.connection for m in soffit} == {"eave-trim:vented-soffit"}


def test_fascia_tops_sit_on_the_roof_plane_and_the_rake_slopes(resolved):
    """Fascia tops are the plane at the *roof edge*, so a heel lift carries them with it."""
    roof = _roof(resolved)
    nailers = [m for m in _members(resolved, "fascia") if m.connection.endswith("spf")]
    level = [m for m in nailers if m.z1_m == pytest.approx(m.z1_end_m)]
    rakes = [m for m in nailers if m.z1_m != pytest.approx(m.z1_end_m)]
    assert len(level) == 2 and len(rakes) == 4
    for member in level:
        assert member.z1_m == pytest.approx(roof.eave_z_m, abs=1e-9)
    assert max(max(m.z1_m, m.z1_end_m) for m in rakes) == pytest.approx(roof.ridge_z_m)
    # The rake nailer starts one board thickness up-slope of the eave, not on it: that is the
    # mitred corner, where the rake dies into the eave nailer's inner face.
    span = max(p[1] for p in roof.footprint) - min(p[1] for p in roof.footprint)
    pitch = (roof.ridge_z_m - roof.eave_z_m) / (span / 2.0)
    foot = min(min(m.z1_m, m.z1_end_m) for m in rakes)
    assert foot == pytest.approx(roof.eave_z_m + inch(1.5).meters * pitch, abs=1e-9)


def test_soffit_spans_the_overhang_from_the_wall_face_to_the_fascia(resolved):
    soffit = _members(resolved, "soffit")[0]
    wall = next(w for w in resolved.walls if w.tag == "W-S")
    # Overhang, less the wall's projection past its (center-aligned) axis, less the
    # fascia nailer the soffit dies into.
    expected = OVERHANG.meters - wall.thickness_m / 2.0 - inch(1.5).meters
    assert cross_section(soffit.profile).width_m == pytest.approx(expected, abs=1e-6)


def test_a_roof_without_eave_trim_emits_none(resolved):
    model, _ = resolve(_plan(eave_trim=None))
    assert not [m for m in model.roofs[0].members if m.category in ("fascia", "soffit")]


# --- 5. the EaveSoffit element -------------------------------------------------------------

def test_authored_eave_soffit_and_fascia_resolve_to_trim_solids():
    """``EaveSoffit`` is a first-class edge run, distinct from the interior ceiling Soffit."""
    runs = (
        Fascia(uid="TR00000001", tag="TR-FASCIA", kind=TrimKind.FASCIA,
               path=(pt(ft(0), ft(0)), pt(ft(20), ft(0))), top_elevation=ft(10),
               depth=inch(6), thickness=inch(1), material="pvc-cellular"),
        EaveSoffit(uid="TR00000002", tag="TR-SOFFIT", path=(pt(ft(0), ft(-1)),
                                                            pt(ft(20), ft(-1))),
                   top_elevation=ft(9.5), depth=inch(0.5), thickness=inch(16),
                   material="pvc-cellular", vented=True),
    )
    model, _ = resolve(_plan(extra_elements=runs))
    by_tag = {solid.tag: solid for solid in model.solids}
    assert by_tag["TR-SOFFIT-1"].category == "soffit"
    assert by_tag["TR-FASCIA-1"].category == "fascia"
    assert by_tag["TR-SOFFIT-1"].z1_m == pytest.approx(ft(9.5).meters)


# --- 6. the above-deck stack edge, and the framing/skin split ------------------------------

# A roof whose assembly carries real layers above the structure — foam thick enough that its
# exposed edge is a band you can see from the ground, like the catlin house's 8" over-deck
# stack. The base fixture's roof is structure-only, so nothing above the deck to wrap.
_STACK_LAYERS = (
    Layer(name="deck", material_ref="wood", thickness=inch(0.75),
          function=LayerFunction.SHEATHING),
    Layer(name="foam", material_ref="polyiso", thickness=inch(6),
          function=LayerFunction.INSULATION),
    Layer(name="roofing", material_ref="standing-seam", thickness=inch(0.5),
          function=LayerFunction.CLADDING),
)


@pytest.fixture(scope="module")
def stacked():
    model, _findings = resolve(_plan(roof_layers=_STACK_LAYERS))
    return model


def _edge_cladding(model):
    return [m for m in _roof(model).members if m.child_key.endswith("-edge-cladding")]


def test_no_edge_cladding_without_layers_above_the_deck(resolved):
    """The base fixture's roof is bare structure — a band there would be inventing material."""
    assert _edge_cladding(resolved) == []


def test_edge_cladding_wraps_every_roof_edge_in_the_roofing_material(stacked):
    band = _edge_cladding(stacked)
    # Two level eaves + two rakes split at the ridge = six runs, same as the fascia.
    assert len(band) == 6
    assert {m.category for m in band} == {"cladding"}
    assert {m.material for m in band} == {"standing-seam"}


def test_edge_cladding_bridges_the_wall_cladding_top_to_the_roofing(stacked):
    """It closes exactly what the reference leaves to the drip edge and gutter flashing.

    Its bottom is the wall cladding's mating face (the roof foam underside) and its top is
    the roofing underside, so the wall's run of metal and the roof's are continuous. Both are
    perpendicular offsets, so the vertical band is slope-corrected or it lands short.
    """
    roof = _roof(stacked)
    deck, foam, roofing = _STACK_LAYERS
    span = max(p[1] for p in roof.footprint) - min(p[1] for p in roof.footprint)
    slope = (roof.ridge_z_m - roof.eave_z_m) / (span / 2.0)
    factor = math.hypot(1.0, slope)
    assert factor > 1.0  # the correction is real, not a no-op
    # Wall cladding dies under the foam; the band picks up there and runs to the roofing.
    base = deck.thickness.meters * factor
    expected = foam.thickness.meters * factor
    for member in _edge_cladding(stacked):
        assert member.z1_m - member.z0_m == pytest.approx(expected, abs=1e-9)
        assert member.z1_end_m - member.z0_end_m == pytest.approx(expected, abs=1e-9)
    # Every band starts a deck above the roof plane, and the rakes climb to the ridge with it.
    eaves = [m for m in _edge_cladding(stacked) if m.z0_m == pytest.approx(m.z0_end_m)]
    assert len(eaves) == 2
    assert {round(m.z0_m, 9) for m in eaves} == {round(roof.eave_z_m + base, 9)}
    peak = max(max(m.z0_m, m.z0_end_m) for m in _edge_cladding(stacked))
    assert peak == pytest.approx(roof.ridge_z_m + base, abs=1e-9)


def test_a_deck_and_metal_roof_needs_no_edge_band(resolved):
    """Nothing between the deck and the metal means the wall cladding already reaches it."""
    thin = (Layer(name="deck", material_ref="wood", thickness=inch(0.75),
                  function=LayerFunction.SHEATHING),
            Layer(name="roofing", material_ref="standing-seam", thickness=inch(0.5),
                  function=LayerFunction.CLADDING))
    model, _ = resolve(_plan(roof_layers=thin))
    assert _edge_cladding(model) == []


def test_closure_bands_carry_their_source_layer_material(resolved):
    """Without it both emitters paint a standing-seam band the category-grey of plywood."""
    closures = _closures(resolved, "W-S")
    assert closures
    assert {m.material for m in closures} == {"wood"}


def test_derived_trim_carries_its_board_material(resolved):
    assert {m.material for m in _members(resolved, "fascia")} == {"spf", "pvc-cellular"}
    assert {m.material for m in _members(resolved, "soffit")} == {"pvc-cellular"}


def test_roof_members_split_into_framing_sticks_and_envelope_skin(stacked):
    """Trusses belong under the framing toggle; the skin belongs with the shell it finishes."""
    roof = _roof(stacked)
    framing = {m.category for m in roof.members if is_roof_framing_member(m)}
    skin = {m.category for m in roof.members if not is_roof_framing_member(m)}
    assert {"top_chord", "bottom_chord", "truss_web", "stud", "fascia"} <= framing
    assert skin == {"sheathing", "cladding", "soffit"}
    assert not framing & skin


# --- 7. the golden detail's per-layer mating (flush eave) ----------------------------------

# The reference eave (tests/fixtures/catlin_reference/scripts/roof_wall_eave_detail_ifc.py)
# is a *flush* eave closed by a box gutter, not an overhang closed by a soffit: the roof
# layers stop at the wall stack's faces and the wall layers run up into the roof stack. This
# fixture is that condition — the same layered roof, zero overhang.
@pytest.fixture(scope="module")
def flush():
    model, _findings = resolve(_plan(roof_layers=_STACK_LAYERS, overhang=inch(0)))
    return model


def _closure(model, wall_tag, layer_name):
    return next(m for m in _roof(model).members
                if m.child_key == f"{wall_tag}-closure-0-{layer_name}")


def test_flush_eave_runs_each_wall_layer_to_its_own_face_in_the_roof_stack(flush):
    """Not one band to one underside: sheathing to the deck, foam and cladding under the
    roof foam, furring up to the roof furring so the vent channel stays continuous."""
    roof = _roof(flush)
    deck, foam, _roofing = _STACK_LAYERS
    span = max(p[1] for p in roof.footprint) - min(p[1] for p in roof.footprint)
    factor = math.hypot(1.0, (roof.ridge_z_m - roof.eave_z_m) / (span / 2.0))
    for name, perpendicular in (("sheathing", 0.0),
                                ("cladding", deck.thickness.meters)):
        member = _closure(flush, "W-S", name)
        plane = roof_height_at(roof, member.p0)
        assert member.z1_m == pytest.approx(plane + perpendicular * factor, abs=1e-9)
    # Each layer mates a little lower than the one inboard of it, because the roof slopes
    # down as it runs out over the stack.
    assert _closure(flush, "W-S", "cladding").z1_m > _closure(flush, "W-S", "sheathing").z1_m


def test_an_overhung_eave_still_stops_at_the_structure_underside(stacked):
    """With an overhang the soffit closes the gap, so the skin must not climb into the stack —
    the two eave types are genuinely different details."""
    roof = _roof(stacked)
    chord_depth = cross_section(CHORD).depth_m
    for name in ("sheathing", "cladding"):
        member = _closure(stacked, "W-S", name)
        underside = roof_height_at(roof, (member.p0[0], 0.0)) - chord_depth
        assert member.z1_m == pytest.approx(underside, abs=1e-6)


def test_flush_gable_rake_carries_the_skin_above_the_deck_plane(flush):
    """A ToRoof gable rakes to the deck plane, so its foam, furring and cladding are the
    layers with somewhere left to go — and the sheathing, already there, emits nothing."""
    keys = {m.child_key for m in _roof(flush).members}
    # W-E1/W-E2 are the ToRoof gable segments; W-W is a flat 9' wall.
    assert "W-E1-closure-0-sheathing" not in keys
    member = _closure(flush, "W-E1", "cladding")
    wall = next(w for w in flush.walls if w.tag == "W-E1")
    # It springs from the raked wall top (the deck plane) and climbs above it.
    assert member.z0_m == pytest.approx(wall.top_z0_m, abs=1e-9)
    assert member.z1_m > member.z0_m
    # A wall that already reaches its face produces nothing at all — this one still does,
    # because the deck plane is not where its cladding dies.
    assert _closures(flush, "W-E1")


# --- 8. mitred rake corners ----------------------------------------------------------------

def _plan_polygon(member):
    """A trim member's plan footprint, the way every emitter builds it."""
    half = cross_section(member.profile).width_m / 2.0
    return Polygon(rect_between(member.p0, member.p1, -half, half))


def _overlapping_pairs(members):
    polygons = [(m.child_key, _plan_polygon(m)) for m in members]
    return [(a[0], b[0]) for index, a in enumerate(polygons) for b in polygons[index + 1:]
            if a[1].intersection(b[1]).area > 1e-9]


@pytest.mark.parametrize("band", ["below", "above"])
def test_eave_and_rake_trim_tile_the_rake_corners_instead_of_overlapping(stacked, band):
    """The eave run and the rake run of the same piece used to both claim the corner square.

    A box member cannot carry a 45° end cut, so the corner is lapped rather than truly
    mitred — but the material must be there exactly once, which is what a miter guarantees
    and what doubling did not. Checked per elevation band: the fascia and soffit hang under
    the roof plane, the edge cladding stands on top of it, so the two never share space.
    """
    hanging = [m for m in _roof(stacked).members if m.category in ("fascia", "soffit")]
    standing = [m for m in _roof(stacked).members if m.child_key.endswith("-edge-cladding")]
    members = hanging if band == "below" else standing
    assert len(members) >= 6  # at least one piece on each of the six runs
    assert _overlapping_pairs(members) == []


def test_the_eave_run_owns_the_corner_square_so_nothing_is_left_open(stacked):
    """The lap must not open a notch where the doubled material used to be: the eave piece is
    cut back to its own outer face, which is exactly where the rake piece stops."""
    roof = _roof(stacked)
    minx = min(point[0] for point in roof.footprint)
    miny = min(point[1] for point in roof.footprint)
    nailer = inch(1.5).meters  # the innermost fascia board's thickness
    corner = Point(minx + nailer / 2.0, miny + nailer / 2.0)
    covering = [m for m in _members(stacked, "fascia")
                if m.child_key.endswith("-fascia-0") and _plan_polygon(m).covers(corner)]
    assert [m.child_key for m in covering] == ["eave-lo-fascia-0"]


def test_fascia_carries_the_framing_trade_so_a_framing_toggle_shows_it(stacked):
    """A fascia board is trim by category but a nailer on the rafter tails by trade."""
    assert {m.trade for m in _members(stacked, "fascia")} == {"framing"}
    # The panels it trims are not framing, and neither is ordinary lumber (its category
    # already files it there).
    assert {m.trade for m in _members(stacked, "soffit")} == {None}
    assert {m.trade for m in _members(stacked, "top_chord")} == {None}


# --- 9. the derived gutter -----------------------------------------------------------------

_GUTTER = EaveGutter(material="aluminum", depth=inch(5), thickness=inch(6),
                     top_drop=inch(1.2), edges=("south",), slope="1/16 in/ft")


@pytest.fixture(scope="module")
def guttered():
    trim = _EAVE_TRIM.model_copy(update={"gutter": _GUTTER})
    model, _findings = resolve(_plan(roof_layers=_STACK_LAYERS, eave_trim=trim))
    return model


def test_the_gutter_hangs_on_the_authored_eave_only(guttered):
    """The ridge runs along x, so the eaves are the south and north edges; a rake sheds into
    the eave below it and gets no channel at all."""
    gutters = _members(guttered, "gutter")
    assert [m.child_key for m in gutters] == [
        "eave-lo-gutter-back", "eave-lo-gutter-bottom", "eave-lo-gutter-front"]
    assert {m.material for m in gutters} == {"aluminum"}
    assert {m.connection for m in gutters} == {"eave-trim:gutter:1/16 in/ft"}


def test_the_gutter_rides_the_roof_plane_through_the_raised_heel(guttered):
    """Authored at an absolute elevation it would sit a heel below the eave it drains."""
    roof = _roof(guttered)
    top = roof.eave_z_m - inch(1.2).meters
    by_key = {m.child_key.rsplit("-", 1)[1]: m for m in _members(guttered, "gutter")}
    for side in ("back", "front"):
        assert by_key[side].z1_m == pytest.approx(top, abs=1e-9)
        assert by_key[side].z1_m - by_key[side].z0_m == pytest.approx(inch(5).meters,
                                                                      abs=1e-9)
    # Hung outboard of the fascia stack's outer face (the pvc board laps 1" past the roof
    # edge; the spf nailer sits inboard of it), not overlapping it: the back sheet's centre
    # is half a shell out from that face, the front face's is half a shell in from the
    # channel's outer face.
    face = inch(1).meters
    edge = min(p[1] for p in roof.footprint)
    shell = inch(0.5).meters

    def outward(member):
        return min(abs(point[1] - edge) for point in (member.p0, member.p1))

    assert outward(by_key["back"]) == pytest.approx(face + shell / 2.0, abs=1e-9)
    assert outward(by_key["front"]) == pytest.approx(face + inch(6).meters - shell / 2.0,
                                                     abs=1e-9)


def test_the_gutter_is_an_open_channel_not_a_solid_bar(guttered):
    """Three thin bands — back, bottom, front — leave an open trough rain can land in."""
    by_key = {m.child_key.rsplit("-", 1)[1]: m for m in _members(guttered, "gutter")}
    assert set(by_key) == {"back", "bottom", "front"}
    shell = inch(0.5).meters
    from typehaus.resolve.framing.profiles import cross_section as cs
    # The two walls are shell-thin; the bottom spans the width left between them.
    assert cs(by_key["back"].profile).width_m == pytest.approx(shell, abs=1e-9)
    assert cs(by_key["front"].profile).width_m == pytest.approx(shell, abs=1e-9)
    assert cs(by_key["bottom"].profile).width_m == pytest.approx(
        inch(6).meters - 2 * shell, abs=1e-9)
    # The bottom band closes only the underside; everything above it is open trough.
    assert by_key["bottom"].z0_m == pytest.approx(by_key["back"].z0_m, abs=1e-9)
    assert by_key["bottom"].z1_m == pytest.approx(by_key["back"].z0_m + shell, abs=1e-9)
    assert by_key["back"].z1_m - by_key["bottom"].z1_m > inch(3).meters


def test_no_gutter_without_one_on_the_declaration(stacked):
    assert _members(stacked, "gutter") == []


# --- 10. the vented ridge cap --------------------------------------------------------------

def test_a_vented_attic_gets_a_ridge_cap_on_the_plane_itself(resolved):
    """The base fixture's soffits are vented, so the truss space must exhaust at the ridge.
    A truss roof has no ridge beam — the cap keys off ``ridge_z_m``, the plane's own peak."""
    caps = _members(resolved, "ridge_cap")
    assert [m.child_key for m in caps] == ["ridge-vent-cap"]
    cap = caps[0]
    roof = _roof(resolved)
    # Bare structure above the plane: the cap sits straight on the ridge elevation and runs
    # the footprint's whole ridge-axis extent, rake overhangs included.
    assert cap.z0_m == pytest.approx(roof.ridge_z_m, abs=1e-9)
    assert cap.z1_m - cap.z0_m == pytest.approx(inch(2).meters, abs=1e-9)
    mid_y = (min(p[1] for p in roof.footprint) + max(p[1] for p in roof.footprint)) / 2.0
    assert cap.p0[1] == pytest.approx(mid_y) and cap.p1[1] == pytest.approx(mid_y)
    assert {cap.p0[0], cap.p1[0]} == {min(p[0] for p in roof.footprint),
                                      max(p[0] for p in roof.footprint)}


def test_the_ridge_cap_rides_on_top_of_the_layer_stack(stacked):
    """With deck + foam + roofing over the structure the cap sits on the roofing surface,
    slope-corrected, and reads in the roofing's own material."""
    roof = _roof(stacked)
    cap = _members(stacked, "ridge_cap")[0]
    span = max(p[1] for p in roof.footprint) - min(p[1] for p in roof.footprint)
    factor = math.hypot(1.0, (roof.ridge_z_m - roof.eave_z_m) / (span / 2.0))
    stack = sum(layer.thickness.meters for layer in _STACK_LAYERS)
    assert cap.z0_m == pytest.approx(roof.ridge_z_m + stack * factor, abs=1e-9)
    assert cap.material == "standing-seam"


def test_an_unvented_roof_gets_no_ridge_cap():
    """No vented soffit and no over-deck vent channel means no slot to cap."""
    unvented = EaveTrim(
        fascia=(FasciaBoard(material="spf", thickness=inch(1.5), depth=inch(5.5)),))
    model, _ = resolve(_plan(eave_trim=unvented, roof_layers=_STACK_LAYERS))
    assert _members(model, "ridge_cap") == []


def test_an_over_deck_vent_channel_calls_for_a_ridge_cap_without_any_eave_trim():
    """The hot-roof path (the catlin house): the batten gap between the foam and the
    standing seam runs eave to ridge, so the ridge must exhaust it even with no authored
    eave trim at all."""
    vented_layers = (
        Layer(name="deck", material_ref="wood", thickness=inch(0.75),
              function=LayerFunction.SHEATHING),
        Layer(name="foam", material_ref="polyiso", thickness=inch(6),
              function=LayerFunction.INSULATION),
        Layer(name="batten-gap", material_ref="wood", thickness=inch(0.75),
              function=LayerFunction.AIRGAP),
        Layer(name="roofing", material_ref="standing-seam", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    )
    model, _ = resolve(_plan(eave_trim=None, roof_layers=vented_layers))
    caps = _members(model, "ridge_cap")
    assert [m.child_key for m in caps] == ["ridge-vent-cap"]
    assert caps[0].material == "standing-seam"


# --- 11. soffit and gutter no longer require a fascia stack --------------------------------

def test_soffit_and_gutter_derive_without_any_fascia_boards():
    """An eave trim with an empty fascia stack is soffit/gutter-only: the reference detail
    for a wrapped standing-seam roof keeps the vented soffit but hangs no fascia boards."""
    trim = EaveTrim(fascia=(), soffit_material="pvc-cellular",
                    soffit_thickness=inch(0.5), soffit_vented=True, gutter=_GUTTER)
    model, _ = resolve(_plan(eave_trim=trim))
    assert _members(model, "fascia") == []
    soffits = _members(model, "soffit")
    assert len(soffits) == 6
    roof = _roof(model)
    # With no fascia to hang from, the panel tucks its own thickness under the roof edge.
    level = [m for m in soffits if m.z1_m == pytest.approx(m.z1_end_m)]
    assert len(level) == 2
    for member in level:
        assert member.z1_m == pytest.approx(roof.eave_z_m, abs=1e-9)
    for member in soffits:
        assert member.z1_m - member.z0_m == pytest.approx(inch(0.5).meters, abs=1e-9)
    gutters = _members(model, "gutter")
    assert {m.child_key for m in gutters} == {
        "eave-lo-gutter-back", "eave-lo-gutter-bottom", "eave-lo-gutter-front"}
    # The channel registers against the roof edge itself (fascia outer face = 0).
    edge = min(p[1] for p in roof.footprint)
    back = next(m for m in gutters if m.child_key.endswith("back"))
    assert min(abs(p[1] - edge) for p in (back.p0, back.p1)) == pytest.approx(
        inch(0.25).meters, abs=1e-9)


# --- 12. the fascia rides up over the deck edge --------------------------------------------

def test_outboard_fascia_rides_up_over_the_deck_edge(stacked):
    """The board hung clear of the roof edge climbs to the foam underside so the deck's
    exposed edge (the visible-sheathing defect) is covered; the nailer directly under the
    deck keeps topping out at the plane."""
    roof = _roof(stacked)
    deck = _STACK_LAYERS[0]
    span = max(p[1] for p in roof.footprint) - min(p[1] for p in roof.footprint)
    factor = math.hypot(1.0, (roof.ridge_z_m - roof.eave_z_m) / (span / 2.0))
    rise = deck.thickness.meters * factor
    nailers = [m for m in _members(stacked, "fascia") if m.connection.endswith("spf")]
    faces = [m for m in _members(stacked, "fascia")
             if m.connection.endswith("pvc-cellular")]
    level_nailer = next(m for m in nailers if m.z1_m == pytest.approx(m.z1_end_m))
    level_face = next(m for m in faces if m.z1_m == pytest.approx(m.z1_end_m))
    assert level_nailer.z1_m == pytest.approx(roof.eave_z_m, abs=1e-9)
    assert level_face.z1_m == pytest.approx(roof.eave_z_m + rise, abs=1e-9)
    # The bottom is still set by the authored depth, so the gutter/soffit registration the
    # declaration was sized around does not move.
    assert level_face.z0_m == pytest.approx(roof.eave_z_m - inch(6).meters, abs=1e-9)


# --- 13. the wrapped (continuous standing-seam) edge ---------------------------------------

# Wall cladding and roofing in the same material over a flush edge: the catlin house's
# standing-seam wrap. The wall fixture's cladding is "wood", so the roofing here is too.
_WRAPPED_LAYERS = (
    Layer(name="deck", material_ref="wood", thickness=inch(0.75),
          function=LayerFunction.SHEATHING),
    Layer(name="foam", material_ref="polyiso", thickness=inch(6),
          function=LayerFunction.INSULATION),
    Layer(name="roofing", material_ref="wood", thickness=inch(0.5),
          function=LayerFunction.CLADDING),
)


@pytest.fixture(scope="module")
def wrapped():
    model, _findings = resolve(
        _plan(roof_layers=_WRAPPED_LAYERS, overhang=inch(0), eave_trim=None))
    return model


def test_a_wrapped_edge_swaps_the_band_for_a_corner_trim_piece(wrapped):
    """Same-material skin over a flush edge: no drip-edge band, a corner trim on each run."""
    assert _edge_cladding(wrapped) == []
    trims = [m for m in _roof(wrapped).members if m.category == "corner_trim"]
    assert len(trims) == 6
    assert {m.material for m in trims} == {"wood"}
    assert {m.connection for m in trims} == {"roof:corner-trim"}


def test_the_corner_trim_caps_the_roofing_edge(wrapped):
    """Top flush with the roofing's top surface, leg lapping down over the wall panels."""
    roof = _roof(wrapped)
    deck, foam, roofing = _WRAPPED_LAYERS
    span = max(p[1] for p in roof.footprint) - min(p[1] for p in roof.footprint)
    factor = math.hypot(1.0, (roof.ridge_z_m - roof.eave_z_m) / (span / 2.0))
    under = (deck.thickness.meters + foam.thickness.meters) * factor
    top = under + roofing.thickness.meters * factor
    eaves = [m for m in _roof(wrapped).members
             if m.category == "corner_trim" and m.z0_m == pytest.approx(m.z0_end_m)]
    assert len(eaves) == 2
    for member in eaves:
        assert member.z1_m == pytest.approx(roof.eave_z_m + top, abs=1e-9)
        assert member.z0_m == pytest.approx(roof.eave_z_m + under - inch(2).meters,
                                            abs=1e-9)


def test_a_wrapped_edge_runs_the_wall_cladding_to_the_roofing_underside(wrapped):
    """The wall's metal keeps climbing past the foam underside — there is no band left for
    it to die under, which is what makes the skin read as one continuous surface."""
    roof = _roof(wrapped)
    deck, foam, _roofing = _WRAPPED_LAYERS
    span = max(p[1] for p in roof.footprint) - min(p[1] for p in roof.footprint)
    factor = math.hypot(1.0, (roof.ridge_z_m - roof.eave_z_m) / (span / 2.0))
    member = _closure(wrapped, "W-S", "cladding")
    plane = roof_height_at(roof, member.p0)
    under = (deck.thickness.meters + foam.thickness.meters) * factor
    assert member.z1_m == pytest.approx(plane + under, abs=1e-9)
    # The sheathing still stops at the deck plane — only the cladding wraps.
    sheathing = _closure(wrapped, "W-S", "sheathing")
    assert sheathing.z1_m == pytest.approx(roof_height_at(roof, sheathing.p0), abs=1e-9)


def test_a_mixed_material_flush_edge_keeps_the_band(flush):
    """The flush fixture's wall cladding is wood and its roofing standing-seam: not one
    skin, so the conventional edge-cladding band remains."""
    assert len(_edge_cladding(flush)) == 6
    assert not [m for m in _roof(flush).members if m.category == "corner_trim"]


# --- 14. gable studs must stay inside the end-truss plane ----------------------------------

@pytest.mark.xfail(
    reason="gable studs are oriented through the wall (3.5in) instead of lying flat in the "
           "1.5in drop-truss plane, so they poke ~1in past the gable sheathing plane and "
           "show through the closure cladding. Fix belongs to resolve/framing/roof_gable.py "
           "(_gable_studs: orient=layout.truss_orient) — outside the roof-eave stream's "
           "ownership; recorded as a coordinator escape.",
    strict=False)
def test_gable_studs_lie_flat_in_the_drop_truss_plane(resolved):
    """A drop truss is a planar 1.5in assembly: its stud infill lies in the chord plane."""
    from typehaus.resolve.framing.footprint import member_footprint

    members = _roof(resolved).members
    chord = next(m for m in members if m.child_key == "truss-000-bc")
    ring, _, _ = member_footprint(chord)
    lo, hi = min(x for x, _ in ring), max(x for x, _ in ring)
    studs = [m for m in members if m.child_key.startswith("truss-000-gable-stud-")]
    assert studs
    for stud in studs:
        stud_ring, _, _ = member_footprint(stud)
        assert min(x for x, _ in stud_ring) >= lo - 1e-9
        assert max(x for x, _ in stud_ring) <= hi + 1e-9
