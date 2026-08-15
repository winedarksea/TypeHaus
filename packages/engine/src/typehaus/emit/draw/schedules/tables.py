"""Matplotlib table layout for the schedule sheets — widths, fitting, truncation.

Everything here answers one question the sheet writers should not have to: given a box
on a page and a list of rows, how wide is each column and what does not fit. The sheets
above only say *what* to tabulate.

Widths are measured, not counted. A character count is not a width — see ``_text_width``
and ``_column_weights`` below for what that difference costs.
"""

from __future__ import annotations

from functools import lru_cache

# Column-width clamps, in lowercase-"n" widths of the table face. Below the floor a short
# header ("V", "Qty") loses its own label; above the cap one prose column ("Locations",
# "Basis") starves every number beside it. Both were read off E-602, the widest sheet in
# the set. The pad covers matplotlib's inset of cell text from the rule, which measuring
# the string alone does not see.
_MIN_COL_W = 5.0
_MAX_COL_W = 52.0
_COL_PAD_W = 2.5
_WIDTH_SAMPLE = 4  # longest cells per column actually measured


@lru_cache(maxsize=65536)
def _text_width(text: str) -> float:
    """Rendered width of ``text`` in the table face, in lowercase-"n" widths.

    Measured, not estimated. A character count is not a width — a column of uppercase
    element tags ("RM-M-BATH1, RM-S-SUITEBATH") runs ~35% wider than the same count of
    mixed-case prose, and an estimate that was wrong in that direction is what let
    E-602's last column run off the sheet. Cached because a schedule repeats its tags.
    """
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath

    if not text:
        return 0.0
    prop = FontProperties(size=10)
    return TextPath((0, 0), text, prop=prop).get_extents().width / _n_width()


@lru_cache(maxsize=1)
def _n_width() -> float:
    """Width of a lowercase "n" in the table face — the unit the clamps above are in."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath

    return TextPath((0, 0), "nnnnnnnnnn", prop=FontProperties(size=10)).get_extents().width / 10.0


def _column_weights(rows: list[tuple], col_labels: tuple[str, ...]) -> list[float]:
    """Relative column widths, from the widest cell each column actually holds.

    matplotlib gives every column an equal share of the table, so a 44-character room
    list and a 3-character voltage got the same inch. The long cell then drew past its
    own boundary and was painted over by the next column's background — or, in the last
    column, ran straight off the sheet edge, which is what clipped E-602's "Locations".
    Sizing by content is the fix; ``cellLoc="left"`` means the overflow is always to the
    right, so shrinking the lettering would never have recovered it.
    """
    weights = []
    for index, label in enumerate(col_labels):
        cells = [str(label)] + [str(row[index]) for row in rows if index < len(row)]
        # Measuring every cell costs more than the layout is worth on a 900-row schedule.
        # Character count ranks candidates well enough *within* one column — the alphabet
        # does not change down a column — so only the longest few are actually measured.
        candidates = sorted(set(cells), key=len, reverse=True)[:_WIDTH_SAMPLE]
        widest = max(_text_width(text) for text in candidates)
        weights.append(min(max(widest, _MIN_COL_W), _MAX_COL_W) + _COL_PAD_W)
    total = sum(weights)
    return [w / total for w in weights]


def _shorten(text: str, budget: float) -> str:
    """``text`` cut to ``budget`` n-widths on a list-item boundary, with the count kept.

    A hard character slice produced "RM-A-STUDY, RM-M-STUDY, RM-S-PLANT, RM-S-STU": a
    truncation the reader cannot see is a truncation, and a half-written tag reads as a
    tag that does not exist. Say how many were dropped instead. Only called for columns
    the caller marked truncatable, and only once the layout knows the width the column
    actually got — which is why it lives here and not at the call site.
    """
    if _text_width(text) <= budget:
        return text
    items = text.split(", ")
    kept: list[str] = []
    for index, item in enumerate(items):
        dropped = len(items) - index - 1
        tail = f" +{dropped} more" if dropped else ""
        if kept and _text_width(", ".join([*kept, item]) + tail) > budget:
            break
        kept.append(item)
    if not kept:  # a single item wider than the whole column
        return items[0]
    dropped = len(items) - len(kept)
    return ", ".join(kept) + (f" +{dropped} more" if dropped else "")


def _fit_cells(rows: list[tuple], col_widths: list[float], table_pt: float,
               font_pt: float, truncate: tuple[int, ...]) -> list[tuple]:
    """Shorten the truncatable columns to the width they were actually allotted.

    Two pads, not one: matplotlib insets the cell text from both rules, so a budget that
    subtracts only the left inset leaves the last character sitting on the right one.
    """
    unit_pt = _n_width() * font_pt / 10.0  # one n-width at the size this table prints at
    out = []
    for row in rows:
        cells = list(row)
        for index in truncate:
            if index < len(cells):
                budget = col_widths[index] * table_pt / unit_pt - 2 * _COL_PAD_W
                cells[index] = _shorten(str(cells[index]), budget)
        out.append(tuple(cells))
    return out


def _add_table(fig, rows: list[tuple], col_labels: tuple[str, ...],
               bbox: tuple[float, float, float, float],
               truncate: tuple[int, ...] = ()) -> None:
    """Contained tables: matplotlib's default rows are font-height-sized and spill past a
    short axes (the ledger page is 11" tall where the old portrait pages had 14-17").
    An explicit table bbox compresses rows to fit; a list too long for the box at legible
    lettering is split into two side-by-side runs, and the font tracks the row height.
    Column widths follow the content (→ ``_column_weights``); they are computed over the
    full row list so a split table's two runs stay aligned with each other."""
    if not rows:
        return
    col_widths = _column_weights(rows, col_labels)
    height_pt = bbox[3] * fig.get_size_inches()[1] * 72.0
    capacity = max(4, int(height_pt / 7.5) - 1)  # rows that stay legible at ~6pt
    chunks = [rows]
    if len(rows) > capacity and len(rows) >= 8:
        half = (len(rows) + 1) // 2
        chunks = [rows[:half], rows[half:]]
    gap = 0.02
    width = (bbox[2] - gap * (len(chunks) - 1)) / len(chunks)
    for column, chunk in enumerate(chunks):
        ax = fig.add_axes((bbox[0] + column * (width + gap), bbox[1], width, bbox[3]))
        ax.axis("off")
        n = len(chunk) + 1  # + header row
        frac = min(1.0, n * 11.0 / height_pt)  # 11pt rows until the box is full
        row_pt = height_pt * frac / n
        font_pt = max(3.2, min(6.0, row_pt * 0.72))
        if truncate:
            chunk = _fit_cells(chunk, col_widths,
                               width * fig.get_size_inches()[0] * 72.0, font_pt, truncate)
        table = ax.table(cellText=chunk, colLabels=col_labels, cellLoc="left",
                         colLoc="left", colWidths=col_widths,
                         bbox=(0.0, 1.0 - frac, 1.0, frac))
        # ``fontsize=`` via ax.table does not stop the per-cell auto-shrink, which
        # crushes any run containing one wide cell; pin the size explicitly.
        table.auto_set_font_size(False)
        table.set_fontsize(font_pt)


def _number(value: object, fmt: str) -> str:
    """A stated number in ``fmt``, or an em dash — never a plausible-looking zero."""
    return fmt.format(value) if isinstance(value, (int, float)) else ""
