"""S-103 and IRC R602.10 — the braced wall plan (→ 30 §Structural).

MNSPECT's most-cited residential omission, and this set had none. The whole design of this
module is a consequence of one spike result, which is asserted here so it cannot be lost:
**the lines are derivable and the panels are not**, and a check that pretended otherwise
would report PASS on a house with no hold-downs in it.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential.profile import MN_2020
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.checks.structural.braced_wall import (
    MAX_LINE_SPACING_FT,
    braced_wall_line_spacing,
    braced_wall_panels,
)
from typehaus.emit.draw.bracedwallplan import (
    BWL_LAYER,
    METHOD_UNRATED,
    METHOD_WSP,
    braced_wall_lines,
    build_braced_wall_plan,
    has_braced_wall_content,
)
from typehaus.emit.draw.scene import Polyline, Text
from typehaus.emit.draw.sheets import build_sheet_index
from typehaus.findings import Result


def _ctx(model):
    return CheckContext(plan=model.plan, model=model, preferences=Preferences(),
                        profile=MN_2020)


def test_structural_role_is_not_the_input_and_never_was(catlin_model_ro):
    """The spike result that shaped this module.

    The plan for this work assumed walls carry `structural_role`. They carry the FIELD;
    this house authors it nowhere, on any of its 174 walls. Lines are identified by what is
    actually known instead.
    """
    roles = {getattr(wall, "structural_role", None) for wall in catlin_model_ro.walls}
    assert roles == {None}


def test_each_framed_storey_gets_its_four_perimeter_lines(catlin_model_ro):
    for storey in ("main", "second", "attic"):
        lines = braced_wall_lines(catlin_model_ro, storey)
        assert len(lines) == 4, f"{storey}: {[line.tag for line in lines]}"
        assert {line.direction for line in lines} == {"x", "y"}
        assert all(abs(line.length_ft - 36.0) < 0.5 for line in lines)
    # The garage storey carries FIVE, and the odd one out is not a garage wall at all:
    # `W-BW-SCREEN` is the north entry canopy's west shear panel, filed on this storey with
    # the canopy roof it braces. It is genuinely a braced wall line — sheathed both faces,
    # standing on the seat beams over two piers — and 6'-6 3/4" long rather than 24'-0",
    # which is why the length assertion below excludes it by tag instead of by count.
    garage = braced_wall_lines(catlin_model_ro, "garage")
    assert len(garage) == 5, [line.tag for line in garage]
    perimeter = [line for line in garage if "W-BW-SCREEN" not in line.wall_tags]
    assert len(perimeter) == 4
    assert all(abs(line.length_ft - 24.0) < 0.5 for line in perimeter)


def test_a_poured_wall_is_not_a_braced_wall_line(catlin_model_ro):
    """R602 is the LIGHT-FRAME chapter and a concrete wall is not in it.

    Without this filter the basement reported 23 lines, most of them foundation walls and
    the sunken garden's retaining walls. A concrete wall braces by being concrete, and a
    braced wall panel is a thing you fasten to studs.
    """
    basement = braced_wall_lines(catlin_model_ro, "basement")
    assert len(basement) < 8, [line.tag for line in basement]
    assert not [line for line in basement if "SG" in line.tag], \
        "the sunken garden's retaining walls are not braced wall lines"


def test_the_method_follows_the_sheathing(catlin_model_ro):
    """A line is only WSP where every wall on it carries a wood structural panel — a line
    whose sheathing changes part-way is not one method."""
    main = {line.tag: line.method for line in braced_wall_lines(catlin_model_ro, "main")}
    assert set(main.values()) == {METHOD_WSP}
    # The attic's east and west lines are rafter plates: 1-1/2" of wood and no sheathing.
    attic = {line.tag: line.method for line in braced_wall_lines(catlin_model_ro, "attic")}
    assert METHOD_UNRATED in attic.values()


def test_the_sheet_says_on_itself_that_the_panels_are_missing(catlin_model_ro):
    """A braced wall plan with no panels on it that does not say so would read as a plan
    with no bracing required."""
    scene = build_braced_wall_plan(catlin_model_ro, "main")
    printed = " ".join(n.content for n in scene.nodes if isinstance(n, Text))
    assert "PANELS ARE NOT MODELLED" in printed
    assert [n for n in scene.nodes if isinstance(n, Polyline) and n.layer == BWL_LAYER]


def test_a_sheet_exists_for_every_storey_that_has_lines(catlin_model_ro):
    storeys = [s.tag for s in catlin_model_ro.plan.storeys
               if has_braced_wall_content(catlin_model_ro, s.tag)]
    numbers = [s.number for s in build_sheet_index(catlin_model_ro)
               if s.number.startswith("S-103")]
    assert len(numbers) == len(storeys) > 0


def test_line_spacing_passes_and_names_the_clause(catlin_model_ro):
    findings = braced_wall_line_spacing(_ctx(catlin_model_ro))
    assert len(findings) == 1
    assert findings[0].result is Result.PASS
    assert findings[0].code_ref == "IRC R602.10.1.3"
    assert f"{MAX_LINE_SPACING_FT:.0f}'" in findings[0].message


def test_the_panel_rule_is_unknown_and_says_exactly_why(catlin_model_ro):
    """Decision #32: a rule that cannot evaluate is UNKNOWN, never a pass.

    Do NOT close this by deriving panels from the sheathed length of a line. Sheathing a
    wall is not bracing it — a panel has a minimum width, full-height blocking, a fastening
    schedule and a hold-down or return corner at a line's end. Counting sheathed feet would
    report PASS on a house with no hold-downs in it.
    """
    findings = braced_wall_panels(_ctx(catlin_model_ro))
    assert findings
    assert all(f.result is Result.UNKNOWN for f in findings)
    assert all("no braced wall PANEL is modelled" in f.message for f in findings)
    assert all("BracedWallPanel" in (f.fix_hint or "") for f in findings)


def test_a_building_with_no_framed_envelope_earns_not_applicable(catlin_model_ro):
    """Earned from positive evidence of absence, never returned as `[]`."""
    from copy import copy

    stripped = copy(catlin_model_ro)
    stripped.walls = []
    findings = braced_wall_panels(_ctx(stripped))
    assert len(findings) == 1
    assert findings[0].result is Result.NOT_APPLICABLE
