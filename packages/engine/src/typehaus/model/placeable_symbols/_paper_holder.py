"""Pivoting paper-holder hardware; loaded-roll space belongs to installation review."""

from typehaus.model.placeable_symbols._frame import Part, Stroke, box, depth_cylinder, rect

_POST_TO_WIDTH_RATIO = 1.34 / 8.11
_POST_TO_DEPTH_RATIO = 1.34 / 3.34


def pivoting_paper_holder(width: float, depth: float, height: float
                          ) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    # The selected Align's round post diameter equals its published overall height.
    diameter = min(height, width * _POST_TO_WIDTH_RATIO, depth * _POST_TO_DEPTH_RATIO)
    radius = diameter / 2
    post_x = width / 2 - radius
    plate_depth = min(diameter / 6, depth / 8)
    arm_diameter = diameter / 3
    bar_diameter = diameter / 4
    bar_y = -depth / 2 + bar_diameter / 2
    parts = []
    strokes = []
    for x in (-post_x, post_x):
        parts.append(depth_cylinder(x, depth / 2 - plate_depth / 2,
                                    height / 2, radius, plate_depth, "metal"))
        arm_depth = depth - plate_depth - bar_diameter / 2
        parts.append(depth_cylinder(x, depth / 2 - plate_depth - arm_depth / 2,
                                    height / 2, arm_diameter / 2, arm_depth, "metal"))
        strokes.append(rect(x, depth / 2 - plate_depth / 2,
                            diameter, plate_depth, fill="metal"))
    parts.append(box(0, bar_y, (height - bar_diameter) / 2,
                     (height + bar_diameter) / 2, 2 * post_x, bar_diameter, "metal"))
    strokes.append(rect(0, bar_y, 2 * post_x, bar_diameter, fill="metal"))
    return tuple(strokes), tuple(parts)
