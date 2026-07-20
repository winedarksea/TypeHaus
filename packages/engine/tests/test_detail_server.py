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
