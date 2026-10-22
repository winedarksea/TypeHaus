"""Moen Align T393 at 10-inch handle centres, without a handshower.

Local +y is the rear. The origin is the trim envelope centre, not the hole line.
Published dimensions: t393sp.pdf Rev. 1/18; body/rod diameters without callouts are
representative. Keep overall reach distinct from the outlet centre's 7 1/4-inch reach.
"""

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, circle, line, rect
from typehaus.model.placeable_symbols._round_hardware import round_cylinder

HANDLE_CENTRES_IN = 10.0
LEVER_REACH_IN = 2.96875
SPOUT_BASE_DIAMETER_IN = 2.25
HANDLE_BASE_DIAMETER_IN = 1.9375
SPOUT_OVERALL_REACH_IN = 7.90625
SPOUT_OUTLET_REACH_IN = 7.25
OUTLET_UNDERSIDE_IN = 3.71875
SPOUT_AXIS_HEIGHT_IN = 4.6875
HANDLE_HEIGHT_IN = 2.5625
TYPE_WIDTH_IN = HANDLE_CENTRES_IN + 2 * LEVER_REACH_IN
TYPE_DEPTH_IN = SPOUT_OVERALL_REACH_IN + SPOUT_BASE_DIAMETER_IN / 2
TYPE_HEIGHT_IN = 6.40625
# These small, uncalled-out diameters convey the product's cylindrical form.
NECK_RADIUS_IN = 0.875
ARM_RADIUS_IN = 0.59375
OUTLET_RADIUS_IN = 0.5
LEVER_RADIUS_IN = 0.1875
BASE_THICKNESS_IN = 0.125


def roman_tub_filler(width: float, depth: float, height: float) -> Geometry:
    """Outward closed levers flank a straight round spout and a downturned outlet."""
    sx, sy, sz = width / TYPE_WIDTH_IN, depth / TYPE_DEPTH_IN, height / TYPE_HEIGHT_IN
    radial_scale = min(sx, sy)
    hole_y = depth / 2 - sy * SPOUT_BASE_DIAMETER_IN / 2
    outlet_y = hole_y - sy * SPOUT_OUTLET_REACH_IN
    front_y = hole_y - sy * SPOUT_OVERALL_REACH_IN
    arm_z = sz * SPOUT_AXIS_HEIGHT_IN
    neck_r = radial_scale * NECK_RADIUS_IN
    base_t = sz * BASE_THICKNESS_IN
    strokes = [
        rect(0, (hole_y + front_y) / 2, 2 * neck_r, hole_y - front_y),
        circle(0, hole_y, radial_scale * SPOUT_BASE_DIAMETER_IN / 2, weight=DETAIL_WEIGHT),
        circle(0, outlet_y, radial_scale * OUTLET_RADIUS_IN, weight=DETAIL_WEIGHT),
    ]
    parts = [
        round_cylinder((0, hole_y, base_t / 2), radial_scale * SPOUT_BASE_DIAMETER_IN / 2,
                       base_t, axis=2, color="metal"),
        round_cylinder((0, hole_y, height / 2), neck_r, height, axis=2, color="metal"),
        round_cylinder((0, (hole_y + front_y) / 2, arm_z), radial_scale * ARM_RADIUS_IN,
                       hole_y - front_y, axis=1, color="metal"),
        round_cylinder((0, outlet_y, (arm_z + sz * OUTLET_UNDERSIDE_IN) / 2),
                       radial_scale * OUTLET_RADIUS_IN, arm_z - sz * OUTLET_UNDERSIDE_IN,
                       axis=2, color="metal"),
    ]
    for sign in (-1, 1):
        x = sign * sx * HANDLE_CENTRES_IN / 2
        tip = x + sign * sx * LEVER_REACH_IN
        lever_z = sz * HANDLE_HEIGHT_IN - radial_scale * LEVER_RADIUS_IN
        strokes.extend((circle(x, hole_y, radial_scale * HANDLE_BASE_DIAMETER_IN / 2),
                        line((x, hole_y), (tip, hole_y))))
        parts.extend((
            round_cylinder((x, hole_y, base_t / 2), radial_scale * HANDLE_BASE_DIAMETER_IN / 2,
                           base_t, axis=2, color="metal"),
            round_cylinder((x, hole_y, sz * HANDLE_HEIGHT_IN / 2), neck_r * 0.8,
                           sz * HANDLE_HEIGHT_IN, axis=2, color="metal"),
            round_cylinder(((x + tip) / 2, hole_y, lever_z), radial_scale * LEVER_RADIUS_IN,
                           abs(tip - x), axis=0, color="metal"),
        ))
    return tuple(strokes), tuple(parts)
