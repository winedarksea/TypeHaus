"""The site surface end to end on the reference house: CLI, GET, and a real write.

The write test is the one that matters. ``PUT /inspections`` has to land in
``houses/<name>/inspections.toml`` deterministically, because that file is the owner's
record of what the AHJ said and a server that mangled it would be worse than no server.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from _helpers import copy_house
from typer.testing import CliRunner

from typehaus.cli.app import app

CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def house(tmp_path_factory) -> Path:
    return copy_house(CATLIN, tmp_path_factory.mktemp("site") / "catlin")


@pytest.fixture
def client(house: Path):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    from typehaus.server.app import create_app

    with fastapi_testclient.TestClient(create_app(house)) as c:
        yield c


# --- CLI --------------------------------------------------------------------------------

def test_inspections_lists_the_profiles_own_list_plus_the_houses_extra(house: Path) -> None:
    result = CliRunner().invoke(app, ["inspections", str(house), "--json"])
    assert result.exit_code == 0, result.output
    import json

    payload = json.loads(result.stdout)
    records = payload["inspections"]
    from typehaus.checks.code.mn_residential.inspections import MN_INSPECTIONS

    assert len(records) == len(MN_INSPECTIONS) + 1        # + girt_screws
    assert records[0]["id"] == "erosion"
    assert [r["id"] for r in records if r["extra"]] == ["girt_screws"]
    # The engine ships no phone numbers; the house does.
    assert payload["authorities"]["building"]["phone"]


def test_gas_and_lath_are_not_applicable_with_evidence(house: Path) -> None:
    import json

    payload = json.loads(CliRunner().invoke(
        app, ["inspections", str(house), "--json"]).stdout)
    by_id = {r["id"]: r for r in payload["inspections"]}
    assert by_id["gas_test"]["state"] == "not_applicable"
    assert "all-electric" in by_id["gas_test"]["evidence"]
    assert by_id["lath"]["state"] == "not_applicable"
    assert "cement plaster" in by_id["lath"]["evidence"]


def test_the_fireplace_inspection_stays_listed_because_na_is_not_earned(house: Path) -> None:
    import json

    payload = json.loads(CliRunner().invoke(
        app, ["inspections", str(house), "--json"]).stdout)
    fireplace = next(r for r in payload["inspections"] if r["id"] == "fireplace")
    assert fireplace["applies"] is None
    assert fireplace["state"] != "not_applicable"
    assert "no fireplace element kind" in fireplace["evidence"]


def test_footing_is_not_ready_and_names_what_is_missing(house: Path) -> None:
    result = CliRunner().invoke(app, ["inspections", str(house)])
    assert result.exit_code == 0, result.output
    assert "footing" in result.stdout
    assert "Erosion and sediment control resolved" in result.stdout


def test_the_weathertight_milestone_names_its_real_blockers(house: Path) -> None:
    result = CliRunner().invoke(
        app, ["schedule", str(house), "--milestone", "weathertight"])
    assert result.exit_code == 0, result.output
    assert "Weathertight" in result.stdout
    assert "Damproofing, drainage and backfill passed" in result.stdout
    assert "Girt screws verified on every wall" in result.stdout
    # Only the one milestone.
    assert "Foundation\n" not in result.stdout


def test_propose_prints_a_split_and_writes_nothing(house: Path) -> None:
    before = (house / "tasks.toml").read_text() if (house / "tasks.toml").exists() else None
    result = CliRunner().invoke(
        app, ["schedule", str(house), "--propose", "task/concrete/building"])
    assert result.exit_code == 0, result.output
    assert "[visits." in result.stdout
    after = (house / "tasks.toml").read_text() if (house / "tasks.toml").exists() else None
    assert after == before


def test_propose_on_an_unknown_package_lists_the_real_ones(house: Path) -> None:
    result = CliRunner().invoke(app, ["schedule", str(house), "--propose", "task/nope"])
    assert result.exit_code == 2
    assert "task/concrete/" in result.stdout


# --- server -----------------------------------------------------------------------------

def test_get_schedule(client) -> None:
    payload = client.get("/schedule").json()
    assert payload["profile"] == "mn-2020"
    assert [m["id"] for m in payload["milestones"]] == [
        "preconstruction", "foundation", "weathertight", "rough_ins", "insulated",
        "final", "complete"]
    assert payload["visits"]
    concrete = [v for v in payload["visits"] if v["trade"] == "concrete"]
    assert concrete and all(v["readiness"] in ("ready", "blocked") for v in concrete)
    assert any(item["id"].startswith("sleeves:")
               for v in concrete for item in v["handoff"])
    assert "checks_pending" in payload


def test_get_inspections(client) -> None:
    payload = client.get("/inspections").json()
    assert payload["authorities"]["electrical"]["phone"] == "651-266-9003"
    footing = next(r for r in payload["inspections"] if r["id"] == "footing")
    assert footing["prerequisites"]
    # Passes included, unlike the UI's default findings view: before an inspection you
    # want the green ones too. The check job is queued behind the first resolve, so a
    # payload fetched inside that window carries no findings AND says so.
    assert footing["checks"] or payload["checks_pending"]


def test_put_inspections_writes_the_file_deterministically(client, house: Path) -> None:
    response = client.put("/inspections", json={"ops": [
        {"op": "set_inspection", "id": "footing", "requested": "2027-05-04"}]})
    assert response.status_code == 200
    footing = next(r for r in response.json()["inspections"] if r["id"] == "footing")
    assert footing["state"] == "requested"

    text = (house / "inspections.toml").read_text()
    assert '[entries.footing]' in text and '"2027-05-04"' in text
    # Idempotent: writing the same value again reproduces the file byte for byte.
    client.put("/inspections", json={"ops": [
        {"op": "set_inspection", "id": "footing", "requested": "2027-05-04"}]})
    assert (house / "inspections.toml").read_text() == text
    # The house's own authorities and extra survived the round trip.
    assert "651-266-9002" in text and "girt_screws" in text


def test_a_bad_op_persists_nothing(client, house: Path) -> None:
    before = (house / "inspections.toml").read_text()
    response = client.put("/inspections", json={"ops": [
        {"op": "set_inspection", "id": "footing", "scheduled": "2027-05-05"},
        {"op": "set_inspection", "id": "footing", "result": "probably"}]})
    assert response.status_code == 400
    assert "result" in response.json()["error"]
    assert (house / "inspections.toml").read_text() == before


def test_put_tasks_set_visit_writes_the_visits_table(client, house: Path) -> None:
    slug = "task/concrete/basement/walls"
    response = client.put("/tasks", json={"ops": [
        {"op": "set_visit", "slug": slug, "label": "Walls", "status": "scheduled",
         "scheduled": "2027-05-04"}]})
    assert response.status_code == 200
    text = (house / "tasks.toml").read_text()
    assert f'[visits."{slug}"]' in text
    # The board picks it up, and the package's implicit visit is gone.
    slugs = {v["slug"] for v in client.get("/schedule").json()["visits"]}
    assert slug in slugs and "task/concrete/basement" not in slugs


def test_a_checkpointed_visit_refuses_a_status_write(client) -> None:
    """The footings visit is three stops, so its status is derived from them."""
    response = client.put("/tasks", json={"ops": [
        {"op": "set_visit", "slug": "task/concrete/building/footings",
         "status": "scheduled"}]})
    assert response.status_code == 400
    assert "checkpoint" in response.json()["error"]
    ok = client.put("/tasks", json={"ops": [
        {"op": "set_checkpoint", "slug": "task/concrete/building/footings",
         "checkpoint": "forms", "status": "in_progress"}]})
    assert ok.status_code == 200


def test_set_task_still_works_beside_set_visit(client, house: Path) -> None:
    response = client.put("/tasks", json={"ops": [
        {"op": "set_task", "slug": "task/earth/building", "status": "done"}]})
    assert response.status_code == 200
    text = (house / "tasks.toml").read_text()
    assert '[entries."task/earth/building"]' in text
    assert '[visits."task/concrete/building/footings"]' in text
