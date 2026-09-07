"""``emit/notes_index.py`` — the house's markdown notes as a list a reader can page."""

from __future__ import annotations

from pathlib import Path

from typehaus.emit.notes_index import (
    KIND_ORDER,
    note_title,
    notes_index,
    oracle_notes,
    read_note,
    sheets_by_note,
)


def _house(catlin_model_ro) -> Path:
    return Path(catlin_model_ro.plan.source_root)


def test_the_brief_comes_first_and_is_its_own_kind(catlin_model_ro):
    entries = notes_index(_house(catlin_model_ro), catlin_model_ro)
    assert entries[0].path == "brief.md"
    assert entries[0].kind == "brief"
    assert entries[0].chars > 0
    assert all(entry.kind in KIND_ORDER for entry in entries)


def test_scaffolding_is_not_a_note(catlin_model_ro):
    paths = {entry.path for entry in notes_index(_house(catlin_model_ro), catlin_model_ro)}
    assert "notes/README.md" not in paths and "notes/TEMPLATE.md" not in paths
    assert "notes/brief.md" not in paths


def test_a_note_a_sheet_prints_is_a_detail_note(catlin_model_ro):
    """The binding is the drawing's, not a naming convention's."""
    bound = sheets_by_note(catlin_model_ro)
    assert bound, "catlin binds notes to detail sheets"
    entries = {entry.path: entry for entry in notes_index(_house(catlin_model_ro),
                                                          catlin_model_ro)}
    for rel in bound:
        assert entries[rel].kind == "detail", rel
        assert entries[rel].on_sheets, rel


def test_an_oracle_note_is_a_calculation(catlin_model_ro):
    oracles = oracle_notes()
    assert "catlin_truss_engineering.md" in oracles
    entries = {entry.path: entry for entry in notes_index(_house(catlin_model_ro),
                                                          catlin_model_ro)}
    for name in oracles:
        entry = entries.get(f"notes/{name}")
        if entry is None or entry.on_sheets:
            continue  # a sheet-printed note is a construction note first
        assert entry.kind == "calc", name


def test_superseded_and_design_notes(catlin_model_ro):
    entries = {entry.path: entry for entry in notes_index(_house(catlin_model_ro),
                                                          catlin_model_ro)}
    superseded = [p for p in entries if p.startswith("notes/superseded/")]
    assert superseded, "catlin keeps superseded notes"
    assert all(entries[p].kind == "superseded" for p in superseded)
    assert entries["notes/interior_selections.md"].kind == "design"


def test_titles_prefer_frontmatter_then_the_heading_then_the_stem():
    # Seven catlin notes open `# Notes` under a real frontmatter title. Reading the heading
    # would list all seven as "Notes".
    assert note_title('---\ntitle: "Backup Power"\n---\n# Notes\n\nbody', "notes/x.md") \
        == "Backup Power"
    assert note_title("---\nkind: design\n---\n# Real title\n\nbody", "notes/x.md") \
        == "Real title"
    assert note_title("no heading here", "notes/pocket_door_at_laundry.md") \
        == "Pocket door at laundry"


def test_no_two_catlin_notes_share_a_title(catlin_model_ro):
    """A list where seven rows read "Notes" is not an index."""
    titles = [entry.title for entry in notes_index(_house(catlin_model_ro), catlin_model_ro)]
    duplicated = {t for t in titles if titles.count(t) > 1}
    assert not duplicated, f"ambiguous note titles: {sorted(duplicated)}"


def test_reading_a_note_is_sandboxed(catlin_model_ro):
    house = _house(catlin_model_ro)
    assert read_note(house, "brief.md")
    assert read_note(house, "notes/interior_selections.md")
    assert read_note(house, "../pyproject.toml") is None
    assert read_note(house, "notes/../../../pyproject.toml") is None
    assert read_note(house, "preferences.toml") is None
    assert read_note(house, "notes/does_not_exist.md") is None


def test_the_index_survives_a_house_that_does_not_resolve(catlin_model_ro):
    """No model means no sheet bindings — never an exception."""
    entries = notes_index(_house(catlin_model_ro), None)
    assert entries and all(entry.on_sheets == () for entry in entries)
