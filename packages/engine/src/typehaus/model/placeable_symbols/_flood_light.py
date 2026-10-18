"""An underside-mounted, shielded flood with a visibly adjustable head.

The pose is a design allowance, not manufacturer photometry. Local -y is the throw;
the lens and visor share its downward axis so exports cannot turn it into a wall pack.
"""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._frame import box, line, rect
from typehaus.model.placeable_symbols._mesh import mesh_part

FLOOD_DOWNWARD_AIM_DEGREES = 66.0
FLOOD_BEAM_DEGREES = 60.0
_BOX_TRIANGLES = ((0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                  (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                  (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7))
_HINGE_SEGMENTS = 24


def flood_head_direction() -> tuple[float, float, float]:
    angle = math.radians(FLOOD_DOWNWARD_AIM_DEGREES)
    return 0.0, -math.cos(angle), -math.sin(angle)


def _head_dimensions(depth: float, height: float) -> tuple[float, float]:
    return min(depth * 0.58, height * 0.48), min(depth * 0.20, height * 0.16)


def flood_lens_center(width: float, depth: float, height: float) -> tuple[float, float, float]:
    _, thickness = _head_dimensions(depth, height)
    center = (0.0, -depth * 0.08, height * 0.30)
    return tuple(center[i] + flood_head_direction()[i] * thickness * 0.54 for i in range(3))


def _head_box(center, width, face_height, thickness, color):
    direction = flood_head_direction()
    vertical = (0.0, direction[2], -direction[1])
    positions = [tuple(center[i] + x * width / 2 * (1 if i == 0 else 0)
                       + y * thickness / 2 * direction[i]
                       + z * face_height / 2 * vertical[i] for i in range(3))
                 for x, y, z in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                                 (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))]
    return mesh_part(positions, [(a, c, b) for a, b, c in _BOX_TRIANGLES], color)


def _hinge(center, radius, length):
    """A horizontal axle across the head's pitch joint, shared as triangles everywhere."""
    positions = [(center[0] + side * length / 2,
                  center[1] + radius * math.cos(math.tau * i / _HINGE_SEGMENTS),
                  center[2] + radius * math.sin(math.tau * i / _HINGE_SEGMENTS))
                 for side in (-1, 1) for i in range(_HINGE_SEGMENTS)]
    positions.extend(((center[0] - length / 2, center[1], center[2]),
                      (center[0] + length / 2, center[1], center[2])))
    triangles = []
    for i in range(_HINGE_SEGMENTS):
        following = (i + 1) % _HINGE_SEGMENTS
        triangles.extend(((i, following, i + _HINGE_SEGMENTS),
                          (following, following + _HINGE_SEGMENTS, i + _HINGE_SEGMENTS),
                          (2 * _HINGE_SEGMENTS, following, i),
                          (2 * _HINGE_SEGMENTS + 1, i + _HINGE_SEGMENTS,
                           following + _HINGE_SEGMENTS)))
    return mesh_part(positions, triangles, "metal-black")


def flood_light(width: float, depth: float, height: float):
    head_height, thickness = _head_dimensions(depth, height)
    direction = flood_head_direction()
    vertical = (0.0, direction[2], -direction[1])
    center = (0.0, -depth * 0.08, height * 0.30)
    housing = "luminaire-housing"
    strokes = (rect(0, depth * 0.08, width * 0.55, depth * 0.55, fill=housing),
               rect(0, -depth * 0.08, width * 0.90, depth * 0.55, fill=housing),
               line((-width * 0.35, -depth * 0.20), (-width * 0.48, -depth * 0.48)),
               line((width * 0.35, -depth * 0.20), (width * 0.48, -depth * 0.48)))
    parts = [
        box(0, depth * 0.08, height * 0.82, height, width * 0.55, depth * 0.55, housing),
        box(0, depth * 0.08, height * 0.37, height * 0.86,
            width * 0.18, depth * 0.18, housing),
        _hinge((0, depth * 0.08, height * 0.59),
               min(depth * 0.12, height * 0.08), width * 0.28),
        _head_box(center, width * 0.90, head_height, thickness, housing),
        _head_box(flood_lens_center(width, depth, height), width * 0.76,
                  head_height * 0.80, thickness * 0.08, "lamp"),
    ]
    # A top visor and side cheeks project past the lens, shielding its bright face.
    visor_center = tuple(center[i] + vertical[i] * head_height * 0.50
                         + direction[i] * thickness * 0.70 for i in range(3))
    parts.append(_head_box(visor_center, width * 0.94, head_height * 0.08,
                           thickness * 1.20, housing))
    for side in (-1, 1):
        cheek_center = (side * width * 0.44,
                        center[1] + direction[1] * thickness * 0.70,
                        center[2] + direction[2] * thickness * 0.70)
        parts.append(_head_box(cheek_center, width * 0.06, head_height,
                               thickness * 1.20, housing))
    return strokes, tuple(parts)
