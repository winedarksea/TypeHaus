"""WAC BL-23210-BK, arm extended straight into the room and head aimed down.

Published inches: 4 3/8 canopy, 1 1/8 canopy depth and head diameter, 5 head
length, 8 overall height, 9 7/8 projection in this pose. Small hardware and
arm dimensions are estimated from WAC's photos; this is not fabrication geometry.
Reference: https://waclighting.com/product/sprig/?download=specs3
"""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import (
    Part,
    box,
    circle,
    line,
    prism,
    rect,
)
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

CANOPY_DIAMETER = 4.375
CANOPY_DEPTH = 1.125
HEAD_DIAMETER = 1.125
HEAD_LENGTH = 5.0
OVERALL_HEIGHT = 8.0
OVERALL_PROJECTION = 9.875
ROUND_SEGMENTS = 32
ELBOW_SEGMENTS = 8
ARM_RADIUS = 0.125
ELBOW_RADIUS = 0.625
ARM_TOP = 6.875
FINISH = "metal-black"


def sprig_sconce(width: float, depth: float, height: float) -> Geometry:
    """Scale the product envelope; +y is the mounting wall, z=0 the canopy bottom."""
    scale_x, scale_y, scale_z = (width / CANOPY_DIAMETER,
                                 depth / OVERALL_PROJECTION, height / OVERALL_HEIGHT)

    def point(x: float, projection: float, z: float) -> tuple[float, float, float]:
        return x * scale_x, depth / 2 - projection * scale_y, z * scale_z

    def vertical_round(projection: float, radius: float, bottom: float, top: float,
                       color: str = FINISH) -> Part:
        ring = tuple(point(radius * math.cos(math.tau * i / ROUND_SEGMENTS),
                           projection + radius * math.sin(math.tau * i / ROUND_SEGMENTS),
                           0)[:2] for i in range(ROUND_SEGMENTS))
        return prism(ring, bottom * scale_z, top * scale_z, color)

    def wall_round(projection: float, z: float, radius: float, length: float,
                   color: str = FINISH) -> Part:
        # A mesh preserves circular front elevation even under the registry's anisotropic
        # size sweep; the production type uses the published proportions.
        positions = [point(radius * math.cos(math.tau * i / ROUND_SEGMENTS),
                           projection + side * length / 2,
                           z + radius * math.sin(math.tau * i / ROUND_SEGMENTS))
                     for side in (-1, 1) for i in range(ROUND_SEGMENTS)]
        triangles: list[tuple[int, int, int]] = []
        for i in range(ROUND_SEGMENTS):
            following = (i + 1) % ROUND_SEGMENTS
            triangles.extend(((i, following, i + ROUND_SEGMENTS),
                              (following, following + ROUND_SEGMENTS, i + ROUND_SEGMENTS)))
        for offset in (0, ROUND_SEGMENTS):
            triangles.extend((offset, offset + i + 1, offset + i) if offset == 0 else
                             (offset, offset + i, offset + i + 1)
                             for i in range(1, ROUND_SEGMENTS - 1))
        return mesh_part(positions, outward(positions, triangles), color)

    head_projection = OVERALL_PROJECTION - HEAD_DIAMETER / 2
    head_bottom = OVERALL_HEIGHT - HEAD_LENGTH
    parts = [wall_round(CANOPY_DEPTH / 2, CANOPY_DIAMETER / 2,
                        CANOPY_DIAMETER / 2, CANOPY_DEPTH),
             vertical_round(head_projection, HEAD_DIAMETER / 2,
                            head_bottom + .025, OVERALL_HEIGHT),
             vertical_round(head_projection, HEAD_DIAMETER * .38,
                            head_bottom, head_bottom + .025, "lamp"),
             wall_round(CANOPY_DEPTH + .035, 1.65, .27, .07, "screen"),
             wall_round(CANOPY_DEPTH + .08, 1.65, .20, .05),
             vertical_round(CANOPY_DEPTH / 2, .20, 4.25, 5.25)]
    # The USB socket is a dark inset on the bottom edge, rather than a front-face mark.
    _, socket_y, _ = point(0, CANOPY_DEPTH / 2, 0)
    parts.append(box(0, socket_y, 0, .035 * scale_z,
                     .50 * scale_x, .20 * scale_y, "screen"))

    # Sweep a round tube through the elbow so the arm reads as one bent rod.
    elbow_start = ARM_TOP - ELBOW_RADIUS
    path = [(CANOPY_DEPTH / 2, 5.0, 0.0)]
    path.extend((CANOPY_DEPTH / 2 + ELBOW_RADIUS * (1 - math.cos(angle)),
                 elbow_start + ELBOW_RADIUS * math.sin(angle), angle)
                for angle in (math.pi / 2 * i / ELBOW_SEGMENTS
                              for i in range(ELBOW_SEGMENTS + 1)))
    path.append((head_projection, ARM_TOP, math.pi / 2))
    positions = [point(ARM_RADIUS * math.cos(angle),
                       projection + ARM_RADIUS * math.sin(angle) * math.cos(tangent),
                       z - ARM_RADIUS * math.sin(angle) * math.sin(tangent))
                 for projection, z, tangent in path
                 for angle in (math.tau * i / ROUND_SEGMENTS for i in range(ROUND_SEGMENTS))]
    triangles: list[tuple[int, int, int]] = []
    for section in range(len(path) - 1):
        for i in range(ROUND_SEGMENTS):
            a = section * ROUND_SEGMENTS + i
            b = section * ROUND_SEGMENTS + (i + 1) % ROUND_SEGMENTS
            triangles.extend(((a, a + ROUND_SEGMENTS, b),
                              (b, a + ROUND_SEGMENTS, b + ROUND_SEGMENTS)))
    for offset in (0, (len(path) - 1) * ROUND_SEGMENTS):
        triangles.extend((offset, offset + i, offset + i + 1) if offset == 0 else
                         (offset, offset + i + 1, offset + i)
                         for i in range(1, ROUND_SEGMENTS - 1))
    parts.append(mesh_part(positions, outward(positions, triangles), FINISH))
    strokes = (rect(0, depth / 2 - CANOPY_DEPTH / 2 * scale_y,
                    width, CANOPY_DEPTH * scale_y, fill=FINISH),
               line(point(0, CANOPY_DEPTH / 2, 0)[:2],
                    point(0, head_projection, 0)[:2]),
               circle(0, depth / 2 - head_projection * scale_y,
                      min(HEAD_DIAMETER * scale_x, HEAD_DIAMETER * scale_y) / 2,
                      fill=FINISH))
    return strokes, tuple(parts)
