"""Direct-mount outdoor track: open channel, internal splice keys and recessed screws.

Mosquito Curtains publishes the 3/4-inch envelope and 7-foot stock length. Wall, slot,
splice and screw details are illustrative rather than a manufacturer shop drawing.
"""

from __future__ import annotations

import math

from typehaus.model.curtain_track import CurtainTrackSpec
from typehaus.model.placeable_symbols._frame import Part, box, prism

SCREW_HEAD_DIAMETER_M = 0.0048
SCREW_HEAD_HEIGHT_M = 0.0015
SCREW_HEAD_SEGMENTS = 16
SCREW_RECESS_WIDTH_M = 0.0007
SCREW_RECESS_DEPTH_M = 0.0003
RAIL_COLOR = "appliance-white"
HARDWARE_COLOR = "metal"


def outdoor_track_parts(spec: CurtainTrackSpec, run_m: float, top_m: float) -> tuple[Part, ...]:
    """Keep the screw heads inside the channel and the mounting face flush to ``top_m``."""
    width, height = spec.rail_width.meters, spec.rail_height.meters
    wall, slot = spec.rail_wall_thickness.meters, spec.carrier_slot_width.meters
    bottom = top_m - height
    lip_width = (width - slot) / 2
    parts = [box(0, 0, top_m - wall, top_m, run_m, width, RAIL_COLOR)]
    for sign in (-1, 1):
        parts.append(box(0, sign * (width - wall) / 2, bottom + wall, top_m - wall,
                         run_m, wall, RAIL_COLOR))
        parts.append(box(0, sign * (width + slot) / 4, bottom, bottom + wall,
                         run_m, lip_width, RAIL_COLOR))

    # Keys sit inside the upper channel: no sleeve crosses or blocks the carrier slot.
    stock = spec.stock_length.meters
    section_count = math.ceil(run_m / stock)
    for section in range(1, section_count):
        seam = -run_m / 2 + section * stock
        key_length = min(spec.splice_length.meters, 2 * (run_m / 2 - seam))
        parts.append(box(seam, 0, top_m - 2 * wall, top_m - wall,
                         key_length, width - 2 * wall, HARDWARE_COLOR))

    # Two removable stop plugs, fitted within the channel rather than widening the rail.
    stop_length = min(spec.end_stop_length.meters, run_m / 4)
    for sign in (-1, 1):
        parts.append(box(sign * (run_m - stop_length) / 2, 0, bottom, top_m - wall,
                         stop_length, width - 2 * wall, "plastic-white"))

    for section in range(section_count):
        start = section * stock
        length = min(stock, run_m - start)
        # Cut sticks retain the full-stick maximum spacing, including short offcuts.
        inset = min(spec.mounting_end_inset.meters, length / 4)
        maximum_spacing = (stock - 2 * spec.mounting_end_inset.meters) / (
            spec.mounting_screws_per_stock - 1)
        intervals = max(1, math.ceil((length - 2 * inset) / maximum_spacing))
        for index in range(intervals + 1):
            x = -run_m / 2 + start + inset + (length - 2 * inset) * index / intervals
            radius = SCREW_HEAD_DIAMETER_M / 2
            outline = [(x + radius * math.cos(math.tau * step / SCREW_HEAD_SEGMENTS),
                        radius * math.sin(math.tau * step / SCREW_HEAD_SEGMENTS))
                       for step in range(SCREW_HEAD_SEGMENTS)]
            head_bottom = top_m - wall - SCREW_HEAD_HEIGHT_M
            parts.append(prism(outline, head_bottom, top_m - wall, HARDWARE_COLOR))
            for crosswise in (False, True):
                parts.append(box(x, 0, head_bottom - SCREW_RECESS_DEPTH_M, head_bottom,
                                 SCREW_RECESS_WIDTH_M if crosswise else radius * 1.5,
                                 radius * 1.5 if crosswise else SCREW_RECESS_WIDTH_M,
                                 "metal-black"))
    return tuple(parts)
