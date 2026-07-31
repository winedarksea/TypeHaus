"""The straight flight: two raked 2x12 stringers and full-width tread boards."""

from __future__ import annotations

import math

from typehaus.model.spatial import Stair
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.resolve.stairs.common import _notch_z, _tread_board_profile


def _straight_stair_members(stair: Stair, minx: float, miny: float, z0: float,
                            risers: int, riser: float,
                            going: float, tread_depth: float,
                            nosing: float) -> tuple[FramedMember, ...]:
    along_x = stair.run_direction == "x"
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    width = stair.width.meters
    sign = -1 if stair.run_reversed else 1
    if along_x:
        end_x, end_y = start_x + sign * going * (risers - 1), start_y
        strings = (((start_x, start_y), (end_x, end_y)),
                   ((start_x, start_y + width), (end_x, end_y + width)))
    else:
        end_x, end_y = start_x, start_y + sign * going * (risers - 1)
        strings = (((start_x, start_y), (end_x, end_y)),
                   ((start_x + width, start_y), (end_x + width, end_y)))
    stringer_depth = cross_section("2x12").depth_m
    # Both ends are notch lines — the first tread board and the arrival subfloor sit *on*
    # them (``_notch_z``), which is what keeps the rake straight and the first and last
    # risers the same height as the rest.
    spring_notch = _notch_z(z0 + riser)
    arrival_notch = _notch_z(z0 + riser * risers)
    out = [
        FramedMember(stair.uid, f"stringer-{index}", "stringer", "2x12", a, b,
                     spring_notch - stringer_depth, spring_notch,
                     math.hypot(going, riser) * (risers - 1),
                     z0_end_m=arrival_notch - stringer_depth, z1_end_m=arrival_notch)
        for index, (a, b) in enumerate(strings)
    ]
    tread_profile = _tread_board_profile(tread_depth)
    for index in range(risers - 1):
        # The axis is the board's *centreline*, half a going past the riser it sits on: a
        # ``deck`` footprint is centred on the axis, so anchoring it on the riser line would
        # leave the flight half a going short of the arrival deck.
        # The board spans one going plus the nose beyond the lower riser.  Adjacent boards
        # overlap by the nose in plan but are one riser apart vertically, as built treads are.
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
        out.append(FramedMember(stair.uid, f"tread-{index:03d}", "tread", tread_profile,
                                a, b, _notch_z(top), top, stair.width.meters,
                                riser_line=riser_line))
    return tuple(out)
