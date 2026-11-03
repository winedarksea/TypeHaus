"""§10 of ``notes/mep_drain_routing_basis.md``: a 6" jog becomes a 45 pair; a 3" tie's pitch."""

from __future__ import annotations

import math

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_inlet_spacing import main_inlet_pitch_m
from typehaus.routing.compaction import compact_offsets

_JOG = [(0.0, 0.0, 0.0), (48.0, 0.0, 0.0), (48.0, 6.0, 0.0), (96.0, 6.0, 0.0)]


def _developed(points) -> float:
    return sum(math.dist(a[:2], b[:2]) for a, b in zip(points, points[1:], strict=False))


def test_a_six_inch_jog_becomes_a_45_pair_and_hands_back_three_and_a_half_inches() -> None:
    points = [tuple(v * M_PER_IN for v in p) for p in _JOG]
    out, made = compact_offsets(points, 18 * M_PER_IN, lambda _c, _i: True)
    assert made == 1
    assert [(round(x / M_PER_IN, 3), round(y / M_PER_IN, 3)) for x, y, _z in out] == [
        (0.0, 0.0), (45.0, 0.0), (51.0, 6.0), (96.0, 6.0)]
    assert _developed(out) / M_PER_IN == pytest.approx(98.485, abs=1e-3)
    assert (_developed(points) - _developed(out)) / M_PER_IN / 12 * 0.25 == pytest.approx(
        0.073, abs=1e-3)


def test_a_pair_that_fails_its_regrade_keeps_the_jog() -> None:
    points = [tuple(v * M_PER_IN for v in p) for p in _JOG]
    out, made = compact_offsets(points, 18 * M_PER_IN, lambda _c, _i: False)
    assert made == 0 and out == points


@pytest.mark.parametrize(("size_in", "pitch_in"),
                         [(1.5, 4.75), (2.0, 5.875), (3.0, 8.125), (4.0, 9.9375)])
def test_a_branch_keeps_the_tightest_catalogued_wye_pitch_from_any_inlet(
        size_in, pitch_in) -> None:
    assert main_inlet_pitch_m(size_in * M_PER_IN) / M_PER_IN == pytest.approx(pitch_in)


def test_a_turns_room_is_the_hub_od_nipple_and_a_hub_plus_tool_heel() -> None:
    """§10: 1 1/2" PVC, no published elbow body — nipple 2.190", heel 1.145"."""
    from typehaus.routing.cost import RouteCost
    from typehaus.routing.fitting_room import fitting_terms

    nipple, heel = fitting_terms(RouteCost(), "drain", 1.5 * M_PER_IN, "pvc",
                                 1.900 / 2 * M_PER_IN)
    assert nipple / M_PER_IN == pytest.approx(2.190, abs=1e-6)
    assert heel / M_PER_IN == pytest.approx(1.145, abs=1e-6)
