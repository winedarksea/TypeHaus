"""Column layout for the note-block sheets (G-002, S-001, A-002).

Extracted from ``schedules/architectural.py``, which had outgrown the 500-line rule and
was the only owner of a routine three sheets need. Nothing here knows what a block *says*
— a block is a title and a list of already-formatted lines, and the whole of this module's
job is deciding which column it lands in and reporting what did not fit.
"""

from __future__ import annotations

from typehaus.emit.draw.sheet_writer import section

#: The four columns a note sheet lays out into, as figure-fraction left edges, and the band
#: they run between. Measured off the composed sheet, which is why they are here and not
#: guessed.
_NOTE_COLUMNS_X = (0.03, 0.275, 0.52, 0.765)
_NOTE_BAND = (0.90, 0.115)
_NOTE_STEP = 0.011


def _lay_out_blocks(fig, blocks: list[tuple[str, list[str]]]) -> int:
    """Lay blocks into four columns; return how many did NOT fit.

    The old loop ``break``ed out of both levels when it ran out of column and dropped
    everything after, including the remainder of the block it was mid-way through. This one
    never splits a block across a column boundary and never drops one silently — it counts
    what it could not place and hands the count back to be printed on the sheet.
    """
    top, bottom = _NOTE_BAND
    column, y = 0, top
    dropped = 0
    for title, lines in blocks:
        needed = (len(lines) + 2) * _NOTE_STEP
        if y - needed < bottom and y < top:
            column, y = column + 1, top
        if column >= len(_NOTE_COLUMNS_X):
            dropped += 1
            continue
        x = _NOTE_COLUMNS_X[column]
        section(fig, x, y, title, fontsize=7, va="top")
        y -= _NOTE_STEP * 1.6
        for line in lines:
            fig.text(x, y, line, fontsize=6, family="monospace", va="top")
            y -= _NOTE_STEP
        y -= _NOTE_STEP
    return dropped
