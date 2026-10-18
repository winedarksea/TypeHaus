# haus: editable
# The living room's east wall: one SEKTION line, less the fireplace brick (2026-10-02).
# Replaced eight 16 1/2"-deep BESTA units (29 3/4" top). Types/products:
# plan/living_east_run_types.py; slabs CT-M-LIV-E-S/-N in plan/countertops.py.
#
# All on W-M-E1, rotation -90 (back on the gwb at x=35'-5 3/8"). 15"-deep SEKTION frames,
# 15 1/2" with fronts, so fronts at x=34'-1 7/8". The kitchen's 3 1/2" leg + 30" frame +
# 1 1/4" sub-top (3/4" + 1/2" ply) + 1 1/4" ash slab = 36", one toe-kick line down the wall.
#
# ** RE-BANKED ROUND THE BRICK AT y=88" (2026-10-16). ** The fireplace and E1/E2 moved 16"
# south; each window's B36 centres 1 1/4" off it, away from the brick. Joints are 0":
#   south  y 6 5/8"..65 1/4":  4 1/8" filler, B18, B36 (E1), 1/2" end panel to the brick
#   north  y 110 3/4"..271 1/4": 1/2" end panel, B36 (E2), three B36, B15, 1" filler;
#          then the 1/8" sealed joint to the pantry
# Fillers are elements (FT-LIV-E-FILLER-*), faced to match; the slab runs straight over them.
#
# Stools: E1, E2 and WIN-M-DINING-E share a 2'-10" sill so the frame rail, and so the stool
# top, meets the slab top (36 15/16" above the storey datum; the rail lands 1/64" proud).
# overhang=0 and horn=0, so each stool meets the slab's back edge in one plane.
# White ash, 1 1/4" off 6/4 (ash-stool-6q), quarter or rift (the slab is flat-sawn off the
# same logs), urethane: the slab's own thickness and species, so stool and counter read as one board. Black cherry at 2" before.
#
# ** THE ELM SLAT PARTITION (2026-10-16, Oksana's request). ** Floor to ceiling at y=13'-0",
# over the flush LVP/coated-concrete joint, running 60 1/2" west from the gwb: a 16 1/2"
# piece standing on the counter's full depth, then a 44" piece on the floor. Both are whole
# 2 3/4" pitches, so the slats keep one rhythm across the joint. Types and fixing:
# plan/living_east_run_types.py.

from typehaus import Furniture, Mount, MountKind
from typehaus.model import WindowStool, deg, ft, inch, pt

LIVING_EAST_RUN = [
    Furniture(uid="CX4TPWQTWN", tag="FURN-M-LIV-E-FILLER-S", type_ref="FT-LIV-E-FILLER-4125", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), inch(8.6875)), rotation=deg(-90)),
    Furniture(uid="HNPX20V3CE", tag="FURN-M-LIV-E-B18-S", type_ref="SEKT-B18-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(1, 7.75)), rotation=deg(-90)),
    Furniture(uid="FS3M2DPTHF", tag="FURN-M-LIV-E-B36-E1", type_ref="SEKT-B36-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(3, 10.75)), rotation=deg(-90)),
    Furniture(uid="GAE528B6J0", tag="FURN-M-LIV-E-END-S", type_ref="FT-LIV-E-END-PANEL", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(5, 5)), rotation=deg(-90)),
    Furniture(uid="VYF21YNX09", tag="FURN-M-LIV-E-END-N", type_ref="FT-LIV-E-END-PANEL", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(9, 3)), rotation=deg(-90)),
    Furniture(uid="Y44J503GS1", tag="FURN-M-LIV-E-B36-E2", type_ref="SEKT-B36-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(10, 9.25)), rotation=deg(-90)),
    Furniture(uid="TKX5EHYSZW", tag="FURN-M-LIV-E-B36-E3", type_ref="SEKT-B36-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(13, 9.25)), rotation=deg(-90)),
    Furniture(uid="QKGYPHFV12", tag="FURN-M-LIV-E-B36-MID", type_ref="SEKT-B36-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(16, 9.25)), rotation=deg(-90)),
    Furniture(uid="WQ2SWGGP5K", tag="FURN-M-LIV-E-B36-PANTRY", type_ref="SEKT-B36-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(19, 9.25)), rotation=deg(-90)),
    Furniture(uid="TA461J20Q0", tag="FURN-M-LIV-E-B15-N", type_ref="SEKT-B15-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(21, 10.75)), rotation=deg(-90)),
    Furniture(uid="RM02NX344E", tag="FURN-M-LIV-E-FILLER-N", type_ref="FT-LIV-E-FILLER-1", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(22, 6.75)), rotation=deg(-90)),
    # The slat partition. Centres: counter piece x=34'-9 1/8" (gwb face less 8 1/4"), its
    # base the counter top, 36" AFF; floor piece x=32'-2 7/8" (less 16 1/2" and 22").
    Furniture(uid="FSHNPD0260", tag="FURN-M-LIV-SLAT-COUNTER", type_ref="FT-LIV-SLAT-ELM-COUNTER",
              room="RM-M-LIVING", position=pt(inch(417.125), ft(13)), rotation=deg(0),
              mount=Mount(kind=MountKind.FLOOR, elevation=inch(36))),
    Furniture(uid="7ES588S8KP", tag="FURN-M-LIV-SLAT-FULL", type_ref="FT-LIV-SLAT-ELM-FULL",
              room="RM-M-LIVING", position=pt(inch(386.875), ft(13)), rotation=deg(0)),
]

LIVING_EAST_STOOLS = [
    WindowStool(uid="Y9025C8NTZ", tag="STOOL-WIN-M-LIV-E1", window_ref="WIN-M-LIV-E1",
                material_ref="ash-stool-6q", thickness=inch(1.25),
                overhang=inch(0), horn=inch(0), profile="eased"),
    WindowStool(uid="7TK2C8BGBM", tag="STOOL-WIN-M-LIV-E2", window_ref="WIN-M-LIV-E2",
                material_ref="ash-stool-6q", thickness=inch(1.25),
                overhang=inch(0), horn=inch(0), profile="eased"),
    WindowStool(uid="7209APS8G4", tag="STOOL-WIN-M-DINING-E", window_ref="WIN-M-DINING-E",
                material_ref="ash-stool-6q", thickness=inch(1.25),
                overhang=inch(0), horn=inch(0), profile="eased"),
]
