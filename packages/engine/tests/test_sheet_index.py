"""Declarative sheet composer — build_sheet_index is the one source of sheet order (→ 20)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.sheets import build_sheet_index, write_permit_set
from typehaus.resolve import resolve
from typehaus.source import load_plan


@pytest.fixture(scope="module")
def starter_model(starter_dir: Path):
    result = load_plan(starter_dir)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def test_sheet_numbers_are_unique(catlin_model):
    sheets = build_sheet_index(catlin_model)
    numbers = [s.number for s in sheets]
    assert len(numbers) == len(set(numbers))


def test_catlin_includes_s100_and_two_framing_sheets(catlin_model):
    sheets = build_sheet_index(catlin_model)
    numbers = [s.number for s in sheets]
    assert "S-100" in numbers
    assert "S-101.1" in numbers and "S-101.2" in numbers
    assert "S-101" not in numbers  # only used when there's exactly one resolved floor


def test_starter_omits_s100_and_uses_bare_s101(starter_model):
    sheets = build_sheet_index(starter_model)
    numbers = [s.number for s in sheets]
    assert "S-100" not in numbers
    assert "S-101" in numbers
    assert not any(n.startswith("S-101.") for n in numbers)


def test_s100_and_s101_no_longer_alias_floorplan_builder(catlin_model):
    from typehaus.emit.draw.floorplan import build_floorplan
    from typehaus.emit.draw.foundationplan import build_foundation_plan
    from typehaus.emit.draw.framingplan import build_framing_plan

    sheets = {s.number: s for s in build_sheet_index(catlin_model)}
    # S-100 is a partial now: the jurisdiction profile that states the frost depth in
    # its notes is bound at index time, not re-looked-up inside the builder.
    assert sheets["S-100"].scene.func is build_foundation_plan
    assert sheets["S-101.1"].scene.func is build_framing_plan
    assert sheets["S-101.1"].scene is not build_floorplan


def test_cover_index_matches_emitted_pages(catlin_model, tmp_path: Path):
    _, meta = write_permit_set(catlin_model, tmp_path / "permit_set.pdf")
    index = meta["index"]
    sheets = build_sheet_index(catlin_model)
    assert index == [(s.number, s.title) for s in sheets]


def test_write_permit_set_produces_a_nonempty_pdf(catlin_model, tmp_path: Path):
    path, _ = write_permit_set(catlin_model, tmp_path / "permit_set.pdf")
    assert path.stat().st_size > 0
