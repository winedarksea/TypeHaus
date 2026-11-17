"""OMVI 3i ceiling-mounted reference geometry, facing local -Y.

Envelope from Reolink's product page; housing and optical details are visual
approximations of its product photos, not fabrication geometry.
"""

import math
from dataclasses import dataclass

from typehaus.model.placeable_symbols._frame import Part, ellipse
from typehaus.model.placeable_symbols._round_hardware import round_cylinder


@dataclass(frozen=True)
class PanTiltCameraGeometryConfig:
    segments: int = 48
    latitude_rings: int = 24
    upper_bottom: float = 0.47
    upper_top: float = 0.94
    fascia_bottom: float = 0.60
    fascia_top: float = 0.87
    panorama_lens_offset: float = 0.29
    panorama_lens_height: float = 0.745
    panorama_lens_radius: float = 0.085
    tracking_center_height: float = 0.245
    tracking_width: float = 0.83
    tracking_depth: float = 0.91
    tracking_height: float = 0.49
    tracking_lens_radius: float = 0.145
    optical_relief: float = 0.012


PAN_TILT_CAMERA_GEOMETRY = PanTiltCameraGeometryConfig()


def _ellipsoid(center, size, color) -> Part:
    config = PAN_TILT_CAMERA_GEOMETRY
    segments, rings = config.segments, config.latitude_rings
    radii = tuple(value / 2 for value in size)
    positions, normals, triangles = [], [], []
    # Individual poles avoid collapsed triangles and keep the export watertight.
    for latitude in range(1, rings):
        angle = math.pi * latitude / rings
        for segment in range(segments):
            azimuth = math.tau * segment / segments
            unit = (math.sin(angle) * math.cos(azimuth),
                    math.sin(angle) * math.sin(azimuth), math.cos(angle))
            positions.append(tuple(c + r * u for c, r, u in zip(center, radii, unit, strict=True)))
            normal = tuple(u / r for u, r in zip(unit, radii, strict=True))
            length = math.sqrt(sum(value * value for value in normal))
            normals.append(tuple(value / length for value in normal))
    for latitude in range(rings - 2):
        for segment in range(segments):
            a = latitude * segments + segment
            b = latitude * segments + (segment + 1) % segments
            triangles.extend(((a, a + segments, b), (b, a + segments, b + segments)))
    for sign in (1, -1):
        pole = len(positions)
        positions.append((center[0], center[1], center[2] + sign * radii[2]))
        normals.append((0, 0, sign))
        start = 0 if sign > 0 else (rings - 2) * segments
        for segment in range(segments):
            a, b = start + segment, start + (segment + 1) % segments
            triangles.append((pole, a, b) if sign > 0 else (pole, b, a))
    return {"center": center, "size": size, "color": color, "points": (), "shape": "mesh",
            "mesh": {"positions": tuple(positions), "normals": tuple(normals),
                     "triangles": tuple(triangles)}}


def _oval_housing(width, depth, bottom, top, color):
    part = round_cylinder((0, 0, (bottom + top) / 2), width / 2, top - bottom,
                          axis=2, color=color)
    ratio = depth / width
    mesh = part["mesh"]
    normals = []
    for x, y, z in mesh["normals"]:
        length = math.sqrt(x * x + (y / ratio) ** 2 + z * z)
        normals.append((x / length, y / ratio / length, z / length))
    return {**part, "size": (width, depth, top - bottom),
            "mesh": {**mesh, "positions": tuple((x, y * ratio, z) for x, y, z in mesh["positions"]),
                     "normals": tuple(normals)}}


def reolink_omvi_3i_ceiling(width, depth, height):
    config = PAN_TILT_CAMERA_GEOMETRY
    parts = [
        _oval_housing(width, depth * .96, height * config.upper_bottom,
                      height * config.upper_top, "plastic-white"),
        _oval_housing(width * .985, depth, height * config.fascia_bottom,
                      height * config.fascia_top, "screen"),
        _oval_housing(width * .53, depth * .60, height * config.upper_top,
                      height, "plastic-white"),
        _oval_housing(width * .68, depth * .76, height * .44,
                      height * .49, "metal-black"),
        _ellipsoid((0, 0, height * config.tracking_center_height),
                   (width * config.tracking_width, depth * config.tracking_depth,
                    height * config.tracking_height), "metal-black"),
    ]

    def optic(x, y, z, radius):
        # Opaque optical glass reads as a lens in both the viewer and exported models.
        for scale, offset, color in ((1, 0, "device-accent"), (.85, .5, "metal-black"),
                                     (.66, 1, "screen"), (.36, 1.5, "device-slot")):
            parts.append(round_cylinder((x, y - depth * config.optical_relief * offset, z),
                                        radius * scale, depth * config.optical_relief,
                                        axis=1, color=color))

    for sign in (-1, 1):
        x = sign * width * config.panorama_lens_offset
        # Put lenses on the curved fascia, ahead of its surface at both lens edges.
        face = -depth / 2 * math.sqrt(1 - (2 * abs(x) / (width * .985)) ** 2)
        optic(x, face - depth * .03, height * config.panorama_lens_height,
              min(width, height) * config.panorama_lens_radius)
    optic(0, -depth * .455, height * config.tracking_center_height,
          min(width, height) * config.tracking_lens_radius)
    for z, y in ((height * config.panorama_lens_height, -depth * .495),
                 (height * .105, -depth * .395)):
        for sign in (-1, 1):
            parts.append(round_cylinder((sign * width * .025, y, z),
                                        min(width, height) * .024, depth * .009,
                                        axis=1, color="plastic-white"))
    return (ellipse(0, 0, width / 2, depth / 2, fill="plastic-white"),), tuple(parts)
