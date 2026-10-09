"""Physical rectangular tread boards and consistent riser-face grids."""

from __future__ import annotations

import math

import pytest

from typehaus.quantities import inch
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section

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
            authored = catlin_model.plan.by_tag(stair.tag)
            thickness = authored.tread_thickness.meters if authored.tread_thickness else _TREAD_THICKNESS_M
            assert section.depth_m == pytest.approx(thickness), tread.child_key


def test_default_treads_are_eleven_inches_with_a_one_inch_nose(catlin_model):
    # The two EXTERIOR flights are the exception and each states why in its own source: 11"
    # boards with NO nose, so the going is the full 11". ST-G-SERVICE keeps the 3'-8" run the
    # four concrete treads it replaced occupied; ST-SG-PORCH (2026-09-03) borrows the same
    # pattern to reach grade off the porch's east edge. Neither has a shaft to fit inside, so
    # the compaction a nose buys is worth nothing on either — and outdoors a nose is a lip
    # that ices.
    for stair in catlin_model.stairs:
        if stair.tag == "ST-BW-ENTRY":
            # The third exception, and it is not a board at all: 18" (was 24") since
            # 2026-09-10, when the flight became four composite BOX tiers on 42" footings
            # rather than a cut-stringer run. The "tread" is the tier's whole walking
            # surface — face-fastened square-edge deck boards on supports at 9" o.c. — so
            # there is nothing for a nose to overhang and the going is the full 18".
            assert stair.tread_depth_m == pytest.approx(inch(18).meters)
            assert stair.nosing_depth_m == 0
            assert stair.going_depth_m == pytest.approx(inch(18).meters)
            continue
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
    first = min(_treads(winder), key=lambda m: m.z1_m)
    last = max(_treads(winder), key=lambda m: m.z1_m)
    normal = winder.winder_turn.normals[-1]
    origin = first.riser_line[0]
    ring = member_footprint(last)[0]
    reach = max((p[0] - origin[0]) * normal[0] + (p[1] - origin[1]) * normal[1] for p in ring)
    assert reach == pytest.approx(winder.going_depth_m * len(_treads(winder)), abs=1e-9)


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
    top_fan = winder.winder_turn.riser_lines[-1]
    first = min(_treads(winder), key=lambda member: member.z0_m)
    assert _collinear(top_fan[0], *first.riser_line)
    assert _collinear(top_fan[1], *first.riser_line)
    for stair in (s for s in catlin_model.stairs if s.layout == "u_split_landing"):
        along = 1 if stair.run_direction == "y" else 0
        going = stair.going_depth_m
        by_flight: dict[str, list] = {}
        for tread in _treads(stair):
            by_flight.setdefault(tread.child_key.rsplit("-", 1)[0], []).append(tread)
        lower = sorted(by_flight["tread-lower"], key=lambda member: member.z0_m)
        upper = sorted(by_flight["tread-upper"], key=lambda member: member.z0_m)
        # ** EACH FLIGHT AGAINST ITS OWN LANDING. ** The two half-landings no longer share
        # one near edge: a flight is anchored to the storey edge it MEETS, so when the tread
        # counts differ (``flight_treads`` odd, ST-M2S) the upper half-landing starts one
        # going further back and absorbs the slack. Reading the upper flight against
        # ``landing-lower`` was passing only because the upper flight used to be laid out
        # backwards from the lower flight's line — the bug, not the rule
        # (notes/u_stair_split_landing.md).
        for flight, landing_key in (("lower", "landing-lower"), ("upper", "landing-upper")):
            landing = next(member for member in stair.members
                           if member.child_key == landing_key)
            near_edge = landing.p0[along]  # this landing's edge toward its own flight
            treads = lower if flight == "lower" else upper
            # The riser face a walker steps up at to LEAVE this landing (upper) or to
            # ARRIVE on it (lower) is exactly one going from its near edge.
            adjacent = treads[-1] if flight == "lower" else treads[0]
            gap = abs(near_edge - adjacent.riser_line[0][along])
            # ...plus, arriving, the head riser's board (and its carpet), which stands past
            # its line against the landing edge (notes/stair_nosing_basis.md).
            board = stair.finish_thickness_m + 0.75 * 0.0254
            expected = going + board if flight == "lower" else 0.0
            assert gap == pytest.approx(expected, abs=1e-9), (stair.tag, flight)


