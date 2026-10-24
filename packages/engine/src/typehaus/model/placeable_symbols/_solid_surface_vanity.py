"""Floating 48-inch SEKTION vanity with a seam-bonded white lavatory bowl.

Dimensions follow Bath2's cabinet and bowl envelope; the basin curvature is illustrative.
The rectangular mouth matches the declared countertop cutout exactly.
"""

from math import cos, pi, sin, sqrt

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import box, circle, ellipse, rect
from typehaus.model.placeable_symbols._lav_faucets import faucet_band, lav_faucet
from typehaus.model.placeable_symbols._lav_waste import lav_waste
from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.model.placeable_symbols._sektion_fronts import axstad_front

REFERENCE_DEPTH_IN = 18.0
BOWL_WIDTH_IN = 16.375
BOWL_DEPTH_IN = 13.0
BOWL_CENTER_Y_IN = -1.125
BOWL_DROP_IN = 5.0
TOP_THICKNESS_IN = 0.472
CABINET_BOTTOM_IN = 5.5
CABINET_DEPTH_IN = 15.5
CABINET_HEIGHT_IN = 30.0
DOOR_THICKNESS_IN = 0.75
DOOR_REVEAL_IN = 0.125
FAUCET_REAR_CLEARANCE_M = 2.5 * 0.0254
BASIN_SEGMENTS = 64
BASIN_LEVELS = 12
BASIN_FLOOR_FRACTION = 0.22


def deck_height(height: float, faucet: str = "genta") -> float:
    """Deck below the faucet band, shared with the separately emitted overhang."""
    return height - faucet_band(height, faucet)


def solid_surface_vanity(width: float, depth: float, height: float, *,
                         fronts: tuple[float, ...] = (0.25, 0.375, 0.375),
                         bowl_count: int = 1, faucet: str = "genta",
                         basin_size_in: tuple[float, float, float] | None = None,
                         top_thickness_in: float = TOP_THICKNESS_IN,
                         include_waste: bool = True) -> Geometry:
    if bowl_count < 1 or not fronts or any(f <= 0 for f in fronts) or abs(sum(fronts) - 1) > 1e-9:
        raise ValueError("vanity needs at least one bowl and front fractions summing to one")
    if bowl_count > 1:
        return _multiple_bowls(width, depth, height, fronts, bowl_count, faucet)
    sy = depth / REFERENCE_DEPTH_IN
    deck = deck_height(height, faucet)
    sz = deck / (CABINET_BOTTOM_IN + CABINET_HEIGHT_IN + TOP_THICKNESS_IN)
    top_thickness = min(top_thickness_in * 0.0254, deck * 0.12)
    bowl_w, bowl_d, bowl_drop = basin_size_in or (BOWL_WIDTH_IN, BOWL_DEPTH_IN, BOWL_DROP_IN)
    basin_width = min(bowl_w * 0.0254, width * 0.82)
    basin_depth = min(bowl_d * 0.0254, depth * 0.74)
    basin_y = BOWL_CENTER_Y_IN * sy
    bottom = deck - min(bowl_drop * 0.0254, deck * 0.5)
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

    if include_waste:
        parts.extend(lav_waste(depth, deck, bottom, basin_y))

    cabinet_bottom = CABINET_BOTTOM_IN * sz
    cabinet_top = deck - top_thickness
    cabinet_depth = CABINET_DEPTH_IN * sy
    cabinet_y = -depth / 2 + cabinet_depth / 2
    wall = min(DOOR_THICKNESS_IN * .0254, width * .06)
    parts.append(box(0, cabinet_y, cabinet_bottom, cabinet_bottom + wall,
                     width, cabinet_depth, "appliance-white"))
    for x in (-width / 2 + wall / 2, -width / 4, width / 2 - wall / 2):
        parts.append(box(x, cabinet_y, cabinet_bottom, cabinet_top,
                         wall, cabinet_depth, "appliance-white"))
    reveal = min(DOOR_REVEAL_IN * .0254, width * .01)
    front_y = -depth / 2 + wall / 2
    edge = -width / 2
    for fraction in fronts:
        nominal_width = width * fraction
        x = edge + nominal_width / 2
        edge += nominal_width
        parts.extend(axstad_front(nominal_width - reveal, front_y - wall / 2, wall,
                                  cabinet_bottom, cabinet_top, center_x=x))

    faucet_y = depth / 2 - min(FAUCET_REAR_CLEARANCE_M, depth * 0.16)
    parts.extend(lav_faucet(width, depth, deck, height, faucet_y, faucet))
    return (rect(0, 0, width, depth, fill="porcelain"),
            ellipse(0, basin_y, basin_width / 2, basin_depth / 2),
            circle(0, basin_y, drain_size / 2)), tuple(parts)


def _multiple_bowls(width, depth, height, fronts, count, faucet) -> Geometry:
    """Each cabinet bay retains a full-size bowl; all bays share a continuous deck plane."""
    strokes, parts = [], []
    bay_width = width / count
    for index in range(count):
        offset = -width / 2 + bay_width * (index + 0.5)
        bay_strokes, bay_parts = solid_surface_vanity(
            bay_width, depth, height, fronts=fronts, faucet=faucet)
        strokes.extend({**stroke, "points": tuple((x + offset, y) for x, y in stroke["points"])}
                       for stroke in bay_strokes)
        for part in bay_parts:
            x, y, z = part["center"]
            shifted = {**part, "center": (x + offset, y, z),
                       "points": tuple((x + offset, y) for x, y in part["points"])}
            if "mesh" in part:
                shifted["mesh"] = {**part["mesh"], "positions": tuple(
                    (x + offset, y, z) for x, y, z in part["mesh"]["positions"])}
            parts.append(shifted)
    return tuple(strokes), tuple(parts)
