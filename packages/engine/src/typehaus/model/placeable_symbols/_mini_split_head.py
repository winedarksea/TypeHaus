"""Generic wall-mounted mini-split, white moulded plastic with its outlet open toward -y."""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Part, box, line, rect

CASING_CORNER_SEGMENTS = 5
INTAKE_SLOT_COUNT = 7
OUTLET_FIN_COUNT = 11
CASING_COLOR = "appliance-white"


def _rounded_casing(center: tuple[float, float, float], size: tuple[float, float, float],
                    radius: float) -> Part:
    """Round a box's edges with explicit smooth normals, shared by viewer and exports."""
    half = tuple(length / 2 for length in size)
    core = tuple(length - radius for length in half)
    coordinates = [
        [sign * (inner + radius * math.sin(math.pi * step / (2 * CASING_CORNER_SEGMENTS)))
         for sign, steps in ((-1, range(CASING_CORNER_SEGMENTS, -1, -1)),
                             (1, range(CASING_CORNER_SEGMENTS + 1)))
         for step in steps]
        for inner in core
    ]
    positions, normals, triangles = [], [], []
    for axis in range(3):
        first, second = (axis + 1) % 3, (axis + 2) % 3
        for sign in (-1, 1):
            base = len(positions)
            for u in coordinates[first]:
                for v in coordinates[second]:
                    point = [0.0, 0.0, 0.0]
                    point[axis], point[first], point[second] = sign * half[axis], u, v
                    nearest = [max(-inner, min(inner, value))
                               for value, inner in zip(point, core, strict=True)]
                    offset = [value - inner for value, inner in zip(point, nearest, strict=True)]
                    magnitude = math.sqrt(sum(value * value for value in offset))
                    normal = tuple(value / magnitude for value in offset)
                    positions.append(tuple(origin + inner + radius * direction
                                           for origin, inner, direction in
                                           zip(center, nearest, normal, strict=True)))
                    normals.append(normal)
            columns = len(coordinates[second])
            for row in range(len(coordinates[first]) - 1):
                for column in range(columns - 1):
                    a = base + row * columns + column
                    faces = ((a, a + columns, a + columns + 1),
                             (a, a + columns + 1, a + 1))
                    triangles.extend(faces if sign > 0 else
                                     tuple((a, c, b) for a, b, c in faces))
    return {"center": center, "size": size, "color": CASING_COLOR,
            "points": (), "shape": "mesh",
            "mesh": {"positions": tuple(positions), "normals": tuple(normals),
                     "triangles": tuple(triangles)}}


def mini_split_head(width: float, depth: float, height: float) -> Geometry:
    corner = min(depth * 0.14, height * 0.10, width * 0.025)
    opening_top = height * 0.25
    # The lower casing stands behind the outlet, leaving a real recess below the cover.
    parts = [
        _rounded_casing((0, depth * 0.002, (height * 0.997 + opening_top) / 2),
                        (width, depth * 0.996, height * 0.997 - opening_top), corner),
        _rounded_casing((0, depth * 0.12, height * 0.16),
                        (width, depth * 0.76, height * 0.32), corner),
        _rounded_casing((0, -depth * 0.07, height * 0.055),
                        (width * 0.96, depth * 0.82, height * 0.11), corner * 0.45),
        box(0, -depth * 0.28, height * 0.105, opening_top,
            width * 0.88, depth * 0.035, "screen"),
    ]
    for sign in (-1, 1):
        parts.append(_rounded_casing((sign * width * 0.475, -depth * 0.07, height * 0.17),
                                    (width * 0.05, depth * 0.8, height * 0.24),
                                    min(corner * 0.45, width * 0.02)))
    # Pale directional fins sit in the shadow of the long discharge opening.
    for index in range(OUTLET_FIN_COUNT):
        parts.append(box(width * 0.82 * ((index + 0.5) / OUTLET_FIN_COUNT - 0.5),
                         -depth * 0.33, height * 0.12, height * 0.23,
                         width * 0.003, depth * 0.10, CASING_COLOR))
    parts.append(_rounded_casing((0, -depth * 0.40, height * 0.135),
                                (width * 0.88, depth * 0.15, height * 0.027),
                                min(height * 0.012, depth * 0.06, width * 0.01)))
    # Dark intake slots stay on the flat portion of the upper surface.
    for index in range(INTAKE_SLOT_COUNT):
        y = depth * (-0.21 + index * 0.055)
        parts.append(box(0, y, height * 0.997, height, width * 0.84,
                         depth * 0.018, "screen"))
    # A small receiver window suggests controls without a brand or an invented display.
    parts.append(box(width * 0.34, -depth * 0.498, height * 0.34, height * 0.37,
                     width * 0.035, depth * 0.004, "screen"))
    strokes = [rect(0, 0, width, depth, fill=CASING_COLOR),
               line((-width * 0.44, -depth * 0.37), (width * 0.44, -depth * 0.37))]
    return tuple(strokes), tuple(parts)
