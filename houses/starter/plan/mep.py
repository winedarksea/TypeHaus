# haus: editable
# The passive radon system MN 1303.2402 requires of every new Minnesota dwelling.
#
# Three elements, and every new house in the state needs all three: a sealed collection
# point under the floor, a pipe that carries the soil gas from it to above the roof, and a
# box beside the pipe so a fan can be added later without opening a wall. There is no
# "small house" exemption — this is the shortest complete version of the system.

from typehaus import (
    DeviceKind,
    ElectricalDevice,
    Mount,
    MountKind,
    PipeSystem,
    Sump,
    VentRun,
    ft,
    inch,
    pt,
)

# The collection point (subpart 3/4.E). It sits in the north-west corner of the floor,
# under the upper storey's landing, so the pipe above it rises inside a closet corner
# instead of through the middle of the room.
#
# The starter models no foundation yet, so the pit names no `host_ref`: add one pointing
# at your slab when you author it. `sealed_cover=True` is what subpart 4.E grades — an
# open pit vents the soil gas straight back into the house.
SUMP = [
    Sump(uid="Q2CDVAATY2", tag="SM-RADON", position=pt(ft(1), ft(16)),
         diameter=inch(12), depth=inch(18),
         sealed_cover=True, radon_vent=True, vent_ref="VR-RADON"),
]

# The vent (subpart 5). Up the landing's corner to 16'-0", out through the west wall, then
# up the siding to 21'-0". `systems` is a tuple, so the one-element case still needs its
# trailing comma; a house with plumbing would add PipeSystem.VENT here and share the chase.
#
# 21'-0" is authored rather than derived because the starter has no Roof element for the
# resolver to measure from — normally you leave `roof_termination_elevation` off and let
# the engine put the terminal 12" above the true roof surface. It is the number subpart 5
# turns on: the highest window head in the house is the upper storey's at 16'-6", so every
# opening sits more than 2' below the exhaust and the soil gas cannot fall back in. That
# matters here because the footprint is only 24' x 20' — nowhere on it is a full 10' from
# every window, so the system earns its clearance vertically.
RISER = [
    VentRun(uid="BAMTTS248T", tag="VR-RADON", systems=(PipeSystem.RADON,), diameter=inch(3),
            chase_position=pt(ft(1), ft(16)), start_elevation=ft(-2),
            exit_elevation=ft(16), exit_offset=pt(ft(-2), ft(0)),
            roof_termination_elevation=ft(21),
            wall_ref="W-204", attachment="standing_seam_clamp"),
]

# The future fan's power (subpart 6). An approved box gets installed with the house even
# though the fan may never be; the rule also forbids putting it in conditioned space, a
# basement or a crawl space, which is why it rides the siding beside the exterior riser
# rather than sitting next to the pit.
FAN_BOX = [
    ElectricalDevice(uid="1S4K85KRDC", tag="ED-RADON-FAN-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(-1), ft(13)),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(10))),
]
