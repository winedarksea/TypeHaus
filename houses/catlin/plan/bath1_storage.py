# haus: editable
# Three SEKTION 24x24x90 frames, south wall of RM-S-BATH1. Owner, 2026-10-02: WC stays
# at y=363 1/2"; west and centre lower 30" are OPEN shelves, with no doors or drawers.
# Their one drawer starts at 34 1/2" AFF, above the WC's 29 1/8" top. East has three drawers.
# All units have 30+20" VOXTORP upper doors and a 4 1/2" plinth; installed top is 94 1/2".
# South face y=321.385", fronts y=346.260"; x=7 1/8"..79 1/8" plus the 1/2" east cover.
# The rail crosses W-S-BD-N / -N1B at x=70 1/2"; plan/backing.py backs both segments.

from typehaus import Furniture, Location, Mount, MountKind, WallAttachment
from typehaus.model import deg, inch

BATH1_STORAGE = [
    Furniture(uid="CSB707AAAA", tag="FURN-S-BATH1-CLOSET", type_ref="FURN-S-SEKTION-LINEN-OPEN-24",
              room="RM-S-BATH1", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BD-N", face="left", distance_from_start=inch(19.125),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="H1BAWZB2RJ", tag="FURN-S-BATH1-CLOSET-C", type_ref="FURN-S-SEKTION-LINEN-OPEN-24",
              room="RM-S-BATH1", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BD-N", face="left", distance_from_start=inch(43.125),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="EF02W2YB4J", tag="FURN-S-BATH1-CLOSET-E", type_ref="FURN-S-SEKTION-LINEN-DRAWER-24",
              room="RM-S-BATH1", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BD-N", face="left", distance_from_start=inch(67.125),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    Furniture(uid="BK2YQQT8GB", tag="FURN-S-BATH1-CLOSET-COVER", type_ref="FT-S-SEKTION-COVER-90",
              room="RM-S-BATH1", mount=Mount(kind=MountKind.FLOOR, elevation=inch(4.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BD-N1B", face="left", distance_from_start=inch(8.875),
                  normal_gap=inch(0.25), rotation_offset=deg(-180)))),
    Furniture(uid="K2608V384Q", tag="FURN-S-BATH1-CLOSET-SCRIBE", type_ref="FT-S-SEKTION-SCRIBE-90",
              room="RM-S-BATH1", mount=Mount(kind=MountKind.FLOOR, elevation=inch(4.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BD-N", face="left", distance_from_start=inch(6.9375),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
]
