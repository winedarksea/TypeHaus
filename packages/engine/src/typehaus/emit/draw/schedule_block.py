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
from dataclasses import dataclass

from typehaus.emit.draw.scene import Polyline, SceneBuilder, Text

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
# Monospace advance width as a fraction of cap height — the same ratio the PDF writer
# reserves room with, used here only to size the table's underscore rules.
CHARACTER_WIDTH_RATIO = 0.62
# Long notes wrap at a sheet-note measure rather than running off the drawing.
NOTE_WRAP_COLUMNS = 96
# A leader note is read next to the thing it points at, so it wraps much narrower.
LEADER_WRAP_COLUMNS = 40

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
    for index, note in enumerate(notes, start=1):
        lead = f"{index}. "
        for line in textwrap.wrap(note, NOTE_WRAP_COLUMNS) or [""]:
            b.add(Text(anchor=(x0, row_y), content=lead + line, height=metrics.text_height,
                       layer=SCHEDULE_TEXT_LAYER))
            lead = " " * len(lead)
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
