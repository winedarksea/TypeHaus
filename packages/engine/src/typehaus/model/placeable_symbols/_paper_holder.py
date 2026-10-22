"""Pivoting paper-holder hardware; loaded-roll space belongs to installation review."""

from typehaus.model.placeable_symbols._frame import Part, Stroke, box, depth_cylinder, rect


def pivoting_paper_holder(width: float, depth: float, height: float
                          ) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    # The selected Align's round post diameter equals its published overall height.
    diameter = min(height, width / 4, depth / 2)
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
        strokes.append(rect(x - radius, x + radius,
                            depth / 2 - plate_depth, depth / 2, fill="metal"))
    parts.append(box(0, bar_y, (height - bar_diameter) / 2,
                     (height + bar_diameter) / 2, 2 * post_x, bar_diameter, "metal"))
    strokes.append(rect(-post_x, post_x, -depth / 2,
                        -depth / 2 + bar_diameter, fill="metal"))
    return tuple(strokes), tuple(parts)
