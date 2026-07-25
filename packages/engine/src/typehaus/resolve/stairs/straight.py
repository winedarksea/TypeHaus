"""The straight flight: two raked 2x12 stringers and full-width tread boards."""

from __future__ import annotations

import math

from typehaus.model.spatial import Stair
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.resolve.stairs.common import _TREAD_THICKNESS_M, _tread_board_profile


def _straight_stair_members(stair: Stair, minx: float, miny: float, z0: float,
                            risers: int, riser: float,
                            tread: float) -> tuple[FramedMember, ...]:
    along_x = stair.run_direction == "x"
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    width = stair.width.meters
    sign = -1 if stair.run_reversed else 1
    if along_x:
        end_x, end_y = start_x + sign * tread * (risers - 1), start_y
        strings = (((start_x, start_y), (end_x, end_y)),
                   ((start_x, start_y + width), (end_x, end_y + width)))
    else:
        end_x, end_y = start_x, start_y + sign * tread * (risers - 1)
        strings = (((start_x, start_y), (end_x, end_y)),
                   ((start_x + width, start_y), (end_x + width, end_y)))
    stringer_depth = cross_section("2x12").depth_m
    spring_top = z0 + riser + _TREAD_THICKNESS_M  # top of the first tread at the springing
    arrival = z0 + riser * risers
    out = [
        FramedMember(stair.uid, f"stringer-{index}", "stringer", "2x12", a, b,
                     spring_top - stringer_depth, spring_top,
                     math.hypot(tread * (risers - 1), riser * risers),
                     z0_end_m=arrival - stringer_depth, z1_end_m=arrival)
        for index, (a, b) in enumerate(strings)
    ]
    tread_profile = _tread_board_profile(tread)
    for index in range(risers - 1):
        # The axis is the board's *centreline*, half a going past the riser it sits on: a
        # ``deck`` footprint is centred on the axis, so anchoring it on the riser line would
        # leave the flight half a going short of the arrival deck.
        centre = tread * index + tread / 2.0
        if along_x:
            a = (start_x + sign * centre, start_y)
            b = (start_x + sign * centre, start_y + width)
        else:
            a = (start_x, start_y + sign * centre)
            b = (start_x + width, start_y + sign * centre)
        z = z0 + riser * (index + 1)
        out.append(FramedMember(stair.uid, f"tread-{index:03d}", "tread", tread_profile,
                                a, b, z, z + _TREAD_THICKNESS_M, stair.width.meters))
    return tuple(out)
