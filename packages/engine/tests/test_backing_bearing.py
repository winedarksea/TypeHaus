"""``advisory.wall_backing_bearing``: both ends of a band want something to nail to.

Geometry only, against the same minimal wall double ``test_backing_bands`` builds — the
check itself is a loop over walls and a message, and a hand-assembled ``CheckContext`` would
test the loop rather than the rule.

The defect this was written for is catlin's ``BK-G-W-RAIL-FOOT``: a 12" block in a 24" o.c.
bay, lapping one stud by 1/4" and floating 10 1/4" clear at its other end. It resolved, it
drew, and nothing said a word.
"""

from __future__ import annotations

import dataclasses

from test_backing_bands import _band, _wall_and_plan
from typehaus.checks.advisory.backing import floating_band_ends
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.framing.openings import WallOpening
from typehaus.resolve.framing.solver import frame_wall

# Studs land 16" o.c. on this fixture, so the bay between stud-001 and stud-002 runs face to
# face from 16 3/4" to 31 1/4" — 14 1/2" of clear bay.
BAY_START_IN = 16.75
BAY_LEN_IN = 14.5


def _floating(band, openings=()):
    plan, rw = _wall_and_plan()
    members = frame_wall(plan, rw, openings=list(openings), backing=(band,))
    return floating_band_ends(dataclasses.replace(rw, members=tuple(members)), [band])


def test_a_band_floating_in_the_bay_is_reported_at_both_ends():
    band = _band(start_m=inch(20).meters, length_m=inch(8).meters)
    found = _floating(band)
    assert len(found) == 2
    assert {tag for tag, _, _ in found} == {"BK-TEST"}
    # 20"-28" inside a 16 3/4"-31 1/4" bay: 3 1/4" clear at each end.
    assert sorted(round(gap / M_PER_IN, 2) for _, _, gap in found) == [3.25, 3.25]


def test_a_band_cut_to_fill_its_bay_is_silent():
    """Both ends butt a stud face, which is the fix the finding asks for."""
    band = _band(start_m=inch(BAY_START_IN).meters, length_m=inch(BAY_LEN_IN).meters)
    assert _floating(band) == []


def test_the_walls_own_ends_are_exempt():
    """Plates and the corner pack close them; without this every full-run band reports."""
    assert _floating(_band()) == []


def test_an_opening_break_lands_on_the_jack_and_is_not_floating():
    """The band stops at the rough opening, and the jack is standing right there."""
    opening = WallOpening(center_m=2.0, width_m=1.0, height_m=inch(60).meters,
                          sill_m=inch(24).meters, is_door=False)
    assert _floating(_band(), openings=(opening,)) == []


def test_a_wall_with_no_backing_has_nothing_to_grade():
    plan, rw = _wall_and_plan()
    members = frame_wall(plan, rw, openings=[])
    assert floating_band_ends(dataclasses.replace(rw, members=tuple(members)), []) == []


def test_the_finding_names_the_authored_tag_not_the_member_key():
    """Re-sorted with the emitter's own ``(elevation_m, tag)`` key, so an author can act."""
    low = _band(tag="BK-LOW", elevation_m=inch(20).meters,
                start_m=inch(20).meters, length_m=inch(8).meters)
    high = _band(tag="BK-HIGH", elevation_m=inch(60).meters,
                 start_m=inch(20).meters, length_m=inch(8).meters)
    plan, rw = _wall_and_plan()
    members = frame_wall(plan, rw, openings=[], backing=(low, high))
    found = floating_band_ends(dataclasses.replace(rw, members=tuple(members)), [high, low])
    assert {tag for tag, _, _ in found} == {"BK-LOW", "BK-HIGH"}
