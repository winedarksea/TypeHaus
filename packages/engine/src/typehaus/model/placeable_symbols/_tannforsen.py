"""IKEA TÄNNFORSEN wall cabinet: a white box behind one flush, square-edged slab door.

No knob: IKEA sells them separately and the door hinges either side, so one glyph serves both.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, line, rect

DOOR_THICKNESS_M = 0.016  # 5/8"
REVEAL_M = 0.002  # door edge to carcass edge
SHADOW_M = 0.003  # of the door's thickness, drawn as its shadowed back edge


def tannforsen_wall(width: float, depth: float, height: float) -> Geometry:
    """Overall depth includes the door; the carcass sits behind it, hard to the wall."""
    front = -depth / 2
    door_t = min(DOOR_THICKNESS_M, depth / 6)
    carcass_d = depth - door_t
    carcass_y = front + door_t + carcass_d / 2
    parts = (
        box(0, carcass_y, 0, height, width, carcass_d, "appliance-white"),
        # The door's shadowed back edge: a dark sliver, full size, that its 2 mm reveal shows.
        box(0, front + door_t - SHADOW_M / 2, 0, height, width, SHADOW_M, "casework-shadow"),
        box(0, front + (door_t - SHADOW_M) / 2, REVEAL_M, height - REVEAL_M,
            width - 2 * REVEAL_M, door_t - SHADOW_M, "appliance-white"),
    )
    strokes = (rect(0, 0, width, depth, fill="appliance-white"),
               line((-width / 2, front + door_t), (width / 2, front + door_t),
                    weight=DETAIL_WEIGHT))
    return strokes, parts
