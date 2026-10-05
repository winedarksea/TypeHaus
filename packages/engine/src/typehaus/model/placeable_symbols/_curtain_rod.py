"""Bare curtain hardware, contained in the scheduled rod's W×D×H envelope."""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._frame import (
    Part,
    PartMesh,
    Stroke,
    box,
    depth_cylinder,
    line,
)

# Generic hardware proportions, not a claim about a selected manufacturer's product.
ROUND_SEGMENTS = 32
FINIAL_PROFILE_SEGMENTS = 16
ROD_DIAMETER_M = 0.0254
FINIAL_DIAMETER_M = 0.0381
BRACKET_PLATE_DIAMETER_M = 0.0508
BRACKET_PLATE_THICKNESS_M = 0.003175
BRACKET_ARM_THICKNESS_M = 0.00635
BRACKET_END_INSET_M = 0.0762
COLLAR_LENGTH_M = 0.0127
CENTER_SUPPORT_MIN_WIDTH_M = 1.8288
HARDWARE_COLOR = "metal-black"


def _turned_solid(profile: list[tuple[float, float, float, float]],
                  y: float, z: float) -> Part:
    """Revolve (x, radius, axial normal, radial normal) with hard end-cap edges."""
    positions, normals, triangles = [], [], []
    for x, radius, axial_normal, radial_normal in profile:
        for segment in range(ROUND_SEGMENTS):
            angle = math.tau * segment / ROUND_SEGMENTS
            cosine, sine = math.cos(angle), math.sin(angle)
            positions.append((x, y + radius * cosine, z + radius * sine))
            normals.append((axial_normal, radial_normal * cosine, radial_normal * sine))
    for course in range(len(profile) - 1):
        for segment in range(ROUND_SEGMENTS):
            following = (segment + 1) % ROUND_SEGMENTS
            a, b = course * ROUND_SEGMENTS + segment, (course + 1) * ROUND_SEGMENTS + segment
            c, d = course * ROUND_SEGMENTS + following, (course + 1) * ROUND_SEGMENTS + following
            if profile[course][1] > 0:
                triangles.append((a, c, b))
            if profile[course + 1][1] > 0:
                triangles.append((c, d, b))
    for (x, radius, _, _), sign in ((profile[0], -1), (profile[-1], 1)):
        if radius == 0:
            continue
        base = len(positions)
        positions.append((x, y, z))
        normals.append((float(sign), 0.0, 0.0))
        for segment in range(ROUND_SEGMENTS):
            angle = math.tau * segment / ROUND_SEGMENTS
            positions.append((x, y + radius * math.cos(angle), z + radius * math.sin(angle)))
            normals.append((float(sign), 0.0, 0.0))
        for segment in range(ROUND_SEGMENTS):
            a, b = base + 1 + segment, base + 1 + (segment + 1) % ROUND_SEGMENTS
            triangles.append((base, b, a) if sign < 0 else (base, a, b))
    bounds = [(min(point[axis] for point in positions), max(point[axis] for point in positions))
              for axis in range(3)]
    mesh: PartMesh = {"positions": tuple(positions), "normals": tuple(normals),
                      "triangles": tuple(triangles)}
    return {"center": tuple((low + high) / 2 for low, high in bounds),
            "size": tuple(high - low for low, high in bounds), "color": HARDWARE_COLOR,
            "points": (), "shape": "mesh", "mesh": mesh}


def _shaft(left: float, right: float, radius: float, y: float, z: float) -> Part:
    return _turned_solid([(left, radius, 0.0, 1.0), (right, radius, 0.0, 1.0)], y, z)


def _ball_finial(center_x: float, radius: float, y: float, z: float) -> Part:
    profile = []
    for step in range(FINIAL_PROFILE_SEGMENTS + 1):
        angle = -math.pi / 2 + math.pi * step / FINIAL_PROFILE_SEGMENTS
        axial, radial = math.sin(angle), math.cos(angle)
        # Exact poles avoid sliver triangles and leave a watertight turned surface.
        ring_radius = 0.0 if step in (0, FINIAL_PROFILE_SEGMENTS) else radius * radial
        profile.append((center_x + radius * axial, ring_radius, axial, radial))
    return _turned_solid(profile, y, z)


def curtain_rod(width: float, depth: float, height: float
                ) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    """Round rod, ball finials and projecting supports; no fabric or curtain rings.

    Local +y is the wall side, matching the other wall-hung furniture symbols. The long
    rod gains a middle support without changing its placement or scheduled dimensions.
    """
    finial_radius = min(FINIAL_DIAMETER_M / 2, height * 0.375, depth / 4, width / 12)
    rod_radius = min(ROD_DIAMETER_M / 2, finial_radius * 2 / 3)
    plate_radius = min(BRACKET_PLATE_DIAMETER_M / 2, height / 2, width / 12)
    plate_thickness = min(BRACKET_PLATE_THICKNESS_M, depth / 12)
    arm_thickness = min(BRACKET_ARM_THICKNESS_M, rod_radius / 2)
    collar_length = min(COLLAR_LENGTH_M, width / 24)
    rod_y, rod_z = -depth / 2 + finial_radius, height / 2
    shaft_end = width / 2 - finial_radius * 2
    parts = [_shaft(-shaft_end, shaft_end, rod_radius, rod_y, rod_z)]
    for sign in (-1, 1):
        parts.append(_ball_finial(sign * (width / 2 - finial_radius), finial_radius,
                                 rod_y, rod_z))
        collar_center = sign * (shaft_end - collar_length / 2)
        parts.append(_shaft(collar_center - collar_length / 2,
                            collar_center + collar_length / 2, rod_radius * 1.15, rod_y, rod_z))
    support_x = shaft_end - min(BRACKET_END_INSET_M, shaft_end / 3)
    support_positions = [-support_x, support_x]
    if width >= CENTER_SUPPORT_MIN_WIDTH_M:
        support_positions.append(0.0)
    plate_y = depth / 2 - plate_thickness / 2
    arm_back = depth / 2 - plate_thickness
    for x in support_positions:
        parts.append(depth_cylinder(x, plate_y, rod_z, plate_radius, plate_thickness,
                                    HARDWARE_COLOR))
        # The arm intersects both its backplate and the saddle beneath the rod.
        parts.append(box(x, (rod_y + arm_back) / 2,
                         rod_z - rod_radius - arm_thickness, rod_z - rod_radius,
                         arm_thickness, arm_back - rod_y, HARDWARE_COLOR))
        parts.append(_shaft(x - collar_length / 2, x + collar_length / 2,
                            rod_radius + arm_thickness, rod_y, rod_z))
    return (line((-width / 2, rod_y), (width / 2, rod_y)),), tuple(parts)
