"""RenewAire FA8-P (102409): folded rain hood with a downward screened mouth.

Shape reference: renewaire.com/wp-content/uploads/2025/09/Hoods-Dampers-.pdf.
Only the 8in connection and 1/4in mesh are published. Plate, projection and sheet
thickness below are visual estimates inside Catlin's retained 12in clearance box.
The mounting plate is at local +y; the existing duct supplies the through-wall neck.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Part, box, rect
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

ENVELOPE_IN = 12.0
HOOD_WIDTH_IN = 10.5
PROJECTION_IN = 7.5
PLATE_OPENING_IN = 9.0
SHEET_THICKNESS_IN = 0.04
MOUTH_HEIGHT_IN = 0.75
HOOD_TOP_IN = 11.25
SCREEN_PITCH_IN = 0.25
SCREEN_WIRE_IN = 0.025
# Match the north facade's board-batten-24 display colour without applying its rib texture.
FINISH = "vent-hood-painted"


def erv_wall_hood(width: float, depth: float, height: float) -> Geometry:
    """An open shell, rather than a solid wedge or an indoor ventilator cabinet."""
    scale_x, scale_y, scale_z = (value / ENVELOPE_IN for value in (width, depth, height))

    def panel_box(x, projection, bottom, top, panel_width, panel_depth, role,
                  color=FINISH) -> Part:
        part = box(x * scale_x, depth / 2 - projection * scale_y,
                   bottom * scale_z, top * scale_z,
                   panel_width * scale_x, panel_depth * scale_y, color)
        part["role"] = role
        return part

    def side_profile(left, right, profile, role) -> Part:
        positions = [(x * scale_x, depth / 2 - projection * scale_y, z * scale_z)
                     for x in (left, right) for projection, z in profile]
        count = len(profile)
        triangles = [(0, i + 1, i) for i in range(1, count - 1)]
        triangles += [(count, count + i, count + i + 1) for i in range(1, count - 1)]
        for i in range(count):
            following = (i + 1) % count
            triangles += [(i, following, count + following),
                          (i, count + following, count + i)]
        part = mesh_part(positions, outward(positions, triangles), FINISH)
        part["role"] = role
        return part

    thickness = SHEET_THICKNESS_IN
    half_width = HOOD_WIDTH_IN / 2
    flange = (ENVELOPE_IN - PLATE_OPENING_IN) / 2
    # Four flange strips leave the rough opening and the duct axis unobstructed.
    parts = [panel_box(0, thickness / 2, bottom, top, ENVELOPE_IN, thickness,
                       "hood:mounting-flange")
             for bottom, top in ((0, flange), (ENVELOPE_IN - flange, ENVELOPE_IN))]
    parts += [panel_box(sign * (ENVELOPE_IN - flange) / 2, thickness / 2,
                        flange, ENVELOPE_IN - flange, flange, thickness,
                        "hood:mounting-flange") for sign in (-1, 1)]
    side = ((thickness, MOUTH_HEIGHT_IN), (PROJECTION_IN, MOUTH_HEIGHT_IN),
            (thickness, HOOD_TOP_IN))
    parts += [side_profile(left, right, side, "hood:side") for left, right in
              ((-half_width, -half_width + thickness), (half_width - thickness, half_width))]
    slope = ((thickness, HOOD_TOP_IN), (PROJECTION_IN, MOUTH_HEIGHT_IN),
             (PROJECTION_IN, MOUTH_HEIGHT_IN + thickness),
             (thickness, HOOD_TOP_IN + thickness))
    parts.append(side_profile(-half_width, half_width, slope, "hood:rain-cover"))
    # Open quarter-inch mesh remains visible from below; there is no damper blade.
    for index in range(1, round(HOOD_WIDTH_IN / SCREEN_PITCH_IN)):
        parts.append(panel_box(-half_width + index * SCREEN_PITCH_IN, PROJECTION_IN / 2,
                                MOUTH_HEIGHT_IN, MOUTH_HEIGHT_IN + SCREEN_WIRE_IN,
                                SCREEN_WIRE_IN, PROJECTION_IN - thickness,
                                "hood:screen", "metal"))
    for index in range(1, round(PROJECTION_IN / SCREEN_PITCH_IN)):
        parts.append(panel_box(0, index * SCREEN_PITCH_IN,
                                MOUTH_HEIGHT_IN, MOUTH_HEIGHT_IN + SCREEN_WIRE_IN,
                                HOOD_WIDTH_IN - 2 * thickness, SCREEN_WIRE_IN,
                                "hood:screen", "metal"))
    strokes = (rect(0, depth / 2 - thickness * scale_y / 2,
                    width, thickness * scale_y, fill=FINISH),
               rect(0, depth / 2 - PROJECTION_IN * scale_y / 2,
                    HOOD_WIDTH_IN * scale_x, PROJECTION_IN * scale_y, fill=FINISH))
    return strokes, tuple(parts)
