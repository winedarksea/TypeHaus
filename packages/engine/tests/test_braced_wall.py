"""S-103 and IRC R602.10 — braced wall lines, the panels on them, and what they owe.

MNSPECT's most-cited residential omission, and this set had none. The spike result that
shaped the module is asserted here so it cannot be lost: **the lines are derivable and the
panels are not**. What changed on 2026-09-22 is that the panels are now AUTHORED
(``BracedWallPanel``) rather than absent — so the contract that used to be "UNKNOWN, always"
is now "UNKNOWN wherever a braced line carries no panel", which is the same rule with
something to compare against.
"""

from __future__ import annotations

import pytest

from typehaus.checks.code.mn_residential.profile import MN_2020
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.checks.structural.braced_wall import (
    braced_wall_line_spacing,
    braced_wall_panels,
)
from typehaus.checks.structural.braced_wall_panels import braced_wall_panel_rules
from typehaus.checks.structural.bracing_eval import braced_storeys, evaluate_storey, story_location
from typehaus.checks.structural.bracing_tables import (
    MAX_LINE_SPACING_FT,
    STORY_FIRST_OF_TWO,
    STORY_TOP,
)
from typehaus.emit.draw.bracedwallplan import (
    BWL_LAYER,
    build_braced_wall_plan,
    has_braced_wall_content,
)
from typehaus.emit.draw.scene import Polyline, Text
from typehaus.findings import Result
from typehaus.model.braced_wall import BracedWallPanel
from typehaus.quantities import inch
from typehaus.resolve.braced_walls import (
    KIND_BRACED,
    KIND_ENGINEERED,
    KIND_GABLE_END,
    KIND_INTERIOR,
    KIND_PLATE,
    METHOD_UNRATED,
    METHOD_WSP,
    braced_wall_lines,
    is_service_penetration,
    resolved_braced_wall_panels,
)


def _ctx(model):
    return CheckContext(plan=model.plan, model=model, preferences=Preferences(),
                        profile=MN_2020)


# --- the six structural facts, kept -----------------------------------------------------

def test_structural_role_is_not_the_input_and_never_was(catlin_model_ro):
    roles = {getattr(wall, "structural_role", None) for wall in catlin_model_ro.walls}
    assert roles == {None}


def test_each_framed_storey_gets_its_four_perimeter_lines(catlin_model_ro):
    for storey in ("main", "second", "attic"):
        lines = braced_wall_lines(catlin_model_ro, storey)
        assert len(lines) == 4, f"{storey}: {[line.tag for line in lines]}"
        assert {line.direction for line in lines} == {"x", "y"}
        assert all(abs(line.length_ft - 36.0) < 0.5 for line in lines)
    # The garage carries its OWN four and nothing else; `W-BW-SCREEN` is the north entry
    # canopy's shear panel and belongs to another structure four feet away.
    garage = braced_wall_lines(catlin_model_ro, "garage")
    assert len(garage) == 4, [line.tag for line in garage]
    assert all(abs(line.length_ft - 24.0) < 0.5 for line in garage)
    assert not [line for line in garage if "W-BW-SCREEN" in line.wall_tags]

    entry = braced_wall_lines(catlin_model_ro, "entry-low")
    assert [line.wall_tags for line in entry] == [("W-BW-SCREEN",)]


def test_a_poured_wall_is_not_a_braced_wall_line(catlin_model_ro):
    basement = braced_wall_lines(catlin_model_ro, "basement")
    assert len(basement) < 8, [line.tag for line in basement]
    assert not [line for line in basement if "SG" in line.tag], \
        "the sunken garden's retaining walls are not braced wall lines"


def test_the_method_follows_the_sheathing(catlin_model_ro):
    main = {line.tag: line.method for line in braced_wall_lines(catlin_model_ro, "main")}
    assert set(main.values()) == {METHOD_WSP}
    attic = {line.tag: line.method for line in braced_wall_lines(catlin_model_ro, "attic")}
    assert METHOD_UNRATED in attic.values()


def test_a_sheet_exists_for_every_level_that_has_lines(catlin_model_ro, catlin_sheet_index):
    from typehaus.emit.draw.datum import model_at_level

    levels = [primary.tag for primary, _here in catlin_model_ro.plan.levels()
              if has_braced_wall_content(model_at_level(catlin_model_ro, primary.tag),
                                         primary.tag)]
    numbers = [s.number for s in catlin_sheet_index() if s.number.startswith("S-103")]
    assert len(numbers) == len(levels) > 0


def test_line_spacing_passes_and_names_the_clause(catlin_model_ro):
    findings = braced_wall_line_spacing(_ctx(catlin_model_ro))
    assert len(findings) == 1
    assert findings[0].result is Result.PASS
    assert findings[0].code_ref == "IRC R602.10.1.3"
    assert f"{MAX_LINE_SPACING_FT:.0f}'" in findings[0].message


# --- the kinds, which are what decides who owes a length --------------------------------

def test_a_line_is_classified_by_what_it_is_measured_to_be(catlin_model_ro):
    kinds = {(line.storey, line.tag): line.kind
             for storey in ("basement", "main", "attic", "entry-low")
             for line in braced_wall_lines(catlin_model_ro, storey)}
    assert kinds[("attic", "BWL-W-A-E1")] == KIND_PLATE
    assert kinds[("attic", "BWL-W-A-N1")] == KIND_GABLE_END
    assert kinds[("basement", "BWL-W-B-SA-W")] == KIND_INTERIOR
    assert kinds[("entry-low", "BWL-W-BW-SCREEN")] == KIND_ENGINEERED
    assert kinds[("main", "BWL-W-A-E1")] == KIND_BRACED


def test_the_engineered_screen_flips_back_if_its_shear_panel_goes(catlin_model):
    """The marker is `Wall.shear_panel` and nothing else — remove it and the line is an
    ordinary braced wall line again, which is what keeps this out of a second vocabulary."""
    wall = catlin_model.plan.by_tag("W-BW-SCREEN")
    assert wall.shear_panel is not None
    stripped = wall.model_copy(update={"shear_panel": None})
    plan = catlin_model.plan.with_elements(
        "entry-low", [stripped if e is wall else e
                      for e in catlin_model.plan.storey_elements("entry-low")])
    catlin_model.plan = plan
    line = braced_wall_lines(catlin_model, "entry-low")[0]
    assert line.kind == KIND_BRACED


def test_a_habitable_attic_is_not_a_story_and_the_count_says_so(catlin_model_ro):
    """IRC R325.6 in the model's own terms: the attic carries no `braced` line (its east and
    west sides are rafter plates), so it never enters the story count."""
    assert braced_storeys(catlin_model_ro, "house") == ["main", "second"]
    assert story_location(catlin_model_ro, "main")[0] == STORY_FIRST_OF_TWO
    assert story_location(catlin_model_ro, "second")[0] == STORY_TOP
    assert story_location(catlin_model_ro, "attic")[0] is None
    assert story_location(catlin_model_ro, "basement")[0] is None
    row, words = story_location(catlin_model_ro, "main")
    assert "2 story" in words and "main, second" in words


# --- the panels -------------------------------------------------------------------------

def test_every_braced_line_on_the_house_and_garage_passes(catlin_model_ro):
    findings = braced_wall_panels(_ctx(catlin_model_ro))
    graded = [f for f in findings if f.result is Result.PASS]
    assert len(graded) == 12, [f.message[:60] for f in findings]
    assert not [f for f in findings if f.result in (Result.FAIL, Result.UNKNOWN)]
    assert braced_wall_panel_rules(_ctx(catlin_model_ro))[0].result is not Result.FAIL


def test_the_census_is_twenty_seven_thirty_one_and_nine(catlin_model_ro):
    counts = {storey: len([e for e in catlin_model_ro.plan.storey_elements(storey)
                           if isinstance(e, BracedWallPanel)])
              for storey in ("main", "second", "garage")}
    assert counts == {"main": 27, "second": 31, "garage": 9}


def test_the_garage_door_piers_need_no_portal_frame(catlin_model_ro):
    """48" of pier against Table R602.10.5's CS-WSP row at an 84" adjacent opening — the
    graded fact `OVERHEAD_DOOR_OFFSET` now is."""
    panels, _ = resolved_braced_wall_panels(catlin_model_ro, "garage")
    piers = [p for p in panels if p.line_tag == "BWL-W-G-N"]
    assert len(piers) == 2
    assert all(abs(p.length_in - 48.0) < 0.1 for p in piers)
    assert all(p.adjacent_opening_height_in == pytest.approx(84.0, abs=0.1) for p in piers)
    evaluation = next(e for e in evaluate_storey(catlin_model_ro, "garage")
                      if e.line.tag == "BWL-W-G-N")
    assert all(g.contributes_in > 0 for g in evaluation.panels)
    assert evaluation.ok


def test_the_ne_corner_carries_its_four_devices(catlin_model_ro):
    """Owner's option (c): both lines at that corner end in a 17" sliver, so the panel
    nearest the corner takes an 800-lb hold-down on each floor."""
    refs = {ref for storey in ("main", "second")
            for panel in resolved_braced_wall_panels(catlin_model_ro, storey)[0]
            for ref in panel.hold_down_refs}
    assert refs == {"CN-M-BWHD-NE-E", "CN-M-BWHD-NE-N",
                    "CN-S-BWHD-NE-E", "CN-S-BWHD-NE-N"}
    for ref in refs:
        assert catlin_model_ro.plan.by_tag(ref) is not None


def test_a_sub_minimum_run_contributes_nothing_and_says_so(catlin_model_ro):
    """Main E1's 17" end sliver is not authored at all; this is the same rule from the
    other side — a panel SHORTER than Table R602.10.5's row buys zero feet."""
    from typehaus.checks.structural.bracing_eval import _grade_panel

    panels, _ = resolved_braced_wall_panels(catlin_model_ro, "main")
    panel = next(p for p in panels if p.line_tag == "BWL-W-A-E1")
    short = panel.__class__(**{**panel.__dict__, "u1_m": panel.u0_m + inch(20).meters})
    grade = _grade_panel(short, 108.0)
    assert grade.contributes_in == 0.0
    assert "minimum" in grade.reason


def test_a_nine_inch_service_penetration_does_not_split_a_panel(catlin_model_ro):
    """AO-M-ERV-OA sits inside BWP-M-N3B-0000 and the panel is whole across it. No code
    section states the 24" x 24" threshold — it is this engine's, and it is stated."""
    port = next(o for o in catlin_model_ro.openings if o.tag == "AO-M-ERV-OA")
    assert is_service_penetration(port)
    panels, _ = resolved_braced_wall_panels(catlin_model_ro, "main")
    panel = next(p for p in panels if "BWP-M-N3B-0000" in p.tags)
    assert panel.contains_opening == ()
    assert panel.length_in == pytest.approx(78.0, abs=0.1)


def test_a_panel_across_a_window_is_reported(catlin_model):
    """R602.10.2: a panel is a FULL-HEIGHT section of wall."""
    panel = BracedWallPanel(uid="TESTBWP001", tag="BWP-TEST-BAD", wall_ref="W-M-E1",
                            start=inch(0.0), width=inch(120.0))
    catlin_model.plan = catlin_model.plan.with_elements(
        "main", [*catlin_model.plan.storey_elements("main"), panel])
    findings = braced_wall_panel_rules(_ctx(catlin_model))
    bad = [f for f in findings if "BWP-TEST-BAD" in f.element_tags]
    assert bad and any("FULL-HEIGHT" in f.message for f in bad)


def test_an_unrated_device_is_named_and_refused(catlin_model):
    """A hold-down whose part publishes no allowable is not a hold-down for R602.10.7."""
    from typehaus.checks.structural.braced_wall_panels import _hold_down

    class _Panel:
        hold_down_refs = ("CN-M-HD-ENTRY-E",)   # size "STHD", a family record with no row

    ok, sentence = _hold_down(_ctx(catlin_model), _Panel())
    assert not ok
    assert "no allowable tension" in sentence


def test_a_braced_line_with_no_panel_is_still_unknown(catlin_model):
    """The old contract, kept: decision #32, a rule that cannot evaluate never passes.

    Do NOT close it by deriving panels from the sheathed length of a line. Sheathing a wall
    is not bracing it, and counting sheathed feet would report PASS on a house with no
    hold-downs in it.
    """
    keep = [e for e in catlin_model.plan.storey_elements("garage")
            if not isinstance(e, BracedWallPanel)]
    catlin_model.plan = catlin_model.plan.with_elements("garage", keep)
    findings = [f for f in braced_wall_panels(_ctx(catlin_model))
                if f.message.startswith("UNKNOWN") and "garage" in f.message]
    assert len(findings) == 4
    assert all("no braced wall PANEL is modelled" in f.message for f in findings)
    assert all("BracedWallPanel" in (f.fix_hint or "") for f in findings)


def test_a_building_with_no_framed_envelope_earns_not_applicable(catlin_model_ro):
    from copy import copy

    stripped = copy(catlin_model_ro)
    stripped.walls = []
    findings = braced_wall_panels(_ctx(stripped))
    assert len(findings) == 1
    assert findings[0].result is Result.NOT_APPLICABLE


def test_the_basement_south_line_prints_the_other_reading(catlin_model_ro):
    """Decision #17/#79: framed infill in an R404 box is N/A, and the finding argues it."""
    finding = next(f for f in braced_wall_panels(_ctx(catlin_model_ro))
                   if "BWL-W-A-S1" in f.element_tags and "basement" in f.message)
    assert finding.result is Result.NOT_APPLICABLE
    assert "R404" in finding.message
    assert "the other reading" in finding.message or "read the other way" in finding.message


# --- the sheet ---------------------------------------------------------------------------

def test_the_sheet_draws_the_panels_and_the_rows_it_read(catlin_model_ro):
    scene = build_braced_wall_plan(catlin_model_ro, "main")
    printed = " ".join(n.content for n in scene.nodes if isinstance(n, Text))
    assert "REQ" in printed and "PROV" in printed
    assert "Table R602.10.3(1)" in printed
    assert "CN-M-BWHD-NE-E" in printed
    assert "R602.10.8" in printed, "the conditions the PASS rests on"
    assert [n for n in scene.nodes if isinstance(n, Polyline) and n.layer == BWL_LAYER]


def test_the_sheet_labels_a_line_that_owes_no_length(catlin_model_ro):
    printed = " ".join(n.content for n in build_braced_wall_plan(catlin_model_ro, "attic").nodes
                       if isinstance(n, Text))
    assert "GABLE END" in printed
    assert "RAFTER PLATE" in printed
