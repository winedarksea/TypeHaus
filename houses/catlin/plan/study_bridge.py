# haus: editable
# Four owner-stock oak boards bridging the study door's casing to the fixed bookcase.
# The open back lands on stationary backing and filler, preserving the purchased casing
# and pivot hardware. Field-fit after hanging the door; notes/study_bookcase_bridge.md.

from typehaus import Furniture, FurnitureType, Mount, MountKind
from typehaus.model import inch, pt

BOARD_THICKNESS = inch(0.75)
BRIDGE_HEIGHT = inch(60)
FRONT_WIDTH = inch(5.5)
RETURN_DEPTH = inch(5.125)
CAP_WIDTH = inch(4)
CAP_BOTTOM_ELEVATION = inch(59.25)

# Explicit centers keep this fitted joinery writable through the editable plan dialect.
# Envelope: x=263 7/8..269 3/8", y=99 3/4..105 5/8"; 1/8" off the door casing.
FRONT_POSITION = pt(inch(266.625), inch(100.125))
WEST_RETURN_POSITION = pt(inch(264.25), inch(103.0625))
EAST_RETURN_POSITION = pt(inch(269), inch(103.0625))
CAP_POSITION = pt(inch(266.625), inch(103.0625))

BRIDGE_SOURCE = """Owner-stock 4/4 oak dressed to 3/4 in.; match oak-trim and adjacent finish.
Stationary open-backed cover, 5 1/2 x 5 7/8 x 60 in., 1/8 in. off D-A-STUDY casing.
Fasten to partition backing and fixed filler, never the moving door.
Field-fit after hanging and adjusting the factory unit; exact pivot sweep is not modeled.
Cut list and fabrication/install allowance: notes/study_bookcase_bridge.md."""

BRIDGE_FRONT = FurnitureType(
    tag="FT-A-STUDY-BRIDGE-FRONT", name='Study oak bridge front, 5 1/2 x 60 x 3/4"',
    footprint=(FRONT_WIDTH, BOARD_THICKNESS), height=BRIDGE_HEIGHT,
    storage=False, work_surface=False, plan_symbol="closet-board",
    wood_material_ref="oak-trim", source=BRIDGE_SOURCE,
)
BRIDGE_RETURN = FurnitureType(
    tag="FT-A-STUDY-BRIDGE-RETURN", name='Study oak bridge return, 5 1/8 x 60 x 3/4"',
    footprint=(BOARD_THICKNESS, RETURN_DEPTH), height=BRIDGE_HEIGHT,
    storage=False, work_surface=False, plan_symbol="closet-board",
    wood_material_ref="oak-trim", source=BRIDGE_SOURCE,
)
BRIDGE_CAP = FurnitureType(
    tag="FT-A-STUDY-BRIDGE-CAP", name='Study oak bridge cap, 4 x 5 1/8 x 3/4"',
    footprint=(CAP_WIDTH, RETURN_DEPTH), height=BOARD_THICKNESS,
    storage=False, work_surface=False, plan_symbol="closet-board",
    wood_material_ref="oak-trim", source=BRIDGE_SOURCE,
)

STUDY_BRIDGE_TYPES = (BRIDGE_FRONT, BRIDGE_RETURN, BRIDGE_CAP)

STUDY_BRIDGE = [
    Furniture(uid="SX3RBRDG01", tag="FURN-A-STUDY-BRIDGE-FRONT",
              type_ref="FT-A-STUDY-BRIDGE-FRONT", room="RM-A-STUDY",
              position=FRONT_POSITION),
    Furniture(uid="SX3RBRDG02", tag="FURN-A-STUDY-BRIDGE-WEST",
              type_ref="FT-A-STUDY-BRIDGE-RETURN", room="RM-A-STUDY",
              position=WEST_RETURN_POSITION),
    Furniture(uid="SX3RBRDG03", tag="FURN-A-STUDY-BRIDGE-EAST",
              type_ref="FT-A-STUDY-BRIDGE-RETURN", room="RM-A-STUDY",
              position=EAST_RETURN_POSITION),
    Furniture(uid="SX3RBRDG04", tag="FURN-A-STUDY-BRIDGE-CAP",
              type_ref="FT-A-STUDY-BRIDGE-CAP", room="RM-A-STUDY",
              position=CAP_POSITION,
              mount=Mount(kind=MountKind.FLOOR, elevation=CAP_BOTTOM_ELEVATION)),
]
