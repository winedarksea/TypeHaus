"""The interior dimension tier of the architectural floor plan (→ 20 §Drawing IR).

The auto-dimensioner had two tiers and both were exterior: a per-facade string at 14" and
an overall bbox chain outside it. Between them they say where every *opening* is and how
big the building is, and they say nothing at all about where the partitions inside it
stand — which is the half of a floor plan a framer actually lays out from.

This is the third tier, and three things about it are deliberate:

**It measures FACE OF STUD, both faces of every partition.** A partition's centreline is
not a number anyone pulls a tape to, and its near face alone made a segment read "wall +
room" (D1-001). Each kept partition contributes its two stud faces, so its thickness is its
own segment and the room between is the next. Faces come off ``ResolvedWall``'s resolved
layer polygons, so a wall whose assembly changes thickness moves its own dimension.

**One chain per bearing direction.** Catlin's bearing lines run north-south and the joists
span east-west, so the E-W chain is the one that says where the load paths are and the N-S
chain says where the rooms are cut. Both are emitted, both outside the building beside the
exterior tiers, because a chain struck *through* the plan would cross every room's label
block and every fixture on the way.

**Crowding is answered by staggering, then by leaving whole partitions off** — never a
bearing wall (D1-104): ``bearing_wall_tags`` walls are pinned on every chain.
``dimension_rows.dimension_offsets`` steps a segment too short to hold its own string onto
an outer row; a chain whose strings would still slide off it (or past
``MAX_INTERIOR_SEGMENTS``) is re-struck at a coarser clear gap, so it is as fine as the
sheet's scale can letter.
Either way the chain stays contiguous and closes on the envelope, and its stations are
snapped (``dimension_rows.snap_chain``) so the printed 1/8" strings sum to the overall.
"""

from __future__ import annotations

from collections.abc import Collection

from typehaus.emit.draw._shared import (
    DIMENSION_FACE_FUNCTIONS,
    PLAN_RESERVATION_SCALE,
    to_in,
    wall_face_bounds,
)
from typehaus.emit.draw._shared import (
    _dimension_label as _label,
)
from typehaus.emit.draw.dimension_rows import dimension_offsets, snap_chain
from typehaus.emit.draw.scene import ArchDimension, NamedPoint, SceneBuilder
from typehaus.model.enums import StructuralRole
from typehaus.model.floors import FloorSystem
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel, ResolvedWall

#: Clear space between two partitions (or a partition and the envelope) below which the
#: later partition is left off the chain. A partition always keeps BOTH stud faces, so its
#: thickness is its own segment (D1-001): a 3/4" jog between a 2x4 and a 2x6 run on one
#: line is the same partition, not a dimension.
MIN_INTERIOR_STATION_GAP_IN = 6.0

#: Coarser clear gaps to fall back through when the fine one produces an unreadable chain.
#: The basement plan spans the house, the garage and the sunken garden — 98'-11" — and at
#: 6" it is thirty-odd segments. Stepping the gap up leaves partitions off, never a face of
#: one, so the chain still closes on the overall.
_COARSER_STATION_GAPS_IN = (12.0, 16.0, 24.0, 36.0, 48.0, 72.0)

#: Segments a chain may carry before it is re-struck at a coarser gap: eight partitions,
#: each a wall segment and a clear segment, plus the closing one.
MAX_INTERIOR_SEGMENTS = 17

#: A wall counts as running along an axis when it is within this of parallel to it. Plan
#: walls are orthogonal here; the tolerance only absorbs resolver noise.
_PARALLEL_TOLERANCE = 0.05

Faces = tuple[float, float]


def bearing_wall_tags(model: ResolvedModel) -> frozenset[str]:
    """Walls a deck declares it bears on (``joists.bearing_refs``) or authored BEARING —
    the same two readings S-101 draws heavy (``framingplan._emit_walls_below``)."""
    declared = {tag for element in model.plan.all_elements()
                if isinstance(element, FloorSystem) for tag in element.joists.bearing_refs}
    authored = {wall.tag for wall in model.walls
                if getattr(model.plan.by_tag(wall.tag), "structural_role", None)
                is StructuralRole.BEARING}
    return frozenset(declared | authored)


def _face_stations(walls: list[ResolvedWall], axis: int,
                   only: Collection[str] | None = None) -> list[Faces]:
    """``(near, far)`` stud faces, metres along ``axis``, of every wall across that axis.

    A wall running *along* the measuring axis has no face to measure to on it — its two
    faces are perpendicular to the chain and its ends are already stations on the facade
    string — so only the crossing walls contribute. Faces are the structure (stud) layer,
    or the sheathing where a wall has one (``DIMENSION_FACE_FUNCTIONS``).
    """
    pairs: list[Faces] = []
    for wall in walls:
        if only is not None and wall.tag not in only:
            continue
        (sx, sy), (ex, ey) = wall.axis
        delta = (abs(ex - sx), abs(ey - sy))
        if delta[axis] > delta[1 - axis] * (1.0 + _PARALLEL_TOLERANCE):
            continue  # runs along the chain, not across it
        coordinates = [point[axis] for layer in wall.layers
                       if layer.function in DIMENSION_FACE_FUNCTIONS
                       and len(layer.polygon) >= 3
                       for point in layer.polygon]
        if coordinates:
            pairs.append((min(coordinates), max(coordinates)))
    return pairs


def _merged(pairs: list[Faces]) -> list[Faces]:
    """Overlapping pairs as one: a bearing line built of collinear runs is one partition."""
    out: list[Faces] = []
    for near, far in sorted(pairs):
        if out and near <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], far))
        else:
            out.append((near, far))
    return out


def _chains(pairs: list[Faces], lo: float, hi: float,
            pinned: list[Faces] = ()) -> list[list[float]]:
    """Candidate station lists, finest clear gap first: both faces of each kept partition.

    ``pinned`` partitions (bearing walls) are on every candidate; the rest join where they
    clear every station already kept by the gap.
    """
    envelope = MIN_INTERIOR_STATION_GAP_IN * M_PER_IN
    fixed = [face for near, far in _merged(list(pinned))
             if near >= lo + envelope and far <= hi - envelope for face in (near, far)]
    ordered = sorted(pairs)
    out: list[list[float]] = []
    for gap_in in (MIN_INTERIOR_STATION_GAP_IN, *_COARSER_STATION_GAPS_IN):
        gap = gap_in * M_PER_IN
        kept = [lo, hi, *fixed]
        for near, far in ordered:
            if near < lo + gap or far > hi - gap:
                continue  # the envelope wall itself, or a partition hard against it
            if any(near - gap < station < far + gap for station in kept):
                continue  # the same partition again (collinear), or too close to one kept
            kept.extend((near, far))
        out.append(snap_chain(sorted(kept)))
    return out


def _laid_out(pairs: list[Faces], lo: float, hi: float, offset: float, scale: float,
              pinned: list[Faces] = ()):
    """``(stations, offsets)`` of the finest chain whose strings all sit on a stagger row.

    Failing that, the one (within ``MAX_INTERIOR_SEGMENTS``) that slides the fewest strings
    off their segments. So a chain is as fine as its sheet's scale can letter.
    """
    laid = []
    for stations in _chains(pairs, lo, hi, pinned):
        spans = [(stations[i + 1] - stations[i]) / M_PER_IN
                 for i in range(len(stations) - 1)]
        offsets = dimension_offsets(spans, [_label(span) for span in spans], offset, scale)
        slides = sum(1 for _offset, shift in offsets if shift)
        if len(spans) <= MAX_INTERIOR_SEGMENTS and not slides:
            return stations, offsets
        laid.append((len(spans) > MAX_INTERIOR_SEGMENTS, slides, len(laid), stations, offsets))
    best = min(laid)
    return best[3], best[4]


def emit_interior_dimension_chains(b: SceneBuilder, walls: list[ResolvedWall],
                                   offset: float = 44.0,
                                   scale: float = PLAN_RESERVATION_SCALE,
                                   model: ResolvedModel | None = None) -> None:
    """Two face-to-face partition chains, stacked outside the per-facade strings.

    ``model``'s bearing walls (``bearing_wall_tags``) are kept on every chain, however crowded.

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
    bearing = bearing_wall_tags(model) if model is not None else frozenset()
    for axis, lo, hi, coordinate, sign in chains:
        stations, offsets = _laid_out(_face_stations(walls, axis), lo, hi, sign * offset,
                                      scale, _face_stations(walls, axis, bearing))
        if len(stations) <= 2:
            continue  # nothing inside the envelope to say — the overall chain covers it
        for index, (span_offset, text_along) in enumerate(offsets):
            s0, s1 = stations[index], stations[index + 1]
            p0 = (s0, coordinate) if axis == 0 else (coordinate, s0)
            p1 = (s1, coordinate) if axis == 0 else (coordinate, s1)
            b.add(ArchDimension(
                kind="linear",
                ends=(NamedPoint(xy=to_in(p0), name=f"I{axis}-{index}"),
                      NamedPoint(xy=to_in(p1), name=f"I{axis}-{index + 1}")),
                p0=to_in(p0), p1=to_in(p1), offset=span_offset, text_along=text_along,
            ))
