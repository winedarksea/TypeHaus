"""S-100/S-101/S-102 as complete structural sheets, not reused floor or energy views.

Covers what each sheet must *carry* (footings + schedule; joist direction, headers, member
schedule; roof framing), and that each is derived from the resolved model rather than being
a copy of another sheet's builder.
"""

from __future__ import annotations

from pathlib import Path

from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.foundation_schedule import (
    anchorage_schedule,
    build_foundation_schedules,
    footing_steps,
    foundation_general_notes,
    foundation_marks,
    foundation_sheet_findings,
    reinforcement_schedule,
    slabs_on_grade,
)
from typehaus.emit.draw.foundationplan import build_foundation_plan
from typehaus.emit.draw.framing_schedule import (
    build_storey_framing_schedules,
    framed_levels,
    storey_framing_findings,
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
    assert "PD-BW-1" not in tags          # breezeway pad, authored on `main` — still foundation
    slab_tags = {node.tag for node in scene.by_layer()["A-SLAB"] if isinstance(node, Polyline)}
    assert {"SL-B-FLOOR", "SL-G-FLOOR"} <= slab_tags


def test_s100_excludes_structural_decks_from_the_slab_schedule(catlin_model):
    # SL-M-DECK spans the basement: framing, not foundation, so it may not appear as
    # slab-on-grade.
    on_grade = {slab.tag for slab in slabs_on_grade(catlin_model)}
    assert "SL-M-DECK" not in on_grade


def test_s100_has_a_keyed_foundation_schedule(catlin_model):
    marks = foundation_marks(catlin_model)
    titles = [table.title for table in build_foundation_schedules(catlin_model)]
    assert titles == ["FOOTING / PAD SCHEDULE", "FOUNDATION WALL SCHEDULE",
                      "SLAB-ON-GRADE SCHEDULE", "SILL ANCHORAGE SCHEDULE",
                      "FOUNDATION REINFORCEMENT SCHEDULE"]
    text = _joined(build_foundation_plan(catlin_model))
    # every mark the schedule defines is keyed onto the plan
    for mark in {*marks.footing.values(), *marks.pad.values(), *marks.wall.values(),
                 *marks.slab.values()}:
        assert mark in text


def test_s100_schedules_size_bearing_elevation_and_thickness(catlin_model):
    tables = {table.title: table for table in build_foundation_schedules(catlin_model)}
    footings = tables["FOOTING / PAD SCHEDULE"]
    assert footings.columns == ("MARK", "TYPE", "SIZE", "BEARING EL.", "QTY", "SUPPORTS")
    # A house strip footing. The exclusion here used to be FT-B-BRICK, the 10"x5" veneer
    # plinth cast on the house footing's toe, which also supported a "W-B-" wall; it was
    # retired 2026-09-05 when W-B-BRICK was re-founded on the spanning beam W-SG-BRKBM, and
    # a wall that spans has no footing. The filter is kept so the schedule cannot silently
    # start reporting a non-strip pour against this 20"x8" claim again.
    strip = next(row for row in footings.rows
                 if row[5].startswith("W-B-") and row[5] != "W-B-BRICK")
    # -9.79': the strips follow the basement slab, bearing on the deck's flat bearing seat.
    assert strip[2] == '20" W × 8" D' and strip[3] == "-9.79'"
    walls = tables["FOUNDATION WALL SCHEDULE"]
    # A whole-inch monolithic pour, thickness and run both stated: the 12" side/retaining
    # walls. Every THK is an inch string and every RUN a lineal foot.
    assert any(row[1] == "SUNKEN_GARDEN_WALL" and row[2] == '12"' and row[3].endswith("LF")
               for row in walls.rows)
    assert all(row[2].endswith('"') and row[3].endswith("LF") for row in walls.rows)
    slabs = tables["SLAB-ON-GRADE SCHEDULE"]
    # Thickness keeps its eighth-inch fraction rather than rounding a 3-1/2" slab to 4".
    # SL-G-HYDRANT-PED, a genuinely 4" topping block that would fold in by rounding, is not
    # in the model (houses/catlin/notes/garage_hydrant.md); every remaining pour is 3-1/2".
    assert slabs.columns[1] == "TAG" and slabs.columns[2] == "THK"
    poured = {row[1]: row[2] for row in slabs.rows}
    assert poured["SL-B-FLOOR"] == '3-1/2"' and poured["SL-G-FLOOR"] == '3-1/2"'
    assert "SL-G-HYDRANT-PED" not in poured
    # Every *floor* pour is 3-1/2". SL-G-STEP-0 is 6" — the landing at the garage service
    # door's 0'-0" threshold, 2'-10" over the slab at grade, and a 6" pad is the pour rather
    # than a rounding of one. Its treads are a pressure-treated `Stair` (ST-G-SERVICE), so
    # they are framing, not flatwork, and this schedule is right not to list them.
    # SL-SG-FROST-* are the R403.3 wing insulation under the sunken-garden slab: 1" and 2"
    # of XPS, `role="band"` assemblies with no structure in them at all. They are slabs
    # only because a horizontal band of foam has no other element kind to be, and they are
    # not pours.
    #
    # SL-SG-HPPAD and SL-SG-STAIRPAD are the third and fourth exceptions and, like
    # SL-G-STEP-0, real thicknesses rather than rounded ones: two 4" unreinforced pads in the
    # pocket east of the porch — the equipment pad for the heat pumps that came off the
    # balcony on 2026-09-02, and the pad and R311.7.6 bottom landing for ST-SG-PORCH. They
    # were ONE 4" pour from 2026-09-03 and split on 2026-09-04, when the condenser row and
    # the flight swapped halves of the pocket (houses/catlin/notes/heat_pump_ground_pad.md
    # and porch_stair.md). Both are asserted by name so the exemption cannot quietly cover a
    # fifth slab.
    #
    # SL-M-HP3PAD is the fifth and, like the other two pads, a real 4" pour: the north-side
    # equipment pad under EQ-M-HP3-OD, in the slot between the house and the garage
    # (plan/site.py). It arrived 2026-09-04 when that unit stopped floating on the storey
    # datum. SL-M-HP1PAD is the sixth and the same article again, poured later the same day
    # when EQ-M-HP1-OD crossed from the pocket to the north face east of the garage
    # (params/hp1_north_pad.py). **SL-SG-STOOP was the seventh and is RETIRED (2026-09-05):**
    # it was a 7-1/4" block of the old flush floor left as the R311.3 landing when the court
    # dropped, and `court_step_down_in` going back to 0 made the whole 494 sf court that
    # plane again, so the landing is SL-SG-FLOOR and the block is redundant.
    #
    # SL-SG-FIELD is not a pour at all: 12" of growing medium over the sunken garden's
    # court, a `Slab` for the same reason the frost wings are — a horizontal band has no
    # other element kind to be (params/sunken_garden.py states the case at length).
    assert poured["SL-SG-HPPAD"] == '4"' and poured["SL-SG-STAIRPAD"] == '4"'
    assert poured["SL-M-HP3PAD"] == '4"' and poured["SL-M-HP1PAD"] == '4"'
    assert "SL-SG-STOOP" not in poured, "the stoop was retired 2026-09-05"
    assert poured["SL-SG-FIELD"] == '18"'
    assert all(thickness == '3-1/2"' for tag, thickness in poured.items()
               if not tag.startswith(("SL-G-STEP-", "SL-SG-FROST-", "SL-SG-HPPAD",
                                      "SL-SG-STAIRPAD", "SL-M-HP3PAD", "SL-M-HP1PAD",
                                      "SL-SG-FIELD"))), poured
    assert not {tag for tag in poured if tag.startswith("SL-G-STEP-")}
    assert [tag for tag in poured if tag.startswith("SL-G-STEP-")] == ["SL-G-STEP-0"]
    assert {poured[tag] for tag in poured if tag.startswith("SL-SG-FROST-")} == {'1"', '2"'}


def test_s100_calls_frost_depth_drainage_and_steps(catlin_model):
    notes = " | ".join(foundation_general_notes(catlin_model))
    # "ALL FOOTINGS TO BEAR 42" MIN BELOW FINISHED GRADE" was a blanket claim this sheet
    # printed for as long as it existed, and on a site with an open sunken court beside the
    # house it was false: the strips along that court bear 8" below the court floor. The
    # number was never the wrong part — the word "GRADE" was.
    assert '42" MIN BELOW THE LOWEST ADJACENT FINISHED GRADE' in notes
    assert "SL-SG-FLOOR, NOT THE SITE GRADE PLANE" in notes
    # The note reads the tile's authored discharge, and as of 2026-09-05 NOTHING on this
    # project discharges to daylight: the house tile falls to the SM-B-RADON pit (its invert
    # is 7'-6 1/2" below site grade, so daylight was never available to it) and the sunken
    # garden's falls to DRW-SG-MAIN. Two destinations, both named on the sheet.
    assert "DRAIN TILE" in notes
    assert "DRAINING TO DRW-SG-MAIN, SM-B-RADON" in notes
    assert "DAYLIGHT" not in notes
    assert "STEP FOOTING" in notes
    # step callouts are placed at real adjacencies, not at every elevation pair
    steps = footing_steps(catlin_model)
    assert steps and all(lower.z0_m < upper.z0_m for lower, upper, _at in steps)
    assert "STEP FTG." in _joined(build_foundation_plan(catlin_model))


def test_s100_names_its_missing_inputs_instead_of_inventing_them(catlin_model):
    ids = {finding.check_id for finding in foundation_sheet_findings(catlin_model)}
    # Slab steel stays on the missing list: no Slab on grade carries a ReinforcementSpec.
    assert "sheet.foundation.slab_reinforcement" in ids
    # Sill anchorage has LEFT it. The 137 MASA anchors were derived all along and the sheet
    # was declining to print a number it was already holding; they schedule now, so the
    # WARN survives only for a house that models neither a strap nor an anchor bolt.
    assert "sheet.foundation.sill_anchorage" not in ids
    # Every foundation wall assembly that R406.1 could reach is dampproofed, so the
    # presence finding does not fire either.
    assert "sheet.foundation.dampproofing" not in ids
    # `sheet.foundation.vapour_retarder` is NOT in that set: SLAB_FLOOR and
    # GARAGE_SLAB_ON_GRADE carry a 10-mil ASTM E1745 Class A retarder over a 4" capillary
    # break, and the exterior slabs that never needed one — the garden floor, the garage
    # step landing — are out of R506.2.3's scope rather than failing it.
    assert "sheet.foundation.vapour_retarder" not in ids
    sheet_text = _joined(build_foundation_plan(catlin_model))
    assert "NOT SHOWN — MISSING MODEL INPUTS" in sheet_text
    for check_id in ids:
        assert check_id in sheet_text
    # no invented reinforcement callout anywhere on the sheet
    assert "O.C. E.W." not in sheet_text


def test_s100_schedules_the_sill_anchorage_it_already_derived(catlin_model):
    from typehaus.takeoff.anchors import mudsill_anchor_rows
    from typehaus.takeoff.hardware_config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG

    table = anchorage_schedule(catlin_model)
    assert table.columns == ("MARK", "TYPE", "PART", "SPACING", "QTY", "WALLS")
    assert table.rows, "137 MASA anchors are derived; the sheet must show them"
    pitch = CONFIG.sill_plate_anchors.mudsill_anchor_pitch_ft
    # The printed pitch IS the takeoff's, not a second number that looks like it.
    assert all(row[3] == f"{pitch:.0f}'-0\" O.C." for row in table.rows), table.rows
    assert {row[2] for row in table.rows} == {"MASA"}
    # The table splits the house by condition; the split must not lose or gain an anchor.
    takeoff = mudsill_anchor_rows(catlin_model, CONFIG.sill_plate_anchors,
                                  CONFIG.sill_plate_takeoff_category)
    assert sum(int(row[4]) for row in table.rows) == takeoff[0]["count"]
    # Both conditions are on this house and they are not the same detail: a mudsill over a
    # foundation wall, and a partition plate on the basement slab.
    types = {row[1].split(" — ")[0] for row in table.rows}
    assert types == {"FDN WALL", "SLAB"}
    assert "MASA" in _joined(build_foundation_plan(catlin_model))


def test_s100_schedules_the_authored_reinforcement(catlin_model):
    table = reinforcement_schedule(catlin_model)
    assert table.columns == ("MARK", "ELEMENT", "ROLE", "BAR", "SPACING", "LYRS",
                             "COVER", "LAP")
    rows = {(row[2], row[3], row[4], row[6], row[7]) for row in table.rows}
    # `_B8_STEEL` on the basement walls: IRC Table R404.1.2(8), 2" cover, no lap class
    # authored — and the schedule says "NOT STATED" rather than assuming a class.
    assert ("VERTICAL", "#5", '41" O.C.', '2"', "—") in rows
    # The sunken-garden court footing mat: cover comes from ReinforcementSpec.cover (3"),
    # which outranks the mix's, and both mat directions print. It was `#6 @ 10"` until
    # 2026-09-10, when all five strips narrowed 96" -> 84" and took 22% off the toe moment
    # with them (notes/sunken_garden_court_free_body.md §7e).
    assert ("BOTTOM-X", "#5", '12" O.C.', '3"', "B") in rows
    assert ("TOP-X", "#5", '12" O.C.', '3"', "B") in rows
    # The stem keeps `#6 @ 10"` at 2" cover, so the sheet carries two bar sizes on one pour
    # and a reader must not collapse them. That is a real change from the one-bar schedule
    # the mat and the stem shared before the narrowing.
    assert ("VERTICAL", "#6", '10" O.C.', '3"', "B") in rows
    # Nothing is invented for the pours that carry no spec.
    assert all(row[3].startswith("#") for row in table.rows)
    assert "FOUNDATION REINFORCEMENT SCHEDULE" in _joined(build_foundation_plan(catlin_model))


def test_s100_reinforcement_schedule_renders_a_plain_pour_honestly(catlin_model,
                                                                   monkeypatch):
    """A house may pour its foundation plain (ACI 318-19 §14.1.4) and this house may yet
    decide to — notes/rebar_backout.md is that argument. The sheet must then print no
    reinforcement schedule at all rather than an empty heading or an invented mat."""
    import typehaus.emit.draw.foundation_schedule as schedule

    monkeypatch.setattr(schedule, "_reinforced_elements", lambda model: [])
    assert reinforcement_schedule(catlin_model).rows == ()
    titles = [table.title for table in build_foundation_schedules(catlin_model)]
    assert "FOUNDATION REINFORCEMENT SCHEDULE" not in titles
    # ...and the sill anchorage, which is derived and not authored, is unaffected.
    assert "SILL ANCHORAGE SCHEDULE" in titles


def test_s100_radon_block_is_derived_item_by_item(catlin_model):
    notes = " | ".join(foundation_general_notes(catlin_model))
    assert "RADON CONTROL — MN 1303.2400" in notes
    # Subp. 2 — the course under the pour, read off the slab assembly, not a code minimum.
    assert "SUBP. 2: SL-B-FLOOR — 2\" XPS, 10 MIL POLYETHYLENE, 4\" CAPILLARY-BREAK-STONE" \
        in notes
    # ...and what the model does NOT say is said as such, never as a default.
    assert "AGGREGATE GRADATION AND THE 12\" MEMBRANE LAP ARE NOT MODELLED" in notes
    assert "SUBP. 3-4: COLLECTION POINT SM-B-RADON" in notes and "SEALED COVER" in notes
    assert "SUBP. 5: VENT VR-M-RADON-VENT" in notes
    assert "NOT MODELLED — FIELD ITEMS" in notes
    # Subp. 6 names the same two boxes code.MN_1303_2402_radon passes on, and only those:
    # a box that declares a room is a lighting supply on some other storey.
    assert "SUBP. 6: POWER FOR A FUTURE FAN AT ED-A-NEMA-JB, ED-A-PV-JB" in notes
    # A schedule that abbreviates carries its legend on the sheet, not in this repo.
    assert "NO PLATE RUN TAKES FEWER THAN 2 (IRC R403.1.6)" in notes
    assert "LAP CLASS IS ACI 318-19 §25.5.2.1" in notes
    # R406.1 reads the assembly's water-control layer rather than asserting a product.
    assert "BASEMENT_8 (8)" in notes and "50 MIL AIR-BARRIER ('DAMP-PROOF')" in notes


def test_s100_is_not_a_floor_plan(catlin_model):
    foundation = build_foundation_plan(catlin_model)
    assert foundation.to_json() != build_floorplan(catlin_model, "basement").to_json()
    assert "A-DOOR" not in foundation.by_layer()


# --- S-101 floor framing ------------------------------------------------------


def test_s101_carries_joist_direction_size_and_spacing(catlin_model):
    scene = build_framing_plan(catlin_model, "second")
    arrows = [node for node in scene.nodes if getattr(node, "name", "") == "span-arrow"]
    assert arrows and arrows[0].rotation == 0.0  # FS-S-EAST spans x
    text = _joined(scene)
    assert 'I-JOIST @ 16" O.C.' in text and "MAX SPAN" in text


def test_s101_schedules_headers_over_their_openings(catlin_model):
    levels = framed_levels(catlin_model, "second")
    headers = {table.title: table for table in build_storey_framing_schedules(levels)}
    table = headers["HEADER SCHEDULE — BEARING WALLS BELOW"]
    assert table.rows
    assert any(row[1].startswith("2-2x") for row in table.rows)      # size
    assert any("'-" in row[2] for row in table.rows)                 # span in feet-inches
    assert any("WIN-" in row[4] or "D-" in row[4] for row in table.rows)  # keyed to openings


def test_s101_draws_the_load_path_beam_to_post_to_support(catlin_model):
    levels = framed_levels(catlin_model, "second")
    tables = {table.title: table for table in build_storey_framing_schedules(levels)}
    load_path = tables["BEAM / POST SCHEDULE (LOAD PATH)"]
    beams = [row for row in load_path.rows if row[2] == "BEAM"]
    posts = [row for row in load_path.rows if row[2] == "POST"]
    assert beams and posts
    assert any(row[5].startswith("PT-SG-") for row in beams)      # beam bears on posts
    assert all(row[5] for row in posts)                            # post bears on something
    scene = build_framing_plan(catlin_model, "second")
    assert "S-BEAM" in scene.by_layer() and "S-COLS" in scene.by_layer()
    assert "CONNECTOR SCHEDULE" in _joined(scene)


def test_s101_marks_bearing_walls_below(catlin_model):
    scene = build_framing_plan(catlin_model, "second")
    text = _joined(scene)
    assert "BRG: W-M-C2" in text          # declared deck bearing
    assert "BEARING" in text              # authored StructuralRole.BEARING walls below
    assert "DECKS BEAR ON" in text


def test_s101_member_schedule_counts_match_the_resolved_deck(catlin_model):
    levels = framed_levels(catlin_model, "second")
    table = next(t for t in build_storey_framing_schedules(levels)
                 if t.title == "MEMBER SCHEDULE")
    east = next(level for level in levels if level.floor.tag == "FS-S-EAST")
    joists = [m for m in east.floor.members if m.category == "joist"]
    # The leading DECK column is what makes one sheet per storey readable: the row shape
    # is (DECK, MARK, MEMBER, SIZE, SPACING, QTY, MAX SPAN).
    joist_row = next(row for row in table.rows
                     if row[0] == "FS-S-EAST" and row[2] == "FLOOR JOIST")
    assert joist_row[5] == str(len(joists))
    assert joist_row[3] == joists[0].profile


def test_s101_names_braced_wall_lines_as_a_missing_input(catlin_model):
    levels = framed_levels(catlin_model, "second")
    ids = {finding.check_id for finding in storey_framing_findings(catlin_model, levels)}
    assert "sheet.framing.braced_wall_lines" in ids
    assert "sheet.framing.braced_wall_lines" in _joined(
        build_framing_plan(catlin_model, "second"))


def test_s101_is_not_a_floor_plan_or_an_energy_view(catlin_model):
    framing = build_framing_plan(catlin_model, "second")
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


def test_s102_schedules_the_truss_for_a_truss_roof(catlin_model):
    """One member per truss, so one schedule mark: the sheet says "T1", not a chord/web
    breakdown the fabricator's own plate layout owns."""
    roof = next(item for item in catlin_model.roofs if item.tag == "RF-GARAGE")
    marks = {row[0] for row in build_roof_framing_schedule(catlin_model, roof).rows}
    assert "T1" in marks
    assert not {mark for mark in marks if mark.startswith(("TC", "BC", "TW", "TH"))}


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
    assert sheets["S-601"] == "Framing schedule / bill of materials"


def test_structural_scenes_are_deterministic(catlin_model):
    for scene_a, scene_b in (
        (build_foundation_plan(catlin_model), build_foundation_plan(catlin_model)),
        (build_framing_plan(catlin_model, "second"),
         build_framing_plan(catlin_model, "second")),
        (build_roof_framing_plan(catlin_model, "RF-HOUSE"),
         build_roof_framing_plan(catlin_model, "RF-HOUSE")),
    ):
        assert scene_a.to_json() == scene_b.to_json()


def test_structural_sheets_round_trip_to_dxf(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    for name, scene in (("s100", build_foundation_plan(catlin_model)),
                        ("s101", build_framing_plan(catlin_model, "second")),
                        ("s102", build_roof_framing_plan(catlin_model, "RF-HOUSE"))):
        document = ezdxf.readfile(write_dxf(scene, tmp_path / f"{name}.dxf"))
        assert document.units == 1
        assert "A-ANNO-TABL" in {layer.dxf.name for layer in document.layers}


def test_hardware_schedule_is_its_own_sheet(catlin_model):
    """S-602 must appear in the index, or the derived hardware counts reach no reader.

    ``hardware_takeoff`` produced screw, anchor and connector quantities that the lumber
    cut list on S-601 structurally cannot carry (a screw has no cut length), and they were
    reaching the CLI only.
    """
    from typehaus.emit.draw.sheets import build_sheet_index

    sheets = {spec.number: spec for spec in build_sheet_index(catlin_model)}
    assert "S-602" in sheets
    assert sheets["S-602"].title == "Connection hardware schedule"
    # A schedule page composes tables directly rather than building a Scene.
    assert sheets["S-602"].page is not None and sheets["S-602"].scene is None


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
        _write_hardware_schedule(pdf, catlin_model, "S-602", "Connection hardware schedule")
    assert out.stat().st_size > 0
