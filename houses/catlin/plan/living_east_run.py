# haus: editable
# The living room's east wall: one SEKTION line, less the fireplace brick (2026-10-02).
# Replaced eight 16 1/2"-deep BESTA units (29 3/4" top). Types/products:
# plan/living_east_run_types.py; slabs CT-M-LIV-E-S/-N in plan/countertops.py.
#
# All on W-M-E1, rotation -90 (back on the gwb at x=35'-5 3/8"). 15"-deep SEKTION frames,
# 15 1/2" with fronts, so fronts at x=34'-1 7/8". The kitchen's 3 1/2" leg + 30" frame +
# 1/2" sub-top + 2" live-edge oak = 36", one toe-kick line down the whole wall.
#
# ** KEYED TO THE WINDOWS, MIRRORED ABOUT THE BRICK (y=104"). ** The B30s centre 1/4" off
# WIN-M-LIV-E1/-E2 at 104 -/+ 56 1/4"; the B18s flank the brick at 104 -/+ 32 1/4". The B36
# centres 3/4" off WIN-M-EAST-MID. A plain 2xB36 split put a joint 3 1/4" off E1's centre,
# which reads as a mistake under counter-height glass. Eight units (BESTA was eight).
#   south  y 6 5/8"..81 1/4":  2 1/8" scribe, B24, B30, B18, 1/2" end panel to the brick
#   north  y 126 3/4"..259 3/4": 1/2" end panel, B18, B30, B30, B36, B18, 1/2" scribe
# Fillers are gaps, the kitchen's idiom: under 3", the slab is cut straight across them.
# MAXIMERA drawers in every unit. The 0" gaps to the brick are hand-measured; nothing grades
# two bodies in one volume.
#
# Stools: the three east windows' sills rose to 2'-10" so the frame rail, and so the stool
# top, meets the slab top (36 15/16" above the storey datum; the rail lands 1/64" proud).
# overhang=0 and horn=0, so each stool meets the slab's back edge in one plane.

from typehaus import Furniture
from typehaus.model import WindowStool, deg, ft, inch, pt

LIVING_EAST_RUN = [
    Furniture(uid="X9TX2CRJYR", tag="FURN-M-LIV-E-B24-S", type_ref="SEKT-B24-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(1, 8.75)), rotation=deg(-90)),
    Furniture(uid="FS3M2DPTHF", tag="FURN-M-LIV-E-B30-E1", type_ref="SEKT-B30-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(3, 11.75)), rotation=deg(-90)),
    Furniture(uid="6DF1QVWE9H", tag="FURN-M-LIV-E-B18-S", type_ref="SEKT-B18-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(5, 11.75)), rotation=deg(-90)),
    Furniture(uid="GAE528B6J0", tag="FURN-M-LIV-E-END-S", type_ref="FT-LIV-E-END-PANEL", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(6, 9)), rotation=deg(-90)),
    Furniture(uid="VYF21YNX09", tag="FURN-M-LIV-E-END-N", type_ref="FT-LIV-E-END-PANEL", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(10, 7)), rotation=deg(-90)),
    Furniture(uid="Y44J503GS1", tag="FURN-M-LIV-E-B18-N", type_ref="SEKT-B18-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(11, 4.25)), rotation=deg(-90)),
    Furniture(uid="P7S6W1H6EP", tag="FURN-M-LIV-E-B30-E2", type_ref="SEKT-B30-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(13, 4.25)), rotation=deg(-90)),
    # The pier unit between E2 and EAST-MID: the only wall the north bank's receptacles get.
    Furniture(uid="TKX5EHYSZW", tag="FURN-M-LIV-E-B30-PIER", type_ref="SEKT-B30-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(15, 10.25)), rotation=deg(-90)),
    Furniture(uid="15FPP4DBD8", tag="FURN-M-LIV-E-B36-MID", type_ref="SEKT-B36-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(18, 7.25)), rotation=deg(-90)),
    Furniture(uid="QKGYPHFV12", tag="FURN-M-LIV-E-B18-PAN", type_ref="SEKT-B18-D15", room="RM-M-LIVING",
              position=pt(ft(34, 9.625), ft(20, 10.25)), rotation=deg(-90)),
]

LIVING_EAST_STOOLS = [
    WindowStool(uid="Y9025C8NTZ", tag="STOOL-WIN-M-LIV-E1", window_ref="WIN-M-LIV-E1",
                material_ref="live-edge-white-oak", thickness=inch(2),
                overhang=inch(0), horn=inch(0), profile="S4S"),
    WindowStool(uid="7TK2C8BGBM", tag="STOOL-WIN-M-LIV-E2", window_ref="WIN-M-LIV-E2",
                material_ref="live-edge-white-oak", thickness=inch(2),
                overhang=inch(0), horn=inch(0), profile="S4S"),
    WindowStool(uid="SKCRC41TEC", tag="STOOL-WIN-M-EAST-MID", window_ref="WIN-M-EAST-MID",
                material_ref="live-edge-white-oak", thickness=inch(2),
                overhang=inch(0), horn=inch(0), profile="S4S"),
]
