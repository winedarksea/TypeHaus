# haus: editable
# North-wall displays: x=73.9375, 97.9375, 121.9375, 145.9375 inches, centred on the desk.
# Mount elevations are AFF; backing elevations are above the second-storey datum.
# Shelf tops are illustrative; use the delivered IKEA 720 mm template for bracket holes.
# Pots rest on trays at floor-relative heights; wall attachments keep their centres aligned.
# The hanging assemblies include their cords: 46-inch body + 1.165-inch ceiling offset
# gives drop=47.165 inches, so the eye plate meets the finished PVC ceiling, not its datum.

from typehaus import Furniture, Location, Mount, MountKind, WallAttachment, WallBacking
from typehaus.model import deg, inch, pt

PLANT_ROOM_PLACEABLES = [
    Furniture(uid="PLNSTND001", tag="FURN-S-PLANT-STAND-1",
              type_ref="FT-PLANT-ROOM-SKUGGRONA", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS1", face="right", distance_from_start=inch(73.9375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNPOT0101", tag="FURN-S-PLANT-STAND-1-POT-1",
              type_ref="FT-PLANT-ROOM-POT-3P5", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(50)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS1", face="right", distance_from_start=inch(73.9375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNPOT0102", tag="FURN-S-PLANT-STAND-1-POT-2",
              type_ref="FT-PLANT-ROOM-POT-3P5", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(62.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS1", face="right", distance_from_start=inch(73.9375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNPOT0103", tag="FURN-S-PLANT-STAND-1-POT-3",
              type_ref="FT-PLANT-ROOM-POT-3P5", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(75)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS1", face="right", distance_from_start=inch(73.9375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNSTND002", tag="FURN-S-PLANT-STAND-2",
              type_ref="FT-PLANT-ROOM-SKUGGRONA", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS1", face="right", distance_from_start=inch(97.9375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNPOT0201", tag="FURN-S-PLANT-STAND-2-POT-1",
              type_ref="FT-PLANT-ROOM-POT-3P5", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(50)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS1", face="right", distance_from_start=inch(97.9375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNPOT0202", tag="FURN-S-PLANT-STAND-2-POT-2",
              type_ref="FT-PLANT-ROOM-POT-3P5", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(62.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS1", face="right", distance_from_start=inch(97.9375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNPOT0203", tag="FURN-S-PLANT-STAND-2-POT-3",
              type_ref="FT-PLANT-ROOM-POT-3P5", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(75)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS1", face="right", distance_from_start=inch(97.9375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNSTND003", tag="FURN-S-PLANT-STAND-3",
              type_ref="FT-PLANT-ROOM-SKUGGRONA", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS2", face="right", distance_from_start=inch(6.4375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNPOT0301", tag="FURN-S-PLANT-STAND-3-POT-1",
              type_ref="FT-PLANT-ROOM-POT-3P5", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(50)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS2", face="right", distance_from_start=inch(6.4375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNPOT0302", tag="FURN-S-PLANT-STAND-3-POT-2",
              type_ref="FT-PLANT-ROOM-POT-3P5", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(62.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS2", face="right", distance_from_start=inch(6.4375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNPOT0303", tag="FURN-S-PLANT-STAND-3-POT-3",
              type_ref="FT-PLANT-ROOM-POT-3P5", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(75)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS2", face="right", distance_from_start=inch(6.4375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNSTND004", tag="FURN-S-PLANT-STAND-4",
              type_ref="FT-PLANT-ROOM-SKUGGRONA", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS2", face="right", distance_from_start=inch(30.4375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNPOT0401", tag="FURN-S-PLANT-STAND-4-POT-1",
              type_ref="FT-PLANT-ROOM-POT-3P5", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(50)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS2", face="right", distance_from_start=inch(30.4375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNPOT0402", tag="FURN-S-PLANT-STAND-4-POT-2",
              type_ref="FT-PLANT-ROOM-POT-3P5", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(62.25)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS2", face="right", distance_from_start=inch(30.4375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNPOT0403", tag="FURN-S-PLANT-STAND-4-POT-3",
              type_ref="FT-PLANT-ROOM-POT-3P5", room="RM-S-PLANT",
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(75)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-PS2", face="right", distance_from_start=inch(30.4375),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="PLNHANG0NW", tag="FURN-S-PLANT-HANG-NW",
              type_ref="FT-PLANT-ROOM-HANGING-VINE-12", room="RM-S-PLANT",
              position=pt(inch(25.915), inch(96)),
              mount=Mount(kind=MountKind.CEILING, drop=inch(47.165))),
    Furniture(uid="PLNHANG0NE", tag="FURN-S-PLANT-HANG-NE",
              type_ref="FT-PLANT-ROOM-HANGING-VINE-12", room="RM-S-PLANT",
              position=pt(inch(193.96), inch(96)),
              mount=Mount(kind=MountKind.CEILING, drop=inch(47.165))),
]

# Four 14.5-inch clear stud bays; both ends of every block butt a stud face.
PLANT_ROOM_BACKING = [
    WallBacking(uid="PLNBK0101A", tag="BK-S-PLANT-STAND-1-LOW",
                wall_ref="W-S-PS1", face="right", start=inch(64.75),
                length=inch(14.5), elevation=inch(48), height=inch(7.25),
                profile="2x8", material_ref="spf",
                purpose="SKUGGRONA stand 1 lower bracket; sealed spacer to stud-bay block"),
    WallBacking(uid="PLNBK0102A", tag="BK-S-PLANT-STAND-1-HIGH",
                wall_ref="W-S-PS1", face="right", start=inch(64.75),
                length=inch(14.5), elevation=inch(72), height=inch(7.25),
                profile="2x8", material_ref="spf",
                purpose="SKUGGRONA stand 1 upper bracket; sealed spacer to stud-bay block"),
    WallBacking(uid="PLNBK0201A", tag="BK-S-PLANT-STAND-2-LOW",
                wall_ref="W-S-PS1", face="right", start=inch(96.75),
                length=inch(14.5), elevation=inch(48), height=inch(7.25),
                profile="2x8", material_ref="spf",
                purpose="SKUGGRONA stand 2 lower bracket; sealed spacer to stud-bay block"),
    WallBacking(uid="PLNBK0202A", tag="BK-S-PLANT-STAND-2-HIGH",
                wall_ref="W-S-PS1", face="right", start=inch(96.75),
                length=inch(14.5), elevation=inch(72), height=inch(7.25),
                profile="2x8", material_ref="spf",
                purpose="SKUGGRONA stand 2 upper bracket; sealed spacer to stud-bay block"),
    WallBacking(uid="PLNBK0301A", tag="BK-S-PLANT-STAND-3-LOW",
                wall_ref="W-S-PS2", face="right", start=inch(0.75),
                length=inch(14.5), elevation=inch(48), height=inch(7.25),
                profile="2x8", material_ref="spf",
                purpose="SKUGGRONA stand 3 lower bracket; sealed spacer to stud-bay block"),
    WallBacking(uid="PLNBK0302A", tag="BK-S-PLANT-STAND-3-HIGH",
                wall_ref="W-S-PS2", face="right", start=inch(0.75),
                length=inch(14.5), elevation=inch(72), height=inch(7.25),
                profile="2x8", material_ref="spf",
                purpose="SKUGGRONA stand 3 upper bracket; sealed spacer to stud-bay block"),
    WallBacking(uid="PLNBK0401A", tag="BK-S-PLANT-STAND-4-LOW",
                wall_ref="W-S-PS2", face="right", start=inch(16.75),
                length=inch(14.5), elevation=inch(48), height=inch(7.25),
                profile="2x8", material_ref="spf",
                purpose="SKUGGRONA stand 4 lower bracket; sealed spacer to stud-bay block"),
    WallBacking(uid="PLNBK0402A", tag="BK-S-PLANT-STAND-4-HIGH",
                wall_ref="W-S-PS2", face="right", start=inch(16.75),
                length=inch(14.5), elevation=inch(72), height=inch(7.25),
                profile="2x8", material_ref="spf",
                purpose="SKUGGRONA stand 4 upper bracket; sealed spacer to stud-bay block"),
]
