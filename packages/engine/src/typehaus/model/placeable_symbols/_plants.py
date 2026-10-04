"""Indoor plant supports and foliage, shared by the canvas, viewer and exports."""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import (
    DETAIL_WEIGHT,
    box,
    circle,
    line,
    polygon,
    prism,
    rect,
)
from typehaus.model.placeable_symbols._plant_primitives import (
    folded_leaf,
    slender_segment,
    tapered_pot,
)

# Shelf elevations are illustrative; the mounting brackets use the manufacturer's template.
WALL_STAND_SHELF_TOP_FRACTIONS = (2 / 30.75, 14.25 / 30.75, 27 / 30.75)
WALL_STAND_ROD_DIAMETER_M = 0.004
WALL_STAND_TRAY_THICKNESS_M = 0.003
WALL_STAND_FRAME_WIDTH_SHARE = 0.58
WALL_STAND_RUNG_COUNT = 12
SMALL_POT_DIAMETER_SHARE = 3.5 / 5.5
SMALL_POT_HEIGHT_SHARE = 3.5 / 8
SMALL_PLANT_LEAF_COUNT = 12
STEM_RADIUS_M = 0.001
HANGING_POT_DIAMETER_SHARE = 12 / 16
HANGING_POT_BOTTOM_SHARE = 16 / 46
HANGING_POT_RIM_SHARE = 24 / 46
HANGING_CORD_RADIUS_M = 0.0015
HANGING_VINE_COUNT = 6
HANGING_VINE_STATIONS = 8


def wall_plant_stand(width: float, depth: float, height: float) -> Geometry:
    """A broad-face steel ladder and three round trays, without embedded plants."""
    rod = min(WALL_STAND_ROD_DIAMETER_M, width * 0.04, depth * 0.04, height * 0.02)
    frame_width = width * WALL_STAND_FRAME_WIDTH_SHARE
    rear_y = depth / 2 - rod / 2
    tray_radius = min(width, depth) / 2
    tray_thickness = min(WALL_STAND_TRAY_THICKNESS_M, height * 0.02)
    strokes = [circle(0, 0, tray_radius),
               rect(0, rear_y, frame_width, rod, fill="metal-black")]
    parts = [box(sign * (frame_width - rod) / 2, rear_y, 0, height,
                 rod, rod, "metal-black") for sign in (-1, 1)]
    for index in range(WALL_STAND_RUNG_COUNT):
        z = rod + (height - 2 * rod) * index / (WALL_STAND_RUNG_COUNT - 1)
        parts.append(box(0, rear_y, z - rod / 2, z + rod / 2,
                         frame_width, rod, "metal-black"))
    for fraction in WALL_STAND_SHELF_TOP_FRACTIONS:
        top = height * fraction
        parts.append(prism(circle(0, 0, tray_radius)["points"],
                           top - tray_thickness, top, "metal-black"))
    return tuple(strokes), tuple(parts)


def small_potted_plant(width: float, depth: float, height: float) -> Geometry:
    """A 3½-inch pot within a 5½-inch foliage envelope at the reference catalog size."""
    canopy_radius = min(width, depth) / 2
    pot_radius = canopy_radius * SMALL_POT_DIAMETER_SHARE
    rim = height * SMALL_POT_HEIGHT_SHARE
    strokes = [circle(0, 0, pot_radius, fill="porcelain")]
    parts = [tapered_pot(pot_radius, 0, rim, "porcelain"),
             prism(circle(0, 0, pot_radius * 0.86)["points"], rim * 0.94, rim, "potting-soil")]
    for index in range(SMALL_PLANT_LEAF_COUNT):
        angle = 2 * math.pi * (index + 0.15) / SMALL_PLANT_LEAF_COUNT
        center = (canopy_radius * 0.52 * math.cos(angle),
                  canopy_radius * 0.52 * math.sin(angle),
                  height * (0.62 + 0.10 * (index % 3)))
        leaf_length, leaf_width = canopy_radius * 0.82, canopy_radius * 0.38
        strokes.append(polygon(((0, 0),
            (center[0] - math.sin(angle) * leaf_width / 2,
             center[1] + math.cos(angle) * leaf_width / 2),
            (canopy_radius * 0.93 * math.cos(angle), canopy_radius * 0.93 * math.sin(angle)),
            (center[0] + math.sin(angle) * leaf_width / 2,
             center[1] - math.cos(angle) * leaf_width / 2)), weight=DETAIL_WEIGHT))
        parts.extend((slender_segment((0, 0, rim), center,
                                      min(STEM_RADIUS_M, canopy_radius * 0.02), "foliage"),
                      folded_leaf(center, leaf_length, leaf_width, angle, height * 0.22)))
    return tuple(strokes), tuple(parts)


def hanging_vine_planter(width: float, depth: float, height: float) -> Geometry:
    """A 12-inch basket, three cords and 24-inch vines in a 16×16×46-inch envelope."""
    canopy_radius = min(width, depth) / 2
    pot_radius = canopy_radius * HANGING_POT_DIAMETER_SHARE
    bottom, rim = height * HANGING_POT_BOTTOM_SHARE, height * HANGING_POT_RIM_SHARE
    cord_radius = min(HANGING_CORD_RADIUS_M, canopy_radius * 0.015, height * 0.005)
    stem_radius = min(STEM_RADIUS_M, canopy_radius * 0.01, height * 0.003)
    strokes = [circle(0, 0, pot_radius, fill="terracotta")]
    parts = [tapered_pot(pot_radius, bottom, rim, "terracotta"),
             prism(circle(0, 0, pot_radius * 0.86)["points"],
                   rim - height * 0.01, rim, "potting-soil"),
             box(0, 0, height - cord_radius * 4, height,
                 canopy_radius * 0.20, canopy_radius * 0.06, "metal-black")]
    for index in range(3):
        angle = 2 * math.pi * index / 3
        at_rim = (pot_radius * math.cos(angle), pot_radius * math.sin(angle), rim)
        parts.append(slender_segment(at_rim, (0, 0, height - cord_radius * 4),
                                     cord_radius, "metal-black"))
        strokes.append(line((0, 0), at_rim[:2]))
    for vine in range(HANGING_VINE_COUNT):
        angle = 2 * math.pi * (vine + 0.12) / HANGING_VINE_COUNT
        vine_length = rim * (0.80 + 0.035 * vine)
        previous = (pot_radius * 0.86 * math.cos(angle),
                    pot_radius * 0.86 * math.sin(angle), rim)
        for station in range(HANGING_VINE_STATIONS):
            fraction = (station + 1) / HANGING_VINE_STATIONS
            radius = pot_radius * (0.86 + 0.10 * math.sin(fraction * math.pi * 2))
            leaf_angle = angle + (0.55 if station % 2 else -0.55)
            point = (radius * math.cos(angle), radius * math.sin(angle),
                     rim - vine_length * fraction)
            leaf_length = canopy_radius * 0.28
            leaf_width = min(canopy_radius * 0.20, rim * 0.10)
            parts.extend((slender_segment(previous, point, stem_radius, "foliage"),
                          folded_leaf(point, leaf_length, leaf_width, leaf_angle,
                                      -leaf_width * 0.4)))
            previous = point
        strokes.append(polygon(((pot_radius * 0.80 * math.cos(angle),
                                 pot_radius * 0.80 * math.sin(angle)),
                                (canopy_radius * 0.97 * math.cos(angle - 0.12),
                                 canopy_radius * 0.97 * math.sin(angle - 0.12)),
                                (canopy_radius * 0.97 * math.cos(angle + 0.12),
                                 canopy_radius * 0.97 * math.sin(angle + 0.12))),
                               fill="foliage", weight=DETAIL_WEIGHT))
    return tuple(strokes), tuple(parts)
