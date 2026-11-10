"""Simplified WashTower: two round glazed doors and a shared center console.

Internal proportions approximate LG's WKHC252HBA product photograph; the caller owns
the overall envelope. Front is local -y. No controls or service dimensions are inferred.
"""

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import box, depth_cylinder, line, rect
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

DOOR_SEGMENTS = 64
BODY_COLOR = "laundry-black-steel"
MACHINE_HEIGHT_BANDS = ((0.02, 0.49), (0.55, 0.99))
DOOR_RADIUS_WIDTH_RATIO = 0.39
DOOR_RADIUS_CELL_HEIGHT_RATIO = 0.43
GLASS_RADIUS_RATIO = 0.83
FRONT_LAYERS_DEPTH_RATIOS = (0.0, 0.025, 0.04, 0.055, 0.16)


def _opening_shell(center_z, outer_radius, inner_radius, front_y, back_y, color,
                   rectangle_half_size=None):
    """Closed annular extrusion, optionally with a rectangular outer perimeter.

    The face and rim have actual holes so transparent glass reveals a recessed drum,
    rather than the solid appliance box immediately behind a translucent patch.
    """
    positions, triangles = [], []
    for y, inner in ((front_y, False), (front_y, True),
                     (back_y, False), (back_y, True)):
        for index in range(DOOR_SEGMENTS):
            angle = 2 * math.pi * index / DOOR_SEGMENTS
            cosine, sine = math.cos(angle), math.sin(angle)
            radius = inner_radius if inner else outer_radius
            if rectangle_half_size is not None and not inner:
                half_width, half_height = rectangle_half_size
                radius = 1 / max(abs(cosine) / half_width, abs(sine) / half_height)
            positions.append((radius * cosine, y, center_z + radius * sine))
    # Join the four loops around the annulus with consistent winding.
    for first, second in ((0, 1), (1, 3), (3, 2), (2, 0)):
        for index in range(DOOR_SEGMENTS):
            following = (index + 1) % DOOR_SEGMENTS
            a, b = first * DOOR_SEGMENTS + index, first * DOOR_SEGMENTS + following
            c, d = second * DOOR_SEGMENTS + following, second * DOOR_SEGMENTS + index
            triangles.extend(((a, b, c), (a, c, d)))
    return mesh_part(positions, outward(positions, triangles), color)


def laundry_tower(width: float, depth: float, height: float) -> Geometry:
    front = -depth / 2
    rim_front, glass_front, glass_back, face_front, body_front = (
        front + depth * fraction for fraction in FRONT_LAYERS_DEPTH_RATIOS
    )
    parts = [box(0, (body_front + depth / 2) / 2, 0, height,
                 width, depth / 2 - body_front, BODY_COLOR)]
    for bottom_ratio, top_ratio in MACHINE_HEIGHT_BANDS:
        bottom, top = height * bottom_ratio, height * top_ratio
        center_z = (bottom + top) / 2
        radius = min(width * DOOR_RADIUS_WIDTH_RATIO,
                     (top - bottom) * DOOR_RADIUS_CELL_HEIGHT_RATIO)
        glass_radius = radius * GLASS_RADIUS_RATIO
        parts.extend((
            _opening_shell(center_z, radius, radius, face_front, body_front,
                           BODY_COLOR, (width / 2, (top - bottom) / 2)),
            _opening_shell(center_z, radius, glass_radius, rim_front, face_front,
                           "metal-black"),
            _opening_shell(center_z, glass_radius, glass_radius * 0.96,
                           glass_back, body_front, "appliance-steel"),
            depth_cylinder(0, (glass_front + glass_back) / 2, center_z,
                           glass_radius, glass_back - glass_front, "glass"),
            depth_cylinder(0, body_front - depth * 0.005, center_z,
                           glass_radius * 0.96, depth * 0.01, "screen"),
        ))
    # The central band is enough to suggest the shared controls at room-view scale.
    parts.extend((
        box(0, (face_front + body_front) / 2, height * 0.49, height * 0.55,
            width, body_front - face_front, "metal-black"),
        box(0, face_front - depth * 0.002, height * 0.505, height * 0.535,
            width * 0.48, depth * 0.004, "screen"),
        box(0, (face_front + body_front) / 2, 0, height * 0.02,
            width, body_front - face_front, "metal-black"),
        box(0, (face_front + body_front) / 2, height * 0.99, height,
            width, body_front - face_front, BODY_COLOR),
    ))
    strokes = (rect(0, 0, width, depth, fill=BODY_COLOR),
               line((-width / 2, face_front), (width / 2, face_front)))
    return strokes, tuple(parts)
