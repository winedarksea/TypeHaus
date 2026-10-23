"""Dependency-free triangulation of simple planar rings, preserving source indices."""

from __future__ import annotations

from collections.abc import Sequence

_AREA_EPSILON_M2 = 1e-12


def planar_ring_triangles(
    ring: Sequence[tuple[float, float, float]],
) -> list[tuple[int, int, int]]:
    """Ear-clip in the dominant plane; triangles keep the ring's winding.

    Source indices also let sweep consumers share vertices between caps and side faces.
    No GEOS triangulation feature is required, including in the browser's Python runtime.
    """
    if len(ring) < 3:
        return []
    origin = ring[0]
    local = [tuple(value - start for value, start in zip(point, origin, strict=True))
             for point in ring]
    normal = [sum(a[(axis + 1) % 3] * b[(axis + 2) % 3]
                  - a[(axis + 2) % 3] * b[(axis + 1) % 3]
                  for a, b in zip(local, local[1:] + local[:1], strict=True))
              for axis in range(3)]
    drop = max(range(3), key=lambda axis: abs(normal[axis]))
    points = [tuple(value for axis, value in enumerate(point) if axis != drop)
              for point in local]
    area = sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(points, points[1:] + points[:1], strict=True))
    if abs(area) <= _AREA_EPSILON_M2:
        raise ValueError("Cannot triangulate a zero-area planar ring")
    winding = 1 if area > 0 else -1

    def cross(a: int, b: int, c: int) -> float:
        ax, ay = points[a]
        bx, by = points[b]
        cx, cy = points[c]
        return winding * ((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))

    # Preserve the cheap fan for rings it actually tiles, including existing convex stock.
    if all(cross(0, i, i + 1) >= -_AREA_EPSILON_M2 for i in range(1, len(ring) - 1)):
        return [(0, i, i + 1) for i in range(1, len(ring) - 1)]
    remaining = list(range(len(ring)))
    triangles = []
    while len(remaining) > 3:
        for index, b in enumerate(remaining):
            a, c = remaining[index - 1], remaining[(index + 1) % len(remaining)]
            turn = cross(a, b, c)
            if abs(turn) <= _AREA_EPSILON_M2:
                remaining.pop(index)
                break
            if turn < 0:
                continue
            if any(cross(a, b, p) >= -_AREA_EPSILON_M2
                   and cross(b, c, p) >= -_AREA_EPSILON_M2
                   and cross(c, a, p) >= -_AREA_EPSILON_M2
                   for p in remaining if p not in (a, b, c)):
                continue
            triangles.append((a, b, c))
            remaining.pop(index)
            break
        else:
            raise ValueError("Cannot triangulate a non-simple planar ring")
    if cross(*remaining) > _AREA_EPSILON_M2:
        triangles.append((remaining[0], remaining[1], remaining[2]))
    return triangles
