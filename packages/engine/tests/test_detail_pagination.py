"""Notes paginate; they do not truncate, and they do not move the drawing (→ 30 §Details).

With the lettering fixed by definition, a note column that does not fit has exactly two
honest outcomes: shrink the type until nobody can read it, or print another page. The
behaviour this replaces was a third — silently dropping the tail of a permit set's
construction notes.

Catlin *was* the live two-page case: its eave carried 108 bullets of design rationale.
Since the note files split into sheet notes and a design record it is not, and no catlin
detail is — which is the objective, and is why the overflow case below is manufactured on
a real card rather than found on one.
"""

from __future__ import annotations

import pytest

from typehaus.emit.draw.detail_card import NOTES_W_IN, card_for_crop
from typehaus.emit.draw.pdf_writer import note_pages
from typehaus.emit.draw.typography import NOTES_PT, wrap_columns_for

_NARROW = (5.0, 0.5, NOTES_W_IN, 6.4)
_WIDE = (0.5, 0.5, 10.0, 6.6)


_BULLET = ("a bullet about something in the wall that runs on well past any one column's "
           "measure so that both bands have to wrap it")


def _lines(count: int, text: str = _BULLET) -> tuple[str, ...]:
    return tuple(f"• {i} {text}" for i in range(count))


def test_every_line_reaches_a_page():
    """The property that matters. Nothing is dropped, at any length."""
    for count in (1, 5, 40, 200, 1000):
        notes = _lines(count)
        pages = note_pages(notes, _NARROW)
        placed = [line for page in pages for column in page for line in column]
        # Wrapping splits lines, so compare the *content*: every bullet's first words survive.
        joined = " ".join(placed)
        for note in notes:
            assert note.split(" ")[1] in joined


def test_a_bullet_is_never_split_across_pages():
    """Pages break between logical lines, which is why each page can re-wrap to its own band."""
    notes = _lines(60)
    pages = note_pages(notes, _NARROW)
    assert len(pages) > 1
    for page in pages:
        first = next(line for column in page for line in column)
        assert first.startswith("• "), "a page opened mid-bullet"


def test_a_continuation_page_wraps_to_its_own_wider_band():
    """The reason wrapping had to leave the note loader.

    ``Scene.notes`` is logical lines, so page 2 on a full-width sheet gets full-width lines
    instead of inheriting page 1's narrow column. Pre-wrapping at a guessed 42 columns made
    that impossible, and ``pdf_writer._rewrap_notes`` existed to paper over it.
    """
    pages = note_pages(_lines(80), _NARROW, _WIDE)
    assert len(pages) > 1
    narrow = max(len(line) for line in pages[0][0])
    wide = max(len(line) for column in pages[1] for line in column)
    assert wide > narrow * 1.4
    assert wide <= wrap_columns_for((10.0 - 0.25) / 2, NOTES_PT)


def test_a_wide_band_lays_out_in_columns():
    """A 10-inch band is two 3.4" columns, not one 10-inch line of 9 pt monospace."""
    pages = note_pages(_lines(80), _WIDE)
    assert len(pages[0]) == 2, "the wide band did not split into columns"


def test_no_notes_is_no_pages():
    assert note_pages((), _NARROW) == []


def test_a_card_that_outgrows_its_band_gets_a_second_page(catlin_model):
    """The behaviour this module exists for, on a real card with synthetic notes.

    It used to read the catlin eave, which carried 108 bullets of design rationale and
    needed two pages to print them. That is no longer true and should not be: the eave's
    notes are now 46 rows of the band's 48, because the rationale moved below `# Notes`
    and stopped being drawing content (``emit/draw/sheet_notes.py``). A house whose
    details each fit one page is the objective, not a reason to delete the pagination —
    so the *card* stays real and the overflow is manufactured.
    """
    from typehaus.emit.draw.details import build_detail, derive_detail_slices

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF")
    scene, _ = build_detail(catlin_model, derived)
    band = scene.frame.bands["notes"]
    assert len(note_pages(scene.notes, band)) == 1, \
        "a migrated detail's notes fit one page"
    assert len(note_pages(tuple(scene.notes) + _lines(200), band)) > 1, \
        "notes that outgrow the band paginate rather than truncate"


def test_the_notes_are_logical_lines_not_pre_wrapped(catlin_model):
    """One string per bullet. Wrapping is the writer's, at the width it prints into.

    The property is about the *source's* hard wraps, not length. A note file wraps at
    column 100 for its own readability, and until ``note_text.logical_bullets`` landed,
    each physical line became a separate ``Scene.notes`` entry — so a sentence broke
    mid-clause on the sheet, at a column nothing on the sheet had.

    This used to assert "some bullet is over 100 characters", which was a proxy for the
    same thing and stopped being one: a migrated note file is authored in short imperative
    notes, so every bullet is legitimately short now. The fragment test below is the
    property that was always meant.
    """
    from typehaus.emit.draw.details import build_detail, derive_detail_slices

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF")
    scene, _ = build_detail(catlin_model, derived)
    bullets = [line for line in scene.notes if line.startswith("• ")]
    assert bullets
    assert not [line for line in scene.notes if line.startswith("  ")], \
        "continuation lines are a wrapped artefact and must not be in the IR"
    # A source hard wrap resumed mid-sentence, so the continuation opened lowercase or on
    # a bare punctuation mark. Every bullet is now a whole authored bullet.
    fragments = [b for b in bullets if b[2:3].islower() or b[2:3] in ",;)"]
    assert not fragments, f"source hard wraps reached the IR: {fragments[:2]}"


def test_no_markdown_or_repository_path_reaches_the_notes(catlin_model):
    """The acceptance property, at the one detail with the most note text."""
    from typehaus.emit.draw.details import build_detail, derive_detail_slices

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF")
    scene, _ = build_detail(catlin_model, derived)
    joined = "\n".join(scene.notes)
    for artefact in ("**", "`", "](", ".md", ".py", "::"):
        assert artefact not in joined, f"{artefact!r} printed onto a permit sheet"


def test_pagination_does_not_touch_the_drawing(catlin_model):
    """The acceptance test from the plan, at the card level."""
    from typehaus.emit.draw.details import build_detail, derive_detail_slices

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF")
    scene, _ = build_detail(catlin_model, derived)
    longer = scene.model_copy(update={"notes": scene.notes + _lines(500)})
    assert longer.frame == scene.frame
    assert len(note_pages(longer.notes, longer.frame.bands["notes"])) > \
        len(note_pages(scene.notes, scene.frame.bands["notes"]))


@pytest.mark.parametrize("span", [(24.0, 30.0), (96.0, 24.0), (400.0, 300.0)])
def test_a_card_always_leaves_its_notes_a_band(span):
    frame = card_for_crop(span[0], span[1], (0.0, 0.0))
    band = frame.bands["notes"]
    assert band[2] >= NOTES_W_IN - 1e-9
    assert band[3] > 1.0
