"""The SPA catch-all: client routes get index.html, a missing asset gets a 404."""

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from typehaus.server.app import _mount_spa  # noqa: E402


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><title>haus</title>")
    (tmp_path / "assets" / "app-abc.js").write_text("export {};")
    app = FastAPI()
    _mount_spa(app, tmp_path)
    return TestClient(app)


def test_root_and_client_routes_serve_index(client: TestClient) -> None:
    for path in ("/", "/site/board"):
        res = client.get(path)
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/html")
        assert res.headers["cache-control"] == "no-cache"


def test_real_asset_is_served(client: TestClient) -> None:
    assert client.get("/assets/app-abc.js").text == "export {};"


@pytest.mark.parametrize(
    "path",
    ["/assets/DocumentsView-oldhash.js", "/assets/nope", "/favicon.ico", "/missing.webmanifest"],
)
def test_missing_file_is_404_not_index(client: TestClient, path: str) -> None:
    res = client.get(path)
    assert res.status_code == 404
    assert not res.headers["content-type"].startswith("text/html")
