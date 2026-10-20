"""Purchased adjustable footrest, shown at nominal ten-degree platform inclination."""
import math

from typehaus.model.placeable_symbols._frame import box, rect
from typehaus.model.placeable_symbols._mesh import mesh_part

FOOTREST_NOMINAL_TILT_DEGREES = 10
PLATFORM_THICKNESS_M = .0127
SUPPORT_INSET_FRACTION = .12


def footrest(width, depth, height):
    lower_top = max(PLATFORM_THICKNESS_M, height - depth * math.tan(
        math.radians(FOOTREST_NOMINAL_TILT_DEGREES)))
    vertices = [(x, y, z) for z in (0, PLATFORM_THICKNESS_M)
                for x, y in ((-width / 2, -depth / 2), (width / 2, -depth / 2),
                             (width / 2, depth / 2), (-width / 2, depth / 2))]
    vertices = [(x, y, lower_top - PLATFORM_THICKNESS_M + z
                 + (y + depth / 2) * (height - lower_top) / depth) for x, y, z in vertices]
    triangles = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                 (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                 (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    platform = mesh_part(vertices, triangles, "metal-black")
    supports = tuple(box(sign * width * (.5 - SUPPORT_INSET_FRACTION), 0, 0,
                         lower_top - PLATFORM_THICKNESS_M, width * .08, depth * .75,
                         "metal-black") for sign in (-1, 1))
    return (rect(0, 0, width, depth),), (platform, *supports)
