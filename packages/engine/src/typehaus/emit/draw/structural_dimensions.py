"""Dimension tiers on the structural plans S-100..S-103 (C7-E2, D1-003, D1-004).

Three tiers, inner to outer, on the south (E-W chains) and west (N-S chains):

* **LOCATING** — every bearing line plus what a framer or a form crew places off it: pad
  and post centres, beam lines, floor-opening edges and the openings in bearing walls.
* **BEARING LINES C/C** — the bearing-line axes alone.
* **OVERALL** — face of foundation (S-100) or face of sheathing / stud (S-101..S-103), the
  same extent the A-1xx sheets state.

All of them stand clear of everything already drawn (leaders and their notes included,
at the size they will print), so a string never lands on a callout. Every station is read
off the resolved model, and every chain is snapped (``dimension_rows.snap_chain``) so the
printed 1/8" strings sum to the overall.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from typehaus.emit.draw._shared import _dimension_label, to_in, wall_face_bounds
from typehaus.emit.draw.dimension_rows import (
    TIER_FIRST_IN,
    TIER_GAP_IN,
    dimension_offsets,
    row_pitch_in,
    snap_chain,
)
from typehaus.emit.draw.scene import ArchDimension, Leader, NamedPoint, SceneBuilder, Text
from typehaus.emit.draw.typography import CHAR_ASPECT, MIN_PT, TEXT_PT, model_in_per_pt
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry import opening_center
from typehaus.resolve.model import ResolvedModel, ResolvedWall

#: Station merge gaps tried, finest first, until a chain letters without sliding a string.
_MERGE_GAPS_IN = (1.0, 6.0, 12.0, 24.0, 48.0)
#: A wall is "across" an axis when its run along that axis is under this fraction of it.
_PARALLEL_TOLERANCE = 0.05
_LEADER_TEXT_H_IN = 1.6  # pdf_writer's default leader height, model inches
LOCATING = "LOCATING"
BEARING = "BRG LINES C/C"


@dataclass(frozen=True)
class Tier:
    """One tier: its legend and its raw stations (metres) along x and along y."""

    label: str
    xs: tuple[float, ...] = ()
    ys: tuple[float, ...] = ()


def crosses(wall_axis, axis: int) -> bool:
    """Whether a wall axis runs across ``axis`` (so it is a station on that axis)."""
    (sx, sy), (ex, ey) = wall_axis
    delta = (abs(ex - sx), abs(ey - sy))
    return delta[axis] <= delta[1 - axis] * _PARALLEL_TOLERANCE


def axis_stations(axes: Iterable, axis: int) -> list[float]:
    """The ``axis`` coordinate of every line in ``axes`` that runs across it."""
    return [(p0[axis] + p1[axis]) / 2.0 for p0, p1 in axes if crosses((p0, p1), axis)]


def line_stations(axes: Iterable) -> tuple[list[float], list[float]]:
    """``(xs, ys)``: each line located on the axis it runs across."""
    axes = list(axes)
    return axis_stations(axes, 0), axis_stations(axes, 1)


def wall_opening_stations(model: ResolvedModel, wall: ResolvedWall,
                          tags: Iterable[str] | None = None
                          ) -> tuple[list[float], list[float]]:
    """Centrelines of the openings in ``wall`` (concrete/masonry: both R.O. edges)."""
    from typehaus.emit.draw._shared import is_masonry_host

    xs: list[float] = []
    ys: list[float] = []
    along = 0 if not crosses(wall.axis, 0) else 1  # the axis the wall runs along
    wanted = None if tags is None else set(tags)
    for opening in model.openings:
        if opening.host_wall != wall.tag or (wanted is not None and opening.tag not in wanted):
            continue
        centre = opening_center(wall, opening)
        if centre is None:
            continue
        half = opening.width_m / 2.0
        points = ((centre[along] - half, centre[along] + half) if is_masonry_host(wall)
                  else (centre[along],))
        (xs if along == 0 else ys).extend(points)
    return xs, ys


def overall_tier(label: str, walls: Sequence[ResolvedWall]) -> Tier | None:
    """The face-to-face overall of ``walls`` (structure/sheathing faces)."""
    bounds = wall_face_bounds(list(walls))
    if bounds is None:
        return None
    minx, maxx, miny, maxy = bounds
    return Tier(label, (minx, maxx), (miny, maxy))


def emit_structural_tiers(b: SceneBuilder, tiers: Sequence[Tier | None],
                          scale: float, legend_pad_pt: float = 0.0
                          ) -> tuple[float, float] | None:
    """Draw ``tiers`` inner to outer, south and west of everything already in ``b``.

    Each side stacks only the tiers it has, each as deep as the stagger rows it used, so
    the band costs the sheet no more paper than it prints. Returns ``(x, y)``, model
    inches: how far west and south the tiers reach (``None`` if none drew). A legend steps
    ``legend_pad_pt`` printed points west, clear of a first label wider than its segment.
    """
    box = drawn_box(b.build().nodes, scale)
    if box is None:
        return None
    per_paper_in = model_in_per_pt(scale) * 72.0
    west, south = box[0], box[1]
    reach = [TIER_FIRST_IN, TIER_FIRST_IN]  # paper inches off the box, (south, west)
    present = [tier for tier in tiers if tier is not None]
    for index, tier in enumerate(present):
        for axis, edge in ((0, south), (1, west)):
            if _repeats(tier, present[index + 1:], axis):
                continue  # the next tier says the same thing (a ridge on a bearing line)
            distance = reach[axis] * per_paper_in
            rows = _emit_chain(b, tier, axis, edge, -distance, scale)
            if rows and axis == 0:
                _emit_legend(b, tier.label,
                             (west - legend_pad_pt * model_in_per_pt(scale), south - distance),
                             scale)
            if rows:
                reach[axis] += (rows - 1) * row_pitch_in() + TIER_GAP_IN
    if reach == [TIER_FIRST_IN, TIER_FIRST_IN]:
        return None
    return west - reach[1] * per_paper_in, south - reach[0] * per_paper_in


def _repeats(tier: Tier, later: Sequence[Tier], axis: int) -> bool:
    mine = _chain(tier.xs if axis == 0 else tier.ys, 1.0)
    return any(_chain(other.xs if axis == 0 else other.ys, 1.0) == mine for other in later)


def _chain(stations: Iterable[float], gap_in: float) -> list[float]:
    ordered = sorted(stations)
    if len(ordered) < 2:
        return ordered
    gap = gap_in * M_PER_IN
    kept = [ordered[0]]
    for station in ordered[1:-1]:
        if station - kept[-1] >= gap and ordered[-1] - station >= gap:
            kept.append(station)
    kept.append(ordered[-1])
    return snap_chain(kept)


def _laid_out(stations: Sequence[float], offset: float, scale: float):
    """The finest merge of ``stations`` whose strings all sit on a stagger row."""
    first = None
    for gap_in in _MERGE_GAPS_IN:
        chain = _chain(stations, gap_in)
        if len(chain) < 2 or chain[-1] - chain[0] < gap_in * M_PER_IN:
            return first
        spans = [(chain[i + 1] - chain[i]) / M_PER_IN for i in range(len(chain) - 1)]
        offsets = dimension_offsets(spans, [_dimension_label(s) for s in spans], offset,
                                    scale)
        first = first or (chain, offsets)
        if not any(shift for _offset, shift in offsets):
            return chain, offsets
    return first


def _emit_chain(b: SceneBuilder, tier: Tier, axis: int, edge_in: float, offset: float,
                scale: float) -> int:
    """Draw one chain; return the stagger rows it used (0: nothing to draw)."""
    laid = _laid_out(tier.xs if axis == 0 else tier.ys, offset, scale)
    if laid is None:
        return 0
    chain, offsets = laid
    edge_m = edge_in * M_PER_IN
    for index, (row_offset, shift) in enumerate(offsets):
        s0, s1 = chain[index], chain[index + 1]
        p0 = (s0, edge_m) if axis == 0 else (edge_m, s0)
        p1 = (s1, edge_m) if axis == 0 else (edge_m, s1)
        name = f"{tier.label[:3]}{axis}-{index}"
        b.add(ArchDimension(
            kind="linear",
            ends=(NamedPoint(xy=to_in(p0), name=name), NamedPoint(xy=to_in(p1), name=name)),
            p0=to_in(p0), p1=to_in(p1), offset=row_offset, text_along=shift,
        ))
    pitch = row_pitch_in() * model_in_per_pt(scale) * 72.0
    return 1 + max(round((abs(row) - abs(offset)) / pitch) for row, _shift in offsets)


def _emit_legend(b: SceneBuilder, label: str, at: tuple[float, float], scale: float) -> None:
    """The tier's name, right-aligned in the free corner under the west band, at TEXT_PT so
    it stays inside that band rather than widening the sheet."""
    per_pt = model_in_per_pt(scale)
    b.add(Text(anchor=at, content=label, height=TEXT_PT * per_pt, height_pt=TEXT_PT,
               layer="A-ANNO-DIMS", align="right"))


def drawn_box(nodes: Iterable, scale: float) -> tuple[float, float, float, float] | None:
    """``(minx, miny, maxx, maxy)`` model inches of the drawing AS IT WILL PRINT at ``scale``.

    Text and leader notes are measured at their printed size (``MIN_PT`` floor), which
    ``pdf_writer._scene_bounds`` deliberately does not do.
    """
    per_pt = model_in_per_pt(scale)
    xs: list[float] = []
    ys: list[float] = []
    for node in nodes:
        points = getattr(node, "points", None) or getattr(node, "boundary", None)
        if points:
            xs.extend(p[0] for p in points)
            ys.extend(p[1] for p in points)
            continue
        if isinstance(node, Text):
            content, anchor, model_h = node.content, node.anchor, node.height
            align = node.align
        elif isinstance(node, Leader):
            content, anchor, model_h = node.text, node.at, node.height or _LEADER_TEXT_H_IN
            align = "right" if node.at[0] < node.to[0] else "left"  # pdf_writer._leader_align
            xs.append(node.to[0])
            ys.append(node.to[1])
        else:
            continue
        if not isinstance(anchor, tuple):
            continue
        pt = max(MIN_PT, node.height_pt or model_h / per_pt)
        lines = content.split("\n")
        width = max(len(line) for line in lines) * pt * CHAR_ASPECT * per_pt
        height = pt * 1.4 * len(lines) * per_pt
        start = {"left": anchor[0], "center": anchor[0] - width / 2.0,
                 "right": anchor[0] - width}.get(align, anchor[0] - width)
        xs.extend((start, start + width))
        ys.extend((anchor[1] - height, anchor[1] + height))
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)
