"""Tread boards and winder narrow ends (plans/TODO.md "Stair framing follow-ups").

Two geometry defects, both of which the member IR made easy to miss:

* **treads rendered as 1.5" strips.** A tread was spelled ``"2x12"``, and a member's plan
  footprint is built from a profile's *thickness* face — so every tread drew as the 1.5"
  edge of the stock instead of the board a framer nails down.
* **D2: winder narrow ends converged on a point.** Every winder started at the newel's
  *centreline*, so the narrow-end tread depth was exactly 0 where IRC R311.7.5.2.1 wants 6".

The fan now *constructs* the narrow path at the 6" code minimum — three 6" offsets around
the inside corner rather than a radial fan converging on the newel — so
``structural.winder_narrow_tread_depth`` measures a built-in PASS. The check stays: it is
what keeps the construction honest, and the synthetic-fan tests here hold it honest in
both directions.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from typehaus.checks import build_context
from typehaus.checks.structural.stairs import (
    MIN_WINDER_NARROW_TREAD_IN,
    winder_narrow_tread_depth,
    winder_walk_line_depth,
)
from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedStair
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR

_TREAD_THICKNESS_M = inch(1.5).meters
# A profile string is a rounded human-readable catalog key ("deck 10.3333x1.5"), so a
# going read back out of one lands within a thou of the resolver's own float.
_PROFILE_ROUND_TRIP_M = inch(0.001).meters


def _treads(stair):
    return [member for member in stair.members if member.category == "tread"]


def _ring_extent(ring):
    xs = [x for x, _ in ring]
    ys = [y for _, y in ring]
    return max(xs) - min(xs), max(ys) - min(ys)


# ----------------------------------------------------------------- tread boards
def test_every_tread_is_a_full_depth_board(catlin_model):
    for stair in catlin_model.stairs:
        tread_depth = stair.tread_depth_m
        for tread in _treads(stair):
            section = cross_section(tread.profile)
            assert section.width_m == pytest.approx(tread_depth, abs=_PROFILE_ROUND_TRIP_M), (
                tread.child_key)
            assert section.depth_m == pytest.approx(_TREAD_THICKNESS_M), tread.child_key


def test_default_treads_are_eleven_inches_with_a_one_inch_nose(catlin_model):
    # The two EXTERIOR flights are the exception and each states why in its own source: 11"
    # boards with NO nose, so the going is the full 11". ST-G-SERVICE keeps the 3'-8" run the
    # four concrete treads it replaced occupied; ST-SG-PORCH (2026-09-03) borrows the same
    # pattern to reach grade off the porch's east edge. Neither has a shaft to fit inside, so
    # the compaction a nose buys is worth nothing on either — and outdoors a nose is a lip
    # that ices.
    for stair in catlin_model.stairs:
        assert stair.tread_depth_m == pytest.approx(inch(11).meters)
        if stair.tag in ("ST-G-SERVICE", "ST-SG-PORCH"):
            assert stair.nosing_depth_m == 0.0
            assert stair.going_depth_m == pytest.approx(inch(11).meters)
            continue
        assert stair.nosing_depth_m == pytest.approx(inch(1).meters)
        assert stair.going_depth_m == pytest.approx(inch(10).meters)


def test_tread_plan_footprint_is_going_by_stair_width(catlin_model):
    """The regression itself: this used to measure 1.5" on the going axis."""
    for stair in catlin_model.stairs:
        tread_depth = stair.tread_depth_m
        for tread in _treads(stair):
            long_side, short_side = sorted(_ring_extent(member_footprint(tread)[0]),
                                           reverse=True)
            assert short_side == pytest.approx(tread_depth, abs=_PROFILE_ROUND_TRIP_M), (
                tread.child_key)
            assert long_side == pytest.approx(tread.length_m, abs=1e-9), tread.child_key
            assert short_side > inch(1.5).meters, tread.child_key


def test_tread_boards_tile_the_flight_without_overlap_or_gap(catlin_model):
    """Boards are centred half a going past their riser, so consecutive centres are
    exactly one going apart — no double thickness at a riser, no bare stringer between."""
    for stair in catlin_model.stairs:
        going = stair.going_depth_m
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
    # The flight springs off the top winder box's departing rim, at the newel end of it.
    springing = next(member for member in winder.members
                     if member.child_key == "newel-000").p0
    going = winder.going_depth_m
    reaches = [math.hypot(tread.p0[0] - springing[0], tread.p0[1] - springing[1])
               + winder.tread_depth_m / 2.0
               for tread in _treads(winder)]
    assert min(reaches) == pytest.approx(going, abs=1e-9)  # first board starts at the springing
    assert max(reaches) == pytest.approx(going * len(reaches), abs=1e-9)


# ------------------------------------------------------------------ riser lines
def test_every_straight_tread_carries_its_riser_line(catlin_model):
    """The 2D stair icon marks riser faces, not board centrelines: each tread publishes the
    ``going * i`` face it serves, parallel to the board and one going from its neighbours.
    Drawing the centrelines instead put a (going − nosing)/2 sliver at one end of every
    flight and (going + nosing)/2 at the other, against full-going interiors — uniform
    steps that read as non-uniform."""
    for stair in catlin_model.stairs:
        going = stair.going_depth_m
        by_flight: dict[str, list] = {}
        for tread in _treads(stair):
            assert tread.riser_line is not None, tread.child_key
            a, b = tread.riser_line
            assert math.dist(a, b) == pytest.approx(tread.length_m, abs=1e-9), tread.child_key
            axis = (tread.p1[0] - tread.p0[0], tread.p1[1] - tread.p0[1])
            line = (b[0] - a[0], b[1] - a[1])
            assert abs(axis[0] * line[1] - axis[1] * line[0]) < 1e-9, tread.child_key
            by_flight.setdefault(tread.child_key.rsplit("-", 1)[0], []).append(tread)
        for key, treads in by_flight.items():
            treads.sort(key=lambda member: member.z0_m)
            steps = [math.dist(lower.riser_line[0], upper.riser_line[0])
                     for lower, upper in zip(treads, treads[1:])]
            assert steps == pytest.approx([going] * len(steps), abs=1e-9), key


def test_riser_grid_is_flush_at_the_springing_and_the_landing_zone(catlin_model):
    """Flush ends are the point: the first drawn line sits exactly where the flight
    springs, and a landing edge is exactly one going past the last riser before it."""
    def _collinear(point, a, b):
        return abs((b[0] - a[0]) * (point[1] - a[1])
                   - (b[1] - a[1]) * (point[0] - a[0])) < 1e-9

    winder = next(stair for stair in catlin_model.stairs if stair.winder_count)
    # The straight flight springs at the turn square's departing edge — the top winder's
    # fan line — so its first riser line lies on that same line.
    top_fan = next(member for member in winder.members
                   if member.child_key == f"winder-{winder.winder_count - 1:03d}")
    first = min(_treads(winder), key=lambda member: member.z0_m)
    assert _collinear(top_fan.p0, *first.riser_line)
    assert _collinear(top_fan.p1, *first.riser_line)
    for stair in (s for s in catlin_model.stairs if s.layout == "u_split_landing"):
        along = 1 if stair.run_direction == "y" else 0
        going = stair.going_depth_m
        by_flight: dict[str, list] = {}
        for tread in _treads(stair):
            by_flight.setdefault(tread.child_key.rsplit("-", 1)[0], []).append(tread)
        lower = sorted(by_flight["tread-lower"], key=lambda member: member.z0_m)
        upper = sorted(by_flight["tread-upper"], key=lambda member: member.z0_m)
        landing = next(member for member in stair.members
                       if member.child_key == "landing-lower")
        near_edge = landing.p0[along]  # the landing zone's edge toward the flights
        # The upper flight's first riser face IS the landing-zone edge...
        assert upper[0].riser_line[0][along] == pytest.approx(near_edge, abs=1e-9), stair.tag
        # ...and the lower flight's last riser sits exactly one going before it.
        assert abs(near_edge - lower[-1].riser_line[0][along]) == pytest.approx(
            going, abs=1e-9), stair.tag


# ------------------------------------------------------------- winder narrow ends
def test_winder_narrow_ends_are_spaced_at_the_code_minimum(catlin_model):
    winder = next(stair for stair in catlin_model.stairs if stair.winder_count)
    winders = [member for member in winder.members if member.category == "winder"]
    assert len(winders) == winder.winder_count
    narrow_ends = {member.p0 for member in winders}
    assert len(narrow_ends) == len(winders), "narrow ends still share one point"
    gaps = [math.dist(upper.p0, lower.p0) for lower, upper in zip(winders, winders[1:])]
    assert min(gaps) >= inch(6).meters - 1e-9


def test_winder_narrow_end_depth_is_measured_and_reported(catlin_model):
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    findings = winder_narrow_tread_depth(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.result is Result.PASS
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


# ------------------------------------------------------------------ the walk line
def test_winder_walk_line_is_measured_a_foot_out_from_the_narrow_end(catlin_model):
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    findings = winder_walk_line_depth(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.result is Result.PASS
    assert finding.severity.value == "warn"  # advisory, never build-breaking
    assert "R311.7.5.2.1" in finding.message
    # It is a *different* measurement from the narrow end, taken further out along the
    # same treads, so it reads wider than the code-minimum narrow end.
    narrow = winder_narrow_tread_depth(ctx)[0]
    assert _reported_inches(finding) > _reported_inches(narrow)


def test_walk_line_check_passes_a_turn_that_does_open_up(catlin_model):
    """A fan wide enough at the walk line passes, so the FAIL above is the well and not
    a rule that can only ever fire. The synthetic winders run 1 m out from their narrow
    ends, radiating from a point 1 m apart at the far end: at the 12" walk line the gap
    is a bit under a third of that."""
    ctx = SimpleNamespace(model=SimpleNamespace(stairs=[_stair_with_narrow_ends(0.0)]))
    assert [finding.result for finding in winder_walk_line_depth(ctx)] == [Result.FAIL]
    wide = ResolvedStair(uid="S", tag="S-WIDE", storey="main", to_storey="second",
                         outline=[], riser_count=4, riser_height_m=0.18,
                         tread_depth_m=0.28, run_direction="x", run_reversed=False,
                         layout="right_angle_winder", turn_direction="left",
                         winder_count=3, members=tuple(
                             _winder_at((0.0, index * inch(11).meters), index * 0.18)
                             for index in range(3)))
    ctx = SimpleNamespace(model=SimpleNamespace(stairs=[wide]))
    assert [finding.result for finding in winder_walk_line_depth(ctx)] == [Result.PASS]


def _reported_inches(finding) -> float:
    """The measured number a stair advisory prints, e.g. ``... is 5.0", under ...``."""
    return float(finding.message.split(" is ")[1].split('"')[0])
