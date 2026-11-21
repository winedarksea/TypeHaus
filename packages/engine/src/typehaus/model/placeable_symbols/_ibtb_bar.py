"""nVent ERICO IBTB intersystem bonding termination bar, back at +y.

Elliott/nVent specification sheet: bronze bar, 4 in long, 2.01 in wide, 1.41 in (36 mm) deep.
Five bonding terminals (#14-#6) and one #6-#2 GEC lay-in (nVent spec, per the catalog
Product). Mounting is face-on, so it is drawn as a bar 4 L x 2.01 H x 1.41 D. The clear
terminal cover, screw layout and mounting holes are representative: no drawing was read.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._led_frame import ProductFrame

LONG, THICK, TALL = 4.0, 1.41, 2.01
BAR_T, COVER_T = 0.95, THICK
SCREW_U = tuple(0.42 + 0.52 * i for i in range(5))
LUG_U0, LUG_U1 = 2.85, 3.75


def ibtb_bar(width, depth, height):
    f = ProductFrame(LONG, THICK, TALL, width, depth, height)
    mid = TALL / 2
    parts = [
        f.slab(0, LONG, 0, BAR_T, 0, TALL, "brass"),
        # Mounting ears are the bar's own ends, each with a screw head.
        f.cylinder(.2, BAR_T + .05, .3, .1, .1, 1, "metal"),
        f.cylinder(LONG - .2, BAR_T + .05, TALL - .3, .1, .1, 1, "metal"),
        # GEC lay-in lug: open channel with its own screw.
        f.slab(LUG_U0, LUG_U1, BAR_T, BAR_T + .22, .25, TALL - .25, "brass"),
        f.cylinder((LUG_U0 + LUG_U1) / 2, BAR_T + .3, mid, .24, .16, 1, "metal"),
    ]
    for u in SCREW_U:  # bonding terminals: screw heads under the cover
        parts.append(f.cylinder(u, BAR_T + .2, mid, .17, .4, 1, "metal-black"))
    # Insulating cover over the five terminals only; the lug stays open.
    parts.append(f.slab(.08, 2.75, BAR_T, COVER_T, .2, TALL - .2, "seal"))
    strokes = (f.outline(0, LONG, 0, COVER_T, fill="brass"),
               f.outline(.08, 2.75, BAR_T, COVER_T, fill="seal"))
    return strokes, tuple(parts)
