"""Where a deck's joists actually *stop*, as opposed to which line they are cut at.

``resolve/floors.py`` splits a deck into spans at its bearing refs' **axis** coordinates.
For an interior line two decks share that is right — one plate, split between them. At an
outermost line it is not, and on a face-aligned wall it is not close: catlin's trusses ran
to x=0'-0", the outside of the sheathing, when the plate is at 0 1/2"..6" with a 1 1/4" rim
closing the ends. 18'-0" of drawn member against a real 17'-11".

Three coordinates live at every deck end, and only the first was derived: the **span line**
(what a span table reads), the **joist tip** (where the stick ends), and the **deck edge**
(the subfloor's own edge, over the rim). This derives all three plus the seat length, so a
fabricated member's ordered length and its bearing are numbers rather than implications.
Read by ``checks/structural/bearing_seat.py`` and ``takeoff/fabrication.py``.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.floors import FloorSystem, JoistSpec
from typehaus.resolve.model import ResolvedModel

_TOL_M = 1e-6


@dataclass(frozen=True)
class BearingLine:
    """One span boundary: the axis the joists are cut at, and the structure under it."""

    coord: float
    refs: tuple[str, ...]
    structure: tuple[float, float] | None
    has_wall: bool


@dataclass(frozen=True)
class FloorEnds:
    """The outermost joist tips, rim axes and deck edges of one deck, with seat lengths.

    ``seat_*`` is ``None`` where the end cantilevers (nothing is seated) or where the
    bearing under it could not be resolved to a structure extent. ``rim_*`` is ``None`` on
    a *shared* line, where two decks' joists spend the whole plate between them and a band
    across their ends has nowhere to sit. Nothing replaces it: what restrains those ends is
    each member's own end detail — the tie the take-off already bills per bearing joint, a
    truss's end vertical, an I-joist's squash block — and a course of blocking between one
    deck's joist lines would land on the other deck's, whose spacing need not agree.
    """

    tip_lo: float
    tip_hi: float
    rim_lo: float | None
    rim_hi: float | None
    deck_lo: float
    deck_hi: float
    seat_lo: float | None
    seat_hi: float | None
    shared_lo: bool
    shared_hi: bool


def structure_span(model: ResolvedModel, tag: str, across: int) -> tuple[float, float] | None:
    """The plan extent of a bearing ref's *structure*, across the joist direction.

    A wall reads its structure-layer polygon, never axis ± thickness: on a face-aligned wall
    that stack includes 7 1/4" of foam, girt and cladding, none of which carries anything. A
    ``Beam`` has no layers, so its section straddles its axis as the resolver places it.
    """
    from typehaus.resolve.floors import _bearing_footprint_span
    from typehaus.resolve.framing.solver import _structure_polygon

    wall = model.wall(tag)
    if wall is not None:
        band = _structure_polygon(wall)
        if band and len(band) >= 3:
            values = [point[across] for point in band]
            return min(values), max(values)
        return None
    return _bearing_footprint_span(model, tag, across)


def bearing_lines(model: ResolvedModel, spec: JoistSpec, boundaries: list[float],
                  across: int) -> list[BearingLine]:
    """One :class:`BearingLine` per distinct span boundary.

    Several refs can name one line (catlin's x=18' carries ``W-M-C2`` and the ``BM-M-HALL``
    flitch continuing it); a wall wins over a beam, being what the joists sit on.
    """
    from typehaus.resolve.floors import _bearing_axis

    lines: dict[float, tuple[list[str], tuple[float, float] | None, bool]] = {}
    for tag in spec.bearing_refs:
        axis = _bearing_axis(model, tag)
        if axis is None:
            continue
        (p0, p1) = axis
        coord = (p0[across] + p1[across]) / 2.0
        key = min((b for b in boundaries), key=lambda b: abs(b - coord))
        if abs(key - coord) > _TOL_M:
            continue
        refs, structure, has_wall = lines.get(key, ([], None, False))
        span = structure_span(model, tag, across)
        is_wall = model.wall(tag) is not None
        refs.append(tag)
        if span is not None and (structure is None or is_wall):
            structure = span
        lines[key] = (refs, structure, has_wall or is_wall)
    return [BearingLine(coord, tuple(refs), structure, has_wall)
            for coord, (refs, structure, has_wall) in sorted(lines.items())]


def _is_shared(model: ResolvedModel, system: FloorSystem, storey_tag: str, coord: float,
               low_end: bool, across: int, perp0: float, perp1: float) -> bool:
    """Does another deck on this storey land on the same line from the other side?

    The whole difference between an end bearing and a split one. Coordinate alone would be
    wrong — catlin's main storey has four decks whose west ends all sit on x=0 sharing no
    plate — so the sibling must reach ACROSS the line and overlap this deck perpendicular.
    """
    from typehaus.resolve.floors import _bearing_axis

    for other in model.plan.storey_elements(storey_tag):
        if not isinstance(other, FloorSystem) or other.uid == system.uid:
            continue
        if other.joists.direction != system.joists.direction:
            continue
        coords = [((a[0][across] + a[1][across]) / 2.0)
                  for a in (_bearing_axis(model, tag) for tag in other.joists.bearing_refs)
                  if a is not None]
        if len(coords) < 2:
            continue
        reaches = (min(coords) < coord - _TOL_M) if low_end else (max(coords) > coord + _TOL_M)
        if not reaches or not (min(coords) - _TOL_M <= coord <= max(coords) + _TOL_M):
            continue
        if other.outline:
            perp = [(p.xy_m[1] if across == 0 else p.xy_m[0]) for p in other.outline]
            if min(perp) >= perp1 - _TOL_M or max(perp) <= perp0 + _TOL_M:
                continue  # side by side, not back to back
        return True
    return False


def floor_ends(model: ResolvedModel, system: FloorSystem, storey_tag: str,
               boundaries: list[float], across: int, perp0: float, perp1: float,
               rim_thickness_m: float, cant_start_m: float, cant_end_m: float) -> FloorEnds:
    """Joist tips, deck edges and seat lengths at a deck's two outermost bearing lines.

    Four cases, in the order they are tested: a **shared** line, where the tip is this
    deck's authored share of the plate (``JoistSpec.end_bearing``) or half of it, and no rim
    fits; a **cantilever**, where the tip is the authored fascia line and nothing is seated;
    a **beam-borne** end, unchanged from the span line because a beam's section straddles
    its own axis; and a **free end on a wall plate**, where the rim goes flush with the
    framing face and the joists stop against its inboard face.
    """
    lines = {line.coord: line for line in bearing_lines(model, system.joists, boundaries, across)}
    authored = {ref: length.meters for ref, length in system.joists.end_bearing}
    ends: list[tuple[float, float | None, float, float | None, bool]] = []
    for low_end, cantilever in ((True, cant_start_m), (False, cant_end_m)):
        coord = boundaries[0] if low_end else boundaries[-1]
        sign = 1.0 if low_end else -1.0  # inboard is +x at the low end, -x at the high one
        line = lines.get(coord)
        structure = line.structure if line is not None else None
        seat = next((authored[ref] for ref in (line.refs if line else ()) if ref in authored),
                    None)
        shared = _is_shared(model, system, storey_tag, coord, low_end, across, perp0, perp1)
        near = None if structure is None else (structure[1] if low_end else structure[0])
        if shared:
            # A shared plate: the tip is this deck's authored share of it, else half. No
            # rim — the two decks' joists are seated across the whole plate between them,
            # and the band that would close their ends has nowhere to sit.
            tip = coord if (seat is None or near is None) else near - sign * seat
            ends.append((tip, None, coord,
                         None if near is None else abs(near - tip), shared))
        elif cantilever:
            # Nothing is seated here. The tip is the authored fascia line and the rim keeps
            # its axis on it, which is where every deck in the model already draws its band.
            tip = coord - sign * cantilever
            ends.append((tip, tip, tip, None, shared))
        elif structure is None or not (line and line.has_wall):
            # A beam-borne end: the joists land on the beam, whose own section straddles its
            # axis. There is no plate face to run out to, so the span line stands unchanged.
            ends.append((coord, coord, coord,
                         None if near is None else abs(near - coord), shared))
        else:
            # A free end on a wall plate — the ordinary platform-framing detail. The rim's
            # outboard face is flush with the framing face (the sheathing runs down over it)
            # and the joists stop against its inboard face, so the two touch rather than
            # overlap and the tip is the length the member is actually cut to.
            lo, hi = structure  # not None: the branch above is the only way it can be
            face, opposite = (lo, hi) if low_end else (hi, lo)
            tip = face + sign * rim_thickness_m
            ends.append((tip, face + sign * rim_thickness_m / 2.0, face,
                         abs(opposite - tip), shared))
    ((tip_lo, rim_lo, deck_lo, seat_lo, shared_lo),
     (tip_hi, rim_hi, deck_hi, seat_hi, shared_hi)) = ends
    return FloorEnds(tip_lo=tip_lo, tip_hi=tip_hi, rim_lo=rim_lo, rim_hi=rim_hi,
                     deck_lo=deck_lo, deck_hi=deck_hi,
                     seat_lo=seat_lo, seat_hi=seat_hi,
                     shared_lo=shared_lo, shared_hi=shared_hi)
