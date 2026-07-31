"""The U split-landing layout: two parallel flights, two half-width landings, well wall."""

from __future__ import annotations

import math

from typehaus.model.spatial import Stair
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.resolve.stairs.common import (
    _FRAMING_SPACING_M,
    _LANDING_JOIST_PROFILE,
    _WELL_PARTITION_THICKNESS_M,
    _grid_positions,
    _notch_z,
    _tread_board_profile,
)


def _u_split_landing_members(stair: Stair, minx: float, miny: float, z0: float,
                             risers: int, riser: float, tread: float,
                             tread_depth: float, nosing: float,
                             landing_depth_m: float) -> tuple[FramedMember, ...]:
    """Generate two parallel flights joined by two half-width landings one riser apart.

    Riser budget (split-landing semantics): ``lower`` treads, the lower landing, the
    upper landing one riser above it (that riser IS the "step" between the landings),
    ``upper`` treads, then the arrival deck — ``lower + upper + 3 == risers``. Both
    landings sit in the landing zone beyond the flight ends, ``landing_depth_m`` deep.

    Cross-run the well is ``width + partition + width``: the two flight lanes are held
    apart by the well partition rather than butting against each other.

    ``stair.turn_direction`` picks the hand of the 180° turn. The well itself is symmetric,
    so handedness is purely *which lane each flight occupies*: ``"right"`` (the default, and
    the only behaviour before it was authorable) springs from the lane at the ``start``
    corner and arrives in the far one; ``"left"`` swaps them. Nothing else moves — the
    partition stays on the well centreline and the landing zone stays at the far end of the
    run — so mirroring a stair never changes the opening it needs.
    """
    width = stair.width.meters
    flight_treads = max(0, risers - 3)
    lower_treads = (flight_treads + 1) // 2  # odd extra tread goes to the lower flight
    upper_treads = flight_treads - lower_treads
    sign = -1 if stair.run_reversed else 1
    along_x = stair.run_direction == "x"
    # The authored origin, exactly as ``straight.py`` and ``winder.py`` read it. This layout
    # used to take the opening bbox's corner unconditionally and never look at
    # ``stair.start`` — so an authored origin was silently ignored here while
    # ``_stair_fits_opening`` validated against it, and generation and validation ran on two
    # different origins.
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    start = start_x if along_x else start_y
    lane0 = start_y if along_x else start_x
    partition_centre = lane0 + width + _WELL_PARTITION_THICKNESS_M / 2.0
    lane1 = lane0 + width + _WELL_PARTITION_THICKNESS_M
    # The two half-landings, each running from its own flight lane to the partition
    # centreline (the bearing a framer frames into, so no unsupported strip of well is left
    # between them). Which one the *lower* flight walks onto is the stair's handedness.
    near_half = (lane0, partition_centre - lane0)
    far_half = (partition_centre, lane1 + width - partition_centre)
    mirrored = stair.turn_direction == "left"
    lower_lane, upper_lane = (lane1, lane0) if mirrored else (lane0, lane1)
    lower_half, upper_half = (far_half, near_half) if mirrored else (near_half, far_half)

    def at(s: float, cross: float) -> tuple[float, float]:
        """Plan point ``s`` metres along the run (signed from the start edge) at the
        absolute cross-run coordinate ``cross``."""
        return (start + sign * s, cross) if along_x else (cross, start + sign * s)

    stringer_depth = cross_section("2x12").depth_m
    flight_len = tread * lower_treads  # ``tread`` is the riser-to-riser going here.
    lower_landing_z = z0 + riser * (lower_treads + 1)
    upper_landing_z = lower_landing_z + riser
    arrival = z0 + riser * risers
    out: list[FramedMember] = []
    # Stringers, raked: at the springing end the top meets the first tread's top; at the
    # far end it meets the flight's bearing (lower flight → the lower landing, upper
    # flight → the arrival deck). The subfloor clip clamps the springing dip.
    for prefix, lane_lo, s_lo, s_hi, spring_z, bear_z, count in (
        ("lower", lower_lane, 0.0, flight_len, z0, lower_landing_z, lower_treads),
        ("upper", upper_lane, flight_len, flight_len - tread * upper_treads,
         upper_landing_z, arrival, upper_treads),
    ):
        if not count:
            continue
        # Notch lines at both ends: the first tread board sits on one, the landing/arrival
        # deck it bears into on the other (see ``_notch_z``).
        spring_notch = _notch_z(spring_z + riser)
        bear_notch = _notch_z(bear_z)
        for index, cross in enumerate((lane_lo, lane_lo + width)):
            out.append(FramedMember(
                stair.uid, f"stringer-{prefix}-{index}", "stringer", "2x12",
                at(s_lo, cross), at(s_hi, cross),
                spring_notch - stringer_depth, spring_notch,
                math.hypot(tread * count, bear_z - spring_z),
                z0_end_m=bear_notch - stringer_depth, z1_end_m=bear_notch))
    # Both flights' boards run from their riser toward +s (the lower flight ascends that
    # way, the upper descends it), so both centrelines sit half a going past the riser —
    # see ``_tread_board_profile`` for why the axis is the board centre and not the riser.
    tread_profile = _tread_board_profile(tread_depth)
    for index in range(lower_treads):
        top = z0 + riser * (index + 1)
        s = tread * index + (tread - nosing) / 2.0
        out.append(FramedMember(stair.uid, f"tread-lower-{index:03d}", "tread", tread_profile,
                                at(s, lower_lane), at(s, lower_lane + width),
                                _notch_z(top), top, width,
                                riser_line=(at(tread * index, lower_lane),
                                            at(tread * index, lower_lane + width))))
    # Upper flight climbs back toward the start edge; its first tread leaves the upper
    # landing, and its top tread ends one riser below the arrival deck. Its riser faces run
    # back from the landing-zone edge — ``flight_len - tread * index`` is the face a walker
    # steps up at to reach tread ``index``, so the drawn grid stays flush at both ends.
    for index in range(upper_treads):
        top = z0 + riser * (lower_treads + 3 + index)
        s = flight_len - tread * (index + 1) + (tread - nosing) / 2.0
        out.append(FramedMember(stair.uid, f"tread-upper-{index:03d}", "tread", tread_profile,
                                at(s, upper_lane), at(s, upper_lane + width),
                                _notch_z(top), top, width,
                                riser_line=(at(flight_len - tread * index, upper_lane),
                                            at(flight_len - tread * index,
                                               upper_lane + width))))
    # Two landing platforms in the landing zone beyond the flight ends, each on its own
    # flight's side of the well partition.
    out.extend(_landing_platform(stair, "lower", at, flight_len, landing_depth_m,
                                 *lower_half, lower_landing_z))
    out.extend(_landing_platform(stair, "upper", at, flight_len, landing_depth_m,
                                 *upper_half, upper_landing_z))
    # Well partition between the up and down flights: generated stud framing (not an
    # authored Wall) centred in the gap the two lanes leave, bearing on the subfloor the
    # stair springs from and rising to the arrival deck — never past the subfloor into the
    # foundation (the flight-clip guard is the backstop). Both flights' inner stringers
    # bear on it. It stops at the flight end; the landing platforms take over beyond. The
    # 0.20 m inset holds its ends off the opening perimeter framing.
    inset = 0.20
    lo_s, hi_s = inset, flight_len - inset
    if hi_s > lo_s:
        plate = 0.0381  # a 2x4 plate laid flat
        pa, pb = at(lo_s, partition_centre), at(hi_s, partition_centre)
        out.append(FramedMember(stair.uid, "well-partition-plate-bottom", "partition",
                                "2x4", pa, pb, z0, z0 + plate, hi_s - lo_s))
        out.append(FramedMember(stair.uid, "well-partition-plate-top", "partition",
                                "2x4", pa, pb, arrival - plate, arrival, hi_s - lo_s))
        orient = (float(sign), 0.0) if along_x else (0.0, float(sign))
        for index, offset in enumerate(_grid_positions(hi_s - lo_s, _FRAMING_SPACING_M)):
            point = at(lo_s + offset, partition_centre)
            out.append(FramedMember(stair.uid, f"well-partition-stud-{index:03d}",
                                    "partition", "2x4", point, point,
                                    z0 + plate, arrival - plate,
                                    arrival - z0 - 2 * plate, orient=orient))
    return tuple(out)


def _landing_platform(stair: Stair, name: str, at, s0: float, depth: float,
                      lane_lo: float, width: float,
                      landing_z: float) -> list[FramedMember]:
    """One half-width landing platform: full-width deck + joists + perimeter rims.

    The deck is a single ``deck WxT`` member (a parseable profile, so it renders at the
    platform's true width instead of a 1.5" strip). Joists run across the lane on the
    deduplicated 16" grid — edge joists land exactly at 0 and ``depth`` — and the two
    rims cap the joist ends along the run direction.

    The deck is category ``landing``; everything under it is ``landing_framing``. That split
    matters well beyond tidiness: when this function was one member, ``landing`` meant "the
    surface you stand on", and the 2D plan drawer's ``{tread, winder, landing}`` filter was
    written against that meaning. Turning a landing into ~7 members while leaving them all
    ``landing`` silently turned the drawer into a framing plan — about 14 stray A-STAIR
    polylines per landing zone. Category is the axis interference, the IFC mapping and the
    glTF routing already discriminate on, so splitting there is what stays correct for the
    next consumer; narrowing the drawer's filter by child-key prefix would have fixed the
    picture and left the same trap set.
    """
    joist_depth = cross_section(_LANDING_JOIST_PROFILE).depth_m
    # ``landing_z`` is the platform's *finished* walking face; its deck is dropped below it
    # and the joists hang under that, so the risers onto and off the landing are equal.
    deck_bottom = _notch_z(landing_z)
    z_top, z_bot = deck_bottom, deck_bottom - joist_depth
    mid = lane_lo + width / 2.0
    out = [FramedMember(stair.uid, f"landing-{name}", "landing",
                        f"deck {width / 0.0254:g}x1.5",
                        at(s0, mid), at(s0 + depth, mid),
                        deck_bottom, landing_z, depth)]
    for index, offset in enumerate(_grid_positions(depth, _FRAMING_SPACING_M)):
        out.append(FramedMember(stair.uid, f"landing-joist-{name}-{index:03d}",
                                "landing_framing",
                                _LANDING_JOIST_PROFILE, at(s0 + offset, lane_lo),
                                at(s0 + offset, lane_lo + width), z_bot, z_top, width))
    for index, cross in enumerate((lane_lo, lane_lo + width)):
        out.append(FramedMember(stair.uid, f"landing-rim-{name}-{index}", "landing_framing",
                                _LANDING_JOIST_PROFILE, at(s0, cross),
                                at(s0 + depth, cross), z_bot, z_top, depth))
    return out
