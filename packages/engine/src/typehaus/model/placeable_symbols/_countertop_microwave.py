"""Countertop microwave (Panasonic NN-SN686S layout), front toward local -y.

Door on the left ~74% of the face with a dark viewing window and a vertical pull handle on
its latch edge; the control column on the right carries the display, keypad and dial.
"""

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, line, rect

DOOR_FRAC = 0.74
FOOT_RATIO = 0.02
SKIN_T = 0.012  # front shell thickness; every front detail sits inside it


def countertop_microwave(width: float, depth: float, height: float) -> Geometry:
    front = -depth / 2
    foot = height * FOOT_RATIO
    door_w = width * DOOR_FRAC
    door_cx = -width / 2 + door_w / 2
    panel_w = width - door_w
    panel_cx = width / 2 - panel_w / 2
    t = min(SKIN_T, depth * 0.04)
    skin_cy = front + t / 2
    body_d = depth - t
    body_cy = front + t + body_d / 2
    z0, z1 = foot, height
    face_h = z1 - z0

    strokes = (
        rect(0, 0, width, depth, fill="appliance-steel"),
        line((-width / 2 + door_w, front), (-width / 2 + door_w, depth / 2),
             weight=DETAIL_WEIGHT),
        rect(door_cx, front + depth * 0.12, door_w * 0.8, depth * 0.2, weight=DETAIL_WEIGHT),
    )
    parts = [
        box(0, body_cy, z0, z1, width, body_d, "appliance-steel"),
        # Door skin, then the viewing window and handle each on their own plane.
        box(door_cx, skin_cy, z0 + face_h * 0.02, z1 - face_h * 0.02,
            door_w * 0.99, t * 0.5, "appliance-steel"),
        box(door_cx - door_w * 0.02, front + t * 0.15, z0 + face_h * 0.12, z1 - face_h * 0.12,
            door_w * 0.80, t * 0.3, "metal-black"),
        box(door_cx + door_w * 0.43, front + t * 0.5, z0 + face_h * 0.15, z1 - face_h * 0.15,
            min(0.016, width * 0.03), t, "appliance-steel"),
        # Control column: black fascia, display, keypad, dial.
        box(panel_cx, front + t * 0.3, z0 + face_h * 0.02, z1 - face_h * 0.02,
            panel_w * 0.92, t * 0.6, "metal-black"),
        box(panel_cx, front + t * 0.5, z1 - face_h * 0.22, z1 - face_h * 0.10,
            panel_w * 0.70, t * 0.3, "screen"),
        box(panel_cx, front + t * 0.5, z0 + face_h * 0.36, z1 - face_h * 0.32,
            panel_w * 0.70, t * 0.3, "appliance-steel"),
        box(panel_cx, front + t * 0.5, z0 + face_h * 0.12, z0 + face_h * 0.30,
            panel_w * 0.40, t, "appliance-steel"),
    ]
    for dx in (-width / 2 + width * 0.06, width / 2 - width * 0.06):  # four feet
        for cy in (front + depth * 0.15, depth / 2 - depth * 0.15):
            parts.append(box(dx, cy, 0, foot, min(0.025, width * 0.05),
                             min(0.025, depth * 0.05), "metal-black"))
    return strokes, tuple(parts)
