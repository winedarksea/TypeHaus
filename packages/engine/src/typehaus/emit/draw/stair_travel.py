"""The stair's travel line: the walk itself, its arrowhead, its tick and its label.

Split from ``stair_symbol.py`` at the seam the drawing itself has. Everything there is
about which SURFACES reach the sheet — the cut, the break, the occlusion, one line per
riser face. Everything here is about the single heaviest line on the symbol, which says
where a person goes and which way.

What it replaced was a bounding-box centreline of ``stair.outline`` — and ``stair.outline``
is the ``FloorOpening``'s ring, so on a U-stair the 0.50 mm line landed exactly on the WELL
PARTITION, between the two lanes, and ran the length of the landing zone as well; on a
winder it was one straight segment across the fan. There was no arrowhead at all.
"""

from __future__ import annotations

import math

from shapely.geometry import LineString, Point, Polygon

from typehaus.emit.draw._shared import PLAN_RESERVATION_SCALE
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.lineweights import CUT
from typehaus.emit.draw.scene import Polyline, SceneBuilder, Text
from typehaus.emit.draw.typography import CHAR_ASPECT, TEXT_PT, model_in_per_pt
from typehaus.quantities import M_PER_IN

Pt = tuple[float, float]
Box = tuple[float, float, float, float]

#: The travel line's arrowhead and start tick, drawn as plain IR geometry rather than a
#: ``Symbol``. ``span-arrow`` — the only arrow symbol in the vocabulary — renders as a bare
#: LINE with no head in ``dxf_writer`` and in a hardcoded brown in ``pdf_writer``, and a new
#: symbol name costs entries in both writers plus ``SYMBOL_NAMES_WITH_DEDICATED_GLYPH`` and
#: its two tests. A three-point V and a perpendicular tick cost nothing and are
#: writer-agnostic. ``Leader`` is not an option either: it requires ``text``.
_ARROWHEAD_GOINGS = 0.5
_ARROWHEAD_HALF_ANGLE_DEG = 20.0
_START_TICK_WIDTH_FRACTION = 0.5

#: Which end of the travel line carries the head. ``"ascending"`` draws one continuous
#: up-arrow through the well, so a ``DN``-labelled flight's arrow points *toward* the
#: reader's own floor. That is a real convention and not the only one; it is isolated here
#: so the other choice is one line.
_ARROW_AT = "ascending"

#: Gap between the travel line and the near edge of its label, metres. The label is CENTRED
#: on its anchor, so clearing the line means moving it half its own width plus this — a
#: fixed offset only clears a label of one particular length, and "DN 15 R" and "UP 16 R"
#: are not that length.
_STAIR_LABEL_GAP_M = TEXT_PT * model_in_per_pt(PLAN_RESERVATION_SCALE) * M_PER_IN * 0.5


#: Gap between the travel line and the near edge of its label, metres. The label is CENTRED
#: on its anchor, so clearing the line means moving it half its own width plus this — a
#: fixed offset only clears a label of one particular length, and "DN 15 R" and "UP 16 R"
#: are not that length.
_STAIR_LABEL_GAP_M = TEXT_PT * model_in_per_pt(PLAN_RESERVATION_SCALE) * M_PER_IN * 0.5

#: How near another flight's travel line has to be before it decides which side of its own
#: line this label steps off to. A stair shares a well with at most one other flight, and
#: that flight is by construction inside the well; anything farther out is a different stair
#: in a different part of the house and is not a reason to pick a side.
_LABEL_NEIGHBOUR_REACH_M = 0.5


def _interpolate_mid(lo, hi, z: float) -> Pt:
    """Plan midpoint where the walk route crosses elevation ``z``."""
    (a0, b0, z0), (a1, b1, z1) = lo, hi
    t = 0.0 if abs(z1 - z0) < 1e-12 else (z - z0) / (z1 - z0)
    t = max(0.0, min(1.0, t))
    a = (a0[0] + (a1[0] - a0[0]) * t, a0[1] + (a1[1] - a0[1]) * t)
    b = (b0[0] + (b1[0] - b0[0]) * t, b0[1] + (b1[1] - b0[1]) * t)
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def travel_path(route, cut_z: float | None, occluder) -> list[Pt]:
    """The walk, as plan midpoints in climb order, truncated at the cut and at the break.

    A midpoint of each station, so it follows the lanes of a U and the fan of a winder
    instead of running down the bounding box between them. An ARRIVING flight is clipped to
    the part not hidden under the departing one — the longest surviving piece, because a
    travel line in two halves is two travel lines.
    """
    midpoints = [((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0) for a, b, _ in route]
    if cut_z is not None:
        kept = [point for point, station in zip(midpoints, route, strict=True)
                if station[2] <= cut_z]
        crossing = next(((lo, hi) for lo, hi in zip(route, route[1:], strict=False)
                         if lo[2] <= cut_z < hi[2]), None)
        if crossing is not None:
            kept.append(_interpolate_mid(*crossing, cut_z))
        midpoints = kept
    if len(midpoints) < 2:
        return []
    if occluder is None:
        return midpoints
    remainder = LineString(midpoints).difference(occluder)
    if remainder.is_empty:
        return []
    parts = list(getattr(remainder, "geoms", [remainder]))
    longest = max(parts, key=lambda part: part.length)
    points = [tuple(point) for point in longest.coords]
    return points if len(points) >= 2 else []


def emit_travel(b: SceneBuilder, stair, storey: str, path: list[Pt], route,
                travels: list[list[Pt]]) -> list[Box]:
    """The travel line, its arrowhead and start tick, and the ``UP N R`` label.

    All three as plain geometry on ``A-STAIR``; see ``_ARROWHEAD_GOINGS`` for why not a
    ``Symbol``. Returns the boxes a floor-opening note has to keep off: the label, and the
    travel line itself — the heaviest thing on the sheet inside the well, and what a caption
    dropped at the well's representative point lands squarely on.
    """
    b.add(Polyline(points=tuple(_in(point) for point in path), layer="A-STAIR",
                   lineweight=CUT, uid=stair.uid, tag=f"{stair.tag}-travel"))
    head, tail = (path[-1], path[-2]) if _ARROW_AT == "ascending" else (path[0], path[1])
    _emit_arrowhead(b, stair, head, tail)
    start, next_point = (path[0], path[1]) if _ARROW_AT == "ascending" \
        else (path[-1], path[-2])
    width = math.dist(route[0][0], route[0][1])
    _emit_start_tick(b, stair, start, next_point, width)
    # One box per STRAIGHT RUN, not one around the whole path. A U-stair's travel line
    # bounds a box the size of the well, which leaves a caption nowhere to stand and sends
    # ``_place_block`` straight to its last-resort anchor — on top of the line. Run by run
    # it is a set of thin bars with real gaps between them, which is what the well looks
    # like. Each is inflated by the label gap so a caption clears the line rather than
    # touching it.
    pad = _STAIR_LABEL_GAP_M
    boxes = [(min(p0[0], p1[0]) - pad, min(p0[1], p1[1]) - pad,
              max(p0[0], p1[0]) + pad, max(p0[1], p1[1]) + pad)
             for p0, p1 in _straight_runs(path)]
    return [_emit_label(b, stair, storey, path, travels), *boxes]


def _emit_arrowhead(b: SceneBuilder, stair, head: Pt, tail: Pt) -> None:
    dx, dy = head[0] - tail[0], head[1] - tail[1]
    run = math.hypot(dx, dy)
    if run < 1e-9:
        return
    ux, uy = dx / run, dy / run
    size = _ARROWHEAD_GOINGS * stair.going_depth_m
    theta = math.radians(_ARROWHEAD_HALF_ANGLE_DEG)
    barbs = []
    for sign in (1, -1):
        cos, sin = math.cos(sign * theta), math.sin(sign * theta)
        bx, by = ux * cos - uy * sin, ux * sin + uy * cos
        barbs.append((head[0] - bx * size, head[1] - by * size))
    b.add(Polyline(points=(_in(barbs[0]), _in(head), _in(barbs[1])), layer="A-STAIR",
                   lineweight=CUT, uid=stair.uid, tag=f"{stair.tag}-arrow"))


def _emit_start_tick(b: SceneBuilder, stair, start: Pt, toward: Pt, width: float) -> None:
    dx, dy = toward[0] - start[0], toward[1] - start[1]
    run = math.hypot(dx, dy)
    if run < 1e-9:
        return
    half = _START_TICK_WIDTH_FRACTION * width / 2.0
    px, py = -dy / run * half, dx / run * half
    b.add(Polyline(points=(_in((start[0] - px, start[1] - py)),
                           _in((start[0] + px, start[1] + py))), layer="A-STAIR",
                   lineweight=CUT, uid=stair.uid, tag=f"{stair.tag}-start"))


def _straight_runs(path: list[Pt]) -> list[tuple[Pt, Pt]]:
    """``path`` with collinear vertices merged — its maximal STRAIGHT runs.

    A flight's travel line has a vertex at every nosing, so its segments are one going each.
    Measuring "the longest segment" on that picks whichever landing crossing happens to be
    longer than a going and captions the flight across the well it is trying to name.
    """
    runs: list[tuple[Pt, Pt]] = []
    start = path[0]
    for index in range(1, len(path)):
        here, nxt = path[index], path[index + 1] if index + 1 < len(path) else None
        if nxt is None or abs((here[0] - start[0]) * (nxt[1] - start[1])
                              - (here[1] - start[1]) * (nxt[0] - start[0])) > 1e-9:
            runs.append((start, here))
            start = here
    return runs


def _label_side(anchor_a: Pt, anchor_b: Pt, stair, travels: list[list[Pt]]) -> Pt:
    """Which side of its travel line the label steps off to: the one on its OWN lane.

    Two flights in one well put their labels a lane apart or they may as well share a bbox
    centre again — so the side is the one FARTHER from a travel line already drawn IN THIS
    WELL. Only in this well: a stair at the other end of the house is not a reason to pick a
    side, and ranking against it picks one arbitrarily. With no neighbour, the side is the
    one away from the stair's own centre, which on a U puts the label outboard rather than
    over the well partition.
    """
    well = Polygon(stair.outline)
    near = [LineString(other) for other in travels
            if LineString(other).distance(well) <= _LABEL_NEIGHBOUR_REACH_M]
    if near:
        return max((anchor_a, anchor_b),
                   key=lambda point: min(line.distance(Point(*point)) for line in near))
    centre = well.centroid
    return max((anchor_a, anchor_b),
               key=lambda point: math.dist(point, (centre.x, centre.y)))


def _emit_label(b: SceneBuilder, stair, storey: str, path: list[Pt],
                travels: list[list[Pt]]) -> Box:
    """``UP N R`` / ``DN N R``, on the flight's OWN travel line.

    Which way the flight goes is a fact about the READER's storey, not about the stair: it
    is authored departing ``storey`` and arriving ``to_storey`` and drawn on both plans, so
    on the plan it arrives at, it descends. Both flights through catlin's stair hall read
    "UP" until this existed.

    The label sits at the midpoint of the longest straight run of the visible travel line,
    stepped off it perpendicular. There is no longer anything to nudge the two flights'
    labels apart along the run: they are on different lanes to begin with.
    """
    label = f"{'UP' if stair.storey == storey else 'DN'} {stair.riser_count} R"
    p0, p1 = max(_straight_runs(path), key=lambda pair: math.dist(*pair))
    mid = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    run = math.hypot(dx, dy) or 1.0
    half_label = (len(label) * TEXT_PT * CHAR_ASPECT
                  * model_in_per_pt(PLAN_RESERVATION_SCALE) * M_PER_IN / 2.0)
    offset = half_label + _STAIR_LABEL_GAP_M
    anchor = _label_side((mid[0] - dy / run * offset, mid[1] + dx / run * offset),
                         (mid[0] + dy / run * offset, mid[1] - dx / run * offset),
                         stair, travels)
    b.add(Text(anchor=_in(anchor), content=label, height_pt=TEXT_PT, layer="A-STAIR",
               align="center"))
    line = TEXT_PT * model_in_per_pt(PLAN_RESERVATION_SCALE) * M_PER_IN
    return (anchor[0] - half_label, anchor[1] - line / 2.0,
            anchor[0] + half_label, anchor[1] + line / 2.0)
