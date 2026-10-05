"""Four-legged side table with a flush chessboard and one closed piece-storage drawer."""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, rect

TABLETOP_THICKNESS_M = 0.05715  # 2 1/4 in., owner-specified
BOARD_SQUARE_COUNT = 8
BOARD_SIDE_FRACTION = 0.80
INLAY_THICKNESS_M = 0.001
LEG_WIDTH_M = 0.0381
LEG_INSET_M = 0.03175
DRAWER_HEIGHT_M = 0.0762
DRAWER_WIDTH_FRACTION = 0.60
DRAWER_DEPTH_FRACTION = 0.65
DRAWER_PANEL_THICKNESS_M = 0.0127
PULL_WIDTH_FRACTION = 0.18
PULL_PROJECTION_M = 0.0127
PULL_THICKNESS_M = 0.00635


def chess_table(width: float, depth: float, height: float) -> Geometry:
    """Front is -y; unspecified joinery and board size are illustrative planning geometry."""
    tabletop_thickness = min(TABLETOP_THICKNESS_M, height * 0.20)
    tabletop_bottom = height - tabletop_thickness
    inlay_thickness = min(INLAY_THICKNESS_M, tabletop_thickness * 0.10)
    inlay_bottom = height - inlay_thickness
    board_side = min(width, depth) * BOARD_SIDE_FRACTION
    square_side = board_side / BOARD_SQUARE_COUNT
    strokes = [rect(0, 0, width, depth, fill="wood")]
    parts = [box(0, 0, tabletop_bottom, inlay_bottom, width, depth, "wood")]

    # The border and squares tile the surface, avoiding coincident faces in the 3D viewer.
    side_border_width = (width - board_side) / 2
    end_border_depth = (depth - board_side) / 2
    for sign in (-1, 1):
        parts.append(box(sign * (board_side + side_border_width) / 2, 0,
                         inlay_bottom, height, side_border_width, depth, "wood"))
        parts.append(box(0, sign * (board_side + end_border_depth) / 2,
                         inlay_bottom, height, board_side, end_border_depth, "wood"))
    for row in range(BOARD_SQUARE_COUNT):
        for column in range(BOARD_SQUARE_COUNT):
            center_x = -board_side / 2 + (column + 0.5) * square_side
            center_y = -board_side / 2 + (row + 0.5) * square_side
            color = "wood" if (row + column) % 2 else "wood-dark"
            strokes.append(rect(center_x, center_y, square_side, square_side,
                                fill=color, weight=DETAIL_WEIGHT))
            parts.append(box(center_x, center_y, inlay_bottom, height,
                             square_side, square_side, color))

    inset = min(LEG_INSET_M, min(width, depth) * 0.10)
    leg_width = min(LEG_WIDTH_M, min(width, depth) * 0.12)
    for sign_x in (-1, 1):
        for sign_y in (-1, 1):
            parts.append(box(sign_x * (width / 2 - inset - leg_width / 2),
                             sign_y * (depth / 2 - inset - leg_width / 2),
                             0, tabletop_bottom, leg_width, leg_width, "wood-dark"))

    drawer_width = width * DRAWER_WIDTH_FRACTION
    drawer_depth = depth * DRAWER_DEPTH_FRACTION
    drawer_height = min(DRAWER_HEIGHT_M, tabletop_bottom * 0.20)
    panel_thickness = min(DRAWER_PANEL_THICKNESS_M,
                          drawer_height * 0.20, drawer_width * 0.10, drawer_depth * 0.10)
    drawer_bottom = tabletop_bottom - drawer_height
    front_y = -depth / 2 + inset
    drawer_center_y = front_y + drawer_depth / 2
    parts.append(box(0, drawer_center_y, drawer_bottom, drawer_bottom + panel_thickness,
                     drawer_width, drawer_depth, "wood"))
    for sign in (-1, 1):
        parts.append(box(sign * (drawer_width - panel_thickness) / 2, drawer_center_y,
                         drawer_bottom + panel_thickness, tabletop_bottom,
                         panel_thickness, drawer_depth, "wood"))
    for face_y in (front_y + panel_thickness / 2,
                   front_y + drawer_depth - panel_thickness / 2):
        parts.append(box(0, face_y, drawer_bottom + panel_thickness, tabletop_bottom,
                         drawer_width - 2 * panel_thickness, panel_thickness, "wood-dark"))
    pull_projection = min(PULL_PROJECTION_M, inset * 0.50)
    pull_thickness = min(PULL_THICKNESS_M, drawer_height * 0.10)
    pull_center_z = drawer_bottom + drawer_height / 2
    parts.append(box(0, front_y - pull_projection / 2,
                     pull_center_z - pull_thickness / 2, pull_center_z + pull_thickness / 2,
                     drawer_width * PULL_WIDTH_FRACTION, pull_projection, "metal"))
    return tuple(strokes), tuple(parts)
