"""WP2.6/2.7 — drawing IR scene, floorplan builder, DXF/PDF/raster writers (→ 20)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from typehaus.emit.draw import build_floorplan, write_dxf, write_pdf, write_raster
from typehaus.emit.draw.scene import Polyline, Scene, Symbol, Text
from typehaus.resolve import resolve
from typehaus.source import load_plan


@pytest.fixture(scope="module")
def model(starter_dir: Path):
    result = load_plan(starter_dir)
    m, _ = resolve(result.plan)
    return m


@pytest.fixture(scope="module")
def scene(model) -> Scene:
    return build_floorplan(model, "main")


def test_scene_is_pure_data_json_snapshot(scene: Scene):
    # Frozen pure-data records → deterministic JSON snapshot (golden-testable).
    assert scene.to_json() == scene.to_json()
    assert scene.name == "plan-main"


def test_floorplan_has_framing_and_aia_layers(scene: Scene):
    layers = scene.by_layer()
    assert "A-WALL" in layers          # wall linework
    assert "S-FRAM" in layers          # real framing members (signature look)
    assert "A-ANNO-DIMS" in layers     # auto dimension chain
    # framing members carry element provenance for XDATA
    fram = [n for n in layers["S-FRAM"] if isinstance(n, Polyline)]
    assert fram and all(n.uid for n in fram)


def test_floorplan_marks_windows_by_schedule_mark_and_carries_door_handing(scene: Scene,
                                                                          model):
    """The plan says which A-601 row, not which plan-source element.

    It printed ``WIN-101`` — the authoring tag — beside every unit, which at 2.2" of
    building is under the writers' 4 pt legibility floor at any scale a floor plan is drawn
    at. What is there now is the type's schedule mark, in a bubble.
    """
    from typehaus.emit.draw.plan_marks import opening_type_marks

    symbols = [node for node in scene.nodes if isinstance(node, Symbol)]
    windows = [node for node in symbols if node.name == "window-mark"]
    doors = [node for node in symbols if node.name == "door-swing"]
    labels = {node.content for node in scene.nodes if isinstance(node, Text)}
    assert windows and doors
    assert all(node.layer == "A-GLAZ" and node.params["width_in"] > 0 for node in windows)
    assert all(node.params["swing_sign"] in {-1, 1} for node in doors)

    marks = opening_type_marks(model)
    window = next(op for op in model.openings if op.tag == "WIN-101")
    assert "WIN-101" not in labels
    assert marks[window.type_ref] in labels


def test_the_architectural_plan_carries_no_raw_element_tag(scene: Scene):
    """No node's *text* may be an authoring tag — the drawing is not the plan source.

    Openings, placeables, rooms and floor-heat zones must never print their raw tag
    (``op.tag``, ``type_ref``, ``room.tag``, ``zone.tag``) — a 1/4"-scale plan of dashed
    uppercase is unreadable. Element provenance still travels on ``Polyline.tag``/``uid``
    for XDATA and hit-testing, which is where it belongs.
    """
    tagged = {node.tag for node in scene.nodes if getattr(node, "tag", None)}
    printed = {node.content for node in scene.nodes if isinstance(node, Text)}
    assert tagged, "the drawing must still carry element provenance"
    assert not (printed & tagged), printed & tagged


def test_every_plan_label_is_a_printed_size(scene: Scene):
    """``height_pt`` throughout: annotation is paper, not building (→ scene.py, typography).

    A ``Text.height`` of 2.2 model inches is 4.7 pt at 3/16" = 1'-0" and 1.6 pt at 1/16" —
    which is why the old plan's lettering vanished at small scale and swamped the drawing
    at large. Every label the plan builds now states the size it prints at.
    """
    unsized = [node.content for node in scene.nodes
               if isinstance(node, Text) and node.height_pt is None]
    assert not unsized, unsized


def test_the_architectural_plan_leaves_the_trade_devices_to_their_own_sheets() -> None:
    """No ``E-POWR`` / ``M-EQPT`` content on A-1xx (→ ``ARCHITECTURAL_DOMAINS``). Electrical
    devices, mechanical registers and floor heat belong on E-10x/M-10x via
    ``_shared.emit_floor_heat``, not on the architectural plan.
    """
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    model, _ = resolve(load_plan(house).plan)
    for storey in ("main", "second", "basement"):
        layers = build_floorplan(model, storey).by_layer()
        assert "E-POWR" not in layers and "M-EQPT" not in layers, storey
        assert "A-FLR-HEAT" not in layers, storey


def test_floorplan_door_symbol_reflects_both_handing_flips(model):
    flipped = copy.deepcopy(model)
    door = flipped.plan.by_tag("D-101")
    replacement = door.model_copy(update={"flip_hinge": True, "flip_swing": True})
    flipped.plan = flipped.plan.with_elements(
        "main", [replacement if item.tag == door.tag else item
                 for item in flipped.plan.storey_elements("main")],
    )
    symbols = [node for node in build_floorplan(flipped, "main").nodes if isinstance(node, Symbol)]
    (door_symbol,) = [node for node in symbols if node.name == "door-swing"]
    assert door_symbol.params["swing_sign"] == -1


def test_dxf_round_trips_with_layers_and_units(scene: Scene, tmp_path: Path):
    import ezdxf

    path = write_dxf(scene, tmp_path / "plan.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1  # inches, INSUNITS=1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"A-WALL", "S-FRAM", "A-ANNO-DIMS"} <= names
    assert len(list(doc.modelspace())) > 10


def test_pdf_and_raster_write(scene: Scene, tmp_path: Path):
    pdf = write_pdf(scene, tmp_path / "plan.pdf")
    png = write_raster(scene, tmp_path / "plan.png")
    assert pdf.stat().st_size > 0
    assert png.stat().st_size > 0


def test_render_views_per_storey(model, tmp_path: Path):
    from typehaus.emit.draw import render_views

    paths = render_views(model, tmp_path / "r", view="plan")
    assert paths and all(p.suffix == ".png" and p.exists() for p in paths)


def test_render_plan_draws_the_storey_reference_underlay(model, tmp_path: Path):
    """``haus render`` is the only place an underlay has a job, so it has to reach the page.

    The check is that the *pixels change*: the plan renders identically without the
    underlay, and once one is passed for that storey the raster differs. A storey with no
    matching underlay must be untouched, or the survey would bleed onto every sheet.
    """
    import matplotlib.image as mpimg
    import numpy as np

    from typehaus.emit.draw import Underlay, render_plan, render_views

    storey = next(s.tag for s in model.plan.storeys
                  if any(w.storey == s.tag for w in model.walls))
    source = tmp_path / "ref.png"
    mpimg.imsave(source, np.tile(np.linspace(0.0, 1.0, 64), (64, 1)), cmap="gray")

    plain = render_plan(model, storey, tmp_path / "plain.png")
    over = render_plan(model, storey, tmp_path / "over.png", underlays=[
        Underlay(image_path=source, origin_x_m=0.0, origin_y_m=0.0,
                 width_m=11.0, height_m=11.0, opacity=0.3, storey=storey)])
    assert plain.read_bytes() != over.read_bytes()

    # Storey matching: an underlay tagged for another storey never reaches this page.
    written = render_views(model, tmp_path / "r2", view="plan", underlays=[
        Underlay(image_path=source, origin_x_m=0.0, origin_y_m=0.0,
                 width_m=11.0, height_m=11.0, opacity=0.3, storey="not-a-storey")])
    same = next(p for p in written if p.stem == f"plan_{storey}")
    assert same.read_bytes() == plain.read_bytes()


def test_emit_fixtures_draws_the_generated_glyph_as_plain_polylines() -> None:
    """The whole point of generating geometry in the engine: PDF and DXF need no new ``Symbol``
    branch, because a sofa arrives as more polylines on the layer the outline already used."""
    from typehaus.emit.draw import build_floorplan

    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    model, _ = resolve(load_plan(house).plan)
    furniture = [node for node in build_floorplan(model, "main").by_layer()["A-FURN"]
                 if isinstance(node, Polyline)]

    sofa = next(item for item in model.canvas_objects if item.type_ref == "FURN-SOFA-84")
    drawn = [node for node in furniture if node.uid == sofa.uid]
    assert len(drawn) > 1, "the resolved outline plus every generated stroke"
    assert drawn[0].closed and drawn[0].lineweight == 0.25, "the footprint stays the heavy outline"
    assert all(node.tag == sofa.tag for node in drawn), "every stroke keeps element provenance"
    # Glyph geometry is placed, not local: it has to land on top of the object it belongs to.
    inches = [point for node in drawn[1:] for point in node.points]
    center = [part * 39.37007874015748 for part in sofa.position]
    assert max(abs(x - center[0]) for x, _ in inches) < 60
    assert max(abs(y - center[1]) for _, y in inches) < 60


def test_room_blocks_say_name_area_and_ceiling_height() -> None:
    """A room label states name, area and ceiling height. 8'-10 9/16" is what the main
    floor's 9'-0" nominal resolves to under 5/8" gypsum on the second floor's deck
    (``ResolvedCeiling`` carries it per deck region).
    """
    from typehaus.emit.draw.plan_labels import room_display_name

    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    model, _ = resolve(load_plan(house).plan)
    printed = {node.content for node in build_floorplan(model, "main").nodes
               if isinstance(node, Text) and node.layer == "A-AREA-IDEN"}
    assert room_display_name("RM-M-LIVING") == "LIVING"
    assert {"LIVING", "748 SF", 'CLG 8\'-10 9/16"'} <= printed


def test_a_room_over_two_ceiling_planes_labels_both() -> None:
    """``RM-B-GYM`` resolves TWO ceilings and the plan states both, on their own regions.

    234 SF at 8'-0 15/16" under ``FS-M-EAST``'s I-joists and 90 SF at 7'-11 3/8" under
    ``SL-M-DECK``'s cast deck — the 1 9/16" step one flat bearing seat costs
    (houses/catlin/CLAUDE.md). Collapsing them to one number, or picking the bigger, would
    put a step the house is built with on no drawing at all.

    ``RM-M-LIVING`` is the control: it resolves FOUR ceiling records across the second
    floor's truss/I-joist split, all on one plane, and gets ONE caption — a deck seam is
    not a step.
    """
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    model, _ = resolve(load_plan(house).plan)
    printed = [node.content for node in build_floorplan(model, "basement").nodes
               if isinstance(node, Text) and node.layer == "A-AREA-IDEN"]
    assert 'CLG 8\'-0 15/16" / 234 SF' in printed
    assert 'CLG 7\'-11 3/8" / 90 SF' in printed

    assert len([c for c in model.ceilings if c.room_ref == "RM-M-LIVING"]) == 4
    main = [node.content for node in build_floorplan(model, "main").nodes
            if isinstance(node, Text) and node.layer == "A-AREA-IDEN"]
    # The per-region caption form (``CLG <height> / <area> SF``) is what a split looks like,
    # and no main-storey room has one: LIVING's four records are one plane.
    assert 'CLG 8\'-10 9/16"' in main
    assert not [c for c in main if c.startswith("CLG") and " / " in c], main


def test_a_follow_roof_ceiling_states_that_rather_than_a_number() -> None:
    """The whole attic is ``FollowRoof``: ``z0_m`` is None and there is no plane to print."""
    house = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    model, _ = resolve(load_plan(house).plan)
    printed = {node.content for node in build_floorplan(model, "attic").nodes
               if isinstance(node, Text) and node.layer == "A-AREA-IDEN"}
    assert "CLG FOLLOWS ROOF" in printed
    assert not any(c.startswith("CLG ") and c != "CLG FOLLOWS ROOF" for c in printed)
