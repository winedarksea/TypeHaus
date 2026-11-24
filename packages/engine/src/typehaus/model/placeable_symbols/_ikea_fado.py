"""IKEA FADO table lamp, white (US art. 700.963.77; EU 25 cm, 800.963.72).

Published: opal white glass globe on a polypropylene base; 9 in high x 10 in dia (US,
rounded; EU lists 24 x 25 cm = 9.45 x 9.84 in, used here); E26 (US) / E27 (EU), max 75 W.
Estimated from photos, not published: the base height and foot, and the globe's flat-cut
neck, which is whatever the 24 cm height leaves under a 25 cm sphere. The cord is omitted.
Reference: https://www.ikea.com/us/en/p/fado-table-lamp-white-70096377/
"""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import circle
from typehaus.model.placeable_symbols._turned_profile import turned_profile

GLOBE_DIAMETER = 25 / 2.54  # in
OVERALL_HEIGHT = 24 / 2.54
BASE_HEIGHT = 0.6  # estimated
FOOT_RADIUS = 2.3  # estimated; the base flares to the globe's neck
SEGMENTS = 48
ARC_STEPS = 24


def ikea_fado_table_lamp(width: float, depth: float, height: float) -> Geometry:
    """Round in plan: the glyph follows the smaller of width and depth, never height."""
    globe_r = GLOBE_DIAMETER / 2
    centre = OVERALL_HEIGHT - globe_r  # sphere centre height; its top is the lamp's top
    neck_r = math.sqrt(globe_r ** 2 - (BASE_HEIGHT - centre) ** 2)
    first = math.atan2(neck_r, centre - BASE_HEIGHT)  # angle from the sphere's bottom pole
    angles = [first + (math.pi - first) * i / ARC_STEPS for i in range(ARC_STEPS + 1)]
    # Meridians as (radius, height) fractions; the neck is closed by the base.
    globe = ((0.0, BASE_HEIGHT / OVERALL_HEIGHT),) + tuple(
        (math.sin(a), (centre - globe_r * math.cos(a)) / OVERALL_HEIGHT)
        for a in angles[:-1]) + ((0.0, 1.0),)
    base = ((0.0, 0.0), (FOOT_RADIUS * .9 / globe_r, 0.0),
            (FOOT_RADIUS / globe_r, .1 / OVERALL_HEIGHT),
            (neck_r / globe_r, BASE_HEIGHT / OVERALL_HEIGHT),
            (0.0, BASE_HEIGHT / OVERALL_HEIGHT))
    radius = min(width, depth) / 2
    parts = (turned_profile(base, radius, height, "plastic-white", segments=SEGMENTS,
                            smooth=True),
             turned_profile(globe, radius, height, "lamp", segments=SEGMENTS, smooth=True))
    strokes = (circle(0, 0, radius, fill="lamp"),
               circle(0, 0, radius * FOOT_RADIUS / globe_r))
    return strokes, parts
