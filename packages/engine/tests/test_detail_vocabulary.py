"""Per-detail drawing vocabulary dispatched off ``Transition.overlay`` recipe ids.

Companion to ``test_transition_details.py`` (which covers the eave and foundation recipes)
and ``test_catlin_reference_parity.py`` (which covers dimensional parity). This file covers
the dispatch layer itself, the recipes added on top of it (rim band, stepped-wall shelf,
foundation-foam protection), and the invariant that binds them all: **a detail component is
polyline + hatch geometry, never a ``Symbol``** — an unknown ``Symbol`` degrades to a bare
circle in ``DetailCanvas.tsx`` and to a marker glyph in ``pdf_writer.py``.

Assertions are about vocabulary and gating, not pixels: which components appear at which
junction, and — just as important — which junctions correctly draw nothing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from typehaus.emit.draw.details import build_detail, derive_detail_slices
from typehaus.emit.draw.scene import Hatch, Polyline
from typehaus.quantities import inch

FIXTURES = Path(__file__).parent / "fixtures" / "catlin_reference"


def _reference(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def _detail_scene(model, key_prefix: str):
    derived = next((d for d in derive_detail_slices(model)
                    if d.key.startswith(key_prefix)), None)
    assert derived is not None, f"catlin should scaffold a {key_prefix!r} detail"
    scene, _findings = build_detail(model, derived)
    return derived, scene


def _exact_detail_scene(model, key: str):
    """Like ``_detail_scene`` but keyed exactly — a prefix would also match ``key|OTHER``."""
    derived = next((d for d in derive_detail_slices(model) if d.key == key), None)
    assert derived is not None, f"catlin should scaffold the {key!r} detail"
    scene, _findings = build_detail(model, derived)
    return derived, scene


def _component_tags(scene) -> set[str]:
    return {str(node.tag).split(":", 1)[1] for node in scene.nodes
            if str(getattr(node, "tag", "")).startswith("detail-component:")}


def _component_nodes(scene, name: str):
    return [node for node in scene.nodes
            if getattr(node, "tag", None) == f"detail-component:{name}"]


def _authored_scene(model, slice_tag: str):
    from typehaus.emit.draw.details import build_authored_detail_scene

    view = next(s for s in model.plan.elements_of_kind("Slice") if s.tag == slice_tag)
    return build_authored_detail_scene(model, view)


# --- the dispatch layer -------------------------------------------------------

def test_every_authored_overlay_id_is_accounted_for(catlin_model):
    """A recipe id either draws something or records why it does not.

    The point of the registry is that an overlay id is never silently inert. A new id landing
    in the house's transitions with neither a recipe nor a recorded reason is a gap, and this
    is the test that refuses to let it pass unnoticed.
    """
    from typehaus.emit.draw.detail_components import OVERLAY_RECIPES, UNDRAWN_RECIPES

    authored = {t.overlay for t in catlin_model.plan.library.transitions if t.overlay}
    assert authored, "catlin authors overlay recipe ids"
    unaccounted = authored - set(OVERLAY_RECIPES) - set(UNDRAWN_RECIPES)
    assert not unaccounted, (
        f"overlay ids {sorted(unaccounted)} dispatch nothing and record no reason — add a "
        f"recipe to OVERLAY_RECIPES or an explanation to UNDRAWN_RECIPES"
    )


def test_recipes_and_reasons_do_not_overlap():
    """An id that draws must not also claim to be undrawn — the two lists are exclusive."""
    from typehaus.emit.draw.detail_components import OVERLAY_RECIPES, UNDRAWN_RECIPES

    assert not set(OVERLAY_RECIPES) & set(UNDRAWN_RECIPES)
    assert all(reason.strip() for reason in UNDRAWN_RECIPES.values())


def test_a_detail_with_no_overlay_recipe_still_builds(catlin_model):
    """``assembly-change-jog`` deliberately draws nothing; the sheet must still compose."""
    _derived, scene = _detail_scene(catlin_model, "assembly_change:")
    assert scene.nodes, "the cut itself still draws even when the recipe adds nothing"


# --- the polyline/hatch invariant --------------------------------------------

def test_no_detail_component_is_ever_a_symbol(catlin_model):
    """Across *every* derived detail: components are polylines and hatches only.

    A ``Symbol`` has no geometry the writers can draw — it renders as a bare circle in the UI
    canvas and as a marker glyph in the PDF — so a component that reaches for one silently
    turns a flashing profile into a dot.
    """
    for derived in derive_detail_slices(catlin_model):
        scene, _findings = build_detail(catlin_model, derived)
        for node in scene.nodes:
            if not str(getattr(node, "tag", "")).startswith("detail-component:"):
                continue
            assert isinstance(node, (Polyline, Hatch)), (
                f"{derived.key}: component {node.tag} is a {type(node).__name__}"
            )


@pytest.mark.parametrize("key_prefix,name", [
    # The house eave defers to its authored gutter/drip (params/roof_trim.py), so the
    # schematic pair is exercised on the garage eave, which has no authored trim yet.
    ("wall_roof:GARAGE_ROOF", "box-gutter"),
    ("wall_roof:GARAGE_ROOF", "drip-edge"),
    ("wall_roof:CATLIN_EXT_2X6", "apron-flashing"),
    ("wall_roof:CATLIN_EXT_2X6", "insect-screen"),
    ("wall_foundation:CATLIN_BASEMENT_12", "z-flashing"),
    ("wall_foundation:CATLIN_BASEMENT_12", "l-flashing"),
    ("wall_foundation:CATLIN_BASEMENT_12", "sealant-bead"),
    ("wall_foundation:CATLIN_BASEMENT_12", "sill-gasket"),
])
def test_component_is_drawn_as_a_closed_outline_with_a_fill(catlin_model, key_prefix, name):
    """Each named component draws a closed outline, and a hatch shares its boundary."""
    _derived, scene = _detail_scene(catlin_model, key_prefix)
    outlines = _component_nodes(scene, name)
    assert outlines, f"{key_prefix} should draw {name}"
    for outline in outlines:
        assert isinstance(outline, Polyline) and outline.closed
        assert len(outline.points) >= 4
    boundaries = {tuple(h.boundary) for h in scene.nodes if isinstance(h, Hatch)}
    assert any(tuple(o.points) in boundaries for o in outlines), (
        f"{name} draws an outline with no fill behind it"
    )


# --- rim band -----------------------------------------------------------------

def test_rim_band_air_seal_draws_the_air_control_vocabulary(catlin_model):
    """The floor band interrupts the sheathing, so the drawing has to close it.

    Reference: the basement→framed notes' "prioritize air sealing at sill plate (sealant +
    spray foam)", applied at every floor line rather than only the first.
    """
    _derived, scene = _detail_scene(catlin_model, "storey_stack:rim:CATLIN_EXT_2X6")
    tags = _component_tags(scene)
    assert {"rim-air-barrier", "rim-cavity-foam", "rim-sealant-bead"} <= tags


def test_rim_band_seals_at_both_plate_lines(catlin_model):
    """Two beads, not one: the plate below and the plate above are separate joints."""
    _derived, scene = _detail_scene(catlin_model, "storey_stack:rim:CATLIN_EXT_2X6")
    beads = _component_nodes(scene, "rim-sealant-bead")
    elevations = sorted({round(min(z for _u, z in bead.points), 3) for bead in beads})
    assert len(elevations) == 2, f"expected a bead at each plate line, got {elevations}"


def test_interior_partition_rim_gets_no_air_seal(catlin_model):
    """An interior partition has conditioned space on both sides — nothing to seal against."""
    _derived, scene = _exact_detail_scene(catlin_model,
                                          "storey_stack:rim:CATLIN_INT_2X6_BRG")
    assert not _component_tags(scene) & {
        "rim-air-barrier", "rim-cavity-foam", "rim-sealant-bead"}


# --- stepped-wall shelf -------------------------------------------------------

def test_stepped_wall_leaves_a_flashed_shelf(catlin_model):
    """The garage framed wall steps in over its ICF stem, leaving a weather ledge."""
    _derived, scene = _detail_scene(catlin_model,
                                    "stack_width_change:GARAGE_ICF_8|GARAGE_WALL_2X6")
    flashings = _component_nodes(scene, "stack-shelf-flashing")
    assert flashings, "an exposed ledge over a wider wall below has to be flashed"
    for flashing in flashings:
        assert isinstance(flashing, Polyline) and flashing.closed


def test_shelf_flashing_falls_away_from_the_wall(catlin_model):
    """A shelf that does not drain is a water trap — the profile must slope outward."""
    from typehaus.emit.draw.detail_components import STACK_WIDTH_SHELF

    _derived, scene = _detail_scene(catlin_model,
                                    "stack_width_change:GARAGE_ICF_8|GARAGE_WALL_2X6")
    flashing = _component_nodes(scene, "stack-shelf-flashing")[0]
    z_span = max(z for _u, z in flashing.points) - min(z for _u, z in flashing.points)
    assert z_span > STACK_WIDTH_SHELF.slope_fall_in


def test_interior_partition_step_gets_no_shelf_flashing(catlin_model):
    """An interior wall stepping in leaves no weather ledge — flashing it would be fiction."""
    _derived, scene = _detail_scene(
        catlin_model, "stack_width_change:INT_2X4_PARTITION|INT_2X6_PLUMBING")
    assert "stack-shelf-flashing" not in _component_tags(scene)


# --- foundation face ----------------------------------------------------------

def test_exposed_foundation_foam_is_protected(catlin_model):
    """The garage ICF stem stands proud of grade, so its EPS needs a protection board.

    Reference: ``garage_wall_detail_side_ifc.png`` — "protective coating over exposed ICF EPS
    (above grade, both sides)".
    """
    _derived, scene = _detail_scene(catlin_model, "wall_foundation:GARAGE_ICF_8")
    boards = _component_nodes(scene, "foam-protection-board")
    assert boards, "foam surfacing above grade must be shown protected"
    board = boards[0]
    assert isinstance(board, Polyline) and board.closed


def test_protection_board_starts_at_grade(catlin_model):
    """It protects the *exposed* height only — below grade the backfill does that job."""
    from typehaus.emit.draw.detail_components import M_TO_IN

    _derived, scene = _detail_scene(catlin_model, "wall_foundation:GARAGE_ICF_8")
    board = _component_nodes(scene, "foam-protection-board")[0]
    grade_in = catlin_model.plan.project.site.grade.meters * M_TO_IN
    assert min(z for _u, z in board.points) == pytest.approx(grade_in, abs=0.5)


def test_buried_foundation_foam_gets_no_protection_board(catlin_model):
    """The house basement's XPS tops out at grade — nothing is exposed to protect."""
    _derived, scene = _detail_scene(catlin_model, "wall_foundation:CATLIN_BASEMENT_12")
    assert "foam-protection-board" not in _component_tags(scene)


# --- dimensional parity for the drawn vocabulary ------------------------------

def test_sill_gasket_is_the_reference_quarter_inch(catlin_model):
    from typehaus.emit.draw.detail_components import BASEMENT_TO_FRAMED_WALL

    expected = float(_reference("basementtoframedwalldetail")["sill"]["gasket_in"])
    assert BASEMENT_TO_FRAMED_WALL.sill_gasket_in == pytest.approx(expected)

    _derived, scene = _detail_scene(catlin_model, "wall_foundation:CATLIN_BASEMENT_12")
    gasket = _component_nodes(scene, "sill-gasket")[0]
    height = (max(z for _u, z in gasket.points) - min(z for _u, z in gasket.points))
    assert height == pytest.approx(expected, abs=1e-6)


def test_slab_thermal_break_and_sealant_match_the_reference(catlin_model):
    from typehaus.emit.draw.detail_components import SLAB_EDGE

    slab = _reference("basementconstruction")["slab"]
    assert SLAB_EDGE.thermal_break_in == pytest.approx(float(slab["thermal_break_in"]))
    assert SLAB_EDGE.sealant_cap_in == pytest.approx(float(slab["sealant_in"]))

    _derived, scene = _detail_scene(catlin_model, "wall_foundation:GARAGE_ICF_8")
    breaks = _component_nodes(scene, "thermal-break")
    assert breaks
    width = (max(u for u, _z in breaks[0].points) - min(u for u, _z in breaks[0].points))
    assert width == pytest.approx(SLAB_EDGE.thermal_break_in, abs=1e-6)


def test_perimeter_drain_config_matches_the_reference(catlin_model):
    """The drain's own dimensions have no model field to live on yet — pin them here.

    ``FootingBedding`` models drain tile as a bare ``drain_tile: bool``, so the 4" pipe and
    its 10"x8" rock surround are configuration in the view. This is the test that keeps that
    configuration honest against the reference until the model grows the fields.
    """
    from typehaus.emit.draw.detail_components import PERIMETER_DRAIN

    foundation = _reference("basementconstruction")["foundation"]
    assert PERIMETER_DRAIN.drain_diameter_in == pytest.approx(
        float(foundation["french_drain_diameter_in"]))
    assert PERIMETER_DRAIN.rock_width_in == pytest.approx(
        float(foundation["river_rock_width_in"]))
    assert PERIMETER_DRAIN.rock_depth_in == pytest.approx(
        float(foundation["river_rock_depth_in"]))


def test_french_drain_draws_its_configured_size():
    """The drawn pipe and rock trench are the config, not numbers inlined at the call site."""
    from typehaus.emit.draw.detail_components import PERIMETER_DRAIN, french_drain

    nodes = french_drain(center_u=0.0, invert_z=0.0)
    rock = next(n for n in nodes if getattr(n, "tag", None) == "detail-component:river-rock")
    rock_width = max(u for u, _z in rock.points) - min(u for u, _z in rock.points)
    rock_depth = max(z for _u, z in rock.points) - min(z for _u, z in rock.points)
    assert rock_width == pytest.approx(PERIMETER_DRAIN.rock_width_in)
    assert rock_depth == pytest.approx(PERIMETER_DRAIN.rock_depth_in)

    pipe = next(n for n in nodes
                if getattr(n, "tag", None) == "detail-component:french-drain")
    bore = max(u for u, _z in pipe.points) - min(u for u, _z in pipe.points)
    assert bore == pytest.approx(PERIMETER_DRAIN.drain_diameter_in)


# --- sauna --------------------------------------------------------------------

def test_sauna_room_vocabulary_is_polyline_geometry(catlin_model):
    """Benches, heater clearance, floor slope and drop ceiling all draw as real geometry."""
    scene = _authored_scene(catlin_model, "SL-D-SAUNA")
    tags = _component_tags(scene)
    assert {"sauna-bench", "sauna-heater", "sauna-floor-slope", "sauna-drop-ceiling",
            "sauna-baseboard"} <= tags
    for node in scene.nodes:
        if str(getattr(node, "tag", "")).startswith("detail-component:sauna"):
            assert isinstance(node, (Polyline, Hatch))


def test_sauna_heater_clearance_is_an_open_dashed_zone(catlin_model):
    """A keep-clear envelope, not built fabric: dashed and unfilled, or it reads as a cabinet."""
    scene = _authored_scene(catlin_model, "SL-D-SAUNA")
    heater = _component_nodes(scene, "sauna-heater")[0]
    assert heater.linetype == "DASHED" and heater.closed
    boundaries = {tuple(h.boundary) for h in scene.nodes if isinstance(h, Hatch)}
    assert tuple(heater.points) not in boundaries


def test_sauna_floor_falls_to_its_drain(catlin_model):
    """The screed wedge is high away from the drain — the fall is what the drawing is for."""
    scene = _authored_scene(catlin_model, "SL-D-SAUNA")
    wedge = _component_nodes(scene, "sauna-floor-slope")[0]
    drain = _component_nodes(scene, "sauna-floor-drain")[0]
    thick_end_u = min(u for u, _z in wedge.points)
    drain_u = max(u for u, _z in drain.points)
    assert thick_end_u < drain_u, "the screed must be thickest away from the drain"


# --- opening-perimeter details ------------------------------------------------

def test_opening_and_ridge_conditions_scaffold_detail_slices(catlin_model):
    """opening_perimeter and roof_ridge conditions now derive details of their own.

    The opening's tag is not a wall tag, so the host wall is reached through
    ``ResolvedOpening.host_wall``; the ridge has no wall at all and frames its cut off
    the resolved ridge-beam member.
    """
    keys = {d.key for d in derive_detail_slices(catlin_model)}
    assert "opening_perimeter:CATLIN_EXT_2X6" in keys
    assert "opening_perimeter:CATLIN_BASEMENT_12" in keys
    assert "roof_ridge:RF-HOUSE" in keys


def test_opening_crop_holds_sill_and_head(catlin_model):
    """The z-window measures below from the sill and above from the head — the crop has
    to hold the whole opening or the head/sill vocabulary lands outside the drawing."""
    from typehaus.emit.draw.detail_components import M_TO_IN, condition_opening

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "opening_perimeter:CATLIN_EXT_2X6")
    opening = condition_opening(catlin_model, derived.condition)
    host = catlin_model.wall(opening.host_wall)
    (_u0, cz0), (_u1, cz1) = derived.view.crop[0].xy_m, derived.view.crop[1].xy_m
    sill_z = host.z0_m + opening.sill_m
    head_z = sill_z + opening.height_m
    assert min(cz0, cz1) < sill_z and head_z < max(cz0, cz1)


def test_opening_cut_station_crosses_the_opening(catlin_model):
    """The cut runs through the opening's center along the wall, not the wall midpoint."""
    from typehaus.emit.draw.detail_components import condition_opening

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "opening_perimeter:CATLIN_EXT_2X6")
    opening = condition_opening(catlin_model, derived.condition)
    host = catlin_model.wall(opening.host_wall)
    (x0, y0), (x1, y1) = host.axis
    # The station is on the axis perpendicular to u; recover the along-axis position.
    along = derived.station
    import math
    length = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    expected = (x0 + ux * opening.center_along_m if derived.direction == "y"
                else y0 + uy * opening.center_along_m)
    assert along == pytest.approx(expected, abs=1e-6)


def test_framed_weather_opening_draws_head_flashing_and_sill_pan(catlin_model):
    _derived, scene = _exact_detail_scene(catlin_model, "opening_perimeter:CATLIN_EXT_2X6")
    tags = _component_tags(scene)
    assert {"opening-head-flashing", "opening-sill-pan", "opening-sealant"} <= tags


def test_interior_opening_gets_no_applied_vocabulary(catlin_model):
    """An interior door sheds no weather — flashing it would be fiction (id stays in
    UNDRAWN_RECIPES with its reason on the record)."""
    _derived, scene = _exact_detail_scene(catlin_model,
                                          "opening_perimeter:INT_2X4_PARTITION")
    assert not _component_tags(scene) & {
        "opening-head-flashing", "opening-sill-pan", "opening-buck"}


def test_concrete_opening_draws_a_sealed_buck(catlin_model):
    _derived, scene = _exact_detail_scene(catlin_model,
                                          "opening_perimeter:CATLIN_CONC_12_INT")
    tags = _component_tags(scene)
    assert {"opening-buck", "opening-sealant"} <= tags


def test_sauna_opening_returns_the_foil_face(catlin_model):
    """The door punches the hot side's vapour plane; the foil is returned, not butted."""
    _derived, scene = _exact_detail_scene(catlin_model, "opening_perimeter:SAUNA_2X4")
    assert "sauna-foil-return" in _component_tags(scene)


# --- ridge --------------------------------------------------------------------

def test_ridge_detail_draws_hangers_on_both_beam_faces(catlin_model):
    """The lvl-ridge-hanger overlay: one face-mount hanger each side of the beam."""
    _derived, scene = _exact_detail_scene(catlin_model, "roof_ridge:RF-HOUSE")
    hangers = _component_nodes(scene, "ridge-hanger")
    assert len(hangers) == 2
    for hanger in hangers:
        assert isinstance(hanger, Polyline) and hanger.closed


def test_ridge_beam_width_parses_multi_ply_lvl():
    from typehaus.emit.draw.detail_components.ridge import beam_width_in

    assert beam_width_in("3-1.75x11.875 LVL") == pytest.approx(5.25)
    assert beam_width_in("2x12") == pytest.approx(2.0)
    assert beam_width_in("mystery") == pytest.approx(1.5)


# --- shower -------------------------------------------------------------------

def _shower_slice():
    """A documentation slice through the ensuite shower (FX-S-ENSUITE-SH at x~1.5 m)."""
    from typehaus.model.enums import SliceKind
    from typehaus.model.views import Slice
    from typehaus.quantities import m
    from typehaus.quantities import pt as qpt

    return Slice(uid="", tag="TEST-D-SHOWER", kind=SliceKind.DETAIL,
                 title="Shower section", cut_origin=qpt(m(1.524), m(10.0)),
                 cut_direction="y",
                 crop=(qpt(m(8.4), m(2.7)), qpt(m(11.3), m(5.8))))


def test_shower_vocabulary_is_gated_on_the_fixture(catlin_model):
    """No shower assembly exists — the recognition gate is the resolved fixture whose
    type publishes ``plan_symbol="shower"``, cut by the section plane."""
    from typehaus.emit.draw.details import build_authored_detail_scene

    scene = build_authored_detail_scene(catlin_model, _shower_slice())
    tags = _component_tags(scene)
    assert {"shower-recess", "shower-tile", "shower-backer", "shower-glass",
            "shower-drain"} <= tags
    for node in scene.nodes:
        if str(getattr(node, "tag", "")).startswith("detail-component:shower"):
            assert isinstance(node, (Polyline, Hatch))


def test_shower_dimensions_match_the_reference(catlin_model):
    from typehaus.emit.draw.detail_components import (
        SHOWER_BACKER_IN,
        SHOWER_GLASS_GAP_IN,
        SHOWER_GLASS_IN,
        SHOWER_HRV_DUCT_IN,
        SHOWER_RECESS_IN,
        SHOWER_TILE_IN,
    )
    from typehaus.emit.draw.details import build_authored_detail_scene

    ref = _reference("saunashowerdetail")["shower"]
    assert SHOWER_TILE_IN == pytest.approx(float(ref["tile_in"]))
    assert SHOWER_BACKER_IN == pytest.approx(float(ref["wall_backer_in"]))
    assert SHOWER_GLASS_IN == pytest.approx(float(ref["glass_in"]))
    assert SHOWER_GLASS_GAP_IN == pytest.approx(float(ref["glass_gap_in"]))
    assert SHOWER_RECESS_IN == pytest.approx(float(ref["recess_in"]))
    assert SHOWER_HRV_DUCT_IN == pytest.approx(float(ref["hrv_duct_in"]))

    scene = build_authored_detail_scene(catlin_model, _shower_slice())
    glass = _component_nodes(scene, "shower-glass")[0]
    thickness = (max(u for u, _z in glass.points) - min(u for u, _z in glass.points))
    assert thickness == pytest.approx(SHOWER_GLASS_IN, abs=1e-6)
    recess = _component_nodes(scene, "shower-recess")[0]
    depth = (max(z for _u, z in recess.points) - min(z for _u, z in recess.points))
    assert depth == pytest.approx(SHOWER_RECESS_IN, abs=1e-6)


def test_shower_tile_rides_on_backer_on_the_walled_side(catlin_model):
    """Backer against the wall face, tile inboard of it — read from the resolved walls."""
    from typehaus.emit.draw.detail_components import SHOWER_BACKER_IN, SHOWER_TILE_IN
    from typehaus.emit.draw.details import build_authored_detail_scene

    scene = build_authored_detail_scene(catlin_model, _shower_slice())
    backers = _component_nodes(scene, "shower-backer")
    assert backers
    backer = backers[0]
    width = (max(u for u, _z in backer.points) - min(u for u, _z in backer.points))
    assert width == pytest.approx(SHOWER_BACKER_IN, abs=1e-6)
    walls = [n for n in _component_nodes(scene, "shower-tile")
             if (max(z for _u, z in n.points) - min(z for _u, z in n.points)) > 12.0]
    assert walls, "a wall tile band should stand on the walled side"
    assert (max(u for u, _z in walls[0].points)
            - min(u for u, _z in walls[0].points)) == pytest.approx(SHOWER_TILE_IN,
                                                                    abs=1e-6)


def test_shower_hrv_duct_draws_from_model_ducts(catlin_model):
    """The takeoff draws only when a resolved run actually crosses the cut over the
    shower, at the run's own resolved size — never from an invented duct."""
    from typehaus.emit.draw.detail_components import M_TO_IN
    from typehaus.emit.draw.details import build_authored_detail_scene
    from typehaus.resolve.model import ResolvedDuct

    scene = build_authored_detail_scene(catlin_model, _shower_slice())
    assert not _component_nodes(scene, "shower-hrv-duct"), (
        "catlin routes no duct over the ensuite shower yet — drawing one would lie")

    duct = ResolvedDuct(uid="TESTDUCT01", tag="DU-S-HRV-SH", storey="second",
                        system="hrv", path=((1.0, 10.2), (2.0, 10.2)),
                        width_m=3.0 / M_TO_IN, depth_m=3.0 / M_TO_IN,
                        routing="ceiling", floor_ref=None, crossings=(), conflicts=(),
                        depth_ok=True)
    catlin_model.ducts.append(duct)
    try:
        scene = build_authored_detail_scene(catlin_model, _shower_slice())
        drawn = _component_nodes(scene, "shower-hrv-duct")
        assert drawn
        width = (max(u for u, _z in drawn[0].points)
                 - min(u for u, _z in drawn[0].points))
        assert width == pytest.approx(3.0, abs=1e-6)
    finally:
        catlin_model.ducts.remove(duct)


def test_sauna_slice_draws_no_shower_vocabulary(catlin_model):
    """The basement sauna section has no shower fixture in its cut — nothing to draw."""
    scene = _authored_scene(catlin_model, "SL-D-SAUNA")
    assert not {t for t in _component_tags(scene) if t.startswith("shower")}


# --- model-driven dimensions (DrainTile / sill_gasket / thermal break) ---------

def test_french_drain_draws_the_authored_diameter():
    """``DrainTile.diameter`` overrides the pinned 4"; None keeps the reference."""
    from typehaus.emit.draw.detail_components import PERIMETER_DRAIN, french_drain

    nodes = french_drain(center_u=0.0, invert_z=0.0, diameter_in=6.0)
    pipe = next(n for n in nodes
                if getattr(n, "tag", None) == "detail-component:french-drain")
    bore = max(u for u, _z in pipe.points) - min(u for u, _z in pipe.points)
    assert bore == pytest.approx(6.0)

    nodes = french_drain(center_u=0.0, invert_z=0.0)
    pipe = next(n for n in nodes
                if getattr(n, "tag", None) == "detail-component:french-drain")
    bore = max(u for u, _z in pipe.points) - min(u for u, _z in pipe.points)
    assert bore == pytest.approx(PERIMETER_DRAIN.drain_diameter_in)


def test_drain_tile_spec_reads_the_footing_bedding(catlin_model):
    """Every house footing's bedding authors the 4" socked daylight tile now."""
    from typehaus.emit.draw.detail_components.below_grade import drain_tile_spec_for

    footings = [s for s in catlin_model.solids if s.category == "footing"
                and s.tag.startswith("FT-B-")]  # house footings — the ones with beddings
    assert footings
    assert drain_tile_spec_for(catlin_model, None) is None
    for footing in footings:
        spec = drain_tile_spec_for(catlin_model, footing)
        assert spec is not None, footing.tag
        assert spec.diameter == inch(4) and spec.sock and spec.discharge == "daylight"


def test_sill_gasket_prefers_the_authored_framing_spec():
    """``FramingSpec.sill_gasket`` on the assembly's structure layer wins; absent, the
    pinned reference 1/4" stands."""
    from types import SimpleNamespace

    from typehaus.emit.draw.detail_components import BASEMENT_TO_FRAMED_WALL
    from typehaus.emit.draw.detail_components.wall_base import sill_gasket_in
    from typehaus.quantities import inch

    def _model(assembly):
        library = SimpleNamespace(resolve_assembly=lambda _tag: assembly)
        return SimpleNamespace(plan=SimpleNamespace(library=library))

    wall = SimpleNamespace(assembly="STUB")
    authored = SimpleNamespace(layers=(
        SimpleNamespace(framing=None),
        SimpleNamespace(framing=SimpleNamespace(sill_gasket=inch(0.5))),
    ))
    assert sill_gasket_in(_model(authored), wall) == pytest.approx(0.5)

    bare = SimpleNamespace(layers=(SimpleNamespace(framing=None),))
    assert sill_gasket_in(_model(bare), wall) == pytest.approx(
        BASEMENT_TO_FRAMED_WALL.sill_gasket_in)
    assert sill_gasket_in(_model(None), wall) == pytest.approx(
        BASEMENT_TO_FRAMED_WALL.sill_gasket_in)


def test_thermal_break_spec_reads_the_slab_source(catlin_model):
    """``Slab.perimeter_thermal_break`` is read off the cut slab's plan source. The two
    slabs-on-grade (basement + garage) author the 1" XPS edge break; the walking-surface
    decks author none and keep the pinned fallback."""
    from typehaus.emit.draw.detail_components.wall_base import thermal_break_spec

    slabs = {s.tag: s for s in catlin_model.solids if s.category == "slab"}
    assert slabs
    for tag in ("SL-B-FLOOR", "SL-G-FLOOR"):
        spec = thermal_break_spec(catlin_model, slabs[tag])
        assert spec is not None and spec.material_ref == "xps"
        assert spec.thickness == inch(1)
    assert thermal_break_spec(catlin_model, slabs["SL-SG-DECK"]) is None


def test_thermal_break_prefers_the_authored_slab_spec():
    from types import SimpleNamespace

    from typehaus.emit.draw.detail_components.wall_base import thermal_break_spec
    from typehaus.model.floors import SlabThermalBreak
    from typehaus.quantities import inch

    spec = SlabThermalBreak(material_ref="xps", thickness=inch(1.5), depth=inch(24))
    source = SimpleNamespace(perimeter_thermal_break=spec)
    model = SimpleNamespace(plan=SimpleNamespace(by_tag=lambda _tag: source))
    found = thermal_break_spec(model, SimpleNamespace(tag="SL-STUB"))
    assert found is spec
    assert found.thickness.meters == pytest.approx(inch(1.5).meters)


# --- opening voids at detail scale (task 7) -----------------------------------

def test_no_glazing_line_spans_a_whole_detail_crop(catlin_model):
    """A void line running the full crop height reads as an error, not as a window.

    Where the cut passes through an opening with neither head nor sill in frame, the detail
    shows the neighbouring solid bands' edges instead — a centreline through the entire
    drawing tells the reader nothing about the junction the detail is about.
    """
    for derived in derive_detail_slices(catlin_model):
        crop = derived.view.crop
        if crop is None:
            continue
        from typehaus.emit.draw.detail_components import M_TO_IN

        (_cu0, cz0), (_cu1, cz1) = crop[0].xy_m, crop[1].xy_m
        span = abs(cz1 - cz0) * M_TO_IN
        scene, _findings = build_detail(catlin_model, derived)
        for node in scene.nodes:
            if not isinstance(node, Polyline) or node.layer != "A-GLAZ":
                continue
            height = max(z for _u, z in node.points) - min(z for _u, z in node.points)
            assert height < span - 1e-6, (
                f"{derived.key}: glazing line spans the whole crop"
            )
