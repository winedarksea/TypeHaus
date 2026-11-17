"""Mean Well HLG-100H-24A (case 994A) with its RACO 232 / 752 splice box; back at +y.

Appearance: HLG-100H-SPEC 2025-04-10, mechanical page. Body 196 mm finned plus a 12 mm ear
each end (Ø4.2 holes 9.4 mm in from the long edges), 68 W, 38.8 H; glands both ends, the
A-type's Vo/Io pots under caps at the DC end. The AC lead crosses a 20 mm gap into the 4 in
box. Length is along the wall, thickness proud of it, the sheet's width vertical.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._frame import rect
from typehaus.model.placeable_symbols._led_frame import ProductFrame

INCH = 25.4
DRIVER_L, EAR, DRIVER_T, DRIVER_H = 220.0, 12.0, 38.8, 68.0
LEAD_GAP = 20.0
BOX = 4 * INCH
BOX_T, COVER_T = 2.125 * INCH, 0.065 * INCH
TOTAL_L, TOTAL_T, TOTAL_H = DRIVER_L + LEAD_GAP + BOX, BOX_T + COVER_T, BOX
HOLE_INSET, HOLE_D = 9.4, 4.2
EAR_T = 3.0
CORE_T = 26.0
POT_PAD_END = 40.0  # flat face at the DC end the two pot caps sit on
FINS = 9
FIN_Z = 2.4


def meanwell_hlg_100h(width, depth, height):
    f = ProductFrame(TOTAL_L, TOTAL_T, TOTAL_H, width, depth, height)
    z0 = (TOTAL_H - DRIVER_H) / 2
    z1, zc = z0 + DRIVER_H, TOTAL_H / 2
    body_u0, body_u1 = EAR, DRIVER_L - EAR
    parts = [
        f.slab(0, EAR, 0, EAR_T, z0, z1, "metal"),
        f.slab(body_u1, DRIVER_L, 0, EAR_T, z0, z1, "metal"),
        f.slab(body_u0, body_u1, 0, CORE_T, z0, z1, "metal"),
        f.slab(body_u0, POT_PAD_END, CORE_T, CORE_T + 4, z0, z1, "metal"),
    ]
    for u in (EAR / 2, DRIVER_L - EAR / 2):
        for z in (z0 + HOLE_INSET, z1 - HOLE_INSET):
            parts.append(f.slab(u - HOLE_D / 2, u + HOLE_D / 2, EAR_T, EAR_T + 0.6,
                                z - HOLE_D / 2, z + HOLE_D / 2, "metal-black"))
    pitch = (DRIVER_H - 6 - FIN_Z) / (FINS - 1)
    for index in range(FINS):
        bottom = z0 + 3 + index * pitch
        parts.append(f.slab(POT_PAD_END, body_u1, CORE_T, DRIVER_T, bottom, bottom + FIN_Z,
                            "metal"))
    for z in (zc - 10, zc + 10):
        parts.append(f.cylinder((body_u0 + POT_PAD_END) / 2, CORE_T + 6, z, 3.5, 4.0, 1,
                                "metal-black"))
    # Glands over the ears, the DC lead stub, and the AC lead into the box's cord grip.
    for u0, u1 in ((4, EAR), (body_u1, DRIVER_L - 4)):
        parts.append(f.slab(u0, u1, 8, 22, zc - 6, zc + 6, "metal-black"))
    parts += [
        f.slab(0, 4, 12, 19, zc - 3.5, zc + 3.5, "metal-black"),
        f.slab(DRIVER_L - 4, DRIVER_L + LEAD_GAP - 5, 12, 19, zc - 3.5, zc + 3.5,
               "metal-black"),
        f.slab(DRIVER_L + LEAD_GAP - 5, DRIVER_L + LEAD_GAP, 9, 22, zc - 7, zc + 7,
               "appliance-steel"),
    ]
    box_u0 = DRIVER_L + LEAD_GAP
    parts += [
        f.slab(box_u0 + 1, TOTAL_L - 1, 0, BOX_T, 1, TOTAL_H - 1, "appliance-steel"),
        f.slab(box_u0, TOTAL_L, BOX_T, TOTAL_T, 0, TOTAL_H, "appliance-steel"),
    ]
    strokes = (f.outline(0, DRIVER_L, 0, DRIVER_T, fill="metal"),
               f.outline(box_u0, TOTAL_L, 0, TOTAL_T, fill="appliance-steel"),
               rect(0, 0, width, depth))
    return strokes, tuple(parts)
