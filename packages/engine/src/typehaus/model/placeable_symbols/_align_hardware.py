"""Align's round projecting posts and slimmer round crossbar, without hanging goods."""

from typehaus.model.placeable_symbols._frame import Part, Stroke, rect
from typehaus.model.placeable_symbols._round_hardware import round_cylinder

_TUBE_TO_POST_DIAMETER = 0.625 / 1.34
_PIVOT_END_SHARE = 0.16
_PIVOT_CAP_RADIUS_SHARE = 0.96


def align_bar(width: float, depth: float, height: float, *, width_post_ratio: float,
              depth_post_ratio: float, pivoting: bool = False
              ) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    # Plan geometry depends only on the footprint; the 3D post is also limited by height.
    diameter = min(width * width_post_ratio, depth * depth_post_ratio)
    plan_radius = diameter / 2
    plan_post_x = width / 2 - plan_radius
    plan_tube = diameter * _TUBE_TO_POST_DIAMETER
    strokes = [rect(x, 0, diameter, depth, fill="metal") for x in (-plan_post_x, plan_post_x)]
    strokes.append(rect(0, -depth / 2 + plan_radius, 2 * plan_post_x, plan_tube, fill="metal"))
    radius = min(height, diameter) / 2
    post_x = width / 2 - radius
    parts = []
    for x in (-post_x, post_x):
        if pivoting:
            # A recessed circular joint at the nose distinguishes the pivoting carrier.
            cap_depth = min(2 * radius * _PIVOT_END_SHARE, depth / 4)
            parts.append(round_cylinder((x, cap_depth / 2, radius), radius,
                                         depth - cap_depth, axis=1))
            parts.append(round_cylinder((x, -depth / 2 + cap_depth / 2, radius),
                                         radius * _PIVOT_CAP_RADIUS_SHARE, cap_depth, axis=1))
        else:
            parts.append(round_cylinder((x, 0, radius), radius, depth, axis=1))
    parts.append(round_cylinder((0, -depth / 2 + radius, radius),
                                 radius * _TUBE_TO_POST_DIAMETER, 2 * post_x, axis=0))
    return tuple(strokes), tuple(parts)
