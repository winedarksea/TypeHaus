"""WP2.1 — FastAPI server: model.json contract, revision precondition, undo/redo (→ 20)."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import pytest

from typehaus.server.events import EventBus


@pytest.fixture
def house(tmp_path: Path, starter_dir: Path) -> Path:
    dst = tmp_path / "starter"
    shutil.copytree(starter_dir, dst)
    return dst


@pytest.fixture
def client(house: Path):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    from typehaus.server.app import create_app

    with fastapi_testclient.TestClient(create_app(house)) as c:
        yield c, house


def test_model_contract_carries_revision_and_provenance(client):
    c, _ = client
    model = c.get("/model").json()
    assert model["ok"] is True
    assert model["revision"]
    assert model["units"] == "imperial"
    assert "findings" in model
    wall = model["walls"][0]
    assert wall["provenance"]["file"].endswith(".py")
    assert wall["provenance"]["line"] > 0


def test_patch_requires_matching_revision(client):
    c, house = client
    stale = c.patch("/plan", json={
        "revision": "STALE",
        "ops": [{"op": "update", "type": "Wall", "tag": "W-101", "fields": {"top": "11'"}}],
    })
    assert stale.status_code == 409


def test_patch_undo_redo_round_trip(client):
    c, house = client
    rev = c.get("/model").json()["revision"]
    ok = c.patch("/plan", json={
        "revision": rev,
        "ops": [{"op": "update", "type": "Wall", "tag": "W-101", "fields": {"top": "11'"}}],
    })
    assert ok.status_code == 200
    main = house / "plan" / "storeys" / "main.py"
    assert "ft(11)" in main.read_text()
    assert c.post("/undo").status_code == 200
    assert "ft(11)" not in main.read_text()
    assert c.post("/redo").status_code == 200
    assert "ft(11)" in main.read_text()


def test_undo_with_empty_journal_is_409(client):
    c, _ = client
    assert c.post("/undo").status_code == 409


def test_underlay_calibration_rewrites_only_the_matching_toml_table(tmp_path: Path):
    from typehaus.server.app import _write_underlay_calibration

    preferences = tmp_path / "preferences.toml"
    preferences.write_text(
        "[envelope]\nwall_r = 40\n\n"
        "[[underlay]]\npath = \"a.png\"\nstorey = \"main\"\n"
        "origin_x_m = 0\norigin_y_m = 0\nwidth_m = 10\nheight_m = 10\n"
        "rotation_deg = 0\nopacity = 0.25\n\n"
        "[[underlay]]\npath = \"b.png\"\nstorey = \"second\"\n"
        "origin_x_m = 1\norigin_y_m = 2\nwidth_m = 3\nheight_m = 4\n"
        "rotation_deg = 5\nopacity = 0.2\n"
    )
    _write_underlay_calibration(preferences, {
        "path": "a.png", "storey": "main", "origin_x_m": 4, "origin_y_m": 5,
        "width_m": 6, "height_m": 7, "rotation_deg": 8, "opacity": 0.15,
    })
    text = preferences.read_text()
    assert "wall_r = 40" in text and 'path = "b.png"' in text
    assert "origin_x_m = 4" in text and "rotation_deg = 8" in text


def test_event_bus_broadcasts_to_clients():
    class _FakeWS:
        def __init__(self) -> None:
            self.events: list[dict] = []
            self.accepted = False

        async def accept(self) -> None:
            self.accepted = True

        async def send_json(self, event: dict) -> None:
            self.events.append(event)

    async def run() -> None:
        bus = EventBus()
        ws = _FakeWS()
        await bus.connect(ws)
        await bus.broadcast({"type": "build"})
        assert ws.accepted and ws.events == [{"type": "build"}]

    asyncio.run(run())
