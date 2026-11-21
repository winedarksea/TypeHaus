"""U6 Pro reference massing; the face points down on ceilings and along -Y on walls.

The published envelope is exact; the turned profile and status-ring proportions are
visual approximations from Ubiquiti's product images, not fabrication geometry.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.placeable_symbols._frame import Part, Stroke, ellipse, rect
from typehaus.model.placeable_symbols._turned_profile import turned_profile


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
        turned_profile(config.housing_profile, radius, thickness, "plastic-white",
                       segments=config.segments, smooth=True),
        turned_profile(config.status_ring_profile, radius, thickness,
                       "unifi-status-blue", segments=config.segments, closed=True),
        turned_profile(((0.0, config.mounting_front_fraction),
                        (config.mounting_radius_fraction, config.mounting_front_fraction),
                        (config.mounting_radius_fraction, 1.0), (0.0, 1.0)),
                       radius, thickness, "metal", segments=config.segments),
    )
    if wall:
        return (rect(0, 0, width, depth),), tuple(
            _wall_orientation(part, depth, height) for part in parts)
    return (ellipse(0, 0, radius, radius),), parts


def unifi_u6_pro_ceiling(width: float, depth: float, height: float):
    return _access_point(width, depth, height, wall=False)


def unifi_u6_pro_wall(width: float, depth: float, height: float):
    return _access_point(width, depth, height, wall=True)
