"""Socketed, shades-down opal vanity lights, shared by plan and 3D consumers."""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Builder
from typehaus.model.placeable_symbols._frame import box, circle, prism, rect

INCH_M = 0.0254
BACKPLATE_WIDTH_M = 7.25 * INCH_M
BACKPLATE_HEIGHT_M = 4.5 * INCH_M
BACKPLATE_DEPTH_M = 0.5 * INCH_M
JUNCTION_HEIGHT_M = 5.5 * INCH_M
SHADE_HEIGHT_SHARE = 0.62
SHADE_WIDTH_M = 4.0 * INCH_M
SHADE_CENTRE_DEPTH_SHARE = -0.10
JUNCTION_HEIGHT_SHARE = 5.5 / 7.5
BACKPLATE_HEIGHT_SHARE = 0.6
ARM_THICKNESS_M = 0.5 * INCH_M


def socketed_vanity_light(count: int, finish: str) -> Builder:
    def build(width: float, depth: float, height: float):
        plate_width = min(BACKPLATE_WIDTH_M, width * 0.9)
        plate_height = min(BACKPLATE_HEIGHT_M, height * BACKPLATE_HEIGHT_SHARE)
        plate_depth = min(BACKPLATE_DEPTH_M, depth * 0.1)
        junction_height = min(JUNCTION_HEIGHT_M, height * JUNCTION_HEIGHT_SHARE)
        arm_thickness = min(ARM_THICKNESS_M, min(width, depth, height) * 0.1)
        plate_y = depth / 2 - plate_depth / 2
        parts = [box(0, plate_y, junction_height - plate_height / 2,
                     min(height, junction_height + plate_height / 2),
                     plate_width, plate_depth, finish)]
        shade_width = min(SHADE_WIDTH_M, width / count * 0.8, depth * 0.8)
        shade_y = SHADE_CENTRE_DEPTH_SHARE * depth
        parts.append(box(0, shade_y, height - arm_thickness, height,
                         width - shade_width, arm_thickness, finish))
        strokes = [rect(0, plate_y, plate_width, plate_depth, fill=finish)]
        for index in range(count):
            centre_x = -width / 2 + shade_width / 2 + index * (width - shade_width) / (count - 1)
            ring = circle(centre_x, shade_y, shade_width / 2)["points"]
            parts.append(prism(ring, 0, height * SHADE_HEIGHT_SHARE, "lamp"))
            parts.append(box(centre_x, shade_y, height * SHADE_HEIGHT_SHARE, height,
                             arm_thickness, arm_thickness, finish))
            strokes.append(circle(centre_x, shade_y, shade_width / 2, fill="glass"))
        return tuple(strokes), tuple(parts)
    return build
