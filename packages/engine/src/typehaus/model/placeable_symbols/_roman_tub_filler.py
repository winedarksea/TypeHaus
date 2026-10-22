"""Three-hole deck-mount Roman tub filler: two lever handles and an arched spout.

Local frame: the hole line sits at the rear (+y), the spout arches toward the front (-y),
as for the faucet in ``_undermount_sink.py``. Proportions scale from the Delta T2759
class: 8" handle centres, 8" spout reach, 5 7/8" deck to outlet and 10" overall, on a
10 1/2" x 10" x 10" type box.
"""

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, circle, line, rect

TYPE_WIDTH_IN = 10.5
TYPE_DEPTH_IN = 10.0
TYPE_HEIGHT_IN = 10.0
HANDLE_CENTRES_IN = 8.0
ESCUTCHEON_DIAMETER_IN = 2.5
SPOUT_REACH_IN = 8.0
OUTLET_HEIGHT_IN = 5.875
LEVER_LENGTH_IN = 3.5
HANDLE_HEIGHT_IN = 3.0


def roman_tub_filler(width: float, depth: float, height: float) -> Geometry:
    """Handles either side of a spout neck; the arch carries the outlet over the basin."""
    sx, sy, sz = width / TYPE_WIDTH_IN, depth / TYPE_DEPTH_IN, height / TYPE_HEIGHT_IN
    hole_y = depth / 2 - sy * ESCUTCHEON_DIAMETER_IN / 2
    handle_x = sx * HANDLE_CENTRES_IN / 2
    outlet_y = hole_y - sy * SPOUT_REACH_IN
    radius = min(sx, sy) * ESCUTCHEON_DIAMETER_IN / 2
    neck = min(sx, sy) * 1.0
    escutcheon_t = sz * 0.25
    strokes = [
        rect(0, (hole_y + outlet_y) / 2, neck, hole_y - outlet_y),
        circle(0, hole_y, radius, weight=DETAIL_WEIGHT),
        circle(0, outlet_y, neck * 0.4, weight=DETAIL_WEIGHT),
    ]
    parts = [
        box(0, hole_y, 0, escutcheon_t, 2 * radius, 2 * radius, "metal"),
        # Neck up to the crown, the arm across, and the outlet dropping to 5 7/8".
        box(0, hole_y, escutcheon_t, height, neck, neck, "metal"),
        box(0, (hole_y + outlet_y) / 2, height - neck, height, neck, hole_y - outlet_y + neck,
            "metal"),
        box(0, outlet_y, sz * OUTLET_HEIGHT_IN, height - neck, neck, neck, "metal"),
    ]
    lever_y = hole_y - sy * LEVER_LENGTH_IN / 2
    lever_z = sz * HANDLE_HEIGHT_IN
    for sign in (-1, 1):
        x = sign * handle_x
        lever_tip = (x, hole_y - sy * LEVER_LENGTH_IN)
        strokes.extend((circle(x, hole_y, radius), line((x, hole_y), lever_tip)))
        parts.extend((
            box(x, hole_y, 0, escutcheon_t, 2 * radius, 2 * radius, "metal"),
            box(x, hole_y, escutcheon_t, lever_z, neck * 0.8, neck * 0.8, "metal"),
            box(x, lever_y, lever_z - neck * 0.4, lever_z, neck * 0.5, sy * LEVER_LENGTH_IN,
                "metal"),
        ))
    return tuple(strokes), tuple(parts)
