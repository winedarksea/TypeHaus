"""Diode OMNIDRIVE X "-J": the driver in its own listed junction box; back at +y.

Appearance: Diode OMNIDRIVE X spec sheet, mechanical diagrams pp. 3-4. A flanged base with a
slotted ear at each end, a black powder-coated box whose lid splits into a driver bay and a
wiring bay, and three knockouts (one + two) on the long bottom face. Proportions are the
60 W's (7.40 x 3.74 x 1.59 in); the 200 W case is the same idiom, longer.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._frame import line, rect
from typehaus.model.placeable_symbols._led_frame import ProductFrame

LENGTH, THICK, WIDE = 7.40, 1.59, 3.74
EAR = 0.45
FLANGE_T = 0.06
LID_T = 0.09
INSET_Z = 0.10  # body above the flange's long edges, room for the knockouts below
BAY_SPLIT = 4.64  # driver bay | wiring bay, from the driver end
KO_RADIUS = 0.875 / 2
KO_STATIONS = (1.5, 5.4, 6.35)


def diode_odx_j(width, depth, height):
    f = ProductFrame(LENGTH, THICK, WIDE, width, depth, height)
    body_t = THICK - LID_T
    top = WIDE - INSET_Z
    parts = [
        f.slab(0, LENGTH, 0, FLANGE_T, WIDE * .2, WIDE * .8, "driver-black"),
        f.slab(EAR, LENGTH - EAR, FLANGE_T, body_t, INSET_Z, top, "driver-black"),
        # The lid's two bays, a groove between them.
        f.slab(EAR + .04, BAY_SPLIT - .04, body_t, THICK, INSET_Z + .04, top - .04,
               "driver-black"),
        f.slab(BAY_SPLIT + .04, LENGTH - EAR - .04, body_t, THICK, INSET_Z + .04, top - .04,
               "driver-black"),
    ]
    for u in (EAR / 2, LENGTH - EAR / 2):
        parts.append(f.slab(u - .08, u + .08, FLANGE_T, FLANGE_T + .015,
                            WIDE / 2 - .14, WIDE / 2 + .14, "metal-black"))
    for u in KO_STATIONS:
        parts.append(f.cylinder(u, body_t / 2, INSET_Z / 2, KO_RADIUS, INSET_Z, 2, "metal"))
    strokes = (rect(0, 0, width, depth, fill="driver-black"),
               f.outline(EAR, LENGTH - EAR, FLANGE_T, THICK),
               line((f.x(BAY_SPLIT), f.y(body_t)), (f.x(BAY_SPLIT), f.y(THICK))))
    return strokes, tuple(parts)
