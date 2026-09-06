"""``haus record`` — the design record (→ 30 §Notes).

The third kind of content CSI's two-way split has no room for. Drawings carry quantity,
specifications carry procedure, and the argument behind a decision — what was considered,
what it replaced, what it cost, what is still open — belongs to neither. It is the most
valuable writing in the repository and the least suited to a construction sheet.
"""

from __future__ import annotations

from pathlib import Path

from typehaus.emit.design_record import (
    BANNER,
    NoteSource,
    RecordInputs,
    _split_frontmatter,
    design_record,
)

SAMPLE = """---
title: "Roof-to-Wall Eave Detail Notes"
applied_to:
  - detail: roof_wall_eave_detail
tags:
  - roof
  - eave
---

## Sheet notes

### General
- Roof framing: 11-7/8" TJI 230 at 24" o.c.

# Notes

- The spacing is **NOT FINAL**: see `notes/x.md` — ForteWEB owns the last word.
"""


def _inputs(*notes: NoteSource) -> RecordInputs:
    return RecordInputs(house="H", generated="2026-09-06", engine_version="0.1",
                        content_hash="abcdef012345678", notes=notes)


def test_the_body_is_verbatim() -> None:
    """The whole point. This emitter reformats nothing.

    ``emit/draw/note_text.py`` strips markdown, drops repository paths and folds non-ASCII
    because a construction sheet is a hostile medium. A design record is read the same way
    the file is, so anything done to it here can only lose something.
    """
    page = design_record(_inputs(NoteSource("notes/eave.md", SAMPLE)))["eave.md"]
    assert "**NOT FINAL**" in page
    assert "`notes/x.md`" in page
    assert "—" in page


def test_every_page_says_what_it_is_not() -> None:
    files = design_record(_inputs(NoteSource("notes/eave.md", SAMPLE)))
    assert all(BANNER in text for text in files.values())


def test_the_index_splits_by_whether_a_note_reaches_a_drawing() -> None:
    index = design_record(_inputs(
        NoteSource("notes/eave.md", SAMPLE, on_sheets=("A-579", "A-580")),
        NoteSource("notes/why.md", "# Why\n\nbecause."),
    ))["index.md"]
    behind = index.index("## Behind a drawing")
    other = index.index("## Not on any drawing")
    assert behind < index.index("eave.md") < other < index.index("why.md")


def test_a_long_sheet_list_becomes_a_range() -> None:
    """Same rule G-002's index uses — twelve numbers is a wall of text where a range says
    the same thing."""
    many = tuple(f"A-{n}" for n in range(510, 517))
    index = design_record(_inputs(
        NoteSource("notes/eave.md", SAMPLE, on_sheets=many)))["index.md"]
    assert "A-510..A-516 (7 sheets)" in index
    two = design_record(_inputs(
        NoteSource("notes/e.md", SAMPLE, on_sheets=("A-522", "A-523"))))["index.md"]
    assert "A-522, A-523" in two


def test_frontmatter_becomes_a_table_and_a_list_folds_into_its_key() -> None:
    fields, body = _split_frontmatter(SAMPLE)
    assert ("title", "Roof-to-Wall Eave Detail Notes") in fields
    assert ("tags", "roof eave") in fields
    assert body.lstrip().startswith("## Sheet notes")


def test_a_file_with_no_frontmatter_survives() -> None:
    fields, body = _split_frontmatter("# Why\n\nbecause.")
    assert fields == []
    assert body == "# Why\n\nbecause."


def test_the_output_is_deterministic_and_sorted() -> None:
    args = (NoteSource("notes/b.md", SAMPLE), NoteSource("notes/a.md", SAMPLE))
    first = design_record(_inputs(*args))
    assert first == design_record(_inputs(*reversed(args)))
    assert list(first) == sorted(first)


def test_the_catlin_record_covers_every_note(catlin_model_ro, tmp_path):
    """End to end, on the real house — including `superseded/`, which is deliberately in.

    A superseded note opens with a banner naming what replaced it, and the rule it
    established usually outlives the design that prompted it. That is what a record is for.
    """
    from typehaus.cli.cmd_record import _sheets_by_note

    notes = sorted((Path(catlin_model_ro.plan.source_root) / "notes").rglob("*.md"))
    on_sheets = _sheets_by_note(catlin_model_ro)
    assert len(on_sheets) == 6, "exactly six catlin notes are bound to a drawing"
    stems = {p.stem for p in notes} - {"README", "TEMPLATE"}
    files = design_record(_inputs(*[
        NoteSource(f"notes/{p.name}", p.read_text(encoding="utf-8"))
        for p in notes if p.stem not in ("README", "TEMPLATE")]))
    assert stems <= {name.removesuffix(".md") for name in files}
    assert any("superseded" not in n and "balcony_lateral" in n for n in files)
