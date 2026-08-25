"""Opening framing: the king/jack/header pack and the per-operation patterns (→ 11 §Framing).

Split out of ``solver.py`` when door operation started to matter: a swing door, an overhead
sectional and a bifold share a rough opening but not a load path, and the wall solver has no
business knowing which is which. Every dimension used here comes from
:mod:`typehaus.resolve.framing.tables`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from typehaus.model.enums import DoorOperation
from typehaus.quantities import M_PER_IN
from typehaus.quantities import m as _m
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.stud_module import OpeningStudModule, opening_stud_module
from typehaus.resolve.framing.tables import (
    DEFAULT_SPACING,
    OVERHEAD_TRACK_MEMBER,
    POCKET_SPLIT_STUD_MEMBER,
    POCKET_SPLIT_STUD_SPACING,
    header_depth,
    header_profile_from_spec,
    header_size,
    jamb_pack_counts,
    member_actual,
    opening_framing_pattern,
)
from typehaus.resolve.geometry import add, scale
from typehaus.resolve.model import FramedMember

_PLATE_THICKNESS_M = 1.5 * M_PER_IN
# Shorter than a plate is not a buildable stud, it is a sliver: a header landing
# just shy of the plate line gets no cripples rather than a row of offcuts.
_MIN_CRIPPLE_M = _PLATE_THICKNESS_M


@dataclass(frozen=True)
class WallOpening:
    """One opening handed to the framing solver, in wall-axis (metre) coordinates.

    ``operation`` is the authored :class:`DoorOperation` for a door and ``None`` for a
    window or bare rough opening — the two cases the framing pattern table distinguishes.

    ``header_spec`` is the authored engineered-header override (``Door.header_spec``,
    falling back to ``DoorType.header_spec``), e.g. ``'2-ply 14" LVL'``; ``None`` lets
    the prescriptive table size the header.

    ``pocket_run_m`` is how far the leaf's cavity runs past the rough opening, and
    ``pocket_sign`` which way along the wall axis (+1 toward the wall's end node). Both are
    zero for every operation but ``POCKET``. ``width_m`` stays the *clear* opening
    throughout — the pocket is additional, and their sum is the framed extent.
    """

    center_m: float
    width_m: float
    height_m: float
    sill_m: float
    is_door: bool
    operation: DoorOperation | None = None
    header_spec: str | None = None
    pocket_run_m: float = 0.0
    pocket_sign: int = 0


def pocket_extent(opening: WallOpening) -> tuple[float, float]:
    """(mouth, closed-end) stations of ``opening``'s pocket, or ``(0.0, 0.0)`` if none.

    The mouth is the rough-opening edge the leaf passes through — a split jamb, not a
    trimmer — and the closed end is where its solid post stands.
    """
    pattern = opening_framing_pattern(opening.operation)
    if not pattern.pocket_cavity or opening.pocket_run_m <= 1e-9 or not opening.pocket_sign:
        return (0.0, 0.0)
    sign = 1 if opening.pocket_sign > 0 else -1
    mouth = opening.center_m + sign * opening.width_m / 2
    return (mouth, mouth + sign * opening.pocket_run_m)


def opening_stud_break(opening: WallOpening, spacing_m: float, stud_thickness_m: float,
                       phase_m: float = 0.0) -> OpeningStudModule:
    """This opening's verdict against the stud module at ``spacing_m``."""
    return opening_stud_module(opening.center_m, opening.width_m, spacing_m,
                               stud_thickness_m, phase_m)


def needs_jamb_pack(opening: WallOpening, spacing_m: float, stud_thickness_m: float,
                    phase_m: float = 0.0) -> bool:
    """Whether the opening gets the king/jack/header pack at all.

    A door always reaches the floor and breaks the run. A window narrow enough to land
    wholly inside one bay interrupts no stud, so the load path over it is uninterrupted:
    no header, no trimmers, and — critically — the bay's own two bounding studs stay in
    place to carry the rough sill and head nailer.
    """
    return (opening.is_door
            or not opening_stud_break(opening, spacing_m, stud_thickness_m,
                                      phase_m).fits_between_studs)


def opening_exclusions(openings: list[WallOpening], stud_thickness_m: float,
                       spacing_m: float,
                       phase_m: float = 0.0) -> list[tuple[float, float]]:
    """(center, half-width) bands to keep regular module studs clear of each opening.

    The band covers the rough opening *and* the full trimmer+king pack on each side, so a
    module stud never lands inside the pack (redundant load path, guaranteed clash).
    Because ``in_exclusion`` tests a module stud's *centreline*, the band must reach the
    centreline of the last stud that would still clash — the pack's outer face plus half a
    stud thickness — not merely the pack face itself.
    A header-free opening contributes no band at all: it adds no pack, and excluding one
    here is exactly what deleted the two module studs flanking every small window.
    """
    zones: list[tuple[float, float]] = []
    for opening in openings:
        if not needs_jamb_pack(opening, spacing_m, stud_thickness_m, phase_m):
            continue
        kings, jacks = jamb_pack_counts(_m(opening.width_m),
                                        opening_framing_pattern(opening.operation))
        reach = (kings + jacks + 0.5) * stud_thickness_m + 0.005
        low = opening.center_m - opening.width_m / 2 - reach
        high = opening.center_m + opening.width_m / 2 + reach
        # A pocket extends the band on one side only — the cavity is where the leaf lives,
        # and a module stud in it is not a redundant load path but a door that will not
        # open. The band is re-centred rather than widened both ways, so the strike side
        # keeps every module stud it is entitled to.
        mouth, closed = pocket_extent(opening)
        if closed:
            low = min(low, closed - reach)
            high = max(high, closed + reach)
        zones.append(((low + high) / 2, (high - low) / 2))
    return zones


def in_exclusion(station_m: float, zones: list[tuple[float, float]]) -> bool:
    return any(abs(station_m - center) <= half for center, half in zones)


def _sill_datum(rw, z0: float) -> float:
    """The elevation an opening's ``sill_m`` is measured up from.

    ``ResolvedWall.base_ref_z_m`` — the wall's framing base — and never the stud bearing
    line, which sits a bottom plate above it. The fallback to ``z0`` is for the solver's
    own unit fixtures, which hand this function stand-in walls; a real ``ResolvedWall``
    always answers.
    """
    return getattr(rw, "base_ref_z_m", z0)


def _rough_sill_bottom(sill_top: float, z0: float) -> float | None:
    """Underside of the rough sill whose top face is ``sill_top``, or ``None`` if there is
    no room for one.

    A rough sill's *top* is the rough opening — the window bears on it — so the member
    hangs below the sill line rather than standing on it. An opening whose sill lands
    within a plate of the framing base has the bottom plate itself as its rough sill; a
    separate member there would be a sliver buried in the plate.
    """
    bottom = sill_top - _PLATE_THICKNESS_M
    return None if bottom <= z0 + 1e-9 else bottom


def frame_opening(rw, direction, wall_start, opening: WallOpening, member: str,
                  z0: float, top_at, opening_index: int, spacing: float,
                  stud_stations: tuple[float, ...] = (),
                  phase_m: float = 0.0) -> list[FramedMember]:
    """King/jack/header/cripple pack for one opening, plus its operation's extras."""
    out: list[FramedMember] = []
    pattern = opening_framing_pattern(opening.operation)
    thickness = member_actual(member)[0] * M_PER_IN  # stud face dimension along the wall
    kings, jacks = jamb_pack_counts(_m(opening.width_m), pattern)
    center, half = opening.center_m, opening.width_m / 2
    # ``z0`` is where a vertical member BEARS — the top of the bottom plate. It is not the
    # datum a sill is measured from: ``ResolvedWall.base_ref_z_m`` is, and every other
    # consumer of a sill reads it (``geometry_walls``, the buck and ladder blocking in
    # ``truss_frame``, the furring cuts, the IFC void, the elevations). Framing an opening
    # off ``z0`` put the whole pack a plate — 1 1/2" — above the hole it frames, which the
    # viewer showed as a rough sill standing inside the glass of every window in the house.
    sill_datum = _sill_datum(rw, z0)
    # Head = threshold + clear height, doors included. Doors used to skip the ``sill_m``
    # term on the assumption a door always starts at its host wall's own floor; the Catlin
    # garage breaks that (its overhead door drops a negative sill to the slab below the ICF
    # stem the wall bears on), and skipping the term there left the framed header 22" above
    # the head the wall body, the IFC void and the viewer had all already cut. Every
    # sill_m == 0 door is unaffected.
    header_bottom = sill_datum + opening.sill_m + opening.height_m

    # The same phase ``opening_exclusions`` asked with. The two verdicts must agree: one
    # saying "fits inside a bay, no pack" while the other leaves a module stud standing in
    # the rough opening is a stud through the sill.
    if not needs_jamb_pack(opening, spacing, thickness, phase_m):
        return _frame_inside_one_bay(rw, direction, wall_start, opening, member, z0,
                                     top_at, opening_index, thickness, stud_stations,
                                     header_bottom, sill_datum)

    # A pocket moves one jamb pack outboard of the cavity. The rough-opening edge on that
    # side is the split jamb the leaf passes through — putting a trimmer there would stop
    # the door — so the pack stands at the pocket's closed end and carries that end of the
    # header over the whole cavity. ``pocket_extent`` returns (0, 0) for every other
    # operation, which leaves the symmetric pack below exactly as it was.
    mouth, closed = pocket_extent(opening)
    pocket_sign = 0 if not closed else (1 if opening.pocket_sign > 0 else -1)

    # Trimmers (jacks) and kings pack face-to-face outward from each rough-opening edge:
    # the innermost jack's inner face sits on the RO edge (centreline at half a thickness
    # in), each following member is one full thickness further out. Spacing members by
    # their real thickness makes the stud pack *touch* rather than interpenetrate — the
    # box IR then shows a face-nailed pack as adjacency, not a clash.
    pack_edges: dict[int, float] = {}
    for side, sign in (("l", -1), ("r", +1)):
        edge = closed if sign == pocket_sign else center + sign * half
        pack_edges[sign] = edge
        for jack_index in range(jacks):
            station = edge + sign * (thickness / 2 + jack_index * thickness)
            position = add(wall_start, scale(direction, station))
            out.append(FramedMember(rw.uid, f"jack-{opening_index}-{side}{jack_index}",
                                    "jack", member, position, position, z0, header_bottom,
                                    header_bottom - z0, orient=direction))
        for king_index in range(kings):
            station = edge + sign * (thickness / 2 + (jacks + king_index) * thickness)
            position = add(wall_start, scale(direction, station))
            king_top = top_at(station)
            out.append(FramedMember(rw.uid, f"king-{opening_index}-{side}{king_index}",
                                    "king", member, position, position, z0, king_top,
                                    king_top - z0, orient=direction))

    if pocket_sign:
        _append_pocket_cavity(out, rw, direction, wall_start, opening_index, mouth, closed,
                              pocket_sign, z0, header_bottom, thickness)

    # The header bears on both trimmer stacks; its ends land on the king inner faces
    # (the pack edge plus the full trimmer stack), so it butts the kings without crossing
    # them. Over a pocket the left/right stations are no longer symmetric about the
    # opening's centre — the header spans the rough opening *and* the cavity.
    header_left_station = pack_edges[-1] - jacks * thickness
    header_right_station = pack_edges[+1] + jacks * thickness
    header_span = header_right_station - header_left_station
    header_left = add(wall_start, scale(direction, header_left_station))
    header_right = add(wall_start, scale(direction, header_right_station))
    # An authored engineered header (e.g. '2-ply 14" LVL') replaces the table-sized
    # member: the profile carries the ply count/width/depth structurally, and the depth
    # comes from the profile itself. An unparseable spec falls back to the table rather
    # than silently sizing a header off a typo.
    engineered = (header_profile_from_spec(opening.header_spec)
                  if opening.header_spec is not None else None)
    if engineered is not None:
        size = engineered
        depth = cross_section(engineered).depth_m
    else:
        size = header_size(_m(opening.width_m), bearing=pattern.header_is_structural)
        depth = header_depth(size, _m(opening.width_m)).meters
    out.append(FramedMember(rw.uid, f"header-{opening_index}", "header", size,
                            header_left, header_right, header_bottom,
                            header_bottom + depth, header_span))

    if pattern.needs_track_jamb_legs:
        _append_track_jamb_legs(out, rw, direction, wall_start, opening, opening_index,
                                z0, header_bottom)
    # Cripples above the header bear on whatever the header actually carries: the flat
    # track nailer where one is emitted, the header itself otherwise.
    cripple_bottom = header_bottom + depth
    if pattern.needs_track_backing:
        cripple_bottom = _append_track_backing(out, rw, header_left, header_right,
                                               opening_index, header_bottom + depth,
                                               header_span)

    if not opening.is_door:
        sill_top = sill_datum + opening.sill_m
        sill_bottom = _rough_sill_bottom(sill_top, z0)
        # The rough sill fits *between* the trimmers, spanning the rough opening only, so
        # its ends butt the jack inner faces instead of running through them.
        left = add(wall_start, scale(direction, center - half))
        right = add(wall_start, scale(direction, center + half))
        if sill_bottom is not None:
            out.append(FramedMember(rw.uid, f"sill-{opening_index}", "sill", member,
                                    left, right, sill_bottom, sill_top,
                                    opening.width_m))
        # Cripples under the rough sill retain the normal stud module without placing
        # framing through the opening itself.
        _append_sill_cripples(out, rw.uid, opening_index, direction, wall_start, center,
                              half, z0, sill_bottom if sill_bottom is not None else z0,
                              member)
    # Head cripples depend only on the gap between the header (or its nailer) and the
    # plate underside — a door has no rough sill, but it has the same head condition a
    # window does.
    _append_head_cripples(out, rw.uid, opening_index, direction, wall_start, center,
                          half, cripple_bottom, top_at, member)
    return out


def _append_pocket_cavity(out: list[FramedMember], rw, direction, wall_start,
                          opening_index: int, mouth: float, closed: float, sign: int,
                          z0: float, header_bottom: float, thickness: float) -> None:
    """Split studs for the cavity a pocket leaf parks in.

    They are what the leaf runs between: a pair of half-thickness legs with the slot
    between them, at 12" o.c. rather than the wall's 16" module because each leg is too
    thin to hold drywall flat at the wider spacing.

    Two things this function deliberately does *not* emit. There is no separate end post —
    the jamb pack has already been relocated to ``closed`` by the caller, and that king and
    jack together are the solid post the leaf stops against; emitting another one there
    puts two members on one station, which is a clash, not framing. And nothing reaches
    above ``header_bottom``: the cavity exists only under the header, so the wall's own
    plates run continuously over and under the pocket. That is what still lets a partition
    tee into this wall over the cavity, tied plate to plate, with only its vertical edge
    floating.
    """
    spacing = POCKET_SPLIT_STUD_SPACING.meters
    count = int(abs(closed - mouth) // spacing)
    for index in range(1, count + 1):
        station = mouth + sign * index * spacing
        # The last interval is short of a full bay; a split stud landing inside the
        # relocated jamb pack's own footprint would be a clash.
        if abs(station - closed) < thickness:
            break
        point = add(wall_start, scale(direction, station))
        out.append(FramedMember(rw.uid, f"pocketsplit-{opening_index}-{index:02d}", "stud",
                                POCKET_SPLIT_STUD_MEMBER, point, point, z0, header_bottom,
                                header_bottom - z0, orient=direction))


def _append_track_jamb_legs(out: list[FramedMember], rw, direction, wall_start,
                            opening: WallOpening, opening_index: int, z0: float,
                            header_bottom: float) -> None:
    """Continuous jamb legs inside the rough opening carrying the vertical door track.

    They stop at the header: above it the panels are already on the horizontal track, and
    running them through the header would only clash with it.
    """
    leg_thickness = member_actual(OVERHEAD_TRACK_MEMBER)[0] * M_PER_IN
    for side, sign in (("l", -1), ("r", +1)):
        station = opening.center_m + sign * (opening.width_m / 2 - leg_thickness / 2)
        position = add(wall_start, scale(direction, station))
        out.append(FramedMember(rw.uid, f"trackjamb-{opening_index}-{side}", "jack",
                                OVERHEAD_TRACK_MEMBER, position, position, z0,
                                header_bottom, header_bottom - z0, orient=direction))


def _append_track_backing(out: list[FramedMember], rw, header_left, header_right,
                          opening_index: int, header_top: float, span_m: float) -> float:
    """Flat nailer on top of the header: what the horizontal track and operator hang from.

    Returns its own top, which is what any head cripple above it bears on.
    """
    backing_thickness = member_actual(OVERHEAD_TRACK_MEMBER)[0] * M_PER_IN
    out.append(FramedMember(rw.uid, f"trackbacking-{opening_index}", "blocking",
                            OVERHEAD_TRACK_MEMBER, header_left, header_right, header_top,
                            header_top + backing_thickness, span_m))
    return header_top + backing_thickness


def _frame_inside_one_bay(rw, direction, wall_start, opening: WallOpening, member: str,
                          z0: float, top_at, opening_index: int, thickness: float,
                          stud_stations: tuple[float, ...],
                          header_bottom: float, sill_datum: float) -> list[FramedMember]:
    """Rough sill + head nailer for an opening that fits wholly inside one stud bay.

    No header and no jamb pack — but the bay's two bounding studs are load-bearing here:
    the sill and the head nailer bear on them, and they are what keeps the stud line
    continuous past the opening. If the module left no stud on one side (the opening sits
    in a wall's end bay, or a neighbouring opening's pack took it), a flanking stud is
    added at the rough-opening edge so the pair is always there.
    """
    out: list[FramedMember] = []
    center, half = opening.center_m, opening.width_m / 2
    # A flanking stud's centreline sits half a thickness outboard of the RO edge, which is
    # also the closest a module stud can be without the opening interrupting it.
    half_stud = thickness / 2
    left_station = max((s for s in stud_stations if s <= center - half - half_stud + 1e-9),
                       default=None)
    right_station = min((s for s in stud_stations if s >= center + half + half_stud - 1e-9),
                        default=None)
    for side, station, edge in (("l", left_station, center - half - half_stud),
                                ("r", right_station, center + half + half_stud)):
        if station is not None:
            continue
        point = add(wall_start, scale(direction, edge))
        stud_top = top_at(edge)
        out.append(FramedMember(rw.uid, f"flank-{opening_index}-{side}", "stud", member,
                                point, point, z0, stud_top, stud_top - z0,
                                orient=direction))
        if side == "l":
            left_station = edge
        else:
            right_station = edge

    # Sill and head nailer span between the flanking studs' inner faces: they butt the studs
    # they bear on instead of floating across the rough opening with unsupported ends.
    bearing_start = left_station + thickness / 2
    bearing_end = right_station - thickness / 2
    left = add(wall_start, scale(direction, bearing_start))
    right = add(wall_start, scale(direction, bearing_end))
    span = bearing_end - bearing_start
    sill_top = sill_datum + opening.sill_m
    sill_bottom = _rough_sill_bottom(sill_top, z0)
    if sill_bottom is not None:
        out.append(FramedMember(rw.uid, f"sill-{opening_index}", "sill", member,
                                left, right, sill_bottom, sill_top, span))
    out.append(FramedMember(rw.uid, f"roughhead-{opening_index}", "blocking", member,
                            left, right, header_bottom,
                            header_bottom + _PLATE_THICKNESS_M, span))
    return out


def _cripple_stations(center: float, half: float) -> list[tuple[int, float]]:
    """Interior 16 in. o.c. stations across a rough opening, as (index, station).

    The two edge stations coincide with jack framing and are dropped: a cripple there
    would be a second member on the trimmer's own centreline.
    """
    spacing = DEFAULT_SPACING.meters
    start, end = center - half, center + half
    stations = [start + index * spacing for index in range(int((end - start) // spacing) + 1)]
    if not stations or stations[-1] < end - 1e-6:
        stations.append(end)
    return [(index, station) for index, station in enumerate(stations)
            if start + 1e-6 < station < end - 1e-6]


def _append_sill_cripples(out: list[FramedMember], parent_uid: str, opening_index: int,
                          direction: tuple[float, float], wall_start: tuple[float, float],
                          center: float, half: float, bottom: float, sill: float,
                          member: str) -> None:
    """Cripples under a rough sill, at a 16 in. maximum spacing. Windows only — a door
    has no rough sill to carry."""
    if sill - bottom <= _MIN_CRIPPLE_M:
        return
    for index, station in _cripple_stations(center, half):
        position = add(wall_start, scale(direction, station))
        out.append(FramedMember(parent_uid, f"cripple-sill-{opening_index}-{index:02d}",
                                "cripple", member, position, position, bottom, sill,
                                sill - bottom, orient=direction))


def _append_head_cripples(out: list[FramedMember], parent_uid: str, opening_index: int,
                          direction: tuple[float, float], wall_start: tuple[float, float],
                          center: float, half: float, header_top: float,
                          top_at: Callable[[float], float], member: str) -> None:
    """Cripples between the header (or its track nailer) and the plate underside.

    Every opening with a jamb pack gets these, doors included: what governs is the
    arithmetic gap above the header, not the operation. An opening whose header runs to
    the plate line simply has no gap and emits none.
    """
    for index, station in _cripple_stations(center, half):
        position = add(wall_start, scale(direction, station))
        wall_top = top_at(station)
        if wall_top - header_top <= _MIN_CRIPPLE_M:
            continue
        out.append(FramedMember(parent_uid, f"cripple-head-{opening_index}-{index:02d}",
                                "cripple", member, position, position, header_top,
                                wall_top, wall_top - header_top, orient=direction))
