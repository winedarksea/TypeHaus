"""``[visits]`` round-trips, and the one rule the writer enforces.

The old ``[entries]`` half must keep round-tripping byte-identically — a house that has
authored no visits cannot notice this feature exists.
"""

from __future__ import annotations

import pytest

from typehaus.takeoff.task_state import (
    apply_task_op,
    apply_visit_ops,
    load_tasks,
    write_tasks,
)
from typehaus.takeoff.visit_state import VisitsState, apply_visit_op, package_of

_SAMPLE = '''
[entries."task/concrete/building"]
status = "in_progress"
assignee = "Nordic Concrete"

[visits."task/concrete/building/footings"]
label = "House + court footings"
status = "scheduled"
scheduled = "2027-05-04"
rows = ["concrete:footing"]
element_tags = ["FT-B-*", "FT-SG-*"]
depends_on = ["task/earth/basement", "insp/erosion"]
checked = ["sleeves:SL-B-SLAB"]
constraints = [
  { label = "rebar cages delivered", cleared = "2027-04-28" },
  { label = "P/E/M on site during forming" },
]
'''


def _house(tmp_path, text=_SAMPLE):
    (tmp_path / "tasks.toml").write_text(text)
    return tmp_path


def test_loads_both_halves(tmp_path) -> None:
    state = load_tasks(_house(tmp_path))
    assert state.entries["task/concrete/building"].assignee == "Nordic Concrete"
    visit = state.visits.entries["task/concrete/building/footings"]
    assert visit.status == "scheduled"
    assert visit.rows == ("concrete:footing",)
    assert visit.element_tags == ("FT-B-*", "FT-SG-*")
    assert visit.constraints[0].cleared == "2027-04-28"
    assert visit.constraints[1].cleared is None


def test_round_trips(tmp_path) -> None:
    directory = _house(tmp_path)
    first = load_tasks(directory)
    write_tasks(directory, first)
    second = load_tasks(directory)
    assert second == first
    write_tasks(directory, second)
    assert load_tasks(directory) == second


def test_entries_only_file_round_trips_unchanged(tmp_path) -> None:
    """A house with no visits must not grow a ``[visits]`` section it never asked for."""
    directory = _house(tmp_path, '[entries."task/framing/main"]\nstatus = "done"\n')
    write_tasks(directory, load_tasks(directory))
    text = (directory / "tasks.toml").read_text()
    assert not any(line.startswith("[visits.") for line in text.splitlines())
    assert 'status = "done"' in text


def test_package_of() -> None:
    assert package_of("task/concrete/building/footings") == "task/concrete/building"
    # A package slug maps to itself, which is what lets the implicit visit share a code path
    # with an authored one covering the whole package.
    assert package_of("task/concrete/building") == "task/concrete/building"


def test_a_visit_slug_must_extend_a_package_slug(tmp_path) -> None:
    with pytest.raises(ValueError, match="names a package"):
        load_tasks(_house(tmp_path, '[visits."task/concrete/building"]\nlabel = "x"\n'))


def test_unknown_status_raises(tmp_path) -> None:
    with pytest.raises(ValueError, match="status"):
        load_tasks(_house(tmp_path, '[visits."task/a/b/c"]\nstatus = "nearly"\n'))


def test_verified_is_the_new_status(tmp_path) -> None:
    state = load_tasks(_house(tmp_path, '[entries."task/a/b"]\nstatus = "verified"\n'))
    assert state.entries["task/a/b"].status == "verified"


def test_set_visit_writes_through(tmp_path) -> None:
    directory = _house(tmp_path)
    state = load_tasks(directory)
    state = apply_visit_ops(state, {"op": "set_visit",
                                    "slug": "task/concrete/building/footings",
                                    "status": "in_progress"})
    write_tasks(directory, state)
    assert load_tasks(directory).visits.entries[
        "task/concrete/building/footings"].status == "in_progress"


def test_set_task_and_set_visit_do_not_collide(tmp_path) -> None:
    state = load_tasks(_house(tmp_path))
    state = apply_task_op(state, {"op": "set_task", "slug": "task/concrete/building",
                                  "status": "done"})
    assert state.visits.entries  # the visit half survived a task write
    state = apply_visit_ops(state, {"op": "set_visit",
                                    "slug": "task/concrete/building/footings",
                                    "note": "auger booked"})
    assert state.entries["task/concrete/building"].status == "done"


def test_clearing_a_constraint_is_a_label_keyed_write(tmp_path) -> None:
    state = load_tasks(_house(tmp_path))
    state = apply_visit_ops(state, {
        "op": "set_visit", "slug": "task/concrete/building/footings",
        "cleared": {"P/E/M on site during forming": "2027-05-03"}})
    visit = state.visits.entries["task/concrete/building/footings"]
    assert [c.cleared for c in visit.constraints] == ["2027-04-28", "2027-05-03"]


def test_verified_refuses_while_a_hold_is_open(tmp_path) -> None:
    state = load_tasks(_house(tmp_path))
    with pytest.raises(ValueError, match="cannot mark verified"):
        apply_visit_ops(state, {"op": "set_visit",
                                "slug": "task/concrete/building/footings",
                                "status": "verified"})
    cleared = apply_visit_ops(state, {
        "op": "set_visit", "slug": "task/concrete/building/footings",
        "cleared": {"P/E/M on site during forming": "2027-05-03"}})
    done = apply_visit_ops(cleared, {"op": "set_visit",
                                     "slug": "task/concrete/building/footings",
                                     "status": "verified"})
    assert done.visits.entries["task/concrete/building/footings"].status == "verified"


def test_unknown_op_and_field_raise() -> None:
    with pytest.raises(ValueError, match="unknown visit op"):
        apply_visit_op(VisitsState(), {"op": "set_thing", "slug": "task/a/b/c"})
    with pytest.raises(ValueError, match="unknown field"):
        apply_visit_op(VisitsState(), {"op": "set_visit", "slug": "task/a/b/c",
                                       "durations": 3})
