"""Catlin's raceways hold NEC 358.26 between authored pull points, and every conditioned room
has a heating zone.

The pull points in ``plan/electrical.py`` are the accessible boxes (NEC 314.29), each at an
exposed station. A re-laid path shifts vertex indices, so a stale index shows up here as an
over-360° section before it shows up anywhere else.
"""

from __future__ import annotations

from _helpers import check_context

from typehaus.checks.mep.conduit_bends import conduit_bend_total
from typehaus.checks.mep.hvac import heating_capacity
from typehaus.findings import Result
from typehaus.resolve.conduit_pulls import MAX_BEND_DEG_BETWEEN_PULLS, pull_sections


def test_no_raceway_section_is_over_360_degrees(catlin_model_ro) -> None:
    over = [f.message for f in conduit_bend_total(check_context(model=catlin_model_ro))
            if f.message.startswith("ADVISORY — ")]
    assert not over, over


def test_each_authored_pull_point_is_graded(catlin_model_ro) -> None:
    """Every raceway that carries a box splits where the plan says, each section in limit.

    Keyed on the raceway's first run: the two attic runs chain off their basement risers.
    """
    expected = {"CD-B-KITCHEN": 3, "CD-B-DATA-MEDIA": 3, "CD-B-GARAGE": 2,
                "CD-M-DATA-PORCH": 2, "CD-B-ATTIC-RISER": 1, "CD-A-PV-EAST": 1,
                "CD-B-DATA-CHASE": 1, "CD-A-DATA-NE": 1}
    sections = pull_sections(list(catlin_model_ro.conduits))
    for tag, count in expected.items():
        mine = [s for s in sections if s.run_tags[0] == tag]
        assert len(mine) == count, (tag, [(s.starts_at, s.ends_at) for s in mine])
        assert all(s.gradable and s.total_deg <= MAX_BEND_DEG_BETWEEN_PULLS + 1e-6
                   for s in mine), (tag, [s.total_deg for s in mine])


def test_only_the_ess_closet_is_outside_a_heating_zone(catlin_model_ro) -> None:
    """RM-M-PANTRY is EQ-M-HP2-LIVING's; RM-B-ESS is unzoned on purpose (see
    ``test_heating_capacity.test_catlin_zone_loads_do_not_exceed_the_whole_house_load``)."""
    unclaimed = {tag for f in heating_capacity(check_context(model=catlin_model_ro))
                 if f.result is Result.UNKNOWN and "in no equipment zone_rooms" in f.message
                 for tag in f.element_tags}
    assert unclaimed == {"RM-B-ESS"}
