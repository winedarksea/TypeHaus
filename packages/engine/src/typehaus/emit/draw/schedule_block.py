"""Keyed schedule + note blocks drawn straight into the drawing IR (→ 20 §Drawing IR).

A permit structural sheet is a plan *plus* its schedules: the plan carries marks (F1, J1,
B2 …) and the schedule resolves each mark to a size, span, and bearing. Composing the table
as IR ``Text``/``Polyline`` — instead of a matplotlib table on the page — keeps S-100/S-101
pure ``Scene`` builders, so the PDF and DXF writers both get the schedule for free and the
marks stay in the same model-space coordinate system as the members they key.

One ``Text`` node per *row*, space-padded in a monospace face, rather than one per cell: the
writers size lettering from a model-space height, and the effective height they land on
depends on how the sheet ends up fitted to the page. Padding inside a single string keeps
columns aligned under any such fit, which per-cell x-offsets cannot promise.

All metrics are model-space inches (the IR unit, → scene.py), because the block is drawn
beside the plan at plan scale rather than in paper space.
"""

from __future__ import annotations

import textwrap
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from itertools import combinations

from typehaus.emit.draw.scene import Polyline, SceneBuilder, Text
from typehaus.emit.draw.typography import CHAR_ASPECT, LEADER_WRAP_COLUMNS

# Lettering and rhythm of a schedule block, model-space inches at the scale of a plan whose
# longest side is REFERENCE_PLAN_EXTENT_IN. A bigger building is drawn smaller on the same
# sheet, so the block's metrics scale with the plan (``metrics_for``).
SCHEDULE_TEXT_HEIGHT_IN = 3.0
SCHEDULE_TITLE_HEIGHT_IN = 4.5
# Rows sit well over one text height apart: the writers round lettering up to a legible
# minimum point size, so a pitch equal to the nominal height would collide once rounded.
SCHEDULE_ROW_PITCH_IN = 9.0
SCHEDULE_TITLE_PITCH_IN = 14.0
SCHEDULE_BLOCK_GAP_IN = 30.0  # vertical air between two stacked blocks
SCHEDULE_COLUMN_GAP_SPACES = 2
REFERENCE_PLAN_EXTENT_IN = 360.0  # a 30-foot plan: the scale these constants are drawn at
# Used here only to size the table's underscore rules; ``typography`` owns the ratio, and
# ``LEADER_WRAP_COLUMNS`` (a leader note is read beside the thing it points at, so it wraps
# much narrower than a sheet note) comes from there too.
CHARACTER_WIDTH_RATIO = CHAR_ASPECT
# Long notes wrap at a sheet-note measure rather than running off the drawing.
NOTE_WRAP_COLUMNS = 96

# Width / height of a permit-sheet drawing viewport, near enough. Both papers the set can
# print on land close to this (35.30 x 22.25 on ARCH D, 16.30 x 9.25 on ledger), and the
# column reflow only needs to know the *shape* of the hole it is filling, not the size:
# ``select_scale`` takes the largest scale at which both spans fit, so the arrangement that
# prints biggest is the one whose bounding box is closest to this proportion.
SHEET_VIEWPORT_ASPECT = 1.6
# A schedule stack reflowed past this many columns stops reading as a schedule and starts
# reading as a wall of tables; it also bounds the split enumeration below.
MAX_SCHEDULE_COLUMNS = 4

# AIA annotation layers: the table rules are a table, the lettering is text.
SCHEDULE_GRID_LAYER = "A-ANNO-TABL"
SCHEDULE_TEXT_LAYER = "A-ANNO-TEXT"
MARK_TEXT_HEIGHT_IN = 2.5


@dataclass(frozen=True)
class ScheduleTable:
    """One keyed schedule: a title, column headers, and already-formatted string rows."""

    title: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class NoteBlock:
    """A titled, numbered list of sheet notes — the other thing a schedule column stacks."""

    title: str
    notes: tuple[str, ...]


#: What a schedule column may contain. Both kinds measure and draw through the same pair
#: (:func:`block_extent`, :func:`emit_block`), which is what lets the reflow treat a stack
#: of mixed tables and notes as one sequence of boxes.
ScheduleBlock = ScheduleTable | NoteBlock


@dataclass(frozen=True)
class BlockMetrics:
    """Lettering and rhythm for one sheet's blocks, in model-space inches."""

    text_height: float = SCHEDULE_TEXT_HEIGHT_IN
    title_height: float = SCHEDULE_TITLE_HEIGHT_IN
    row_pitch: float = SCHEDULE_ROW_PITCH_IN
    title_pitch: float = SCHEDULE_TITLE_PITCH_IN
    block_gap: float = SCHEDULE_BLOCK_GAP_IN
    mark_height: float = MARK_TEXT_HEIGHT_IN


def metrics_for(points: list[tuple[float, float]]) -> BlockMetrics:
    """Scale the block metrics to the drawing they sit beside (never below 1:1)."""
    if not points:
        return BlockMetrics()
    span = max(max(p[0] for p in points) - min(p[0] for p in points),
               max(p[1] for p in points) - min(p[1] for p in points))
    factor = max(1.0, span / REFERENCE_PLAN_EXTENT_IN)
    return BlockMetrics(
        text_height=SCHEDULE_TEXT_HEIGHT_IN * factor,
        title_height=SCHEDULE_TITLE_HEIGHT_IN * factor,
        row_pitch=SCHEDULE_ROW_PITCH_IN * factor,
        title_pitch=SCHEDULE_TITLE_PITCH_IN * factor,
        block_gap=SCHEDULE_BLOCK_GAP_IN * factor,
        mark_height=MARK_TEXT_HEIGHT_IN * factor,
    )


def emit_schedule_table(b: SceneBuilder, table: ScheduleTable, origin: tuple[float, float],
                        metrics: BlockMetrics) -> float:
    """Draw one schedule table with its top-left at ``origin``; return its bottom y.

    Returning the bottom lets a sheet stack several blocks without any caller re-measuring
    text — the same "the writer never re-measures" contract the rest of the IR follows.
    """
    x0, y0 = origin
    if not table.rows:
        return y0
    widths = _column_widths(table)
    header = _pad_row(table.columns, widths)
    rule_width = len(header) * metrics.text_height * CHARACTER_WIDTH_RATIO

    b.add(Text(anchor=(x0, y0), content=table.title, height=metrics.title_height,
               layer=SCHEDULE_TEXT_LAYER))
    row_y = y0 - metrics.title_pitch
    b.add(Text(anchor=(x0, row_y), content=header, height=metrics.text_height,
               layer=SCHEDULE_TEXT_LAYER))
    row_y -= metrics.row_pitch / 2.0
    _rule(b, x0, row_y, rule_width)
    for row in table.rows:
        row_y -= metrics.row_pitch
        b.add(Text(anchor=(x0, row_y), content=_pad_row(row, widths),
                   height=metrics.text_height, layer=SCHEDULE_TEXT_LAYER))
    bottom_y = row_y - metrics.row_pitch / 2.0
    _rule(b, x0, bottom_y, rule_width)
    return bottom_y


def emit_note_block(b: SceneBuilder, title: str, notes: list[str],
                    origin: tuple[float, float], metrics: BlockMetrics) -> float:
    """Draw a titled, numbered list of general notes; return its bottom y."""
    x0, y0 = origin
    if not notes:
        return y0
    b.add(Text(anchor=(x0, y0), content=title, height=metrics.title_height,
               layer=SCHEDULE_TEXT_LAYER))
    row_y = y0 - metrics.title_pitch
    for line in _note_lines(notes):
        b.add(Text(anchor=(x0, row_y), content=line, height=metrics.text_height,
                   layer=SCHEDULE_TEXT_LAYER))
        row_y -= metrics.row_pitch
    return row_y


def wrap_leader_text(text: str) -> str:
    """Fold a long callout into a short stack of lines so it does not cross the sheet."""
    return "\n".join(textwrap.wrap(text, LEADER_WRAP_COLUMNS)) or text


def emit_mark(b: SceneBuilder, at: tuple[float, float], mark: str, metrics: BlockMetrics,
              layer: str = SCHEDULE_TEXT_LAYER) -> None:
    """Key one plan element to its schedule row."""
    b.add(Text(anchor=at, content=mark, height=metrics.mark_height, layer=layer,
               align="center"))


def block_origin_right_of(points: list[tuple[float, float]],
                          metrics: BlockMetrics) -> tuple[float, float]:
    """Top-left corner of a schedule column placed clear of the drawing's right edge."""
    if not points:
        return (0.0, 0.0)
    return (max(p[0] for p in points) + metrics.block_gap * 2.0, max(p[1] for p in points))


def emit_block(b: SceneBuilder, block: ScheduleBlock, origin: tuple[float, float],
               metrics: BlockMetrics) -> float:
    """Draw one schedule or note block at ``origin``; return its bottom y."""
    if isinstance(block, ScheduleTable):
        return emit_schedule_table(b, block, origin, metrics)
    return emit_note_block(b, block.title, list(block.notes), origin, metrics)


def block_extent(block: ScheduleBlock, metrics: BlockMetrics) -> tuple[float, float]:
    """(width, height) in model inches of what :func:`emit_block` would draw.

    Mirrors the emitters line for line rather than drawing-and-measuring, because the IR
    carries no text metrics: a ``Text`` node is an anchor and a height, and how wide it
    ends up is the writer's business. ``CHARACTER_WIDTH_RATIO`` is the same monospace
    advance the table rules are already sized with, so a reserved width and a drawn rule
    cannot disagree. ``(0.0, 0.0)`` for an empty block — the emitters draw nothing and
    return the origin unmoved, and the reflow must not spend a column on it.

    Pinned against the emitters by ``test_schedule_columns``: an emitter that changes its
    rhythm without changing this drops blocks on top of each other.
    """
    if isinstance(block, ScheduleTable):
        if not block.rows:
            return (0.0, 0.0)
        widths = _column_widths(block)
        lines = [_pad_row(block.columns, widths)]
        lines.extend(_pad_row(row, widths) for row in block.rows)
        height = metrics.title_pitch + metrics.row_pitch * (len(block.rows) + 1)
        return (_lettering_width(block.title, lines, metrics), height)
    if not block.notes:
        return (0.0, 0.0)
    lines = _note_lines(block.notes)
    return (_lettering_width(block.title, lines, metrics),
            metrics.title_pitch + metrics.row_pitch * len(lines))


def emit_block_columns(b: SceneBuilder, blocks: Sequence[ScheduleBlock],
                       plan_points: list[tuple[float, float]], metrics: BlockMetrics,
                       aspect: float = SHEET_VIEWPORT_ASPECT) -> None:
    """Reflow a stack of schedule/note blocks into balanced columns beside the plan.

    A single column is the obvious layout and the wrong one: the sheet is fitted to the
    *scene* bounding box, so a stack twice the plan's height is what ``select_scale`` ends
    up fitting, and the building is drawn small to make room for its own tables. S-100 on
    ARCH D printed at 3/32" = 1'-0" — the bottom of the ladder, on the biggest paper —
    with the sheet's lower third empty.

    So the arrangement is chosen against the shape of the sheet: every contiguous split of
    the stack (order preserved, never a table cut in half) is measured, and the one whose
    overall bounding box is closest to ``aspect`` wins. Reading order stays top-to-bottom
    within a column, then left to right — which contiguity is exactly what guarantees.
    """
    measured = [(block, block_extent(block, metrics)) for block in blocks]
    drawable = [block for block, extent in measured if extent[1] > 0.0]
    extents = [extent for _block, extent in measured if extent[1] > 0.0]
    if not drawable:
        return
    origin = block_origin_right_of(plan_points, metrics)
    if not plan_points:  # nothing to sit beside — one column at the origin
        _emit_columns(b, drawable, (tuple(range(len(drawable))),), origin, extents, metrics)
        return
    plan_x0 = min(point[0] for point in plan_points)
    plan_y0 = min(point[1] for point in plan_points)
    splits = list(_column_splits(len(drawable), MAX_SCHEDULE_COLUMNS))
    best = min(splits, key=lambda split: (
        _split_score(split, extents, (plan_x0, plan_y0), origin, metrics, aspect),
        len(split)))
    _emit_columns(b, drawable, best, origin, extents, metrics)


def _emit_columns(b: SceneBuilder, blocks: Sequence[ScheduleBlock],
                  split: tuple[tuple[int, ...], ...], origin: tuple[float, float],
                  extents: Sequence[tuple[float, float]], metrics: BlockMetrics) -> None:
    x, top = origin
    for column in split:
        y = top
        for index in column:
            y = emit_block(b, blocks[index], (x, y), metrics) - metrics.block_gap
        x += max(extents[i][0] for i in column) + metrics.block_gap


def _column_splits(count: int, max_columns: int
                   ) -> Iterator[tuple[tuple[int, ...], ...]]:
    """Every way to cut ``count`` blocks into 1..``max_columns`` contiguous runs."""
    for columns in range(1, min(max_columns, count) + 1):
        for cuts in combinations(range(1, count), columns - 1):
            bounds = (0, *cuts, count)
            yield tuple(tuple(range(bounds[i], bounds[i + 1])) for i in range(columns))


def _split_score(split: tuple[tuple[int, ...], ...], extents: Sequence[tuple[float, float]],
                 plan_min: tuple[float, float], origin: tuple[float, float],
                 metrics: BlockMetrics, aspect: float) -> float:
    """How small this arrangement will print — lower is better.

    ``max(span_u / aspect, span_z)`` is the span that binds ``select_scale``: on a viewport
    of proportion ``aspect`` the scale is set by whichever of the two runs out first, so
    minimising it maximises the printed scale of the whole sheet.
    """
    plan_x0, plan_y0 = plan_min
    x, top = origin
    widths = [max(extents[i][0] for i in column) for column in split]
    heights = [sum(extents[i][1] for i in column)
               + metrics.block_gap * (len(column) - 1) for column in split]
    span_u = x + sum(widths) + metrics.block_gap * (len(split) - 1) - plan_x0
    span_z = top - min(plan_y0, top - max(heights))
    return max(span_u / aspect, span_z)


def _note_lines(notes: Sequence[str]) -> list[str]:
    """The numbered, wrapped lines ``emit_note_block`` draws for ``notes``."""
    lines: list[str] = []
    for index, note in enumerate(notes, start=1):
        lead = f"{index}. "
        for line in textwrap.wrap(note, NOTE_WRAP_COLUMNS) or [""]:
            lines.append(lead + line)
            lead = " " * len(lead)
    return lines


def _lettering_width(title: str, lines: Sequence[str], metrics: BlockMetrics) -> float:
    """Widest of the title (drawn at title height) and the body lines, in model inches."""
    body = max(len(line) for line in lines) * metrics.text_height
    return max(len(title) * metrics.title_height, body) * CHARACTER_WIDTH_RATIO


def _column_widths(table: ScheduleTable) -> list[int]:
    widths: list[int] = []
    for index, column in enumerate(table.columns):
        widths.append(max([len(column)] + [len(row[index]) for row in table.rows
                                           if index < len(row)]))
    return widths


def _pad_row(cells: tuple[str, ...], widths: list[int]) -> str:
    gap = " " * SCHEDULE_COLUMN_GAP_SPACES
    padded = [cell.ljust(width) for cell, width in zip(cells, widths)]
    return gap.join(padded).rstrip()


def _rule(b: SceneBuilder, x0: float, y: float, width: float) -> None:
    b.add(Polyline(points=((x0, y), (x0 + width, y)), layer=SCHEDULE_GRID_LAYER,
                   lineweight=0.2))
