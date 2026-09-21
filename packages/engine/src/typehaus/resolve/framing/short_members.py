"""A *member*-level short-framing finding: the piece, not the wall.

``solver._short_wall_finding`` grades a WALL against its own plate stack, and it was
written for the wall that wants to be a course of lumber laid flat. It cannot see the
defect underneath it: a wall 62" tall at one end and raked into an eave frames perfectly
legal plates and studs at its tall end and a **1 1/4"** stud at its short one. Nothing
failed, nothing drew wrong, and the BOM cheerfully bought the offcut — catlin's
``W-A-STU-N`` carried exactly that member for the life of the model, and so did
``W-A-SN-EAST`` and ``W-A-GC-S``.

``is_stud_line_offcut`` is now also the **gate**: ``solver.frame_wall`` refuses to emit
what this module would name, so the finding is the assertion that the invariant holds
rather than the report of a defect. The offcut is not re-categorised as blocking — a
sub-3" tapered block is not a piece a framer cuts either, and billing one would repeat
the defect in a different category (``houses/catlin/DESIGN-LOG.md``, 2026-09-20).

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

__all__ = ["MIN_STUD_LINE_IN", "MIN_STUD_LINE_M", "STUD_LINE_CATEGORIES",
           "is_stud_line_offcut", "short_member_findings"]

#: The categories that stand between the plates. ``post`` is not among them: a post inside
#: a wall is graded by ``short_post_findings`` against the wall's framing height, which is
#: a different question with a different answer.
STUD_LINE_CATEGORIES: frozenset[str] = frozenset({"stud", "king", "jack", "cripple"})

#: Two plate thicknesses — see the module docstring. The ONE minimum: ``framing/openings``
#: imports it too, so the gate that refuses to emit a sliver and the finding that asserts
#: none was emitted cannot drift apart.
MIN_STUD_LINE_IN = 3.0
MIN_STUD_LINE_M = MIN_STUD_LINE_IN * M_PER_IN

_VERTICAL_TOL_M = 1e-9


def is_stud_line_offcut(member: FramedMember) -> bool:
    """True for a vertical stud-line member too short to be end-nailed.

    The one predicate behind both the gate (``solver.frame_wall``'s return, which refuses
    to emit such a member) and the finding below (which asserts the gate held). Gate-set
    ≡ finding-set is the whole point: a category this returns False for is one the report
    never names, so widening the gate means widening :data:`STUD_LINE_CATEGORIES`.
    """
    if member.category not in STUD_LINE_CATEGORIES:
        return False
    if abs(member.p0[0] - member.p1[0]) > _VERTICAL_TOL_M:
        return False
    if abs(member.p0[1] - member.p1[1]) > _VERTICAL_TOL_M:
        return False
    return (member.z1_m - member.z0_m) < MIN_STUD_LINE_M - _VERTICAL_TOL_M


def short_member_findings(wall_tag: str,
                          members: tuple[FramedMember, ...]) -> list[Finding]:
    """WARN for each stud-line offcut — today, the assertion that the gate held.

    ``solver.frame_wall`` filters these out of its return with the same predicate, so on a
    framed model this is expected to be empty and a finding means the gate was bypassed
    (a member appended *after* that return: ``furring``/``truss_wall`` cladding verticals,
    which this pass has never covered either).

    One finding per member, named by its ``child_key``: the point of a member-level
    finding is that it says *which* piece, and collapsing a wall's offcuts into one line
    would put us back where the wall-level finding already is.
    """
    findings: list[Finding] = []
    for member in members:
        if not is_stud_line_offcut(member):
            continue
        length_in = (member.z1_m - member.z0_m) / M_PER_IN
        findings.append(Finding(
            severity=Severity.WARN, check_id="integrity.member_shorter_than_minimum",
            message=(f"{member.category} {member.child_key} on {wall_tag} wanted "
                     f"{length_in:.4g}\" — shorter than the {MIN_STUD_LINE_IN:.4g}\" of "
                     "plate it would be nailed between, so it cannot be end-nailed and "
                     "was refused"),
            element_tags=(wall_tag,), result=Result.UNKNOWN,
            fix_hint=("nothing was emitted here: a gap this short is filled with solid "
                      "blocking, not a member. If the piece is wanted, end the wall's "
                      "framing at the last full-length stud, or raise the plate/header "
                      "that swallowed this one's length")))
    return findings
