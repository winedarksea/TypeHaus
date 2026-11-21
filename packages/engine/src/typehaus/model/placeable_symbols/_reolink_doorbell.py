"""Reolink Video Doorbell PoE (D340P), black, on its wall plate, back at +y.

Reolink spec sheet (reolink.com/product/reolink-video-doorbell-poe): 133 H x 48 W x 23 T mm,
the thickness including the included mounting plate. Reolink publishes no feature positions
or plate size: the rounded-rectangle face, lens and IR LEDs at the top, PIR below the lens,
round button near the bottom (blue status ring), the plate's thickness and the corner radii
are representative from the product photos. The optional 15 degree wedge is not drawn.
"""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._led_frame import ProductFrame
from typehaus.model.placeable_symbols.receptacles import _depth_extrusion

WIDE, THICK, TALL = 48.0, 23.0, 133.0
PLATE_T, FACE_T, GLASS_T = 3.0, 21.0, 21.8
CORNER = 7.0
LENS_Z, PIR_Z, BUTTON_Z = 114.0, 94.0, 30.0
CORNER_STEPS = 5


def _rounded(f: ProductFrame, u0, u1, z0, z1, radius):
    """Counter-clockwise X/Z outline of a rounded rectangle, in metres."""
    points = []
    for (cu, cz), start in (((u1 - radius, z0 + radius), -90), ((u1 - radius, z1 - radius), 0),
                            ((u0 + radius, z1 - radius), 90), ((u0 + radius, z0 + radius), 180)):
        for step in range(CORNER_STEPS + 1):
            angle = math.radians(start + 90 * step / CORNER_STEPS)
            points.append((f.x(cu + radius * math.cos(angle)),
                           f.z(cz + radius * math.sin(angle))))
    return points


def reolink_doorbell_d340p(width, depth, height):
    f = ProductFrame(WIDE, THICK, TALL, width, depth, height)
    mid = WIDE / 2

    def layer(t0, t1, inset, radius, color):  # y runs -t, so front is the larger t
        return _depth_extrusion(_rounded(f, inset, WIDE - inset, inset, TALL - inset, radius),
                                f.y(t1), f.y(t0), color)

    parts = [
        layer(0, PLATE_T, 3.0, 3.0, "plastic-gray"),
        layer(PLATE_T, FACE_T, 0.0, CORNER, "metal-black"),
        layer(FACE_T, GLASS_T, 2.0, CORNER - 2, "screen"),
    ]
    front = GLASS_T

    def disc(z, radius, t0, t1, color, u=mid):
        return f.cylinder(u, (t0 + t1) / 2, z, radius, t1 - t0, 1, color)

    parts += [
        disc(LENS_Z, 9.0, front, front + .4, "metal-black"),            # lens bezel
        disc(LENS_Z, 6.0, front + .4, front + .8, "clear-glass"),       # lens
        disc(LENS_Z, 3.0, front + .8, front + 1.0, "luminaire-housing"),
        disc(LENS_Z - 3, 1.2, front, front + .4, "seal", u=mid - 14),   # IR LEDs
        disc(LENS_Z - 3, 1.2, front, front + .4, "seal", u=mid + 14),
        f.slab(mid - 8, mid + 8, front, front + .4, PIR_Z - 3, PIR_Z + 3, "seal"),  # PIR
        disc(BUTTON_Z, 9.0, front, front + .4, "metal-black"),          # button bezel
        disc(BUTTON_Z, 8.0, front + .4, front + .6, "unifi-status-blue"),  # status ring
        disc(BUTTON_Z, 6.5, front + .6, front + .9, "metal-black"),     # button
    ]
    strokes = (f.outline(0, WIDE, 0, FACE_T, fill="metal-black"),
               f.outline(3, WIDE - 3, 0, PLATE_T, fill="plastic-gray"))
    return strokes, tuple(parts)
