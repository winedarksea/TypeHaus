"""Tables that flow across continuation sheets at one legible size (S-601, S-602).

``_add_table`` fits a list into a fixed box by shrinking the lettering, down to 3.2 pt, and
S-602 put 120 hardware rows, their basis paragraphs and the solids tables on one ledger
page that way: unreadable, and overprinted where the shrink ran out (C7-E1). Here the
lettering is fixed and the PAGE count is what gives: tables flow top-to-bottom through
side-by-side runs, a run as wide as the table it carries, and what does not fit goes on
the next sheet (``S-602.1``, …). ``page_count`` is the same flow without drawing, which
is how ``build_sheet_index`` numbers the continuation sheets before any page is written.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor

from typehaus.emit.draw.schedules.tables import _n_width, _shorten, _text_width
from typehaus.emit.draw.sheet_writer import section
from typehaus.emit.draw.title_block import content_box

TABLE_PT = 6.0          #: cell lettering — fixed; never shrunk to fit
_ROW_IN = 8.5 / 72.0    #: row pitch
_TITLE_ROWS = 2         #: row slots a table title takes
_TITLE_PT = 8.0
_RUN_GAP_IN = 0.30
_MIN_SPLIT_ROWS = 4     #: fewer rows than this left in a run start the table on the next
_HEADING_CLEAR_IN = 0.45  #: below the sheet heading ``schedule_sheet`` letters at 0.945
_CELL_PAD = 0.1         #: matplotlib ``Cell.PAD``: the left inset, as a fraction of width


@dataclass(frozen=True)
class PagedTable:
    title: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class _Piece:
    table: int
    start: int
    stop: int
    x: float      # paper inches
    top: float
    widths: tuple[float, ...]


def continuation_number(number: str, page: int) -> str:
    """``S-602`` for the first page, then ``S-602.1``, ``S-602.2`` …"""
    return number if page == 0 else f"{number}.{page}"


def page_count(tables: list[PagedTable], size: tuple[float, float]) -> int:
    return max(1, len(_paginate(tables, size)))


def draw_page(fig, tables: list[PagedTable], size: tuple[float, float], page: int,
              next_number: str | None = None) -> None:
    """Draw page ``page`` of the flow; ``next_number`` letters a continuation note."""
    pages = _paginate(tables, size)
    if page >= len(pages):
        return
    width, height = size
    for piece in pages[page]:
        table = tables[piece.table]
        title = table.title + (" (CONT.)" if piece.start else "")
        section(fig, piece.x / width, piece.top / height, title, fontsize=_TITLE_PT,
                va="top")
        rows = [_fit_row(row, piece.widths) for row in table.rows[piece.start:piece.stop]]
        table_h = (len(rows) + 1) * _ROW_IN
        bottom = piece.top - _TITLE_ROWS * _ROW_IN - table_h
        total = sum(piece.widths)
        ax = fig.add_axes((piece.x / width, bottom / height, total / width, table_h / height))
        ax.axis("off")
        drawn = ax.table(cellText=rows, colLabels=table.columns, cellLoc="left",
                         colLoc="left", colWidths=[w / total for w in piece.widths],
                         bbox=(0.0, 0.0, 1.0, 1.0))
        drawn.auto_set_font_size(False)
        drawn.set_fontsize(TABLE_PT)
    if next_number and page < len(pages) - 1:
        x0, y0, _x1, _y1 = _band(size)
        section(fig, x0 / width, (y0 - 0.05) / height,
                f"SCHEDULE CONTINUES ON {next_number}", fontsize=_TITLE_PT, va="top")


def _band(size: tuple[float, float]) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = content_box(size)
    return x0, y0 + _ROW_IN * 2, x1, min(y1, 0.945 * size[1] - _HEADING_CLEAR_IN)


def _text_in(text: str) -> float:
    return _text_width(text) * _n_width() * TABLE_PT / 10.0 / 72.0


def _widths(table: PagedTable, room: float) -> tuple[float, ...]:
    """Column widths, paper inches, from the widest cell — over the WHOLE table, so a table
    split across runs or sheets keeps one set of columns. Squeezed to ``room`` if wider."""
    widths = []
    for index, label in enumerate(table.columns):
        cells = {label, *(str(row[index]) for row in table.rows if index < len(row))}
        widest = max(_text_in(text) for text in sorted(cells, key=len, reverse=True)[:4])
        widths.append((widest + 2.5 / 72.0) / (1.0 - _CELL_PAD))
    total = sum(widths)
    return tuple(w * min(1.0, room / total) for w in widths)


def _fit_row(row: tuple[str, ...], widths: tuple[float, ...]) -> tuple[str, ...]:
    """Cells shortened to their column, which only bites on a table squeezed to the page."""
    unit = _n_width() * TABLE_PT / 10.0 / 72.0
    return tuple(_shorten(str(cell), width * (1.0 - _CELL_PAD) / unit - 0.5)
                 for cell, width in zip(row, widths, strict=False))


def _paginate(tables: list[PagedTable], size: tuple[float, float]) -> list[list[_Piece]]:
    x0, y0, x1, top = _band(size)
    slots_per_run = floor((top - y0) / _ROW_IN)
    pages: list[list[_Piece]] = []
    page: list[_Piece] = []
    x, run_w, slots = x0, 0.0, 0
    for index, table in enumerate(tables):
        if not table.rows:
            continue
        widths = _widths(table, x1 - x0)
        width = sum(widths)
        start = 0
        while start < len(table.rows):
            remaining = len(table.rows) - start
            need = _TITLE_ROWS + 1 + min(_MIN_SPLIT_ROWS, remaining)
            if not run_w or width > run_w + 1e-6 or slots < need:
                x = x + run_w + _RUN_GAP_IN if run_w else x0
                if x + width > x1 + 1e-6 and page:
                    pages.append(page)
                    page, x = [], x0
                run_w, slots = width, slots_per_run
            take = max(1, min(remaining, slots - _TITLE_ROWS - 1))
            used = _TITLE_ROWS + 1 + take
            page.append(_Piece(index, start, start + take, x,
                               top - (slots_per_run - slots) * _ROW_IN, widths))
            slots -= used + 1  # a blank row before the next table in this run
            start += take
    if page:
        pages.append(page)
    return pages
