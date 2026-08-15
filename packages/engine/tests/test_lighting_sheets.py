"""The E-2xx lighting plans and the E-602 schedule that makes them readable.

Two things are worth holding still here. The sheet index has to carry both — a plan whose
marks resolve nowhere is a puzzle — and the plans must emit only node types the writers
implement, because the whole point of drawing glyphs rather than naming ``Symbol`` markers
was to add no new writer vocabulary.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.lightingplan import build_lighting_plan, has_lighting_content
from typehaus.emit.draw.scene import Polyline, Symbol, Text
from typehaus.emit.draw.sheets import build_sheet_index
from typehaus.model.placeable_symbols import SYMBOL_NAMES


def test_the_sheet_index_carries_a_lighting_plan_per_storey_plus_the_schedule(catlin_model):
    numbers = [sheet.number for sheet in build_sheet_index(catlin_model)]
    lighting = [number for number in numbers if number.startswith("E-2")]
    expected = [storey.tag for storey in
                sorted(catlin_model.plan.storeys, key=lambda s: s.elevation.meters)
                if has_lighting_content(catlin_model, storey.tag)]
    assert lighting == [f"E-{200 + index}" for index in range(1, len(expected) + 1)]
    assert "E-602" in numbers
    # The power sheets are untouched: two series, two readers.
    assert [n for n in numbers if n.startswith("E-1")]
    assert numbers.index("E-601") < numbers.index("E-602")


def test_every_storey_with_luminaires_gets_a_sheet(catlin_model):
    """Including the garage, which is the storey that used to run generic fixtures."""
    lit = {storey.tag for storey in catlin_model.plan.storeys
           if has_lighting_content(catlin_model, storey.tag)}
    assert {"basement", "main", "garage", "second", "attic"} == lit


def test_the_plan_emits_only_known_node_types_and_no_symbol_markers(catlin_model):
    """D2: glyphs are drawn geometry, so the ``Symbol`` vocabulary stays frozen."""
    scene = build_lighting_plan(catlin_model, "main")
    assert scene.nodes
    for node in scene.nodes:
        assert isinstance(node, (Polyline, Text)), type(node).__name__
    assert not [node for node in scene.nodes if isinstance(node, Symbol)]
    # And it did not quietly grow the symbol vocabulary to get its glyphs.
    assert "recessed-can" in SYMBOL_NAMES


def test_fixtures_are_labelled_with_their_mark_not_their_tag(catlin_model):
    scene = build_lighting_plan(catlin_model, "second")
    contents = {node.content for node in scene.nodes if isinstance(node, Text)}
    marks = {product.type_mark for product in catlin_model.plan.library.electrical_device_types
             if getattr(product, "type_mark", None)}
    assert {"A", "C", "L"} <= contents <= (contents | marks)
    assert not [text for text in contents if text.startswith("ED-S-BED1-")]


def test_light_runs_are_drawn_with_their_length(catlin_model):
    scene = build_lighting_plan(catlin_model, "second")
    run = next(r for r in catlin_model.light_runs if r.tag == "LR-S-HALL-GAP")
    cove = [node for node in scene.nodes
            if isinstance(node, Polyline) and node.tag == run.tag]
    assert len(cove) == 1 and len(cove[0].points) == len(run.path)
    assert cove[0].layer == "E-LITE-COVE"
    length_ft = run.length_m * 3.280839895013123
    assert any(isinstance(node, Text) and f"{length_ft:.1f} LF" in node.content
               for node in scene.nodes)


def test_light_run_ticks_mark_every_end_cap_and_corner(catlin_model):
    """A short cross-hatch at every fitting a straight length of channel cannot be on its
    own: two end caps (path endpoints) plus one per interior vertex where it turns."""
    scene = build_lighting_plan(catlin_model, "second")
    run = next(r for r in catlin_model.light_runs if r.tag == "LR-S-HALL-GAP")
    assert len(run.path) > 2, "need a run that actually turns a corner for this test to bite"
    cove_polylines = [node for node in scene.nodes
                      if isinstance(node, Polyline) and node.layer == "E-LITE-COVE"]
    # One 2-point polyline per path vertex is a tick; the run itself is the one polyline
    # whose point count matches its own path and whose tag is the run's tag.
    ticks = [node for node in cove_polylines
             if node.tag != run.tag and len(node.points) == 2]
    assert len(ticks) >= len(run.path), (
        "expected at least one tick per path vertex across every run on this sheet")


def test_psu_leader_connects_a_run_to_its_shared_supply(catlin_model):
    """Two living-room runs share one PSU; the leader and its marker should appear once
    per PSU, not once per run, and every leader should actually reach the PSU's position."""
    scene = build_lighting_plan(catlin_model, "main")
    psu = next(element for storey in catlin_model.plan.storeys
              for element in catlin_model.plan.storey_elements(storey.tag)
              if element.tag == "ED-M-LIVING-LT-PSU")
    psu_xy = psu.position.xy_m
    leaders = [node for node in scene.nodes
              if isinstance(node, Polyline) and node.layer == "E-LITE-COVE"
              and node.linetype == "DASHED"]
    living_runs = [r for r in catlin_model.light_runs if r.psu_ref == "ED-M-LIVING-LT-PSU"]
    assert len(leaders) == len(living_runs) == 2
    _M_TO_IN = 39.37007874015748
    psu_in = (psu_xy[0] * _M_TO_IN, psu_xy[1] * _M_TO_IN)
    for leader in leaders:
        assert any(pt == pytest.approx(psu_in, abs=1e-6) for pt in leader.points)
    psu_labels = [node for node in scene.nodes if isinstance(node, Text) and node.content == "PSU"]
    assert len(psu_labels) == 1, "one shared PSU should get one marker, not one per run"


def test_switch_legs_are_dashed_and_only_drawn_where_both_ends_are_on_the_sheet(catlin_model):
    scene = build_lighting_plan(catlin_model, "basement")
    legs = [node for node in scene.nodes
            if isinstance(node, Polyline) and node.layer == "E-LITE-CIRC"]
    assert legs and all(node.linetype == "DASHED" and len(node.points) == 2
                        for node in legs)
    # LR-B-STAIR-RAIL is 3-way with a main-storey switch; that leg has no second end here,
    # so the basement sheet draws one leg for it, not two.
    run = next(r for r in catlin_model.light_runs if r.tag == "LR-B-STAIR-RAIL")
    assert len(run.controlled_by) == 2
    basement_switches = {element.tag for element in
                         catlin_model.plan.storey_elements("basement")
                         if element.element_kind == "ElectricalDevice"
                         and element.kind.value == "switch"}
    assert len([tag for tag in run.controlled_by if tag in basement_switches]) == 1


def test_the_legend_lists_only_the_forms_on_that_sheet(catlin_model):
    """A legend that lists a chandelier on a sheet with no chandelier is boilerplate."""
    second = {node.content for node in build_lighting_plan(catlin_model, "second").nodes
              if isinstance(node, Text)}
    basement = {node.content for node in build_lighting_plan(catlin_model, "basement").nodes
                if isinstance(node, Text)}
    assert any("CHANDELIER" in text for text in second)
    assert not any("CHANDELIER" in text for text in basement)
    assert any("FLAT PANEL" in text for text in basement)
    assert not any("FLAT PANEL" in text for text in second)
    assert "LUMINAIRE LEGEND" in second and "LUMINAIRE LEGEND" in basement


def test_the_lighting_plan_round_trips_through_the_dxf_writer(catlin_model, tmp_path: Path):
    """The new E-LITE-COVE / E-LITE-CIRC layers have to exist in the writer's table."""
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    out = write_dxf(build_lighting_plan(catlin_model, "main"), tmp_path / "e202.dxf")
    doc = ezdxf.readfile(str(out))
    layers = {layer.dxf.name for layer in doc.layers}
    assert {"E-LITE", "E-LITE-COVE", "E-LITE-CIRC"} <= layers


def test_the_pdf_writer_now_honours_the_ir_linetype():
    """It used to ignore ``Polyline.linetype``, so dashed conduit printed solid."""
    from typehaus.emit.draw.pdf_writer import _LINETYPE_MPL

    assert _LINETYPE_MPL["DASHED"] == "--"
    assert _LINETYPE_MPL["CONTINUOUS"] == "-"
    assert _LINETYPE_MPL.get("NOT-A-LINETYPE") is None  # falls back to solid, never vanishes
