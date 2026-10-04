"""Small closed sheet-steel meshes; catalog dimensions enter in inches, IR uses metres."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import cast

from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_ir import GMesh, Vec3

GEOMETRY_TOLERANCE = 1e-10


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _subtract(a: Vec3, b: Vec3) -> Vec3:
    return cast(Vec3, tuple(x - y for x, y in zip(a, b, strict=True)))


def _dot(a: Vec3, b: Vec3) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _triangulate(profile: tuple[Vec3, ...], normal: Vec3) -> list[tuple[int, int, int]]:
    """Ear clipping preserves notches in folded leaves without a heavyweight CAD kernel."""
    dropped_axis = max(range(3), key=lambda i: abs(normal[i]))
    projected = [tuple(p[i] for i in range(3) if i != dropped_axis) for p in profile]

    def turn(a: Sequence[float], b: Sequence[float], c: Sequence[float]) -> float:
        return ((b[0] - a[0]) * (c[1] - a[1])
                - (b[1] - a[1]) * (c[0] - a[0]))

    area = sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(projected, projected[1:] + projected[:1], strict=True))
    sign = 1.0 if area > 0.0 else -1.0
    remaining = list(range(len(profile)))
    triangles = []
    while len(remaining) > 3:
        for station, index in enumerate(remaining):
            previous, following = remaining[station - 1], remaining[(station + 1) % len(remaining)]
            a, b, c = projected[previous], projected[index], projected[following]
            if sign * turn(a, b, c) <= GEOMETRY_TOLERANCE:
                continue
            if any(all(sign * turn(u, v, projected[other]) >= -GEOMETRY_TOLERANCE
                       for u, v in ((a, b), (b, c), (c, a)))
                   for other in remaining if other not in (previous, index, following)):
                continue
            triangles.append((previous, index, following))
            remaining.pop(station)
            break
        else:
            raise ValueError("connector plate profile must be a simple non-degenerate polygon")
    triangles.append((remaining[0], remaining[1], remaining[2]))
    return triangles


def plate_mesh(profile_in: tuple[Vec3, ...], extrusion_in: Vec3) -> GMesh:
    """Extrude a planar, possibly concave catalog outline into a closed thin plate."""
    if len(profile_in) < 3:
        raise ValueError("connector plate needs at least three vertices")
    # A first-triangle normal can face inward when the profile starts at a reflex corner.
    # Newell's full-polygon normal agrees with the perimeter winding for either outline.
    edge_crosses = [_cross(a, b) for a, b in
                   zip(profile_in, profile_in[1:] + profile_in[:1], strict=True)]
    normal = cast(Vec3, tuple(sum(cross[i] for cross in edge_crosses) for i in range(3)))
    orientation = _dot(normal, extrusion_in)
    if abs(orientation) <= GEOMETRY_TOLERANCE:
        raise ValueError("connector plate extrusion must leave its profile plane")
    if any(abs(_dot(normal, _subtract(point, profile_in[0]))) > GEOMETRY_TOLERANCE
           for point in profile_in):
        raise ValueError("connector plate profile must be planar")
    count = len(profile_in)
    positions = tuple(cast(Vec3, tuple(value * M_PER_IN for value in point))
                      for point in profile_in)
    positions += tuple(cast(Vec3, tuple(
        (value + delta) * M_PER_IN for value, delta in zip(point, extrusion_in, strict=True)))
        for point in profile_in)
    cap = _triangulate(profile_in, normal)
    triangles = [(a, c, b) for a, b, c in cap]
    triangles.extend((a + count, b + count, c + count) for a, b, c in cap)
    for a in range(count):
        b = (a + 1) % count
        triangles.extend(((a, b, b + count), (a, b + count, a + count)))
    if orientation < 0.0:
        triangles = [(a, c, b) for a, b, c in triangles]
    return GMesh(positions=positions, triangles=tuple(triangles))


def box_mesh(minimum_in: Vec3, maximum_in: Vec3) -> GMesh:
    """A plate or block with published axis-aligned bounds in inches."""
    if any(b <= a for a, b in zip(minimum_in, maximum_in, strict=True)):
        raise ValueError("connector box dimensions must be positive")
    x0, y0, z0 = minimum_in
    x1, y1, z1 = maximum_in
    return plate_mesh(((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)),
                      (0.0, 0.0, z1 - z0))


def combine_meshes(*meshes: GMesh) -> GMesh:
    positions: list[Vec3] = []
    triangles: list[tuple[int, int, int]] = []
    for mesh in meshes:
        offset = len(positions)
        positions.extend(mesh.positions)
        triangles.extend((a + offset, b + offset, c + offset) for a, b, c in mesh.triangles)
    return GMesh(positions=tuple(positions), triangles=tuple(triangles))


def transform_mesh(mesh: GMesh, origin_m: Vec3 = (0.0, 0.0, 0.0),
                   x_axis: Vec3 = (1.0, 0.0, 0.0), y_axis: Vec3 = (0.0, 1.0, 0.0),
                   z_axis: Vec3 = (0.0, 0.0, 1.0)) -> GMesh:
    """Place a catalog mesh in a joint frame, preserving outward winding when mirrored."""
    axes = (x_axis, y_axis, z_axis)
    determinant = _dot(_cross(x_axis, y_axis), z_axis)
    if abs(determinant) < GEOMETRY_TOLERANCE:
        raise ValueError("connector placement frame must be invertible")

    def vector(point: Vec3) -> Vec3:
        return cast(Vec3, tuple(sum(point[j] * axes[j][i] for j in range(3)) for i in range(3)))

    positions = tuple(cast(Vec3, tuple(a + b for a, b in zip(origin_m, vector(point), strict=True)))
                      for point in mesh.positions)
    triangles = (tuple((a, c, b) for a, b, c in mesh.triangles)
                 if determinant < 0.0 else mesh.triangles)
    normals = tuple(vector(normal) for normal in mesh.normals) if mesh.normals else None
    return replace(mesh, positions=positions, triangles=triangles, normals=normals)


def translate_mesh(mesh: GMesh, offset_m: Vec3) -> GMesh:
    return transform_mesh(mesh, origin_m=offset_m)
