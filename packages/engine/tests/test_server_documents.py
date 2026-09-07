"""``GET /sheets`` and ``GET /notes`` — the served half of the Documents hub."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from _helpers import CATLIN, copy_house

from typehaus.emit.draw.sheet_manifest import sheet_manifest, write_sheet_manifest


@pytest.fixture
def catlin_house(tmp_path: Path) -> Path:
    dst = tmp_path / "catlin"
    copy_house(CATLIN, dst)
    return dst


@pytest.fixture
def client(catlin_house: Path):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    from typehaus.server.app import create_app

    with fastapi_testclient.TestClient(create_app(catlin_house)) as c:
        yield c


def _print_a_set(house: Path) -> None:
    """Stand in for `haus print` — the routes serve what the CLI left, not what they render."""
    write_sheet_manifest(
        house / "out" / "permit_set.json",
        sheet_manifest([("G-001", "Cover"), ("A-101", "Level 1")], pdf_name="permit_set.pdf",
                       paper="ledger", issue="NOT FOR CONSTRUCTION",
                       printed_at="2026-09-07", engine_version="0.0.0+dev",
                       content_hash="deadbeef"))
    (house / "out" / "permit_set.pdf").write_bytes(b"%PDF-1.4\n%stub\n")


def test_sheets_404s_until_the_set_is_printed(client, catlin_house):
    before = client.get("/sheets")
    assert before.status_code == 404
    assert "haus print" in before.json()["error"]

    _print_a_set(catlin_house)
    after = client.get("/sheets")
    assert after.status_code == 200
    manifest = after.json()
    assert [s["number"] for s in manifest["sheets"]] == ["G-001", "A-101"]
    assert manifest["issue"] == "NOT FOR CONSTRUCTION"


def test_the_pdf_route_is_an_allow_list(client, catlin_house):
    _print_a_set(catlin_house)
    ok = client.get("/sheets/permit_set.pdf")
    assert ok.status_code == 200
    assert ok.content.startswith(b"%PDF")
    # Not a drawing set, and not reachable even though it exists.
    (catlin_house / "out" / "secrets.pdf").write_bytes(b"%PDF-1.4\n")
    assert client.get("/sheets/secrets.pdf").status_code == 404
    assert client.get("/sheets/permit_set_24x36.pdf").status_code == 404  # not printed


def test_notes_lists_the_house_and_serves_one(client):
    listing = client.get("/notes")
    assert listing.status_code == 200
    notes = listing.json()["notes"]
    assert notes[0]["path"] == "brief.md"
    assert any(n["on_sheets"] for n in notes), "some note prints on a sheet"

    one = client.get("/notes/notes/interior_selections.md")
    assert one.status_code == 200
    assert one.json()["markdown"].strip()

    assert client.get("/notes/notes/nope.md").status_code == 404


def test_notes_refuses_to_escape_the_house(client):
    # A plain `..` is collapsed by the HTTP client before it is ever sent, so it never
    # reaches the route at all — which is fine, but proves nothing about the sandbox.
    assert client.get("/notes/../pyproject.toml").status_code in (403, 404)
    # Percent-encoded, it survives the client and lands on the handler as a real path.
    deep = client.get("/notes/notes/%2e%2e/%2e%2e/pyproject.toml")
    assert deep.status_code == 403
    assert "escapes" in deep.json()["error"]
    # Inside the house, but not a note.
    assert client.get("/notes/preferences.toml").status_code == 403


def test_the_manifest_round_trips_as_json(catlin_house):
    _print_a_set(catlin_house)
    from typehaus.server.documents_api import find_manifest

    found = find_manifest(catlin_house)
    assert found is not None
    path, manifest = found
    assert manifest == json.loads(path.read_text(encoding="utf-8"))
