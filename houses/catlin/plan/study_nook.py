# haus: editable
# Study 2 window seat under ST-S2A, against W-S-SS2's south face (y=105.625"). 2026-10-02.
# West to east: 1/2" cover, 18" SEKTION open shelves (83 1/2" top, 13" under the stringers),
# three 24" seat units (19 1/2" top), 1/2" end. x=264"..355"; W-S-SS2 starts at x=263".
# The partition clears D-S-STUDY2's casing (x~261.6"). ED-S-STUDY2-RC3 rose above the top.
# Reading light: a mark-K sconce (<=4" projection) over the west seat, the head end, where the
# stringers are 87" up; its dimmer is in the corner by the shelves, reachable seated or lying.

from typehaus import (DeviceKind, ElectricalDevice, Furniture, Location, Mount, MountKind,
                      WallAttachment)
from typehaus.model import deg, inch

STUDY_NOOK = [
    Furniture(uid="5JZP1S0NBN", tag="FURN-S-STUDY-NOOK-COVER", type_ref="FT-S-STUDY-NOOK-COVER-80",
              room="RM-S-STUDY2", mount=Mount(kind=MountKind.FLOOR, elevation=inch(3.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-SS2", face="right", distance_from_start=inch(1.25),
                  normal_gap=inch(0.25), rotation_offset=deg(0)))),
    Furniture(uid="R7H4YZPP71", tag="FURN-S-STUDY-NOOK-SHELF", type_ref="FURN-S-STUDY-NOOK-SHELF-18",
              room="RM-S-STUDY2", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-SS2", face="right", distance_from_start=inch(10.5),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="67SFJ2Y57A", tag="FURN-S-STUDY-NOOK-SEAT-W", type_ref="FURN-S-STUDY-NOOK-SEAT-24",
              room="RM-S-STUDY2", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-SS2", face="right", distance_from_start=inch(31.5),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="ZKS7ZJW3V6", tag="FURN-S-STUDY-NOOK-SEAT-C", type_ref="FURN-S-STUDY-NOOK-SEAT-24",
              room="RM-S-STUDY2", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-SS2", face="right", distance_from_start=inch(55.5),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="4F4JEG83Z2", tag="FURN-S-STUDY-NOOK-SEAT-E", type_ref="FURN-S-STUDY-NOOK-SEAT-24",
              room="RM-S-STUDY2", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-SS2", face="right", distance_from_start=inch(79.5),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="G20P3WJK82", tag="FURN-S-STUDY-NOOK-END", type_ref="FT-S-STUDY-NOOK-SEAT-END",
              room="RM-S-STUDY2", mount=Mount(kind=MountKind.FLOOR, elevation=inch(3.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-SS2", face="right", distance_from_start=inch(91.75),
                  normal_gap=inch(0.25), rotation_offset=deg(0)))),
    ElectricalDevice(uid="PMAV30JY2Q", tag="ED-S-STUDY2-NOOK-SC", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-STAIR",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2",
                     controlled_by=("ED-S-STUDY2-NOOK-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SS2", face="right", distance_from_start=inch(31.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="17T7VZK2WG", tag="ED-S-STUDY2-NOOK-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-SWITCH-DIM",
                     circuit="CKT-LT-UPPER", room="RM-S-STUDY2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(34)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SS2", face="right", distance_from_start=inch(22.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]
