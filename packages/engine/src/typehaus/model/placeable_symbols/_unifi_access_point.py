"""U6 Pro reference massing; the face points down on ceilings and along -Y on walls.

The published envelope is exact; the turned profile and status-ring proportions are
visual approximations from Ubiquiti's product images, not fabrication geometry.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.model.placeable_symbols._frame import Part, Stroke, ellipse, rect


@dataclass(frozen=True)
class UniFiAccessPointGeometryConfig:
    segments: int = 64
    # Radius / overall radius, distance from face / overall thickness.
    housing_profile: tuple[tuple[float, float], ...] = (
        (0.0, 0.0), (0.36, 0.0), (0.43, 0.035), (0.60, 0.10),
        (0.78, 0.20), (0.91, 0.34), (0.98, 0.48), (1.0, 0.60),
        (0.99, 0.72), (0.95, 0.82), (0.87, 0.89), (0.0, 0.89),
    )
    status_ring_profile: tuple[tuple[float, float], ...] = (
        (0.38, 0.001), (0.42, 0.021), (0.42, 0.041), (0.38, 0.021),
    )
    mounting_radius_fraction: float = 0.69
    mounting_front_fraction: float = 0.88


UNIFI_ACCESS_POINT_GEOMETRY = UniFiAccessPointGeometryConfig()
UNIFI_ACCESS_POINT_SYMBOLS = frozenset({"unifi-u6-pro-ceiling", "unifi-u6-pro-wall"})


def _turned_part(profile: tuple[tuple[float, float], ...], radius: float,
                 thickness: float, color: str, *, closed: bool = False,
                 smooth: bool = False) -> Part:
    """Turn a meridian; smooth the housing while keeping hardware edges crisp."""
    segments = UNIFI_ACCESS_POINT_GEOMETRY.segments
    positions, normals, triangles = [], [], []
    edges = tuple(zip(profile if closed else profile[:-1],
                      (*profile[1:], profile[0]) if closed else profile[1:], strict=True))
    edge_normals = []
    for (r0, a0), (r1, a1) in edges:
        radial_delta, axial_delta = (r1 - r0) * radius, (a1 - a0) * thickness
        length = math.hypot(radial_delta, axial_delta)
        edge_normals.append((axial_delta / length, -radial_delta / length))
    for edge_index, ((radius0, axial0), (radius1, axial1)) in enumerate(edges):
        radius0, radius1 = radius0 * radius, radius1 * radius
        axial0, axial1 = axial0 * thickness, axial1 * thickness
        base = len(positions)
        for endpoint, (ring_radius, axial) in enumerate(((radius0, axial0), (radius1, axial1))):
            radial_normal, axial_normal = edge_normals[edge_index]
            neighbor = edge_index + (1 if endpoint else -1)
            if smooth and 0 <= neighbor < len(edge_normals):
                radial_normal += edge_normals[neighbor][0]
                axial_normal += edge_normals[neighbor][1]
                length = math.hypot(radial_normal, axial_normal)
                radial_normal, axial_normal = radial_normal / length, axial_normal / length
            for segment in range(segments):
                angle = math.tau * segment / segments
                cosine, sine = math.cos(angle), math.sin(angle)
                positions.append((ring_radius * cosine, ring_radius * sine, axial))
                normals.append((radial_normal * cosine, radial_normal * sine, axial_normal))
        for segment in range(segments):
            following = (segment + 1) % segments
            a, b = base + segment, base + following
            c, d = a + segments, b + segments
            if radius0 > 0:
                triangles.append((a, b, c))
            if radius1 > 0:
                triangles.append((b, d, c))
    low = tuple(min(point[axis] for point in positions) for axis in range(3))
    high = tuple(max(point[axis] for point in positions) for axis in range(3))
    return {"center": tuple((a + b) / 2 for a, b in zip(low, high, strict=True)),
            "size": tuple(b - a for a, b in zip(low, high, strict=True)),
            "color": color, "points": (), "shape": "mesh",
            "mesh": {"positions": tuple(positions), "normals": tuple(normals),
                     "triangles": tuple(triangles)}}


def _wall_orientation(part: Part, depth: float, height: float) -> Part:
    # A proper rotation preserves winding: +Z becomes the wall-facing +Y axis.
    def point(position):
        x, y, z = position
        return x, z - depth / 2, height / 2 - y

    mesh = part["mesh"]
    return {**part, "center": point(part["center"]),
            "size": (part["size"][0], part["size"][2], part["size"][1]),
            "mesh": {"positions": tuple(point(p) for p in mesh["positions"]),
                     "normals": tuple((x, z, -y) for x, y, z in mesh["normals"]),
                     "triangles": mesh["triangles"]}}


def _access_point(width: float, depth: float, height: float, *, wall: bool
                  ) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    config = UNIFI_ACCESS_POINT_GEOMETRY
    radius = min(width, height if wall else depth) / 2
    thickness = depth if wall else height
    parts = (
        _turned_part(config.housing_profile, radius, thickness, "plastic-white", smooth=True),
        _turned_part(config.status_ring_profile, radius, thickness,
                     "unifi-status-blue", closed=True),
        _turned_part(((0.0, config.mounting_front_fraction),
                      (config.mounting_radius_fraction, config.mounting_front_fraction),
                      (config.mounting_radius_fraction, 1.0), (0.0, 1.0)),
                     radius, thickness, "metal"),
    )
    if wall:
        return (rect(0, 0, width, depth),), tuple(
            _wall_orientation(part, depth, height) for part in parts)
    return (ellipse(0, 0, radius, radius),), parts


def unifi_u6_pro_ceiling(width: float, depth: float, height: float):
    return _access_point(width, depth, height, wall=False)


def unifi_u6_pro_wall(width: float, depth: float, height: float):
    return _access_point(width, depth, height, wall=True)
