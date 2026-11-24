# haus: editable
# Plug-in lamps (lighting review, 2026-11-23): each on a plain receptacle within its cord,
# switched at the lamp. They take the task light the ceiling no longer chases: reading by a
# seat or a bed, a desk, the lounge's puzzle table (day, 5000 K) and the dining night light.
# A desk or table lamp stands on its surface (mount elevation = the top it sits on); a wall
# reading lamp hangs at 44" on the wall the retired bed reading switch used. A lamp's front
# is local -y: a floor lamp's shade aims at its seat; a desk lamp clamps the desk's back edge
# (or its end, where the desk is shallower than the arm) and reaches toward the sitter.
# Types: plan/lamp_types.py.

from typehaus import Furniture, Location, Mount, MountKind, WallAttachment, deg, ft, inch, pt

MAIN_LAMPS = [
    # Lounge seated reading, beside the sofa ends and the armchairs.
    Furniture(uid="48VAND43CM", tag="LAMP-M-LIV-SOFA-S", type_ref="FT-LAMP-FLOOR-HEKTAR", room="RM-M-LIVING",
              position=pt(ft(22, 7.2), ft(2, 11.2)), rotation=deg(150)),
    Furniture(uid="Z0M4JMMCP1", tag="LAMP-M-LIV-SOFA-N", type_ref="FT-LAMP-FLOOR-HEKTAR", room="RM-M-LIVING",
              position=pt(ft(22, 7.2), ft(11, 9.2)), rotation=deg(30)),
    Furniture(uid="ZYM36V8F38", tag="LAMP-M-LIV-ARM-S", type_ref="FT-LAMP-FLOOR-HEKTAR", room="RM-M-LIVING",
              position=pt(ft(29, 8.4), ft(2, 3.6)), rotation=deg(125)),
    Furniture(uid="1X40940BMV", tag="LAMP-M-LIV-ARM-N", type_ref="FT-LAMP-FLOOR-HEKTAR", room="RM-M-LIVING",
              position=pt(ft(34, 4.8), ft(11, 11.4)), rotation=deg(-60)),
    # The puzzle table's day light (5000 K) since its ceiling cans joined the north row;
    # fed from the floor box ED-M-LIVING-FLOOR-RC1 under the table.
    Furniture(uid="4Q6J4VN2QZ", tag="LAMP-M-LIV-PUZZLE", type_ref="FT-LAMP-DESK-TERTIAL-5000",
              room="RM-M-LIVING", position=pt(ft(27, 5.9), ft(7, 3.6)), rotation=deg(-90),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(19.33))),
    # Dining night layer: a warm globe on the east counter (CT-M-LIV-E-N, top 39").
    Furniture(uid="NE0P3RTQ4Y", tag="LAMP-M-DIN-COUNTER", type_ref="FT-LAMP-TABLE-FADO", room="RM-M-LIVING",
              position=pt(ft(34, 8.4), ft(17, 9.6)),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(39))),
    # Behind the STRANDMON's shoulder: the chair's reading light (its can is retired).
    Furniture(uid="630049BESP", tag="LAMP-M-BED-ARMCHAIR", type_ref="FT-LAMP-FLOOR-HEKTAR", room="RM-M-BED",
              position=pt(ft(1, 10.8), ft(4, 10.8)), rotation=deg(30)),
    # The study's night layer: warm, low, switched at the lamp.
    Furniture(uid="E9W7050T5J", tag="LAMP-M-STUDY-DESK", type_ref="FT-LAMP-DESK-TERTIAL",
              room="RM-M-STUDY-CLOSET", position=pt(ft(14, 7), ft(18, 8.4)), rotation=deg(90),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(30.53))),
]

SECOND_LAMPS = [
    # Bed-head reading lamps, on the walls and stations the bed switches used.
    Furniture(uid="S3VNCXR075", tag="LAMP-S-BED1-READ", type_ref="FT-LAMP-WALL-NYMANE", room="RM-S-BED1",
              mount=Mount(kind=MountKind.WALL, elevation=inch(44)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-SS2", face="left", distance_from_start=inch(145),
                  normal_gap=inch(0), rotation_offset=deg(180)))),
    Furniture(uid="D1VN1ANAJQ", tag="LAMP-S-BED2-READ-E", type_ref="FT-LAMP-WALL-NYMANE", room="RM-S-BED2",
              mount=Mount(kind=MountKind.WALL, elevation=inch(44)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BD2", face="right", distance_from_start=inch(148.75),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="H8JXAZKPMM", tag="LAMP-S-BED2-READ-W", type_ref="FT-LAMP-WALL-NYMANE", room="RM-S-BED2",
              mount=Mount(kind=MountKind.WALL, elevation=inch(44)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-BD2", face="right", distance_from_start=inch(115.25),
                  normal_gap=inch(0), rotation_offset=deg(0)))),
    Furniture(uid="SK54B6BSJQ", tag="LAMP-S-BED3-READ", type_ref="FT-LAMP-WALL-NYMANE", room="RM-S-BED3",
              mount=Mount(kind=MountKind.WALL, elevation=inch(44)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-S-E4", face="left", distance_from_start=inch(59.25),
                  normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Desk lamps, clamped to each desk.
    Furniture(uid="BHQ74A3RNN", tag="LAMP-S-BED1-DESK", type_ref="FT-LAMP-DESK-TERTIAL", room="RM-S-BED1",
              position=pt(ft(34, 7.2), ft(13, 7.2)), rotation=deg(-90),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(31.75))),
    Furniture(uid="SJJ8RG8RN0", tag="LAMP-S-BED2-DESK", type_ref="FT-LAMP-DESK-TERTIAL", room="RM-S-BED2",
              position=pt(ft(28, 9.6), ft(25, 7.3)),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(31.75))),
    Furniture(uid="HK0XJYPS4S", tag="LAMP-S-BED3-DESK", type_ref="FT-LAMP-DESK-TERTIAL", room="RM-S-BED3",
              position=pt(ft(22, 11.3), ft(34, 9.6)), rotation=deg(90),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(31.75))),
    Furniture(uid="HQ1S2NY4T0", tag="LAMP-S-SUITE-DESK", type_ref="FT-LAMP-DESK-TERTIAL", room="RM-S-SUITE",
              position=pt(ft(1), ft(10, 0.3)), rotation=deg(180),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(31.5))),
    Furniture(uid="YR83SZAZ84", tag="LAMP-S-STUDY2-DESK", type_ref="FT-LAMP-DESK-TERTIAL", room="RM-S-STUDY2",
              position=pt(ft(28, 3.6), ft(1, 4.4)), rotation=deg(180),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(29))),
]

ATTIC_LAMPS = [
    # The study reads short by plan: its desk lamp is the task light.
    Furniture(uid="MM7RSXBVZF", tag="LAMP-A-STUDY-DESK", type_ref="FT-LAMP-DESK-TERTIAL", room="RM-A-STUDY",
              position=pt(ft(19, 2.2), ft(4)), rotation=deg(90),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(31.5))),
    # The studio's sloped ceiling takes no cans: two floor lamps on the centre-wall line.
    Furniture(uid="W2MXZGTG8H", tag="LAMP-A-STUDIO-FLOOR-S", type_ref="FT-LAMP-FLOOR-HEKTAR", room="RM-A-STUDIO",
              position=pt(ft(16, 6), ft(3, 2.4)), rotation=deg(-130)),
    Furniture(uid="1VMAGVZN2V", tag="LAMP-A-STUDIO-FLOOR-N", type_ref="FT-LAMP-FLOOR-HEKTAR", room="RM-A-STUDIO",
              position=pt(ft(16, 6), ft(12, 4.8)), rotation=deg(-75)),
]
