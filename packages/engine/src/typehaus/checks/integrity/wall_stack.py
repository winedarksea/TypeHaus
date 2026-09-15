"""A wall stacked on a wall must land on it — a hand-worked top is a hand-worked mistake.

A tall panel built as several walls is authored as a chain: each wall's ``base_elevation``
is the previous one's base plus the previous one's ``top``, worked out by hand and typed
in. Nothing re-derives it. Get one wrong and the wall above starts somewhere its neighbour
does not end, opening a horizontal slot straight through the assembly — and every other
consumer is satisfied, because each wall on its own is a perfectly good wall.

catlin's ``W-M-FIRE`` is the panel this was written from: five brick courses — STUB,
PLINTH, JAMB-S, JAMB-N, HEAD — spanning -13 7/16" to 64 15/16" absolute, every junction an
arithmetic step someone did in their head. The authoring comment in ``storeys/main.py``
even prints the base/top table it was worked from, which is exactly the shape of thing
that goes stale.

**Most of that chain is already defended, and by geometry rather than by grading.**
``resolve/platform.extend_walls_to_platform`` grows a lower wall up to meet the wall
stacked on it whenever the band between them is at most ``_MAX_BAND_M`` (24"). So a
mistyped ``top`` inside that range is not a defect in the resolved model at all — it is
absorbed, and the brick is banded to where it should have been. Typing
``W-M-FIRE-PLINTH.top`` as 18" instead of 24" resolves byte-identically to the correct
model. A check that claimed to catch that would be claiming to catch nothing.

**What the lifter deliberately will not close is this rule's subject.** Past 24" it stops,
because — in its own words — "anything deeper is a real void (a stairwell, a double-height
space) and must not be silently absorbed into the wall below". That is the right call for
a void and the wrong outcome for a typo, and the two are indistinguishable to it. It also
lifts a wall *bodily*, to the nearest thing above any part of its run, so a gap that opens
only over some stations — the firebox — survives it untouched. Those are the gaps that
reach the resolved model, and those are the ones graded here.

**Subject — walls sharing a plane and a storey.** Coplanar (parallel, and within a couple
of inches of the same normal offset) so that a slot between them is really a slot, and
overlapping along that plane so that one is really above the other.

**Same storey, and that restriction is not optional.** Without it the sweep pairs a
basement wall with an attic one and calls the storey in between a 253" gap: on catlin that
is four FAILs, none of them defects. Cross-storey continuity is a different question with
a different mechanism — the storey datum derives it — and it is not this rule's subject.
What this rule governs is the hand-worked chain *inside* one storey.

**A gap can be earned.** The firebox is a gap: PLINTH's top to HEAD's base, 20 5/8" of
nothing, and it is the whole point of the design. What earns it is the two jambs — at
neighbouring stations along the same plane, walls that *do* span that band. A slot with
nothing spanning it anywhere along the panel is a defect; a slot with masonry either side
of it is an opening. So the grade is not "is there a gap" but "is this gap spanned
somewhere" — and without that rule catlin's fireplace reads as a hole in its own wall.
"""

from __future__ import annotations

import itertools
from collections import defaultdict

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry import project_onto_axis, wall_frame
from typehaus.resolve.model import ResolvedWall

_CHECK_ID = "integrity.wall_stack_continuous"

#: A quarter inch — under a mortar joint, and three orders below the kind of typo this
#: exists to catch (a whole course, or a whole wall).
_TOLERANCE_M = 0.25 * M_PER_IN

#: Two walls are the same plane only if their axes are within ~5 deg. This is a much
#: tighter bar than ``reveal_alignment``'s 15 deg: there, a backer a little off-parallel is
#: still the backer; here, two walls that are not really the same panel must not be chained.
_PARALLEL_COS = 0.996

#: How far apart two coplanar walls' faces may sit and still be one panel. A brick wythe
#: and its wash, or a stud wall and a furred layer, share a plane; two walls 6" apart do
#: not stack, they pass.
_COPLANAR_M = 2.0 * M_PER_IN


def _plane_key(wall: ResolvedWall) -> tuple | None:
    """A hashable identity for the vertical plane ``wall`` stands in, or ``None``.

    The tangent is canonicalised so a wall authored S->N and one authored N->S land in the
    same group — direction of authoring is not a property of the plane.
    """
    origin, tangent, normal_vec, axis_length = wall_frame(wall)
    if axis_length <= 1e-9:
        return None
    tx, ty = tangent
    if (tx, ty) < (-tx, -ty):
        tx, ty = -tx, -ty
    offset = origin[0] * normal_vec[0] + origin[1] * normal_vec[1]
    return (round(tx / (1 - _PARALLEL_COS)), round(ty / (1 - _PARALLEL_COS)),
            round(abs(offset) / _COPLANAR_M))


def _lateral_intervals(members: list[ResolvedWall]):
    """Station bands along the shared plane, each with the walls standing in it.

    The breakpoints are every wall end, so within one band the set of walls present is
    constant and their z-extents can be stacked against each other directly. Only bands
    holding two or more walls are stacks; one wall over a station is nothing to grade.
    """
    base = max(members, key=lambda w: wall_frame(w)[3])
    origin, tangent, _normal, _length = wall_frame(base)
    spans = []
    for wall in members:
        a = project_onto_axis(wall.axis[0], origin, tangent)
        b = project_onto_axis(wall.axis[1], origin, tangent)
        spans.append((min(a, b), max(a, b), wall))

    out = []
    edges = sorted({round(value, 6) for span in spans for value in span[:2]})
    for lo, hi in itertools.pairwise(edges):
        if hi - lo < _TOLERANCE_M:
            continue
        mid = (lo + hi) / 2.0
        present = [w for (a, b, w) in spans if a - _TOLERANCE_M <= mid <= b + _TOLERANCE_M]
        if len(present) >= 2:
            out.append((lo, hi, present))
    return out


def _spanned_elsewhere(intervals, here, low: float, high: float) -> bool:
    """Does any *other* station band on this plane carry a wall across ``low..high``?

    This is what makes the firebox an opening rather than a slot: the jambs stand at
    neighbouring stations and run the full height of the gap between plinth and head.
    """
    for lo, hi, present in intervals:
        if (lo, hi) == here:
            continue
        for wall in present:
            if wall.z0_m <= low + _TOLERANCE_M and wall.z1_m >= high - _TOLERANCE_M:
                return True
    return False


@check(Tier.INTEGRITY, _CHECK_ID)
def wall_stack_continuous(ctx: CheckContext) -> list[Finding]:
    groups: dict[tuple, list[ResolvedWall]] = defaultdict(list)
    for wall in ctx.model.walls:
        key = _plane_key(wall)
        if key is not None:
            groups[(key, wall.storey)].append(wall)

    # One wall typed too high opens a slot at every station across the panel, against every
    # wall below it — three bands and three different lower neighbours, for one typo. The
    # defect is the wall that fails to land, so that is the unit: one finding per upper
    # wall, reported against the NEAREST thing under it, because "even the highest wall
    # below you is 30" down" is the statement that cannot be argued with. A finding per band
    # would bury one typo in its own restatements (``member_profile``'s "64 sticks off one
    # typo are one defect").
    slots: dict[str, tuple[str, float, float, float]] = {}
    stacks = 0
    junctions = 0
    earned = 0
    for _key, members in sorted(groups.items(), key=lambda row: str(row[0])):
        if len(members) < 2:
            continue
        intervals = _lateral_intervals(members)
        if not intervals:
            continue
        stacks += 1
        for lo, hi, present in intervals:
            bands = sorted((w.z0_m, w.z1_m, w.tag) for w in present)
            for (_z0a, z1a, tag_a), (z0b, _z1b, tag_b) in itertools.pairwise(bands):
                junctions += 1
                gap = z0b - z1a
                if gap <= _TOLERANCE_M:
                    continue
                if _spanned_elsewhere(intervals, (lo, hi), z1a, z0b):
                    earned += 1
                    continue
                if tag_b not in slots or gap < slots[tag_b][3]:
                    slots[tag_b] = (tag_a, z1a, z0b, gap)

    findings: list[Finding] = []
    for tag_b, (tag_a, z1a, z0b, gap) in sorted(slots.items()):
        findings.append(failed(
            _CHECK_ID,
            f"{tag_b} starts at {z0b / M_PER_IN:.2f}\" but the nearest wall under it, "
            f"{tag_a}, tops out at {z1a / M_PER_IN:.2f}\" — a {gap / M_PER_IN:.2f}\" "
            f"slot runs through the panel, and nothing spans it anywhere along the "
            f"plane",
            tags=(tag_a, tag_b),
            fix=(f"a stacked wall's base_elevation is the one below it plus that "
                 f"one's top, worked by hand — re-add the chain through {tag_a} "
                 f"and correct whichever term is stale. A gap this size is past "
                 f"what resolve/platform.py will close for you; if it is a real "
                 f"void rather than a typo, put a wall across it or say so")))

    if not stacks:
        return [not_applicable(_CHECK_ID,
                               "no two walls in this building share a plane and a storey, "
                               "so nothing here is stacked on anything")]
    if not findings:
        return [passed(_CHECK_ID,
                       f"every one of {junctions} junction(s) across {stacks} stacked "
                       f"wall panel(s) closes, with {earned} earned opening(s)")]
    return findings
