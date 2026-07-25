"""S-100/S-101/S-102 as complete structural sheets, not reused floor or energy views.

Covers what each sheet must *carry* (footings + schedule; joist direction, headers, member
schedule; roof framing), and that each is derived from the resolved model rather than being
a copy of another sheet's builder.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.foundation_schedule import (
    build_foundation_schedules,
    footing_steps,
    foundation_general_notes,
    foundation_marks,
    foundation_sheet_findings,
    slabs_on_grade,
)
from typehaus.emit.draw.foundationplan import build_foundation_plan
from typehaus.emit.draw.framing_schedule import (
    build_framing_schedules,
    framed_level,
    framing_sheet_findings,
)
from typehaus.emit.draw.framingplan import build_framing_plan
from typehaus.emit.draw.roofframingplan import (
    build_roof_framing_plan,
    build_roof_framing_schedule,
    roof_framing_findings,
    roof_pitch_note,
)
from typehaus.emit.draw.scene import Leader, Polyline, Text
from typehaus.emit.draw.sheets import build_sheet_index
from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [finding for finding in findings if finding.severity.value == "error"]
    assert not errors, errors
    return model


def _texts(scene) -> list[str]:
    return [node.content for node in scene.nodes if isinstance(node, Text)]


def _joined(scene) -> str:
    return "\n".join(_texts(scene) + [node.text for node in scene.nodes
                                      if isinstance(node, Leader)])


# --- S-100 foundation ---------------------------------------------------------


def test_s100_carries_footings_pads_and_slabs_from_every_storey(catlin_model):
    scene = build_foundation_plan(catlin_model)
    tags = {node.tag for node in scene.by_layer()["S-FNDN-FTNG"] if isinstance(node, Polyline)}
    assert "FT-B-S1" in tags          # house strip footing, authored on `basement`
    assert "PD-BW-1" in tags          # breezeway pad, authored on `main` — still foundation
    slab_tags = {node.tag for node in scene.by_layer()["A-SLAB"] if isinstance(node, Polyline)}
    assert {"SL-B-FLOOR", "SL-G-FLOOR"} <= slab_tags


def test_s100_excludes_structural_decks_from_the_slab_schedule(catlin_model):
    # SL-M-DECK spans the basement and SL-SG-PORCH rides a joisted deck: framing, not
    # foundation. Neither may appear as slab-on-grade.
    on_grade = {slab.tag for slab in slabs_on_grade(catlin_model)}
    assert "SL-M-DECK" not in on_grade and "SL-SG-PORCH" not in on_grade


def test_s100_has_a_keyed_foundation_schedule(catlin_model):
    marks = foundation_marks(catlin_model)
    titles = [table.title for table in build_foundation_schedules(catlin_model)]
    assert titles == ["FOOTING / PAD SCHEDULE", "FOUNDATION WALL SCHEDULE",
                      "SLAB-ON-GRADE SCHEDULE"]
    text = _joined(build_foundation_plan(catlin_model))
    # every mark the schedule defines is keyed onto the plan
    for mark in {*marks.footing.values(), *marks.pad.values(), *marks.wall.values(),
                 *marks.slab.values()}:
        assert mark in text


def test_s100_schedules_size_bearing_elevation_and_thickness(catlin_model):
    tables = {table.title: table for table in build_foundation_schedules(catlin_model)}
    footings = tables["FOOTING / PAD SCHEDULE"]
    assert footings.columns == ("MARK", "TYPE", "SIZE", "BEARING EL.", "QTY", "SUPPORTS")
    strip = next(row for row in footings.rows if row[5].startswith("W-B-"))
    assert strip[2] == '20" W × 8" D' and strip[3] == "-9.67'"
    walls = tables["FOUNDATION WALL SCHEDULE"]
    assert any(row[2] == '16"' and row[3].endswith("LF") for row in walls.rows)
    slabs = tables["SLAB-ON-GRADE SCHEDULE"]
    # thickness keeps its eighth-inch fraction rather than rounding a 3-1/2" slab to 4"
    assert all(row[2] == '3-1/2"' for row in slabs.rows)


def test_s100_calls_frost_depth_drainage_and_steps(catlin_model):
    notes = " | ".join(foundation_general_notes(catlin_model))
    assert '42" MIN BELOW FINISHED GRADE' in notes
    assert "DRAIN TILE" in notes and "SUMP SM-B-RADON" in notes
    assert "STEP FOOTING" in notes
    # step callouts are placed at real adjacencies, not at every elevation pair
    steps = footing_steps(catlin_model)
    assert steps and all(lower.z0_m < upper.z0_m for lower, upper, _at in steps)
    assert "STEP FTG." in _joined(build_foundation_plan(catlin_model))


def test_s100_names_its_missing_inputs_instead_of_inventing_them(catlin_model):
    ids = {finding.check_id for finding in foundation_sheet_findings(catlin_model)}
    assert {"sheet.foundation.slab_reinforcement", "sheet.foundation.vapour_retarder",
            "sheet.foundation.sill_anchorage"} <= ids
    sheet_text = _joined(build_foundation_plan(catlin_model))
    assert "NOT SHOWN — MISSING MODEL INPUTS" in sheet_text
    for check_id in ids:
        assert check_id in sheet_text
    # no invented reinforcement callout anywhere on the sheet
    assert "O.C. E.W." not in sheet_text


def test_s100_is_not_a_floor_plan(catlin_model):
    foundation = build_foundation_plan(catlin_model)
    assert foundation.to_json() != build_floorplan(catlin_model, "basement").to_json()
    assert "A-DOOR" not in foundation.by_layer()


# --- S-101 floor framing ------------------------------------------------------


def test_s101_carries_joist_direction_size_and_spacing(catlin_model):
    scene = build_framing_plan(catlin_model, "FS-SECOND")
    arrows = [node for node in scene.nodes if getattr(node, "name", "") == "span-arrow"]
    assert arrows and arrows[0].rotation == 0.0  # FS-SECOND spans x
    text = _joined(scene)
    assert 'I-JOIST @ 16" O.C.' in text and "MAX SPAN" in text


def test_s101_schedules_headers_over_their_openings(catlin_model):
    level = framed_level(catlin_model, "FS-SECOND")
    headers = {table.title: table for table in build_framing_schedules(level)}
    table = headers["HEADER SCHEDULE — BEARING WALLS BELOW"]
    assert table.rows
    assert any(row[1].startswith("2-2x") for row in table.rows)      # size
    assert any("'-" in row[2] for row in table.rows)                 # span in feet-inches
    assert any("WIN-" in row[4] or "D-" in row[4] for row in table.rows)  # keyed to openings


def test_s101_draws_the_load_path_beam_to_post_to_support(catlin_model):
    level = framed_level(catlin_model, "FS-SG-DECK")
    tables = {table.title: table for table in build_framing_schedules(level)}
    load_path = tables["BEAM / POST SCHEDULE (LOAD PATH)"]
    beams = [row for row in load_path.rows if row[2] == "BEAM"]
    posts = [row for row in load_path.rows if row[2] == "POST"]
    assert beams and posts
    assert any(row[5].startswith("PT-SG-") for row in beams)      # beam bears on posts
    assert all(row[5] for row in posts)                            # post bears on something
    scene = build_framing_plan(catlin_model, "FS-SG-DECK")
    assert "S-BEAM" in scene.by_layer() and "S-COLS" in scene.by_layer()
    assert "CONNECTOR SCHEDULE" in _joined(scene)


def test_s101_marks_bearing_walls_below(catlin_model):
    scene = build_framing_plan(catlin_model, "FS-SECOND")
    text = _joined(scene)
    assert "BRG: W-M-C2" in text          # declared deck bearing
    assert "BEARING" in text              # authored StructuralRole.BEARING walls below
    assert "DECK BEARS ON" in text


def test_s101_member_schedule_counts_match_the_resolved_deck(catlin_model):
    level = framed_level(catlin_model, "FS-SECOND")
    table = next(t for t in build_framing_schedules(level) if t.title.endswith("MEMBER SCHEDULE"))
    joists = [m for m in level.floor.members if m.category == "joist"]
    joist_row = next(row for row in table.rows if row[1] == "FLOOR JOIST")
    assert joist_row[4] == str(len(joists))
    assert joist_row[2] == joists[0].profile


def test_s101_names_braced_wall_lines_as_a_missing_input(catlin_model):
    level = framed_level(catlin_model, "FS-SECOND")
    ids = {finding.check_id for finding in framing_sheet_findings(catlin_model, level)}
    assert "sheet.framing.braced_wall_lines" in ids
    assert "sheet.framing.braced_wall_lines" in _joined(
        build_framing_plan(catlin_model, "FS-SECOND"))


def test_s101_is_not_a_floor_plan_or_an_energy_view(catlin_model):
    framing = build_framing_plan(catlin_model, "FS-SECOND")
    assert framing.to_json() != build_floorplan(catlin_model, "second").to_json()
    layers = framing.by_layer()
    assert "S-FRAM" in layers and "A-FURN" not in layers


# --- S-102 roof framing -------------------------------------------------------


def test_s102_carries_roof_members_ridge_and_pitch(catlin_model):
    roof = next(item for item in catlin_model.roofs if item.tag == "RF-HOUSE")
    table = build_roof_framing_schedule(catlin_model, roof)
    marks = {row[0] for row in table.rows}
    assert {"R1", "RB1"} <= marks
    assert "SLOPE" in roof_pitch_note(roof)
    scene = build_roof_framing_plan(catlin_model, "RF-HOUSE")
    assert "S-FRAM" in scene.by_layer() and "S-BEAM" in scene.by_layer()
    assert "RIDGE" in _joined(scene)


def test_s102_schedules_truss_chords_for_a_truss_roof(catlin_model):
    roof = next(item for item in catlin_model.roofs if item.tag == "RF-GARAGE")
    marks = {row[0] for row in build_roof_framing_schedule(catlin_model, roof).rows}
    assert {"TC1", "BC1", "TW1"} <= marks


def test_s102_names_its_missing_inputs(catlin_model):
    roof = next(item for item in catlin_model.roofs if item.tag == "RF-HOUSE")
    ids = {finding.check_id for finding in roof_framing_findings(catlin_model, roof)}
    assert "sheet.roof_framing.design_loads" in ids


# --- index --------------------------------------------------------------------


def test_sheet_index_keeps_one_structural_series(catlin_model):
    sheets = {sheet.number: sheet.title for sheet in build_sheet_index(catlin_model)}
    assert sheets["S-100"] == "Foundation plan"
    assert any(number.startswith("S-101") for number in sheets)
    assert sheets["S-102.1"].startswith("Roof framing plan")
    assert sheets["S-103"] == "Framing schedule / bill of materials"


def test_structural_scenes_are_deterministic(catlin_model):
    for scene_a, scene_b in (
        (build_foundation_plan(catlin_model), build_foundation_plan(catlin_model)),
        (build_framing_plan(catlin_model, "FS-SECOND"),
         build_framing_plan(catlin_model, "FS-SECOND")),
        (build_roof_framing_plan(catlin_model, "RF-HOUSE"),
         build_roof_framing_plan(catlin_model, "RF-HOUSE")),
    ):
        assert scene_a.to_json() == scene_b.to_json()


def test_structural_sheets_round_trip_to_dxf(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    for name, scene in (("s100", build_foundation_plan(catlin_model)),
                        ("s101", build_framing_plan(catlin_model, "FS-SECOND")),
                        ("s102", build_roof_framing_plan(catlin_model, "RF-HOUSE"))):
        document = ezdxf.readfile(write_dxf(scene, tmp_path / f"{name}.dxf"))
        assert document.units == 1
        assert "A-ANNO-TABL" in {layer.dxf.name for layer in document.layers}
