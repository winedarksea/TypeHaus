"""P9703WBG installed on a west-facing Badger elbow, in disposer-local inches.

LCS1353 envelope: 3 1/2-inch connection spacing and 4 5/8-inch inlet-top to
outside bottom. Curves and slip nuts are representative, pending physical dry-fit.
"""

import math

from typehaus.model.placeable_symbols._mesh import mesh_part, outward
from typehaus.model.placeable_symbols._round_hardware import round_cylinder

INLET_X_IN = -5.0
INLET_TOP_IN = 3.0
CONNECTION_SPACING_IN = 3.5
INLET_TO_BOTTOM_IN = 4.625
# Installed Catlin set-out: pipes use storey Z; the disposer uses finished-floor Z.
# RM-M-LIVING's resolved floor buildup is 26.05 mm, superseding the old 15/16 inch.
FLOOR_BUILDUP_MM = 26.05
DISPOSER_BASE_AFF_IN = 13.319
ARM_START_STOREY_IN = 17.104166667
OUTLET_HEIGHT_IN = ARM_START_STOREY_IN - FLOOR_BUILDUP_MM / 25.4 - DISPOSER_BASE_AFF_IN
TUBE_RADIUS_IN = 0.75
RETURN_RADIUS_IN = 1.3125
OUTLET_BEND_RADIUS_IN = CONNECTION_SPACING_IN - 2 * RETURN_RADIUS_IN
BEND_SEGMENTS = 16
RADIAL_SEGMENTS = 24
NUT_RADIUS_IN = 1.0
NUT_LENGTH_IN = 0.5


def dearborn_trap_parts():
    """Closed exterior solids; inlet overlaps the supplied discharge tailpiece."""
    return_center_z = (INLET_TOP_IN - INLET_TO_BOTTOM_IN
                       + TUBE_RADIUS_IN + RETURN_RADIUS_IN)
    # Each station stores y, z and the tangent angle measured from downward.
    stations = [(0, INLET_TOP_IN, 0)]
    for step in range(BEND_SEGMENTS + 1):
        angle = math.pi * step / BEND_SEGMENTS
        stations.append((RETURN_RADIUS_IN * (1 - math.cos(angle)),
                         return_center_z - RETURN_RADIUS_IN * math.sin(angle), angle))
    for step in range(BEND_SEGMENTS + 1):
        angle = math.pi / 2 * step / BEND_SEGMENTS
        stations.append((CONNECTION_SPACING_IN - OUTLET_BEND_RADIUS_IN * math.cos(angle),
                         OUTLET_HEIGHT_IN - OUTLET_BEND_RADIUS_IN
                         + OUTLET_BEND_RADIUS_IN * math.sin(angle), math.pi - angle))
    positions, triangles = [], []
    for y, z, tangent in stations:
        for segment in range(RADIAL_SEGMENTS):
            angle = math.tau * segment / RADIAL_SEGMENTS
            positions.append((INLET_X_IN + TUBE_RADIUS_IN * math.cos(angle),
                              y + TUBE_RADIUS_IN * math.cos(tangent) * math.sin(angle),
                              z + TUBE_RADIUS_IN * math.sin(tangent) * math.sin(angle)))
    for course in range(len(stations) - 1):
        for segment in range(RADIAL_SEGMENTS):
            a = course * RADIAL_SEGMENTS + segment
            b = course * RADIAL_SEGMENTS + (segment + 1) % RADIAL_SEGMENTS
            triangles.extend(((a, b, a + RADIAL_SEGMENTS),
                              (b, b + RADIAL_SEGMENTS, a + RADIAL_SEGMENTS)))
    for course, reverse in ((0, True), (len(stations) - 1, False)):
        center = len(positions)
        positions.append((INLET_X_IN, *stations[course][:2]))
        for segment in range(RADIAL_SEGMENTS):
            a = course * RADIAL_SEGMENTS + segment
            b = course * RADIAL_SEGMENTS + (segment + 1) % RADIAL_SEGMENTS
            triangles.append((center, b, a) if reverse else (center, a, b))
    parts = [mesh_part(positions, outward(positions, triangles), "appliance-white")]
    for center, axis in (((INLET_X_IN, 0, INLET_TOP_IN - NUT_LENGTH_IN / 2), 2),
                         ((INLET_X_IN, 2 * RETURN_RADIUS_IN,
                           OUTLET_HEIGHT_IN - OUTLET_BEND_RADIUS_IN), 2),
                         ((INLET_X_IN, CONNECTION_SPACING_IN, OUTLET_HEIGHT_IN), 1)):
        parts.append(round_cylinder(center, NUT_RADIUS_IN, NUT_LENGTH_IN,
                                    axis=axis, color="appliance-white"))
    return tuple({**part, "role": "trap:dearborn-p9703wbg"} for part in parts)
