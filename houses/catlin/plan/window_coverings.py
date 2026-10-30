# haus: editable
# Curtain tracks and cellular shades (2026-10-29). Types in plan/window_covering_types.py;
# the seal rule, clearances and products in notes/window_coverings.md.
#
# Every closed curtain edge ends against a wall: in a room corner, in a VIDGA end-closing
# curve back to the wall, or at a centre overlap. Ceiling runs seal the top. Envelopes are
# the CLOSED curtain from a 1/2" floor kiss (Mount.elevation is off the room's finished
# floor) to the ceiling, 6" deep with the back on the finish face (y/x 6.51"); the rail
# runs 3" off the wall. The ceiling runs screw into a joist: FS-S-EAST's and FS-ATTIC's
# extra line at y 9 1/2", and FS-S-WEST's trusses crossing the bedroom run at 16".
#
# Shades are inside mount at the opening (the FURN-M-LIV-BLIND-* idiom): sill AFF and the
# window's centre station.

from typehaus import Furniture, Location, Mount, MountKind, WallAttachment
from typehaus.model import deg, inch, pt

MAIN_WINDOW_COVERINGS = [
    # Living south, WIN-M-LIV-S2/-S1: x 301" (end-closing curve) to 425 1/4" (SE corner).
    Furniture(uid="BZJF36KH8Q", tag="FURN-M-LIV-TRACK-S", type_ref="FT-CURTAIN-TRACK-LIV-S", room="RM-M-LIVING",
              position=pt(inch(363.125), inch(9.5625)), rotation=deg(180),
              mount=Mount(kind=MountKind.CEILING, elevation=inch(0.5))),
    # D-M-BALC: wall run, rail top 88" AFF under EQ-M-HP2-LIVING, x 219 1/2"..291".
    # The door swings out, so the split stacks sit either side of it.
    Furniture(uid="WJTG6V6T09", tag="FURN-M-LIV-TRACK-BALC", type_ref="FT-CURTAIN-TRACK-LIV-BALC",
              room="RM-M-LIVING",
              mount=Mount(kind=MountKind.WALL, elevation=inch(0.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-S2", face="left", distance_from_start=inch(39.25),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Bedroom west, WIN-M-BED-W1/-W2: SW corner to NW corner.
    Furniture(uid="SR87WAPT5T", tag="FURN-M-BED-TRACK-W", type_ref="FT-CURTAIN-TRACK-BED-W", room="RM-M-BED",
              position=pt(inch(9.5625), inch(80.125)), rotation=deg(90),
              mount=Mount(kind=MountKind.CEILING, elevation=inch(0.5))),
    # WIN-M-BED-S1/-S2: cordless. S2 has EQ-M-HP2-BED over it; S1 would need an extra truss.
    Furniture(uid="X3SXCVEE19", tag="FURN-M-BED-BLIND-S1", type_ref="FT-CELLULAR-SHADE-3048-CORDLESS",
              room="RM-M-BED",
              mount=Mount(kind=MountKind.WALL, elevation=inch(30.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-S1", face="left", distance_from_start=inch(48),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="976HP4VWK0", tag="FURN-M-BED-BLIND-S2", type_ref="FT-CELLULAR-SHADE-3048-CORDLESS",
              room="RM-M-BED",
              mount=Mount(kind=MountKind.WALL, elevation=inch(30.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-S1", face="left", distance_from_start=inch(176),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
]

SECOND_WINDOW_COVERINGS = [
    # D-S-DECK-E: x 219 1/2" (corner) to 291" (end-closing), one panel stacking west.
    Furniture(uid="H99NTV3GRV", tag="FURN-S-STUDY-TRACK-DECK", type_ref="FT-CURTAIN-TRACK-STUDY-DECK",
              room="RM-S-STUDY2",
              position=pt(inch(255.25), inch(9.5625)), rotation=deg(180),
              mount=Mount(kind=MountKind.CEILING, elevation=inch(0.5))),
    # Motorized: WIN-S-STUDY1/-2 (south), WIN-S-STUDY3 (east, 36" sill).
    Furniture(uid="NM0D2S1S3R", tag="FURN-S-STUDY2-SHADE-S1", type_ref="FT-CELLULAR-SHADE-3048-MOTOR",
              room="RM-S-STUDY2",
              mount=Mount(kind=MountKind.WALL, elevation=inch(30.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-S2", face="left", distance_from_start=inch(104),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="QJ8G5PG4YK", tag="FURN-S-STUDY2-SHADE-S2", type_ref="FT-CELLULAR-SHADE-3048-MOTOR",
              room="RM-S-STUDY2",
              mount=Mount(kind=MountKind.WALL, elevation=inch(30.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-S2", face="left", distance_from_start=inch(168),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="BZK9V8GDDD", tag="FURN-S-STUDY2-SHADE-E", type_ref="FT-CELLULAR-SHADE-2748-MOTOR",
              room="RM-S-STUDY2",
              mount=Mount(kind=MountKind.WALL, elevation=inch(34.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-E1", face="left", distance_from_start=inch(64),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
]

ATTIC_WINDOW_COVERINGS = [
    # WIN-A-S-JUL-E motorized; WIN-A-S3 cordless (14" is under the motor's minimum).
    Furniture(uid="CRS8FD8CFD", tag="FURN-A-STUDY-SHADE-JUL-E", type_ref="FT-CELLULAR-SHADE-2754-MOTOR",
              room="RM-A-STUDY",
              mount=Mount(kind=MountKind.WALL, elevation=inch(30.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-A-S3", face="left", distance_from_start=inch(24),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="N4CVFTG3G2", tag="FURN-A-STUDY-SHADE-S3", type_ref="FT-CELLULAR-SHADE-1424-CORDLESS",
              room="RM-A-STUDY",
              mount=Mount(kind=MountKind.WALL, elevation=inch(30.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-A-S3", face="left", distance_from_start=inch(80),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
]
