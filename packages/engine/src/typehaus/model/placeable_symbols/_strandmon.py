"""STRANDMON Nordvalla: rounded upholstery, swept wings and five back buttons.

Coordinates below are proportions of the catalog envelope. The silhouette is illustrative;
only the envelope and seat dimensions are published by IKEA. +y faces the chair's back.
"""
from __future__ import annotations

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Part, rect
from typehaus.model.placeable_symbols._mesh import mesh_part

UPHOLSTERY = "nordvalla-gray"
BUTTON = "nordvalla-gray-seam"
LEG = "strandmon-leg"
RING_SEGMENTS = 40
ROUND_RECT_EXPONENT = .42
# Each horizontal section: z, x centre, y centre, half width, half depth.
Section = tuple[float, float, float, float, float]


def _upholstered_loft(sections: tuple[Section, ...], width: float, depth: float,
                      height: float, color: str = UPHOLSTERY) -> Part:
    vertices = []
    for z, cx, cy, rx, ry in sections:
        for index in range(RING_SEGMENTS):
            angle = math.tau * index / RING_SEGMENTS
            cosine, sine = math.cos(angle), math.sin(angle)
            x = cx + rx * math.copysign(abs(cosine) ** ROUND_RECT_EXPONENT, cosine)
            y = cy + ry * math.copysign(abs(sine) ** ROUND_RECT_EXPONENT, sine)
            vertices.append((x * width, y * depth, z * height))
    triangles = []
    for ring in range(len(sections) - 1):
        for index in range(RING_SEGMENTS):
            a = ring * RING_SEGMENTS + index
            b = ring * RING_SEGMENTS + (index + 1) % RING_SEGMENTS
            triangles.extend(((a, b, b + RING_SEGMENTS),
                              (a, b + RING_SEGMENTS, a + RING_SEGMENTS)))
    for ring, reverse in ((0, True), (len(sections) - 1, False)):
        z, cx, cy, _, _ = sections[ring]
        center = len(vertices)
        vertices.append((cx * width, cy * depth, z * height))
        for index in range(RING_SEGMENTS):
            a = ring * RING_SEGMENTS + index
            b = ring * RING_SEGMENTS + (index + 1) % RING_SEGMENTS
            triangles.append((center, b, a) if reverse else (center, a, b))
    part = mesh_part(vertices, triangles, color)
    # Upholstery should read as a continuous padded surface across the loft rings.
    accumulated_normals = [[0., 0., 0.] for _ in vertices]
    flat_normals = part["mesh"]["normals"]
    for triangle_index, triangle in enumerate(triangles):
        for vertex_index in triangle:
            for axis in range(3):
                accumulated_normals[vertex_index][axis] += flat_normals[triangle_index * 3][axis]
    normals = []
    for normal in accumulated_normals:
        magnitude = math.sqrt(sum(value * value for value in normal))
        normals.append(tuple(value / magnitude for value in normal))
    part["mesh"] = {"positions": tuple(vertices), "triangles": tuple(triangles),
                    "normals": tuple(normals)}
    return part


def strandmon(width: float, depth: float, height: float) -> Geometry:
    """Dedicated wing chair; the generic armchair remains available for other products."""
    def loft(sections: tuple[Section, ...], color: str = UPHOLSTERY) -> Part:
        return _upholstered_loft(sections, width, depth, height, color)

    parts = [
        loft(((.15, 0, -.04, .34, .35), (.18, 0, -.04, .38, .39),
              (.32, 0, -.04, .39, .40), (.35, 0, -.04, .36, .37))),
        # A discrete cushion with a softly crowned top, 19 1/4 by 21 1/4 inches.
        loft(((.35, 0, -.15, .29, .265), (.365, 0, -.15, .305, .282),
              (.425, 0, -.15, .305, .282), (.4465, 0, -.15, .28, .26))),
        # Reclined back widens toward the shoulders and rounds into the top rail.
        loft(((.31, 0, .20, .29, .085), (.44, 0, .22, .32, .095),
              (.64, 0, .28, .36, .10), (.88, 0, .37, .385, .105),
              (.97, 0, .39, .37, .10), (1., 0, .39, .335, .075))),
    ]
    for side in (-1, 1):
        # Arm fronts flare outward at the roll, with a narrow waist below the wings.
        parts.append(loft(((.17, side * .37, -.025, .065, .35),
                           (.37, side * .40, -.035, .075, .375),
                           (.55, side * .415, -.045, .08, .385),
                           (.60, side * .415, -.06, .085, .37),
                           (.625, side * .41, -.06, .065, .34))))
        parts.append(loft(((.53, side * .355, .20, .045, .13),
                           (.65, side * .385, .23, .055, .15),
                           (.83, side * .425, .255, .075, .20),
                           (.96, side * .425, .28, .075, .19),
                           (1., side * .415, .30, .055, .15))))
        for y in (-.34, .32):
            parts.append(loft(((0., side * .34, y, .018, .018),
                               (.18, side * .33, y, .033, .033)), LEG))
    # One row of five fabric-covered buttons, just proud of the reclined back face.
    for x in (-.24, -.12, 0., .12, .24):
        parts.append(loft(((.648, x, .178, .010, .006),
                           (.660, x, .176, .014, .008),
                           (.672, x, .178, .010, .006)), BUTTON))
    strokes = (rect(0, -.15 * depth, .61 * width, .564 * depth, fill=UPHOLSTERY),
               rect(0, .37 * depth, .85 * width, .24 * depth, fill=UPHOLSTERY),
               *(rect(side * .41 * width, -.06 * depth, .17 * width, .74 * depth,
                      fill=UPHOLSTERY) for side in (-1, 1)))
    return strokes, tuple(parts)
