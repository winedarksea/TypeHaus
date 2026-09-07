"""The permit set's on-disk table of contents (``out/permit_set.json``)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from _helpers import CATLIN, copy_house

from typehaus.emit.draw.sheet_manifest import sheet_manifest, write_sheet_manifest

INDEX = [("G-001", "Cover"), ("S-101", "Foundation plan"), ("A-101", "Floor plan")]


def _manifest():
    return sheet_manifest(INDEX, pdf_name="permit_set.pdf", paper="ledger",
                          issue="NOT FOR CONSTRUCTION", printed_at="2026-09-07",
                          engine_version="0.0.0+dev", content_hash="abc123")


def test_pages_are_the_composed_order_one_based():
    sheets = _manifest()["sheets"]
    assert [s["page"] for s in sheets] == [1, 2, 3]
    assert [s["number"] for s in sheets] == ["G-001", "S-101", "A-101"]
    assert sheets[1]["title"] == "Foundation plan"


def test_the_stamp_and_provenance_ride_along():
    manifest = _manifest()
    assert manifest["issue"] == "NOT FOR CONSTRUCTION"
    assert manifest["pdf"] == "permit_set.pdf"
    assert manifest["paper"] == "ledger"
    assert manifest["content_hash"] == "abc123"
    assert manifest["engine_version"] == "0.0.0+dev"


def test_the_file_is_byte_deterministic(tmp_path: Path):
    """Regenerated rather than maintained, so a diff between two prints is a real change."""
    a = write_sheet_manifest(tmp_path / "a.json", _manifest())
    b = write_sheet_manifest(tmp_path / "b.json", _manifest())
    assert a.read_bytes() == b.read_bytes()
    body = a.read_text(encoding="utf-8")
    assert body.endswith("\n")
    assert list(json.loads(body)) == sorted(json.loads(body)), "sort_keys, for a clean diff"


@pytest.mark.slow
def test_haus_print_writes_the_manifest_beside_the_pdf(tmp_path: Path):
    """End to end on the real house — the sandbox print, then the JSON next to it."""
    pytest.importorskip("matplotlib")
    from typer.testing import CliRunner

    from typehaus.cli.app import app

    house = tmp_path / "catlin"
    copy_house(CATLIN, house)
    result = CliRunner().invoke(app, ["print", str(house), "--fmt", "pdf"])
    assert result.exit_code == 0, result.output

    pdf = house / "out" / "permit_set.pdf"
    manifest_path = house / "out" / "permit_set.json"
    assert pdf.is_file() and manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    numbers = [sheet["number"] for sheet in manifest["sheets"]]
    assert numbers[0] == "G-001", "the cover is page 1"
    assert any(n.startswith("A-1") for n in numbers), "a floor plan is in the set"
    assert manifest["issue"] == "NOT FOR CONSTRUCTION", "an unsealed print says so"
    assert manifest["content_hash"], "the manifest names the model it was printed from"
    assert [s["page"] for s in manifest["sheets"]] == list(
        range(1, len(manifest["sheets"]) + 1))
