"""Flat-shaded triangle meshes shared by generated furniture and plants."""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._frame import Part, PartMesh

Point3D = tuple[float, float, float]


def _unit(vector: Point3D) -> Point3D:
    magnitude = math.sqrt(sum(value * value for value in vector))
    return tuple(value / magnitude for value in vector)


def _cross(first: Point3D, second: Point3D) -> Point3D:
    return (first[1] * second[2] - first[2] * second[1],
            first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0])


def mesh_part(positions: list[Point3D], triangles: list[tuple[int, int, int]],
               color: str) -> Part:
    # Split triangle vertices so adjacent faces retain crisp normals.
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

