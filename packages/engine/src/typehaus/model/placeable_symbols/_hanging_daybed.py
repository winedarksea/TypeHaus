"""A rope-hung daybed: a slatted base, a mattress, a back and two arms, four ropes on the arms.

``height`` runs from the frame's underside (z = 0) to its top rail; the ropes above it are
drawn by the resolver's cables (``resolve/suspension.py``), one per hang point, at the same
points these ropes rise from. Front is -y.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, line, rect
from typehaus.model.placeable_symbols._plant_primitives import slender_segment

#: The ropes sit this far inside the frame's ends and its front and back: the type's
#: ``hang_points`` (76 x 36 in on the 80 x 43 in twin).
ROPE_INSET_END_M = 0.0508
ROPE_INSET_SIDE_M = 0.0889
ROPE_RADIUS_M = 0.0127
BASE_M = 0.10        # slatted base
MATTRESS_M = 0.15
RAIL_M = 0.045       # back and arm thickness
ARM_SHARE = 0.65     # arm height as a share of the back's


def hanging_daybed(width: float, depth: float, height: float) -> Geometry:
    """Plan: the frame and the mattress. Model: base, mattress, back, arms and ropes."""
    rail = min(RAIL_M, width * 0.05)
    inner_w, inner_d = width - 2 * rail, depth - rail
    strokes = [
        rect(0, 0, width, depth),
        rect(0, -rail / 2, inner_w, inner_d, fill="cushion", weight=DETAIL_WEIGHT),
        line((-width / 2, depth / 2 - rail), (width / 2, depth / 2 - rail)),
    ]
    base = min(BASE_M, height * 0.15)
    top = min(base + MATTRESS_M, height * 0.5)
    arm_z = min(height, top + (height - top) * ARM_SHARE * 0.5)
    parts = [
        box(0, 0, 0, base, width, depth, "wood"),
        box(0, -rail / 2, base, top, inner_w, inner_d, "mattress"),
        box(0, depth / 2 - rail / 2, base, height, width, rail, "wood"),
        box(-width / 2 + rail / 2, -rail / 2, base, arm_z, rail, inner_d, "wood"),
        box(width / 2 - rail / 2, -rail / 2, base, arm_z, rail, inner_d, "wood"),
    ]
    x, y = width / 2 - ROPE_INSET_END_M, depth / 2 - ROPE_INSET_SIDE_M
    rope = min(ROPE_RADIUS_M, width * 0.01)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        parts.append(slender_segment((sx * x, sy * y, 0.0), (sx * x, sy * y, height),
                                     rope, "mattress"))
    return tuple(strokes), tuple(parts)
