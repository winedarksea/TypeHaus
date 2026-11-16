"""Round downlight with an open white trim and a regressed emitting face.

Proportions are representative, bounded by the catalog envelope; mounting hardware and
manufacturer-specific gimbal poses are omitted. Local z=0 remains the ceiling datum.
"""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._frame import Part
from typehaus.model.placeable_symbols._round_hardware import round_cylinder

CAN_SEGMENTS = 48
APERTURE_RADIUS_SHARE = 0.80
LAMP_RADIUS_SHARE = 0.60
TRIM_THICKNESS_DIAMETER_SHARE = 0.025
TRIM_BEVEL_RADIUS_SHARE = 0.025
REGRESSION_DIAMETER_SHARE = 0.18
LENS_THICKNESS_DIAMETER_SHARE = 0.015
BAFFLE_WALL_RADIUS_SHARE = 0.025
BAFFLE_STEP_COUNT = 5
BAFFLE_STEP_RADIUS_SHARE = 0.012
WHITE_TRIM_COLOR = "appliance-white"


def _turned_shell(profile: tuple[tuple[float, float], ...], color: str) -> Part:
    """Revolve a clockwise closed (radius, z) section, with crisp profile edges.

    Each profile edge has its own vertices: radial shading stays smooth while the trim's
    bevels and baffle steps keep their hard edges. No face spans the central aperture.
    """
    positions, normals, triangles = [], [], []
    for (radius0, z0), (radius1, z1) in zip(profile, (*profile[1:], profile[0]), strict=True):
        radial_delta, vertical_delta = radius1 - radius0, z1 - z0
        length = math.hypot(radial_delta, vertical_delta)
        base = len(positions)
        for radius, z in ((radius0, z0), (radius1, z1)):
            for segment in range(CAN_SEGMENTS):
                angle = math.tau * segment / CAN_SEGMENTS
                cosine, sine = math.cos(angle), math.sin(angle)
                positions.append((radius * cosine, radius * sine, z))
                normals.append((-vertical_delta * cosine / length,
                                -vertical_delta * sine / length, radial_delta / length))
        for segment in range(CAN_SEGMENTS):
            following = (segment + 1) % CAN_SEGMENTS
            a, b = base + segment, base + following
            c, d = a + CAN_SEGMENTS, b + CAN_SEGMENTS
            triangles.extend(((a, c, b), (b, c, d)))
    radius = max(r for r, _ in profile)
    bottom, top = min(z for _, z in profile), max(z for _, z in profile)
    return {"center": (0.0, 0.0, (bottom + top) / 2),
            "size": (2 * radius, 2 * radius, top - bottom),
            "color": color, "points": (), "shape": "mesh",
            "mesh": {"positions": tuple(positions), "normals": tuple(normals),
                     "triangles": tuple(triangles)}}


def recessed_can_parts(width: float, depth: float, height: float) -> tuple[Part, ...]:
    radius = min(width, depth) / 2
    diameter = 2 * radius
    aperture = radius * APERTURE_RADIUS_SHARE
    lamp_radius = radius * LAMP_RADIUS_SHARE
    trim_top = min(diameter * TRIM_THICKNESS_DIAMETER_SHARE, height * 0.06)
    bevel = min(radius * TRIM_BEVEL_RADIUS_SHARE, trim_top / 2)
    lens_bottom = min(diameter * REGRESSION_DIAMETER_SHARE, height * 0.35)
    lens_thickness = min(diameter * LENS_THICKNESS_DIAMETER_SHARE, height * 0.03)
    lens_top = lens_bottom + lens_thickness
    wall = radius * BAFFLE_WALL_RADIUS_SHARE
    trim = _turned_shell(((aperture, 0.0), (aperture, trim_top),
                          (radius, trim_top), (radius, bevel), (radius - bevel, 0.0)),
                         WHITE_TRIM_COLOR)
    # Small ledges interrupt the tapered reflector, suggesting a stepped anti-glare baffle.
    inner_profile = [(aperture, trim_top)]
    for step in range(1, BAFFLE_STEP_COUNT + 1):
        fraction = step / BAFFLE_STEP_COUNT
        r = aperture + (lamp_radius - aperture) * fraction
        z = trim_top + (lens_bottom - trim_top) * fraction
        inner_profile.extend(((r, z), (r - radius * BAFFLE_STEP_RADIUS_SHARE, z)))
    inner_profile.extend(((lamp_radius - radius * BAFFLE_STEP_RADIUS_SHARE, lens_top),
                          (aperture + wall, lens_top), (aperture + wall, trim_top)))
    baffle = _turned_shell(tuple(inner_profile), WHITE_TRIM_COLOR)
    lens = round_cylinder((0.0, 0.0, (lens_bottom + lens_top) / 2), lamp_radius,
                          lens_thickness, axis=2, color="lamp")
    housing = round_cylinder((0.0, 0.0, (lens_top + height) / 2), aperture + wall,
                             height - lens_top, axis=2, color="luminaire-housing")
    return trim, baffle, lens, housing
