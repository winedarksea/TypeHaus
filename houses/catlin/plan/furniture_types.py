"""House-local furniture catalog for items specific to the Catlin plan.

Only the two mudroom closets remain here: their footprints are fitted to specific walls
(each run is sized to fill from its door to the west wall), which is what makes them
house-local. The workbench and the shoe bench were generic and moved to
``library.placeables.furniture`` as FURN-G-WORKBENCH / FURN-M-MUD-BENCH.
"""

from __future__ import annotations

from typehaus import FurnitureType, ft


# Mudroom closets (RM-M-MUDROOM, houses/catlin/plan/storeys/main.py), each run sized to
# fill its wall from its door to the west wall, like library's FURN-WARDROBE-48 the
# depths are set by what has to be *left over*, not a standard 24" reach-in: the room is
# 8'-11 1/2" deep clear, and the 36" walking aisle in front of WIN-M-MUD/FURN-M-MUD-BENCH
# is centred on the window rather than the room, so the two closets end up close but not
# equal in depth. Sliding bypass doors (two overlapping panels, not a pocket sash) for the
# same reason as FURN-WARDROBE-48: neither run has floor to spare for a swing.
MUD_CLOSET_NORTH = FurnitureType(
    tag="FURN-M-MUD-CLOSET-N",
    name="Mudroom closet, north wall (sliding doors)",
    footprint=(ft(5, 11.875), ft(2, 7.875)),
    height=ft(8),
    plan_symbol="tall-cabinet-double",
    storage=True,
    source="Catlin mudroom conversion (2026-07-28): run from D-M-ENTRY to the west wall",
)
MUD_CLOSET_SOUTH = FurnitureType(
    tag="FURN-M-MUD-CLOSET-S",
    name="Mudroom closet, south wall (sliding doors)",
    footprint=(ft(6, 3.875), ft(3, 3.625)),
    height=ft(8),
    plan_symbol="tall-cabinet-double",
    storage=True,
    source="Catlin mudroom conversion (2026-07-28): run from D-M-MUD to the west wall",
)
FURNITURE_TYPES = (MUD_CLOSET_NORTH, MUD_CLOSET_SOUTH)
