"""Thin sheet meshes in metres, including notches and holes, without a CAD dependency."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from typehaus.resolve.geometry_ir import GMesh, Vec2, Vec3

_EPS = 1e-10


def combine_sheets(meshes: Sequence[GMesh]) -> GMesh:
    positions, triangles = [], []
    for mesh in meshes:
        offset = len(positions)
        positions.extend(mesh.positions)
        triangles.extend((a + offset, b + offset, c + offset) for a, b, c in mesh.triangles)
    return GMesh(positions=tuple(positions), triangles=tuple(triangles))


def extruded_quad(points: Sequence[Vec3], extrusion: Vec3) -> GMesh:
    """A convex planar sheet, with outward winding for either handed frame."""
    a, b, c = points[:3]
    u, v = tuple(b[i] - a[i] for i in range(3)), tuple(c[i] - a[i] for i in range(3))
    normal = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
              u[0] * v[1] - u[1] * v[0])
    if sum(normal[i] * extrusion[i] for i in range(3)) < 0:
        points = tuple(reversed(points))
    count = len(points)
    positions = tuple(points) + tuple(tuple(p[i] + extrusion[i] for i in range(3))
                                     for p in points)
    triangles = [(0, i + 1, i) for i in range(1, count - 1)]
    triangles += [(count, count + i, count + i + 1) for i in range(1, count - 1)]
    for i in range(count):
        j = (i + 1) % count
        triangles.extend(((i, j, j + count), (i, j + count, i + count)))
    return GMesh(positions=positions, triangles=tuple(triangles))


def polygon_sheet(rings: Sequence[Sequence[Vec2]], place: Callable[[float, float], Vec3],
                  extrusion: Vec3) -> GMesh:
    """Tile a polygon and its holes with exact trapezoids, then extrude each tile.

    Between consecutive vertex x coordinates every boundary is linear. Even/odd edge
    pairs therefore cover the sheet exactly, including cutouts, on both desktop GEOS and
    Pyodide's older GEOS; no unconstrained triangulation can bridge an obstruction.
    """
    stations = sorted({p[0] for ring in rings for p in ring})
    edges = [(a, b) for ring in rings for a, b in zip(ring, (*ring[1:], ring[0]), strict=True)
             if abs(a[0] - b[0]) > _EPS]
    meshes = []

    def y_at(edge, x):
        (ax, ay), (bx, by) = edge
        return ay + (by - ay) * (x - ax) / (bx - ax)

    for x0, x1 in zip(stations[:-1], stations[1:], strict=True):
        if x1 - x0 <= _EPS:
            continue
        mid = (x0 + x1) / 2
        crossing = sorted((e for e in edges if min(e[0][0], e[1][0]) < mid
                           < max(e[0][0], e[1][0])), key=lambda e: y_at(e, mid))
        if len(crossing) % 2:
            raise ValueError("sheet boundary must have an even number of crossings")
        for lo, hi in zip(crossing[::2], crossing[1::2], strict=True):
            ring = [(x0, y_at(lo, x0)), (x1, y_at(lo, x1)),
                    (x1, y_at(hi, x1)), (x0, y_at(hi, x0))]
            ring = [p for i, p in enumerate(ring) if
                    abs(p[0] - ring[i - 1][0]) + abs(p[1] - ring[i - 1][1]) > _EPS]
            if len(ring) >= 3:
                meshes.append(extruded_quad(tuple(place(*p) for p in ring), extrusion))
    return combine_sheets(meshes)


def sheet_between(a: Vec3, b: Vec3, run: Vec3, thickness_m: float,
                  *, normal_hint: Vec3 | None = None) -> GMesh:
    """One folded leg; a normal hint keeps its sheet faces fixed when the run reverses."""
    import math

    edge = tuple(b[i] - a[i] for i in range(3))
    normal = (run[1] * edge[2] - run[2] * edge[1],
              run[2] * edge[0] - run[0] * edge[2],
              run[0] * edge[1] - run[1] * edge[0])
    magnitude = math.sqrt(sum(v * v for v in normal))
    if magnitude <= _EPS:
        raise ValueError("flashing leg and run must span a sheet")
    sign = (-1 if normal_hint is not None and
            sum(v * h for v, h in zip(normal, normal_hint, strict=True)) < 0 else 1)
    extrusion = tuple(sign * v / magnitude * thickness_m for v in normal)
    return extruded_quad((a, tuple(a[i] + run[i] for i in range(3)),
                          tuple(b[i] + run[i] for i in range(3)), b), extrusion)
