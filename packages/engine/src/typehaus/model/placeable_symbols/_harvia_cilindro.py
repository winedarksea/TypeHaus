"""US PC110E / HPCS11U1H: shielded stone pillar, front at local -y.

Appearance: Harvia's 2024 US heater catalog, pp. 18–19 (Cilindro H).
The caller owns the 16 × 15 × 45 in envelope. This is exterior visualization,
not an internal heating-element or installation-clearance model.
"""

from __future__ import annotations

import math
import random

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Part
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

SHELL_SEGMENTS = 48
FRONT_GRILLE_COLUMNS = 13
FRONT_GRILLE_ROWS = 13
STONE_LAYERS = 12
STONES_PER_LAYER = 10
STONE_FACETS = 7
BASE_TOP = 0.17
COLLAR_BOTTOM = 0.92
STONE_TOP = 0.958
GUARD_BOTTOM = 0.985

# All component coordinates are fractions of the declared W/D/H; assembling by material
# keeps the many stones and grille wires from becoming hundreds of export objects.
Point3 = tuple[float, float, float]
Solid = tuple[list[Point3], list[tuple[int, int, int]]]


def _annular_strip(radius: float, thickness: float, bottom: float, top: float,
                   start: float = 0, end: float = math.tau) -> Solid:
    segments = max(1, math.ceil(SHELL_SEGMENTS * (end - start) / math.tau))
    closed = end - start == math.tau
    positions = []
    for index in range(segments if closed else segments + 1):
        angle = start + (end - start) * index / segments
        for r, z in ((radius, bottom), (radius, top),
                     (radius - thickness, top), (radius - thickness, bottom)):
            positions.append((r * math.cos(angle), r * math.sin(angle), z))
    triangles = [] if closed else [(0, 2, 1), (0, 3, 2)]
    for index in range(segments):
        next_section = 4 * ((index + 1) % segments if closed else index + 1)
        for edge in range(4):
            a, b = 4 * index + edge, 4 * index + (edge + 1) % 4
            next_a, next_b = next_section + edge, next_section + (edge + 1) % 4
            triangles.extend(((a, b, next_b), (a, next_b, next_a)))
    if not closed:
        last = 4 * segments
        triangles.extend(((last, last + 1, last + 2), (last, last + 2, last + 3)))
    return positions, outward(positions, triangles)


def _cuboid(cx: float, cy: float, bottom: float, top: float,
             width: float, depth: float) -> Solid:
    positions = [(cx + x * width / 2, cy + y * depth / 2, z)
                 for z in (bottom, top) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    triangles = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7)]
    for index in range(4):
        following = (index + 1) % 4
        triangles.extend(((index, following, following + 4),
                          (index, following + 4, index + 4)))
    return positions, triangles


def _stone(cx: float, cy: float, cz: float, seed: int,
           radius: float = 0.105, half_height: float = 0.037) -> Solid:
    rng = random.Random(seed)
    phase = rng.random() * math.tau
    positions = [(cx, cy, cz - half_height), (cx + radius * 0.13, cy, cz + half_height)]
    # Unequal, offset rings give angular rock faces rather than stacked round pebbles.
    for ring in range(2):
        for index in range(STONE_FACETS):
            angle = phase + math.tau * (index + ring * 0.17) / STONE_FACETS
            extent = radius * rng.uniform(0.77, 1)
            positions.append((cx + extent * math.cos(angle),
                              cy + extent * math.sin(angle),
                              cz + half_height * (-0.42 if ring == 0 else 0.40)))
    triangles = []
    for index in range(STONE_FACETS):
        following = (index + 1) % STONE_FACETS
        lower, next_lower = 2 + index, 2 + following
        upper, next_upper = lower + STONE_FACETS, next_lower + STONE_FACETS
        triangles.extend(((0, next_lower, lower), (1, upper, next_upper),
                          (lower, next_lower, next_upper), (lower, next_upper, upper)))
    return positions, outward(positions, triangles)


def _material_mesh(solids: list[Solid], width: float, depth: float,
                   height: float, color: str) -> Part:
    positions, triangles = [], []
    for vertices, faces in solids:
        offset = len(positions)
        positions.extend((x * width, y * depth, z * height) for x, y, z in vertices)
        triangles.extend((a + offset, b + offset, c + offset) for a, b, c in faces)
    return mesh_part(positions, triangles, color)


def harvia_cilindro_pc110e(width: float, depth: float, height: float) -> Geometry:
    # Import here to reuse the established drawing without coupling the appliance registry
    # back to this product-specific builder at module import time.
    from typehaus.model.placeable_symbols.appliances import sauna_heater

    strokes, _ = sauna_heater()(width, depth, height)
    steel = [
        _annular_strip(0.48, 0.018, 0.035, BASE_TOP),
        _cuboid(0, 0, 0.035, 0.043, 0.64, 0.64),
        _annular_strip(0.5, 0.012, BASE_TOP, COLLAR_BOTTOM, -0.10, math.pi + 0.10),
        _annular_strip(0.48, 0.012, BASE_TOP - 0.002, BASE_TOP + 0.014),
        _annular_strip(0.48, 0.014, COLLAR_BOTTOM, 0.95),
        _annular_strip(0.47, 0.009, GUARD_BOTTOM, 1.0),
    ]
    for column in range(FRONT_GRILLE_COLUMNS):
        angle = math.pi + 0.13 + (math.pi - 0.26) * column / (FRONT_GRILLE_COLUMNS - 1)
        steel.append(_annular_strip(0.48, 0.009, BASE_TOP, COLLAR_BOTTOM,
                                    angle - 0.008, angle + 0.008))
    for row in range(1, FRONT_GRILLE_ROWS):
        bottom = BASE_TOP + (COLLAR_BOTTOM - BASE_TOP) * row / FRONT_GRILLE_ROWS
        steel.append(_annular_strip(0.48, 0.009, bottom, bottom + 0.003,
                                    math.pi + 0.10, math.tau - 0.10))
    # Raised lattice above the stones, as on the US heater, rather than a solid lid.
    for offset in (-0.28, 0, 0.28):
        span = 2 * math.sqrt(0.46**2 - offset**2)
        steel.extend((_cuboid(0, offset, GUARD_BOTTOM, GUARD_BOTTOM + 0.004, span, 0.009),
                      _cuboid(offset, 0, GUARD_BOTTOM, GUARD_BOTTOM + 0.004, 0.009, span)))
    for angle in (-math.pi / 4, -3 * math.pi / 4, math.pi / 2):
        steel.append(_cuboid(0.465 * math.cos(angle), 0.465 * math.sin(angle),
                             0.945, GUARD_BOTTOM + 0.004, 0.012, 0.012))
    feet = [_cuboid(x, y, 0, 0.04, 0.09, 0.09)
            for x, y in ((-0.30, -0.26), (0.30, -0.26), (0, 0.32))]
    stones = []
    stone_half_height = (STONE_TOP - BASE_TOP) / (2 * STONE_LAYERS)
    for layer in range(STONE_LAYERS):
        center_z = BASE_TOP + stone_half_height * (2 * layer + 1)
        for index in range(STONES_PER_LAYER):
            angle = math.tau * (index + 0.5 * (layer % 2)) / STONES_PER_LAYER
            stones.append(_stone(0.345 * math.cos(angle), 0.345 * math.sin(angle),
                                 center_z, layer * STONES_PER_LAYER + index,
                                 half_height=stone_half_height))
        # Fill the visible top opening; the hidden interior needs no duplicate rock mass.
        if layer == STONE_LAYERS - 1:
            stones.append(_stone(0, 0, center_z, 400, half_height=stone_half_height))
            for index in range(5):
                angle = math.tau * index / 5
                stones.append(_stone(0.175 * math.cos(angle), 0.175 * math.sin(angle),
                                     center_z, 401 + index, half_height=stone_half_height))
    return strokes, (
        _material_mesh(steel, width, depth, height, "appliance-steel"),
        _material_mesh(stones, width, depth, height, "stone"),
        _material_mesh(feet, width, depth, height, "metal-black"),
    )
