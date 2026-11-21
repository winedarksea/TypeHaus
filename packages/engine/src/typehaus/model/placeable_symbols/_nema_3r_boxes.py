"""NEMA 3R screw-cover wall boxes, back at +y: the comms entrance and the PV junction box.

Commodity enclosures with no catalog number named in the house, so the envelopes are the
types' own (8 W x 4 D x 8 H and 6 W x 6 D x 4 H in) and everything drawn is representative:
a rain-tight body, a blank cover that overlaps it with a drip lip, four corner screws
and conduit hubs on the bottom face (a gasketed 3R box takes its
entries low).
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._led_frame import ProductFrame

COVER_T, LIP = 0.55, 0.18   # cover depth; cover overhang past the body
HUB_H, HUB_R = 0.3, 0.42    # bottom hub boss


def _screw_cover_box(width, depth, height, size_in, hub_us):
    w_in, t_in, h_in = size_in
    f = ProductFrame(w_in, t_in, h_in, width, depth, height)
    body_t = t_in - COVER_T
    z0 = HUB_H
    parts = [
        f.slab(LIP, w_in - LIP, 0, body_t, z0, h_in - LIP, "metal"),
        # Cover: blank, overlapping the body on every side with a bottom drip edge.
        f.slab(0, w_in, body_t, t_in, z0 - .05, h_in, "enclosure-gray"),
    ]
    for u in hub_us:
        parts.append(f.cylinder(u, body_t / 2, HUB_H / 2, HUB_R, HUB_H, 2, "metal-black"))
    for u in (.35, w_in - .35):
        for z in (z0 + .3, h_in - .35):
            parts.append(f.cylinder(u, t_in - .05, z, .18, .1, 1, "metal"))
    strokes = (f.outline(LIP, w_in - LIP, 0, body_t, fill="metal"),
               f.outline(0, w_in, body_t, t_in, fill="enclosure-gray"))
    return strokes, tuple(parts)


def comms_entrance_box(width, depth, height):
    return _screw_cover_box(width, depth, height, (8.0, 4.0, 8.0), (2.4, 5.6))


def pv_junction_box(width, depth, height):
    return _screw_cover_box(width, depth, height, (6.0, 6.0, 4.0), (1.8, 3.0, 4.2))
