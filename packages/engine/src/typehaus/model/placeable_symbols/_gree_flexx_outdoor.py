"""FXU24HP230V1R32AO, GREE_FXU24_230V_R32_SUB_01272026 p.4.

Cabinet A/F/C, overall foot depth B and fixing pitch D/E are published.
Fan, panel, foot-width and connection stations below are illustrative readings
of the views, not dimensioned fabrication data. Front discharge is local -y;
the valve/electrical compartment is +x (west at Catlin's 180 degree placement).
"""

import math

from typehaus.model.placeable_symbols._frame import box, line, rect
from typehaus.model.placeable_symbols._mesh import mesh_part, outward
from typehaus.model.placeable_symbols._round_hardware import round_cylinder

OUTDOOR_CABINET_IN = (39.0, 14.5625, 37.8125)
OUTDOOR_FOOT_DEPTH_IN = 16.8125
OUTDOOR_FIXING_PITCH_IN = (29.75, 15.5625)
OUTDOOR_FIXING_CENTERS_IN = tuple(
    (sign_x * OUTDOOR_FIXING_PITCH_IN[0] / 2, sign_y * OUTDOOR_FIXING_PITCH_IN[1] / 2)
    for sign_x in (-1, 1) for sign_y in (-1, 1))
# Only nominal refrigerant tube sizes are verified; the outlet axes/stations are schematic.
OUTDOOR_CONNECTIONS_IN = {
    "liquid": ((19.5, -2.0, 7.0), 0.375),
    "vapor": ((19.5, -2.0, 11.0), 0.75),
}
OUTDOOR_POWER_CENTER_IN = (19.5, 0.0, 25.0)
OUTDOOR_CONTROL_CENTER_IN = (19.5, 2.0, 25.0)
OUTDOOR_BASELINE_CLEARANCE_IN = {"service": 12.0, "rear": 4.0, "left": 4.0, "front": 40.0}
FOOT_WIDTH_IN = 2.0
FOOT_THICKNESS_IN = 0.5
FIXING_MARKER_RADIUS_IN = 0.22  # visual marker, not a claimed hole/slot dimension
VISUAL_SHEET_IN = 0.05
FRONT_RECESS_IN = 0.25
FAN_CENTER_IN = (-5.25, 20.5)
FAN_RADIUS_IN = 14.0
FAN_GUARD_RING_RADII_IN = (3.0, 6.0, 9.0, 12.0, 14.0)
FAN_GUARD_WIRE_IN = 0.08
ROUND_SEGMENTS = 32


def _ring(center, outer_radius, inner_radius, thickness, *, axis=1, color="metal"):
    """Closed annulus, or disk when inner_radius is zero, in the chosen axis."""
    if not inner_radius:
        return round_cylinder(center, outer_radius, thickness, axis=axis, color=color)
    across = [index for index in range(3) if index != axis]
    vertices = []
    radii = (outer_radius, inner_radius)
    for normal in (-thickness / 2, thickness / 2):
        for radius in radii:
            for index in range(ROUND_SEGMENTS):
                point = list(center)
                point[axis] += normal
                angle = 2 * math.pi * index / ROUND_SEGMENTS
                point[across[0]] += radius * math.cos(angle)
                point[across[1]] += radius * math.sin(angle)
                vertices.append(tuple(point))
    triangles = []
    count = ROUND_SEGMENTS
    stride = len(radii) * count
    for index in range(count):
        following = (index + 1) % count
        triangles.extend(((index, following, stride + following),
                          (index, stride + following, stride + index)))
        for offset in (0, stride):
            face = ((offset + index, offset + following, offset + count + index),
                    (offset + following, offset + count + following,
                     offset + count + index))
            triangles.extend(tuple(reversed(triangle)) if offset == 0 else triangle
                             for triangle in face)
        triangles.extend(((count + index, stride + count + index, count + following),
                          (count + following, stride + count + index,
                           stride + count + following)))
    return mesh_part(vertices, outward(vertices, triangles), color)


def gree_flexx_outdoor(width, depth, height):
    """Side-discharge condenser with feet at the stand's published fixing stations."""
    sx, sy, sz = (value / reference for value, reference in
                  zip((width, depth, height), OUTDOOR_CABINET_IN, strict=True))

    def panel(x, y, z0, z1, span_x, span_y, role, color="appliance-steel"):
        part = box(x * sx, y * sy, z0 * sz, z1 * sz, span_x * sx, span_y * sy, color)
        part["role"] = role
        return part

    def round_part(center, radius, inner, thickness, role, axis=1, color="metal"):
        # Build in drawing inches then scale the mesh, retaining nonuniform dimensions.
        part = _ring(center, radius, inner, thickness, axis=axis, color=color)
        vertices = [(x * sx, y * sy, z * sz) for x, y, z in part["mesh"]["positions"]]
        part = mesh_part(vertices, list(part["mesh"]["triangles"]), color)
        part["role"] = role
        return part

    case_width, case_depth, case_height = OUTDOOR_CABINET_IN
    # Recess the front skin so the fan and service panel are visible in every renderer,
    # rather than buried inside a solid cabinet box or coplanar with its front face.
    parts = [panel(-VISUAL_SHEET_IN / 2, (FRONT_RECESS_IN - VISUAL_SHEET_IN) / 2,
                   FOOT_THICKNESS_IN, case_height,
                   case_width - VISUAL_SHEET_IN,
                   case_depth - FRONT_RECESS_IN - VISUAL_SHEET_IN, "flexx-od:cabinet")]
    for sign in (-1, 1):
        parts.append(panel(sign * (case_width - FRONT_RECESS_IN) / 2,
                           (-case_depth + FRONT_RECESS_IN) / 2,
                           FOOT_THICKNESS_IN, case_height, FRONT_RECESS_IN, FRONT_RECESS_IN,
                           "flexx-od:cabinet-lip"))
    for x in (-OUTDOOR_FIXING_PITCH_IN[0] / 2, OUTDOOR_FIXING_PITCH_IN[0] / 2):
        parts.append(panel(x, 0, 0, FOOT_THICKNESS_IN, FOOT_WIDTH_IN, OUTDOOR_FOOT_DEPTH_IN,
                           "flexx-od:foot", "metal"))
    for x, y in OUTDOOR_FIXING_CENTERS_IN:
        parts.append(round_part((x, y, FOOT_THICKNESS_IN - VISUAL_SHEET_IN / 2),
                                FIXING_MARKER_RADIUS_IN, 0, VISUAL_SHEET_IN,
                                "flexx-od:fixing-marker", axis=2, color="metal-black"))
    fan_x, fan_z = FAN_CENTER_IN
    front = -case_depth / 2
    parts.append(round_part((fan_x, front + 0.1, fan_z), FAN_RADIUS_IN, 0, 0.1,
                            "flexx-od:fan-recess", color="metal-black"))
    for radius in FAN_GUARD_RING_RADII_IN:
        parts.append(round_part((fan_x, front + VISUAL_SHEET_IN / 2, fan_z),
                                radius, radius - FAN_GUARD_WIRE_IN, VISUAL_SHEET_IN,
                                "flexx-od:fan-guard"))
    parts.append(round_part((fan_x, front + VISUAL_SHEET_IN / 2, fan_z),
                            2.0, 0, VISUAL_SHEET_IN, "flexx-od:fan-hub"))
    parts.append(panel(13, front + VISUAL_SHEET_IN / 2, 2, case_height - 2,
                       9, VISUAL_SHEET_IN, "flexx-od:service-panel", "metal"))
    # Back coil occupies the surface rather than sitting hidden inside the casing.
    parts.append(panel(0, case_depth / 2 - VISUAL_SHEET_IN / 2, 2, case_height - 2,
                       case_width - 2, VISUAL_SHEET_IN, "flexx-od:rear-coil", "metal-black"))
    for z0, z1 in ((FOOT_THICKNESS_IN, 2), (case_height - 2, case_height)):
        parts.append(panel(0, case_depth / 2 - VISUAL_SHEET_IN / 2, z0, z1,
                           case_width, VISUAL_SHEET_IN, "flexx-od:cabinet-lip"))
    for sign in (-1, 1):
        parts.append(panel(sign * (case_width - 1) / 2,
                           case_depth / 2 - VISUAL_SHEET_IN / 2, 2, case_height - 2,
                           1, VISUAL_SHEET_IN, "flexx-od:cabinet-lip"))
    for tag, (station, diameter) in OUTDOOR_CONNECTIONS_IN.items():
        x, y, z = station
        parts.append(round_part((x - VISUAL_SHEET_IN / 2, y, z), diameter / 2, 0,
                                VISUAL_SHEET_IN, "flexx-od:" + tag, axis=0, color="brass"))
    for tag, station in (("power", OUTDOOR_POWER_CENTER_IN),
                         ("control", OUTDOOR_CONTROL_CENTER_IN)):
        x, y, z = station
        parts.append(panel(x - VISUAL_SHEET_IN / 2, y, z - 0.5, z + 0.5,
                           VISUAL_SHEET_IN, 1, "flexx-od:" + tag, "metal-black"))
    # Plan marks the discharge face; there is no top-discharge fan on this product.
    strokes = (rect(0, 0, width, depth),
               line(((-5.25 - FAN_RADIUS_IN) * sx, front * sy),
                    ((-5.25 + FAN_RADIUS_IN) * sx, front * sy)))
    return strokes, tuple(parts)
