"""Ceiling-mounted Leviton 9880 with a frosted A19 LED.

The 2.31-inch diameter, 1.53-inch projection and two-piece construction follow
the dimensional drawing linked from https://leviton.com/products/9880.
The rib relief and seam are estimated from the product photo.
"""

import math

from typehaus.model.placeable_symbols._a19_led import (
    A19_REFERENCE_SOCKET_FACE_IN,
    DIFFUSER_PROFILE,
    LED_BASE_PROFILE,
)
from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Part, circle
from typehaus.model.placeable_symbols._turned_profile import turned_profile

LEVITON_9880_SYMBOL = "leviton-9880-a19"
HOLDER_RADIUS_IN = 2.31 / 2
HOLDER_PROJECTION_IN = 1.53
ASSEMBLY_DIAMETER_IN = 19 / 8
# The authored mount uses a 5.5-inch band. The holder seats at the top of this band.
MOUNTING_BAND_IN = 5.5
PROFILE_SEGMENTS = 48
RIB_COUNT = 16
RIB_SEGMENTS = 12
RIB_CENTER_IN = .88

BACK_PROFILE = (
    (0, .75), (.90, .75), (1.08, .74), (1.135, .67), (HOLDER_RADIUS_IN, .12),
    (1.15, .04), (1.11, 0), (0, 0),
)
SEAM_PROFILE = ((0, .80), (1.00, .80), (1.00, .69), (0, .69))
FRONT_PROFILE = (
    (0, 1.53), (.68, 1.53), (.78, 1.51), (.84, 1.47), (.87, 1.39),
    (.92, 1.19), (.99, .98), (1.045, .88), (1.09, .85), (1.095, .79),
    (1.06, .76), (0, .76),
)
RIB_PROFILE = ((0, 1.40), (.04, 1.38), (.065, 1.33), (.092, 1.18),
               (.11, 1.01), (.075, .92), (0, .89))
SHELL_LIP_PROFILE = ((0, 1.62), (.55, 1.62), (.59, 1.58), (.59, 1.49), (0, 1.49))


def _rib_ring(rib: Part, offset: float) -> Part:
    positions, normals, triangles = [], [], []
    mesh = rib["mesh"]
    for index in range(RIB_COUNT):
        angle = math.tau * index / RIB_COUNT
        cosine, sine = math.cos(angle), math.sin(angle)
        start = len(positions)
        positions.extend(((x + offset) * cosine - y * sine,
                          (x + offset) * sine + y * cosine, z)
                         for x, y, z in mesh["positions"])
        normals.extend((x * cosine - y * sine, x * sine + y * cosine, z)
                       for x, y, z in mesh["normals"])
        triangles.extend((start + a, start + b, start + c) for a, b, c in mesh["triangles"])
    diameter = 2 * offset + rib["size"][0]
    return {**rib, "size": (diameter, diameter, rib["size"][2]),
            "mesh": {"positions": tuple(positions), "normals": tuple(normals),
                     "triangles": tuple(triangles)}}


def leviton_9880(width: float, depth: float, height: float) -> Geometry:
    radial_scale = min(width, depth) / ASSEMBLY_DIAMETER_IN
    axial_scale = height / MOUNTING_BAND_IN
    bulb_offset = HOLDER_PROJECTION_IN - A19_REFERENCE_SOCKET_FACE_IN

    def turned(profile, color, *, offset=0.0, segments=PROFILE_SEGMENTS, smooth=True):
        meridian = tuple((radius, MOUNTING_BAND_IN - projection - offset)
                         for radius, projection in profile)
        return turned_profile(meridian, radial_scale, axial_scale, color,
                              segments=segments, smooth=smooth)

    ribs = turned(RIB_PROFILE, "porcelain", segments=RIB_SEGMENTS)
    parts = (turned(BACK_PROFILE, "porcelain"),
             turned(SEAM_PROFILE, "metal-black", smooth=False),
             turned(FRONT_PROFILE, "porcelain"),
             _rib_ring(ribs, RIB_CENTER_IN * radial_scale),
             turned(SHELL_LIP_PROFILE, "metal", smooth=False),
             turned(LED_BASE_PROFILE, "plastic-white", offset=bulb_offset),
             turned(DIFFUSER_PROFILE, "lamp", offset=bulb_offset))
    # The installed A19 is slightly wider than the holder.
    return (circle(0, 0, min(width, depth) / 2),), parts
