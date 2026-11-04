"""Flat-shaded triangle meshes shared by generated furniture and plants."""

from __future__ import annotations

import math

import numpy as np

from typehaus.model.placeable_symbols._frame import Part, PartMesh

Point3D = tuple[float, float, float]


def _unit(vector: Point3D) -> Point3D:
    magnitude = math.sqrt(sum(value * value for value in vector))
    return tuple(value / magnitude for value in vector)


def _cross(first: Point3D, second: Point3D) -> Point3D:
    return (first[1] * second[2] - first[2] * second[1],
            first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0])


def outward(positions, triangles) -> list[tuple[int, int, int]]:
    """``triangles`` wound so a closed mesh's signed volume is positive (normals out)."""
    total = 0.0
    for a, b, c in triangles:
        p, q, r = positions[a], positions[b], positions[c]
        total += (p[0] * (q[1] * r[2] - q[2] * r[1]) + p[1] * (q[2] * r[0] - q[0] * r[2])
                  + p[2] * (q[0] * r[1] - q[1] * r[0]))
    return list(triangles) if total >= 0 else [(a, c, b) for a, b, c in triangles]


def mesh_part(positions: list[Point3D], triangles: list[tuple[int, int, int]],
               color: str) -> Part:
    # Split triangle vertices so adjacent faces retain crisp normals.
    corners = np.asarray(positions, dtype=np.float64)[np.asarray(triangles, dtype=np.intp)]
    a, b, c = corners[:, 0], corners[:, 1], corners[:, 2]
    e1, e2 = b - a, c - a
    # Same operation order as _cross/_unit, so the floats match the scalar path bit for bit.
    normal = np.stack([e1[:, 1] * e2[:, 2] - e1[:, 2] * e2[:, 1],
                       e1[:, 2] * e2[:, 0] - e1[:, 0] * e2[:, 2],
                       e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]], axis=1)
    magnitude = np.sqrt(normal[:, 0] * normal[:, 0] + normal[:, 1] * normal[:, 1]
                        + normal[:, 2] * normal[:, 2])
    normal = normal / magnitude[:, None]
    flat = corners.reshape(-1, 3)
    vertices = tuple(map(tuple, flat.tolist()))
    low, high = flat.min(axis=0).tolist(), flat.max(axis=0).tolist()
    mesh: PartMesh = {
        "positions": vertices,
        "triangles": tuple((i, i + 1, i + 2) for i in range(0, len(vertices), 3)),
        "normals": tuple(map(tuple, np.repeat(normal, 3, axis=0).tolist())),
    }
    return {"center": tuple((lo + hi) / 2 for lo, hi in zip(low, high, strict=True)),
            "size": tuple(hi - lo for lo, hi in zip(low, high, strict=True)), "color": color,
            "points": (), "shape": "mesh", "mesh": mesh}
