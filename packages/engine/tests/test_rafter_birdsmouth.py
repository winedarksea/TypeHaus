"""``structural.ijoist_birdsmouth``: TJ-4000's low-end seat, graded off the rafter's own solid.

The FAIL-before case is catlin's pre-#109 eave: a 3 1/2" seat at 6:12 cuts 1.75" plumb, and the
C3-E5 probe read the drawn heel as 1.47" — both deeper than a TJI 230 flange's 1.40".
"""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from typehaus.checks.structural._rafter_seat import ijoist_seat
from typehaus.quantities import inch
from typehaus.resolve.model import FramedMember, SeatCut

_SLOPE = 0.5
_DEPTH = inch(11.875).meters


def _rafter(notch_in: float, plate_in: float = 5.5, high_end: bool = False) -> FramedMember:
    """A TJI 230 bearing at p0 on a plate whose top is z=0, its heel cut ``notch_in`` deep."""
    notch = inch(notch_in).meters
    slope = -_SLOPE if high_end else _SLOPE
    plumb = _DEPTH * math.hypot(1.0, _SLOPE)
    return FramedMember(
        "ROOF", "rafter-000", "rafter", "11.875 TJI 230", (0.0, 0.0), (4.0, 0.0),
        -notch, -notch + plumb, 4.0, z0_end_m=-notch + slope * 4.0,
        z1_end_m=-notch + plumb + slope * 4.0,
        seat=SeatCut(plate_top_z_m=0.0, heel=(0.0, 0.0), seat_run_m=notch / _SLOPE,
                     bearing_run_m=inch(plate_in).meters))


@pytest.mark.parametrize(("notch_in", "plate_in", "high_end", "stiffened", "expect"), [
    (1.25, 5.5, False, True, None),  # catlin since #109: 2 1/2" seat
    (1.75, 5.5, False, True, "deeper than the bottom flange"),  # the pre-#109 3 1/2" seat
    (1.47, 5.5, False, True, "deeper than the bottom flange"),  # C3-E5's probe reading
    (1.25, 2.0, False, True, "overhanging the plate's inside face"),
    (0.75, 5.5, False, True, "under 1 3/4"),
    (1.25, 5.5, True, True, "HIGH end"),
    (1.25, 5.5, False, False, "no beveled web stiffener"),
])
def test_ijoist_seat(notch_in, plate_in, high_end, stiffened, expect):
    seat = ijoist_seat(_rafter(notch_in, plate_in, high_end), stiffened)
    assert seat.flange_plumb_m == pytest.approx(inch(1.25 * math.hypot(1.0, _SLOPE)).meters)
    if expect is None:
        assert seat.problems == ()
        assert seat.seat_m == pytest.approx(inch(2.5).meters)
    else:
        assert any(expect in problem for problem in seat.problems), seat.problems


def test_sawn_rafter_is_not_graded():
    assert ijoist_seat(replace(_rafter(1.25), profile="2x12"), True) is None
