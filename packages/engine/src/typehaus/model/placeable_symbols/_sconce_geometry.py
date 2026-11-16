"""Product-coordinate solids for wall lights; +y is the wall, z=0 the body bottom."""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.model.placeable_symbols._frame import Part, box
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

ROUND_SEGMENTS = 48
BLACK = "metal-black"


@dataclass(frozen=True)
class SconceFrame:
    """Scale measured/estimated product inches into a caller's declared envelope."""

    width: float
    depth: float
    height: float
    nominal: tuple[float, float, float]

    def point(self, x: float, projection: float, z: float) -> tuple[float, float, float]:
        return (x * self.width / self.nominal[0],
                self.depth / 2 - projection * self.depth / self.nominal[1],
                z * self.height / self.nominal[2])

    def block(self, x: float, projection: float, bottom: float, top: float,
              width: float, depth: float, color: str = BLACK) -> Part:
        cx, cy, _ = self.point(x, projection, 0)
        return box(cx, cy, bottom * self.height / self.nominal[2],
                   top * self.height / self.nominal[2], width * self.width / self.nominal[0],
                   depth * self.depth / self.nominal[1], color)

    def wall_plate(self, projection: float, z: float, radius_x: float,
                   radius_z: float, thickness: float, color: str = BLACK) -> Part:
        rings = [[self.point(radius_x * math.cos(angle), projection + offset,
                             z + radius_z * math.sin(angle))
                  for angle in _angles()]
                 for offset in (-thickness / 2, thickness / 2)]
        return _capped_rings(rings, color)

    def turned(self, projection: float, profile: tuple[tuple[float, float], ...],
               color: str = BLACK, *, hollow: bool = False, fluting_depth: float = 0) -> Part:
        """(radius, z) profile; a hollow profile closes through its inner return wall."""
        rings = [[self.point((radius - fluting_depth * (index % 2)) * math.cos(angle),
                             projection + (radius - fluting_depth * (index % 2))
                             * math.sin(angle), z)
                  for index, angle in enumerate(_angles())] for radius, z in profile]
        if not hollow:
            return _capped_rings(rings, color)
        positions = [point for ring in rings for point in ring]
        triangles = _ring_sides(len(rings), closed=True)
        return mesh_part(positions, outward(positions, triangles), color)

    def bent_rod(self, path: tuple[tuple[float, float], ...], radius: float) -> Part:
        """Sweep a circular rod along a smooth side-elevation (projection, z) path."""
        rings = []
        for index, (projection, z) in enumerate(path):
            before, after = path[max(0, index - 1)], path[min(len(path) - 1, index + 1)]
            tangent = math.atan2(after[1] - before[1], after[0] - before[0])
            rings.append([self.point(radius * math.cos(angle),
                                     projection - radius * math.sin(angle) * math.sin(tangent),
                                     z + radius * math.sin(angle) * math.cos(tangent))
                          for angle in _angles()])
        return _capped_rings(rings, BLACK)


def _angles():
    return (math.tau * index / ROUND_SEGMENTS for index in range(ROUND_SEGMENTS))


def _ring_sides(count: int, *, closed: bool = False) -> list[tuple[int, int, int]]:
    triangles = []
    for section in range(count if closed else count - 1):
        following = (section + 1) % count
        for index in range(ROUND_SEGMENTS):
            a = section * ROUND_SEGMENTS + index
            b = section * ROUND_SEGMENTS + (index + 1) % ROUND_SEGMENTS
            c = following * ROUND_SEGMENTS + index
            d = following * ROUND_SEGMENTS + (index + 1) % ROUND_SEGMENTS
            triangles.extend(((a, b, c), (b, d, c)))
    return triangles


def _capped_rings(rings, color: str) -> Part:
    positions = [point for ring in rings for point in ring]
    triangles = _ring_sides(len(rings))
    for section in (0, len(rings) - 1):
        ring = rings[section]
        center = tuple(sum(point[axis] for point in ring) / ROUND_SEGMENTS for axis in range(3))
        center_index = len(positions)
        positions.append(center)
        offset = section * ROUND_SEGMENTS
        for index in range(ROUND_SEGMENTS):
            a, b = offset + index, offset + (index + 1) % ROUND_SEGMENTS
            triangles.append((center_index, b, a) if section == 0 else (center_index, a, b))
    return mesh_part(positions, outward(positions, triangles), color)
