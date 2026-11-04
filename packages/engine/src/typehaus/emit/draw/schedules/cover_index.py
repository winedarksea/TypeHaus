"""The cover's sheet index as pages: grouping, lettering steps, column grids, pagination.

Pure layout, no drawing state. ``cover_plan`` decides the page count while the sheet list
is built (the continuation sheets G-001.1, G-001.2 … are index entries themselves), and
:func:`draw_index` letters exactly the :class:`IndexPage` it was planned with.
"""

from __future__ import annotations

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


def fit(text: str, room: int) -> str:
    """``text`` clipped to ``room`` characters, ellipsised so the clip is visible."""
    if room <= 1 or len(text) <= room:
        return text
    return text[:room - 1].rstrip() + "…"


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


def index_shape(entries: int, *, rows: int, columns: int) -> tuple[int, int]:
    """(rows per column, columns) for ``entries`` lines in a ``rows`` x ``columns`` grid.

    Cap a column at :data:`INDEX_MAX_ROWS`, then **balance**: three columns needed prints
    33/33/32, not 48/48/2, which would look truncated. The grid is a hard bound: callers
    paginate what it cannot hold.
    """
    if entries <= 0:
        return (1, 1)
    per_column = min(rows, INDEX_MAX_ROWS)
    needed = -(-entries // per_column)  # ceil
    columns = max(1, min(needed, columns))
    return (min(rows, -(-entries // columns)), columns)


def _grid(count: int, rows: int, width_in: float, size_pt: float, pitch: float,
          entries: list[Entry]) -> IndexPage:
    """``entries`` (at most the capacity) in a grid of ``rows`` x the columns ``width_in`` holds."""
    per_column, columns = index_shape(
        count, rows=max(1, rows),
        columns=max(1, int(width_in / (INDEX_COLUMN_IN * size_pt / INDEX_PT))))
    return IndexPage(tuple(entries), per_column, columns, size_pt, pitch)


def paginate(index: list[Entry], *, first_height_in: float, later_height_in: float,
             width_in: float) -> list[IndexPage]:
    """The index as pages: ``first_height_in`` on G-001, ``later_height_in`` on each after.

    One page when any of three steps holds it all: a row per sheet, parts on their parent's
    row, then a point smaller on a tighter pitch. Past that the tight, grouped index flows
    onto continuation pages, each filled before the next.
    """
    entries, size_pt, pitch = list(index), INDEX_PT, INDEX_PITCH_IN
    for step in ("rows", "grouped", "tight"):
        if step == "grouped":
            entries = grouped(index)
        elif step == "tight":
            size_pt, pitch = INDEX_TIGHT_PT, INDEX_TIGHT_PITCH_IN
        page = _grid(len(entries), int(first_height_in / pitch), width_in, size_pt, pitch,
                     entries)
        if page.per_column * page.columns >= len(entries):
            return [page]
    pages: list[IndexPage] = []
    rest = entries
    while rest:
        rows = int((first_height_in if not pages else later_height_in) / pitch)
        columns = max(1, int(width_in / (INDEX_COLUMN_IN * size_pt / INDEX_PT)))
        capacity = max(1, rows) * columns
        take, rest = rest[:capacity], rest[capacity:]
        pages.append(_grid(len(take), rows, width_in, size_pt, pitch, take))
    return pages


def draw_index(fig, page: IndexPage, *, x0: float, x1: float, top: float) -> None:
    """Letter ``page`` with its first row at paper-inch height ``top``."""
    width, height = fig.get_size_inches()
    # Spend the leftover width on the columns, and fit each title to its column or it runs
    # through the next column's number.
    pitch_in = min(INDEX_COLUMN_MAX_IN, (x1 - x0) / page.columns)
    field = max([9, *(len(number) for number, _ in page.entries)])
    room = wrap_columns_for(pitch_in - INDEX_GUTTER_IN, page.size_pt) - (field + 1)
    for row, (number, name) in enumerate(page.entries):
        column, line = divmod(row, page.per_column)
        fig.text((x0 + 0.1 + column * pitch_in) / width,
                 (top - line * page.pitch) / height,
                 f"{number:{field}} {fit(name, room)}",
                 fontsize=page.size_pt, family="monospace")
