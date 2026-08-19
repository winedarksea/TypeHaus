"""S-100/S-101/S-102 as complete structural sheets, not reused floor or energy views.

Covers what each sheet must *carry* (footings + schedule; joist direction, headers, member
schedule; roof framing), and that each is derived from the resolved model rather than being
a copy of another sheet's builder.
"""

from __future__ import annotations

from pathlib import Path


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
    # SL-M-DECK spans the basement: framing, not foundation, so it may not appear as
    # slab-on-grade. (The porch used to be the second half of this — SL-SG-PORCH riding a
    # joisted deck — until the slab was deleted and FS-SG-PORCH became the porch floor.)
    on_grade = {slab.tag for slab in slabs_on_grade(catlin_model)}
    assert "SL-M-DECK" not in on_grade


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
    # A house strip footing, not the veneer plinth: FT-B-BRICK also supports a "W-B-" wall
    # but is 10"x5" cast on the house footing's toe (params/foundations.py).
    strip = next(row for row in footings.rows
                 if row[5].startswith("W-B-") and row[5] != "W-B-BRICK")
    assert strip[2] == '20" W × 8" D' and strip[3] == "-9.67'"
    walls = tables["FOUNDATION WALL SCHEDULE"]
    # A whole-inch monolithic pour, thickness and run both stated. This used to read the
    # sunken garden's 16" arched cross-wall; it reads the 12" side/retaining walls that
    # outlived it (2026-08-18). Every THK is an inch string and every RUN a lineal foot.
    assert any(row[1] == "SUNKEN_GARDEN_WALL" and row[2] == '12"' and row[3].endswith("LF")
               for row in walls.rows)
    assert all(row[2].endswith('"') and row[3].endswith("LF") for row in walls.rows)
    slabs = tables["SLAB-ON-GRADE SCHEDULE"]
    # Thickness keeps its eighth-inch fraction rather than rounding a 3-1/2" slab to 4".
    # The counterexample this used to lean on — SL-G-HYDRANT-PED, a genuinely 4" topping
    # block, so folding it in would have passed by rounding — was retired 2026-08-03
    # (houses/catlin/notes/garage_hydrant.md), and every remaining pour is 3-1/2".
    assert slabs.columns[1] == "TAG" and slabs.columns[2] == "THK"
    poured = {row[1]: row[2] for row in slabs.rows}
    assert poured["SL-B-FLOOR"] == '3-1/2"' and poured["SL-G-FLOOR"] == '3-1/2"'
    assert "SL-G-HYDRANT-PED" not in poured
    # Every *floor* pour is 3-1/2". The five SL-G-STEP-* are 6" — the step-down from the
    # garage service door's 0'-0" threshold to the slab at grade (2026-08-18), and a 6"
    # riser is the pour, not a rounding of one.
    assert all(thickness == '3-1/2"' for tag, thickness in poured.items()
               if not tag.startswith("SL-G-STEP-")), poured
    assert {poured[tag] for tag in poured if tag.startswith("SL-G-STEP-")} == {'6"'}


def test_s100_calls_frost_depth_drainage_and_steps(catlin_model):
    notes = " | ".join(foundation_general_notes(catlin_model))
    assert '42" MIN BELOW FINISHED GRADE' in notes
    # The note reads the tile's authored discharge. It used to say "TO SUMP SM-B-RADON"
    # merely because a sump solid existed somewhere in the model, while every DrainTile on
    # the project discharges to daylight — a sheet note that contradicted its own drawing.
    assert "DRAIN TILE" in notes and "DRAINING TO DAYLIGHT" in notes
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


def test_hardware_schedule_is_its_own_sheet(catlin_model):
    """S-104 must appear in the index, or the derived hardware counts reach no reader.

    ``hardware_takeoff`` produced screw, anchor and connector quantities that the lumber
    cut list on S-103 structurally cannot carry (a screw has no cut length), and they were
    reaching the CLI only.
    """
    from typehaus.emit.draw.sheets import build_sheet_index

    sheets = {spec.number: spec for spec in build_sheet_index(catlin_model)}
    assert "S-104" in sheets
    assert sheets["S-104"].title == "Connection hardware schedule"
    # A schedule page composes tables directly rather than building a Scene.
    assert sheets["S-104"].page is not None and sheets["S-104"].scene is None


def test_hardware_schedule_renders_every_derived_row(catlin_model, tmp_path: Path):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.backends.backend_pdf import PdfPages

    from typehaus.emit.draw.sheets import _write_hardware_schedule
    from typehaus.takeoff import hardware_takeoff

    hardware = hardware_takeoff(catlin_model)
    assert hardware, "catlin must derive hardware for this sheet to mean anything"
    # Every row needs the rule behind it — a hardware count nobody can check is not a
    # schedule, and the sheet prints these as keyed notes under the table.
    assert all(row["basis"] for row in hardware)

    out = tmp_path / "s104.pdf"
    with PdfPages(out) as pdf:
        _write_hardware_schedule(pdf, catlin_model, "S-104", "Connection hardware schedule")
    assert out.stat().st_size > 0
