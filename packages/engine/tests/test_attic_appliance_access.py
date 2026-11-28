"""``mep.attic_appliance_access`` - IMC 2018 306.3.

Catlin's numbers are the hand-worked ones in ``houses/catlin/notes/attic_appliance_access.md``.
The passage rule is pinned on a toy room, where a 22 in. gap is the whole question.
"""

from __future__ import annotations

from shapely.geometry import box

from typehaus.checks.mep.appliance_access import (
    CID,
    FT,
    IN,
    _route,
    attic_appliance_access,
)
from typehaus.findings import Result


def test_catlin_air_handler_passes_with_the_hand_numbers(catlin_ctx):
    (finding,) = [f for f in attic_appliance_access(catlin_ctx) if f.check_id == CID]
    assert finding.result is Result.PASS, finding.message
    assert finding.element_tags == ("EQ-S-HP1-AH", "RM-A-EAST-UNFIN")
    # Hand note section 6: 214.4 in. to the base, 84.05 in. of headroom at the service square.
    assert "17.9 ft" in finding.message
    assert "84.1 in high" in finding.message


def _toy(gap_m: float):
    """A 6 x 3 m room split by a baffle leaving ``gap_m`` open; the door is at the south."""
    room = box(0, 0, 6, 3)
    free = room.difference(box(2.9, 0, 3.1, 1.5 - gap_m / 2)).difference(
        box(2.9, 1.5 + gap_m / 2, 3.1, 3))
    square = box(4.5, 1.0, 5.5, 2.0)
    return room, free, [(square, (5.0, 1.5))]


def test_a_22_inch_gap_passes_and_a_20_inch_gap_does_not():
    room, free, squares = _toy(24 * IN)
    hit = _route(free, None, (0.5, -0.1), room, squares)
    assert hit is not None
    assert 4.0 < hit.length_m / FT < 20.0
    room, free, squares = _toy(20 * IN)
    assert _route(free, None, (0.5, -0.1), room, squares) is None
