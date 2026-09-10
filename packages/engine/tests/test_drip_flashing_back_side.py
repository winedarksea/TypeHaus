"""``back_side`` on a drip flashing has to face the building, and nothing used to say so.

The field decides which end of the bent angle carries the turn-down, so inverting it points
the drip back behind the cladding — with no geometric consequence any other consumer
reports. The regression this pins is a real one: ``params/roof_trim.py`` derived the rake
corner returns' ``back_side`` with the eave runs' formula, but the returns travel along x
where the eaves travel along y, so all four came out inverted at 0 FAIL.
"""

from __future__ import annotations

from _helpers import check_context

from typehaus.checks.integrity.drip_flashing import _CHECK_ID, drip_flashing_back_side
from typehaus.findings import Result
from typehaus.model import (
    Building,
    Flashing,
    Library,
    PlanModel,
    Project,
    Site,
    Storey,
    TrimKind,
    inch,
    m,
    pt,
)

#: A 10m square loop walked counter-clockwise, so every run's LEFT normal points inboard.
_SIDE_M = 10.0
_CCW = (
    ("S", (0.0, 0.0), (_SIDE_M, 0.0)),
    ("E", (_SIDE_M, 0.0), (_SIDE_M, _SIDE_M)),
    ("N", (_SIDE_M, _SIDE_M), (0.0, _SIDE_M)),
    ("W", (0.0, _SIDE_M), (0.0, 0.0)),
)


def _loop_plan(back_sides: dict[str, str]) -> PlanModel:
    runs = tuple(
        Flashing(uid=f"drip-{side}", tag=f"TR-{side}", kind=TrimKind.DRIP_FLASHING,
                 path=(pt(m(p0[0]), m(p0[1])), pt(m(p1[0]), m(p1[1]))),
                 top_elevation=inch(0.0), depth=inch(1.5), thickness=inch(0.8),
                 back_side=back_sides[side])
        for side, p0, p1 in _CCW
    )
    return PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000044",
                        building=Building(name="test"),
                        site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(),
        elements={"main": runs},
    )


def _results(plan: PlanModel) -> dict[str, Result]:
    findings = drip_flashing_back_side(check_context(plan=plan))
    assert all(f.check_id == _CHECK_ID for f in findings)
    return {f.element_tags[0] if f.element_tags else "*": f.result for f in findings}


def test_a_counter_clockwise_loop_of_left_backed_runs_passes() -> None:
    """Walked CCW, every left-hand normal points inboard — the catlin garage stem case."""
    assert _results(_loop_plan(dict.fromkeys("SENW", "left"))) == {"*": Result.PASS}


def test_one_inverted_run_is_reported_and_the_other_three_are_not() -> None:
    sides = dict.fromkeys("SENW", "left")
    sides["N"] = "right"
    assert _results(_loop_plan(sides)) == {"TR-N": Result.FAIL}


def test_every_run_inverted_reports_every_run() -> None:
    """The rake-return bug's shape: one helper, one formula, all of its runs wrong."""
    results = _results(_loop_plan(dict.fromkeys("SENW", "right")))
    assert results == {f"TR-{side}": Result.FAIL for side in "SENW"}


def test_a_lone_run_cannot_be_judged_and_says_so() -> None:
    """No loop, no inside: the check reports UNKNOWN rather than guessing a side."""
    plan = _loop_plan(dict.fromkeys("SENW", "left"))
    only_south = plan.elements["main"][:1]
    assert _results(plan.model_copy(update={"elements": {"main": only_south}})) == {
        "TR-S": Result.UNKNOWN}
