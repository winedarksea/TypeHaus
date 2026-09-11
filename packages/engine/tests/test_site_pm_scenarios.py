"""The scenarios PM phase 2 exists to make true, beside the 54 focused tests it kept.

Each of these is a sentence from the review, not a unit of a function. They are here in one
file because the failure they guard against is a *board* that lies, and every one of them
was a real state the surface could reach before this phase: 40 visits and nothing ready,
framing waiting on the driveway apron, a second inspection card overwriting the first, a
``verified`` written in the same request that cleared the last hold.
"""

from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

import pytest

from typehaus.checks.jurisdiction import InspectionSpec, JurisdictionProfile
from typehaus.cli.prices import ZERO
from typehaus.schedule.graph import find_cycles
from typehaus.schedule.inspection_state import (
    Attempt,
    InspectionEntry,
    InspectionsState,
    load_inspections,
    write_inspections,
)
from typehaus.schedule.locates import add_working_days, locate_dates, locate_state
from typehaus.schedule.readiness import make_ready
from typehaus.schedule.rules import validate
from typehaus.schedule.site_ops import SiteOpError, StaleRevision, apply_ops, site_revision
from typehaus.schedule.timing import visit_dates
from typehaus.takeoff.task_state import Calendar, TasksState, load_tasks
from typehaus.takeoff.tasks import WorkItem
from typehaus.takeoff.visit_state import (
    Checkpoint,
    VisitConstraint,
    VisitEntry,
    VisitsState,
)

_UUID = uuid.uuid5(uuid.NAMESPACE_DNS, "typehaus.test")
_ROOT = Path(__file__).resolve().parents[3]
CATLIN = _ROOT / "houses" / "catlin"


class _Plan:
    project = type("P", (), {"project_uuid": _UUID})()


class _Model:
    plan = _Plan()
    walls: list = []
    rooms: list = []
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
                       gates=("earth",), milestone="foundation"),
        InspectionSpec(id="footing", label="Footing", authority="building",
                       after=("erosion",), milestone="foundation"),
        # The catlin case, in miniature: a second gate on `earth` that stands AFTER the
        # first. Applying both to one implicit visit is the deadlock this phase removed.
        InspectionSpec(id="backfill", label="Backfill", authority="building",
                       after=("footing",), gates=("earth", "framing"),
                       milestone="foundation"),
    ),
)


def _item(trade, storey="building", rows=(("concrete", "footing"),),
          tags=("FT-B-E2",), depends_on=()):
    return WorkItem(id=f"id/{trade}/{storey}", slug=f"task/{trade}/{storey}", trade=trade,
                    storey=storey, cost_code="", rows=tuple(rows),
                    element_tags=tuple(tags), estimate=ZERO, depends_on=tuple(depends_on))


def _board(items, visits=None, entries=None, tasks=None):
    return make_ready(
        _Model(), items,
        tasks or TasksState(visits=VisitsState(entries=visits or {})),
        InspectionsState(entries=entries or {}), PROFILE, [])


# --- the graph -------------------------------------------------------------------------

def test_a_later_gate_on_the_same_trade_is_dropped_rather_than_deadlocking() -> None:
    """``backfill`` gates ``earth`` and stands after ``erosion``, which also gates it.

    Both applied to one undifferentiated earth package means excavation waits on the
    backfill inspection, which waits on the walls, which wait on the footings, which wait on
    excavation. The derivation terminated; the board was dead.
    """
    board = _board([_item("earth"), _item("framing")])
    earth = board.visit("task/earth/building")
    assert earth.depends_on == ("insp/erosion",)
    assert ("earth", "insp/backfill") in board.dropped_gates
    # The framing gate is a different trade and a real statement, so it survives.
    assert "insp/backfill" in board.visit("task/framing/building").depends_on


def test_a_late_visit_drops_out_of_package_level_expansion() -> None:
    """Framing's predecessor is the concrete PACKAGE, and flatwork is authored last."""
    visits = {
        "task/concrete/building/footings": VisitEntry(label="Footings"),
        "task/concrete/building/flatwork": VisitEntry(label="Apron",
                                                      blocks_successors=False),
    }
    board = _board([_item("concrete"), _item("framing", depends_on=("task/concrete/building",))],
                   visits=visits)
    depends = board.visit("task/framing/building").depends_on
    assert "task/concrete/building/footings" in depends
    assert "task/concrete/building/flatwork" not in depends


def test_a_hand_authored_cycle_is_reported_by_name() -> None:
    visits = {"task/concrete/building/a": VisitEntry(
                  depends_on=("task/concrete/building/b",)),
              "task/concrete/building/b": VisitEntry(
                  depends_on=("task/concrete/building/a",))}
    board = _board([_item("concrete")], visits=visits)
    assert board.errors, "a loop is an error, not a silently dropped edge"
    assert "task/concrete/building/a" in board.errors[0]
    assert "task/concrete/building/b" in board.errors[0]
    assert find_cycles(board.visits, board.inspections)


def test_a_standalone_visit_needs_no_package() -> None:
    board = _board([_item("concrete")],
                   visits={"site/building-permit": VisitEntry(
                       label="Permit", trade="earth", milestone="preconstruction")})
    visit = board.visit("site/building-permit")
    assert visit is not None and visit.standalone and visit.milestone == "preconstruction"


# --- checkpoints -----------------------------------------------------------------------

def _checkpointed():
    return {"task/concrete/building/footings": VisitEntry(
        checkpoints=(Checkpoint(id="forms", label="Forms"),
                     Checkpoint(id="pour", label="Pour", after=("insp/footing",)),
                     Checkpoint(id="strip", label="Strip", cure_days=3)))}


def test_the_pour_checkpoint_is_unreleased_until_its_inspection_passes() -> None:
    visits = _checkpointed()
    visits["task/concrete/building/walls"] = VisitEntry(
        depends_on=("task/concrete/building/footings#pour",))
    board = _board([_item("concrete")], visits=visits)
    walls = board.readiness["task/concrete/building/walls"]
    assert [c.label for c in walls.blockers] \
        == ["task/concrete/building/footings#pour done"]


def test_a_checkpointed_visit_derives_its_status_and_refuses_an_authored_one() -> None:
    entry = _checkpointed()["task/concrete/building/footings"]
    assert entry.derived_status == "todo"
    started = entry.__class__(checkpoints=(
        Checkpoint(id="forms", status="done"), Checkpoint(id="pour")))
    assert started.derived_status == "in_progress"
    done = entry.__class__(checkpoints=(Checkpoint(id="forms", status="done"),))
    assert done.derived_status == "done"
    with pytest.raises(ValueError, match="derived from the checkpoints"):
        from typehaus.takeoff.visit_state import parse_visit

        parse_visit("task/concrete/building/x",
                    {"status": "done", "checkpoints": [{"id": "forms"}]}, "where")


# --- partial passes --------------------------------------------------------------------

def test_a_partial_pass_releases_only_the_approved_tags() -> None:
    entries = {"footing": InspectionEntry(attempts=(
        Attempt(date="2027-05-08", result="partial", approved=("FT-B-*",)),))}
    visits = {"task/concrete/building/house": VisitEntry(
                  element_tags=("FT-B-*",), depends_on=("insp/footing",)),
              "task/concrete/building/court": VisitEntry(
                  element_tags=("FT-SG-*",), depends_on=("insp/footing",))}
    item = _item("concrete", tags=("FT-B-E2", "FT-SG-W1"))
    board = _board([item], visits=visits, entries=entries)
    assert not board.readiness["task/concrete/building/house"].blockers
    assert board.readiness["task/concrete/building/court"].blockers


def test_two_attempts_on_one_instance_keep_both() -> None:
    entry = InspectionEntry(attempts=(
        Attempt(date="2027-05-05", result="fail", corrections=("bolts off layout",)),
        Attempt(date="2027-05-12", result="pass")))
    assert len(entry.attempts) == 2
    assert entry.result == "pass"
    assert entry.attempts[0].corrections == ("bolts off layout",)


def test_a_second_instance_carries_its_own_booking() -> None:
    entries = {"footing": InspectionEntry(scheduled="2027-05-05"),
               "footing/court": InspectionEntry(scope=("FT-SG-*",),
                                                scheduled="2027-06-02")}
    board = _board([_item("concrete")], entries=entries)
    ids = [record.id for record in board.inspections]
    assert "footing" in ids and "footing/court" in ids
    court = board.inspection("footing/court")
    assert court is not None and court.entry["scheduled"] == "2027-06-02"


def test_a_bare_string_waiver_fails_validation(tmp_path: Path) -> None:
    (tmp_path / "inspections.toml").write_text(
        '[entries.footing]\nwaived = "DSI said so"\n')
    with pytest.raises(ValueError, match="who granted it"):
        load_inspections(tmp_path)


def test_a_bare_id_dependency_means_every_instance(tmp_path: Path) -> None:
    entries = {"footing": InspectionEntry(attempts=(Attempt("2027-05-05", "pass"),)),
               "footing/court": InspectionEntry(scope=("FT-SG-*",))}
    visits = {"task/concrete/building/walls": VisitEntry(depends_on=("insp/footing",))}
    board = _board([_item("concrete")], visits=visits, entries=entries)
    # One instance passed and the other has not, so the wall visit stays blocked.
    assert board.readiness["task/concrete/building/walls"].blockers


# --- verification ----------------------------------------------------------------------

def _verify_op(slug):
    return {"op": "set_visit", "slug": slug, "status": "verified"}


def test_verified_is_refused_while_a_hold_is_open(tmp_path: Path) -> None:
    from typehaus.takeoff.task_state import write_tasks

    slug = "task/concrete/building/footings"
    state = TasksState(visits=VisitsState(entries={slug: VisitEntry(
        constraints=(VisitConstraint(label="rebar delivered"),))}))
    write_tasks(tmp_path, state)
    with pytest.raises(SiteOpError, match="hold"):
        apply_ops(tmp_path, [_verify_op(slug)])


def test_one_request_may_not_both_clear_the_last_hold_and_verify(tmp_path: Path) -> None:
    """The owner claiming they walked work they were still unblocking as they typed."""
    from typehaus.takeoff.task_state import write_tasks

    slug = "task/concrete/building/footings"
    write_tasks(tmp_path, TasksState(visits=VisitsState(entries={slug: VisitEntry(
        constraints=(VisitConstraint(label="rebar delivered"),))})))
    with pytest.raises(SiteOpError, match="before this request"):
        apply_ops(tmp_path, [
            {"op": "clear_hold", "slug": slug, "label": "rebar delivered",
             "cleared": "2027-05-04"},
            _verify_op(slug)])
    # Two requests, in order, are fine — and that is the point: the refusal is about the
    # claim being made in one breath, not about the hold.
    apply_ops(tmp_path, [{"op": "clear_hold", "slug": slug, "label": "rebar delivered",
                          "cleared": "2027-05-04"}])
    apply_ops(tmp_path, [_verify_op(slug)])
    assert load_tasks(tmp_path).visits.entries[slug].status == "verified"


def test_done_under_an_open_hold_records_an_exception(tmp_path: Path) -> None:
    from typehaus.takeoff.task_state import write_tasks

    slug = "task/concrete/building/footings"
    write_tasks(tmp_path, TasksState(visits=VisitsState(entries={slug: VisitEntry(
        constraints=(VisitConstraint(label="rebar delivered"),))})))
    apply_ops(tmp_path, [
        {"op": "set_visit", "slug": slug, "status": "done"},
        {"op": "add_exception", "slug": slug, "hold": "rebar delivered",
         "note": "went ahead"}])
    entry = load_tasks(tmp_path).visits.entries[slug]
    assert entry.status == "done"
    assert entry.exceptions[0].hold == "rebar delivered"
    # The hold STAYS OPEN. An exception records what happened; it does not resolve it.
    assert entry.constraints[0].cleared is None


def test_validate_reports_a_verified_visit_with_an_unresolved_inspection() -> None:
    visits = {"task/concrete/building/walls": VisitEntry(
        status="verified", depends_on=("insp/footing",))}
    board = _board([_item("concrete")], visits=visits)
    errors, _warnings = validate(board, None)
    assert any("verified while insp/footing" in line for line in errors)


def test_validate_reports_two_visits_claiming_one_bom_row() -> None:
    visits = {"task/concrete/building/a": VisitEntry(rows=("concrete:footing",)),
              "task/concrete/building/b": VisitEntry(rows=("concrete:footing",))}
    board = _board([_item("concrete")], visits=visits)
    errors, _warnings = validate(board, None)
    assert any("counts it once per visit" in line for line in errors)
    # Both saying so out loud is the way to keep a deliberate overlap.
    shared = {slug: VisitEntry(rows=("concrete:footing",), shared_rows=True)
              for slug in visits}
    board = _board([_item("concrete")], visits=shared)
    errors, _warnings = validate(board, None)
    assert not errors


# --- timing ----------------------------------------------------------------------------

def _timed(**durations):
    visits = {slug: VisitEntry(duration_days=days, depends_on=deps)
              for slug, (days, deps) in durations.items()}
    return visits


def test_suggested_dates_respect_dependencies_and_cures() -> None:
    visits = {
        "task/concrete/building/footings": VisitEntry(
            duration_days=2,
            checkpoints=(Checkpoint(id="pour"), Checkpoint(id="strip", cure_days=3))),
        "task/concrete/building/walls": VisitEntry(
            duration_days=1, depends_on=("task/concrete/building/footings",)),
    }
    tasks = TasksState(visits=VisitsState(entries=visits))
    board = _board([_item("concrete")], tasks=tasks)
    dates = visit_dates(board, tasks, today=date(2027, 5, 3))   # a Monday
    footings = dates["task/concrete/building/footings"]
    assert footings.suggested_start == "2027-05-03"
    # Two working days, then three calendar days of cure.
    assert footings.suggested_finish == "2027-05-07"
    walls = dates["task/concrete/building/walls"]
    assert walls.suggested_start == "2027-05-10", "the next working day after the cure"


def test_a_visit_with_no_duration_reports_needs_confirmation() -> None:
    visits = {"task/concrete/building/footings": VisitEntry()}
    tasks = TasksState(visits=VisitsState(entries=visits))
    board = _board([_item("concrete")], tasks=tasks)
    record = visit_dates(board, tasks, today=date(2027, 5, 3))[
        "task/concrete/building/footings"]
    assert record.needs_confirmation
    assert "no duration_days" in record.why


def test_a_slipped_predecessor_threatens_a_booking_but_never_moves_it() -> None:
    from typehaus.takeoff.visit_state import Booking

    visits = {
        "task/concrete/building/footings": VisitEntry(duration_days=10),
        "task/concrete/building/walls": VisitEntry(
            duration_days=1, depends_on=("task/concrete/building/footings",),
            booked=Booking(date="2027-05-06")),
    }
    tasks = TasksState(visits=VisitsState(entries=visits))
    board = _board([_item("concrete")], tasks=tasks)
    walls = visit_dates(board, tasks, today=date(2027, 5, 3))["task/concrete/building/walls"]
    assert walls.booked == "2027-05-06", "the engine does not rebook a concrete truck"
    assert walls.threatened_by_days and walls.threatened_by_days > 0


def test_the_house_calendar_is_what_a_working_day_means() -> None:
    calendar = Calendar(workdays=(0, 1, 2, 3), holidays=("2027-05-04",))
    tasks = TasksState(visits=VisitsState(entries={
        "task/concrete/building/footings": VisitEntry(duration_days=2)}), calendar=calendar)
    board = _board([_item("concrete")], tasks=tasks)
    record = visit_dates(board, tasks, today=date(2027, 5, 3))[
        "task/concrete/building/footings"]
    # Monday is worked, Tuesday the 4th is a holiday, so day two is Wednesday.
    assert record.suggested_start == "2027-05-03"
    assert record.suggested_finish == "2027-05-05"


# --- locates ---------------------------------------------------------------------------

def test_a_locate_ticket_arms_after_48_working_hours_and_lapses_at_14_days() -> None:
    hold = VisitConstraint(label="locate", kind="locate", start="2027-05-06")  # a Thursday
    armed, expires, sentence = locate_dates(hold)
    # Two working days from Thursday is Monday: the weekend does not count.
    assert armed == "2027-05-10"
    assert expires == "2027-05-20"
    assert "216D.04" in sentence
    assert locate_state(hold, today=date(2027, 5, 7)) == "pending"
    assert locate_state(hold, today=date(2027, 5, 12)) == "armed"
    assert locate_state(hold, today=date(2027, 5, 18)) == "expiring"
    assert locate_state(hold, today=date(2027, 5, 25)) == "expired"


def test_a_refresh_agreement_buys_six_months_and_a_missing_start_derives_nothing() -> None:
    refreshed = VisitConstraint(label="locate", kind="locate", start="2027-05-06",
                                refresh_agreement=True)
    _armed, expires, _why = locate_dates(refreshed)
    assert expires == "2027-11-05"
    bare = VisitConstraint(label="locate", kind="locate")
    assert locate_dates(bare)[:2] == (None, None)
    assert locate_state(bare) == "needs_confirmation"
    assert add_working_days(date(2027, 5, 6), 2) == date(2027, 5, 10)


def test_an_expired_locate_blocks_its_visit_again() -> None:
    """The one hold on this board that can close on its own after it opened."""
    hold = VisitConstraint(label="locate", kind="locate", start="2020-01-02",
                           cleared="2020-01-06")
    board = _board([_item("earth")],
                   visits={"site/dig": VisitEntry(trade="earth", constraints=(hold,))})
    blockers = board.readiness["site/dig"].blockers
    assert blockers and "expired" in blockers[0].derived


# --- the write path --------------------------------------------------------------------

def test_a_stale_if_revision_is_refused_and_nothing_is_written(tmp_path: Path) -> None:
    from typehaus.takeoff.task_state import write_tasks

    slug = "task/concrete/building/footings"
    write_tasks(tmp_path, TasksState(visits=VisitsState(entries={slug: VisitEntry()})))
    first = site_revision(tmp_path)
    apply_ops(tmp_path, [{"op": "set_visit", "slug": slug, "note": "one"}],
              if_revision=first)
    before = (tmp_path / "tasks.toml").read_text()
    with pytest.raises(StaleRevision):
        apply_ops(tmp_path, [{"op": "set_visit", "slug": slug, "note": "two"}],
                  if_revision=first)
    assert (tmp_path / "tasks.toml").read_text() == before


def test_a_bad_op_in_a_batch_persists_nothing(tmp_path: Path) -> None:
    from typehaus.takeoff.task_state import write_tasks

    slug = "task/concrete/building/footings"
    write_tasks(tmp_path, TasksState(visits=VisitsState(entries={slug: VisitEntry()})))
    before = (tmp_path / "tasks.toml").read_text()
    with pytest.raises(SiteOpError):
        apply_ops(tmp_path, [{"op": "set_visit", "slug": slug, "note": "one"},
                             {"op": "set_visit", "slug": slug, "status": "nonsense"}])
    assert (tmp_path / "tasks.toml").read_text() == before


def test_an_interrupted_write_leaves_the_previous_file_intact(tmp_path: Path) -> None:
    """``os.replace`` is the whole mechanism: the temp file is what a crash loses."""
    import os

    from typehaus.takeoff.atomic import atomic_write_text

    target = tmp_path / "tasks.toml"
    target.write_text("original\n")
    real_replace = os.replace
    try:
        os.replace = lambda *_a, **_k: (_ for _ in ()).throw(OSError("crash"))
        with pytest.raises(OSError):
            atomic_write_text(target, "replacement\n")
    finally:
        os.replace = real_replace
    assert target.read_text() == "original\n"
    assert not list(tmp_path.glob(".tasks.toml.*.tmp")), "the temp file is cleaned up"


def test_a_skip_needs_a_reason(tmp_path: Path) -> None:
    from typehaus.takeoff.task_state import write_tasks

    slug = "task/concrete/building/footings"
    write_tasks(tmp_path, TasksState(visits=VisitsState(entries={slug: VisitEntry()})))
    with pytest.raises(SiteOpError, match="reason"):
        apply_ops(tmp_path, [{"op": "skip_handoff", "slug": slug, "item": "sleeves"}])
    apply_ops(tmp_path, [{"op": "skip_handoff", "slug": slug, "item": "sleeves",
                          "reason": "the next sub supplies them"}])
    assert load_tasks(tmp_path).visits.entries[slug].skipped[0].reason \
        == "the next sub supplies them"


def test_a_status_change_stamps_the_entry_and_appends_one_log_line(tmp_path: Path) -> None:
    from typehaus.takeoff.task_state import write_tasks

    slug = "task/concrete/building/footings"
    write_tasks(tmp_path, TasksState(visits=VisitsState(entries={slug: VisitEntry()})))
    apply_ops(tmp_path, [{"op": "set_visit", "slug": slug, "status": "in_progress"}])
    entry = load_tasks(tmp_path).visits.entries[slug]
    assert entry.updated, "there is no journal file; the stamp is in the TOML"
    assert [(line.from_, line.to) for line in entry.log] == [("todo", "in_progress")]


# --- migration -------------------------------------------------------------------------

def test_migrate_preserves_every_id_date_tick_and_note(tmp_path: Path) -> None:
    from typehaus.schedule.migrate import migrate

    (tmp_path / "inspections.toml").write_text(
        '[authorities.building]\nlabel = "DSI"\nphone = "651-266-9002"\n\n'
        '[entries.footing]\nrequested = "2027-05-04"\nresult = "partial"\n'
        'result_date = "2027-05-05"\ninspector = "J. Smith"\n'
        'reinspect = "2027-05-12"\nhistory = ["2027-05-05 fail bolts off layout"]\n'
        'checked = ["permit card posted"]\nnote = "court piers not ready"\n\n'
        '[[extra]]\nid = "girt_screws"\nlabel = "Girt screws"\nauthority = "owner"\n')
    changes, review = migrate(tmp_path, write=True)
    assert changes
    state = load_inspections(tmp_path)
    entry = state.entries["footing"]
    assert entry.requested == "2027-05-04"
    assert entry.checked == ("permit card posted",)
    assert entry.note == "court piers not ready"
    assert entry.scheduled == "2027-05-12", "reinspect became the next appointment"
    # `partial` is preserved as `partial`; it used to collapse to `failed`.
    assert [a.result for a in entry.attempts] == ["fail", "partial"]
    assert state.authorities["building"].phone == "651-266-9002"
    assert [x.id for x in state.extra] == ["girt_screws"]
    assert not review


def test_migrate_never_promotes_done_to_verified(tmp_path: Path) -> None:
    from typehaus.schedule.migrate import migrate
    from typehaus.takeoff.task_state import TaskEntry, write_tasks

    slug = "task/concrete/building"
    write_tasks(tmp_path, TasksState(
        entries={slug: TaskEntry(status="done")},
        visits=VisitsState(entries={f"{slug}/footings": VisitEntry(status="todo")})))
    _changes, review = migrate(tmp_path, write=False)
    assert any("only you know" in line for line in review)
    assert load_tasks(tmp_path).entries[slug].status == "done"


# --- the reference house ---------------------------------------------------------------

@pytest.mark.skipif(not CATLIN.exists(), reason="the reference house is not in this tree")
def test_catlin_has_a_ready_visit_and_a_reachable_excavation() -> None:
    """The headline: 40 visits, 40 blocked, 0 ready was the state this phase started in."""
    from typehaus.cli.cmd_schedule import _board as board_of

    _model, board, _items = board_of(CATLIN)
    ready = [slug for slug, record in board.readiness.items() if record.state == "ready"]
    assert ready, "a board where nothing is ready is a board nobody can use"

    # Excavation waits on the erosion inspection and on nothing that follows it.
    earth = board.visit("task/earth/basement")
    assert earth is not None
    assert "insp/foundation_backfill" not in earth.depends_on

    # And framing does not wait on the driveway apron, which is poured after they leave.
    framing = board.visit("task/framing/building")
    assert framing is not None
    assert "task/concrete/building/flatwork" not in framing.depends_on


@pytest.mark.skipif(not CATLIN.exists(), reason="the reference house is not in this tree")
def test_catlin_site_state_validates_clean() -> None:
    from typehaus.cli.cmd_schedule import _board as board_of

    model, board, _items = board_of(CATLIN)
    errors, _warnings = validate(board, model)
    assert errors == [], "the reference house is held to a clean site-state report"


@pytest.mark.skipif(not CATLIN.exists(), reason="the reference house is not in this tree")
def test_catlin_authorities_are_saint_pauls_own() -> None:
    """Minn. Stat. 326B.36 subd. 1 and 6: the city runs its own three inspections."""
    state = load_inspections(CATLIN)
    assert state.authorities["electrical"].phone == "651-266-9003"
    assert state.authorities["mechanical"].phone == "651-266-9004"
    assert state.permit.code_edition == "mn-2020"
    assert state.permit.nec_edition == "2026"


def test_write_inspections_round_trips_an_instance_and_its_attempts(tmp_path: Path) -> None:
    state = InspectionsState(entries={
        "footing": InspectionEntry(attempts=(Attempt("2027-05-05", "pass"),)),
        "footing/court": InspectionEntry(
            scope=("FT-SG-*",),
            attempts=(Attempt("2027-06-02", "partial", approved=("FT-SG-W*",)),)),
    })
    write_inspections(tmp_path, state)
    assert load_inspections(tmp_path) == state
