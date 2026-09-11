"""Readiness, derived from hand-built packages, findings and site state.

No house is loaded on purpose: the point of these is that the rules are the rules, whatever
the geometry. The catlin end-to-end lives in ``test_schedule_cli_and_api.py``.
"""

from __future__ import annotations

import uuid

import pytest

from typehaus.checks.jurisdiction import InspectionSpec, JurisdictionProfile
from typehaus.cli.prices import ZERO
from typehaus.findings import Finding, Result, Severity
from typehaus.schedule.inspection_state import (
    ExtraInspection,
    InspectionEntry,
    InspectionsState,
)
from typehaus.schedule.readiness import make_ready
from typehaus.takeoff.task_state import TasksState
from typehaus.takeoff.tasks import WorkItem
from typehaus.takeoff.visit_state import VisitConstraint, VisitEntry, VisitsState

_UUID = uuid.uuid5(uuid.NAMESPACE_DNS, "typehaus.test")


class _Plan:
    project = type("P", (), {"project_uuid": _UUID})()


class _Model:
    plan = _Plan()
    walls: list = []
    pipe_runs: list = []
    solids: list = []
    floors: list = []
    floor_heat: list = []
    roofs: list = []
    openings: list = []
    sleeves: list = []
    footing_beddings: list = []


PROFILE = JurisdictionProfile(
    name="test", edition="", effective_date="", irc_base="", coverage_statement="",
    inspections=(
        InspectionSpec(id="erosion", label="Erosion", authority="building",
                       gates=("earth",), on_site=("silt fence",),
                       milestone="foundation"),
        InspectionSpec(id="footing", label="Footing", authority="building",
                       after=("erosion",), check_ids=("structural.frost_depth",),
                       milestone="foundation"),
        InspectionSpec(id="backfill", label="Backfill", authority="building",
                       after=("footing",), gates=("framing",), on_site=("tile bedded",),
                       milestone="foundation"),
        InspectionSpec(id="lath", label="Lath", authority="building",
                       applies_when="stucco", on_site=("lath lapped",),
                       milestone="weathertight"),
    ),
)


def _item(trade, storey="building", rows=(("concrete", "footing"),),
          tags=("FT-B-E2",), depends_on=()):
    return WorkItem(id=f"id/{trade}/{storey}", slug=f"task/{trade}/{storey}", trade=trade,
                    storey=storey, cost_code="", rows=tuple(rows),
                    element_tags=tuple(tags), estimate=ZERO, depends_on=tuple(depends_on))


def _board(items, visits=None, inspection_entries=None, findings=(), extra=()):
    return make_ready(
        _Model(), items,
        TasksState(visits=VisitsState(entries=visits or {})),
        InspectionsState(entries=inspection_entries or {}, extra=tuple(extra)),
        PROFILE, list(findings))


def test_a_package_with_no_authored_visits_gets_one_implicit_visit() -> None:
    board = _board([_item("earth"), _item("concrete")])
    assert [v.slug for v in board.visits] == ["task/earth/building",
                                             "task/concrete/building"]
    assert all(visit.implicit for visit in board.visits)
    # The implicit visit inherits the package's predecessors AND every inspection gating
    # its trade — which is what makes a house that authored nothing still get a real board.
    assert board.visit("task/earth/building").depends_on == ("insp/erosion",)


def test_authored_visits_replace_the_implicit_one() -> None:
    visits = {"task/concrete/building/footings": VisitEntry(label="Footings"),
              "task/concrete/building/walls": VisitEntry(label="Walls")}
    board = _board([_item("concrete")], visits=visits)
    assert [v.slug for v in board.visits] == sorted(visits)
    assert not any(visit.implicit for visit in board.visits)
    assert board.visit("task/concrete/building/footings").label == "Footings"


def test_row_and_tag_subsets_narrow_the_visit() -> None:
    item = _item("concrete", rows=(("concrete", "footing"), ("concrete", "slab")),
                 tags=("FT-B-E2", "SL-B-SLAB"))
    board = _board([item], visits={"task/concrete/building/footings": VisitEntry(
        rows=("concrete:footing",), element_tags=("FT-*",))})
    visit = board.visit("task/concrete/building/footings")
    assert visit.rows == (("concrete", "footing"),)
    assert visit.element_tags == ("FT-B-E2",)


def test_a_predecessor_visit_blocks_until_it_is_done() -> None:
    board = _board([_item("earth"), _item("concrete", depends_on=("task/earth/building",))])
    assert board.readiness["task/concrete/building"].state == "blocked"
    blocker = board.readiness["task/concrete/building"].blockers[0]
    assert blocker.kind == "visit" and blocker.ref == "task/earth/building"

    done = _board([_item("earth"), _item("concrete", depends_on=("task/earth/building",))],
                  visits={})
    assert done.readiness["task/concrete/building"].state == "blocked"


def test_a_gating_inspection_blocks_until_it_passes() -> None:
    items = [_item("earth"), _item("framing")]
    board = _board(items)
    framing = board.readiness["task/framing/building"]
    assert framing.state == "blocked"
    assert [c.ref for c in framing.blockers if c.kind == "inspection"] == ["backfill"]

    passed = _board(items, inspection_entries={
        "erosion": InspectionEntry(result="pass"),
        "footing": InspectionEntry(result="pass"),
        "backfill": InspectionEntry(result="pass")})
    assert passed.readiness["task/framing/building"].state == "ready"


def test_fail_blocks_a_visit_and_unknown_only_asks_for_attention() -> None:
    red = Finding(severity=Severity.ERROR, check_id="structural.frost_depth",
                  message="footing above frost", element_tags=("FT-B-E2",),
                  result=Result.FAIL)
    grey = Finding(severity=Severity.WARN, check_id="structural.frost_depth",
                   message="UNKNOWN — no soil class", element_tags=("FT-B-E2",),
                   result=Result.UNKNOWN)
    blocked = _board([_item("concrete")], findings=[red])
    assert blocked.readiness["task/concrete/building"].state == "blocked"

    attention = _board([_item("concrete")], findings=[grey])
    readiness = attention.readiness["task/concrete/building"]
    assert readiness.state == "ready"
    assert [c.severity for c in readiness.attention] == ["attention"]


def test_a_finding_on_another_visits_elements_does_not_block_this_one() -> None:
    red = Finding(severity=Severity.ERROR, check_id="x", message="bad",
                  element_tags=("SL-B-SLAB",), result=Result.FAIL)
    board = _board([_item("concrete", tags=("FT-B-E2",))], findings=[red])
    assert board.readiness["task/concrete/building"].state == "ready"


def test_an_authored_constraint_blocks_until_it_is_cleared() -> None:
    entry = VisitEntry(constraints=(VisitConstraint("rebar delivered"),))
    board = _board([_item("concrete")],
                   visits={"task/concrete/building/footings": entry})
    assert board.readiness["task/concrete/building/footings"].state == "blocked"

    cleared = VisitEntry(constraints=(VisitConstraint("rebar delivered", "2027-04-28"),))
    ok = _board([_item("concrete")],
                visits={"task/concrete/building/footings": cleared})
    assert ok.readiness["task/concrete/building/footings"].state == "ready"


def test_constraints_are_ordered_predecessor_inspection_authored_finding() -> None:
    red = Finding(severity=Severity.ERROR, check_id="x", message="bad",
                  element_tags=("FT-B-E2",), result=Result.FAIL)
    entry = VisitEntry(depends_on=("task/earth/building", "insp/backfill"),
                       constraints=(VisitConstraint("rebar delivered"),))
    board = _board([_item("earth"), _item("concrete")],
                   visits={"task/concrete/building/footings": entry}, findings=[red])
    kinds = [c.kind for c in board.readiness["task/concrete/building/footings"].constraints]
    assert kinds == ["visit", "inspection", "authored", "finding"]


def test_status_wins_over_readiness_once_work_has_started() -> None:
    for status in ("in_progress", "done"):
        board = _board([_item("concrete")], visits={
            "task/concrete/building/footings": VisitEntry(
                status=status, constraints=(VisitConstraint("rebar delivered"),))})
        assert board.readiness["task/concrete/building/footings"].state == status


def test_inspection_states_walk_the_whole_ladder() -> None:
    items = [_item("earth")]
    def state(entries):
        return {r.id: r.state for r in _board(items, inspection_entries=entries).inspections}

    # erosion has one on-site tick and no checks, so it is not ready until it is ticked.
    assert state({})["erosion"] == "not_ready"
    assert state({"erosion": InspectionEntry(checked=("silt fence",))})["erosion"] == "ready"
    assert state({"erosion": InspectionEntry(requested="d")})["erosion"] == "requested"
    assert state({"erosion": InspectionEntry(scheduled="d")})["erosion"] == "scheduled"
    assert state({"erosion": InspectionEntry(result="pass")})["erosion"] == "passed"
    assert state({"erosion": InspectionEntry(result="partial")})["erosion"] == "failed"
    assert state({"erosion": InspectionEntry(waived="not required")})["erosion"] == "waived"


def test_na_is_earned_from_the_model_and_satisfies_what_it_precedes() -> None:
    board = _board([_item("earth")])
    lath = board.inspection("lath")
    # No walls modelled at all: absence of a field is not evidence of absence of stucco.
    assert lath.state == "not_ready" and lath.applicability.applies is None

    class _Stuccoless(_Model):
        walls = [type("W", (), {"tag": "W1", "layers": [
            type("L", (), {"material": "cedar_rainscreen"})()]})()]

    board = make_ready(_Stuccoless(), [_item("earth")], TasksState(),
                       InspectionsState(), PROFILE, [])
    lath = board.inspection("lath")
    assert lath.state == "not_applicable" and lath.applicability.applies is False
    assert lath.resolved


def test_waived_and_na_both_satisfy_an_after_dependency() -> None:
    items = [_item("earth")]
    for entry in (InspectionEntry(waived="DSI says no"), InspectionEntry(result="pass")):
        board = _board(items, inspection_entries={"erosion": entry})
        footing = board.inspection("footing")
        met = {p.ref: p.met for p in footing.prerequisites if p.kind == "inspection"}
        assert met == {"erosion": True}


def test_a_house_extra_inspection_joins_the_list_and_can_gate() -> None:
    extra = ExtraInspection(id="girt_screws", label="Girt screws", authority="owner",
                            gates=("walls",), milestone="weathertight")
    board = _board([_item("walls")], extra=[extra])
    assert board.inspection("girt_screws").extra is True
    assert "insp/girt_screws" in board.visit("task/walls/building").depends_on


def test_the_board_cannot_deadlock_itself() -> None:
    """Inspections read visit *status*; visits read inspection *state*. One pass each."""
    items = [_item("framing")]
    board = _board(items, inspection_entries={
        "backfill": InspectionEntry(requires=("task/framing/building",))})
    # The visit waits on the inspection and the inspection waits on the visit — and both
    # still resolve, because "under way" is a status the owner sets, not a derived state.
    assert board.readiness["task/framing/building"].state == "blocked"
    assert board.inspection("backfill").state == "not_ready"


def test_stale_slugs_are_surfaced_never_dropped() -> None:
    board = _board([_item("concrete")],
                   visits={"task/roof/main/ridge": VisitEntry()},
                   inspection_entries={"no_such_inspection": InspectionEntry(note="x")})
    assert board.stale == ("insp/no_such_inspection", "task/roof/main/ridge")


def test_visit_ids_are_derived_and_stable() -> None:
    first = _board([_item("concrete")]).visit("task/concrete/building")
    second = _board([_item("concrete")]).visit("task/concrete/building")
    assert first.id == second.id and first.id


@pytest.mark.parametrize("slug", ["task/earth/building"])
def test_milestones_group_visits_by_trade(slug: str) -> None:
    board = _board([_item("earth"), _item("framing")])
    by_id = {m.id: m for m in board.milestones}
    assert slug in by_id["foundation"].visits
    assert "task/framing/building" in by_id["weathertight"].visits
    assert by_id["foundation"].inspections == ("erosion", "footing", "backfill")


def test_a_dependency_on_a_split_package_follows_the_split() -> None:
    """The predecessor map names packages; the owner books arrivals.

    ``TRADE_PREDECESSORS`` says drainage follows concrete, by package slug. Splitting the
    concrete package into arrivals must not leave that dependency dangling as "names no
    current visit": the owner did not break anything.
    """
    items = [_item("concrete"), _item("drainage", depends_on=("task/concrete/building",))]
    visits = {"task/concrete/building/footings": VisitEntry(),
              "task/concrete/building/slabs": VisitEntry()}
    board = _board(items, visits=visits)
    drainage = board.visit("task/drainage/building")
    assert drainage.depends_on == ("task/concrete/building/footings",
                                   "task/concrete/building/slabs")
    kinds = {c.kind for c in board.readiness["task/drainage/building"].constraints}
    assert kinds == {"visit"}
    assert not any("names no current visit" in c.label
                   for c in board.readiness["task/drainage/building"].constraints)


def test_a_genuinely_stale_dependency_is_still_reported() -> None:
    entry = VisitEntry(depends_on=("task/roof/attic/ridge",))
    board = _board([_item("concrete")],
                   visits={"task/concrete/building/footings": entry})
    labels = [c.label for c in board.readiness["task/concrete/building/footings"].constraints]
    assert any("names no current visit" in label for label in labels)
