"""``code.R312_1_1_stair_open_side`` — R312.1.1 at the open side of a flight.

The rule this file covers exists because catlin passed without it: ST-S2A climbed 30"-120"
out of RM-S-STUDY2 with its whole south side open and every check green, since
``code.R312_1_guard`` grades a floor *opening's* four edges and a flight's own side is not
one of them. So the tests below are as much about the three ways a side is legitimately
*not* open as they are about the deficiency: an over-eager version of this rule fails all
four of the house's stairs.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.code.mn_residential.stair_guards import stair_open_side_guard
from typehaus.findings import Result
from typehaus.quantities import inch


@pytest.fixture(scope="module")
def ctx(catlin_plan, catlin_model_ro):
    return SimpleNamespace(plan=catlin_plan, model=catlin_model_ro, preferences=None)


def _with(ctx, edit):
    """``ctx`` with its authored elements mapped — ``None`` drops one."""
    kept = [e for e in (edit(e) for e in ctx.plan.all_elements()) if e is not None]
    return SimpleNamespace(plan=SimpleNamespace(all_elements=lambda: kept),
                           model=ctx.model, preferences=ctx.preferences)


def _by_stair(findings):
    return {f.message.split(":")[0]: f for f in findings}


def test_every_catlin_flight_is_walled_guarded_or_inside_its_own_well(ctx):
    """All four stairs adjudicated, all four PASS, and each for its own reason.

    ST-B2M and ST-M2S are switchbacks in a shaft: their outer sides are wall and their inner
    sides face each other over the well partition's 4 1/2" reservation, which is inside the
    stair's own outline. ST-G-SERVICE is five risers and never gets 30" up. ST-S2A is the
    one with a genuinely open side, and it carries RL-A-FLIGHT-GUARD.
    """
    findings = stair_open_side_guard(ctx)
    by_stair = _by_stair(findings)
    assert set(by_stair) == {"ST-B2M", "ST-M2S", "ST-S2A", "ST-G-SERVICE"}
    assert {f.result for f in findings} == {Result.PASS}, [f.message for f in findings]
    assert "RL-A-FLIGHT-GUARD" in by_stair["ST-S2A"].message
    # The other three pass without crediting a guard — nothing stands on their sides.
    assert not [tag for tag, f in by_stair.items()
                if tag != "ST-S2A" and "guarded by" in f.message]


def test_the_defect_this_rule_was_written_for(ctx):
    """RL-A-FLIGHT-GUARD knocked out is exactly the house as it stood: ST-S2A open on the
    south for its whole straight run, and every other rule in the book still green."""
    findings = stair_open_side_guard(
        _with(ctx, lambda e: None if getattr(e, "tag", None) == "RL-A-FLIGHT-GUARD" else e))
    by_stair = _by_stair(findings)
    assert by_stair["ST-S2A"].result is Result.FAIL
    # 10 nosing ends: the straight flight's 12 treads less the two lowest, which stand 30"
    # and 22 1/2" over the study floor — R312.1.1 reaches neither.
    assert "10 nosing end(s)" in by_stair["ST-S2A"].message
    assert "105\" fall" in by_stair["ST-S2A"].message
    assert {by_stair[tag].result for tag in ("ST-B2M", "ST-M2S", "ST-G-SERVICE")} \
        == {Result.PASS}


def test_a_short_guard_fails_on_height_rather_than_reading_as_a_missing_one(ctx):
    """R312.1.2 exception 1 lets a stair guard stand 34" off the nosing line where a floor
    guard owes 36". A 30" rail is a height deficiency with a named element, not an absence —
    the same two-verdict shape ``code.R312_1_guard`` has."""
    findings = stair_open_side_guard(_with(
        ctx, lambda e: (e.model_copy(update={"height": inch(30)})
                        if getattr(e, "tag", None) == "RL-A-FLIGHT-GUARD" else e)))
    finding = _by_stair(findings)["ST-S2A"]
    assert finding.result is Result.FAIL
    assert finding.code_ref == "R312.1.2"
    assert "RL-A-FLIGHT-GUARD" in finding.message and "34\"" in finding.message


def test_a_guard_at_exactly_34_inches_passes(ctx):
    """The 34" boundary is the whole reason this rule cannot borrow ``fall_protection``'s
    36" constant, so it is pinned rather than left to the 36" the house happens to build."""
    findings = stair_open_side_guard(_with(
        ctx, lambda e: (e.model_copy(update={"height": inch(34)})
                        if getattr(e, "tag", None) == "RL-A-FLIGHT-GUARD" else e)))
    assert _by_stair(findings)["ST-S2A"].result is Result.PASS


def test_a_partition_standing_above_a_flight_does_not_close_its_side(ctx):
    """W-A-GC-S sits 1 3/8" outboard of ST-S2A's south side in plan and would close it on a
    plan-only test — but it stands on the attic deck at 20'-0", five feet over the treads it
    passes. The wall clause brackets the nosing between ``z0`` and ``z1`` for this reason;
    without the lower half, the rule silently exempts the very flight it was written for."""
    from typehaus.model.structure import Railing

    walls = [w for w in ctx.model.walls if w.tag == "W-A-GC-S"]
    assert walls, "W-A-GC-S is the wall this test is about"
    assert walls[0].z0_m / 0.3048 == pytest.approx(20.0, abs=0.01)
    # With the guard gone, the partition overhead must not stand in for it.
    findings = stair_open_side_guard(_with(
        ctx, lambda e: None if isinstance(e, Railing)
        and e.tag == "RL-A-FLIGHT-GUARD" else e))
    assert _by_stair(findings)["ST-S2A"].result is Result.FAIL


def test_a_house_with_no_stairs_is_unknown_never_a_silent_pass(ctx):
    findings = stair_open_side_guard(
        SimpleNamespace(plan=ctx.plan,
                        model=SimpleNamespace(stairs=(), floors=(), walls=()),
                        preferences=None))
    assert [f.result for f in findings] == [Result.UNKNOWN]
