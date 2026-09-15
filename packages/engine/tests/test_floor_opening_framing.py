"""Floor-opening edge framing (plans/TODO.md "Stair framing follow-ups", defect 1).

Two defects lived side by side in ``resolve/floors.py``:

* the doubled trimmer pair was emitted twice at *identical* endpoints, so the second ply
  was invisible geometry — it rendered, measured and clashed as one member, not two; and
* an opening header was emitted as a single ply of the deck's own ``JoistSpec.member``,
  which is neither doubled nor sized: catlin's 3'-4" attic header and its 11'-0" stair
  header were the same unsized I-joist ply.

These lock the fix, plus the advisory that says so when a header outruns the prescriptive
table rather than letting the drawn member imply a prescriptive answer.
"""

from __future__ import annotations


import pytest

from typehaus.checks import build_context
from typehaus.checks.structural.checks import floor_opening_header_within_prescriptive
from typehaus.findings import Result
from typehaus.quantities import ft, inch
from typehaus.resolve.floors import opening_header_profile
from typehaus.resolve.framing.profiles import cross_section
from _helpers import CATLIN as CATLIN_DIR


def _members(model, category):
    return [member for floor in model.floors for member in floor.members
            if member.category == category]


def _endpoints(member):
    return (round(member.p0[0], 6), round(member.p0[1], 6),
            round(member.p1[0], 6), round(member.p1[1], 6))


# ------------------------------------------------------------------ trimmer plies
def test_trimmer_plies_are_not_coincident(catlin_model):
    trimmers = _members(catlin_model, "trimmer")
    assert trimmers, "catlin frames stair openings in both wood decks"
    assert len({_endpoints(member) for member in trimmers}) == len(trimmers)


def test_trimmer_plies_lie_face_to_face_outboard_of_the_opening(catlin_model):
    """Ply 0 keeps the authored opening line (the header ends bear on it); ply 1 steps
    exactly one ply thickness *away* from the hole, which is where the second trimmer of
    a doubled pair goes.

    **Only the DOUBLED edges are in scope, and since 2026-09-14 that is a real filter rather
    than a formality.** ``_trimmer_plies`` lays one ply, not two, on an edge inside
    R502.10.1's 4' short-opening allowance, and catlin now has two such openings: the 9"
    pillar chases ``FO-SG-BF2``/``-BR2``, where ``PT-SG-BF2``/``PT-SG-BR2`` pass through
    ``FS-SG-PORCH`` on their way down to the cast columns. An edge with no ply 1 is that
    rule working, so this asserts the GEOMETRY of a pair wherever there is a pair, and
    :func:`test_a_short_opening_is_framed_in_single_plies` asserts that the singles are
    single.
    """
    trimmers = {member.child_key: member for member in _members(catlin_model, "trimmer")}
    pairs = {key[: -len("-0")] for key in trimmers
             if key.endswith("-0") and f"{key[: -len('-0')]}-1" in trimmers}
    assert pairs
    for prefix in pairs:
        first, second = trimmers[f"{prefix}-0"], trimmers[f"{prefix}-1"]
        thickness = cross_section(first.profile).width_m
        gap = max(abs(second.p0[0] - first.p0[0]), abs(second.p0[1] - first.p0[1]))
        assert gap == pytest.approx(thickness, abs=1e-9), prefix
        # Same run, same z band — a ply, not a different member.
        assert second.length_m == pytest.approx(first.length_m)
        assert (second.z0_m, second.z1_m) == pytest.approx((first.z0_m, first.z1_m))


# ------------------------------------------------------------------ header sizing
def test_opening_headers_are_multi_ply_and_deck_deep(catlin_model):
    """Every header is flush in its joist band, and doubled unless R502.10.1 says otherwise.

    The DEPTH half holds for every header without exception: a header hangs *inside* the
    band so the cut joists land on it at their own depth, and one that is not band-deep is
    drawn wrong whatever its ply count.

    The PLY half is conditional, and the condition is the code's. ``opening_header_profile``
    emits a single member the size of the floor joist for an opening inside R502.10.1's 4'
    allowance on a sawn-lumber deck, and doubles up past it. Until 2026-09-14 catlin had no
    short opening at all, so "always >= 2" and "doubled unless short" were the same
    assertion; the 9" pillar chases in ``FS-SG-PORCH`` separated them.
    """
    from typehaus.resolve.floors import _prescriptive_short_opening

    headers = _members(catlin_model, "header")
    assert headers
    short = 0
    for floor in catlin_model.floors:
        joist = next((member for member in floor.members if member.category == "joist"), None)
        if joist is None:
            continue
        band_depth = cross_section(joist.profile).depth_m
        for header in (m for m in floor.members if m.category == "header"):
            section = cross_section(header.profile)
            # **The span is not the whole condition — the DECK MATERIAL is the other
            # half.** R502.10 is a sawn-lumber table, so ``FO-M-FIRE``'s 3'-9" header is
            # short and still doubled: ``FS-M-WEST`` is framed in I-joists, where "a single
            # member the same size as the floor joist" means a hung I-joist with web
            # stiffeners and backer blocks out of a manufacturer's table this engine cannot
            # grade. Testing on span alone would have called that header wrong.
            if _prescriptive_short_opening(header.length_m, joist.profile):
                # R502.10.1: a single member the same size as the floor joist.
                assert section.plies == 1, header.child_key
                assert header.profile == joist.profile, header.child_key
                short += 1
            else:
                assert section.plies >= 2, header.child_key
            # Flush in the joist band, so the cut joists hang off it at their own depth.
            assert section.depth_m == pytest.approx(band_depth), header.child_key
    # The two pillar chases, both edges of each. Named rather than merely tolerated, so
    # deleting them would fail here instead of quietly relaxing the rule above back to
    # "always doubled".
    #
    # **Four and not two.** Neither chase has a declared bearing under either edge: the four
    # porch beams stop at the pillar's east and west faces now, so along the chase's own x
    # band there is no beam axis for ``_opening_edge_has_declared_bearing`` to find, and both
    # edges get a member. At ``FO-SG-BF2`` the south one lands in the 1 1/2" between the
    # front rim band and ``PT-SG-BF2``'s south face, which is exactly the block that closes
    # that chase at the deck edge — a real member, not a drafting artifact.
    assert short == 4, "expected both headed edges of each 9\" pillar chase"


def test_header_ply_count_tracks_the_span(catlin_model):
    """Ply count must track span, not draw the same single ply for every opening."""
    band = cross_section("11.875 I-joist").depth_m
    short = cross_section(opening_header_profile(ft(3, 4).meters, band))
    long = cross_section(opening_header_profile(ft(11).meters, band))
    assert short.plies == 2
    assert long.plies > short.plies
    assert short.depth_m == pytest.approx(band) and long.depth_m == pytest.approx(band)


def _plan_without_stair_bearing_refs(catlin_plan):
    """Catlin with FO-S-STAIR's ``bearing_refs`` stripped.

    Both of that opening's long edges are carried by bearing wall, so the resolver draws
    no header for it at all — which leaves the advisory nothing to report. Dropping the
    declared bearing restores exactly the condition the rule guards: a 10'-3" opening edge
    with nothing under it, closed by a header past the prescriptive table.
    """
    plan = catlin_plan
    elements = {
        storey: [element.model_copy(update={"bearing_refs": ()})
                 if getattr(element, "tag", None) == "FO-S-STAIR" else element
                 for element in storey_elements]
        for storey, storey_elements in plan.elements.items()
    }
    return plan.model_copy(update={"elements": elements})


def test_no_header_is_drawn_where_bearing_wall_carries_the_edge(catlin_model):
    """FO-S-STAIR is drawn to the finished well, so no edge coincides with a wall axis.

    The bearing test reads each declared wall's plan *footprint*, so both long edges are
    still recognised as wall-borne — a centreline-equality test claimed neither was and
    put a 10'-3" engineered header under both (plans/TODO.md D3).
    """
    headers = [member for member in _members(catlin_model, "header")
               if "FO-S-STAIR" in member.child_key]
    assert headers == []


def test_beyond_prescriptive_header_is_reported(catlin_plan):
    """A 10'-3" floor-opening header is an engineered beam; the drawing set has to say
    so, which ``structural.header_prescriptive`` only ever did for *wall* openings."""
    plan = _plan_without_stair_bearing_refs(catlin_plan)
    ctx, _ = build_context(plan, CATLIN_DIR)
    findings = floor_opening_header_within_prescriptive(ctx)
    failures = [finding for finding in findings if finding.result is Result.FAIL]
    assert failures, "an unsupported FO-S-STAIR edge needs a header spanning 10'-3\""
    assert all(finding.severity.value == "warn" for finding in findings)
    for header in _members(ctx.model, "header"):
        if header.length_m / inch(12).meters <= 8.0 + 1e-9:
            assert not any(header.child_key in finding.message for finding in failures)


# ------------------------------------------------ R502.10.1: the short-opening allowance
# IRC R502.10.1 lets a header joist spanning 4 ft or less be a single member the same size
# as the floor joist, with single trimmers; the doubling starts past that line. The engine
# threw the prescriptive answer away except for its leading ply digit, so 36", 48" and 49"
# all emitted the same 2-ply LVL.
#
# The allowance is deliberately SAWN-LUMBER ONLY. On an I-joist or floor-truss deck "the
# same size as the floor joist" means a single I-joist used as a header, hung on both
# faces — a manufacturer's table, not R502.10's — so the engineered header is kept there.
# Catlin is all-engineered and therefore unchanged by this rule; that is the honest answer.

def test_short_sawn_opening_takes_a_single_joist_sized_header():
    band = cross_section("2x8").depth_m
    assert opening_header_profile(ft(3, 4).meters, band, "2x8") == "2x8"
    assert opening_header_profile(ft(4).meters, band, "2x8") == "2x8"


def test_past_four_feet_a_sawn_opening_is_back_on_the_prescriptive_header():
    band = cross_section("2x8").depth_m
    header = cross_section(opening_header_profile(ft(4, 1).meters, band, "2x8"))
    assert header.plies == 2


def test_engineered_decks_keep_the_engineered_header_at_every_span():
    """The strength guard: R502.10 is a sawn-lumber table and does not reach an I-joist."""
    band = cross_section("11.875 I-joist").depth_m
    for member in ("11.875 I-joist", "11.875 floor truss", "11.875 TJI 230"):
        short = cross_section(opening_header_profile(ft(3).meters, band, member))
        assert short.plies == 2, member
        assert short.depth_m == pytest.approx(band), member


def test_trimmer_plies_follow_the_same_line():
    from typehaus.resolve.floors import _trimmer_plies
    assert _trimmer_plies(ft(3, 4).meters, "2x8") == 1
    assert _trimmer_plies(ft(4, 1).meters, "2x8") == 2
    assert _trimmer_plies(ft(3, 4).meters, "11.875 I-joist") == 2


def test_catlin_is_unchanged_by_the_short_opening_allowance(catlin_model):
    """Every catlin deck is engineered, so every trimmer stays a doubled pair."""
    trimmers = {member.child_key for member in _members(catlin_model, "trimmer")}
    assert trimmers
    assert {key for key in trimmers if key.endswith("-1")}, "doubled pairs survive"
    for key in trimmers:
        assert key.endswith(("-0", "-1")), key
