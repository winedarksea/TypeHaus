"""Folded KBS1Z geometry, from ER-280 Table 7 / Figure 7 and C-C-2019 p.296.

Two 3-inch legs, each with two perpendicular 1.5-inch flanges, 16-gauge steel;
the legs turn 45 degrees at the joint. Twelve open fastener holes distinguish the
four flanges. Hole centres and diameters are illustrative: the published drawing
does not dimension the punching or bend radii. This is not a fabrication template.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.resolve.geometry_ir import GMesh, Vec3


@dataclass(frozen=True)
class KBSGeometryConfig:
    flange_width_m: float = 1.5 * 0.0254
    leg_length_m: float = 3.0 * 0.0254
    steel_thickness_m: float = 0.0598 * 0.0254
    illustrative_hole_radius_m: float = 0.085 * 0.0254
    holes_per_flange: int = 3
    hole_segments: int = 12


KBS_GEOMETRY = KBSGeometryConfig()


def kbs_heel_spacing(config: KBSGeometryConfig = KBS_GEOMETRY) -> float:
    """The least heel-to-heel distance along one bearing face for two KBS1Z not to overlap:
    one's support leg, plus the next one's brace leaf projected back at 45°."""
    return config.leg_length_m + config.flange_width_m * math.sqrt(2.0)


def _add(a: Vec3, b: Vec3, factor: float = 1.0) -> Vec3:
    return tuple(x + factor * y for x, y in zip(a, b, strict=True))


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def kbs_mesh(heel: Vec3, support_axis: Vec3, support_face_axis: Vec3,
             brace_axis: Vec3, brace_face_axis: Vec3, inward_axis: Vec3,
             config: KBSGeometryConfig = KBS_GEOMETRY) -> GMesh:
    """The four folded leaves at a joint; axes are applied in project coordinates.

    The face leaves sit outside the flush exterior face. The returns wrap inward
    onto the support and brace edges, rather than drawing a strap floating in air.
    """
    positions: list[Vec3] = []
    triangles: list[tuple[int, int, int]] = []
    outward = tuple(-n for n in inward_axis)
    for along, across, normal in (
            (support_axis, support_face_axis, outward),
            (support_axis, inward_axis, tuple(-n for n in support_face_axis)),
            (brace_axis, brace_face_axis, outward),
            (brace_axis, inward_axis, tuple(-n for n in brace_face_axis))):
        cell_length = config.leg_length_m / config.holes_per_flange
        for hole in range(config.holes_per_flange):
            origin = _add(heel, along, hole * cell_length)
            _perforated_cell(positions, triangles, origin, along, across, normal,
                             cell_length, config)
    return GMesh(positions=tuple(positions), triangles=tuple(triangles))


def _perforated_cell(positions, triangles, origin, along, across, normal,
                     length: float, config: KBSGeometryConfig) -> None:
    """A rectangular steel cell with an open circular hole, including its cut edge."""
    hx, hy = length / 2.0, config.flange_width_m / 2.0
    # Include corner rays so the outer ring is exactly rectangular, not a rounded envelope.
    angles = sorted({*(2.0 * math.pi * j / config.hole_segments
                       for j in range(config.hole_segments)),
                     *(math.atan2(y, x) % (2.0 * math.pi)
                       for x, y in ((hx, hy), (-hx, hy), (-hx, -hy), (hx, -hy)))})
    count, base = len(angles), len(positions)
    triangle_start = len(triangles)
    outer, inner = [], []
    for angle in angles:
        c, s = math.cos(angle), math.sin(angle)
        reach = min(hx / abs(c) if abs(c) > 1e-12 else math.inf,
                    hy / abs(s) if abs(s) > 1e-12 else math.inf)
        outer.append((hx + reach * c, hy + reach * s))
        inner.append((hx + config.illustrative_hole_radius_m * c,
                      hy + config.illustrative_hole_radius_m * s))
    for thickness in (0.0, config.steel_thickness_m):
        for ring in (outer, inner):
            for x, y in ring:
                positions.append(_add(_add(_add(origin, along, x), across, y),
                                      normal, thickness))
    for j in range(count):
        k = (j + 1) % count
        # Near/far annuli, outer perimeter and the cylindrical punched-hole wall.
        quads = ((j, count + j, count + k, k),
                 (2 * count + j, 2 * count + k, 3 * count + k, 3 * count + j),
                 (j, k, 2 * count + k, 2 * count + j),
                 (count + j, 3 * count + j, 3 * count + k, count + k))
        for a, b, c, d in quads:
            triangles.extend(((base + a, base + b, base + c),
                              (base + a, base + c, base + d)))
    if sum(a * b for a, b in zip(_cross(along, across), normal, strict=True)) < 0.0:
        triangles[triangle_start:] = [(a, c, b) for a, b, c in triangles[triangle_start:]]
