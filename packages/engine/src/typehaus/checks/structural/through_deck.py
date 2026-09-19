"""A wall passing through a floor deck clears the framing, and stands on something.

The subject is every ``(deck, wall)`` pair in ``ResolvedFloor.through_walls`` — read off the
resolved record rather than re-derived, so the check and the saw that cut the sheet
(``resolve/through_deck.py``) cannot disagree about which walls those are.

**Graded against every resolved member, not against joists.** The historical defect here was
a **trimmer**. Catlin's fireplace opening was first drawn at the brick's own 45 1/2"; the
resolver puts the first trimmer ply's *axis* on the opening edge, so the ply reached into the
hole and shared volume with the brick over the full depth of the joist zone.
``notes/east_breast_bearing.md``: *"Nothing caught it… a wall's masonry layer is not a member,
so the clash sat at 0 FAIL until the resolved member boxes were read by hand."*
``structural.member_interference`` walks framing against framing and a masonry layer is not
framing; this check is the other half. Scoped to joists it would have missed that defect
entirely, which is why it reads joists, sisters, blocking, trimmers, headers and rims alike.

**Catlin governs at 5/8"** — joists ``005`` and ``008``, either side of the three
``W-M-FIRE-STUB-*`` piers — against a 1/2" threshold, so it passes with 1/8" to spare. That
5/8" is *residue*: a 44 1/4" panel laid out on a 16" joist module, not a margin anybody chose.
Read a future FAIL here as information about whatever widened, not as a threshold to raise.

The bearing clause is the second half, and it turns a ⚠ into a rule.
``notes/east_breast_bearing.md`` leads with *"if anyone 'simplifies' this by starting the
wythe on the subfloor, §3's 50 plf limit is exceeded roughly four-fold"* — that edit now FAILs
at ~236 plf against ``max_masonry_dead_load_on_wood_plf`` instead of relying on a reader.
"""

from __future__ import annotations

import math

from shapely.geometry import Polygon

from typehaus.checks._authoring import not_applicable as _not_applicable
from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.masonry_load import dead_load_plf, support_at
from typehaus.findings import Finding, Result
from typehaus.quantities import inch
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import parses
from typehaus.resolve.overlay import intersection, union_all

_CHECK_ID = "structural.through_deck_clearance"

#: Overlap below this is noding noise rather than a clash. 1/6 sq in — the catlin trimmer
#: defect was 4.53 sq in, 29x it.
_TOL_AREA_M2 = inch(1).meters * inch(0.16).meters
#: Float slop on a gap measured through several sums.
_GAP_TOL_M = 1e-5
#: Stations along the wall's run at which its support is read, so a pier that starts on a
#: pour and ends over a deck is read as what it is. Same step ``guards.py`` walks.
_STATION_STEP_M = 0.25


@check(Tier.STRUCTURAL, _CHECK_ID)
def through_deck_clearance(ctx: CheckContext) -> list[Finding]:
    """Every wall standing inside a deck clears its members, and bears on something.

    N/A — earned — where no wall in the plan stands inside a deck and spans it;
    ``houses/starter`` gets that verdict, correctly. UNKNOWN for a member whose ``profile``
    does not parse, deferring to ``integrity.member_profile_parses`` by name, because
    ``cross_section`` falls back silently to a 1 1/2" x 5 1/2" guess and a gap measured off a
    guess is not a gap. FAIL — never UNKNOWN — for a gap under the threshold: both geometries
    are stated exactly and no input is missing.

    ``Railing`` and ``Stair`` are outside the subject by ``resolve/through_deck.py``'s
    ``isinstance(_, Wall)`` clause. A stair genuinely does span a deck; its well is a
    ``FloorOpening``, which is the right article for it.
    """
    pairs = [(floor, wall)
             for floor in ctx.model.floors
             for tag in (floor.through_walls or ())
             for wall in ctx.model.walls if wall.tag == tag]
    if not pairs:
        return [_not_applicable(_CHECK_ID, "no wall in this plan stands inside a floor deck "
                                "and spans it, so no sheet is cut round one and there is no "
                                "clearance to grade")]
    min_gap_m = inch(ctx.preferences.structural.min_through_deck_clearance_in).meters
    allowance = ctx.preferences.structural.max_masonry_dead_load_on_wood_plf
    out: list[Finding] = []
    for floor, wall in pairs:
        out.extend(_clearance(floor, wall, min_gap_m))
        out.append(_bearing(ctx, floor, wall, allowance))
    return out


def _wall_face(wall) -> Polygon:
    """The wall's plan footprint — LAYER polygons, so a coating cannot be silently dropped.

    ``_structure_polygon`` would weigh the fireplace wythe's 3 5/8" of brick and drop the
    1/8" silicate wash standing proud of it on the room face. The saw, and the mason's
    clearance, go round the built thing.
    """
    return union_all([Polygon(layer.polygon)
                      for layer in wall.layers if len(layer.polygon) >= 3])


def _clearance(floor, wall, min_gap_m: float) -> list[Finding]:
    face = _wall_face(wall)
    tags = (floor.tag, wall.tag)
    if face.is_empty:
        return [_unknown(_CHECK_ID, f"wall {wall.tag} stands in deck {floor.tag} but "
                         "resolved no layer geometry, so its clearance to the framing "
                         "cannot be measured", tags)]
    out: list[Finding] = []
    tight: tuple[str, float] | None = None
    for member in floor.members:
        if not parses(member.profile):
            out.append(_unknown(
                _CHECK_ID,
                f"deck {floor.tag} member {member.child_key} has profile "
                f"'{member.profile}', which cross_section did not read — it falls back to a "
                "1 1/2\" x 5 1/2\" rectangle, and a clearance measured off a guessed section "
                f"is not a clearance (see integrity.member_profile_parses)", tags))
            continue
        ring, _z_lo, _z_hi = member_footprint(member)
        box = Polygon(ring)
        if not box.is_valid or box.area <= 0:
            continue
        overlap = intersection(face, box)
        if not overlap.is_empty and overlap.area > _TOL_AREA_M2:
            out.append(_advisory(
                _CHECK_ID,
                f"wall {wall.tag} passes through deck {floor.tag} and shares "
                f"{overlap.area / (inch(1).meters ** 2):.2f} sq in of plan with member "
                f"{member.child_key} ({member.profile}) over the full depth of the deck",
                (*tags, member.child_key), Result.FAIL,
                fix_hint=("move the wall off the member's line, or move the member — the two "
                          "cannot occupy the same air")))
            continue
        gap = face.distance(box)
        if tight is None or gap < tight[1]:
            tight = (member.child_key, gap)
        if gap < min_gap_m - _GAP_TOL_M:
            out.append(_advisory(
                _CHECK_ID,
                f"wall {wall.tag} passes through deck {floor.tag} {gap / inch(1).meters:.3f}\" "
                f"clear of member {member.child_key} ({member.profile}), under the "
                f"{min_gap_m / inch(1).meters:.2f}\" a mason needs to lay against it",
                (*tags, member.child_key), Result.FAIL,
                fix_hint=("widen the gap between the wall and that member; the sheet is cut "
                          "to the framing either way, so the clearance is the mason's, not "
                          "the saw's")))
    if any(f.result is Result.FAIL for f in out):
        return out
    if tight is not None:
        out.append(_advisory(
            _CHECK_ID,
            f"wall {wall.tag} passes through deck {floor.tag} clear of every member; "
            f"{tight[0]} governs at {tight[1] / inch(1).meters:.3f}\" against "
            f"{min_gap_m / inch(1).meters:.2f}\"",
            tags, Result.PASS))
    return out


def _bearing(ctx: CheckContext, floor, wall, allowance_plf: float) -> Finding:
    """What the wall stands on at its base, and whether that can carry it."""
    tags = (floor.tag, wall.tag)
    (x0, y0), (x1, y1) = wall.axis
    run = math.hypot(x1 - x0, y1 - y0)
    steps = max(int(math.ceil(run / _STATION_STEP_M)), 1)
    supports = [support_at(ctx, wall, (x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps))
                for i in range(steps + 1)]
    if any(kind is None for kind, _name in supports):
        return _unknown(_CHECK_ID, f"wall {wall.tag} passes through deck {floor.tag} but part "
                        "of its run has nothing modeled under it at its base elevation, so "
                        "what carries it cannot be identified", tags)
    soft = sorted({name for kind, name in supports if kind == "wood"})
    named = sorted({name for _kind, name in supports if name})
    if not soft:
        return _advisory(_CHECK_ID, f"wall {wall.tag} passes through deck {floor.tag} and "
                         f"bears on {', '.join(named)} the length of its run — no part of its "
                         "weight reaches the deck", tags, Result.PASS)
    load_plf = dead_load_plf(ctx, wall, wall.z1_m - wall.z0_m)
    if load_plf is None:
        return _unknown(_CHECK_ID, f"wall {wall.tag} stands on wood framing ({', '.join(soft)}) "
                        "and has a solid layer whose material states no density, so its dead "
                        "load cannot be derived", (*tags, *soft))
    if load_plf <= allowance_plf + 1e-9:
        return _advisory(_CHECK_ID, f"wall {wall.tag} stands on wood framing "
                         f"({', '.join(soft)}) at {load_plf:.0f} plf, at or under the "
                         f"{allowance_plf:.0f} plf allowance", (*tags, *soft), Result.PASS)
    return _advisory(
        _CHECK_ID,
        f"wall {wall.tag} passes through deck {floor.tag} and puts {load_plf:.0f} plf of dead "
        f"load on wood framing ({', '.join(soft)}), over the {allowance_plf:.0f} plf allowance",
        (*tags, *soft), Result.FAIL,
        fix_hint=("start the wall on the pour or the foundation it passes the deck to reach, "
                  "not on the sheet — a wall that BEARS on a deck is not passing through it"))
