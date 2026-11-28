"""A wall-hung fixed ladder: two rails stood off the wall, rungs every 12" from 12" up.

The pitch and rail size are the Tri-Arc dock-ladder family's (3/4" rungs, 1 1/2" rails); the
rail runs 14" past the top rung (the side-step hand hold). The back (+y) is the wall.
"""

from typehaus.model.placeable_symbols._frame import box, rect
from typehaus.quantities import M_PER_IN

_RAIL_IN = 1.5
_RUNG_IN = 0.75
_PITCH_IN = 12.0
_EXTENSION_IN = 14.0


def fixed_ladder(width, depth, height):
    rail = _RAIL_IN * M_PER_IN
    rung = _RUNG_IN * M_PER_IN
    front = -depth / 2 + rail / 2
    inside = width - 2 * rail
    parts = [box(sign * (width - rail) / 2, front, 0, height, rail, rail, "metal")
             for sign in (-1, 1)]
    z = _PITCH_IN * M_PER_IN
    top = height - _EXTENSION_IN * M_PER_IN + 1e-6
    while z <= top:
        parts.append(box(0, front, z - rung / 2, z + rung / 2, inside, rung, "metal"))
        z += _PITCH_IN * M_PER_IN
    return (rect(0, 0, width, depth),
            rect(0, front, width, rail, fill="metal")), tuple(parts)
