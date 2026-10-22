"""SEKTION bases behind matte-white AXSTAD inset-panel fronts: one door, or three drawers."""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, line, rect
from typehaus.model.placeable_symbols._sektion_seat import (
    BASE_FRAME_HEIGHT_M,
    BASE_HEIGHT_M,
    REVEAL_M,
    SEAT_TOP_THICKNESS_M,
    _carcass,
    _plinth,
)
from typehaus.quantities import inch

DOOR_THICKNESS_M = inch(0.75).meters
# Visual approximation of AXSTAD's profile; IKEA publishes overall door dimensions only.
DOOR_BORDER_M = inch(2).meters
PANEL_RECESS_M = inch(0.25).meters
DRAWER_COUNT = 3


def _front(face_w: float, front: float, door_t: float, bottom: float, top: float) -> list:
    """One AXSTAD front between ``bottom`` and ``top``: a border frame round a recessed panel."""
    border = min(DOOR_BORDER_M, face_w / 4, (top - bottom) / 4)
    recess = min(PANEL_RECESS_M, door_t / 2)
    parts = [box(sign * (face_w - border) / 2, front + door_t / 2,
                 bottom, top, border, door_t, "appliance-white") for sign in (-1, 1)]
    for z0, z1 in ((bottom, bottom + border), (top - border, top)):
        parts.append(box(0, front + door_t / 2, z0, z1,
                         face_w - 2 * border, door_t, "appliance-white"))
    parts.append(box(0, front + (door_t + recess) / 2, bottom + border, top - border,
                     face_w - 2 * border, door_t - recess, "appliance-white"))
    return parts


def _strokes(width: float, depth: float, door_t: float) -> tuple:
    front = -depth / 2
    return (rect(0, 0, width, depth, fill="appliance-white"),
            line((-width / 2, front + door_t), (width / 2, front + door_t),
                 weight=DETAIL_WEIGHT))


def sektion_axstad_base(width: float, depth: float, height: float) -> Geometry:
    """Overall depth includes the door; the carcass stays behind its back face."""
    nominal = BASE_HEIGHT_M + BASE_FRAME_HEIGHT_M + SEAT_TOP_THICKNESS_M
    scale = min(1.0, height / nominal)
    base_h = BASE_HEIGHT_M * scale
    frame_top = height - SEAT_TOP_THICKNESS_M * scale
    front = -depth / 2
    door_t = min(DOOR_THICKNESS_M, depth / 8)
    shelf = base_h + (frame_top - base_h) / 2
    parts = [*_plinth(width, depth, base_h),
             *_carcass(width, depth, base_h, frame_top, front + door_t, (shelf,)),
             box(0, 0, frame_top, height, width, depth, "counter"),
             *_front(width - REVEAL_M, front, door_t,
                     base_h + REVEAL_M / 2, frame_top - REVEAL_M / 2)]
    return _strokes(width, depth, door_t), tuple(parts)


def sektion_axstad_drawers(width: float, depth: float, height: float) -> Geometry:
    """A frame standing on the floor, no plinth, three equal drawer fronts, a 1" top."""
    nominal = BASE_FRAME_HEIGHT_M + SEAT_TOP_THICKNESS_M
    frame_top = height - SEAT_TOP_THICKNESS_M * min(1.0, height / nominal)
    front = -depth / 2
    door_t = min(DOOR_THICKNESS_M, depth / 8)
    pitch = frame_top / DRAWER_COUNT
    parts = [*_carcass(width, depth, 0.0, frame_top, front + door_t),
             box(0, 0, frame_top, height, width, depth, "counter")]
    for index in range(DRAWER_COUNT):
        parts += _front(width - REVEAL_M, front, door_t,
                        index * pitch + REVEAL_M / 2, (index + 1) * pitch - REVEAL_M / 2)
    return _strokes(width, depth, door_t), tuple(parts)
