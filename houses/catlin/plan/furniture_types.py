"""House-local furniture catalog for items specific to the Catlin plan.

Only the south mudroom closet remains here: its footprint is fitted to a specific wall
(sized to fill from its door to the west wall), which is what makes it house-local. The
north closet was reframed as RM-M-MECH (2026-07-28) and no longer exists as furniture.
The workbench and the shoe bench were generic and moved to ``library.placeables.furniture``
as FURN-G-WORKBENCH / FURN-M-MUD-BENCH.
"""

from __future__ import annotations

from typehaus import FurnitureType, ft


# Mudroom closet (RM-M-MUDROOM, houses/catlin/plan/storeys/main.py), sized to fill its
# wall from its door to the west wall, like library's FURN-WARDROBE-48 the depth is set
# by what has to be *left over*, not a standard 24" reach-in: the room is 8'-11 1/2" deep
# clear, and the 36" walking aisle in front of WIN-M-MUD/FURN-M-MUD-BENCH is centred on
# the window rather than the room. Sliding bypass doors (two overlapping panels, not a
# pocket sash) for the same reason as FURN-WARDROBE-48: the run has no floor to spare for
# a swing.
MUD_CLOSET_SOUTH = FurnitureType(
    tag="FURN-M-MUD-CLOSET-S",
    name="Mudroom closet, south wall (sliding doors)",
    footprint=(ft(6, 3.875), ft(3, 3.625)),
    height=ft(8),
    plan_symbol="tall-cabinet-double",
    storage=True,
    source="Catlin mudroom conversion (2026-07-28): run from D-M-MUD to the west wall",
)
FURNITURE_TYPES = (MUD_CLOSET_SOUTH,)
