# haus: editable
# The living room's east wall: storage on the dining side only (2026-10-20). Types/products:
# plan/living_east_run_types.py; slab CT-M-LIV-E-N in plan/countertops.py.
#
# All on W-M-E1, rotation -90 (back on the gwb at x=35'-5 3/8"). 24"-deep stock SEKTION,
# body centres x=34'-5 3/8", fronts flush with FURN-M-KIT-PANTRY-S2. The kitchen's 3 1/2" leg
# + 30" frame + 1 1/4" sub-top + 1 1/4" ash slab = 36", one toe-kick line down the wall.
#
# South of the slat partition is open wall: no bank, no counter. North of it, no fillers:
#   y 156 3/4"..271 1/4": 1/2" end panel, B24, B36, B36, B18, then the 1/8" sealed joint to S2.
# Hang the B24's door on its NORTH edge so it opens away from the slats.
#
# Stools: E1/E2 meet no slab now, so they take the house standard 3/4" overhang and 1" horn
# (plan/window_stools.py). WIN-M-DINING-E still meets the slab's back edge in one plane.
# White ash, 1 1/4" off 6/4 (ash-stool-6q), the slab's own thickness and species.
#
# ** THE ELM SLAT PARTITION (2026-10-16; one piece since 2026-10-20). ** Floor to ceiling,
# centred y=12'-11 1/2" (154 1/4"..156 3/4") so it still covers the LVP/coated-concrete
# joint at 13'-0", running 60 1/2" west from the gwb. Types and fixing:
# plan/living_east_run_types.py.

from typehaus import Furniture
from typehaus.model import WindowStool, deg, inch, pt

LIVING_EAST_RUN = [
    Furniture(uid="VYF21YNX09", tag="FURN-M-LIV-E-END-N", type_ref="FT-LIV-E-END-PANEL", room="RM-M-LIVING",
              position=pt(inch(413.375), inch(157)), rotation=deg(-90)),
    Furniture(uid="TKX5EHYSZW", tag="FURN-M-LIV-E-B24", type_ref="SEKT-B24", room="RM-M-LIVING",
              position=pt(inch(413.375), inch(169.25)), rotation=deg(-90)),
    Furniture(uid="QKGYPHFV12", tag="FURN-M-LIV-E-B36-MID", type_ref="SEKT-B36", room="RM-M-LIVING",
              position=pt(inch(413.375), inch(199.25)), rotation=deg(-90)),
    Furniture(uid="WQ2SWGGP5K", tag="FURN-M-LIV-E-B36-PANTRY", type_ref="SEKT-B36", room="RM-M-LIVING",
              position=pt(inch(413.375), inch(235.25)), rotation=deg(-90)),
    Furniture(uid="TA461J20Q0", tag="FURN-M-LIV-E-B18-N", type_ref="SEKT-B18", room="RM-M-LIVING",
              position=pt(inch(413.375), inch(262.25)), rotation=deg(-90)),
    # The slat partition, centred 30 1/4" off the gwb face.
    Furniture(uid="7ES588S8KP", tag="FURN-M-LIV-SLAT-FULL", type_ref="FT-LIV-SLAT-ELM-FULL",
              room="RM-M-LIVING", position=pt(inch(395.125), inch(155.5)), rotation=deg(0)),
]

LIVING_EAST_STOOLS = [
    WindowStool(uid="Y9025C8NTZ", tag="STOOL-WIN-M-LIV-E1", window_ref="WIN-M-LIV-E1",
                material_ref="ash-stool-6q", thickness=inch(1.25),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="7TK2C8BGBM", tag="STOOL-WIN-M-LIV-E2", window_ref="WIN-M-LIV-E2",
                material_ref="ash-stool-6q", thickness=inch(1.25),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="7209APS8G4", tag="STOOL-WIN-M-DINING-E", window_ref="WIN-M-DINING-E",
                material_ref="ash-stool-6q", thickness=inch(1.25),
                overhang=inch(0), horn=inch(0), profile="eased"),
]
