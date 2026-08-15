"""``tasks.toml``, ``GET/PUT /tasks``, and the estimate-CSV round trip.

Two write-back paths, both deliberately built on machinery that already existed:

* ``haus costs import`` reads an edited estimate CSV back through the *existing*
  ``apply_costs_op`` on the *existing* ``(section, key)`` join — no new state, no new server
  surface, and actual-vs-estimated round-trips through a spreadsheet.
* ``tasks.toml`` mirrors ``costs.toml``'s loader/writer idiom exactly, and status is kept
  **out** of ``CostEntry``: paid and done are different facts about different objects.
"""

from __future__ import annotations

import csv

import pytest
from typer.testing import CliRunner

from typehaus.cli.app import app
from typehaus.takeoff.costs import CostEntry, load_costs
from typehaus.takeoff.task_state import (DEFAULT_STATUS, STATUSES, TaskEntry, TasksState,
                                         apply_task_op, load_tasks, write_tasks)

from _helpers import CATLIN, copy_house

runner = CliRunner()


@pytest.fixture
def sandbox(tmp_path):
    return copy_house(CATLIN, tmp_path / "catlin")


# --- tasks.toml -----------------------------------------------------------------------------

def test_an_absent_file_is_an_empty_state_not_an_error(tmp_path) -> None:
    assert load_tasks(tmp_path).entries == {}
    assert load_tasks(tmp_path).status_of("task/framing/building") == DEFAULT_STATUS


def test_status_round_trips_through_the_file(tmp_path) -> None:
    state = apply_task_op(TasksState(), {"op": "set_task", "slug": "task/framing/building",
                                         "status": "in_progress", "assignee": "Northside"})
    write_tasks(tmp_path, state)
    reloaded = load_tasks(tmp_path)
    assert reloaded.entries["task/framing/building"] == TaskEntry(
        status="in_progress", assignee="Northside")


def test_the_writer_is_deterministic(tmp_path) -> None:
    state = TasksState(entries={"b": TaskEntry(status="done"),
                                "a": TaskEntry(status="scheduled")})
    first = write_tasks(tmp_path, state).read_text()
    second = write_tasks(tmp_path, state).read_text()
    assert first == second
    assert first.index("entries.\"a\"") < first.index("entries.\"b\"")


def test_clearing_every_field_deletes_the_entry(tmp_path) -> None:
    state = apply_task_op(TasksState(), {"op": "set_task", "slug": "x", "status": "done"})
    state = apply_task_op(state, {"op": "set_task", "slug": "x", "status": DEFAULT_STATUS})
    assert state.entries == {}


@pytest.mark.parametrize("body, message", [
    ('[entries."x"]\nstatus = "finished"\n', "expected one of"),
    ('[entries."x"]\nowner = "bob"\n', "unknown field"),
    ('[nope]\nx = 1\n', "unknown top-level"),
])
def test_a_malformed_tasks_file_errors_loudly(tmp_path, body, message) -> None:
    (tmp_path / "tasks.toml").write_text(body)
    with pytest.raises(ValueError, match=message):
        load_tasks(tmp_path)


def test_a_bad_status_is_rejected_by_the_op_too() -> None:
    with pytest.raises(ValueError, match="expected one of"):
        apply_task_op(TasksState(), {"op": "set_task", "slug": "x", "status": "nope"})


def test_status_is_not_a_cost_entry_field() -> None:
    """Paid and done are different facts. A delivered, paid-for pallet of studs sitting in
    the driveway is neither of the other one, and conflating them was the mistake to avoid."""
    assert not hasattr(CostEntry(), "status")
    assert set(STATUSES).isdisjoint(CostEntry().as_dict())


# --- the server -----------------------------------------------------------------------------

def test_get_and_put_tasks(sandbox) -> None:
    from fastapi.testclient import TestClient

    from typehaus.server.app import create_app

    client = TestClient(create_app(sandbox))
    payload = client.get("/tasks").json()
    assert payload["tasks"] and payload["statuses"] == list(STATUSES)
    slug = payload["tasks"][0]["slug"]
    assert payload["tasks"][0]["status"] == DEFAULT_STATUS

    updated = client.put("/tasks", json={"ops": [
        {"op": "set_task", "slug": slug, "status": "done"}]})
    assert updated.status_code == 200
    assert next(t for t in updated.json()["tasks"] if t["slug"] == slug)["status"] == "done"
    assert load_tasks(sandbox).status_of(slug) == "done"


def test_a_bad_op_persists_nothing(sandbox) -> None:
    """All-or-nothing, like /costs: a client retry must not half-apply a batch."""
    from fastapi.testclient import TestClient

    from typehaus.server.app import create_app

    client = TestClient(create_app(sandbox))
    slug = client.get("/tasks").json()["tasks"][0]["slug"]
    response = client.put("/tasks", json={"ops": [
        {"op": "set_task", "slug": slug, "status": "done"},
        {"op": "set_task", "slug": slug, "status": "nonsense"}]})
    assert response.status_code == 400
    assert not (sandbox / "tasks.toml").exists()


def test_a_slug_that_no_longer_derives_is_reported_stale_not_dropped(sandbox) -> None:
    from fastapi.testclient import TestClient

    from typehaus.server.app import create_app

    write_tasks(sandbox, TasksState(entries={"task/nothing/nowhere": TaskEntry(status="done")}))
    payload = TestClient(create_app(sandbox)).get("/tasks").json()
    assert payload["stale"] == ["task/nothing/nowhere"]


# --- haus tasks / haus costs import ------------------------------------------------------

def test_haus_tasks_writes_a_csv_with_the_pm_column_set(sandbox, tmp_path) -> None:
    from typehaus.cli.cmd_tasks import TASK_COLUMNS

    out = tmp_path / "tasks.csv"
    result = runner.invoke(app, ["tasks", str(sandbox), "--csv", str(out)])
    assert result.exit_code == 0, result.output
    rows = list(csv.DictReader(out.open()))
    assert rows and list(rows[0]) == list(TASK_COLUMNS)
    assert {"id", "title", "status", "depends_on"} <= set(rows[0])


def test_re_exporting_after_a_rebuild_is_byte_identical(sandbox, tmp_path) -> None:
    """The stable-GlobalId property, end to end: this is what stops a second export from
    duplicating every card in the receiving tool."""
    first, second = tmp_path / "a.csv", tmp_path / "b.csv"
    runner.invoke(app, ["tasks", str(sandbox), "--csv", str(first)])
    runner.invoke(app, ["build", str(sandbox), "--only", "json"])
    runner.invoke(app, ["tasks", str(sandbox), "--csv", str(second)])
    assert first.read_bytes() == second.read_bytes()


def test_costs_import_lands_an_edited_actual_cost(sandbox, tmp_path) -> None:
    estimate_csv = tmp_path / "estimate.csv"
    assert runner.invoke(app, ["takeoff", str(sandbox), "--csv",
                               str(estimate_csv)]).exit_code == 0
    rows = list(csv.DictReader(estimate_csv.open()))
    target = next(row for row in rows if row["section"] == "framing")
    target["actual_cost"], target["paid"] = "$1,234.56", "yes"
    with estimate_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    result = runner.invoke(app, ["costs", "import", str(estimate_csv), "--house", str(sandbox)])
    assert result.exit_code == 0, result.output
    entry = load_costs(sandbox).entries["framing"][target["key"]]
    assert entry.actual_cost == 1234.56 and entry.paid is True


def test_costs_import_reports_a_stale_row_rather_than_applying_it(sandbox, tmp_path) -> None:
    """A row whose (section, key) matches nothing means the plan moved on under the
    spreadsheet — which is exactly the fact an owner has to see."""
    path = tmp_path / "e.csv"
    path.write_text("section,key,actual_cost,paid\nframing,NOT-A-PROFILE,100,yes\n")
    result = runner.invoke(app, ["costs", "import", str(path), "--house", str(sandbox)])
    assert result.exit_code == 0
    assert "stale" in result.output
    assert not (sandbox / "costs.toml").exists() or "NOT-A-PROFILE" not in (
        sandbox / "costs.toml").read_text()


def test_costs_import_refuses_a_file_that_is_not_an_estimate_csv(sandbox, tmp_path) -> None:
    path = tmp_path / "wrong.csv"
    path.write_text("a,b\n1,2\n")
    result = runner.invoke(app, ["costs", "import", str(path), "--house", str(sandbox)])
    assert result.exit_code == 2
    assert "missing column" in result.output


def test_costs_import_keeps_fields_the_csv_has_no_column_for(sandbox, tmp_path) -> None:
    """product, paid_date and note survive an import. Erasing what somebody recorded would
    be worse than refusing to run."""
    from typehaus.takeoff.costs import CostsState, write_costs

    estimate_csv = tmp_path / "estimate.csv"
    runner.invoke(app, ["takeoff", str(sandbox), "--csv", str(estimate_csv)])
    rows = list(csv.DictReader(estimate_csv.open()))
    target = next(row for row in rows if row["section"] == "framing")
    write_costs(sandbox, CostsState(entries={"framing": {
        target["key"]: CostEntry(product="Menards SPF #2", note="delivered 8/12")}}))

    target["actual_cost"] = "500"
    with estimate_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    runner.invoke(app, ["costs", "import", str(estimate_csv), "--house", str(sandbox)])

    entry = load_costs(sandbox).entries["framing"][target["key"]]
    assert entry.actual_cost == 500.0
    assert entry.product == "Menards SPF #2" and entry.note == "delivered 8/12"
