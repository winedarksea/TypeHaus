"""Sit–stand desk massing: walnut top and two telescoping steel T-legs."""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import box, rect

TOP_THICKNESS_M = 0.025
FOOT_HEIGHT_M = 0.03
COLUMN_WIDTH_M = 0.075
SUPPORT_INSET_FRACTION = 0.12
FOOT_DEPTH_FRACTION = 0.90
FRAME_COLOR = "metal-black"
TOP_COLOR = "wood-dark"


def sit_stand_desk(width: float, depth: float, height: float) -> Geometry:
    """Front is -y; the open centre leaves room for knees at seated height."""
    top_thickness = min(TOP_THICKNESS_M, height * 0.12)
    desktop_bottom = height - top_thickness
    foot_height = min(FOOT_HEIGHT_M, desktop_bottom * 0.15)
    column_width = min(COLUMN_WIDTH_M, width * 0.10, depth * 0.20)
    column_depth = min(column_width, depth * 0.15)
    column_center_x = width * (0.5 - SUPPORT_INSET_FRACTION)
    foot_depth = depth * FOOT_DEPTH_FRACTION
    telescoping_joint = foot_height + (desktop_bottom - foot_height) * 0.55
    strokes = [rect(0, 0, width, depth, fill=TOP_COLOR)]
    parts = [box(0, 0, desktop_bottom, height, width, depth, TOP_COLOR)]
    for sign in (-1, 1):
        support_x = sign * column_center_x
        strokes.append(rect(support_x, 0, column_width, foot_depth))
        parts.extend((
            box(support_x, 0, 0, foot_height, column_width, foot_depth, FRAME_COLOR),
            box(support_x, 0, foot_height, telescoping_joint,
                column_width, column_depth, FRAME_COLOR),
            box(support_x, 0, telescoping_joint, desktop_bottom,
                column_width * 0.8, column_depth * 0.8, FRAME_COLOR),
        ))
    return tuple(strokes), tuple(parts)
