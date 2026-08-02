"""GET/PUT /costs — the server surface over takeoff/costs.py (mirrors test_detail_server)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture
def catlin_house(tmp_path: Path) -> Path:
    dst = tmp_path / "catlin"
    shutil.copytree(CATLIN, dst)
    return dst


@pytest.fixture
def client(catlin_house: Path):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    from typehaus.server.app import create_app

    with fastapi_testclient.TestClient(create_app(catlin_house)) as c:
        yield c


def test_get_costs_serves_the_full_payload(client):
    payload = client.get("/costs").json()
    assert set(payload) == {"prices_loaded", "estimate", "join", "entries", "extra",
                            "stale", "totals"}
    assert "framing" in payload["join"]
    assert payload["stale"] == []


def test_put_costs_round_trips_and_persists(client, catlin_house):
    bom = client.get("/bom").json()
    live_key = str(bom["framing_by_size"][0]["profile"])
    res = client.put("/costs", json={"ops": [
        {"op": "set_entry", "section": "framing", "key": live_key,
         "entry": {"paid": True, "paid_date": "2026-08-02", "actual_cost": 1234.5}},
        {"op": "set_extra", "item": {"name": "Building permit",
                                     "cost": {"low": 1800, "high": 2400}}},
    ]})
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["entries"]["framing"][live_key]["paid"] is True
    assert payload["extra"][0]["id"] == "building-permit"
    assert payload["totals"]["actual_paid"] == 1234.5
    # Durable: written to the house's costs.toml, and a fresh GET re-reads it.
    assert (catlin_house / "costs.toml").exists()
    assert live_key in (catlin_house / "costs.toml").read_text()
    again = client.get("/costs").json()
    assert again["entries"]["framing"][live_key]["actual_cost"] == 1234.5


def test_put_costs_is_all_or_nothing(client, catlin_house):
    res = client.put("/costs", json={"ops": [
        {"op": "set_extra", "item": {"name": "Crane day", "cost": 900}},
        {"op": "set_entry", "section": "lumber", "key": "x", "entry": {"paid": True}},
    ]})
    assert res.status_code == 400
    assert "unknown section" in res.json()["error"]
    # The valid first op must NOT have been persisted.
    assert client.get("/costs").json()["extra"] == []


def test_put_costs_rejects_an_empty_or_missing_ops_list(client):
    assert client.put("/costs", json={}).status_code == 400
    assert client.put("/costs", json={"ops": []}).status_code == 400


def test_costs_endpoints_409_when_the_model_does_not_resolve(tmp_path: Path):
    """An unresolved plan has no BOM to join against; both verbs must say so rather than
    serving a payload whose staleness would be fiction."""
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    from typehaus.server.app import create_app

    broken = tmp_path / "broken"
    shutil.copytree(CATLIN, broken)
    manifest = broken / "plan" / "manifest.py"
    manifest.write_text(manifest.read_text() + "\nraise RuntimeError('broken on purpose')\n")
    with fastapi_testclient.TestClient(create_app(broken)) as client:
        assert client.get("/costs").status_code == 409
        assert client.put("/costs", json={"ops": [
            {"op": "set_extra", "item": {"name": "x"}}]}).status_code == 409
