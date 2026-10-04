"""Single-bowl undermount sink with a separate rear faucet zone.

The installation envelope includes the faucet; the steel flange is smaller. Dimensions
scale from the 32x19 sink / 30x17 bowl class, leaving three inches behind for deck drilling.
"""

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, circle, rect

SINK_WIDTH_IN = 32.0
SINK_DEPTH_IN = 19.0
BOWL_WIDTH_IN = 30.0
BOWL_DEPTH_IN = 17.0
BOWL_DEPTH_BELOW_RIM_IN = 10.0
FAUCET_ZONE_IN = 3.0
INSTALLATION_DEPTH_IN = SINK_DEPTH_IN + FAUCET_ZONE_IN
DRAIN_FROM_REAR_IN = 4.5
FAUCET_FROM_ENVELOPE_REAR_IN = 1.0
FLANGE_THICKNESS_IN = 0.0625
REPRESENTATIVE_HEIGHT_IN = 2 * BOWL_DEPTH_BELOW_RIM_IN
COUNTER_THICKNESS_IN = 1.181


def single_bowl_undermount(width: float, depth: float, height: float) -> Geometry:
    """Rim at half-height (counter underside), bowl below, faucet on the quartz behind."""
    sink_depth = depth * SINK_DEPTH_IN / INSTALLATION_DEPTH_IN
    bowl_width = width * BOWL_WIDTH_IN / SINK_WIDTH_IN
    bowl_depth = depth * BOWL_DEPTH_IN / INSTALLATION_DEPTH_IN
    bowl_y = -depth * FAUCET_ZONE_IN / INSTALLATION_DEPTH_IN / 2
    rear_y = bowl_y + sink_depth / 2
    drain_y = rear_y - depth * DRAIN_FROM_REAR_IN / INSTALLATION_DEPTH_IN
    faucet_y = depth / 2 - depth * FAUCET_FROM_ENVELOPE_REAR_IN / INSTALLATION_DEPTH_IN
    rim_z = height / 2
    flange_t = min(height * 0.01, depth * FLANGE_THICKNESS_IN / INSTALLATION_DEPTH_IN)
    wall_t = min(width, depth, rim_z) * 0.01
    rim_side_width = (width - bowl_width) / 2
    rim_end_depth = (sink_depth - bowl_depth) / 2
    strokes = (
        rect(0, bowl_y, width, sink_depth),
        rect(0, bowl_y, bowl_width, bowl_depth, weight=DETAIL_WEIGHT),
        circle(0, drain_y, min(bowl_width, bowl_depth) * 0.06, weight=DETAIL_WEIGHT),
        circle(0, faucet_y, min(width, depth) * 0.035, weight=DETAIL_WEIGHT),
    )
    parts = [box(0, bowl_y, 0, wall_t, bowl_width, bowl_depth, "appliance-steel")]
    for sign in (-1, 1):
        parts.extend((
            box(0, bowl_y + sign * (bowl_depth / 2 - wall_t / 2), 0, rim_z,
                bowl_width, wall_t, "appliance-steel"),
            box(sign * (bowl_width / 2 - wall_t / 2), bowl_y, 0, rim_z,
                wall_t, bowl_depth - 2 * wall_t, "appliance-steel"),
            box(0, bowl_y + sign * (sink_depth / 2 - rim_end_depth / 2),
                rim_z - flange_t, rim_z, width, rim_end_depth, "appliance-steel"),
            box(sign * (width / 2 - rim_side_width / 2), bowl_y,
                rim_z - flange_t, rim_z, rim_side_width, bowl_depth, "appliance-steel"),
        ))
    # A representative gooseneck: its base sits on the slab, above the undermount flange.
    faucet_base_z = rim_z + height * COUNTER_THICKNESS_IN / REPRESENTATIVE_HEIGHT_IN
    shaft = min(width, depth, height) * 0.04
    spout_y = bowl_y + bowl_depth * 0.25
    parts.extend((
        box(0, faucet_y, faucet_base_z, height - shaft, shaft, shaft, "metal"),
        box(0, (faucet_y + spout_y) / 2, height - shaft, height,
            shaft, faucet_y - spout_y + shaft, "metal"),
        box(0, spout_y, height - shaft * 2, height, shaft, shaft, "metal"),
    ))
    return strokes, tuple(parts)
