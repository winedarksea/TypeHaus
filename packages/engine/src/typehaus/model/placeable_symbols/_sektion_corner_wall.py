"""SEKTION's diagonal-front wall corner, shared by the glyph and collision footprint."""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Point, line, polygon, prism
from typehaus.quantities import inch

CORNER_WALL_LEG_M = inch(15).meters
CORNER_WALL_MODULE_M = inch(26).meters
CORNER_WALL_FRONT_THICKNESS_M = inch(0.875).meters
CORNER_WALL_DOOR_WIDTH_M = inch(14.875).meters
CORNER_WALL_FRONT_REVEAL_M = inch(0.0625).meters


def sektion_corner_wall_points(width: float, depth: float) -> tuple[Point, ...]:
    """Nominal 26-inch legs, backs on +x/+y, a diagonal front toward -x/-y.

    The 15-inch system leg includes the front allowance. Unlike the carousel base,
    this cabinet has a diagonal door rather than an open rectangular notch.
    """
    half_width, half_depth = width / 2, depth / 2
    scale = min(1.0, width / CORNER_WALL_MODULE_M, depth / CORNER_WALL_MODULE_M)
    leg = CORNER_WALL_LEG_M * scale
    return ((-half_width, half_depth - leg), (half_width - leg, -half_depth),
            (half_width, -half_depth), (half_width, half_depth), (-half_width, half_depth))


def sektion_corner_wall(width: float, depth: float, height: float) -> Geometry:
    ring = sektion_corner_wall_points(width, depth)
    first, second = ring[:2]
    diagonal_length = math.dist(first, second)
    tangent = ((second[0] - first[0]) / diagonal_length,
               (second[1] - first[1]) / diagonal_length)
    inward = (-tangent[1], tangent[0])
    scale = min(1.0, width / CORNER_WALL_MODULE_M, depth / CORNER_WALL_MODULE_M)
    reveal = min(CORNER_WALL_FRONT_REVEAL_M, height / 8)
    thickness = CORNER_WALL_FRONT_THICKNESS_M * scale
    end_margin = (diagonal_length - CORNER_WALL_DOOR_WIDTH_M * scale) / 2
    outer_first = tuple(first[i] + tangent[i] * end_margin for i in (0, 1))
    outer_second = tuple(second[i] - tangent[i] * end_margin for i in (0, 1))
    door = (outer_first, outer_second,
            tuple(outer_second[i] + inward[i] * thickness for i in (0, 1)),
            tuple(outer_first[i] + inward[i] * thickness for i in (0, 1)))
    return (polygon(ring, fill="cabinet-cream"), line(first, second)), (
        # The nominal body includes the fixed cheeks beside the narrower door.
        # Its outer envelope is the same polygon used by plan collision checks.
        prism(ring, 0, height, "cabinet-cream"),
        prism(door, reveal, height - reveal, "cabinet-cream-dark"),
    )
