"""IMO ESS-RSD01 rapid-shutdown initiator: NEMA 4X rotary isolator, back at +y.

Appearance: IMO datasheet ESS-RSD01 0426, dimension drawing and photo. A light-grey
polycarbonate box 98 W x 170 H (180 over the top and bottom mounting ears, holes 160 apart),
base and lid split along the depth, four lid screws, a grey ring round a black knob whose
bar stands 31 mm proud of the lid (107 overall), the handle centre below mid-height, and
M25/20/16/12 stepped knockouts in the top and bottom faces. The handle is drawn ON (bar
vertical, the loop closed); the base/lid split, screw heads and badge are representative.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._led_frame import ProductFrame

WIDE, THICK, TALL = 98.0, 107.0, 180.0
EAR = 5.0                     # mounting ear above and below the 170 body
BODY_T, BASE_T = 76.0, 36.0   # lid face; base/lid joint
HANDLE_Z = 78.0
RING_R, KNOB_R = 33.0, 26.0
KO_R, KO_U = 12.5, (24.0, 74.0)
SCREWS = ((11.5, 15.0), (86.5, 15.0), (11.5, 165.0), (86.5, 165.0))


def imo_ess_rsd01(width, depth, height):
    f = ProductFrame(WIDE, THICK, TALL, width, depth, height)
    mid, top = WIDE / 2, TALL - EAR
    parts = [
        f.slab(0, WIDE, 0, BASE_T, EAR, top, "enclosure-gray"),
        f.slab(.8, WIDE - .8, BASE_T - .6, BASE_T + .6, EAR + .8, top - .8, "plastic-gray"),
        f.slab(.4, WIDE - .4, BASE_T + .6, BODY_T, EAR + .4, top - .4, "enclosure-gray"),
        # IMO badge, upper right of the lid.
        f.slab(68, 90, BODY_T, BODY_T + .5, 150, 161, "imo-blue"),
    ]
    for z0, z1 in ((0, EAR), (top, TALL)):  # ears, each with its mounting screw
        parts.append(f.slab(mid - 8, mid + 8, 0, 4, z0, z1, "enclosure-gray"))
        parts.append(f.cylinder(mid, 4.6, (z0 + z1) / 2, 2.4, 1.2, 1, "metal"))
    for u, z in SCREWS:
        parts.append(f.cylinder(u, BODY_T + .4, z, 3.5, .8, 1, "plastic-gray"))
    for z in (EAR - .3, top + .3):  # stepped knockouts, flush in the end faces
        for u in KO_U:
            parts.append(f.cylinder(u, 22, z, KO_R, .6, 2, "plastic-gray"))
            parts.append(f.cylinder(u, 22, z, KO_R * .64, .8, 2, "plastic-gray"))
    # Handle: grey bezel ring, black knob, vertical bar with its padlock tab.
    parts += [
        f.cylinder(mid, BODY_T + 2.5, HANDLE_Z, RING_R, 5, 1, "plastic-gray"),
        f.cylinder(mid, BODY_T + 9, HANDLE_Z, KNOB_R, 8, 1, "metal-black"),
        f.slab(mid - 7, mid + 7, BODY_T + 13, THICK, HANDLE_Z - 24, HANDLE_Z + 24,
               "metal-black"),
        f.slab(mid - 17, mid - 9, BODY_T + 5, BODY_T + 9, HANDLE_Z - 31, HANDLE_Z - 23,
               "metal-black"),
    ]
    strokes = (f.outline(0, WIDE, 0, BODY_T, fill="enclosure-gray"),
               f.outline(mid - RING_R, mid + RING_R, BODY_T, BODY_T + 5),
               f.outline(mid - 7, mid + 7, BODY_T + 13, THICK, fill="metal-black"))
    return strokes, tuple(parts)
