"""The east-wall SEKTION line: products and house types (2026-10-02).

The living-room bases are the library's 15"-deep SEKTION frames (`SEKT-B*-D15`), the two
carousel corners are `SEKT-CORNER-B38`, both shared catalog. What is here is what the house
orders round them: the carousel corner as a product, the peninsula's floor anchoring frame
and connector rails, and three FÖRBÄTTRA-faced pieces the shared catalog has no reason to
carry. NOT editable, in the `study_nook_types.py` idiom. Prices live in prices.toml.
"""

from __future__ import annotations

from typehaus.model import FurnitureType, Product, inch

SEKTION_BASE_15_DEEP = Product(
    tag="PROD-IKEA-SEKTION-BASE-D15", brand="IKEA", model="SEKTION 15\"-deep base frames",
    name='SEKTION white base cabinet frames, 15/18/24/30/36 x 15 x 30"',
    url="https://www.ikea.com/us/en/p/sektion-base-cabinet-with-shelves-white-vedhamn-oak-s19439618/",
    source=("IKEA US listings, read 2026-10-02: 15x15x30, 18x15x30 and 24x15x30 found as "
            "listed configurations (30 and 36 per the base-cabinet category); system depth "
            "15\", frame 15 3/8\" actual. Every living-room unit takes MAXIMERA drawers."),
)
SEKTION_CORNER_CAROUSEL = Product(
    tag="PROD-IKEA-SEKTION-CORNER-CAROUSEL", brand="IKEA",
    model="SEKTION corner base cabinet with carousel",
    name='SEKTION white corner base cabinet with carousel, 38 x 38 x 30"',
    sku="s79582533",
    source=("IKEA US s79582533 / s89506379, read 2026-10-02: 38\" legs 24\" deep, 30\" frame, "
            "13\" + 13\" bifold door, reversible. Hang each door on the end AWAY from the "
            "range: the slide-in stands 3\" proud and a fold toward it strikes it."),
)
SEKTION_FLOOR_ANCHOR = Product(
    tag="PROD-IKEA-SEKTION-FLOOR-ANCHOR", brand="IKEA", model="SEKTION floor anchoring frame",
    name='SEKTION floor anchoring frame, 82 5/8"', sku="105.570.36",
    source=("Holds the peninsula's 84\" of free-standing bases (B36 + B24 + B24) to the "
            "subfloor, inset ~11/16\" at each end."),
)
SEKTION_CONNECTOR_RAIL = Product(
    tag="PROD-IKEA-SEKTION-CONNECTOR-RAIL", brand="IKEA", model="SEKTION connector rail",
    name='SEKTION connector rail, 34 1/4", 2-pack', sku="005.570.32",
    source="Hangs the FÖRBÄTTRA panels on the peninsula's seating face.",
)
LIVING_EAST_RUN_PRODUCTS = (SEKTION_BASE_15_DEEP, SEKTION_CORNER_CAROUSEL,
                            SEKTION_FLOOR_ANCHOR, SEKTION_CONNECTOR_RAIL)

# FÖRBÄTTRA matte white, site-cut from the 25x80 panel (study_nook_types.py's product).
_PANEL = "PROD-IKEA-FORBATTRA-MATTE-25-80"

LIVING_END_PANEL = FurnitureType(
    tag="FT-LIV-E-END-PANEL", name='FÖRBÄTTRA end panel, 1/2 x 15 1/2 x 34"',
    footprint=(inch(0.5), inch(15.5)), height=inch(34), plan_symbol="sektion-cover-panel",
    product_ref=_PANEL,
    source=("Closes a living-room bank against the fireplace brick, floor to slab. Two cut "
            "from one 25x80 panel. Check the insert's side clearance against it."),
)
PENINSULA_END_PANEL = FurnitureType(
    tag="FT-KIT-PEN-END-PANEL", name='FÖRBÄTTRA end panel, 1/2 x 24 x 34"',
    footprint=(inch(0.5), inch(24)), height=inch(34), plan_symbol="sektion-cover-panel",
    product_ref=_PANEL,
    source="The peninsula's west end, floor to slab, under the quartz.",
)
PENINSULA_BACK_PANEL = FurnitureType(
    tag="FT-KIT-PEN-BACK-PANEL", name='FÖRBÄTTRA seating face, 98 1/2 x 3/4 x 34"',
    footprint=(inch(98.5), inch(0.75)), height=inch(34), plan_symbol="sektion-cover-panel",
    product_ref=_PANEL,
    source=("Covers the bases' backs and the corner leg's from the end panel to the support "
            "box, on SEKTION connector rails. Three 25x80 panels laid horizontally."),
)
PENINSULA_SUPPORT_BOX = FurnitureType(
    tag="FT-KIT-PEN-SUPPORT-BOX", name='Closed support box, 24 x 9 5/8 x 36"',
    footprint=(inch(24), inch(9.625)), height=inch(36), plan_symbol="sektion-cover-panel",
    storage=False, work_surface=False, product_ref=_PANEL,
    source=("Shop-built 3/4\" ply box, FÖRBÄTTRA-faced, standing where the seating overhang "
            "would be under FURN-M-KIT-MIXER-GARAGE: a counter-to-ceiling cabinet cannot "
            "stand on a cantilever."),
)
LIVING_EAST_RUN_TYPES = (LIVING_END_PANEL, PENINSULA_END_PANEL, PENINSULA_BACK_PANEL,
                         PENINSULA_SUPPORT_BOX)
