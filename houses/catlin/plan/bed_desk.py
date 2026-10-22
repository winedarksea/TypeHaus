# haus: editable
# RM-M-BED desk in the southeast corner, backs on the east finish face (x=212.115"),
# 2026-10-21. South to north: a 15" SEKTION drawer base, a 31" knee bay on a hidden
# ledger, a second base: 61" over y=7.25"..68.25", the HEMNES footprint it replaces.
# One 1" walnut glue-up top spans all three at 31". 12 3/4" from the north end to
# D-M-BED2's hinge jamb; the chair zone stays south of the king's foot (y=68.445").
# Types in `bed_desk_types.py`.

from typehaus import Furniture, Mount, MountKind
from typehaus.model import Countertop, deg, inch, m, pt

BED_DESK = [
    Furniture(uid="ASP214N8HR", tag="FURN-M-BED-DESK-CAB-S", type_ref="FURN-M-BED-DESK-DRAWERS-15",
              room="RM-M-BED", position=pt(inch(199.74), inch(14.75)), rotation=deg(-90)),
    # The knee bay's ledger keeps the desk's tag and uid: it carries the chair zone.
    Furniture(uid="CMD701AAAA", tag="FURN-M-BED-DESK", type_ref="FT-M-BED-DESK-LEDGER-31",
              room="RM-M-BED", mount=Mount(kind=MountKind.FLOOR, elevation=inch(27.5)),
              position=pt(inch(211.74), inch(37.75)), rotation=deg(-90)),
    Furniture(uid="P4W7XCY102", tag="FURN-M-BED-DESK-CAB-N", type_ref="FURN-M-BED-DESK-DRAWERS-15",
              room="RM-M-BED", position=pt(inch(199.74), inch(60.75)), rotation=deg(-90)),
    Countertop(uid="Z1TG1TK4K3", tag="CT-M-BED-DESK",
               hosts=("FURN-M-BED-DESK-CAB-S", "FURN-M-BED-DESK", "FURN-M-BED-DESK-CAB-N"),
               material_ref="walnut-counter", thickness=inch(1), overhang=inch(0.875),
               depth=inch(24.875)),
    # Its chair faces east, tucked into the knee and inside the ledger's chair zone.
    Furniture(uid="PJSHPJN6TV", tag="FURN-M-BED-DESK-CHAIR", type_ref="FURN-DESK-CHAIR",
              room="RM-M-BED", position=pt(m(4.80049), m(0.954962)), rotation=deg(90)),
]
