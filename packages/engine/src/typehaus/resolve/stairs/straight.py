"""The straight flight: a raked stringer carriage or stacked box tiers, and tread boards."""

from __future__ import annotations

import math

from typehaus.model.spatial import Stair
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.resolve.stairs.common import _tread_board_profile, _tread_thickness

# A tier rim/joist is deck framing, not a stair member: DCA 6 sizes an intermediate
# landing off its DECK tables, and 2x8 is what the landing beside these tiers uses.
_TIER_FRAME_PROFILE = "2x8"


def _straight_stair_members(stair: Stair, minx: float, miny: float, z0: float,
                            risers: int, riser: float,
                            going: float, tread_depth: float,
                            nosing: float) -> tuple[FramedMember, ...]:
    along_x = stair.run_direction == "x"
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    width = stair.width.meters
    sign = -1 if stair.run_reversed else 1
    bays = (max(1, math.ceil(width / stair.stringer_spacing.meters - 1e-9))
            if stair.stringer_spacing is not None else 1)
    offsets = [width * index / bays for index in range(bays + 1)]
    if along_x:
        end_x, end_y = start_x + sign * going * (risers - 1), start_y
        strings = [((start_x, start_y + offset), (end_x, end_y + offset))
                   for offset in offsets]
    else:
        end_x, end_y = start_x, start_y + sign * going * (risers - 1)
        strings = [((start_x + offset, start_y), (end_x + offset, end_y))
                   for offset in offsets]
    if stair.carriage == "cast":
        # No carriage — the tiers are authored pours (→ ``Stair.carriage``) — but the TREADS
        # stay. They are not lumber and nothing bills them (``takeoff/stairs.py::
        # cast_stair_members``); they are the flight's walking surface, and returning ()
        # instead put ST-BW-ENTRY at UNKNOWN width and a hard R311.7 FAIL, because every rule
        # that grades a stair measures the treads it resolved and not the numbers authored on
        # it. A cast nosing IS a tread.
        return _tread_members(stair, start_x, start_y, z0, risers, riser, going,
                              tread_depth, nosing, width, sign, along_x)
    if stair.carriage == "box":
        return _box_tier_members(stair, start_x, start_y, z0, risers, riser, going,
                                 tread_depth, nosing, width, sign, along_x, offsets)
    stringer_depth = cross_section("2x12").depth_m
    # Both ends are notch lines — the first tread board and the arrival subfloor sit *on*
    # them (``_notch_z``), which is what keeps the rake straight and the first and last
    # risers the same height as the rest.
    thickness = _tread_thickness(stair)
    spring_notch = z0 + riser - thickness
    arrival_notch = z0 + riser * risers - thickness
    out = [
        FramedMember(stair.uid, f"stringer-{index}", "stringer", "2x12", a, b,
                     spring_notch - stringer_depth, spring_notch,
                     math.hypot(going, riser) * (risers - 1),
                     z0_end_m=arrival_notch - stringer_depth, z1_end_m=arrival_notch)
        for index, (a, b) in enumerate(strings)
    ]
    out.extend(_tread_members(stair, start_x, start_y, z0, risers, riser, going,
                              tread_depth, nosing, width, sign, along_x))
    return tuple(out)


def _tread_members(stair: Stair, start_x: float, start_y: float, z0: float,
                   risers: int, riser: float, going: float, tread_depth: float,
                   nosing: float, width: float, sign: int,
                   along_x: bool) -> tuple[FramedMember, ...]:
    """The walking surfaces, which every carriage has and no carriage owns.

    Shared by all three carriages — a raked stringer flight, a box tier and a cast tier put
    the SAME surface in the same place, and the three had drifted into three copies of this
    loop. What differs is the order it lands in, and that is ``takeoff/stairs.py``'s call.

    The axis is the board's *centreline*, half a going past the riser it sits on: a ``deck``
    footprint is centred on the axis, so anchoring it on the riser line would leave the
    flight half a going short of the arrival deck. The board spans one going plus the nose
    beyond the lower riser, so adjacent boards overlap by the nose in plan but are one riser
    apart vertically, as built treads are.
    """
    thickness = _tread_thickness(stair)
    profile = _tread_board_profile(tread_depth, thickness)
    out: list[FramedMember] = []
    for index in range(risers - 1):
        centre = going * index + (going - nosing) / 2.0
        riser_s = going * index  # the riser face itself, which the plan drawing marks
        if along_x:
            a = (start_x + sign * centre, start_y)
            b = (start_x + sign * centre, start_y + width)
            riser_line = ((start_x + sign * riser_s, start_y),
                          (start_x + sign * riser_s, start_y + width))
        else:
            a = (start_x, start_y + sign * centre)
            b = (start_x + width, start_y + sign * centre)
            riser_line = ((start_x, start_y + sign * riser_s),
                          (start_x + width, start_y + sign * riser_s))
        top = z0 + riser * (index + 1)  # the finished walking face, board dropped below it
        out.append(FramedMember(stair.uid, f"tread-{index:03d}", "tread", profile,
                                a, b, top - thickness, top, stair.width.meters,
                                riser_line=riser_line))
    return tuple(out)


def _box_tier_members(stair: Stair, start_x: float, start_y: float, z0: float,
                      risers: int, riser: float, going: float, tread_depth: float,
                      nosing: float, width: float, sign: int, along_x: bool,
                      offsets: list[float]) -> tuple[FramedMember, ...]:
    """One framed box per tread, stacked — the carriage a broad shallow terrace tier wants.

    Each box is a rim front and back with joists between them running FRONT TO BACK (up the
    run, across the boards), so the spacing that matters is the one the tread product
    publishes. ``stringer_spacing`` carries it, because for a box it is still exactly what
    the name says: the centre-to-centre spacing of the supports under the walking surface.

    ** THE TREAD SPACING IS NOT THE DECKING SPACING, AND THEY DIFFER BY 4"-7" ON ONE BOARD. **
    A composite board is rated for a UNIFORM load as decking and a 300 lb CONCENTRATED load
    as a stair tread (IRC Table R301.5 fn. c; ICC-ES AC174 §4.1.1 tests it at 1/8" of
    deflection under 300 lb, an absolute limit, not a ratio). ESR-3771 shows the gap plainly:
    16" as decking, 11" as a stair tread, identical product. IRC R507.2.2.5 makes the
    manufacturer's instruction binding and IRC Table R507.7 excludes stairways outright, so
    the number must be read off the purchased board's STAIR row. Published stair spacings run
    8" to 12" across the major brands.

    No member here is a stringer and none is notched, so neither of the cut-stringer limits
    (6'-0" span, 5" throat) applies — see ``Stair.carriage``. They resolve as
    ``landing_framing``, the category a tier already is.
    """
    thickness = _tread_thickness(stair)
    joist_depth = cross_section(_TIER_FRAME_PROFILE).depth_m
    out: list[FramedMember] = []
    for index in range(risers - 1):
        top = z0 + riser * (index + 1)          # the finished walking face of this tier
        frame_z1 = top - thickness              # the boards sit on the frame
        frame_z0 = frame_z1 - joist_depth
        back = going * index                    # the riser face, measured along the run
        front = going * (index + 1)
        # Two rims, across the width at the front and back of this tier's band -- except the
        # TOP tier, whose front edge bolts to the arrival structure's own rim. Emitting one
        # there puts a rim inside the landing beam it is fastened to.
        edges = [("back", back)] + ([] if index == risers - 2 else [("front", front)])
        for edge, along in edges:
            if along_x:
                a, b = ((start_x + sign * along, start_y),
                        (start_x + sign * along, start_y + width))
            else:
                a, b = ((start_x, start_y + sign * along),
                        (start_x + width, start_y + sign * along))
            out.append(FramedMember(
                stair.uid, f"tier-{index:03d}-rim-{edge}", "landing_framing",
                _TIER_FRAME_PROFILE, a, b, frame_z0, frame_z1, width))
        # Joists between them, front to back, at the tread product's own support spacing.
        for step, offset in enumerate(offsets):
            if along_x:
                a, b = ((start_x + sign * back, start_y + offset),
                        (start_x + sign * front, start_y + offset))
            else:
                a, b = ((start_x + offset, start_y + sign * back),
                        (start_x + offset, start_y + sign * front))
            out.append(FramedMember(
                stair.uid, f"tier-{index:03d}-joist-{step:03d}", "landing_framing",
                _TIER_FRAME_PROFILE, a, b, frame_z0, frame_z1, abs(going)))
    out.extend(_tread_members(stair, start_x, start_y, z0, risers, riser, going,
                              tread_depth, nosing, width, sign, along_x))
    return tuple(out)
