"""A *member*-level short-framing finding: the piece, not the wall.

``solver._short_wall_finding`` grades a WALL against its own plate stack, and it was
written for the wall that wants to be a course of lumber laid flat. It cannot see the
defect underneath it: a wall 62" tall at one end and raked into an eave frames perfectly
legal plates and studs at its tall end and a **1 1/4"** stud at its short one. Nothing
failed, nothing drew wrong, and the BOM cheerfully bought the offcut — catlin's
``W-A-STU-N`` carried exactly that member for the life of the model, and so do
``W-A-SN-EAST`` and ``W-A-GC-S``.

The shape is ``framing/posts.short_post_findings``'s: a named gap, WARN/UNKNOWN, at the
place the arithmetic already knows the answer, rather than a silent wrong number.

**Only vertical pieces in the stud line.** ``p0 == p1`` is what makes a member a stud-line
member here — a plate, a rim, a header or a sill is a board laid along the wall and its
length is a span, not a stack height. A tread, a brace and a strap are out for the same
reason.

**Why 3".** A stud-line member is captured between 1 1/2" of plate below and 1 1/2" above:
a piece shorter than the material it is nailed between cannot be end-nailed at all, and
what the framer actually installs there is a solid block cut to fill the gap. The
threshold is therefore the two plate thicknesses it has to reach, not a proportion of the
wall — the same reasoning the ordinary cripple space follows, which is why a 3" head
cripple (catlin's ``W-B-CE``) passes and a 2 1/8" one does not.

A leaf, like ``framing/posts.py``: it imports ``findings``/``resolve.model`` and is
imported by ``framing/solver.py``, never the other way round.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import FramedMember

__all__ = ["MIN_STUD_LINE_IN", "STUD_LINE_CATEGORIES", "short_member_findings"]

#: The categories that stand between the plates. ``post`` is not among them: a post inside
#: a wall is graded by ``short_post_findings`` against the wall's framing height, which is
#: a different question with a different answer.
STUD_LINE_CATEGORIES: frozenset[str] = frozenset({"stud", "king", "jack", "cripple"})

#: Two plate thicknesses — see the module docstring.
MIN_STUD_LINE_IN = 3.0

_VERTICAL_TOL_M = 1e-9


def short_member_findings(wall_tag: str,
                          members: tuple[FramedMember, ...]) -> list[Finding]:
    """WARN for each stud-line member resolved shorter than :data:`MIN_STUD_LINE_IN`.

    One finding per member, named by its ``child_key``: the point of a member-level
    finding is that it says *which* piece, and collapsing a wall's offcuts into one line
    would put us back where the wall-level finding already is.
    """
    findings: list[Finding] = []
    for member in members:
        if member.category not in STUD_LINE_CATEGORIES:
            continue
        if abs(member.p0[0] - member.p1[0]) > _VERTICAL_TOL_M:
            continue
        if abs(member.p0[1] - member.p1[1]) > _VERTICAL_TOL_M:
            continue
        length_in = (member.z1_m - member.z0_m) / M_PER_IN
        if length_in >= MIN_STUD_LINE_IN - 1e-9:
            continue
        findings.append(Finding(
            severity=Severity.WARN, check_id="integrity.member_shorter_than_minimum",
            message=(f"{member.category} {member.child_key} on {wall_tag} resolves "
                     f"{length_in:.4g}\" long — shorter than the {MIN_STUD_LINE_IN:.4g}\" "
                     "of plate it is nailed between, so it cannot be end-nailed"),
            element_tags=(wall_tag,), result=Result.UNKNOWN,
            fix_hint=("a gap this short is filled with solid blocking, not a member: "
                      "end the wall's framing at the last full-length stud, or raise the "
                      "plate/header that swallowed this one's length")))
    return findings
