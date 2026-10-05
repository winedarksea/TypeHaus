# haus: editable
# RM-M-BED reading corner on W-M-W4 (west finish face x=6.635"), 2026-10-03. W4 runs N->S
# from y=156", so distance_from_start = 156" - y_centre. South to north: 1/2" cover,
# 12" SEKTION end (the backrest), two 24"
# seat units (19 1/2" top, Study 2's), 12" SEKTION end, 1/2" cover (ends y=116.63").
# The 73" seat/cabinet run centres at y=80.13", halfway between the room's finished
# south/north faces (6.635"/153.625"); moved 1.62" north on 2026-10-04. Symmetric ends.
# Cabinet tops finish at 36" (2x4 base + 30" frame + 1" walnut top), 1.70" under the
# WIN-M-BED-W1/-W2 stools (37.70"). D-M-BATH2's open leaf reaches y=124", 7.37" clear.
# Walnut tops (24 7/8" deep) run flush with the seat fronts and cap the covers, which stand
# tight to the wall and 1/4" behind the top's front edge.
# STRANDMON: rotated toward the room beside the south end cover, clear of the
# south-wall bookcase and bed, under ED-M-BED-LT.

from typehaus import Furniture, Location, Mount, MountKind, WallAttachment
from typehaus.model import Countertop, deg, inch, m, pt

BED_READING_CORNER = [
    Furniture(uid="NJW8BV7455", tag="FURN-M-BED-ARMCHAIR", type_ref="FURN-ARMCHAIR-STRANDMON",
              room="RM-M-BED", position=pt(m(1.17423), m(0.799996)), rotation=deg(120)),
    Furniture(uid="B08H9SJH2J", tag="FURN-M-BED-NOOK-COVER-S", type_ref="FT-M-BED-NOOK-COVER-30",
              room="RM-M-BED", mount=Mount(kind=MountKind.FLOOR, elevation=inch(3.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-W4", face="left", distance_from_start=inch(112.12),
                  normal_gap=inch(0), rotation_offset=deg(180)))),
    Furniture(uid="Y7F92HXTWS", tag="FURN-M-BED-NOOK-END-S", type_ref="FURN-M-BED-NOOK-END-12",
              room="RM-M-BED", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-W4", face="left", distance_from_start=inch(105.87),
                  normal_gap=inch(0), rotation_offset=deg(180)))),
    Furniture(uid="KJMYJ82SRN", tag="FURN-M-BED-NOOK-SEAT-S", type_ref="FURN-S-STUDY-NOOK-SEAT-24",
              room="RM-M-BED", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-W4", face="left", distance_from_start=inch(87.87),
                  normal_gap=inch(0), rotation_offset=deg(180)))),
    Furniture(uid="KCC06VWZYF", tag="FURN-M-BED-NOOK-SEAT-N", type_ref="FURN-S-STUDY-NOOK-SEAT-24",
              room="RM-M-BED", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-W4", face="left", distance_from_start=inch(63.87),
                  normal_gap=inch(0), rotation_offset=deg(180)))),
    Furniture(uid="F07E6N0BHW", tag="FURN-M-BED-NOOK-END-N", type_ref="FURN-M-BED-NOOK-END-12",
              room="RM-M-BED", mount=Mount(kind=MountKind.FLOOR, elevation=inch(0)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-W4", face="left", distance_from_start=inch(45.87),
                  normal_gap=inch(0), rotation_offset=deg(180)))),
    Furniture(uid="NJNFYCF99Z", tag="FURN-M-BED-NOOK-COVER-N", type_ref="FT-M-BED-NOOK-COVER-30",
              room="RM-M-BED", mount=Mount(kind=MountKind.FLOOR, elevation=inch(3.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-W4", face="left", distance_from_start=inch(39.62),
                  normal_gap=inch(0), rotation_offset=deg(180)))),
    Furniture(uid="VTNCQXD81D", tag="FURN-M-BED-NOOK-CUSHION", type_ref="FT-M-BED-NOOK-CUSHION",
              room="RM-M-BED", mount=Mount(kind=MountKind.FLOOR, elevation=inch(19.5)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-W4", face="left", distance_from_start=inch(75.87),
                  normal_gap=inch(0), rotation_offset=deg(180)))),
    Countertop(uid="VRHHG92SFT", tag="CT-M-BED-NOOK-S",
               hosts=("FURN-M-BED-NOOK-COVER-S", "FURN-M-BED-NOOK-END-S"),
               material_ref="walnut-counter", thickness=inch(1), overhang=inch(0.875),
               depth=inch(24.875)),
    Countertop(uid="55YXHKRRFA", tag="CT-M-BED-NOOK-N",
               hosts=("FURN-M-BED-NOOK-END-N", "FURN-M-BED-NOOK-COVER-N"),
               material_ref="walnut-counter", thickness=inch(1), overhang=inch(0.875),
               depth=inch(24.875)),
]
