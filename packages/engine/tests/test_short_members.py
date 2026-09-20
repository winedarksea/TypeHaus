"""The member-level short-framing finding, and the garage track-jamb legs it sits beside.

``integrity.wall_shorter_than_plates`` grades a WALL; these tests pin the piece. Catlin's
raked attic walls frame legal plates at their tall end and 1 1/4" studs at their short
one — a defect no wall-level finding can reach, because the wall is 62" tall.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import inch
from typehaus.resolve.framing.short_members import (
    MIN_STUD_LINE_IN,
    short_member_findings,
)
from typehaus.resolve.model import FramedMember


def _vertical(category: str, length_in: float, key: str = "stud-000") -> FramedMember:
    z1 = inch(length_in).meters
    return FramedMember("W1", key, category, "2x4", (1.0, 2.0), (1.0, 2.0), 0.0, z1, z1,
                        orient=(1.0, 0.0))


def _horizontal(category: str, length_in: float) -> FramedMember:
    span = inch(length_in).meters
    return FramedMember("W1", f"{category}-0", category, "2x4", (0.0, 0.0), (span, 0.0),
                        0.0, inch(1.5).meters, span)


def test_a_stud_shorter_than_its_plates_is_reported_by_name():
    findings = short_member_findings("W-A-STU-N", (_vertical("stud", 1.25),))
    assert [f.check_id for f in findings] == ["integrity.member_shorter_than_minimum"]
    assert findings[0].result.name == "UNKNOWN"
    assert findings[0].severity.name == "WARN"
    # The point of a MEMBER-level finding is that it names the member.
    assert "stud-000" in findings[0].message
    assert "W-A-STU-N" in findings[0].message
    assert "blocking" in findings[0].fix_hint


def test_each_short_member_gets_its_own_finding():
    members = (_vertical("stud", 1.25, "stud-000"), _vertical("cripple", 2.125, "c-01"),
               _vertical("stud", 92.25, "stud-001"))
    findings = short_member_findings("W-X", members)
    assert len(findings) == 2
    assert {"stud-000", "c-01"} == {k for f in findings for k in ("stud-000", "c-01")
                                    if k in f.message}


def test_the_threshold_is_the_two_plate_thicknesses_and_a_member_at_it_passes():
    """An ordinary 3" head cripple (catlin's W-B-CE) is real framing; 2 1/8" is not."""
    assert MIN_STUD_LINE_IN == 3.0
    assert short_member_findings("W-B-CE", (_vertical("cripple", 3.0),)) == []
    assert short_member_findings("W-A-SN", (_vertical("cripple", 2.125),))


@pytest.mark.parametrize("category", ["stud", "king", "jack", "cripple"])
def test_every_stud_line_category_is_graded(category):
    assert short_member_findings("W-X", (_vertical(category, 1.0),))


def test_a_board_laid_along_the_wall_is_not_graded():
    """A plate, a header, a sill and a rim carry a SPAN, not a stack height — a 2" header
    over a 2" opening is not a short stud, and a plate returning 1 1/2" at a corner is the
    normal answer."""
    for category in ("plate", "header", "sill", "rim", "blocking"):
        assert short_member_findings("W-X", (_horizontal(category, 2.0),)) == []
    # Even a stud-line category is skipped when it is laid down rather than stood up.
    assert short_member_findings("W-X", (_horizontal("cripple", 2.0),)) == []


def test_catlin_reports_its_four_offcuts_and_no_more(catlin_model):
    """The live house: three 1 1/4"-class studs in the raked attic walls plus one 2 1/8"
    head cripple. Every one of them is a real offcut nobody can nail."""
    reported = {}
    for wall in catlin_model.walls:
        for finding in short_member_findings(wall.tag, wall.members):
            reported[finding.message.split()[1]] = wall.tag
    assert sorted(reported.items()) == [
        ("cripple-head-0-02", "W-A-SN"),
        ("stud-000", "W-A-STU-N"),
        ("stud-004", "W-A-SN-EAST"),
        ("stud-005", "W-A-GC-S"),
    ]


def test_the_garage_track_jamb_legs_bear_on_the_slab_not_on_a_removed_plate(catlin_model):
    """``sole_plate_breaks`` takes the plate away under an overhead door's rough opening;
    bottoming the legs on ``z0`` left them 23 1/2" in the air. They start at the opening's
    own sill instead (fixed 2026-09-15, ``openings._append_track_jamb_legs``)."""
    wall = next(w for w in catlin_model.walls if w.tag == "W-G-N")
    legs = sorted((m for m in wall.members if m.child_key.startswith("trackjamb-")),
                  key=lambda m: m.child_key)
    assert [m.child_key for m in legs] == ["trackjamb-0-l", "trackjamb-0-r"]
    plate_top = max(m.z1_m for m in wall.members
                    if m.child_key.startswith("plate-bottom"))
    for leg in legs:
        assert leg.z0_m < plate_top - inch(12).meters, "a leg bearing on the plate top"
        assert leg.length_m == pytest.approx(leg.z1_m - leg.z0_m)
    # And they are long enough that the member-level finding has nothing to say.
    assert short_member_findings("W-G-N", tuple(legs)) == []
