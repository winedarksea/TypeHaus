"""Siemens FirstSurge FS140 whole-house SPD, lying along the wall, back at +y.

Envelope: Siemens FS100P product data, 8 x 4 x 3 in (one FirstSurge enclosure for the
FS60/FS100/FS140). Look: the FirstSurge overview photo and its installation figure, which
lays the unit on its side beside the panel and close-nipples it into the panel's side:
a light-grey polycarbonate body between two metal end caps whose flanges are the mounting
ears, a white label with two green phase LEDs and a red service light, and the nipple at
the ``u = LONG`` end (local +x). Cap depth, label and LED positions and the 3/4 in nipple
(Siemens' FSPD140 successor drawing) are representative.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._led_frame import ProductFrame

LONG, THICK, TALL = 8.0, 3.0, 4.0
LID = THICK - 0.1  # the label and LEDs stand on the lid, inside the envelope
NIPPLE_U, CAP_U = 0.6, 0.5
BODY_U0, BODY_U1 = CAP_U, LONG - NIPPLE_U - CAP_U
MID_Z, NIPPLE_T = TALL / 2, 1.3


def siemens_fs140(width, depth, height):
    f = ProductFrame(LONG, THICK, TALL, width, depth, height)
    parts = [
        f.cylinder(LONG - NIPPLE_U / 2, NIPPLE_T, MID_Z, 0.525, NIPPLE_U, 0, "metal"),
        f.cylinder(LONG - NIPPLE_U + 0.08, NIPPLE_T, MID_Z, 0.75, 0.16, 0, "metal"),  # locknut
        f.slab(BODY_U0, BODY_U1, 0, LID, 0.25, TALL - 0.25, "enclosure-gray"),
        # Lid seam, a shade darker, set into the body's sides.
        f.slab(BODY_U0 - 0.02, BODY_U1 + 0.02, 2.0, 2.1, 0.23, TALL - 0.23, "plastic-gray"),
        f.slab(2.0, 6.6, LID, LID + 0.03, 0.8, 3.2, "plastic-white"),  # label
    ]
    for u0 in (0.0, BODY_U1):  # end caps; the full-height flange is the ear
        parts.append(f.slab(u0, u0 + CAP_U, 0, 2.6, 0.2, TALL - 0.2, "metal"))
        parts.append(f.slab(u0, u0 + CAP_U, 0, 0.12, 0, TALL, "metal"))
    for u, color in ((3.0, "eg4-status-green"), (3.8, "eg4-status-green"),
                     (5.8, "disposal-reset")):
        parts.append(f.cylinder(u, LID + 0.06, 1.4, 0.09, 0.08, 1, color))
    strokes = (f.outline(BODY_U0, BODY_U1, 0, LID, fill="enclosure-gray"),
               f.outline(0, CAP_U, 0, 2.6),
               f.outline(BODY_U1, BODY_U1 + CAP_U, 0, 2.6),
               f.outline(LONG - NIPPLE_U, LONG, NIPPLE_T - 0.525, NIPPLE_T + 0.525))
    return strokes, tuple(parts)
