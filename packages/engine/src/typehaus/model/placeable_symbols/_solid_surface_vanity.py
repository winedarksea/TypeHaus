"""Floating 48-inch SEKTION vanity with a seam-bonded white lavatory bowl.

Dimensions follow Bath2's cabinet and bowl envelope; the basin curvature is illustrative.
The rectangular mouth matches the declared countertop cutout exactly.
"""

from math import cos, pi, sin, sqrt

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import box, circle, ellipse, rect
from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.model.placeable_symbols._sektion_fronts import axstad_front

REFERENCE_WIDTH_IN = 48.0
REFERENCE_DEPTH_IN = 18.0
BOWL_WIDTH_IN = 16.375
BOWL_DEPTH_IN = 13.0
BOWL_CENTER_Y_IN = -0.5
BOWL_DROP_IN = 5.0
TOP_THICKNESS_IN = 0.472
CABINET_BOTTOM_IN = 5.5
CABINET_DEPTH_IN = 15.5
CABINET_HEIGHT_IN = 30.0
DOOR_THICKNESS_IN = 0.75
DOOR_REVEAL_IN = 0.125
DOOR_BORDER_IN = 2.0
FAUCET_HEIGHT_M = 0.14
BASIN_SEGMENTS = 64
BASIN_LEVELS = 12
BASIN_FLOOR_FRACTION = 0.22


def deck_height(height: float) -> float:
    """Deck below the faucet band, shared with the separately emitted overhang."""
    return height - min(FAUCET_HEIGHT_M, height * 0.16)


def solid_surface_vanity(width: float, depth: float, height: float) -> Geometry:
    sx, sy = width / REFERENCE_WIDTH_IN, depth / REFERENCE_DEPTH_IN
    deck = deck_height(height)
    sz = deck / (CABINET_BOTTOM_IN + CABINET_HEIGHT_IN + TOP_THICKNESS_IN)
    top_thickness = TOP_THICKNESS_IN * sz
    basin_width, basin_depth = BOWL_WIDTH_IN * sx, BOWL_DEPTH_IN * sy
    basin_y = BOWL_CENTER_Y_IN * sy
    bottom = deck - BOWL_DROP_IN * sz
    parts = []
    # Four uninterrupted deck strips leave a real opening, rather than covering the bowl.
    for sign in (-1, 1):
        strip_width = (width - basin_width) / 2
        parts.append(box(sign * (basin_width + strip_width) / 2, 0,
                         deck - top_thickness, deck, strip_width, depth, "porcelain"))
    for edge, mouth in ((-depth / 2, basin_y - basin_depth / 2),
                        (depth / 2, basin_y + basin_depth / 2)):
        parts.append(box(0, (edge + mouth) / 2, deck - top_thickness, deck,
                         basin_width, abs(edge - mouth), "porcelain"))

    vertices, triangles = [], []
    # A rounded floor widens into the rectangular bonding envelope at the deck plane.
    for level in range(BASIN_LEVELS + 1):
        fraction = level / BASIN_LEVELS
        radius = BASIN_FLOOR_FRACTION + (1 - BASIN_FLOOR_FRACTION) * sqrt(fraction)
        for index in range(BASIN_SEGMENTS):
            angle = 2 * pi * index / BASIN_SEGMENTS
            x, y = cos(angle), sin(angle)
            rectangular_blend = 1 + fraction**4 * (1 / max(abs(x), abs(y)) - 1)
            vertices.append((basin_width / 2 * radius * x * rectangular_blend,
                             basin_y + basin_depth / 2 * radius * y * rectangular_blend,
                             bottom + fraction * (deck - bottom)))
    for level in range(BASIN_LEVELS):
        for index in range(BASIN_SEGMENTS):
            following = (index + 1) % BASIN_SEGMENTS
            a, b = level * BASIN_SEGMENTS + index, level * BASIN_SEGMENTS + following
            c, d = a + BASIN_SEGMENTS, b + BASIN_SEGMENTS
            triangles.extend(((a, c, d), (a, d, b)))
    center = len(vertices)
    vertices.append((0, basin_y, bottom))
    triangles.extend((center, index, (index + 1) % BASIN_SEGMENTS)
                     for index in range(BASIN_SEGMENTS))
    parts.append(mesh_part(vertices, triangles, "porcelain"))
    drain_size = min(basin_width, basin_depth) * 0.09
    parts.append(box(0, basin_y, bottom, bottom + top_thickness / 8,
                     drain_size, drain_size, "metal"))

    cabinet_bottom = CABINET_BOTTOM_IN * sz
    cabinet_top = deck - top_thickness
    cabinet_depth = CABINET_DEPTH_IN * sy
    cabinet_y = -depth / 2 + cabinet_depth / 2
    wall = DOOR_THICKNESS_IN * sx
    parts.append(box(0, cabinet_y, cabinet_bottom, cabinet_bottom + wall,
                     width, cabinet_depth, "appliance-white"))
    for x in (-width / 2 + wall / 2, -width / 4, width / 2 - wall / 2):
        parts.append(box(x, cabinet_y, cabinet_bottom, cabinet_top,
                         wall, cabinet_depth, "appliance-white"))
    reveal = DOOR_REVEAL_IN * sx
    front_y = -depth / 2 + wall / 2
    # Preserve the vanity's one 12-inch and two 18-inch doors and its existing envelope.
    for x, nominal_width in ((-3 * width / 8, width / 4),
                             (-width / 16, width * 3 / 8), (5 * width / 16, width * 3 / 8)):
        parts.extend(axstad_front(nominal_width - reveal, front_y - wall / 2, wall,
                                  cabinet_bottom, cabinet_top, center_x=x))

    shaft = min(width, depth) * 0.035
    faucet_y = depth / 2 - depth / 9
    spout_y = basin_y + basin_depth / 4
    parts.extend((box(0, faucet_y, deck, height - shaft, shaft, shaft, "metal"),
                  box(0, (faucet_y + spout_y) / 2, height - shaft, height,
                      shaft, faucet_y - spout_y + shaft, "metal")))
    return (rect(0, 0, width, depth, fill="porcelain"),
            ellipse(0, basin_y, basin_width / 2, basin_depth / 2),
            circle(0, basin_y, drain_size / 2)), tuple(parts)
