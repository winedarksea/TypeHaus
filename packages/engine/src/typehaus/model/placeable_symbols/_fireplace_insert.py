"""Lightweight infrared insert: open firebox, static log bed and upper heater grille.

Proportions suggest the ClassicFlame 28II042FGL; internal details are schematic.
The dark open face avoids a transparent pane's sorting and reflection costs.
"""

import math

from typehaus.model.placeable_symbols._frame import Part, Stroke, box, line, rect
from typehaus.model.placeable_symbols._mesh import mesh_part, outward

UPPER_GRILLE_BOTTOM = 0.79
UPPER_GRILLE_TOP = 0.94
GRILLE_LOUVER_COUNT = 4
GRILLE_LOUVER_HEIGHT = 0.012
LOG_CROSS_SECTION_SEGMENTS = 8
LOG_LAYOUT = ((-0.08, -0.13, 0.15, 0.56), (0.08, 0.01, 0.23, 0.58),
              (-0.03, -0.07, 0.31, 0.39))


def fireplace_insert(width: float, depth: float, height: float
                     ) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    """Front faces local -Y; all details stay within the equipment envelope."""
    def panel(x, y, bottom, top, span, thickness, color, role):
        return {**box(x * width, y * depth, bottom * height, top * height,
                      span * width, thickness * depth, color), "role": role}

    parts = [panel(0, 0.47, 0, 1, 1, 0.06, "metal-black", "fireplace:back"),
             panel(0, 0, 0, 0.06, 1, 1, "metal-black", "fireplace:floor"),
             panel(0, 0, 0.94, 1, 1, 1, "metal-black", "fireplace:top")]
    for side in (-1, 1):
        parts.append(panel(side * 0.48, 0, 0.06, 0.94, 0.04, 1,
                           "metal-black", "fireplace:side"))
        parts.append(panel(side * 0.4475, -0.46, 0.06, 0.94, 0.025, 0.08,
                           "luminaire-housing", "fireplace:bezel"))
    parts.extend((panel(0, -0.46, 0.06, 0.11, 0.87, 0.08,
                        "luminaire-housing", "fireplace:sill"),
                  panel(0, -0.46, 0.75, UPPER_GRILLE_BOTTOM, 0.87, 0.08,
                        "metal-black", "fireplace:header"),
                  panel(0, -0.33, UPPER_GRILLE_BOTTOM, UPPER_GRILLE_TOP, 0.87, 0.08,
                        "metal-black", "fireplace:grille-recess"),
                  panel(0, 0.425, 0.11, 0.75, 0.87, 0.03,
                        "screen", "fireplace:firebox-liner")))
    # Separate slats leave actual shadow gaps without a perforated mesh or texture.
    grille_height = UPPER_GRILLE_TOP - UPPER_GRILLE_BOTTOM
    for index in range(GRILLE_LOUVER_COUNT):
        bottom = UPPER_GRILLE_BOTTOM + grille_height * (index + 0.5) / GRILLE_LOUVER_COUNT
        parts.append(panel(0, -0.455, bottom, bottom + GRILLE_LOUVER_HEIGHT,
                           0.84, 0.065, "luminaire-housing", "fireplace:louver"))
    for station in (-0.28, 0, 0.28):
        parts.append(panel(station, -0.455, UPPER_GRILLE_BOTTOM, UPPER_GRILLE_TOP,
                           0.008, 0.065, "metal-black", "fireplace:grille-guard"))
    parts.append(panel(0, -0.06, 0.11, 0.145, 0.76, 0.60,
                       "fireplace-ember", "fireplace:ember-bed"))
    # Eight-sided logs keep a rounded silhouette without bark textures or dense meshes.
    for log_index, (x, y, bottom, span) in enumerate(LOG_LAYOUT):
        vertices = []
        slope = 0.025 if log_index % 2 else -0.025
        for end in (-1, 1):
            for index in range(LOG_CROSS_SECTION_SEGMENTS):
                angle = math.tau * index / LOG_CROSS_SECTION_SEGMENTS
                vertices.append(((x + end * span / 2) * width,
                                 (y + math.cos(angle) * 0.10) * depth,
                                 (bottom + 0.05 + end * slope
                                  + math.sin(angle) * 0.05) * height))
        segments = LOG_CROSS_SECTION_SEGMENTS
        triangles = []
        for index in range(1, segments - 1):
            triangles.extend(((0, index + 1, index),
                              (segments, segments + index, segments + index + 1)))
        for index in range(segments):
            following = (index + 1) % segments
            triangles.extend(((index, following, segments + following),
                              (index, segments + following, segments + index)))
        parts.append({**mesh_part(vertices, outward(vertices, triangles), "fireplace-log"),
                      "role": "fireplace:log"})
    for station in (-0.27, -0.09, 0.09, 0.27):
        parts.append(panel(station, -0.35, 0.12, 0.23, 0.012, 0.025,
                           "metal-black", "fireplace:log-grate"))
    # Plan strokes depend only on the footprint, as required by the symbol contract.
    strokes = (rect(0, 0, width, depth),
               line((-width * 0.46, -depth * 0.42), (width * 0.46, -depth * 0.42)))
    return strokes, tuple(parts)
