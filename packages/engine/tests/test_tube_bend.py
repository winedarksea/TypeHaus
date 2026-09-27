"""A PEX turn off a stock elbow angle is a BEND, graded against the maker's minimum radius.

Minn. R. 4714.0609 lets flexible tubing change direction without fittings per the
manufacturer's instructions; Uponor's is 6 x OD (``library/fittings.TUBE_BEND_RULES``). The
bend's tangent ``R tan(theta/2)`` has to fit on the straight tube either side of it.
"""

from __future__ import annotations

import math

from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_fittings import FAMILY_PIPE, polyline_fittings

_THREE_QUARTER = 0.75 * M_PER_IN


def _elbow(angle_deg: float, leg_in: float, material: str | None):
    """One interior turn of ``angle_deg`` in plan, between two legs of ``leg_in``."""
    leg = leg_in * M_PER_IN
    turn = math.radians(angle_deg)
    points = [(0.0, 0.0, 2.0), (leg, 0.0, 2.0),
              (leg + leg * math.cos(turn), leg * math.sin(turn), 2.0)]
    (record,) = polyline_fittings("PR-TEST", FAMILY_PIPE, "water_cold", points,
                                  _THREE_QUARTER, material=material)
    return record


def test_a_pex_bend_with_room_either_side_is_graded_as_a_bend() -> None:
    record = _elbow(60.0, 24.0, "pex")
    assert record.spec is not None and record.gap is None
    assert record.spec.tag == "BEND-PEX-0.75"
    assert math.isclose(record.spec.bend_radius_in, 6 * 0.875)  # 3/4" CTS OD


def test_a_pex_bend_short_of_its_tangent_is_refused_with_the_arithmetic() -> None:
    # 5.25" x tan(30 deg) = 3.03" of tube each side; 2" legs cannot hold it.
    record = _elbow(60.0, 2.0, "pex")
    assert record.spec is None
    assert "5.25\" radius" in record.gap and "lengthen the leg" in record.gap


def test_a_reversal_is_two_bends_never_one() -> None:
    record = _elbow(180.0, 24.0, "pex")
    assert record.spec is None and "reversal" in record.gap


def test_copper_publishes_no_bend_rule_and_stays_ungraded() -> None:
    record = _elbow(60.0, 24.0, "copper")
    assert record.spec is None and "BENT TUBE" in record.gap
