"""The cover's sheet index as pages: grouping, lettering steps, column grids, pagination.

Pure layout, no drawing state. ``cover_plan`` decides the page count while the sheet list
is built (the continuation sheets G-001.1, G-001.2 … are index entries themselves), and
:func:`draw_index` letters exactly the :class:`IndexPage` it was planned with.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass

from typehaus.emit.draw.typography import wrap_columns_for

#: Lettering pitch for the sheet index, inches per row. 8pt monospace on a 0.135" pitch is
#: the density a real index prints at.
INDEX_PITCH_IN = 0.135

#: Narrowest index column, inches — the width the *column count* is decided against.
INDEX_COLUMN_IN = 2.95

#: Widest index column, inches. Past it the eye stops associating a number with its title.
INDEX_COLUMN_MAX_IN = 6.2

#: Clear space between one index column's text and the next column's number, inches.
INDEX_GUTTER_IN = 0.20

#: Index lettering; the number field is 9 characters plus a separating space.
INDEX_PT = 8.0

#: Longest index column worth printing, rows. Above the cap the list balances across as
#: many columns as the sheet is wide enough to hold.
INDEX_MAX_ROWS = 48

#: The last step before an index paginates: one point smaller, on a tighter pitch. Still
#: above the 6.5 pt of the plans' own tags.
INDEX_TIGHT_PT = 7.0
INDEX_TIGHT_PITCH_IN = 0.118

#: Space under the "SHEET INDEX" heading before the first row, inches.
HEADING_GAP_IN = 0.42

Entry = tuple[str, str]


@dataclass(frozen=True)
class IndexPage:
    """One page's slice of the index and the grid it letters in."""
    entries: tuple[Entry, ...]
    per_column: int
    columns: int
    size_pt: float
    pitch: float
    #: Width of the number field and of the title beside it, characters.
    field: int = 9
    room: int = 80


def fit(text: str, room: int) -> str:
    """``text`` clipped to ``room`` characters, ellipsised so the clip is visible."""
    if room <= 1 or len(text) <= room:
        return text
    return text[:room - 1].rstrip() + "…"


def title_lines(title: str, room: int) -> list[str]:
    """``title`` wrapped to ``room``: a series' distinguishing tag is at its end (D1-107)."""
    if room <= 1:
        return [title]
    return textwrap.wrap(title, room, break_on_hyphens=False) or [""]


def grouped(index: list[Entry]) -> list[Entry]:
    """Continuation and enlarged sub-sheets folded onto their parent's row.

    ``S-602.1`` "(cont.)" and ``A-512.1`` "… · head" carry their parent's title, so their
    numbers join its row ("A-512/.1/.2"). ``A-301.1`` names its own section and keeps one.
    """
    rows: list[tuple[str, str, list[str]]] = []
    for number, title in index:
        if rows:
            head, head_title, parts = rows[-1]
            if number.startswith(head + ".") and title.startswith(head_title):
                parts.append(number[len(head):])
                continue
        rows.append((number, title, []))
    return [("/".join([head, *parts]), title) for head, title, parts in rows]


def expand_numbers(rows: list[Entry]) -> list[str]:
    """The sheet numbers behind printed rows: the inverse of :func:`grouped`'s numbering."""
    out: list[str] = []
    for number, _ in rows:
        head, *parts = number.split("/")
        out.extend([head, *(head + part for part in parts)])
    return out


def place(entries: list[Entry], room: int, per_column: int,
          columns: int) -> list[tuple[int, int, list[str]]]:
    """(column, row, lines) for the leading ``entries`` the grid holds, column-major.

    A wrapped title keeps its lines in one column; the first entry that does not fit
    ends the list.
    """
    out: list[tuple[int, int, list[str]]] = []
    column = row = 0
    for _, title in entries:
        lines = title_lines(title, room)[:per_column]
        if row + len(lines) > per_column:
            column, row = column + 1, 0
        if column >= columns:
            break
        out.append((column, row, lines))
        row += len(lines)
    return out


def _field(entries: list[Entry]) -> int:
    return max([9, *(len(number) for number, _ in entries)])


def _room(width_in: float, columns: int, size_pt: float, field: int) -> int:
    """Title characters in one of ``columns`` columns across ``width_in``."""
    pitch_in = min(INDEX_COLUMN_MAX_IN, width_in / columns)
    return wrap_columns_for(pitch_in - INDEX_GUTTER_IN, size_pt) - (field + 1)


def _max_columns(width_in: float, size_pt: float) -> int:
    return max(1, int(width_in / (INDEX_COLUMN_IN * size_pt / INDEX_PT)))


def _page(entries: list[Entry], rows: int, width_in: float, size_pt: float,
          pitch: float) -> IndexPage:
    """The leading ``entries`` one page of ``rows`` holds.

    When the page holds them all: the fewest columns that do (the least wrapping) under
    :data:`INDEX_MAX_ROWS` if it can, each as short as still holds them, so three columns
    print 33/33/32 rather than 48/48/2. Otherwise the column count that holds the most.
    """
    rows, field = max(1, rows), _field(entries)
    widths = [(c, _room(width_in, c, size_pt, field))
              for c in range(1, _max_columns(width_in, size_pt) + 1)]
    for cap in dict.fromkeys((min(rows, INDEX_MAX_ROWS), rows)):
        for columns, room in widths:
            if len(place(entries, room, cap, columns)) < len(entries):
                continue
            lines = sum(len(title_lines(t, room)[:cap]) for _, t in entries)
            per = next(r for r in range(max(1, -(-lines // columns)), cap + 1)
                       if len(place(entries, room, r, columns)) == len(entries))
            return IndexPage(tuple(entries), per, columns, size_pt, pitch, field, room)
    held, columns, room = max((len(place(entries, room, rows, c)), -c, room)
                              for c, room in widths)
    return IndexPage(tuple(entries[:held]), rows, -columns, size_pt, pitch, field, room)


def paginate(index: list[Entry], *, first_height_in: float, later_height_in: float,
             width_in: float) -> list[IndexPage]:
    """The index as pages: ``first_height_in`` on G-001, ``later_height_in`` on each after.

    One page when any of three steps holds it all: a row per sheet, parts on their parent's
    row, then a point smaller on a tighter pitch. Past that the tight, grouped index flows
    onto continuation pages, each filled before the next. Titles wrap, never clip.
    """
    entries, size_pt, pitch = list(index), INDEX_PT, INDEX_PITCH_IN
    for step in ("rows", "grouped", "tight"):
        if step == "grouped":
            entries = grouped(index)
        elif step == "tight":
            size_pt, pitch = INDEX_TIGHT_PT, INDEX_TIGHT_PITCH_IN
        page = _page(entries, int(first_height_in / pitch), width_in, size_pt, pitch)
        if len(page.entries) == len(entries):
            return [page]
    pages: list[IndexPage] = []
    rest = entries
    while rest:
        rows = int((first_height_in if not pages else later_height_in) / pitch)
        page = _page(rest, rows, width_in, size_pt, pitch)
        if not page.entries:
            raise RuntimeError("sheet index: an entry fits no page")
        pages.append(page)
        rest = rest[len(page.entries):]
    return pages


def draw_index(fig, page: IndexPage, *, x0: float, x1: float, top: float) -> None:
    """Letter ``page`` with its first row at paper-inch height ``top``."""
    width, height = fig.get_size_inches()
    # Spend the leftover width on the columns; a title wraps under itself in its column.
    pitch_in = min(INDEX_COLUMN_MAX_IN, (x1 - x0) / page.columns)
    entries = list(page.entries)
    for (number, _), (column, row, lines) in zip(
            entries, place(entries, page.room, page.per_column, page.columns), strict=True):
        for k, line in enumerate(lines):
            fig.text((x0 + 0.1 + column * pitch_in) / width,
                     (top - (row + k) * page.pitch) / height,
                     f"{number if k == 0 else '':{page.field}} {line}",
                     fontsize=page.size_pt, family="monospace")
