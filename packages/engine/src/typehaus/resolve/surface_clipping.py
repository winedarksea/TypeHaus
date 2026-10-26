"""Convex sheet pieces clipped by half spaces, including their exposed cut edges.

Keeping closed face polygons until the final tessellation avoids cracks where a thin
fold meets an opening, a mitre, or a roof rake. No optional geometry kernel is needed.
"""

from __future__ import annotations

import math

from typehaus.resolve.geometry_ir import GMesh, Vec3

CLIP_TOLERANCE_M = 1e-9
MINIMUM_FACE_AREA_M2 = 1e-12
Plane = tuple[float, float, float, float]  # a*x + b*y + c*z <= d
Faces = list[list[Vec3]]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b, strict=True))


def face_normal(face):
    origin = face[0]
    normal = [0.0, 0.0, 0.0]
    for a, b in zip(face[1:-1], face[2:], strict=True):
        value = cross(subtract(a, origin), subtract(b, origin))
        normal = [x + y for x, y in zip(normal, value, strict=True)]
    magnitude = math.sqrt(dot(normal, normal))
    return tuple(x / magnitude for x in normal) if magnitude > MINIMUM_FACE_AREA_M2 else None


def box_faces(x0, x1, y0, y1, z0, z1) -> Faces:
    p = [
        (x0, y0, z0),
        (x1, y0, z0),
        (x1, y1, z0),
        (x0, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x1, y1, z1),
        (x0, y1, z1),
    ]
    return [
        [p[i] for i in indices]
        for indices in (
            (3, 2, 1, 0),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (1, 2, 6, 5),
            (2, 3, 7, 6),
            (3, 0, 4, 7),
        )
    ]


def clip_faces(faces: Faces, plane: Plane) -> Faces:
    """Intersect a convex polyhedron with a half space; retain outward winding."""
    normal, limit = plane[:3], plane[3]
    distances = [dot(normal, p) - limit for face in faces for p in face]
    if not distances or min(distances) > CLIP_TOLERANCE_M:
        return []
    if max(distances) <= CLIP_TOLERANCE_M:
        return faces
    result, crossings = [], []
    for face in faces:
        clipped = []
        for a, b in zip(face, face[1:] + face[:1], strict=True):
            da, db = dot(normal, a) - limit, dot(normal, b) - limit
            if da <= CLIP_TOLERANCE_M:
                clipped.append(a)
            if (da < -CLIP_TOLERANCE_M and db > CLIP_TOLERANCE_M) or (
                db < -CLIP_TOLERANCE_M and da > CLIP_TOLERANCE_M
            ):
                t = da / (da - db)
                point = tuple(x + t * (y - x) for x, y in zip(a, b, strict=True))
                clipped.append(point)
                crossings.append(point)
            elif abs(da) <= CLIP_TOLERANCE_M:
                crossings.append(a)
        if len(clipped) >= 3 and face_normal(clipped):
            result.append(clipped)
    unique = list({tuple(round(v, 10) for v in p): p for p in crossings}.values())
    if len(unique) >= 3:
        center = tuple(sum(p[i] for p in unique) / len(unique) for i in range(3))
        first = subtract(unique[0], center)
        second = cross(normal, first)
        unique.sort(
            key=lambda p: math.atan2(
                dot(subtract(p, center), second), dot(subtract(p, center), first)
            )
        )
        if dot(face_normal(unique) or (0, 0, 0), normal) < 0:
            unique.reverse()
        if face_normal(unique):
            result.append(unique)
    return result


def subtract_convex(faces: Faces, planes: list[Plane]) -> list[Faces]:
    """Partition A minus a convex opening without overlapping the retained pieces."""
    # Most panels miss a given opening; avoid splitting them at its other planes.
    if any(
        all(dot(plane[:3], p) >= plane[3] - CLIP_TOLERANCE_M for face in faces for p in face)
        for plane in planes
    ):
        return [faces]
    result = []
    for plane in planes:
        outside = clip_faces(faces, tuple(-v for v in plane))
        if outside:
            result.append(outside)
        faces = clip_faces(faces, plane)
        if not faces:
            break
    return result


def mesh_from_faces(pieces: list[Faces], transform, mirrored: bool) -> GMesh:
    positions, triangles, normals = [], [], []
    for piece in pieces:
        for face in piece:
            world = [transform(p) for p in face]
            if mirrored:
                world.reverse()
            normal = face_normal(world)
            if normal is None:
                continue
            start = len(positions)
            positions.extend(world)
            normals.extend([normal] * len(world))
            for i in range(1, len(world) - 1):
                if face_normal([world[0], world[i], world[i + 1]]):
                    triangles.append((start, start + i, start + i + 1))
    if not all(math.isfinite(v) for p in positions for v in p):
        raise ValueError("Non-finite siding mesh coordinate")
    return GMesh(tuple(positions), tuple(triangles), tuple(normals))
