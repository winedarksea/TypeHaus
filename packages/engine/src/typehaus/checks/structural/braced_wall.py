"""IRC R602.10 wall bracing — the lines are derived, the panels are authored, both graded.

MNSPECT runs a discrete braced-wall inspection and this set had no braced wall plan at all.
S-103 draws one (``emit/draw/bracedwallplan.py``) and this is the rule that grades it.

**Do not derive panels from the sheathed length of a line.** Sheathing a wall is not
bracing it — a braced wall panel has a minimum length, and at a line's end a return corner,
a hold-down or a 48" panel. A check that counted sheathed feet would report PASS on a house
with no hold-downs in it, which is worse than reporting that it does not know. That is why
the panels are an authored ``BracedWallPanel`` and why a ``braced`` line carrying none is
still UNKNOWN (decision #32: a rule that cannot evaluate never passes).

**Not every line owes a length**, and the reason is measured rather than assumed
(``resolve/braced_walls.py`` derives the kind). An engineered shear wall is out of the
prescriptive path; a rafter plate is not a wall; a gable end is braced by the roof
assembly; a poured foundation braces by being concrete; an interior partition is not a
designated line here; and framed infill inside an R404 concrete box has no braced-wall
share to give — the finding prints the other reading so a reviewer can disagree with
reasoning rather than with silence.

Per-panel rules live in ``braced_wall_panels.py``; the table reads in
``bracing_tables.py``; what one line needs in ``bracing_eval.py``.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.bracing_eval import LineEvaluation, evaluate_line
from typehaus.checks.structural.bracing_tables import MAX_LINE_SPACING_FT
from typehaus.findings import (
    Authority,
    Finding,
    Result,
    Severity,
    failed,
    not_applicable,
    passed,
    unknown,
)
from typehaus.quantities import M_PER_IN
from typehaus.resolve.braced_walls import (
    KIND_ENGINEERED,
    KIND_FOUNDATION,
    KIND_GABLE_END,
    KIND_INFILL,
    KIND_INTERIOR,
    KIND_PLATE,
    braced_wall_lines,
    resolved_braced_wall_panels,
)

_SPACING_ID = "structural.braced_wall_line_spacing"
_PANELS_ID = "structural.braced_wall_panels"

#: The engineered lateral system catlin's one shear-panel line belongs to. A line whose
#: walls all carry ``Wall.shear_panel`` hands its verdict to that item rather than to a
#: prescriptive table (decision #79 (2)).
_ENGINEERED_ITEM = "lateral_system/RF-BW-CANOPY"


def _storeys(ctx: CheckContext) -> list[str]:
    return [storey.tag for storey in ctx.model.plan.storeys]


@check(Tier.STRUCTURAL, _SPACING_ID)
def braced_wall_line_spacing(ctx: CheckContext) -> list[Finding]:
    """R602.10.1.3 — parallel braced wall lines not more than 60'-0" apart."""
    findings: list[Finding] = []
    for storey in _storeys(ctx):
        lines = braced_wall_lines(ctx.model, storey)
        if not lines:
            continue
        for axis in ("x", "y"):
            along = sorted([line for line in lines if line.direction == axis],
                           key=lambda item: _offset(item, axis))
            if len(along) < 2:
                continue
            for first, second in zip(along, along[1:], strict=False):
                gap = abs(_offset(second, axis) - _offset(first, axis)) / M_PER_IN / 12.0
                if gap > MAX_LINE_SPACING_FT:
                    findings.append(failed(
                        _SPACING_ID,
                        f"{storey}: {first.tag} and {second.tag} are {gap:.1f}' apart, "
                        f"over R602.10.1.3's {MAX_LINE_SPACING_FT:.0f}'",
                        (first.tag, second.tag), code="IRC R602.10.1.3"))
    if not findings:
        graded = [line for storey in _storeys(ctx)
                  for line in braced_wall_lines(ctx.model, storey)]
        if not graded:
            return [not_applicable(
                _SPACING_ID,
                "no storey in this building carries a wall on the exterior envelope, so "
                "there is no braced wall line to space", code="IRC R602.10.1.3")]
        return [passed(_SPACING_ID,
                       f"{len(graded)} braced wall line(s) across "
                       f"{len(_storeys(ctx))} storey(s), none over "
                       f"{MAX_LINE_SPACING_FT:.0f}' apart", code="IRC R602.10.1.3")]
    return findings


def _offset(line, axis: str) -> float:
    """Where the line sits ACROSS its own direction — a line running in x is located by y."""
    return line.p0[1] if axis == "x" else line.p0[0]


#: Why a line is not graded against R602.10.3, by kind. The sentence is the verdict.
_NOT_APPLICABLE_REASONS = {
    KIND_PLATE: ("every wall on it is under 12 inches tall — a rafter plate is not a wall "
                 "and carries no braced wall panel"),
    KIND_GABLE_END: ("it is a gable end on the topmost storey, braced by the roof assembly "
                     "above it; R602.10.4.2 sheathes it and R602.10.3 asks it for no "
                     "length of its own"),
    KIND_FOUNDATION: ("no wall on it resolves a framing member in its structure layer: it "
                      "is a poured foundation, which braces by being concrete, and R602 is "
                      "the light-frame chapter"),
    KIND_INTERIOR: ("it carries rooms on both sides on every wall — an interior partition "
                    "this plan does not designate as a braced wall line (R602.10.1 leaves "
                    "the designation to the plan)"),
}


@check(Tier.STRUCTURAL, _PANELS_ID)
def braced_wall_panels(ctx: CheckContext) -> list[Finding]:
    """R602.10.3 — required bracing length per line, against the panels authored on it."""
    findings: list[Finding] = []
    total = 0
    for storey in _storeys(ctx):
        lines = braced_wall_lines(ctx.model, storey)
        if not lines:
            continue
        total += len(lines)
        panels, _unplaced = resolved_braced_wall_panels(ctx.model, storey, lines)
        for line in lines:
            if line.kind == KIND_ENGINEERED:
                findings.append(Finding(
                    severity=Severity.WARN, check_id=_PANELS_ID,
                    message=(f"N/A — {storey}: {line.tag} carries a ShearPanelSpec on every "
                             f"wall, so it is an engineered shear wall and not a "
                             f"prescriptive braced wall line; its capacity belongs to "
                             f"`{_ENGINEERED_ITEM}`"),
                    element_tags=(line.tag, *line.wall_tags), code_ref="IRC R602.10",
                    result=Result.NOT_APPLICABLE, authority=Authority.ENGINEERED,
                    engineering_item=_ENGINEERED_ITEM))
                continue
            if line.kind == KIND_INFILL:
                findings.append(not_applicable(
                    _PANELS_ID, _infill_reason(ctx, storey, line),
                    (line.tag, *line.wall_tags), code="IRC R602.10.3"))
                continue
            reason = _NOT_APPLICABLE_REASONS.get(line.kind)
            if reason is not None:
                findings.append(not_applicable(
                    _PANELS_ID, f"{storey}: {line.tag} — {reason}",
                    (line.tag, *line.wall_tags), code="IRC R602.10"))
                continue
            findings.append(_graded(ctx, storey, line, lines, panels))
    if not total:
        return [not_applicable(
            _PANELS_ID,
            "no storey in this building carries a wall on the exterior envelope, so R602.10 "
            "governs no line here", code="IRC R602.10.3")]
    return findings


def _graded(ctx: CheckContext, storey: str, line, lines, panels) -> Finding:
    mine = [p for p in panels if p.line_tag == line.tag]
    if not mine:
        return unknown(
            _PANELS_ID,
            f"{storey}: {line.tag} is a braced wall line {line.length_ft:.1f}' long and no "
            f"braced wall PANEL is modelled on it, so the required bracing length cannot be "
            f"compared against anything",
            (line.tag, *line.wall_tags), code="IRC R602.10.3",
            fix="author a BracedWallPanel per panel (wall_ref, start, width, R602.10.4 "
                "method) in a `# haus: editable` file")
    evaluation = evaluate_line(ctx.model, line, lines, panels)
    if evaluation.required_ft is None:
        return unknown(
            _PANELS_ID,
            f"{storey}: {line.tag} — {evaluation.describe()}",
            (line.tag, *line.wall_tags), code="IRC R602.10.3",
            fix="author the missing input named above")
    message = f"{storey}: {line.tag} — {evaluation.describe()}. {report(evaluation)}"
    tags = (line.tag, *[t for p in evaluation.panels for t in p.panel.tags])
    if evaluation.ok:
        return passed(_PANELS_ID, message, tags, code="IRC R602.10.3")
    return failed(_PANELS_ID, message, tags, code="IRC R602.10.3",
                  fix="lengthen a panel, add one, or take a factor the model has not "
                      "claimed (the rows read are printed above)")


def report(evaluation: LineEvaluation) -> str:
    """Every row read and every factor not taken, for the finding and for S-103."""
    parts = [f"read: {evaluation.base.row}" if evaluation.base else ""]
    parts += [f"x {factor.row}" for factor in evaluation.factors]
    parts += [f"NOT taken: {reason}" for reason in evaluation.not_taken]
    for grade in evaluation.panels:
        if grade.reason:
            parts.append(f"{'/'.join(grade.panel.tags)}: {grade.reason}")
    return " | ".join(p for p in parts if p)


def _infill_reason(ctx: CheckContext, storey: str, line) -> str:
    """The basement south line, and the reading that disagrees, printed on purpose.

    Decision #79 / #17: this is framed infill standing inside an R404 concrete box. The
    storey's lateral system is the 8" concrete around it and the framed wall carries no
    storey shear to a foundation it is not part of. A reviewer who reads it the other way
    gets the arithmetic here rather than a blank.
    """
    other = evaluate_line(ctx.model, line, braced_wall_lines(ctx.model, storey),
                          resolved_braced_wall_panels(ctx.model, storey)[0])
    alternative = ("the other reading, first story of the stack, cannot be priced here: "
                   + "; ".join(other.gaps)) if other.required_ft is None else (
        f"read the other way — as the first story of the stack — it would need "
        f"{other.required_ft:.2f} ft on {line.length_ft:.1f} ft of line")
    return (f"{storey}: {line.tag} is framed infill in a concrete storey. The lateral "
            f"system of this storey is the 8-inch R404 wall box around it, and a story with "
            f"no braced-wall share to give asks this line for no length. {alternative}")
