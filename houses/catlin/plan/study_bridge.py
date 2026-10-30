# haus: editable
# One owner-stock oak infill between the study door's east casing leg and the fixed
# bookcase, in the casing's plane on W-A-SN's study face. notes/study_bookcase_bridge.md.

from typehaus import Furniture, FurnitureType
from typehaus.model import inch, pt

INFILL_WIDTH = inch(6.5)
BOARD_THICKNESS = inch(0.75)
INFILL_HEIGHT = inch(60)

# Envelope: x=262 7/8..269 3/8", y=105..105.75" (the finish face; paint takes no depth, over the
# 1/2" board); butts CASING-D-A-STUDY-R's east leg in its plane.
INFILL_POSITION = pt(inch(266.125), inch(105.375))

INFILL_SOURCE = """Owner-stock 4/4 oak dressed to 3/4 in.; match the oak-trim casing finish.
Infill 6 1/2 x 60 x 3/4 in. on W-A-SN's study face, butted to the east casing leg in its plane.
Fasten to partition backing and glue/biscuit to the leg; scribe the east edge to the filler.
Cut list and fabrication/install allowance: notes/study_bookcase_bridge.md."""

INFILL = FurnitureType(
    tag="FT-A-STUDY-BRIDGE-FRONT", name='Study oak casing infill, 6 1/2 x 60 x 3/4"',
    footprint=(INFILL_WIDTH, BOARD_THICKNESS), height=INFILL_HEIGHT,
    storage=False, work_surface=False, plan_symbol="closet-board",
    wood_material_ref="oak-trim", source=INFILL_SOURCE,
)

STUDY_BRIDGE_TYPES = (INFILL,)

# SX3RBRDG02..04 (the former returns and cap) are retired; never reuse them.
STUDY_BRIDGE = [
    Furniture(uid="SX3RBRDG01", tag="FURN-A-STUDY-BRIDGE-FRONT",
              type_ref="FT-A-STUDY-BRIDGE-FRONT", room="RM-A-STUDY",
              position=INFILL_POSITION),
]
