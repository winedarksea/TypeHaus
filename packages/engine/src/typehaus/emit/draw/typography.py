"""Lettering constants and the two unit conversions every writer needs (→ 30 §Details).

A drawing has two coordinate systems and the difference between them is the whole subject of
this module. **Model space** is the building, in inches, at whatever scale the sheet chose.
**Paper space** is the printed page, in inches, at 1:1 — where a title block, a legend and a
notes column live, and where lettering has to end up whatever the drawing's scale is.

Text is the one thing that crosses. A note is not 1.6" *of building*; it is 7 points *of
paper*, and the only reason it was ever written in model inches is that the writers had no
way to say otherwise. That is what ``height_pt`` on the IR text nodes fixes, and this module
is where the sizes it takes come from.

A constant that three modules have to agree on is not three constants — that is why
``CHAR_ASPECT`` lives here rather than duplicated in ``pdf_writer``, ``annotate``, and the
wrap-column code that must match it.

Conversions
-----------
``scale`` throughout is the number ``sheet_writer.ARCH_SCALES`` carries: **paper inches per
model foot**. 1-1/2" = 1'-0" is ``1.5``; 1/4" = 1'-0" is ``0.25``. Not the ratio-denominator
form (8, 48) — one convention, and it is the one the scale ladder and ``select_scale``
already speak.
"""

from __future__ import annotations

#: Monospace advance width as a fraction of cap height. Only ever used to *reserve* room —
#: matplotlib measures the real thing at draw time, and DXF has its own font metrics.
CHAR_ASPECT = 0.62

#: Vertical advance per text line, in multiples of the text height. matplotlib's default is
#: 1.2; the extra air covers descenders and the leader shoulder.
LINE_SPACING = 1.4

#: The legibility floor at 300 dpi. A label that would print smaller than this is drawn at
#: this size instead — a note nobody can read is not a smaller note, it is a missing one.
MIN_PT = 4.0

#: Default printed sizes, points.
TEXT_PT = 7.0          #: general annotation (layer ladders, seed callouts, eave labels)
LEADER_TEXT_PT = 7.0   #: leader notes
DIM_TEXT_PT = 6.5      #: dimension strings — the literal `_draw_dimension` hardcoded
NOTES_PT = 9.0         #: the paper-space notes column
#: Subordinate lines under a primary label — a room block's area and ceiling under its
#: name, and the placeable caption on a trade plan. The ladder above has no genuine
#: *secondary* step: 9 / 7 / 6.5 / 4-floor puts a room's area at 6.5 pt against a 7.0 pt
#: name, which is a rounding difference rather than a hierarchy, so a plan label block read
#: as one undifferentiated paragraph. Deliberately NOT in the vocabulary manifest — the
#: viewer's DetailCanvas draws details, and a detail has no label block to subordinate.
SUB_TEXT_PT = 5.5

#: Columns a long leader note wraps at.
LEADER_WRAP_COLUMNS = 40


def model_in_per_pt(scale: float) -> float:
    """How many *model* inches one printed point covers at ``scale``.

    The conversion the ladder and ``dodge`` need: they reserve space in model inches, and
    what they are really reserving is room for lettering of a fixed printed size. At
    1-1/2" = 1'-0" a 7 pt label is 0.778 model inches — against the 1.6" the ladder
    hardcoded, which is the 2x oversize the details showed.
    """
    return 12.0 / scale / 72.0


def paper_in_per_model_in(scale: float) -> float:
    """The reciprocal — how much paper one model inch takes up."""
    return scale / 12.0


def wrap_columns_for(band_in: float, size_pt: float) -> int:
    """How many monospace characters fit across a ``band_in``-wide paper band at ``size_pt``.

    Wrapping belongs to the writer, at the width it is actually printing into — wrapping
    earlier (in the note loader, at a guessed column count) is what makes the same note
    ragged on a card and square on a sheet.
    """
    if size_pt <= 0.0:
        return 1
    return max(1, int(band_in * 72.0 / (size_pt * CHAR_ASPECT)))
