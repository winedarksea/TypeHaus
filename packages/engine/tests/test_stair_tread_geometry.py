"""Tread boards and winder narrow ends (plans/TODO.md "Stair framing follow-ups").

Two geometry defects, both of which the member IR made easy to miss:

* **treads rendered as 1.5" strips.** A tread was spelled ``"2x12"``, and a member's plan
  footprint is built from a profile's *thickness* face — so every tread drew as the 1.5"
  edge of the stock instead of the board a framer nails down.
* **D2: winder narrow ends converged on a point.** Every winder started at the newel's
  *centreline*, so the narrow-end tread depth was exactly 0 where IRC R311.7.5.2.1 wants 6".

The narrow ends now leave the newel's face, which is real construction but still short of
the 6" — a quarter turn taken in three winders cannot reach it. That residual is reported
by ``structural.winder_narrow_tread_depth`` rather than papered over, and the last test
here is what holds the reporting honest in both directions.
"""

from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.checks import build_context
from typehaus.checks.structural.stairs import (
    MIN_WINDER_NARROW_TREAD_IN,
    winder_narrow_tread_depth,
)
from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.resolve import resolve
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedStair
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"
_TREAD_THICKNESS_M = inch(1.5).meters
# A profile string is a rounded human-readable catalog key ("deck 10.3333x1.5"), so a
# going read back out of one lands within a thou of the resolver's own float.
_PROFILE_ROUND_TRIP_M = inch(0.001).meters


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [finding for finding in findings if finding.severity.value == "error"]
    assert not errors, [finding.message for finding in errors]
    return model


def _treads(stair):
    return [member for member in stair.members if member.category == "tread"]


def _ring_extent(ring):
    xs = [x for x, _ in ring]
    ys = [y for _, y in ring]
    return max(xs) - min(xs), max(ys) - min(ys)


# ----------------------------------------------------------------- tread boards
def test_every_tread_is_a_full_depth_board(catlin_model):
    for stair in catlin_model.stairs:
        going = stair.tread_depth_m
        for tread in _treads(stair):
            section = cross_section(tread.profile)
            assert section.width_m == pytest.approx(going, abs=_PROFILE_ROUND_TRIP_M), (
                tread.child_key)
            assert section.depth_m == pytest.approx(_TREAD_THICKNESS_M), tread.child_key


def test_tread_plan_footprint_is_going_by_stair_width(catlin_model):
    """The regression itself: this used to measure 1.5" on the going axis."""
    for stair in catlin_model.stairs:
        going = stair.tread_depth_m
        for tread in _treads(stair):
            long_side, short_side = sorted(_ring_extent(member_footprint(tread)[0]),
                                           reverse=True)
            assert short_side == pytest.approx(going, abs=_PROFILE_ROUND_TRIP_M), (
                tread.child_key)
            assert long_side == pytest.approx(tread.length_m, abs=1e-9), tread.child_key
            assert short_side > inch(1.5).meters, tread.child_key


def test_tread_boards_tile_the_flight_without_overlap_or_gap(catlin_model):
    """Boards are centred half a going past their riser, so consecutive centres are
    exactly one going apart — no double thickness at a riser, no bare stringer between."""
    for stair in catlin_model.stairs:
        going = stair.tread_depth_m
        by_flight: dict[str, list] = {}
        for tread in _treads(stair):
            by_flight.setdefault(tread.child_key.rsplit("-", 1)[0], []).append(tread)
        for key, treads in by_flight.items():
            if len(treads) < 2:
                continue
            treads.sort(key=lambda member: member.z0_m)
            steps = [math.hypot(b.p0[0] - a.p0[0], b.p0[1] - a.p0[1])
                     for a, b in zip(treads, treads[1:])]
            assert steps == pytest.approx([going] * len(steps), abs=1e-9), key


def test_top_tread_board_reaches_the_arrival_deck(catlin_model):
    """Anchoring the board on its riser line instead of its centre would leave the flight
    half a going short of the deck it arrives at — a visible hole at the top of the run."""
    winder = next(stair for stair in catlin_model.stairs if stair.winder_count)
    springing = next(member for member in winder.members
                     if member.child_key == "winder-header").p0
    going = winder.tread_depth_m
    reaches = [math.hypot(tread.p0[0] - springing[0], tread.p0[1] - springing[1]) + going / 2.0
               for tread in _treads(winder)]
    assert min(reaches) == pytest.approx(going, abs=1e-9)  # first board starts at the springing
    assert max(reaches) == pytest.approx(going * len(reaches), abs=1e-9)


# ------------------------------------------------------------- winder narrow ends
def test_winder_narrow_ends_no_longer_converge_on_the_newel_centreline(catlin_model):
    winder = next(stair for stair in catlin_model.stairs if stair.winder_count)
    newel = next(member for member in winder.members if member.child_key == "newel-000")
    winders = [member for member in winder.members if member.category == "winder"]
    assert len(winders) == winder.winder_count
    narrow_ends = {member.p0 for member in winders}
    assert len(narrow_ends) == len(winders), "narrow ends still share one point"
    half_face = cross_section("4x4").width_m / 2.0
    for member in winders:
        reach = math.hypot(member.p0[0] - newel.p0[0], member.p0[1] - newel.p0[1])
        # On the square post's face: half a face out at worst, half a diagonal at best.
        assert half_face - 1e-9 <= reach <= half_face * math.sqrt(2.0) + 1e-9, member.child_key


def test_winder_narrow_end_depth_is_measured_and_reported(catlin_model):
    """Catlin's quarter turn cannot reach 6" in three winders around a 4x4, so the check
    must FAIL here — and it must be an advisory WARN, never a build-breaking error."""
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    findings = winder_narrow_tread_depth(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.result is Result.FAIL
    assert finding.severity.value == "warn"
    assert "R311.7.5.2.1" in finding.message


def _winder_at(narrow_end, z0):
    return FramedMember("S", f"winder-{z0:.3f}", "winder", "tapered tread",
                        narrow_end, (narrow_end[0] + 1.0, narrow_end[1]),
                        z0, z0 + _TREAD_THICKNESS_M, 1.0)


def _stair_with_narrow_ends(spacing_m):
    members = tuple(_winder_at((0.0, index * spacing_m), index * 0.18) for index in range(3))
    return ResolvedStair(uid="S", tag="S-WIND", storey="main", to_storey="second",
                         outline=[], riser_count=4, riser_height_m=0.18,
                         tread_depth_m=0.28, run_direction="x", run_reversed=False,
                         layout="right_angle_winder", turn_direction="left",
                         winder_count=3, members=members)


def test_winder_check_passes_a_turn_that_does_meet_the_six_inch_minimum():
    """The FAIL above must be the geometry, not a rule that can only ever fail."""
    generous = inch(MIN_WINDER_NARROW_TREAD_IN + 1.0).meters
    ctx = SimpleNamespace(model=SimpleNamespace(stairs=[_stair_with_narrow_ends(generous)]))
    findings = winder_narrow_tread_depth(ctx)
    assert [finding.result for finding in findings] == [Result.PASS]

    tight = inch(MIN_WINDER_NARROW_TREAD_IN - 1.0).meters
    ctx = SimpleNamespace(model=SimpleNamespace(stairs=[_stair_with_narrow_ends(tight)]))
    assert [finding.result for finding in winder_narrow_tread_depth(ctx)] == [Result.FAIL]
