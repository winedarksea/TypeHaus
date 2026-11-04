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
from typehaus.model import inch
from typehaus.resolve.conduit_pulls import (
    CONDUIT_ENDPOINT_TOLERANCE_M,
    MAX_BEND_DEG_BETWEEN_PULLS,
    pull_sections,
    raceway_chains,
)
from typehaus.resolve.model import ResolvedConduitRun


def test_no_raceway_section_is_over_360_degrees(catlin_model_ro) -> None:
    over = [f.message for f in conduit_bend_total(check_context(model=catlin_model_ro))
            if f.message.startswith("ADVISORY — ")]
    assert not over, over


def test_each_authored_pull_point_is_graded(catlin_model_ro) -> None:
    """Every raceway that carries a box splits where the plan says, each section in limit.

    Keyed on the raceway's first run: the two attic runs chain off their basement risers.
    """
    expected = {"CD-B-KITCHEN": 3, "CD-B-DATA-MEDIA": 3, "CD-B-GARAGE": 2,
                "CD-M-DATA-PORCH": 2, "CD-B-ATTIC-RISER": 1, "CD-A-PV-EAST": 2,
                "CD-B-DATA-CHASE": 1, "CD-A-DATA-NE": 1}
    sections = pull_sections(list(catlin_model_ro.conduits))
    for tag, count in expected.items():
        mine = [s for s in sections if s.run_tags[0] == tag]
        assert len(mine) == count, (tag, [(s.starts_at, s.ends_at) for s in mine])
        assert all(s.gradable and s.total_deg <= MAX_BEND_DEG_BETWEEN_PULLS + 1e-6
                   for s in mine), (tag, [s.total_deg for s in mine])


def test_every_room_is_inside_a_heating_zone(catlin_model_ro) -> None:
    """RM-M-PANTRY is EQ-M-HP2-LIVING's and RM-B-ESS is EQ-B-HP2-GYM's, both for load only
    (see ``test_heating_capacity.test_catlin_zone_loads_do_not_exceed_the_whole_house_load``)."""
    unclaimed = {tag for f in heating_capacity(check_context(model=catlin_model_ro))
                 if f.result is Result.UNKNOWN and "in no equipment zone_rooms" in f.message
                 for tag in f.element_tags}
    assert unclaimed == set()


def _run(tag, start, end, z0=0.0, z1=0.0, **kw) -> ResolvedConduitRun:
    return ResolvedConduitRun(uid=tag, tag=tag, storey="main", path=(start, end),
                              trade_size_m=0.0254, z_start_m=z0, z_end_m=z1, length_m=1.0,
                              z_m=(z0, z1), **kw)


def test_chain_detection_is_exact_not_nearby() -> None:
    """End->start joints within 1/16" chain; a run 1/8" off, or 3" off, is its own raceway."""
    assert abs(CONDUIT_ENDPOINT_TOLERANCE_M - inch(1 / 16).meters) < 1e-12
    for gap_in, chained in ((0.0, True), (1 / 32, True), (1 / 8, False), (3.0, False)):
        runs = [_run("A", (0.0, 0.0), (1.0, 0.0)),
                _run("B", (1.0 + gap_in * 0.0254, 0.0), (1.0, 2.0))]
        assert (raceway_chains(runs) == [["A", "B"]]) is chained, gap_in
    # z counts too: the same plan point at another height is not a coupling.
    stacked = [_run("A", (0.0, 0.0), (1.0, 0.0)), _run("B", (1.0, 0.0), (1.0, 2.0), z0=0.0762)]
    assert raceway_chains(stacked) == [["A"], ["B"]]


def test_shared_boxes_and_branches_keep_their_rules() -> None:
    """Both runs naming the joint's element meet in a box; two runs leaving one point is a box."""
    boxed = [_run("A", (0.0, 0.0), (1.0, 0.0), to_ref="JB"),
             _run("B", (1.0, 0.0), (1.0, 2.0), from_ref="JB")]
    assert raceway_chains(boxed) == [["A"], ["B"]]
    branched = [_run("A", (0.0, 0.0), (1.0, 0.0)), _run("B", (1.0, 0.0), (1.0, 2.0)),
                _run("C", (1.0, 0.0), (3.0, 0.0))]
    assert raceway_chains(branched) == [["A"], ["B"], ["C"]]


def test_catlin_pv_riser_chains_to_the_attic_run_with_its_three_sections(catlin_model_ro) -> None:
    """The riser and CD-A-PV-EAST share one exact chase station; CD-B-PV-INV is not chained."""
    chains = raceway_chains(list(catlin_model_ro.conduits))
    assert ["CD-B-ATTIC-RISER", "CD-A-PV-EAST"] in chains and ["CD-B-PV-INV"] in chains
    sections = [s for s in pull_sections(list(catlin_model_ro.conduits))
                if s.run_tags[0] in ("CD-B-ATTIC-RISER", "CD-A-PV-EAST")]
    assert [round(s.total_deg) for s in sections] == [270, 90, 180]
