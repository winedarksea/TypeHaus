"""SEKTION frames on a 2x4 plinth: a lift-up seat base, an open high frame, a seat cushion.

Both stand on the BESTA precedent's 3 1/2" 2x4 base with a wall-painted baseboard face
instead of IKEA legs. Dimensions shrink proportionally only when the declared height is short.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, line, rect
from typehaus.quantities import inch

BASE_HEIGHT_M = inch(3.5).meters
BASEBOARD_DEPTH_M = inch(0.75).meters
SEAT_TOP_THICKNESS_M = inch(1).meters
SEAT_FRAME_HEIGHT_M = inch(15).meters
HIGH_FRAME_HEIGHT_M = inch(80).meters
PANEL_M = inch(0.75).meters
BACK_M = inch(0.125).meters
FRONT_M = inch(0.875).meters
REVEAL_M = inch(0.125).meters
GROOVE_HEIGHT_M = inch(0.5).meters
GROOVE_DEPTH_M = inch(0.0625).meters
# Owner-adjustable shelves, frame inches above the frame's bottom panel.
HIGH_SHELVES_INCHES = (15, 30, 45, 60)


def _carcass(width: float, depth: float, z0: float, z1: float, front_y: float,
             shelves: tuple[float, ...] = ()) -> list:
    """Sides, back, bottom and top panels of one frame between ``z0`` and ``z1``."""
    panel = min(PANEL_M, width / 8, depth / 8, (z1 - z0) / 4)
    back_y = depth / 2
    carcass_depth = back_y - front_y
    cy = (front_y + back_y) / 2
    inner = width - 2 * panel
    shelf_depth = carcass_depth - BACK_M
    shelf_cy = cy - BACK_M / 2
    parts = [box(sign * (width / 2 - panel / 2), cy, z0, z1, panel, carcass_depth,
                 "appliance-white") for sign in (-1, 1)]
    parts.append(box(0, back_y - BACK_M / 2, z0, z1, inner, BACK_M, "appliance-white"))
    for z in (z0, z1 - panel, *shelves):
        parts.append(box(0, shelf_cy, z, z + panel, inner, shelf_depth, "appliance-white"))
    return parts


def _plinth(width: float, depth: float, base_h: float) -> list:
    """The 2x4 base: a frame at the back and a baseboard flush with the fronts."""
    board = min(BASEBOARD_DEPTH_M, depth / 8)
    rail = min(inch(1.5).meters, depth / 8)
    return [box(0, depth / 2 - rail / 2, 0, base_h, width, rail, "appliance-white"),
            box(0, -depth / 2 + board / 2, 0, base_h, width, board, "appliance-white")]


def sektion_seat_base(width: float, depth: float, height: float) -> Geometry:
    """A 15" SEKTION frame behind one lift-up VOXTORP front, under a 1" seat top."""
    nominal = BASE_HEIGHT_M + SEAT_FRAME_HEIGHT_M + SEAT_TOP_THICKNESS_M
    scale = min(1.0, height / nominal)
    base_h = BASE_HEIGHT_M * scale
    top_t = SEAT_TOP_THICKNESS_M * scale
    frame_top = height - top_t
    front = -depth / 2
    front_t = min(FRONT_M, depth / 8)
    parts = [*_plinth(width, depth, base_h),
             *_carcass(width, depth, base_h, frame_top, front + front_t),
             box(0, 0, frame_top, height, width, depth, "appliance-white")]
    bottom, top = base_h + REVEAL_M / 2, frame_top - REVEAL_M / 2
    face_w = width - REVEAL_M
    groove_h = min(GROOVE_HEIGHT_M, (top - bottom) / 8)
    parts.append(box(0, front + front_t / 2, bottom, top, face_w, front_t, "porcelain"))
    # A lift-up front is pulled from its bottom edge.
    parts.append(box(0, front + GROOVE_DEPTH_M / 2, bottom, bottom + groove_h,
                     face_w - 2 * PANEL_M, GROOVE_DEPTH_M, "casework-shadow"))
    strokes = (rect(0, 0, width, depth, fill="appliance-white"),
               line((-width / 2, front + front_t), (width / 2, front + front_t),
                    weight=DETAIL_WEIGHT))
    return strokes, tuple(parts)


def sektion_open_high(width: float, depth: float, height: float) -> Geometry:
    """An open SEKTION high frame on the 2x4 base: no fronts, adjustable shelves."""
    scale = min(1.0, height / (BASE_HEIGHT_M + HIGH_FRAME_HEIGHT_M))
    base_h = BASE_HEIGHT_M * scale
    shelves = tuple(base_h + inch(s).meters * scale for s in HIGH_SHELVES_INCHES)
    front = -depth / 2
    parts = [*_plinth(width, depth, base_h),
             *_carcass(width, depth, base_h, height, front, shelves)]
    strokes = (rect(0, 0, width, depth, fill="appliance-white"),
               rect(0, BACK_M / 2, width - 2 * PANEL_M, depth - BACK_M,
                    weight=DETAIL_WEIGHT))
    return strokes, tuple(parts)


def seat_cushion(width: float, depth: float, height: float) -> Geometry:
    """A loose foam cushion: the slab, and its welt seam at mid-thickness."""
    welt = min(inch(0.25).meters, height / 4)
    # The welt is the outermost edge; the foam crowns just inside it.
    parts = (box(0, 0, 0, height, width - welt, depth - welt, "cushion"),
             box(0, 0, height / 2 - welt / 2, height / 2 + welt / 2,
                 width, depth, "upholstery"))
    return (rect(0, 0, width, depth, fill="cushion"),), parts
