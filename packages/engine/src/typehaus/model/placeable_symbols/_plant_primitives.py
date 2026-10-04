"""Curved pots, slender stems and folded leaves for indoor plant symbols."""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._frame import Part, PartMesh

Point3D = tuple[float, float, float]
ROUND_SEGMENTS = 16
LEAF_FOLD_SHARE = 0.12


def _unit(vector: Point3D) -> Point3D:
    magnitude = math.sqrt(sum(value * value for value in vector))
    return tuple(value / magnitude for value in vector)


def _cross(first: Point3D, second: Point3D) -> Point3D:
    return (first[1] * second[2] - first[2] * second[1],
            first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0])


def _mesh_part(positions: list[Point3D], triangles: list[tuple[int, int, int]],
               color: str) -> Part:
    # Split vertices at every triangle: leaf folds and pot rims need crisp normals.
    vertices, normals = [], []
    for first, second, third in triangles:
        a, b, c = positions[first], positions[second], positions[third]
        normal = _unit(_cross(tuple(b[i] - a[i] for i in range(3)),
                              tuple(c[i] - a[i] for i in range(3))))
        vertices.extend((a, b, c))
        normals.extend((normal,) * 3)
    bounds = [(min(point[axis] for point in vertices),
               max(point[axis] for point in vertices)) for axis in range(3)]
    mesh: PartMesh = {
        "positions": tuple(vertices),
        "triangles": tuple((i, i + 1, i + 2) for i in range(0, len(vertices), 3)),
        "normals": tuple(normals),
    }
    return {"center": tuple((low + high) / 2 for low, high in bounds),
            "size": tuple(high - low for low, high in bounds), "color": color,
            "points": (), "shape": "mesh", "mesh": mesh}


def tapered_pot(radius: float, bottom: float, top: float, color: str) -> Part:
    """An open tapered vessel with a rolled rim and a dark soil disc drawn separately."""
    ring_profile = ((radius * 0.72, bottom), (radius, top),
                    (radius * 0.88, top), (radius * 0.65, bottom))
    positions = [(r * math.cos(2 * math.pi * segment / ROUND_SEGMENTS),
                  r * math.sin(2 * math.pi * segment / ROUND_SEGMENTS), z)
                 for r, z in ring_profile for segment in range(ROUND_SEGMENTS)]
    triangles = []
    for course in range(len(ring_profile)):
        next_course = (course + 1) % len(ring_profile)
        for segment in range(ROUND_SEGMENTS):
            following = (segment + 1) % ROUND_SEGMENTS
            a, b = course * ROUND_SEGMENTS + segment, course * ROUND_SEGMENTS + following
            c = next_course * ROUND_SEGMENTS + segment
            d = next_course * ROUND_SEGMENTS + following
            triangles.extend(((a, b, c), (b, d, c)))
    return _mesh_part(positions, triangles, color)


def slender_segment(start: Point3D, end: Point3D, radius: float, color: str) -> Part:
    """A round stem or cord along a 3D segment, rather than its bounding box."""
    direction = _unit(tuple(end[i] - start[i] for i in range(3)))
    reference = (0.0, 0.0, 1.0) if abs(direction[2]) < 0.9 else (1.0, 0.0, 0.0)
    across = _unit(_cross(direction, reference))
    other = _cross(direction, across)
    positions = [tuple(point[i] + radius * (
        across[i] * math.cos(2 * math.pi * segment / ROUND_SEGMENTS)
        + other[i] * math.sin(2 * math.pi * segment / ROUND_SEGMENTS)) for i in range(3))
        for point in (start, end) for segment in range(ROUND_SEGMENTS)]
    triangles = []
    for segment in range(ROUND_SEGMENTS):
        following = (segment + 1) % ROUND_SEGMENTS
        triangles.extend(((segment, following, segment + ROUND_SEGMENTS),
                          (following, following + ROUND_SEGMENTS, segment + ROUND_SEGMENTS)))
    return _mesh_part(positions, triangles, color)


def folded_leaf(center: Point3D, length: float, width: float,
                angle: float, rise: float) -> Part:
    """A pointed leaf with a raised midrib and visible faces on both sides."""
    along = (math.cos(angle), math.sin(angle))
    across = (-along[1], along[0])
    positions = [
        (center[0] - along[0] * length / 2, center[1] - along[1] * length / 2,
         center[2] - rise / 2),
        (center[0] + across[0] * width / 2, center[1] + across[1] * width / 2, center[2]),
        (center[0] + along[0] * length / 2, center[1] + along[1] * length / 2,
         center[2] + rise / 2),
        (center[0] - across[0] * width / 2, center[1] - across[1] * width / 2, center[2]),
        (center[0], center[1], center[2] + width * LEAF_FOLD_SHARE),
    ]
    front = [(edge, (edge + 1) % 4, 4) for edge in range(4)]
    return _mesh_part(positions, front + [(a, c, b) for a, b, c in front], "foliage")
