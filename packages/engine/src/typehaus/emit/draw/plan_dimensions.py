"""The interior dimension tier of the architectural floor plan (→ 20 §Drawing IR).

The auto-dimensioner had two tiers and both were exterior: a per-facade string at 14" and
an overall bbox chain outside it. Between them they say where every *opening* is and how
big the building is, and they say nothing at all about where the partitions inside it
stand — which is the half of a floor plan a framer actually lays out from.

This is the third tier, and three things about it are deliberate:

**It measures FACES, not axes.** A partition's centreline is not a number anyone pulls a
tape to; the room's clear dimension is face to face, and both faces come straight off
``ResolvedWall``'s resolved layer polygons, so a wall whose assembly changes thickness moves
its own dimension with it. (``INT_2X6_STAGGERED_PLUMBING`` → ``CATLIN_INT_2X6_BRG_PLUMBING``
on the second storey is exactly that case: same 6.77" total, so this string does not move,
which is the honest report.)

**One chain per bearing direction.** Catlin's bearing lines run north-south and the joists
span east-west, so the E-W chain is the one that says where the load paths are and the N-S
chain says where the rooms are cut. Both are emitted, both outside the building beside the
exterior tiers, because a chain struck *through* the plan would cross every room's label
block and every fixture on the way.

**Crowding is answered by staggering, then by MERGING stations — never by dropping one.**
``_shared.dimension_offsets`` steps a segment too short to hold its own string onto an
outer tier, via ``annotate.dodge``. Where two rows are still not enough the chain is
re-struck at a coarser station gap, which merges neighbouring stations into one segment.
Both are safe; *dropping* a station is not, because the chain would then stop summing to
the overall dimension, which is the one property a dimension chain has to have.
"""

from __future__ import annotations

from typehaus.emit.draw._shared import (
    DIMENSION_FACE_FUNCTIONS,
    dimension_offsets,
    to_in,
    wall_face_bounds,
)
from typehaus.emit.draw._shared import (
    _dimension_label as _label,
)
from typehaus.emit.draw.scene import ArchDimension, NamedPoint, SceneBuilder
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedWall

#: Two partition faces closer together than this are one station. Bigger than the facade
#: string's 1" because an interior chain has an order of magnitude more candidates: every
#: partition contributes two faces, and a 3/4" jog between a 2x4 and a 2x6 run reads as a
#: printing error rather than as a dimension.
MIN_INTERIOR_STATION_GAP_IN = 6.0

#: Coarser gaps to fall back through when the fine one produces an unreadable chain. The
#: basement plan is the case that needs them: its bbox spans the house, the freestanding
#: garage and the sunken garden — 98'-11" of it — and every wall in all three contributes
#: two faces, which at 6" is thirty-odd segments printing through each other. Stepping the
#: gap up merges stations rather than dropping the chain, so it still sums to the overall.
_COARSER_STATION_GAPS_IN = (12.0, 16.0, 24.0, 36.0, 48.0, 72.0)

#: Segments a chain may carry before it is re-struck at a coarser gap. Two staggered rows
#: hold roughly this many strings across a whole-storey plan; past it the tier stops being
#: a dimension chain and becomes a grey band.
MAX_INTERIOR_SEGMENTS = 12

#: A wall counts as running along an axis when it is within this of parallel to it. Plan
#: walls are orthogonal here; the tolerance only absorbs resolver noise.
_PARALLEL_TOLERANCE = 0.05


def _face_stations(walls: list[ResolvedWall], axis: int) -> list[float]:
    """Both faces, in meters along ``axis``, of every wall standing across that axis.

    A wall running *along* the measuring axis has no face to measure to on it — its two
    faces are perpendicular to the chain and its ends are already stations on the facade
    string — so only the crossing walls contribute.
    """
    stations: list[float] = []
    for wall in walls:
        (sx, sy), (ex, ey) = wall.axis
        delta = (abs(ex - sx), abs(ey - sy))
        if delta[axis] > delta[1 - axis] * (1.0 + _PARALLEL_TOLERANCE):
            continue  # runs along the chain, not across it
        coordinates = [point[axis] for layer in wall.layers
                       if layer.function in DIMENSION_FACE_FUNCTIONS
                       and len(layer.polygon) >= 3
                       for point in layer.polygon]
        if not coordinates:
            continue
        stations.extend((min(coordinates), max(coordinates)))
    return stations


def _chain(stations: list[float], lo: float, hi: float) -> list[float]:
    """Sorted, deduped, corner-closed station list for one interior chain.

    Re-struck at a coarser station gap until the chain is short enough to read (see
    ``MAX_INTERIOR_SEGMENTS``). The last gap in the ladder is used whatever it produces —
    a chain that is still crowded at 6'-0" between stations is a plan whose bbox spans
    three separate structures, and there is no station spacing that makes that one drawing.
    """
    ordered = sorted(stations)
    kept: list[float] = []
    for gap_in in (MIN_INTERIOR_STATION_GAP_IN, *_COARSER_STATION_GAPS_IN):
        gap = gap_in * M_PER_IN
        kept = [lo]
        for station in ordered:
            if station <= lo + gap or station >= hi - gap:
                continue
            if station - kept[-1] < gap:
                continue
            kept.append(station)
        kept.append(hi)
        if len(kept) - 1 <= MAX_INTERIOR_SEGMENTS:
            break
    return kept


def emit_interior_dimension_chains(b: SceneBuilder, walls: list[ResolvedWall],
                                   offset: float = 44.0) -> None:
    """Two face-to-face partition chains, stacked outside the per-facade strings.

    ``offset`` is the distance outside the sheathing face at which the primary tier sits;
    a staggered segment steps further out from there. The caller stacks the overall bbox
    chain outside *this*, so the ladder reads inner-to-outer: openings, partitions, overall.
    """
    bounds = wall_face_bounds(walls)
    if bounds is None:
        return
    minx, maxx, miny, maxy = bounds
    # (measuring axis, chain lo, chain hi, the facade coordinate the chain is drawn on,
    #  which side of it the chain steps out to)
    chains = (
        (0, minx, maxx, miny, -1.0),   # east-west, drawn below the south face
        (1, miny, maxy, minx, -1.0),   # north-south, drawn left of the west face
    )
    for axis, lo, hi, coordinate, sign in chains:
        stations = _chain(_face_stations(walls, axis), lo, hi)
        if len(stations) <= 2:
            continue  # nothing inside the envelope to say — the overall chain covers it
        spans = [(stations[i + 1] - stations[i]) / M_PER_IN
                 for i in range(len(stations) - 1)]
        offsets = dimension_offsets(spans, [_label(span) for span in spans], sign * offset)
        for index, span_offset in enumerate(offsets):
            s0, s1 = stations[index], stations[index + 1]
            p0 = (s0, coordinate) if axis == 0 else (coordinate, s0)
            p1 = (s1, coordinate) if axis == 0 else (coordinate, s1)
            b.add(ArchDimension(
                kind="linear",
                ends=(NamedPoint(xy=to_in(p0), name=f"I{axis}-{index}"),
                      NamedPoint(xy=to_in(p1), name=f"I{axis}-{index + 1}")),
                p0=to_in(p0), p1=to_in(p1), offset=span_offset,
            ))
