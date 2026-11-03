# haus: editable
# Night-light motion sensors (IKEA MYGGSPRAY): one in each room holding a 2200 K night-light
# run, plus one at the basement stair. HA turns the room's run on 22:00-07:00 on motion
# (notes/smart_home.md). Battery, Thread via the ZBT-2. Type and product:
# plan/motion_sensor_types.py. All at 72" AFF (maker limit 78.7"), on a wall of the room
# (face = the room side), off the door casing and the mirrors, never in a wet enclosure.

from typehaus import DeviceKind, ElectricalDevice, Mount, MountKind, deg, inch
from typehaus.model import Location, WallAttachment

BASEMENT_ELEMENTS = [
    # Bath: north wall east of the WC, door cross-view on the east wall, lav to the south.
    ElectricalDevice(uid="P5P47W7S1K", tag="ED-B-BATH-MOTION", kind=DeviceKind.SWITCH, type_ref="ED-T-MOTION-MYGGSPRAY",
                     room="RM-B-BATH", mount=Mount(kind=MountKind.WALL, elevation=inch(72)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-BA-N", face="right", distance_from_start=inch(36),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Stair foot: hall side (east) wall at the foot of the lower flight. Sees the hall
    # approach and the first risers; would trigger LR-B-STAIR-RAIL (no night-light run yet,
    # the rail strip is on the 3-way pair ED-B-STAIR-SW / ED-M-STAIR-SW).
    ElectricalDevice(uid="1VD5NW5KK0", tag="ED-B-STAIR-MOTION", kind=DeviceKind.SWITCH, type_ref="ED-T-MOTION-MYGGSPRAY",
                     room="RM-B-STAIR", mount=Mount(kind=MountKind.WALL, elevation=inch(72)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CN", face="left", distance_from_start=inch(30.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]

MAIN_ELEMENTS = [
    # Hall bath: north wall mid-room; sees the east door, the WC (SW) and the lav (S).
    ElectricalDevice(uid="PZM4JR34KG", tag="ED-M-BATH1-MOTION", kind=DeviceKind.SWITCH, type_ref="ED-T-MOTION-MYGGSPRAY",
                     room="RM-M-BATH1", mount=Mount(kind=MountKind.WALL, elevation=inch(72)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-STOS", face="right", distance_from_start=inch(45),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Bath 2: entry wall, west of the door and 22" above the switch stack at its corner;
    # looks across the vanity, WC and tub, clear of the shower (x >= 58").
    ElectricalDevice(uid="H28FC7KCR4", tag="ED-M-BATH2-MOTION", kind=DeviceKind.SWITCH, type_ref="ED-T-MOTION-MYGGSPRAY",
                     room="RM-M-BATH2", mount=Mount(kind=MountKind.WALL, elevation=inch(72)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-BDN1", face="left", distance_from_start=inch(16),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]

SECOND_ELEMENTS = [
    # Bath 1: west wall between the closet corner and the window/WC; looks across to the
    # south door and the lav.
    ElectricalDevice(uid="X00WWV6TEG", tag="ED-S-BATH1-MOTION", kind=DeviceKind.SWITCH, type_ref="ED-T-MOTION-MYGGSPRAY",
                     room="RM-S-BATH1", mount=Mount(kind=MountKind.WALL, elevation=inch(72)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-W1", face="left", distance_from_start=inch(57),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Vanity alcove: south wall centred between the hand-towel bars, above the night relay.
    ElectricalDevice(uid="VXVSJQAYGW", tag="ED-S-VANITY-MOTION", kind=DeviceKind.SWITCH, type_ref="ED-T-MOTION-MYGGSPRAY",
                     room="RM-S-VANITY", mount=Mount(kind=MountKind.WALL, elevation=inch(72)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SN1", face="left", distance_from_start=inch(37.4),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Suite bath: west wall midway between the pegs and the towel bar; sees the south door,
    # the WC and the lav; the tub is on the far east wall.
    ElectricalDevice(uid="1ZQN20GYDV", tag="ED-S-SUITEBATH-MOTION", kind=DeviceKind.SWITCH, type_ref="ED-T-MOTION-MYGGSPRAY",
                     room="RM-S-SUITEBATH", mount=Mount(kind=MountKind.WALL, elevation=inch(72)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-DC2", face="right", distance_from_start=inch(37),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]

ATTIC_ELEMENTS = [
    # Studio bath: south wall under the rake where the ceiling clears 80", between the
    # towel bar and the switch; sees the door to the east and the WC (W).
    ElectricalDevice(uid="T3R7GNVAGA", tag="ED-A-STUBATH-MOTION", kind=DeviceKind.SWITCH, type_ref="ED-T-MOTION-MYGGSPRAY",
                     room="RM-A-STUBATH", mount=Mount(kind=MountKind.WALL, elevation=inch(72)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-BATH-S", face="left", distance_from_start=inch(46),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]
