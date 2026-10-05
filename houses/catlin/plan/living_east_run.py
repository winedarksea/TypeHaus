# haus: editable
# The living room's east wall: one SEKTION line, less the fireplace brick (2026-10-02).
# Replaced eight 16 1/2"-deep BESTA units (29 3/4" top). Types/products:
# plan/living_east_run_types.py; slabs CT-M-LIV-E-S/-N in plan/countertops.py.
#
# All on W-M-E1, rotation -90 (back on the gwb at x=35'-5 3/8"). 15"-deep SEKTION frames,
# 15 1/2" with fronts, so fronts at x=34'-1 7/8". The kitchen's 3 1/2" leg + 30" frame +
# 1/2" sub-top + 2" live-edge oak = 36", one toe-kick line down the whole wall.
#
# ** MIRRORED ABOUT THE BRICK (y=104"), 2026-10-03. ** E1 and E2 flank the brick at
# 104 -/+ 40"; each window's unit centres 1 1/4" off the window, away from the brick, and
# the fireplace-adjacent units retain that offset. The 0" joints are the end panels and fillers.
#   south  y 6 5/8"..81 1/4":  2 1/8" filler, B36, B36 (E1), 1/2" end panel to the brick
#   north  y 126 3/4"..271 1/4": 1/2" end panel, four B36; 1/8" sealed joint to the pantry
# Fillers are elements (FT-LIV-E-FILLER-*), faced to match; the slab runs straight over them.
# Six B36 with paired nominal 18" doors and shelves (2026-10-04). The former B15 + B30 +
# B15 + B12 total 72", so two B36 preserve the bank length; the retained middle B36 moves
# south to make the modules consecutive. Window centres no longer govern those joints.
#
# Stools: all four east windows share a 2'-10" sill so the frame rail, and so the stool
# top, meets the slab top (36 15/16" above the storey datum; the rail lands 1/64" proud).
# overhang=0 and horn=0, so each stool meets the slab's back edge in one plane.

from typehaus import Furniture
from typehaus.model import WindowStool, deg, ft, inch, pt

LIVING_EAST_RUN = [
    Furniture(uid="CX4TPWQTWN", tag="FURN-M-LIV-E-FILLER-S", type_ref="FT-LIV-E-FILLER-2125", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), inch(7.6875)), rotation=deg(-90)),
    Furniture(uid="X9TX2CRJYR", tag="FURN-M-LIV-E-B36-S", type_ref="SEKT-B36-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(2, 2.75)), rotation=deg(-90)),
    Furniture(uid="FS3M2DPTHF", tag="FURN-M-LIV-E-B36-E1", type_ref="SEKT-B36-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(5, 2.75)), rotation=deg(-90)),
    Furniture(uid="GAE528B6J0", tag="FURN-M-LIV-E-END-S", type_ref="FT-LIV-E-END-PANEL", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(6, 9)), rotation=deg(-90)),
    Furniture(uid="VYF21YNX09", tag="FURN-M-LIV-E-END-N", type_ref="FT-LIV-E-END-PANEL", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(10, 7)), rotation=deg(-90)),
    Furniture(uid="Y44J503GS1", tag="FURN-M-LIV-E-B36-E2", type_ref="SEKT-B36-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(12, 1.25)), rotation=deg(-90)),
    Furniture(uid="TKX5EHYSZW", tag="FURN-M-LIV-E-B36-E3", type_ref="SEKT-B36-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(15, 1.25)), rotation=deg(-90)),
    Furniture(uid="QKGYPHFV12", tag="FURN-M-LIV-E-B36-MID", type_ref="SEKT-B36-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(18, 1.25)), rotation=deg(-90)),
    Furniture(uid="WQ2SWGGP5K", tag="FURN-M-LIV-E-B36-PANTRY", type_ref="SEKT-B36-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(21, 1.25)), rotation=deg(-90)),
]

LIVING_EAST_STOOLS = [
    WindowStool(uid="Y9025C8NTZ", tag="STOOL-WIN-M-LIV-E1", window_ref="WIN-M-LIV-E1",
                material_ref="live-edge-white-oak", thickness=inch(2),
                overhang=inch(0), horn=inch(0), profile="eased"),
    WindowStool(uid="7TK2C8BGBM", tag="STOOL-WIN-M-LIV-E2", window_ref="WIN-M-LIV-E2",
                material_ref="live-edge-white-oak", thickness=inch(2),
                overhang=inch(0), horn=inch(0), profile="eased"),
    WindowStool(uid="WMLIVE3STL", tag="STOOL-WIN-M-LIV-E3", window_ref="WIN-M-LIV-E3",
                material_ref="live-edge-white-oak", thickness=inch(2),
                overhang=inch(0), horn=inch(0), profile="eased"),
    WindowStool(uid="SKCRC41TEC", tag="STOOL-WIN-M-EAST-MID", window_ref="WIN-M-EAST-MID",
                material_ref="live-edge-white-oak", thickness=inch(2),
                overhang=inch(0), horn=inch(0), profile="eased"),
]
