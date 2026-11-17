"""LED controllers and a plug-in driver, back at +y; size from the caller.

Appearance: Gledopto GL-C-001P manual (125 x 37 x 24 mm, screw terminals both ends); IKEA
603.426.61 TRADFRI 30 W driver (285 x 55 x 18 mm, clip-on end cover over the outputs); and
the gasketed PVC NEMA 4X box the GL-C-208M rides in (6 x 6 x 4 in, two cord grips and an M12
breather on the bottom face, which stand below the can inside the same envelope).
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._frame import rect
from typehaus.model.placeable_symbols._led_frame import ProductFrame


def gledopto_gl_c_001p(width, depth, height):
    length, thick, wide, block = 125.0, 24.0, 37.0, 15.0
    f = ProductFrame(length, thick, wide, width, depth, height)
    parts = [f.slab(block, length - block, 0, thick, 0, wide, "plastic-white")]
    # Input V+/V- at one end, the six outputs at the other.
    for u0, screws in ((0, 2), (length - block, 6)):
        parts.append(f.slab(u0, u0 + block, 0, thick * .75, 3, wide - 3, "plastic-gray"))
        pitch = (wide - 10) / max(screws - 1, 1)
        for index in range(screws):
            z = wide / 2 if screws == 1 else 5 + index * pitch
            parts.append(f.cylinder(u0 + block / 2, thick * .75 + 1, z, 1.8, 2.0, 1, "metal"))
    strokes = (rect(0, 0, width, depth, fill="plastic-white"),
               f.outline(block, length - block, 0, thick))
    return strokes, tuple(parts)


def ikea_tradfri_driver(width, depth, height):
    length, thick, wide, cover = 285.0, 18.0, 55.0, 32.0
    f = ProductFrame(length, thick, wide, width, depth, height)
    parts = [f.slab(0, length - cover, 0, thick, 1, wide - 1, "plastic-gray"),
             f.slab(length - cover, length, 0, thick - .8, 0, wide, "plastic-white")]
    for index in range(3):
        z = wide / 2 + (index - 1) * 14
        parts.append(f.slab(length - cover + 9, length - 9, thick - .8, thick,
                            z - 4, z + 4, "metal-black"))
    strokes = (rect(0, 0, width, depth, fill="plastic-gray"),
               f.outline(length - cover, length, 0, thick - .8))
    return strokes, tuple(parts)


def nema_4x_box(width, depth, height):
    side, thick, grip = 6.0, 4.0, 0.75
    f = ProductFrame(side, thick, side, width, depth, height)
    can_t, gasket_t, lid_t = 3.45, 3.52, 3.88
    parts = [
        f.slab(0, side, 0, can_t, grip, side, "plastic-gray"),
        f.slab(.05, side - .05, can_t, gasket_t, grip + .05, side - .05, "metal-black"),
        f.slab(.12, side - .12, gasket_t, lid_t, grip + .12, side - .12, "plastic-gray"),
    ]
    for u in (.45, side - .45):
        for z in (grip + .45, side - .45):
            parts.append(f.cylinder(u, lid_t + .06, z, .14, .12, 1, "metal"))
    for u in (1.6, 3.2):
        parts.append(f.cylinder(u, can_t / 2, grip / 2, .42, grip, 2, "metal-black"))
    parts.append(f.cylinder(4.6, can_t / 2, grip * .7, .3, grip * .6, 2, "plastic-white"))
    strokes = (rect(0, 0, width, depth, fill="plastic-gray"),
               f.outline(.12, side - .12, gasket_t, lid_t))
    return strokes, tuple(parts)
