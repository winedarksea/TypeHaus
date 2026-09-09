"""Declarative sheet composer — build_sheet_index is the one source of sheet order (→ 20)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.sheets import build_sheet_index, write_permit_set
from typehaus.resolve import resolve
from typehaus.source import load_plan

# ``slow`` (→ pyproject.toml, AGENTS.md §3): the permit-set PDF: 37 s to render and diff
# the whole sheet index. `scripts/verify.sh --fast` deselects it; the full gate still
# runs it.
pytestmark = pytest.mark.slow


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


def test_catlin_has_one_framing_sheet_per_framed_storey(catlin_model):
    """Three, not ten: the S-101 series is per STOREY, and catlin's main floor is six
    framed bays that used to be six sheets of one floor."""
    sheets = build_sheet_index(catlin_model)
    numbers = [s.number for s in sheets]
    assert "S-100" in numbers
    assert [n for n in numbers if n.startswith("S-101")] == ["S-101.1", "S-101.2",
                                                            "S-101.3"]
    assert "S-101.4" not in numbers
    assert "S-101" not in numbers  # only used when there's exactly one framed storey
    by_number = {s.number: s for s in sheets}
    assert by_number["S-101.1"].keywords == {"storey": "main"}
    assert by_number["S-101.2"].keywords == {"storey": "second"}
    assert by_number["S-101.3"].keywords == {"storey": "attic"}


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


# --- permit vs full -----------------------------------------------------------


def test_the_permit_set_is_an_ordered_subset_of_the_full_one(catlin_model):
    """Two sets, one composer. The permit set may drop sheets; it may never REORDER them,
    invent one, or renumber one — a callout that moved between sets would be a lie."""
    full = build_sheet_index(catlin_model, sets="full")
    permit = build_sheet_index(catlin_model, sets="permit")
    full_numbers = [s.number for s in full]
    permit_numbers = [s.number for s in permit]
    assert set(permit_numbers) <= set(full_numbers)
    assert permit_numbers == [n for n in full_numbers if n in set(permit_numbers)]
    titles = {s.number: s.title for s in full}
    assert all(s.title == titles[s.number] for s in permit)


def test_the_permit_set_fits_what_a_plan_checker_will_read(catlin_model):
    """The ask that started this: 109 sheets is not a set anybody reviews."""
    permit = build_sheet_index(catlin_model, sets="permit")
    assert len(permit) <= 55, [s.number for s in permit]
    numbers = {s.number for s in permit}
    # What DSI's new-construction checklist asks for.
    assert {"G-001", "C-101", "S-001", "S-100", "S-101.1", "A-101", "A-201",
            "A-301", "A-601", "A-602", "E-601"} <= numbers
    # ...and what it does not: no separate E or P drawings, no BOM, no finish schedule.
    assert not [n for n in numbers if n.startswith(("E-1", "E-2", "P-1", "P-2"))]
    assert "S-601" not in numbers and "A-603" not in numbers and "E-603" not in numbers


def test_a_house_can_put_a_dropped_series_back_in_one_line(catlin_model):
    """``[print] permit_add`` is the escape hatch for a reviewer who asks for E-1xx."""
    from typehaus.checks.registry import Preferences, PrintPreferences

    prefs = Preferences(print_options=PrintPreferences(permit_add=("E-1", "P-1")))
    numbers = {s.number for s in build_sheet_index(catlin_model, prefs, sets="permit")}
    assert "E-101" in numbers and "P-101" in numbers

    # ...and drop beats add, so a house cannot author a contradiction that silently
    # resolves one way.
    both = Preferences(print_options=PrintPreferences(permit_add=("E-1",),
                                                      permit_drop=("E-1",)))
    assert "E-101" not in {s.number
                           for s in build_sheet_index(catlin_model, both, sets="permit")}
