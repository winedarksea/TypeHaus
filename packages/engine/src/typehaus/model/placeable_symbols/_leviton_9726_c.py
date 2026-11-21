"""Leviton 9726-C with a frosted A19 LED in the wall-mount orientation.

The 4.56-inch flange and 2.50-inch holder projection follow Leviton's catalog
(https://assets.usesi.com/product-media/catalogs/USESI_6599_catalog.pdf).
The profile and hardware are estimated from Leviton's product photo. The model
shows the factory bead chain with a short pull.
"""

from typehaus.model.placeable_symbols._a19_led import DIFFUSER_PROFILE, LED_BASE_PROFILE
from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import Part, rect
from typehaus.model.placeable_symbols._round_hardware import round_cylinder
from typehaus.model.placeable_symbols._turned_profile import turned_profile
from typehaus.model.placeable_symbols.receptacles import (
    _clipped_outline,
    _depth_extrusion,
    _slot_marks,
)
from typehaus.quantities import M_PER_IN

LEVITON_9726_C_SYMBOL = "leviton-9726-c-a19"
MOUNTING_FLANGE_DIAMETER_IN = 4.56
ASSEMBLY_PROJECTION_IN = 5.5
ASSEMBLY_HEIGHT_IN = 5.5
PROFILE_SEGMENTS = 48
CHAIN_SEGMENTS = 12
CHAIN_BEAD_RADIUS_IN = .055
CHAIN_BEAD_PITCH_IN = .15
CHAIN_BEAD_COUNT = 13
CHAIN_LENGTH_IN = 2.27

# Meridians run from the room-facing end toward the box, in (radius, projection) inches.
PORCELAIN_PROFILE = (
    (0, 2.50), (.88, 2.50), (.99, 2.46), (1.05, 2.35), (1.06, 2.15),
    (1.02, 1.48), (1.06, 1.18), (1.18, .92), (1.44, .69), (1.93, .50),
    (2.17, .40), (2.25, .31), (2.28, .19), (2.28, .08), (2.24, .02), (2.18, 0), (0, 0),
)


def leviton_9726_c(width: float, depth: float, height: float) -> Geometry:
    radial_scale = min(width / MOUNTING_FLANGE_DIAMETER_IN, height / ASSEMBLY_HEIGHT_IN)
    projection_scale = depth / ASSEMBLY_PROJECTION_IN
    chain_scale = min(radial_scale, projection_scale)
    socket_z = height / 2

    def wall_profile(profile, color, *, smooth=False):
        # A quarter-turn keeps the plate centered on the box with its back at +depth/2.
        meridian = tuple((radius, -projection) for radius, projection in profile)
        part = turned_profile(meridian, radial_scale, projection_scale, color,
                              segments=PROFILE_SEGMENTS, smooth=smooth)
        mesh = part["mesh"]
        return {**part, "center": (0, part["center"][2] + depth / 2, socket_z),
                "size": (part["size"][0], part["size"][2], part["size"][1]),
                "mesh": {**mesh,
                         "positions": tuple((x, z + depth / 2, socket_z - y)
                                            for x, y, z in mesh["positions"]),
                         "normals": tuple((x, z, -y) for x, y, z in mesh["normals"])}}

    shell_lip = (
        (0, 2.58), (.55, 2.58), (.57, 2.55), (.58, 2.47), (0, 2.47),
    )
    parts: list[Part] = [
        wall_profile(PORCELAIN_PROFILE, "porcelain", smooth=True),
        wall_profile(shell_lip, "metal"),
        wall_profile(LED_BASE_PROFILE, "plastic-white", smooth=True),
        wall_profile(DIFFUSER_PROFILE, "lamp", smooth=True),
    ]
    # The outlet sits on a raised boss beside the socket, where it clears the bulb.
    outlet_x, outlet_z = 1.22 * radial_scale, socket_z + .87 * radial_scale
    outlet_front = depth / 2 - 1.13 * projection_scale
    outlet_back = depth / 2 - .32 * projection_scale
    outlet_outline = _clipped_outline(outlet_x, outlet_z, .91 * radial_scale,
                                      1.03 * radial_scale, .14)
    parts.append(_depth_extrusion(outlet_outline, outlet_front, outlet_back, "porcelain"))
    parts.extend(_slot_marks(outlet_x, outlet_z, radial_scale / M_PER_IN,
                             outlet_front - .012 * projection_scale, outlet_front, "120"))

    for offset in (-1.65, 1.65):
        parts.append(round_cylinder(
            (offset * radial_scale, depth / 2 - .63 * projection_scale, socket_z),
            .135 * radial_scale, .10 * projection_scale, axis=1, color="metal"))

    chain_x, chain_y = -1.37 * radial_scale, depth / 2 - .85 * projection_scale
    chain_end = socket_z - CHAIN_LENGTH_IN * chain_scale
    chain_profile = [(0, 0), (.085, 0), (.10, .09), (.065, .23), (.021, .27)]
    for index in range(CHAIN_BEAD_COUNT):
        position = .30 + index * CHAIN_BEAD_PITCH_IN
        chain_profile.extend(((.021, position - CHAIN_BEAD_RADIUS_IN / 2),
                              (CHAIN_BEAD_RADIUS_IN, position),
                              (.021, position + CHAIN_BEAD_RADIUS_IN / 2)))
    chain_profile.extend(((.021, CHAIN_LENGTH_IN), (0, CHAIN_LENGTH_IN)))
    chain = turned_profile(tuple(chain_profile), chain_scale, chain_scale, "metal",
                           segments=CHAIN_SEGMENTS)
    mesh = chain["mesh"]
    parts.append({**chain, "center": (chain_x, chain_y, chain_end + chain["center"][2]),
                  "mesh": {**mesh, "positions": tuple(
                      (chain_x + x, chain_y + y, chain_end + z)
                      for x, y, z in mesh["positions"])}})
    parts.append(round_cylinder((chain_x, chain_y, socket_z), .18 * radial_scale,
                                .22 * chain_scale, axis=2, color="porcelain"))
    return (rect(0, 0, width, depth),), tuple(parts)
