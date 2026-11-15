"""FXU24 horizontal-left coordination geometry, from Gree's 2026-01-27 submittal.

Local -x is discharge, +x return, -y the removable service panels. Catlin's
rotation 0 places these west, east and south. Only the cabinet and
supply opening sizes are dimensioned; fitting stations are schematic, not templates.
"""

import math

from typehaus.model.placeable_symbols._frame import box, line, rect
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

CABINET_IN = (43.5, 21.25, 18.125)
SUPPLY_OPENING_IN = (11.625, 16.75)  # local y span, z span
# The drawing places the opening at the rear; the setback is not dimensioned.
SUPPLY_CENTER_IN = (-21.75, 4.8125, 9.0625)
RETURN_CENTER_IN = (21.75, 0.0, 9.0625)
SERVICE_CLEARANCE_IN = 24.0
SHEET_IN = 0.05  # visualization thickness, not a cabinet construction specification
CONNECTION_MARKER_SIDES = 16
# tag: (x, z, nominal connection inches); stations read schematically from the views.
FRONT_CONNECTIONS_IN = {
    "liquid": (5.0, 3.0, 0.375),
    "vapor": (10.0, 3.0, 0.75),
    "condensate_primary": (16.0, 1.0, 0.75),
    "condensate_secondary": (19.0, 1.5, 0.75),
}
POWER_CENTER_IN = (-15.0, -10.625, 9.0625)
CONTROL_CENTER_IN = (-12.0, -10.625, 9.0625)


def _round_connection_marker(x, y, z, radius, thickness):
    # Explicit triangles keep round port markers identical in the viewer, GLB and IFC.
    count = CONNECTION_MARKER_SIDES
    vertices = [(x + radius * math.cos(2 * math.pi * index / count), face,
                 z + radius * math.sin(2 * math.pi * index / count))
                for face in (y, y + thickness) for index in range(count)]
    triangles = []
    for index in range(count):
        following = (index + 1) % count
        triangles.extend(((index, following, following + count),
                          (index, following + count, index + count)))
    for index in range(1, count - 1):
        triangles.extend(((0, index + 1, index), (count, count + index, count + index + 1)))
    return mesh_part(vertices, outward(vertices, triangles), "brass")


def gree_flexx_horizontal(width, depth, height):
    """An open shell: no solid end cap masquerading as an air connection."""
    sx, sy, sz = (value / reference for value, reference in
                  zip((width, depth, height), CABINET_IN, strict=True))

    def panel(x, y, z0, z1, span_x, span_y, role, color="metal"):
        part = box(x * sx, y * sy, z0 * sz, z1 * sz, span_x * sx, span_y * sy, color)
        part["role"] = role
        return part

    length, case_depth, case_height = CABINET_IN
    sheet = SHEET_IN
    parts = [panel(0, 0, z, z + sheet, length, case_depth, "flexx:case")
             for z in (0, case_height - sheet)]
    parts.append(panel(0, case_depth / 2 - sheet / 2, sheet, case_height - sheet,
                       length, sheet, "flexx:case"))
    # Split service panels make the front and the coil/blower division legible.
    for start, end in ((-length / 2, 0), (sheet, length / 2)):
        parts.append(panel((start + end) / 2, -case_depth / 2 + sheet / 2,
                           sheet, case_height - sheet, end - start, sheet,
                           "flexx:service-panel"))
    opening_depth, opening_height = SUPPLY_OPENING_IN
    cx, cy, cz = SUPPLY_CENTER_IN
    low_y, high_y = cy - opening_depth / 2, cy + opening_depth / 2
    low_z, high_z = cz - opening_height / 2, cz + opening_height / 2
    for z0, z1 in ((0, low_z), (high_z, case_height)):
        parts.append(panel(cx + sheet / 2, 0, z0, z1, sheet, case_depth,
                           "flexx:supply-frame"))
    parts.append(panel(cx + sheet / 2, (-case_depth / 2 + low_y) / 2,
                       low_z, high_z, sheet, low_y + case_depth / 2,
                       "flexx:supply-frame"))
    # Return is intentionally open-ended: Gree does not dimension its clear aperture.
    # The shell's sheet edges are illustrative, not a claimed return neck size.
    for tag, (x, z, diameter) in FRONT_CONNECTIONS_IN.items():
        part = _round_connection_marker(x * sx, -case_depth / 2 * sy, z * sz,
                                        diameter / 2 * min(sx, sz), sheet * sy)
        part["role"] = "flexx:" + tag
        parts.append(part)
    for tag, station in (("power", POWER_CENTER_IN), ("control", CONTROL_CENTER_IN)):
        parts.append(panel(station[0], station[1] + sheet / 2,
                           station[2] - 0.5, station[2] + 0.5,
                           1.0, sheet, "flexx:" + tag, "metal-black"))
    strokes = (rect(0, 0, width, depth),
               line((cx * sx, low_y * sy), (cx * sx, high_y * sy)),
               line((0, -depth / 2), (0, depth / 2)))
    return strokes, tuple(parts)
