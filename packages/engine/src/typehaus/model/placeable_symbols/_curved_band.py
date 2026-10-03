"""Closed ribbon solids following a sampled elevation curve, with smooth face normals."""

from __future__ import annotations

import math
from collections.abc import Sequence

from typehaus.model.placeable_symbols._frame import Part, PartMesh


def curved_elevation_band(samples: Sequence[tuple[float, float, float]], y: float,
                          width: float, lower_offset: float, upper_offset: float,
                          color: str) -> Part:
    """Carry a rectangular band along ``(x, elevation, dz/dx)`` samples.

    Offsets are vertical, keeping adjoining material layers coincident. Analytic slopes
    shade the top and underside smoothly; split edge vertices keep the sides and ends crisp.
    """
    if len(samples) < 2 or width <= 0 or upper_offset <= lower_offset:
        raise ValueError("A curved band needs two samples, positive width and ordered offsets")
    if any(after[0] <= before[0] for before, after in zip(samples[:-1], samples[1:], strict=True)):
        raise ValueError("Curved band samples must increase along the width axis")

    positions: list[tuple[float, float, float]] = []
    normals: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    profile = ((y - width / 2, lower_offset), (y + width / 2, lower_offset),
               (y + width / 2, upper_offset), (y - width / 2, upper_offset))
    for edge in range(len(profile)):
        base = len(positions)
        for x, elevation, slope in samples:
            length = math.hypot(slope, 1.0)
            normal = ((slope / length, 0.0, -1.0 / length), (0.0, 1.0, 0.0),
                      (-slope / length, 0.0, 1.0 / length), (0.0, -1.0, 0.0))[edge]
            for plan_y, offset in (profile[edge], profile[(edge + 1) % len(profile)]):
                positions.append((x, plan_y, elevation + offset))
                normals.append(normal)
        for step in range(len(samples) - 1):
            a = base + step * 2
            triangles.extend(((a, a + 1, a + 3), (a, a + 3, a + 2)))

    for sample, outward in ((samples[0], -1.0), (samples[-1], 1.0)):
        x, elevation, _ = sample
        base = len(positions)
        positions.extend((x, plan_y, elevation + offset) for plan_y, offset in profile)
        normals.extend(((outward, 0.0, 0.0),) * len(profile))
        cap = ((0, 2, 1), (0, 3, 2)) if outward < 0 else ((0, 1, 2), (0, 2, 3))
        triangles.extend(tuple(base + index for index in triangle) for triangle in cap)

    bounds = tuple((min(point[axis] for point in positions),
                    max(point[axis] for point in positions)) for axis in range(3))
    mesh: PartMesh = {"positions": tuple(positions), "triangles": tuple(triangles),
                      "normals": tuple(normals)}
    center = [(low + high) / 2 for low, high in bounds]
    size = [high - low for low, high in bounds]
    return {"center": (center[0], center[1], center[2]), "size": (size[0], size[1], size[2]),
            "color": color, "points": (), "shape": "mesh", "mesh": mesh}
