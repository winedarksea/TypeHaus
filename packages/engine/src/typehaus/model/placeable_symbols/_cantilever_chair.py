"""A cantilevered wooden chair: a bent wood side member on each side under a seat shell and back.

Local frame as every builder: origin at the footprint centre, ``+y`` toward the back, ``z = 0``
at the floor. Each side is ONE continuous bent member, traced from the top of the back post:
down the post to the seat's rear, forward along the seat, round a smooth bend that comes down
to the floor, and back along the floor as a runner. The runner stops short of the back post, so
the lower back is open: the side reads as a ``b``, its bowl at the front and its ascender the
back post. Nothing joins the two sides at the rear, which is what makes it a cantilever.

The product page gives the envelope, seat height and materials, not the frame joinery, so the
member path is an illustrative cantilever.

Joints are read at the LYCKAN envelope (inches) and scaled by fraction to the declared box, so a
register-sized or sectional-sized footprint still draws the same chair.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, line, rect
from typehaus.model.placeable_symbols._plant_primitives import slender_segment

# The envelope the joints below were read at: width, depth, height, in inches.
WIDTH_IN, DEPTH_IN, HEIGHT_IN = 17.75, 20.125, 32.625
INCH = 0.0254
SEAT_TOP_IN = 18.125
SEAT_DEPTH_IN = 16.5
ARM_CENTRE_IN = 17.1  # the seat arm's centreline; its top carries the seat shell
MEMBER_RADIUS_IN = 0.42
# Joints of each side member as (depth, height) in inches from the floor and centre.
ARM_FRONT = (-7.6, ARM_CENTRE_IN)  # where the seat arm leaves the bend
ARM_REAR = (6.6, ARM_CENTRE_IN)  # the seat's rear, where the back post rises
BACK_TOP = (7.4, 32.0)
# The bend is a quadratic curve from the seat arm down to the floor, then the runner.
BEND_CONTROL = (-9.7, 0.0)
FLOOR_CONTACT = (-6.6, 0.0)
RUNNER_END = (3.0, 0.0)  # the open lower back: the runner stops short of the post
BEND_SAMPLES = 8
PANEL_DEPTH_IN = 7.6  # back panel centre, thickness 0.8"
PANEL_THICKNESS_IN = 0.8
PANEL_HALF_WIDTH_IN = 8.0
PANEL_BOTTOM_IN, PANEL_TOP_IN = 20.5, 31.5


def _bend(samples: int) -> tuple[tuple[float, float], ...]:
    """Quadratic bezier from ARM_FRONT through BEND_CONTROL to FLOOR_CONTACT, end included."""
    (x0, z0), (cx, cz), (x1, z1) = ARM_FRONT, BEND_CONTROL, FLOOR_CONTACT
    points = []
    for step in range(1, samples + 1):
        t = step / samples
        u = 1 - t
        points.append((u * u * x0 + 2 * u * t * cx + t * t * x1,
                       u * u * z0 + 2 * u * t * cz + t * t * z1))
    return tuple(points)


def cantilever_chair(width: float, depth: float, height: float) -> Geometry:
    """Plan: seat, back band and each side's runner. Model: seat, back panel, bent members."""
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
    # The side's path from the top of the back post, round the bend, to the open runner end.
    path = (BACK_TOP, ARM_REAR, ARM_FRONT, *_bend(BEND_SAMPLES), RUNNER_END)
    for sign in (-1, 1):
        x = sign * half_x
        strokes.append(line((x, y_of(FLOOR_CONTACT)), (x, y_of(RUNNER_END)),
                            weight=DETAIL_WEIGHT))
        for start, end in zip(path, path[1:], strict=False):
            parts.append(slender_segment(at(x, start), at(x, end), radius, "wood"))
    return tuple(strokes), tuple(parts)
