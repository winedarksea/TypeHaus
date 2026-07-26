"""WP6 — /details + /detail endpoints and the shared pure-data payload (server + Pyodide)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from typehaus.emit.draw.details import detail_index, detail_payload

CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"


def test_detail_index_and_payload_are_pure_data(catlin_model):
    index = detail_index(catlin_model)
    assert index
    keys = [row["key"] for row in index]
    assert keys == sorted(set(keys))
    eave_key = next(k for k in keys if k.startswith("wall_roof"))
    payload = detail_payload(catlin_model, eave_key)
    assert payload is not None
    assert payload["scene"]["nodes"]  # a real scene
    assert isinstance(payload["annotations"], list)
    # unknown key → None (server maps to 404)
    assert detail_payload(catlin_model, "no_such_key") is None


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


def test_details_endpoint_lists_and_serves_a_scene(client):
    index = client.get("/details").json()["details"]
    assert index
    key = next(row["key"] for row in index if row["key"].startswith("wall_roof"))
    payload = client.get("/detail", params={"key": key}).json()
    assert payload["key"] == key
    assert payload["scene"]["nodes"]
    # a key containing '|' and ':' round-trips through the query param
    assert "|" in key and ":" in key
    missing = client.get("/detail", params={"key": "nope"})
    assert missing.status_code == 404


def _noted_key(client) -> str:
    """A detail key whose payload carries a notes file (Transition.notes set)."""
    index = client.get("/details").json()["details"]
    for row in index:
        payload = client.get("/detail", params={"key": row["key"]}).json()
        if payload.get("notes"):
            return row["key"]
    raise AssertionError("no detail with a notes file in the catlin fixture")


def test_append_detail_note_appends_one_bullet(client, catlin_house):
    key = _noted_key(client)
    before = client.get("/detail", params={"key": key}).json()
    assert before["notes_markdown"], "payload should carry the notes file content"

    res = client.post("/detail/notes", json={"key": key, "text": "verify gutter slope"})
    assert res.status_code == 200
    updated = res.json()["notes_markdown"]
    assert updated.endswith("- verify gutter slope\n")
    # persisted to the house's notes file, not just echoed
    rel = before["notes"]
    assert (catlin_house / rel).read_text(encoding="utf-8") == updated
    # and the next payload fetch reflects it
    after = client.get("/detail", params={"key": key}).json()
    assert after["notes_markdown"] == updated


def test_append_detail_note_flattens_markdown_structure(client):
    key = _noted_key(client)
    res = client.post("/detail/notes",
                      json={"key": key, "text": "line one\n# heading\n- sneaky bullet"})
    assert res.status_code == 200
    # whitespace (incl. newlines) collapses: one note, one bullet
    assert res.json()["notes_markdown"].endswith("- line one # heading - sneaky bullet\n")


def test_append_detail_note_rejects_bad_requests(client):
    key = _noted_key(client)
    assert client.post("/detail/notes", json={"key": key, "text": "   "}).status_code == 400
    assert client.post("/detail/notes", json={"text": "no key"}).status_code == 400
    assert client.post("/detail/notes",
                       json={"key": "no_such_key", "text": "x"}).status_code == 404
