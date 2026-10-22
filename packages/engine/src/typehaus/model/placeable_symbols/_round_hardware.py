"""Smooth closed hardware cylinders shared by viewer, glTF and IFC tessellation."""

import math

from typehaus.model.placeable_symbols._frame import Part

ROUND_SEGMENTS = 32


def round_cylinder(center: tuple[float, float, float], radius: float, length: float,
                   *, axis: int, color: str = "brushed-nickel") -> Part:
    """Axis is 0/1/2 for local width/depth/height; caps keep separate flat normals."""
    radial_axes = ((axis + 1) % 3, (axis + 2) % 3)
    positions, normals, triangles = [], [], []
    for sign in (-1, 1):
        for segment in range(ROUND_SEGMENTS):
            angle = math.tau * segment / ROUND_SEGMENTS
            normal = [0.0, 0.0, 0.0]
            normal[radial_axes[0]], normal[radial_axes[1]] = math.cos(angle), math.sin(angle)
            point = [center[i] + radius * normal[i] for i in range(3)]
            point[axis] += sign * length / 2
            positions.append(tuple(point))
            normals.append(tuple(normal))
    for segment in range(ROUND_SEGMENTS):
        following = (segment + 1) % ROUND_SEGMENTS
        a, b = segment, following
        c, d = segment + ROUND_SEGMENTS, following + ROUND_SEGMENTS
        triangles.extend(((a, b, c), (b, d, c)))
    for sign in (-1, 1):
        base = len(positions)
        normal = tuple(float(sign) if i == axis else 0.0 for i in range(3))
        point = list(center)
        point[axis] += sign * length / 2
        positions.append(tuple(point))
        normals.append(normal)
        ring_start = 0 if sign < 0 else ROUND_SEGMENTS
        positions.extend(positions[ring_start:ring_start + ROUND_SEGMENTS])
        normals.extend([normal] * ROUND_SEGMENTS)
        for segment in range(ROUND_SEGMENTS):
            a, b = base + 1 + segment, base + 1 + (segment + 1) % ROUND_SEGMENTS
            triangles.append((base, b, a) if sign < 0 else (base, a, b))
    size = tuple(length if i == axis else 2 * radius for i in range(3))
    return {"center": center, "size": size, "color": color, "points": (), "shape": "mesh",
            "mesh": {"positions": tuple(positions), "normals": tuple(normals),
                     "triangles": tuple(triangles)}}
