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
    ("wall_roof:CATLIN_EXT_2X4", "box-gutter"),
    ("wall_roof:CATLIN_EXT_2X4", "drip-edge"),
    ("wall_roof:CATLIN_EXT_2X4", "apron-flashing"),
    ("wall_roof:CATLIN_EXT_2X4", "insect-screen"),
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
    _derived, scene = _detail_scene(catlin_model, "storey_stack:rim:CATLIN_EXT_2X4|")
    tags = _component_tags(scene)
    assert {"rim-air-barrier", "rim-cavity-foam", "rim-sealant-bead"} <= tags


def test_rim_band_seals_at_both_plate_lines(catlin_model):
    """Two beads, not one: the plate below and the plate above are separate joints."""
    _derived, scene = _detail_scene(catlin_model, "storey_stack:rim:CATLIN_EXT_2X4|")
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
        catlin_model, "stack_width_change:CATLIN_INT_2X6_BRG|INT_2X4_PARTITION")
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
