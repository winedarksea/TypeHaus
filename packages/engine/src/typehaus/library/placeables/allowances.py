"""Scheduled-and-billed fit-out: curtain rods, access panels, closet shelving.

``plan_symbol=None`` where the object is not a floor-plan thing (a rod at 7'-0", a panel in a
wall face): these exist to be scheduled, billed, and drawn in 3D at the height they are hung.
None is in a STARTER_* tuple; a house opts in to the ones it places.
"""

from __future__ import annotations

from typehaus.model import FurnitureType, Mount, MountKind, inch

_WALL = Mount(kind=MountKind.WALL)
_ROD = ("Curtain rod on end brackets. Width is the rod, not the opening: a rod runs past the "
        "rough opening both sides so the stack sits on wall, not glass. Depth is the bracket "
        "projection, height the rod and finial.")
_PANEL = ("Framed metal access panel in a finished wall face; size is the clear opening, "
          "depth the frame's projection.")
_CLOSET = ("Ventilated epoxy-coated steel shelf on 12 ga. wall standards and brackets, with "
           "the integral hang rod — the ordinary reach-in fit-out. Standards land on studs.")

CURTAIN_ROD_48 = FurnitureType(
    tag="FT-CURTAIN-ROD-48", name='Curtain rod, 48"',
    footprint=(inch(48), inch(4)), height=inch(2),
    plan_symbol=None, mount=_WALL, source=_ROD,
)
CURTAIN_ROD_84 = FurnitureType(
    tag="FT-CURTAIN-ROD-84", name='Curtain rod, 84"',
    footprint=(inch(84), inch(4)), height=inch(2),
    plan_symbol=None, mount=_WALL, source=_ROD,
)
# 14x14 is a tub waste-and-overflow size; 14x29 reaches the whole of a wall-hung WC carrier.
ACCESS_PANEL_1414 = FurnitureType(
    tag="FT-ACCESS-PANEL-1414", name='Access panel, 14" x 14"',
    footprint=(inch(14), inch(1)), height=inch(14),
    plan_symbol=None, mount=_WALL, source=_PANEL,
)
ACCESS_PANEL_1429 = FurnitureType(
    tag="FT-ACCESS-PANEL-1429", name='Access panel, 14" x 29"',
    footprint=(inch(14), inch(1)), height=inch(29),
    plan_symbol=None, mount=_WALL, source=_PANEL,
)
# A CEILING panel swaps the fields' roles: the clear opening is in PLAN and the frame's
# projection is the height. Gasketed, because a return-side cavity behind an unsealed lid in
# a closet ceiling is IMC 601.5(7)'s return-air-from-a-closet.
ACCESS_PANEL_CLG_3029 = FurnitureType(
    tag="FT-ACCESS-PANEL-CLG-3029", name='Ceiling access panel, 30" x 29", gasketed',
    footprint=(inch(30), inch(29)), height=inch(1),
    plan_symbol=None, mount=Mount(kind=MountKind.CEILING),
    source=("Hinged, gasketed framed panel in a finished ceiling face; plan size is the clear "
            "opening, height the frame's projection. The gasket keeps the lid from being a "
            "return inlet (IMC 601.5(7))."),
)
CLOSET_SHELF_ROD_60 = FurnitureType(
    tag="FT-CLOSET-SHELFROD-60", name='Closet shelf and rod, 60" x 16"',
    footprint=(inch(60), inch(16)), height=inch(1),
    storage=True, work_surface=False, plan_symbol="bookcase", mount=_WALL, source=_CLOSET,
)
CLOSET_SHELF_ROD_84 = FurnitureType(
    tag="FT-CLOSET-SHELFROD-84", name='Closet shelf and rod, 84" x 16"',
    footprint=(inch(84), inch(16)), height=inch(1),
    storage=True, work_surface=False, plan_symbol="bookcase", mount=_WALL, source=_CLOSET,
)
CLOSET_SHELF_ROD_96 = FurnitureType(
    tag="FT-CLOSET-SHELFROD-96", name='Closet shelf and rod, 96" x 16"',
    footprint=(inch(96), inch(16)), height=inch(1),
    storage=True, work_surface=False, plan_symbol="bookcase", mount=_WALL, source=_CLOSET,
)
CLOSET_SHELF_36 = FurnitureType(
    tag="FT-CLOSET-SHELF-36", name='Closet linen shelf, 36" x 12"',
    footprint=(inch(36), inch(12)), height=inch(1),
    storage=True, work_surface=False, plan_symbol="bookcase", mount=_WALL, source=_CLOSET,
)

FIT_OUT_TYPES = (
    CURTAIN_ROD_48, CURTAIN_ROD_84, ACCESS_PANEL_1414, ACCESS_PANEL_1429,
    ACCESS_PANEL_CLG_3029, CLOSET_SHELF_ROD_60, CLOSET_SHELF_ROD_84, CLOSET_SHELF_ROD_96,
    CLOSET_SHELF_36,
)
