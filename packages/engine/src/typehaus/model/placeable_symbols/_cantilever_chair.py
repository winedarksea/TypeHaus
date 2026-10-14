"""A cantilevered wooden chair: bent wood side members, a plywood seat shell, a back panel.

Local frame as every builder: origin at the footprint centre, ``+y`` toward the back, ``z = 0``
at the floor. Each side is one bent member: a rear foot, a leg up to the seat and on to the back
post, and a forward arm that springs down to a front foot. A steel cross rail joins the rear
legs. The product page gives the envelope, seat height and materials, not the frame joinery, so
the member path is an illustrative cantilever.

Joints are read at the LYCKAN envelope (inches) and scaled by fraction to the declared box, so a
register-sized or sectional-sized footprint still draws the same chair.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, circle, rect
from typehaus.model.placeable_symbols._plant_primitives import slender_segment

# The envelope the joints below were read at: width, depth, height, in inches.
WIDTH_IN, DEPTH_IN, HEIGHT_IN = 17.75, 20.125, 32.625
INCH = 0.0254
SEAT_TOP_IN = 18.125
SEAT_DEPTH_IN = 16.5
ARM_CENTRE_IN = 17.1  # the cantilever arm's centreline; its top carries the seat shell
MEMBER_RADIUS_IN = 0.42
# Joints of each side member as (depth, height) in inches from the floor and centre.
FRONT_FOOT = (-9.2, 0.0)
FRONT_SPRING = (-8.9, 8.5)
ARM_FRONT = (-7.6, ARM_CENTRE_IN)
ARM_REAR = (6.6, ARM_CENTRE_IN)
REAR_FOOT = (6.9, 0.0)
BACK_TOP = (7.4, 32.0)
CROSS_RAIL = (6.8, 6.0)  # depth and height of the steel rail between the rear legs
CROSS_RAIL_RADIUS_IN = 0.2
PANEL_DEPTH_IN = 7.6  # back panel centre, thickness 0.8"
PANEL_THICKNESS_IN = 0.8
PANEL_HALF_WIDTH_IN = 8.0
PANEL_BOTTOM_IN, PANEL_TOP_IN = 20.5, 31.5


def cantilever_chair(width: float, depth: float, height: float) -> Geometry:
    """Plan: seat, back band and the four feet. Model: seat, back panel, bent members, rail."""
    # One uniform scale for the members, set by the plan box, so the plan glyph does not
    # depend on the object's height.
    scale = min(width / (WIDTH_IN * INCH), depth / (DEPTH_IN * INCH))
    radius = MEMBER_RADIUS_IN * INCH * scale
    seat_depth = SEAT_DEPTH_IN / DEPTH_IN * depth
    half_x = width / 2 - radius

    def at(x: float, point: tuple[float, float]) -> tuple[float, float, float]:
        """A joint, clamped so a member never sinks through the floor or rises past the top."""
        z = min(max(point[1] / HEIGHT_IN * height, radius), height - radius)
        return (x, point[0] / DEPTH_IN * depth, z)

    def y_of(point: tuple[float, float]) -> float:
        return point[0] / DEPTH_IN * depth

    panel_y = PANEL_DEPTH_IN / DEPTH_IN * depth
    panel_thickness = PANEL_THICKNESS_IN / DEPTH_IN * depth
    panel_width = PANEL_HALF_WIDTH_IN * 2 / WIDTH_IN * width
    strokes = [rect(0, 0, width, seat_depth, fill="wood"),
               rect(0, panel_y, panel_width, panel_thickness, fill="wood-dark",
                    weight=DETAIL_WEIGHT)]
    seat_bottom = (ARM_CENTRE_IN / HEIGHT_IN * height) + radius
    parts = [
        box(0, 0, seat_bottom, SEAT_TOP_IN / HEIGHT_IN * height, width, seat_depth, "wood"),
        box(0, panel_y, PANEL_BOTTOM_IN / HEIGHT_IN * height, PANEL_TOP_IN / HEIGHT_IN * height,
            panel_width, panel_thickness, "wood"),
    ]
    arm = (FRONT_FOOT, FRONT_SPRING, ARM_FRONT, ARM_REAR)
    for sign in (-1, 1):
        x = sign * half_x
        strokes.extend((circle(x, y_of(FRONT_FOOT), radius, fill="wood-dark"),
                        circle(x, y_of(REAR_FOOT), radius, fill="wood-dark")))
        for start, end in zip(arm, arm[1:], strict=False):
            parts.append(slender_segment(at(x, start), at(x, end), radius, "wood"))
        parts.append(slender_segment(at(x, ARM_REAR), at(x, REAR_FOOT), radius, "wood"))
        parts.append(slender_segment(at(x, ARM_REAR), at(x, BACK_TOP), radius, "wood"))
    rail_radius = CROSS_RAIL_RADIUS_IN * INCH * scale
    parts.append(slender_segment(at(-half_x, CROSS_RAIL), at(half_x, CROSS_RAIL),
                                 rail_radius, "metal"))
    return tuple(strokes), tuple(parts)
