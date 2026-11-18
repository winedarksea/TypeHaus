"""MidNite Solar MNSPD surge protector, hung dome-down from a bottom knockout, back at +y.

MidNite MNSPD datasheet dimension drawing: a 3.527 in diameter clear polycarbonate dome,
3.82 in from the dome top to the base of the black neck, 4.425 in overall to the tip of the
1/2 in conduit-knockout nipple, its only mounting. So it hangs from the enclosure it
protects, nipple up through a bottom knockout, and the envelope's top is that enclosure's
underside. The blue MOV housing shows through the dome; one blue status LED. The 24 in leads
run inside the enclosure, so are not drawn. Neck taper, flange and core are representative.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._frame import circle
from typehaus.model.placeable_symbols._led_frame import ProductFrame

DIA, TALL = 3.527, 4.425
NIPPLE = TALL - 3.82
R = DIA / 2
# Measured down from the nipple tip (the enclosure's underside): z0, z1, radius.
NECK = ((NIPPLE, 1.0, 0.6), (1.0, 1.35, 0.9), (1.35, 1.75, 1.25))
FLANGE_Z0, FLANGE_Z1 = 1.75, 2.05


def midnite_mnspd(width, depth, height):
    f = ProductFrame(DIA, DIA, TALL, width, depth, height)

    def disc(d0, d1, radius, color):  # d is depth below the nipple tip
        return f.cylinder(R, R, TALL - (d0 + d1) / 2, radius, d1 - d0, 2, color)

    parts = [disc(0, NIPPLE, 0.42, "metal"), disc(NIPPLE - 0.12, NIPPLE, 0.6, "metal")]
    parts += [disc(d0, d1, radius, "metal-black") for d0, d1, radius in NECK]
    parts += [
        disc(FLANGE_Z0, FLANGE_Z1, R, "metal-black"),
        disc(FLANGE_Z1 + 0.05, TALL - 0.35, 1.3, "midnite-blue"),
        disc(FLANGE_Z1, TALL, 1.62, "seal"),
        disc(TALL - 0.02, TALL, 0.1, "unifi-status-blue"),
    ]
    scale = min(width, depth) / DIA
    strokes = (circle(0.0, 0.0, R * scale, fill="metal-black"),
               circle(0.0, 0.0, 1.62 * scale))
    return strokes, tuple(parts)
