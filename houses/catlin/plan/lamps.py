# haus: editable
# Plug-in lamps (lighting review, 2026-11-23): each on a plain receptacle within its cord,
# switched at the lamp. They take the task light the ceiling does not: a desk, the attic
# studio's sloped ceiling, and the dining night light. The lounge floor lamps, its puzzle-table
# lamp, the main-bed armchair lamp, the main study's desk lamp and the second-floor NYMÅNE
# bed-head lamps left on 2026-11-24 (owner: no floor-lamp clutter, ceiling day cans over the
# puzzle table, beds get rearranged). A desk or table lamp stands on its surface (mount
# elevation = the top it sits on). A lamp's front is local -y: a floor lamp's shade aims at its
# seat; a desk lamp clamps the desk's back edge (or its end, where the desk is shallower than
# the arm) and reaches toward the sitter. Types: plan/lamp_types.py.

from typehaus import Furniture, Mount, MountKind, deg, ft, inch, pt

MAIN_LAMPS = [
    # Dining night layer: a warm globe on the east counter (CT-M-LIV-E-N, top 39").
    Furniture(uid="NE0P3RTQ4Y", tag="LAMP-M-DIN-COUNTER", type_ref="FT-LAMP-TABLE-FADO", room="RM-M-LIVING",
              position=pt(ft(34, 8.4), ft(17, 9.6)),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(39))),
]

SECOND_LAMPS = [
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
