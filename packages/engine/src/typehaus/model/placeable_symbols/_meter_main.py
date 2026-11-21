"""Class 320 ringless lever-bypass meter-main (NEMA 3R), back at +y.

Envelope 20 W x 8 D x 36 H in is the house type's (no catalog number is picked yet; the
shortlist is in plans/TODO-nec-2026.md). Layout follows the Class 320 ringless pattern shared
by the shortlisted makers (Siemens MK0402L1400RLM, Eaton, Milbank): a sealed upper cover with
the glass-fronted register ~8 in below the top and the lever-bypass handle beside it, and a
hinged main-breaker door below with two breaker windows and a hasp. Positions, hinges and
latch are representative, not read off a drawing (the Siemens catalog row, 27.27 x 29 x
6.37 in, is a different size from this envelope).
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._led_frame import ProductFrame

WIDE, THICK, TALL = 20.0, 8.0, 36.0
CAN_T, COVER_T, DOOR_T = 6.4, 7.0, 7.0
SPLIT_Z = 16.0                      # meter cover above, breaker door below
METER_U, METER_Z = 8.5, TALL - 8.0  # register centre, 8 in below the top
BASE_R, GLASS_R = 3.9, 3.1
LEVER_U = 16.4
WINDOW_U = ((2.4, 8.6), (10.2, 16.4))


def meter_main_class320(width, depth, height):
    f = ProductFrame(WIDE, THICK, TALL, width, depth, height)
    side = 0.6
    parts = [
        f.slab(0, WIDE, 0, CAN_T, 0, TALL, "metal"),
        f.slab(side, WIDE - side, CAN_T, COVER_T, SPLIT_Z + .7, TALL - side, "enclosure-gray"),
        f.slab(side, WIDE - side, CAN_T, DOOR_T, side, SPLIT_Z - .7, "enclosure-gray"),
        # Meter: black socket base, the white register, the glass over it.
        f.cylinder(METER_U, COVER_T + .15, METER_Z, BASE_R, .3, 1, "metal-black"),
        f.cylinder(METER_U, COVER_T + .4, METER_Z, 2.4, .2, 1, "appliance-white"),
        f.slab(METER_U - 1.3, METER_U + 1.3, COVER_T + .45, COVER_T + .5, METER_Z + .3,
               METER_Z + 1.3, "metal-black"),
        f.cylinder(METER_U, (COVER_T + .3 + THICK) / 2, METER_Z, GLASS_R, THICK - COVER_T - .3,
                   1, "glass"),
        # Lever bypass: guide plate, pivot, handle.
        f.slab(LEVER_U - 1.2, LEVER_U + 1.2, COVER_T, COVER_T + .3, METER_Z - 5.5, METER_Z + 4.5,
               "metal-black"),
        f.cylinder(LEVER_U, COVER_T + .6, METER_Z + 3, .6, .6, 1, "metal"),
        f.slab(LEVER_U - .4, LEVER_U + .4, COVER_T + .3, THICK - .1, METER_Z - 4.2, METER_Z + 3,
               "metal-black"),
        # Seal/lock hasp on the cover's free edge.
        f.slab(WIDE - 1.9, WIDE - .9, COVER_T, COVER_T + .3, METER_Z - 1.2, METER_Z + 1.2, "metal"),
        # Door latch with padlock hasp.
        f.slab(WIDE - 2.2, WIDE - 1.0, DOOR_T, DOOR_T + .4, 5.5, 9.5, "metal"),
    ]
    for u0, u1 in WINDOW_U:  # breaker windows with the handle in the ON position
        parts.append(f.slab(u0, u1, DOOR_T, DOOR_T + .1, 9.5, 13.5, "driver-black"))
        parts.append(f.slab((u0 + u1) / 2 - 1, (u0 + u1) / 2 + 1, DOOR_T + .1, DOOR_T + .7,
                            11.6, 13, "metal"))
    for z in (2.5, 8.0, 13.0):  # hinge knuckles on the left edge
        parts.append(f.cylinder(side, CAN_T + .3, z, .4, 2.2, 2, "metal"))
    strokes = (f.outline(0, WIDE, 0, CAN_T, fill="metal"),
               f.outline(side, WIDE - side, CAN_T, COVER_T, fill="enclosure-gray"),
               f.outline(METER_U - GLASS_R, METER_U + GLASS_R, COVER_T, THICK, fill="glass"),
               f.outline(LEVER_U - .4, LEVER_U + .4, COVER_T, THICK - .1, fill="metal-black"))
    return strokes, tuple(parts)
