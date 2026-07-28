"""House-local furniture catalog for items specific to the Catlin plan."""

from __future__ import annotations

from typehaus import FurnitureType, ft, inch


GARAGE_WORKBENCH = FurnitureType(
    tag="FURN-G-WORKBENCH",
    name="Garage workbench, 60 x 30 x 34 in",
    footprint=(inch(60), inch(30)),
    height=inch(34),
    plan_symbol="desk",
    source="Catlin owner requirement: 60 x 30 x 34 in workbench",
)

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
# The shoe-changing bench under WIN-M-MUD. Not fitted joinery like the sauna benches
# (`sauna-bench` reused for its plan symbol — a platform against the +y wall, which is
# exactly this bench's shape against the west wall at rotation 90), 18" seat height matches
# FURN-SAUNA-BENCH-54's foot bench.
MUD_BENCH = FurnitureType(
    tag="FURN-M-MUD-BENCH",
    name="Mudroom bench, 36 x 18 in",
    footprint=(ft(3), ft(1, 6)),
    height=ft(1, 6),
    plan_symbol="sauna-bench",
    storage=False,
    source="Catlin mudroom conversion (2026-07-28): shoe-changing bench under WIN-M-MUD",
)

FURNITURE_TYPES = (GARAGE_WORKBENCH, MUD_CLOSET_NORTH, MUD_CLOSET_SOUTH, MUD_BENCH)
