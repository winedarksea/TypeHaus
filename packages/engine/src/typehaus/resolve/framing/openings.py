"""Opening framing: the king/jack/header pack and the per-operation patterns (→ 11 §Framing).

Split out of ``solver.py`` when door operation started to matter: a swing door, an overhead
sectional and a bifold share a rough opening but not a load path, and the wall solver has no
business knowing which is which. Every dimension used here comes from
:mod:`typehaus.resolve.framing.tables`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.model.enums import DoorOperation
from typehaus.quantities import m as _m
from typehaus.resolve.framing.tables import (
    DEFAULT_SPACING,
    OVERHEAD_TRACK_MEMBER,
    header_depth,
    header_size,
    jamb_pack_counts,
    member_actual,
    opening_framing_pattern,
)
from typehaus.resolve.geometry import add, scale
from typehaus.resolve.model import FramedMember

_M_PER_IN = 0.0254
_PLATE_THICKNESS_M = 1.5 * _M_PER_IN


@dataclass(frozen=True)
class WallOpening:
    """One opening handed to the framing solver, in wall-axis (metre) coordinates.

    ``operation`` is the authored :class:`DoorOperation` for a door and ``None`` for a
    window or bare rough opening — the two cases the framing pattern table distinguishes.
    """

    center_m: float
    width_m: float
    height_m: float
    sill_m: float
    is_door: bool
    operation: DoorOperation | None = None


def opening_exclusions(openings: list[WallOpening],
                       stud_thickness_m: float) -> list[tuple[float, float]]:
    """(center, half-width) bands to keep regular module studs clear of each opening.

    The band covers the rough opening *and* the full trimmer+king pack on each side, so a
    module stud never lands inside the pack (redundant load path, guaranteed clash).
    """
    zones: list[tuple[float, float]] = []
    for opening in openings:
        kings, jacks = jamb_pack_counts(_m(opening.width_m),
                                        opening_framing_pattern(opening.operation))
        zones.append((opening.center_m,
                      opening.width_m / 2 + (kings + jacks) * stud_thickness_m + 0.005))
    return zones


def in_exclusion(station_m: float, zones: list[tuple[float, float]]) -> bool:
    return any(abs(station_m - center) <= half for center, half in zones)


def frame_opening(rw, direction, wall_start, opening: WallOpening, member: str,
                  z0: float, top_at, opening_index: int,
                  spacing: float) -> list[FramedMember]:
    """King/jack/header/cripple pack for one opening, plus its operation's extras."""
    out: list[FramedMember] = []
    pattern = opening_framing_pattern(opening.operation)
    thickness = member_actual(member)[0] * _M_PER_IN  # stud face dimension along the wall
    kings, jacks = jamb_pack_counts(_m(opening.width_m), pattern)
    center, half = opening.center_m, opening.width_m / 2
    header_bottom = (z0 + opening.height_m if opening.is_door
                     else z0 + opening.sill_m + opening.height_m)

    # A window narrower than the stud module that lands wholly inside one bay breaks no
    # stud line: the load path over it is uninterrupted, so it needs no structural header
    # (and no king/jack trimmers). It gets a flat rough sill + rough head nailer between
    # the intact bounding studs. Doors always reach the floor and break the run, so they
    # always frame fully.
    if not opening.is_door and _studs_broken(center, half, spacing) == 0:
        left = add(wall_start, scale(direction, center - half))
        right = add(wall_start, scale(direction, center + half))
        sill_z0 = z0 + opening.sill_m
        out.append(FramedMember(rw.uid, f"sill-{opening_index}", "sill", member,
                                left, right, sill_z0, sill_z0 + _PLATE_THICKNESS_M,
                                opening.width_m))
        out.append(FramedMember(rw.uid, f"roughhead-{opening_index}", "blocking", member,
                                left, right, header_bottom,
                                header_bottom + _PLATE_THICKNESS_M, opening.width_m))
        return out

    # Trimmers (jacks) and kings pack face-to-face outward from each rough-opening edge:
    # the innermost jack's inner face sits on the RO edge (centreline at half a thickness
    # in), each following member is one full thickness further out. Spacing members by
    # their real thickness makes the stud pack *touch* rather than interpenetrate — the
    # box IR then shows a face-nailed pack as adjacency, not a clash.
    for side, sign in (("l", -1), ("r", +1)):
        edge = center + sign * half
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

    # The header bears on both trimmer stacks; its ends land on the king inner faces
    # (RO half-width + the full trimmer stack), so it butts the kings without crossing them.
    header_half = half + jacks * thickness
    header_left = add(wall_start, scale(direction, center - header_half))
    header_right = add(wall_start, scale(direction, center + header_half))
    size = header_size(_m(opening.width_m), bearing=pattern.header_is_structural)
    depth = header_depth(size, _m(opening.width_m)).meters
    out.append(FramedMember(rw.uid, f"header-{opening_index}", "header", size,
                            header_left, header_right, header_bottom,
                            header_bottom + depth, 2 * header_half))

    if pattern.needs_track_jamb_legs:
        _append_track_jamb_legs(out, rw, direction, wall_start, opening, opening_index,
                                z0, header_bottom)
    if pattern.needs_track_backing:
        _append_track_backing(out, rw, header_left, header_right, opening_index,
                              header_bottom + depth, 2 * header_half)

    if not opening.is_door:
        sill_z0 = z0 + opening.sill_m
        # The rough sill fits *between* the trimmers, spanning the rough opening only, so
        # its ends butt the jack inner faces instead of running through them.
        left = add(wall_start, scale(direction, center - half))
        right = add(wall_start, scale(direction, center + half))
        out.append(FramedMember(rw.uid, f"sill-{opening_index}", "sill", member,
                                left, right, sill_z0, sill_z0 + _PLATE_THICKNESS_M,
                                opening.width_m))
        # Cripples under the rough sill and above the header retain the normal stud
        # module without placing framing through the opening itself.
        _append_opening_cripples(out, rw.uid, opening_index, direction, wall_start, center,
                                 half, z0, sill_z0, header_bottom + depth, top_at, member)
    return out


def _append_track_jamb_legs(out: list[FramedMember], rw, direction, wall_start,
                            opening: WallOpening, opening_index: int, z0: float,
                            header_bottom: float) -> None:
    """Continuous jamb legs inside the rough opening carrying the vertical door track.

    They stop at the header: above it the panels are already on the horizontal track, and
    running them through the header would only clash with it.
    """
    leg_thickness = member_actual(OVERHEAD_TRACK_MEMBER)[0] * _M_PER_IN
    for side, sign in (("l", -1), ("r", +1)):
        station = opening.center_m + sign * (opening.width_m / 2 - leg_thickness / 2)
        position = add(wall_start, scale(direction, station))
        out.append(FramedMember(rw.uid, f"trackjamb-{opening_index}-{side}", "jack",
                                OVERHEAD_TRACK_MEMBER, position, position, z0,
                                header_bottom, header_bottom - z0, orient=direction))


def _append_track_backing(out: list[FramedMember], rw, header_left, header_right,
                          opening_index: int, header_top: float, span_m: float) -> None:
    """Flat nailer on top of the header: what the horizontal track and operator hang from."""
    backing_thickness = member_actual(OVERHEAD_TRACK_MEMBER)[0] * _M_PER_IN
    out.append(FramedMember(rw.uid, f"trackbacking-{opening_index}", "blocking",
                            OVERHEAD_TRACK_MEMBER, header_left, header_right, header_top,
                            header_top + backing_thickness, span_m))


def _studs_broken(center: float, half: float, spacing: float) -> int:
    """How many on-module stud lines an opening interrupts (0 => it fits inside a bay)."""
    lo = math.ceil((center - half) / spacing - 1e-9)
    hi = math.floor((center + half) / spacing + 1e-9)
    return max(0, hi - lo + 1)


def _append_opening_cripples(out: list[FramedMember], parent_uid: str, opening_index: int,
                             direction, wall_start, center: float, half: float,
                             bottom: float, sill: float, header_top: float, top_at,
                             member: str) -> None:
    """Add deterministic sill and header cripples at a 16 in. maximum spacing."""
    spacing = DEFAULT_SPACING.meters
    start, end = center - half, center + half
    stations = [start + index * spacing for index in range(int((end - start) // spacing) + 1)]
    if not stations or stations[-1] < end - 1e-6:
        stations.append(end)
    # Edge stations coincide with jack framing, so only interior stations are cripples.
    for index, station in enumerate(stations):
        if station <= start + 1e-6 or station >= end - 1e-6:
            continue
        position = add(wall_start, scale(direction, station))
        if sill - bottom > 1e-6:
            out.append(FramedMember(parent_uid, f"cripple-sill-{opening_index}-{index:02d}",
                                    "cripple", member, position, position, bottom, sill,
                                    sill - bottom, orient=direction))
        wall_top = top_at(station)
        if wall_top - header_top > 1e-6:
            out.append(FramedMember(parent_uid, f"cripple-head-{opening_index}-{index:02d}",
                                    "cripple", member, position, position, header_top,
                                    wall_top, wall_top - header_top, orient=direction))
