"""Floor-opening edge framing: headers, trimmer packs, and the joist lines they displace.

Split out of ``resolve/floors.py``. Two rules the old inline block got wrong:

* **A trimmer runs bearing to bearing.** At an edge closed by a generated header, the
  trimmer pack carries that header's end, so it must reach the bearing line beyond it —
  a pack that stopped at the opening edge bore on nothing but the header it was carrying.
  At an edge a declared wall carries, the trimmer stops at the edge.
* **Framing stands behind the opening line.** The outline is the finished hole, so a
  header or trimmer ply 0 has its inner face on it — never half a ply into the well. An
  authored ``FloorOpening.lining`` pushes that line out by its own thickness.
* **Trimmer stock matches the band.** An I-joist deck trims in 1.75" LVL plies (a 2x12 is
  11 1/4" and would sit 5/8" low); a sawn or truss deck trims in its own joist stock.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from typehaus.findings import Finding, Result, Severity
from typehaus.model.floors import FloorOpening, FloorSystem
from typehaus.quantities import inch, m
from typehaus.resolve.framing.profiles import cross_section, is_sawn_lumber
from typehaus.resolve.framing.tables import ENGINEERED_LVL, header_size
from typehaus.resolve.model import FramedMember, ResolvedModel

# One LVL ply. A floor-opening header hangs *inside* the joist band, so the deck fixes its
# depth and the ply count is the only free variable — which the prescriptive table names.
_LVL_PLY_WIDTH_IN = 1.75
# Past the prescriptive table's 8 ft ceiling the header is a designed beam;
# ``structural.floor_opening_header`` says so.
_ENGINEERED_HEADER_PLIES = 3
# Doubled trimmers: the prescriptive answer (IRC R502.10) for an edge carrying a header end.
_TRIMMER_PLIES = 2
# IRC R502.10.1: a header spanning 4 ft or less may be a single joist-size member, with
# single trimmers. Doubling (R502.10.2) starts past that line.
_SINGLE_MEMBER_SPAN_M = inch(4.0 * 12.0).meters
_IJOIST = re.compile(r"\bI-joist$|\bTJI\s+\d+$")


def _prescriptive_short_opening(span_m: float, member: str) -> bool:
    """Whether R502.10.1's short-opening allowance governs this edge.

    Sawn lumber only, on purpose: R502.10 is a sawn-lumber table, and "a single member the
    same size as the floor joist" on an I-joist or truss deck is a manufacturer's hung-
    I-joist detail the engine has no table to grade. Those decks keep the engineered header.
    """
    return span_m <= _SINGLE_MEMBER_SPAN_M + 1e-9 and is_sawn_lumber(member)


def _trimmer_plies(span_m: float, member: str) -> int:
    """Plies in an opening's trimmer pack — single under R502.10.1, doubled past it."""
    return 1 if _prescriptive_short_opening(span_m, member) else _TRIMMER_PLIES


def opening_header_profile(span_m: float, band_depth_m: float, member: str = "") -> str:
    """Header profile for a floor opening of ``span_m`` in a deck framed of ``member``.

    The prescriptive table sizes the ply count; the deck's joist depth sizes the member so
    the header sits flush in the band. R502.10.1's short opening names the joist itself.
    """
    if _prescriptive_short_opening(span_m, member):
        return member
    prescriptive = header_size(m(span_m))
    plies = (_ENGINEERED_HEADER_PLIES if prescriptive == ENGINEERED_LVL
             else int(prescriptive.split("-", 1)[0]))
    return f"{plies}-{_LVL_PLY_WIDTH_IN:g}x{band_depth_m / inch(1).meters:g} LVL"


def opening_trimmer_profile(member: str, depth_m: float) -> str:
    """One trimmer ply: band-deep LVL on an I-joist deck, the deck's own joist otherwise."""
    if _IJOIST.search(member.strip()):
        return f"{_LVL_PLY_WIDTH_IN:g}x{depth_m / inch(1).meters:g} LVL"
    return member


def _shift(p0: tuple[float, float], p1: tuple[float, float],
           normal: tuple[float, float], distance: float):
    """``p0``/``p1`` translated ``distance`` along the unit ``normal``."""
    return ((p0[0] + normal[0] * distance, p0[1] + normal[1] * distance),
            (p1[0] + normal[0] * distance, p1[1] + normal[1] * distance))


@dataclass(frozen=True)
class OpeningFrame:
    """One rectangular opening, in deck coordinates (``axis`` = along the joists)."""

    opening: FloorOpening
    #: The authored (finished) hole. ``perp*``/``axis*`` are the FRAMED lines: this box
    #: grown by the lining's thickness.
    minx: float
    maxx: float
    miny: float
    maxy: float
    perp0: float
    perp1: float
    axis0: float
    axis1: float
    #: Which axis edges (lo, hi) get a generated header — no declared bearing under them.
    headers: tuple[bool, bool]
    #: The trimmer run: extended to the bearing line beyond each header edge.
    trim0: float
    trim1: float
    #: 0 when the opening sits inside one bay: no framing, see :func:`within_one_bay`.
    plies: int
    trimmer_profile: str
    #: How far the trimmer pack reaches outboard of each parallel edge.
    trim_band: float
    #: The header's width, outboard of each headed axis edge; the cut tails end past it.
    header_width: float = 0.0
    #: The lining's total thickness between the authored and the framed lines.
    setback: float = 0.0
    #: Half the deck's own joist width: a line closer than this to the pack would lap it.
    line_half_width: float = 0.0

    def framed_ring(self, along_x: bool):
        """The rough opening in plan: what the framing and the sheet stop at."""
        (x0, x1), (y0, y1) = ((self.axis0, self.axis1), (self.perp0, self.perp1)) if along_x \
            else ((self.perp0, self.perp1), (self.axis0, self.axis1))
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    def clip(self, segments: list[tuple[float, float]], perp: float):
        """A regular joist line's segments with this opening's framing taken out.

        A line strictly inside the opening keeps its tails. A line on an edge or inside the
        trim band is absorbed into the trimmer pack over the pack's whole run — subtracting
        only the opening's own interval left a stub beside the extended trimmer.
        """
        if self.perp0 + 1e-9 < perp < self.perp1 - 1e-9:
            reach = self.header_width if self.plies else 0.0
            return _subtract_interval(segments, self.axis0 - reach * self.headers[0],
                                      self.axis1 + reach * self.headers[1])
        if not self.plies:
            return segments
        reach = self.trim_band + self.line_half_width
        if self.perp0 - reach - 1e-9 < perp < self.perp1 + reach + 1e-9:
            return _subtract_interval(segments, self.trim0, self.trim1)
        return segments


def opening_frames(model: ResolvedModel, system: FloorSystem, along_x: bool,
                   boundaries: list[float], ends, depth_m: float):
    """``(frames, findings)`` for every opening of ``system``; ``frames`` is None on error."""
    member = system.joists.member
    trimmer_profile = opening_trimmer_profile(member, depth_m)
    ply_width = cross_section(trimmer_profile).width_m
    frames: list[OpeningFrame] = []
    for opening_tag in system.openings:
        opening = model.plan.by_tag(opening_tag)
        if not isinstance(opening, FloorOpening):
            continue
        box = _rectangular_opening_box(opening)
        if box is None:
            return None, [Finding(
                severity=Severity.ERROR, check_id="integrity.floor_opening_shape",
                message=f"floor {system.tag} only frames axis-aligned rectangular "
                        f"opening {opening.tag}",
                element_tags=(system.tag, opening.tag), result=Result.FAIL,
            )]
        minx, maxx, miny, maxy = box
        setback = sum(layer.thickness.meters for layer in opening.lining)
        perp0, perp1 = (miny, maxy) if along_x else (minx, maxx)
        axis0, axis1 = (minx, maxx) if along_x else (miny, maxy)
        perp0, perp1, axis0, axis1 = perp0 - setback, perp1 + setback, axis0 - setback, \
            axis1 + setback
        headers = tuple(not _opening_edge_has_declared_bearing(model, opening, p0, p1)
                        for p0, p1 in _header_edges(box, along_x))
        trim0 = _bearing_beyond(axis0, boundaries, ends.tip_lo, lo=True) if headers[0] else axis0
        trim1 = _bearing_beyond(axis1, boundaries, ends.tip_hi, lo=False) if headers[1] else axis1
        # Ply count is a property of the header span (across the joists), not trimmer length.
        plies = _trimmer_plies(perp1 - perp0, member)
        header_width = cross_section(
            opening_header_profile(perp1 - perp0, depth_m, member)).width_m
        frames.append(OpeningFrame(
            opening, minx, maxx, miny, maxy, perp0, perp1, axis0, axis1, headers,
            trim0, trim1, plies, trimmer_profile, plies * ply_width, header_width, setback,
            cross_section(member).width_m / 2.0))
    return [_stop_at_neighbour_bearing(frame, frames) for frame in frames], []


def _stop_at_neighbour_bearing(frame: OpeningFrame, frames: list[OpeningFrame]) -> OpeningFrame:
    """Stop an extended trimmer at a neighbouring opening's declared bearing edge.

    The joists that opening cuts bear on that wall, so it is a bearing line on this
    trimmer's line too — running on to the deck's own boundary crossed the other well.
    """
    trim0, trim1 = frame.trim0, frame.trim1
    for other in frames:
        if other is frame or not (other.perp0 - other.trim_band < frame.perp1
                                  and frame.perp0 < other.perp1 + other.trim_band):
            continue
        if not other.headers[0] and frame.axis1 - 1e-9 <= other.axis0 < trim1:
            trim1 = other.axis0
        if not other.headers[1] and trim0 < other.axis1 <= frame.axis0 + 1e-9:
            trim0 = other.axis1
    return replace(frame, trim0=trim0, trim1=trim1)


def within_one_bay(frames: list[OpeningFrame], lines: list[float]) -> list[OpeningFrame]:
    """Frames with no framing at all where the opening cuts no joist line.

    A hole between two neighbouring joists interrupts nothing: the joists either side are
    whole and are its trimmers, and the sheet either side of it still spans joist to joist
    in its strong axis, so a header would carry neither a tail nor a sheet edge. R502.10's
    doubled trimmer is for an edge carrying a header's cut joists; here a pack only stepped a
    second ply into the next bay, and a header blocked the bay a riser turns along.
    """
    return [replace(frame, plies=0, trim_band=0.0)
            if not any(frame.perp0 + 1e-6 < line < frame.perp1 - 1e-6 for line in lines)
            else frame for frame in frames]


def _header_edges(box, along_x: bool):
    minx, maxx, miny, maxy = box
    if along_x:
        return (((minx, miny), (minx, maxy)), ((maxx, miny), (maxx, maxy)))
    return (((minx, miny), (maxx, miny)), ((minx, maxy), (maxx, maxy)))


def _bearing_beyond(coord: float, boundaries: list[float], tip: float, *, lo: bool) -> float:
    """The span boundary outboard of ``coord`` — the joist tip past the outermost bearing."""
    if lo:
        inner = [b for b in boundaries[1:] if b <= coord + 1e-9]
        return inner[-1] if inner else min(tip, coord)
    inner = [b for b in boundaries[:-1] if b >= coord - 1e-9]
    return inner[0] if inner else max(tip, coord)


def opening_members(system: FloorSystem, frames: list[OpeningFrame], along_x: bool,
                    z0: float, z1: float, depth_m: float,
                    deck: tuple[float, float] = (-1e9, 1e9)) -> list[FramedMember]:
    """Headers on the undeclared-bearing edges, then the trimmer packs.

    Each header stands outboard of its framed edge and the cut joists land on its far face.
    Trimmer ply 0 has its inner face on the parallel edge; later plies step outboard, face
    to face. A ply that would pass the deck's edge (``deck``, perpendicular extent) is not
    laid: the wall under that edge carries the line. A ply that would overlap one already
    laid — two chases in one span, or two a pack-width apart — is folded into it: bearing
    to bearing, one pack serves both openings.
    """
    headers: list[FramedMember] = []
    #: [key, profile, perp centre, width, run lo, run hi]
    plies: list[list] = []
    for frame in frames:
        if not frame.plies:
            continue
        span = frame.perp1 - frame.perp0
        half = frame.header_width / 2.0
        for edge_index, line in enumerate((frame.axis0 - half, frame.axis1 + half)):
            if not frame.headers[edge_index]:
                continue
            p0, p1 = (((line, frame.perp0), (line, frame.perp1)) if along_x
                      else ((frame.perp0, line), (frame.perp1, line)))
            headers.append(FramedMember(
                system.uid, f"header-{frame.opening.tag}-{edge_index}", "header",
                opening_header_profile(span, depth_m, system.joists.member),
                p0, p1, z0, z1, span,
            ))
        width = frame.trim_band / frame.plies
        for edge_index, (edge, sign) in enumerate(((frame.perp0, -1.0), (frame.perp1, 1.0))):
            for ply in range(frame.plies):
                centre = edge + sign * (ply + 0.5) * width
                if centre - width / 2.0 < deck[0] - 1e-6 or centre + width / 2.0 > deck[1] + 1e-6:
                    continue
                shared = next((laid for laid in plies
                               if abs(laid[2] - centre) < (laid[3] + width) / 2.0 - 1e-6
                               and laid[4] < frame.trim1 - 1e-9
                               and frame.trim0 < laid[5] - 1e-9), None)
                if shared is not None:
                    shared[4], shared[5] = min(shared[4], frame.trim0), max(shared[5], frame.trim1)
                    continue
                plies.append([f"trimmer-{frame.opening.tag}-{edge_index}-{ply}",
                              frame.trimmer_profile, centre, width, frame.trim0, frame.trim1])
    members = headers
    for key, profile, centre, _width, run0, run1 in plies:
        p0, p1 = ((run0, centre), (run1, centre)) if along_x else ((centre, run0), (centre, run1))
        members.append(FramedMember(system.uid, key, "trimmer", profile, p0, p1, z0, z1,
                                    run1 - run0))
    return members


def _rectangular_opening_box(opening: FloorOpening) -> tuple[float, float, float, float] | None:
    points = [point.xy_m for point in opening.outline]
    if len(points) != 4:
        return None
    xs, ys = {point[0] for point in points}, {point[1] for point in points}
    if len(xs) != 2 or len(ys) != 2:
        return None
    return min(xs), max(xs), min(ys), max(ys)


def _subtract_interval(intervals: list[tuple[float, float]], cut0: float,
                       cut1: float) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for start, end in intervals:
        if cut1 <= start or cut0 >= end:
            out.append((start, end))
            continue
        if start < cut0:
            out.append((start, min(end, cut0)))
        if cut1 < end:
            out.append((max(start, cut1), end))
    return out


def _opening_edge_has_declared_bearing(model: ResolvedModel, opening: FloorOpening,
                                       p0: tuple[float, float], p1: tuple[float, float]) -> bool:
    """Does a declared bearing wall carry this whole opening edge?

    Tested against each wall's plan *footprint*, not its centreline: an opening drawn to the
    finished well never coincides with a wall axis (plans/TODO.md D3).
    """
    # Lazy: floors.py imports this module.
    from typehaus.resolve.floors import _bearing_axis, _bearing_footprint_span

    covered: list[tuple[float, float]] = []
    vertical = abs(p0[0] - p1[0]) < 1e-9
    across, along = (0, 1) if vertical else (1, 0)
    for tag in opening.bearing_refs:
        axis = _bearing_axis(model, tag)
        if axis is None:
            continue
        a0, a1 = axis
        if abs(a0[across] - a1[across]) > 1e-9:
            continue  # runs across the edge, not along it — it cannot carry its length
        footprint = _bearing_footprint_span(model, tag, across)
        if footprint is None or not (footprint[0] - 1e-9 <= p0[across] <= footprint[1] + 1e-9):
            continue
        covered.append((min(a0[along], a1[along]), max(a0[along], a1[along])))
    if not covered:
        return False
    target0, target1 = min(p0[along], p1[along]), max(p0[along], p1[along])
    cursor = target0
    for start, end in sorted(covered):
        if start > cursor + 1e-9:
            return False
        cursor = max(cursor, end)
    return cursor >= target1 - 1e-9
