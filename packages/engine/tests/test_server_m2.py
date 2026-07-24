"""WP2.1 — FastAPI server: model.json contract, revision precondition, undo/redo (→ 20)."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import pytest

from typehaus.server.events import EventBus
from typehaus.server.app import _is_project_source_change


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


def test_asset_creation_is_watched_without_observing_output_files(tmp_path: Path):
    house = tmp_path / "house"
    assert _is_project_source_change(house, house / "assets" / "placeables.json")
    assert _is_project_source_change(house, house / "plan" / "main.py")
    assert not _is_project_source_change(house, house / "out" / "model.ifc")


def test_model_contract_carries_opening_product_and_handing(client):
    c, _ = client
    model = c.get("/model").json()
    opening = model["openings"][0]
    assert opening["type_ref"]
    assert isinstance(opening["flip_hinge"], bool)
    assert isinstance(opening["flip_swing"], bool)
    wall_tags = {wall["tag"] for wall in model["walls"]}
    wall_uids = {wall["uid"] for wall in model["walls"]}
    assert all(item["host"] in wall_tags for item in model["openings"])
    assert all(item["host"] not in wall_uids for item in model["openings"])


def test_patch_requires_matching_revision(client):
    c, house = client
    stale = c.patch("/plan", json={
        "revision": "STALE",
        "ops": [{"op": "update", "type": "Wall", "tag": "W-101", "fields": {"top": "11'"}}],
    })
    assert stale.status_code == 409


def test_patch_undo_redo_round_trip(client):
    c, house = client
    state = c.app.state.project
    rev = c.get("/model").json()["revision"]
    ok = c.patch("/plan", json={
        "revision": rev,
        "ops": [{"op": "update", "type": "Wall", "tag": "W-101", "fields": {"top": "11'"}}],
    })
    assert ok.status_code == 200
    # The fast path answers before the source writeback lands (→ Phase 2b); flush it before
    # asserting on disk. undo()/redo() flush internally (source is the ground truth there).
    state._flush_writes()
    main = house / "plan" / "storeys" / "main.py"
    assert "ft(11)" in main.read_text()
    assert c.post("/undo").status_code == 200
    assert "ft(11)" not in main.read_text()
    assert c.post("/redo").status_code == 200
    assert "ft(11)" in main.read_text()


def test_preview_returns_reduced_geometry_without_mutating_state(client):
    c, house = client
    state = c.app.state.project
    rev = c.get("/model").json()["revision"]
    resp = c.post("/preview", json={
        "ops": [{"op": "update", "type": "Wall", "tag": "W-101", "fields": {"top": "11'"}}],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "walls" in body and "openings" in body and "rooms" in body
    assert any(w["tag"] == "W-101" for w in body["walls"])
    # A preview never mutates project state: revision unchanged, nothing queued to disk.
    assert state.revision() == rev
    main = house / "plan" / "storeys" / "main.py"
    assert "ft(11)" not in main.read_text()


def test_preview_rejects_ops_that_cannot_apply_in_memory(client):
    c, _ = client
    resp = c.post("/preview", json={
        "ops": [{"op": "update", "type": "Wall", "tag": "NO-SUCH-WALL", "fields": {"top": "11'"}}],
    })
    assert resp.status_code == 422


def test_undo_with_empty_journal_is_409(client):
    c, _ = client
    assert c.post("/undo").status_code == 409


def test_checks_run_async_after_a_fast_edit(client):
    """→ Phase 3: the fast path's response lands before the check-tier job finishes; the
    findings/ok update in place afterwards without a further revision bump."""
    c, _ = client
    state = c.app.state.project
    state._flush_checks()  # settle the initial open()'s check job before asserting deltas
    rev = c.get("/model").json()["revision"]
    ok = c.patch("/plan", json={
        "revision": rev,
        "ops": [{"op": "update", "type": "Wall", "tag": "W-101", "fields": {"top": "11'"}}],
    })
    assert ok.status_code == 200
    new_rev = ok.json()["revision"]
    assert new_rev != rev
    state._flush_checks()
    assert state.checks_pending is False
    model = c.get("/model").json()
    assert model["revision"] == new_rev  # checks landing doesn't bump the client revision
    assert model["checksPending"] is False
    state._flush_writes()


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


def test_events_socket_accepts_the_handshake_and_pushes_build_events(client):
    """The UI's liveness signal is the WS handshake itself — a rejected upgrade reads to the
    user as "haus serve not running" even while every GET succeeds (deferred-import ForwardRef
    regression: the endpoint degraded into a required `ws` query param, closing with 403)."""
    c, _ = client
    with c.websocket_connect("/events") as ws:
        c.post("/build")
        assert ws.receive_json()["type"] == "build"


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
