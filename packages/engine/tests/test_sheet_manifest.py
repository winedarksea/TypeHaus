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
def test_haus_print_passes_the_draft_gate_on_catlin(tmp_path: Path):
    """The draft gate, end to end — and on 2026-09-20 it started OPENING on catlin.

    ** THIS TEST IS THE INVERSE OF THE ONE IT REPLACES, AND DELETING THAT ONE WAS ITS OWN
    INSTRUCTION. ** From 2026-09-18 `haus print houses/catlin` was refused: the north entry's
    cast column bases did not have the IBC 1807.3.2.1 embedment every `deck_post` record had
    been naming as an assumption and none grading. That test asserted the refusal and said in
    as many words that "the day the design closes … this test fails and tells somebody to
    delete it". `notes/entry_column_base_fixity.md` §6a closed the canopy pair with concrete
    and §6e closed the landing pair with a graded §1806.3.4 claim, so it did and this is what
    stands in its place.

    Asserting the gate OPEN is worth as much as asserting it shut, and for the same reason: a
    permit set that silently stopped being printable is exactly as bad as one that silently
    started. The half of the pair that is about the gate REFUSING where it should is
    `test_calc_package.py` and `test_permit_coverage.py`, which do not need catlin red.
    """
    pytest.importorskip("matplotlib")
    from typer.testing import CliRunner

    from typehaus.cli.app import app

    house = tmp_path / "catlin"
    copy_house(CATLIN, house)
    result = CliRunner().invoke(app, ["print", str(house), "--fmt", "pdf"])
    assert result.exit_code == 0, result.output
    assert "permit print blocked" not in result.output
    assert (house / "out" / "permit_set.pdf").is_file()


@pytest.mark.slow
def test_haus_print_writes_the_manifest_beside_the_pdf(tmp_path: Path):
    """End to end on the real house — the sandbox print, then the JSON next to it.

    ** THE GATE IS NO LONGER STUBBED, SINCE 2026-09-20. ** It was, for two years' worth of
    commits in two days: catlin could not pass the draft gate while its column bases were
    open, no shipped house could, and patching ``PermitChecklist.ok`` was what kept the
    composition, the writer and the file format under test at all. It passes now
    (``test_haus_print_passes_the_draft_gate_on_catlin`` above), so the stub is gone and this
    test exercises the real path end to end. The gate is the test above's subject and has its
    own coverage in ``test_calc_package`` and ``test_permit_coverage``.
    """
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
