"""A single-element radiant bar aimed 45 degrees down, with wall swivel brackets.

DR-238 dimensional basis: 34.6in length, 7.69in face, 3.33in case thickness. The
34.6x14x8in installed envelope allows 6in behind the tilted body. Bracket mounting
holes follow the manufacturer's 10.8in inner spacing and 1.1in hole pairs.
"""

import math

from typehaus.model.placeable_symbols._frame import box, line, rect
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

ENVELOPE_IN = (34.6, 14.0, 8.0)
FACE_WIDTH_IN = 7.69
CASE_THICKNESS_IN = 3.33
REAR_CLEARANCE_IN = 6.0
TILT_DEGREES = 45.0
BRACKET_STATIONS_IN = (-5.95, 5.95)
GUARD_STATIONS_IN = (-12.0, -6.0, 0.0, 6.0, 12.0)
SHEET_THICKNESS_IN = 0.08
RIM_WIDTH_IN = 0.4


def infrared_heater(width, depth, height):
    """Shared plan and 3D geometry, scaled from the installed reference envelope."""
    sine = math.sin(math.radians(TILT_DEGREES))
    cosine = math.cos(math.radians(TILT_DEGREES))
    projected_depth = FACE_WIDTH_IN * sine + CASE_THICKNESS_IN * cosine
    body_y = ENVELOPE_IN[1] / 2 - REAR_CLEARANCE_IN - projected_depth / 2
    scale = (width / ENVELOPE_IN[0], depth / ENVELOPE_IN[1], height / ENVELOPE_IN[2])

    def tilted_box(x, transverse, thickness, span, face_span, case_depth, color):
        corners = []
        for dx, across, normal in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                                  (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
            face = transverse + across * face_span / 2
            case = thickness + normal * case_depth / 2
            corners.append(((x + dx * span / 2) * scale[0],
                            (body_y - face * sine + case * cosine) * scale[1],
                            (ENVELOPE_IN[2] / 2 + face * cosine + case * sine) * scale[2]))
        triangles = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                     (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                     (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
        return mesh_part(corners, outward(corners, triangles), color)

    parts = [tilted_box(0, 0, CASE_THICKNESS_IN / 2 - SHEET_THICKNESS_IN / 2,
                        ENVELOPE_IN[0], FACE_WIDTH_IN, SHEET_THICKNESS_IN, "metal-black")]
    # Open reflector tray: the tube and guard sit in front of its recessed back.
    parts.append(tilted_box(0, 0, 0.8, 32.2, 7.3, SHEET_THICKNESS_IN, "metal"))
    for transverse in (-FACE_WIDTH_IN / 2 + RIM_WIDTH_IN / 2,
                       FACE_WIDTH_IN / 2 - RIM_WIDTH_IN / 2):
        parts.append(tilted_box(0, transverse, 0, ENVELOPE_IN[0], RIM_WIDTH_IN,
                                CASE_THICKNESS_IN, "metal-black"))
    for x in (-ENVELOPE_IN[0] / 2 + RIM_WIDTH_IN / 2,
              ENVELOPE_IN[0] / 2 - RIM_WIDTH_IN / 2):
        parts.append(tilted_box(x, 0, 0, RIM_WIDTH_IN, FACE_WIDTH_IN,
                                CASE_THICKNESS_IN, "metal-black"))
    parts.append(tilted_box(15.8, 0, -1.6, 1.6, 2.0, 0.08, "metal-black"))
    parts.append(tilted_box(15.8, 0.3, -1.65, 0.8, 0.45, 0.03, "screen"))
    parts.append(tilted_box(0, 0, -0.6, 30, 0.3, 0.3, "brass"))
    for transverse in (-2.5, 2.5):
        parts.append(tilted_box(0, transverse, -1.4, 31.8, 0.07, 0.07, "metal-black"))
    for x in GUARD_STATIONS_IN:
        parts.append(tilted_box(x, 0, -1.4, 0.07, 7.3, 0.07, "metal-black"))

    strokes = [rect(0, body_y * scale[1], width, projected_depth * scale[1]),
               line((-15 * scale[0], (body_y - 0.6 * cosine) * scale[1]),
                    (15 * scale[0], (body_y - 0.6 * cosine) * scale[1]))]
    for station in BRACKET_STATIONS_IN:
        # Wall plates reach the footprint's back plane; arms meet the tilted case.
        parts.append(box(station * scale[0], (7 - 0.06) * scale[1],
                         2.5 * scale[2], 5.5 * scale[2],
                         1.5 * scale[0], 0.12 * scale[1], "metal"))
        arm_end = body_y + CASE_THICKNESS_IN * cosine
        parts.append(box(station * scale[0], (arm_end + 7) / 2 * scale[1],
                         3.8 * scale[2], 4.2 * scale[2],
                         0.5 * scale[0], (7 - arm_end) * scale[1], "metal"))
        strokes.append(rect(station * scale[0], (arm_end + 7) / 2 * scale[1],
                            0.5 * scale[0], (7 - arm_end) * scale[1]))
    return tuple(strokes), tuple(parts)
