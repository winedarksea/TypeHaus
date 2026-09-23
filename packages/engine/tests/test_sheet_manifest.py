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
def test_haus_print_refuses_catlin_on_the_deck_ledger_anchors(tmp_path: Path):
    """The draft gate, end to end — and since 2026-09-22 (evening) it REFUSES catlin again.

    It opened earlier that day when the last engineering line closed, and shut when the
    porch went onto two wall ledgers: `structural.deck_ledger` reads UNKNOWN because DCA6
    leaves adhesive-anchor spacing and embedment to the anchor maker, and that table is not
    yet quoted. That is the ONLY blocking line, and it is asserted by name. The day it closes
    this test fails and tells somebody to invert it back; a permit set that silently became
    printable is exactly as bad as one that silently stopped.
    """
    from typer.testing import CliRunner

    from typehaus.cli.app import app

    house = tmp_path / "catlin"
    copy_house(CATLIN, house)
    result = CliRunner().invoke(app, ["print", str(house), "--fmt", "pdf"])
    assert result.exit_code == 1, result.output
    assert "permit print blocked" in result.output
    blocking = [line for line in result.output.splitlines()
                if ": UNKNOWN" in line or ": FAIL" in line]
    assert len(blocking) == 1 and "Deck ledgers and their attachment: UNKNOWN" in blocking[0], \
        result.output
    assert not (house / "out" / "permit_set.pdf").is_file()


@pytest.mark.slow
def test_haus_print_writes_the_manifest_beside_the_pdf(tmp_path: Path, monkeypatch):
    """End to end on the real house — the sandbox print, then the JSON next to it.

    ** THE GATE IS STUBBED AGAIN, SINCE 2026-09-20. ** catlin does not reach draft (the test
    above), and patching ``PermitChecklist.ok`` is what keeps the composition, the writer
    and the file format under test while it does not. Remove the stub the day catlin passes.
    """
    pytest.importorskip("matplotlib")
    from typer.testing import CliRunner

    from typehaus.checks.permit import PermitChecklist
    from typehaus.cli.app import app

    monkeypatch.setattr(PermitChecklist, "ok", property(lambda self: True))

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
    # catlin authors `[print] issue`, and the house has the last word on the wording of
    # its own submittal — the engine's "NOT FOR CONSTRUCTION" is only the fallback.
    assert manifest["issue"] == "ISSUED FOR PERMIT", "the house's [print] issue is stamped"
    assert manifest["content_hash"], "the manifest names the model it was printed from"
    assert [s["page"] for s in manifest["sheets"]] == list(
        range(1, len(manifest["sheets"]) + 1))


def test_a_house_authored_issue_is_recorded_verbatim():
    """The manifest is the audit trail: it records whatever was stamped, not a category."""
    manifest = sheet_manifest(INDEX, pdf_name="permit_set_24x36.pdf", paper="arch-d",
                              issue="ISSUED FOR PERMIT", printed_at="2026-09-08",
                              engine_version="0.0.0+dev", content_hash="abc123")
    assert manifest["issue"] == "ISSUED FOR PERMIT"
