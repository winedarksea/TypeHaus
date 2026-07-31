"""The R311.7 stair checks measure built members, not authored intent.

``code.R311_7_stair_geometry`` once *reported* headroom by reading the arrival storey's
nominal ceiling height — 11' of "headroom" for a winder climbing into a roof. The checks
here each measure resolved output: plumb clearance sampled along the sloped nosing line
against floor/roof/soffit structure, flight width off the tread boards, landing depth off
the deck members. Each check gets a two-sided synthetic test (a geometry that passes AND
one that fails), so no rule can rot into always-pass or always-fail.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.checks import build_context
from typehaus.checks.code.mn_residential.rules import (
    stair_handrail,
    stair_headroom,
    stair_landing_depth,
    stair_width,
)
from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.resolve.model import FramedMember, ResolvedFloor, ResolvedStair
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"

_RISER = 0.19
_GOING = 0.254


@pytest.fixture(scope="module")
def catlin_ctx():
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    return ctx


def _tread(index: int, width_m: float = 1.0) -> FramedMember:
    y = _GOING * index
    centre = y + (_GOING - inch(1).meters) / 2.0
    top = _RISER * (index + 1)
    return FramedMember("S", f"tread-{index:03d}", "tread", "deck 11x1.5",
                        (0.0, centre), (width_m, centre), top - inch(1.5).meters, top,
                        width_m, riser_line=((0.0, y), (width_m, y)))


def _flight(tread_count: int = 4, width_m: float = 1.0) -> ResolvedStair:
    return ResolvedStair(uid="S", tag="S-STR", storey="main", to_storey="second",
                         outline=[], riser_count=tread_count + 1, riser_height_m=_RISER,
                         tread_depth_m=inch(11).meters, run_direction="y",
                         run_reversed=False, layout="straight", turn_direction=None,
                         winder_count=0,
                         members=tuple(_tread(i, width_m) for i in range(tread_count)),
                         going_depth_m=_GOING, nosing_depth_m=inch(1).meters)


def _deck_at(z: float) -> ResolvedFloor:
    return ResolvedFloor(uid="F", tag="F-DECK", storey="second", direction="x",
                         members=(), deck_outline=[(-5.0, -5.0), (5.0, -5.0),
                                                   (5.0, 5.0), (-5.0, 5.0)],
                         deck_voids=(), deck_z0_m=z, deck_z1_m=z + 0.018)


def _ctx(stair, floors=()):
    return SimpleNamespace(model=SimpleNamespace(stairs=[stair], floors=list(floors),
                                                 roofs=[], soffits=[]))


# ------------------------------------------------------------------- headroom
def test_headroom_passes_and_fails_on_the_measured_plumb_clearance():
    """The walk tops out at ~0.95 m (synthesized arrival station); a deck whose underside
    clears that by more than 6'-8" passes, one that pinches it fails — same flight."""
    tall = _ctx(_flight(), [_deck_at(3.5)])
    assert [f.result for f in stair_headroom(tall)] == [Result.PASS]
    low = _ctx(_flight(), [_deck_at(2.8)])
    findings = stair_headroom(low)
    assert [f.result for f in findings] == [Result.FAIL]
    assert "F-DECK" in findings[0].message  # names the obstructing element


def test_headroom_never_passes_by_absence():
    findings = stair_headroom(_ctx(_flight()))
    assert [f.result for f in findings] == [Result.UNKNOWN]


def test_headroom_ignores_structure_below_the_walk():
    """A deck under the flight (the floor it springs from) is not overhead."""
    findings = stair_headroom(_ctx(_flight(), [_deck_at(-0.5), _deck_at(3.5)]))
    assert [f.result for f in findings] == [Result.PASS]


def test_catlin_stair_headroom_is_measured_and_passes(catlin_ctx):
    findings = {f.message.split()[0]: f for f in stair_headroom(catlin_ctx)}
    assert set(findings) == {"ST-B2M", "ST-M2S", "ST-S2A"}
    for finding in findings.values():
        assert finding.result is Result.PASS, finding.message
        assert "plumb under" in finding.message  # a measurement, not a storey attribute
    # The winder's overhead constraint is the roof it climbs into, not a nominal ceiling.
    assert "RF-" in findings["ST-S2A"].message


# ---------------------------------------------------------------------- width
def test_width_measures_the_tread_boards():
    wide = _ctx(_flight(width_m=1.0))  # ~39.4"
    assert [f.result for f in stair_width(wide)] == [Result.PASS]
    narrow = _ctx(_flight(width_m=0.8))  # ~31.5"
    assert [f.result for f in stair_width(narrow)] == [Result.FAIL]


def test_catlin_stair_widths_pass_at_or_above_the_minimum(catlin_ctx):
    findings = stair_width(catlin_ctx)
    assert len(findings) == 3
    assert all(f.result is Result.PASS for f in findings)
    # ST-S2A rides the 36" limit exactly — the tolerance idiom is what keeps it passing.
    assert any("36.00" in f.message for f in findings)


# ------------------------------------------------------------------- landings
def _with_landing(depth_m: float) -> ResolvedStair:
    stair = _flight()
    landing = FramedMember("S", "landing-lower", "landing", "deck 42x1.5",
                           (0.5, 1.2), (0.5, 1.2 + depth_m), 0.9, 0.94, depth_m)
    return ResolvedStair(**{**stair.__dict__, "members": (*stair.members, landing)})


def test_landing_depth_measures_the_deck_member():
    deep = _ctx(_with_landing(1.0))
    assert [f.result for f in stair_landing_depth(deep)] == [Result.PASS]
    shallow = _ctx(_with_landing(0.8))  # ~31.5" in the direction of travel
    assert [f.result for f in stair_landing_depth(shallow)] == [Result.FAIL]


def test_catlin_landings_pass_both_axes(catlin_ctx):
    findings = stair_landing_depth(catlin_ctx)
    # Two U-stairs x two half-landings; the winder stair has no landing members.
    assert len(findings) == 4
    assert all(f.result is Result.PASS for f in findings)


# ------------------------------------------------------------------ handrails
def test_handrail_is_unknown_on_required_flights_not_silent(catlin_ctx):
    findings = stair_handrail(catlin_ctx)
    assert len(findings) == 3
    assert all(f.result is Result.UNKNOWN for f in findings)
    assert all("handrail" in f.message for f in findings)


def test_handrail_not_required_under_four_risers():
    stub = _flight(tread_count=2)  # 3 risers
    assert [f.result for f in stair_handrail(_ctx(stub))] == [Result.PASS]
