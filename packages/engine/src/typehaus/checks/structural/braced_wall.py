"""IRC R602.10 wall bracing — the lines are derivable, the panels are not.

MNSPECT runs a discrete braced-wall inspection and this set had no braced wall plan at all.
S-1xx now draws one (``emit/draw/bracedwallplan.py``), and this is the rule that grades it.

**Two questions, and this check can answer only one.**

*Are there braced wall lines, and are they spaced legally?* Yes, derivable.
``resolve/layout_lines.py`` builds the collinear stacked chains a line is, and R602.10.1.3
bounds the spacing between parallel lines at 60'-0" for most methods. Both are graded here.

*Is there enough bracing on each line?* R602.10.3's required length is a table lookup — wind
speed, exposure, storey, wall height, method — compared against the sum of the PANEL widths
on the line. **This model carries no panels.** A panel is a designer's decision about where
to spend bracing, and its method carries hold-down, fastening and corner requirements no
field here expresses. So this half is UNKNOWN, and it is UNKNOWN in the strict sense of
decision #32: the rule cannot evaluate, and a rule that cannot evaluate never passes.

**Do not "fix" this by deriving panels from the sheathed length of the line.** Sheathing a
wall is not bracing it — a braced wall panel has a minimum width, full-height blocking, a
fastening schedule and, at a line's end, a hold-down or a return corner. A check that
counted sheathed feet would report PASS on a house with no hold-downs in it, which is worse
than reporting that it does not know.

What closes it is a ``BracedWallPanel`` element authored in a ``# haus: editable`` file:
position, width and method per panel. Until then this check names the lines it found and
what it could not grade, which is what a reviewer needs in order to ask for the rest.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.emit.draw.bracedwallplan import METHOD_UNRATED, braced_wall_lines
from typehaus.findings import Finding, failed, not_applicable, passed, unknown
from typehaus.quantities import M_PER_IN

_SPACING_ID = "structural.braced_wall_line_spacing"
_PANELS_ID = "structural.braced_wall_panels"

#: IRC R602.10.1.3: braced wall lines are spaced not more than 60 feet on centre. The
#: exception (25' for a line braced by methods GB or PCP alone) is not implemented — no
#: catlin line uses either, and implementing an exception nothing reaches is a rule that
#: cannot be wrong because it never runs.
MAX_LINE_SPACING_FT = 60.0


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
            # A line running in x is braced against loads in y, so what matters is the
            # spacing between lines of the SAME direction, measured across it.
            along = sorted(lines, key=lambda item: _offset(item, axis))
            along = [line for line in along if line.direction == axis]
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
    """Where the line sits ACROSS its own direction — the coordinate spacing is measured
    on. A line running in x is located by its y."""
    return line.p0[1] if axis == "x" else line.p0[0]


@check(Tier.STRUCTURAL, _PANELS_ID)
def braced_wall_panels(ctx: CheckContext) -> list[Finding]:
    """R602.10.3 — required bracing length per line. UNKNOWN until panels are modelled.

    Reported per storey rather than once, so the register names how much is ungraded rather
    than reducing a five-storey house to a single line of doubt.
    """
    findings: list[Finding] = []
    total = 0
    for storey in _storeys(ctx):
        lines = braced_wall_lines(ctx.model, storey)
        if not lines:
            continue
        total += len(lines)
        rated = [line for line in lines if line.method != METHOD_UNRATED]
        findings.append(unknown(
            _PANELS_ID,
            f"{storey}: {len(lines)} braced wall line(s), {len(rated)} on wood structural "
            f"panel sheathing — the required bracing length cannot be compared against "
            f"anything, because no braced wall PANEL is modelled in this house",
            tuple(line.tag for line in lines[:4]),
            code="IRC R602.10.3",
            fix="author a BracedWallPanel per panel (position, width, R602.10.4 method) "
                "in a `# haus: editable` file"))
    if not total:
        return [not_applicable(
            _PANELS_ID,
            "no storey in this building carries a wall on the exterior envelope, so R602.10 "
            "governs no line here", code="IRC R602.10.3")]
    return findings
