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


# --- paged layout (S-001 and its continuations) ---------------------------------------
# ``_lay_out_blocks`` lays one page in figure fractions and clips nothing, so a line longer
# than its column ran into the next one and a block taller than the band ran off the sheet
# (S-001's anchorage block, C7-E1). The paged layout works in paper inches: lines wrap to
# the column's own measure, a block taller than what is left of a column continues in the
# next one, and what does not fit the sheet goes on ``S-001.1``.

NOTE_PT = 6.0
_NOTE_TITLE_PT = 7.0
_LINE_IN = NOTE_PT * 1.45 / 72.0
_MIN_COLUMN_IN = 4.0
_COLUMN_GAP_IN = 0.25
_HEADING_CLEAR_IN = 0.45
_MIN_SPLIT_LINES = 4

#: One placed line: (column, row, text, is_title).
PlacedLine = tuple[int, int, str, bool]


def _note_geometry(size: tuple[float, float]) -> tuple[float, float, float, int, int]:
    """(x0, top, column pitch, columns, lines per column) for ``size``, paper inches."""
    from typehaus.emit.draw.title_block import content_box

    x0, y0, x1, y1 = content_box(size)
    top = min(y1, 0.945 * size[1] - _HEADING_CLEAR_IN)
    columns = max(1, int((x1 - x0 + _COLUMN_GAP_IN) // (_MIN_COLUMN_IN + _COLUMN_GAP_IN)))
    pitch = (x1 - x0 + _COLUMN_GAP_IN) / columns
    return x0, top, pitch, columns, int((top - y0) // _LINE_IN)


def _wrap_line(line: str, columns: int) -> list[str]:
    """Wrap to ``columns`` characters with a hanging indent: under a ``_row`` value, or two
    spaces past the line's own indent."""
    import re
    import textwrap

    if len(line) <= columns:
        return [line]
    lead = len(line) - len(line.lstrip())
    row = re.match(r"^\S.{0,28}?\s{2,}(?=\S)", line)
    indent = row.end() if row and row.end() < columns // 2 else lead + 2
    return textwrap.wrap(line, columns, subsequent_indent=" " * indent,
                         break_on_hyphens=False) or [line]


def paginate_note_blocks(blocks: list[tuple[str, list[str]]], size: tuple[float, float],
                         ) -> list[list[PlacedLine]]:
    """Every page's placed lines. Never empty: an empty sheet is still one page."""
    from typehaus.emit.draw.typography import wrap_columns_for

    _x0, _top, pitch, columns, per_column = _note_geometry(size)
    measure = wrap_columns_for(pitch - _COLUMN_GAP_IN, NOTE_PT)
    pages: list[list[PlacedLine]] = [[]]
    column, row = 0, 0

    def next_column() -> None:
        nonlocal column, row
        column, row = column + 1, 0
        if column >= columns:
            pages.append([])
            column = 0

    for title, lines in blocks:
        body = [part for line in lines for part in _wrap_line(line, measure)]
        first = True
        while first or body:
            left = per_column - row
            whole = len(body) + 2
            if row and (whole > left and (whole <= per_column or left < _MIN_SPLIT_LINES + 2)):
                next_column()
                left = per_column
            heading = title if first else f"{title} (CONT.)"
            pages[-1].append((column, row, heading, True))
            take = body[:max(1, left - 2)]
            for offset, text in enumerate(take, start=1):
                pages[-1].append((column, row + offset, text, False))
            body = body[len(take):]
            row += len(take) + 2  # the title line, then a blank line after the block
            first = False
            if body:
                next_column()
    return pages


def draw_note_page(fig, page: list[PlacedLine], size: tuple[float, float]) -> None:
    from typehaus.emit.draw.sheet_writer import section

    x0, top, pitch, _columns, _per = _note_geometry(size)
    width, height = size
    for column, row, text, is_title in page:
        x, y = (x0 + column * pitch) / width, (top - row * _LINE_IN) / height
        if is_title:
            section(fig, x, y, text, fontsize=_NOTE_TITLE_PT, va="top")
        else:
            fig.text(x, y, text, fontsize=NOTE_PT, family="monospace", va="top")
