"""Notes paginate; they do not truncate, and they do not move the drawing (→ 30 §Details).

With the lettering fixed by definition, a note column that does not fit has exactly two
honest outcomes: shrink the type until nobody can read it, or print another page. The
behaviour this replaces was a third — silently dropping the tail of a permit set's
construction notes. Catlin's eave is a live two-page case at 108 bullets.
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


def test_the_catlin_eave_is_a_two_page_detail(catlin_model):
    from typehaus.emit.draw.details import build_detail, derive_detail_slices

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF")
    scene, _ = build_detail(catlin_model, derived)
    band = scene.frame.bands["notes"]
    assert len(note_pages(scene.notes, band)) > 1, \
        "this detail is the case the pagination exists for"


def test_the_notes_are_logical_lines_not_pre_wrapped(catlin_model):
    """One string per bullet. Wrapping is the writer's, at the width it prints into."""
    from typehaus.emit.draw.details import build_detail, derive_detail_slices

    derived = next(d for d in derive_detail_slices(catlin_model)
                   if d.key == "wall_roof:CATLIN_EXT_2X6|CATLIN_ROOF")
    scene, _ = build_detail(catlin_model, derived)
    bullets = [line for line in scene.notes if line.startswith("• ")]
    assert bullets
    assert max(len(line) for line in bullets) > 100, \
        "notes arrived pre-wrapped; the writer can no longer choose its own column"
    assert not [line for line in scene.notes if line.startswith("  ")], \
        "continuation lines are a wrapped artefact and must not be in the IR"


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
