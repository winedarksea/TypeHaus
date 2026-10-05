"""A sparse woody ficus with folded, fiddle-shaped blades rather than a radial canopy."""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, circle, polygon, prism
from typehaus.model.placeable_symbols._plant_primitives import (
    _mesh_part,
    slender_segment,
    tapered_pot,
)

LEAF_COUNT = 10
LEAF_SPIRAL_ANGLE = math.pi * (3 - math.sqrt(5))
# Narrow attachment, pinched waist and broad rounded tip distinguish a fiddle from a lance.
LEAF_HALF_WIDTH_PROFILE = (
    (0.0, 0.0), (0.18, 0.32), (0.38, 0.25),
    (0.62, 0.50), (0.85, 0.46), (0.97, 0.25), (1.0, 0.0),
)
POT_DIAMETER_SHARE = 14 / 24
POT_HEIGHT_SHARE = 14 / 60
LEAF_LENGTH_RADIUS_SHARE = 0.78
LEAF_WIDTH_RADIUS_SHARE = 0.62
LEAF_ATTACHMENT_RADIUS_SHARE = 0.14
LOWEST_LEAF_HEIGHT_SHARE = 0.42
HIGHEST_LEAF_HEIGHT_SHARE = 0.92
LEAF_RISE_HEIGHT_SHARE = 0.08
LEAF_FOLD_WIDTH_SHARE = 0.10
TRUNK_RADIUS_SHARE = 0.035
PETIOLE_RADIUS_SHARE = 0.009


def fiddle_leaf_fig(width: float, depth: float, height: float) -> Geometry:
    """Ten double-sided leaf meshes on a visible trunk; one shared model for all outputs."""
    radius = min(width, depth) / 2
    pot_radius, rim = radius * POT_DIAMETER_SHARE, height * POT_HEIGHT_SHARE
    trunk_radius = min(radius * TRUNK_RADIUS_SHARE, height * 0.02)
    petiole_radius = min(radius * PETIOLE_RADIUS_SHARE, height * 0.005)
    strokes = [circle(0, 0, pot_radius, fill="terracotta")]
    parts = [tapered_pot(pot_radius, 0, rim, "terracotta"),
             prism(circle(0, 0, pot_radius * 0.86)["points"], rim * 0.94, rim,
                   "potting-soil"),
             slender_segment((0, 0, rim * 0.94), (0, 0, height * 0.96),
                             trunk_radius, "wood-dark")]
    leaf_length = radius * LEAF_LENGTH_RADIUS_SHARE
    leaf_width = radius * LEAF_WIDTH_RADIUS_SHARE
    # Limit the fold by height too so the model also fits unusually short catalog envelopes.
    fold = min(leaf_width * LEAF_FOLD_WIDTH_SHARE, height * 0.025)
    for index in range(LEAF_COUNT):
        angle = index * LEAF_SPIRAL_ANGLE
        along = (math.cos(angle), math.sin(angle))
        across = (-along[1], along[0])
        elevation = height * (LOWEST_LEAF_HEIGHT_SHARE + index / (LEAF_COUNT - 1)
                              * (HIGHEST_LEAF_HEIGHT_SHARE - LOWEST_LEAF_HEIGHT_SHARE))
        attachment = (radius * LEAF_ATTACHMENT_RADIUS_SHARE * along[0],
                      radius * LEAF_ATTACHMENT_RADIUS_SHARE * along[1], elevation)
        parts.append(slender_segment((0, 0, elevation - height * 0.025), attachment,
                                     petiole_radius, "wood-dark"))
        outline = [*LEAF_HALF_WIDTH_PROFILE,
                   *((station, -half_width)
                     for station, half_width in reversed(LEAF_HALF_WIDTH_PROFILE[1:-1]))]
        positions = [(attachment[0] + along[0] * station * leaf_length
                      + across[0] * half_width * leaf_width,
                      attachment[1] + along[1] * station * leaf_length
                      + across[1] * half_width * leaf_width,
                      elevation + station * height * LEAF_RISE_HEIGHT_SHARE)
                     for station, half_width in outline]
        strokes.append(polygon(tuple(point[:2] for point in positions),
                               fill="foliage", weight=DETAIL_WEIGHT))
        # A raised midrib makes both sides legible without adding veins or tiny leaf parts.
        positions.append((attachment[0] + along[0] * leaf_length * 0.55,
                          attachment[1] + along[1] * leaf_length * 0.55,
                          elevation + height * LEAF_RISE_HEIGHT_SHARE * 0.55 + fold))
        front = [(edge, (edge + 1) % len(outline), len(outline))
                 for edge in range(len(outline))]
        parts.append(_mesh_part(positions, front + [(a, c, b) for a, b, c in front],
                                "foliage"))
    return tuple(strokes), tuple(parts)
