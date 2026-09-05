"""A reveal cut through a veneer must line up with the opening it reveals.

A ``RoughOpening`` in a wythe standing in front of another wall is not an opening in its
own right — it is a *hole for* the door or window behind it. Nothing owned that
relationship. The two elements are authored on different walls, off different nodes, in
different files, and each is individually correct: the reveal frames a rectangle, the door
fills a rough opening, and every geometry, framing and egress consumer is satisfied by
both. Move one and the other does not follow, and ``haus check`` reports 0 FAIL over a
brick arch sitting half a leaf off the door it arches over.

That is not hypothetical. catlin's ``AO-B-BRICK-DOOR`` sat 6" east of ``D-B-PATIO`` for
five days: the reveal was authored against the door's position, the door later moved 6"
west, and the reveal stayed. The stale comment above it still claimed the door's head was
"covered across its full width" while the reveal in fact left the west 6" of the leaf pair
bare and overhung 6" of blind brick to the east.

**Subject — a rough opening with a wall standing behind it.** Not every rough opening is a
reveal: most are cased passthroughs (catlin's ``D-S-STUDY2``, ``O-S-VANITY``), a hole in a
single wall that fronts nothing and reveals nothing. What makes a reveal a reveal is a
*second* wall, roughly parallel, a short normal distance away, overlapping it in
elevation — the backer whose door or window this hole exists to show. A rough opening with
no such wall is out of this rule's subject, not a gap in it.

**Pair.** Within that backer, the nearest ``door``/``window`` that overlaps the reveal in
elevation. A veneer cavity is 1½" and the deepest assembly either side of it is a few
inches more, so 12" reaches any real backer while staying far short of the next opening on
an unrelated wall. A backer wall with no opening in it *is* an UNKNOWN: a hole through a
wythe onto blind wall behind is either a mistake or a decoration, and the model cannot tell
which.

**Grade.** The lateral (along-wall) offset between the two plan centres. Elevations are
deliberately *not* graded: a reveal is normally shorter than the opening it fronts (catlin
crowns its arch below the door head on purpose), so a height difference is a design choice
while a lateral difference never is.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry import opening_center, project_onto_axis, wall_frame
from typehaus.resolve.model import ResolvedOpening, ResolvedWall

_CHECK_ID = "integrity.reveal_concentric"

#: How far off the reveal's own wall plane a backer may sit and still be the thing it
#: reveals. The cavity itself is 1½"; this covers cavity plus either assembly's depth.
_SEARCH_NORMAL_M = 12.0 * M_PER_IN

#: Two walls are the same plane if their axes are within ~15° of parallel. Anything more is
#: a different face of the building, not a backer.
_PARALLEL_COS = 0.966

#: Well under a mortar joint, and two orders below the 6" error this check was written for.
_TOLERANCE_M = 1.0 * M_PER_IN


def _z_span(wall: ResolvedWall, opening: ResolvedOpening) -> tuple[float, float]:
    """The opening's absolute elevation band. ``base_ref_z_m`` is the datum a sill is
    stated from (→ ``ResolvedWall.base_ref_z_m``), not the wall's clad bottom."""
    base = wall.base_ref_z_m + opening.sill_m
    return base, base + opening.height_m


def _overlaps(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return min(a[1], b[1]) - max(a[0], b[0]) > 0.0


@check(Tier.INTEGRITY, _CHECK_ID)
def reveal_concentric(ctx: CheckContext) -> list[Finding]:
    walls = {wall.tag: wall for wall in ctx.model.walls}
    placed = []
    for opening in ctx.model.openings:
        wall = walls.get(opening.host_wall)
        if wall is None:
            continue
        center = opening_center(wall, opening)
        if center is None:  # degenerate axis
            continue
        placed.append((opening, center, wall))

    reveals = [row for row in placed if row[0].kind == "rough_opening"]
    if not reveals:
        return [not_applicable(_CHECK_ID,
                               "no wall in this building carries a rough opening, so there "
                               "is no reveal to line up with anything")]

    findings: list[Finding] = []
    aligned = 0
    fronted = 0
    for opening, center, wall in sorted(reveals, key=lambda row: row[0].tag):
        _origin, tangent, normal_vec, axis_length = wall_frame(wall)
        if axis_length <= 1e-9:
            continue
        span = _z_span(wall, opening)

        # The backer: a parallel wall across the cavity, covering this hole in elevation
        # and reaching past it along the axis.
        backers = set()
        for candidate in ctx.model.walls:
            if candidate.tag == wall.tag:
                continue
            o_origin, o_tangent, _o_normal, o_len = wall_frame(candidate)
            if o_len <= 1e-9:
                continue
            if abs(tangent[0] * o_tangent[0] + tangent[1] * o_tangent[1]) < _PARALLEL_COS:
                continue
            if not _overlaps(span, (candidate.z0_m, candidate.z1_m)):
                continue
            across = abs(project_onto_axis(o_origin, center, normal_vec))
            if across > _SEARCH_NORMAL_M:
                continue
            along = project_onto_axis(center, o_origin, o_tangent)
            if not (-_TOLERANCE_M <= along <= o_len + _TOLERANCE_M):
                continue
            backers.add(candidate.tag)
        if not backers:
            continue  # a cased passthrough, not a reveal — out of subject
        fronted += 1

        best = None
        for other, other_center, other_wall in placed:
            if other.kind == "rough_opening" or other_wall.tag not in backers:
                continue
            if not _overlaps(span, _z_span(other_wall, other)):
                continue
            along = abs(project_onto_axis(other_center, center, tangent))
            if best is None or along < best[1]:
                best = (other, along)

        if best is None:
            findings.append(unknown(
                _CHECK_ID,
                f"{opening.tag} cuts through a wythe standing in front of "
                f"{', '.join(sorted(backers))}, but no door or window in that wall is "
                f"behind it — the reveal opens onto blind wall",
                tags=(opening.tag, *sorted(backers)),
                fix=("author the opening this reveal fronts, or — if the arch is "
                     "decorative — say so in a comment beside it")))
            continue

        other, along = best
        if along <= _TOLERANCE_M:
            aligned += 1
            continue
        findings.append(failed(
            _CHECK_ID,
            f"{opening.tag} sits {along / M_PER_IN:.1f}\" along the wall from "
            f"{other.tag}, the opening it reveals — the two are not concentric",
            tags=(opening.tag, other.tag),
            fix=("move the reveal's position onto the opening's — they are authored off "
                 "different nodes on different walls, so one does not follow the other")))

    if not fronted:
        return [not_applicable(_CHECK_ID,
                               "every rough opening in this building is a cased "
                               "passthrough — none stands in front of another wall, so "
                               "none reveals anything")]
    if not findings:
        return [passed(_CHECK_ID,
                       f"every one of {aligned} reveals is concentric with the opening "
                       f"behind it")]
    return findings
