"""Plan dimension tiers at a constant PAPER spacing, and the stagger rows inside one tier.

A dimension string is lettering, and lettering is a printed size — so the room between the
building and its first dimension line, between two tiers, and between two stagger rows is a
paper measurement too. These used to be model inches worked out for 3/16" = 1'-0"; a ledger
plan that printed at 3/32" then carried every label at twice the size it had reserved, and
the chains printed through each other and onto the wall hatch.

The numbers are the NCS / A/E/C CAD Standard R4.0 ones: the first dimension line at least
9/16" off the object, each further line at least 3/8" beyond the last. ``sheet_writer``
reserves :func:`dimension_band_in` out of the viewport before it picks a scale, so a plan
whose tiers would not fit steps down a scale instead of running off the sheet.
"""

from __future__ import annotations

from typehaus.emit.draw.annotate import DODGE_GAP_PT, text_extent
from typehaus.emit.draw.typography import (
    CHAR_ASPECT,
    DIM_STRING_PT,
    DIMENSION_DENOMINATOR,
    LINE_SPACING,
    model_in_per_pt,
    round_to_fraction,
)
from typehaus.quantities import M_PER_IN

#: Paper inches from the sheathing face to the first (facade) tier. NCS: >= 9/16".
TIER_FIRST_IN = 9.0 / 16.0
#: Paper inches from a tier's outermost stagger row to the next tier. NCS: >= 3/8".
TIER_GAP_IN = 3.0 / 8.0

#: Rows a staggered string may use. A label that fits none of them slides along the chain
#: to the nearest free slot, outside its extension lines — never onto a used row, because
#: text over text is the one thing no drafting standard allows.
STAGGER_ROWS = 3

_PT_PER_IN = 72.0


def row_pitch_in(height_pt: float = DIM_STRING_PT) -> float:
    """Paper inches between two stagger rows: one text line plus the dodge gap."""
    return (height_pt * LINE_SPACING + DODGE_GAP_PT) / _PT_PER_IN


def _tiers_paper_in() -> tuple[float, float, float]:
    """(facade, interior, overall) tier bases, paper inches off the sheathing face."""
    stack = (STAGGER_ROWS - 1) * row_pitch_in()
    facade = TIER_FIRST_IN
    interior = facade + stack + TIER_GAP_IN
    return facade, interior, interior + stack + TIER_GAP_IN


def tier_offsets(scale: float) -> tuple[float, float, float]:
    """(facade, interior, overall) tier bases in MODEL inches at ``scale``."""
    per_paper_in = model_in_per_pt(scale) * _PT_PER_IN
    facade, interior, overall = _tiers_paper_in()
    return facade * per_paper_in, interior * per_paper_in, overall * per_paper_in


def dimension_band_in() -> tuple[float, float, float, float]:
    """(west, east, south, north) paper inches the floor plan's tiers occupy off the faces.

    South and west carry all three tiers; north and east the facade tier only. Text sits
    above a horizontal line and left of a vertical one, so it is OUTBOARD on the north and
    west — one more text line of paper there.
    """
    _facade, _interior, overall = _tiers_paper_in()
    facade_outer = TIER_FIRST_IN + (STAGGER_ROWS - 1) * row_pitch_in()
    text = DIM_STRING_PT * LINE_SPACING / _PT_PER_IN
    return overall + text, facade_outer, overall, facade_outer + text


def snap_chain(stations: list[float]) -> list[float]:
    """Stations (metres, sorted) with the inner ones moved onto the 1/8" grid off the first.

    Rounding each segment on its own made A-104's chain print 36'-1" under a 36'-0" overall.
    Rounding the cumulative station instead makes every inner segment an exact eighth, and
    the last segment then prints ``round(overall) - sum(the rest)``, so the printed chain
    sums to the printed overall exactly. A station is moved at most 1/16"; the two ends stay.
    Stations that collapse onto one another are merged.
    """
    if len(stations) <= 2:
        return list(stations)
    lo, hi = stations[0], stations[-1]
    step = M_PER_IN / DIMENSION_DENOMINATOR
    out = [lo]
    for station in stations[1:-1]:
        snapped = lo + round_to_fraction((station - lo) / M_PER_IN) * step
        if snapped - out[-1] > step / 2 and hi - snapped > step / 2:
            out.append(snapped)
    out.append(hi)
    return out


def _free(interval: tuple[float, float], row: list[tuple[float, float]]) -> bool:
    return all(interval[1] <= lo or hi <= interval[0] for lo, hi in row)


def dimension_offsets(spans: list[float], labels: list[str], base_offset: float,
                      scale: float, height_pt: float = DIM_STRING_PT,
                      ) -> list[tuple[float, float]]:
    """Per-segment ``(offset, text_along)`` for one dimension chain, model inches.

    The writers centre a string on the segment it measures, so a 6" segment handed a
    4'-3 1/2" string prints through both neighbours. Each label, in chain order, takes the
    first of ``STAGGER_ROWS`` rows (stepping outward from ``base_offset``) where it clears
    every label already there — the staggered dimension string of any hand-drafted plan.
    A label no row has room for takes the nearest free slot ALONG the chain on any row, and
    ``text_along`` says how far it slid; the writer draws it on a leader. ``offset`` carries
    ``base_offset``'s sign. Deterministic: same chain, same rows.
    """
    sign = -1.0 if base_offset < 0 else 1.0
    magnitude = abs(base_offset)
    per_pt = model_in_per_pt(scale)
    pitch = row_pitch_in(height_pt) * _PT_PER_IN * per_pt
    # One character of air between two strings on a row: at the dodge gap alone a crowded
    # 1/8" chain read as one run-on number.
    gap = max(DODGE_GAP_PT, height_pt * CHAR_ASPECT) * per_pt
    rows: list[list[tuple[float, float]]] = [[] for _ in range(STAGGER_ROWS)]
    out: list[tuple[float, float]] = []
    along = 0.0
    for span, label in zip(spans, labels, strict=True):
        centre = along + span / 2.0
        along += span
        half = (text_extent(label, height_pt)[0] * per_pt + gap) / 2.0
        placed = next(((index, 0.0) for index, row in enumerate(rows)
                       if _free((centre - half, centre + half), row)), None)
        if placed is None:
            placed = _slide(rows, centre, half)
        index, shift = placed
        rows[index].append((centre + shift - half, centre + shift + half))
        out.append((sign * (magnitude + index * pitch), shift))
    return out


def _slide(rows: list[list[tuple[float, float]]], centre: float,
           half: float) -> tuple[int, float]:
    """The nearest free slot along the chain on any row: ``(row, shift)``.

    Candidates are the positions butting either side of each label already on a row;
    the smallest shift wins, the inner row on a tie.
    """
    best: tuple[float, int, float] | None = None
    for index, row in enumerate(rows):
        for lo, hi in row:
            for at in (lo - half, hi + half):
                if not _free((at - half, at + half), row):
                    continue
                key = (abs(at - centre), index, at - centre)
                if best is None or key < best:
                    best = key
    assert best is not None  # the slot beyond a row's outermost label is always free
    return best[1], best[2]


def dimension_reserve(scene, scale: float) -> tuple[float, float, float, float]:
    """``(w, e, s, n)`` paper inches the scene's dimension strings stand past its bounds.

    ``pdf_writer._scene_bounds`` (what a frame is fitted to) does not see an
    ``ArchDimension``; a sheet whose tiers are built at ``scale`` reserves this much more.
    """
    from typehaus.emit.draw.pdf_writer import _scene_bounds
    from typehaus.emit.draw.scene import ArchDimension

    bounds = _scene_bounds(scene)
    dims = [node for node in scene.nodes if isinstance(node, ArchDimension)]
    if bounds is None or not dims:
        return (0.0, 0.0, 0.0, 0.0)
    per_pt = model_in_per_pt(scale)
    xs: list[float] = []
    ys: list[float] = []
    for node in dims:
        (x0, y0), (x1, y1) = node.p0, node.p1
        width = text_extent(node.text or "0'-00 0/0\"", node.height_pt)[0] * per_pt
        text = (node.height_pt * LINE_SPACING + DODGE_GAP_PT) * per_pt
        if abs(x1 - x0) >= abs(y1 - y0):
            y = y0 + node.offset
            centre = (x0 + x1) / 2.0 + node.text_along
            xs.extend((min(x0, x1), max(x0, x1), centre - width / 2, centre + width / 2))
            ys.extend((y, y + text))
        else:
            x = x0 + node.offset
            centre = (y0 + y1) / 2.0 + node.text_along
            ys.extend((min(y0, y1), max(y0, y1), centre - width / 2, centre + width / 2))
            xs.extend((x, x - text))
    u0, z0, u1, z1 = bounds
    to_paper = scale / 12.0
    return (max(0.0, u0 - min(xs)) * to_paper, max(0.0, max(xs) - u1) * to_paper,
            max(0.0, z0 - min(ys)) * to_paper, max(0.0, max(ys) - z1) * to_paper)
