"""The east-wall SEKTION line: products and house types (2026-10-02).

The living-room bases are the library's 15"-deep SEKTION frames (`SEKT-B*-D15`), the two
carousel corners are `SEKT-CORNER-B38`, both shared catalog. What is here is what the house
orders round them: the carousel corner as a product, the peninsula's floor anchoring frame
and connector rails, and the FÖRBÄTTRA-faced end panels, seating face and fillers the shared
catalog has no reason to carry. NOT editable, in the `study_nook_types.py` idiom. Prices
live in prices.toml.
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
SEKTION_BASE24_FRAME = Product(
    tag="PROD-IKEA-SEKTION-BASE24-30", brand="IKEA", model="SEKTION base frame 24x24x30",
    name='SEKTION 24x24x30" base frame', sku="902.653.88",
    url="https://www.ikea.com/us/en/p/sektion-base-cabinet-white-90265388/",
)
SEKTION_WALL12_FRAME = Product(
    tag="PROD-IKEA-SEKTION-WALL12-30", brand="IKEA", model="SEKTION wall frame 12x15x30",
    name='SEKTION 12x14 3/4x30" wall frame', sku="102.654.72",
    url="https://www.ikea.com/us/en/p/sektion-wall-cabinet-white-10265472/",
)
SEKTION_CORNER_WALL_FRAME = Product(
    tag="PROD-IKEA-SEKTION-CORNER-W26-30", brand="IKEA", model="SEKTION corner wall frame",
    name='SEKTION 26x26x30" corner wall frame', sku="102.655.04",
    url="https://www.ikea.com/us/en/p/sektion-corner-wall-cabinet-white-10265504/",
    source='Stock diagonal front with a 15-inch VOXTORP door; hinges included, rail separate.',
)
SEKTION_DEEP24_TOP_FRAME = Product(
    tag="PROD-IKEA-SEKTION-TOP24-15", brand="IKEA", model="SEKTION top frame 24x24x15",
    name='SEKTION 24x24x15" top cabinet with ventilation', sku="904.997.35",
    url="https://www.ikea.com/us/en/p/sektion-top-cabinet-with-ventilation-white-90499735/",
    source='IKEA US, read 2026-10-03: 23 5/8-inch bare depth, 24 with rail; east pantry tops.',
)
LIVING_EAST_RUN_PRODUCTS = (SEKTION_BASE_15_DEEP, SEKTION_CORNER_CAROUSEL,
                          SEKTION_FLOOR_ANCHOR, SEKTION_CONNECTOR_RAIL,
                          SEKTION_BASE24_FRAME, SEKTION_WALL12_FRAME,
                          SEKTION_CORNER_WALL_FRAME, SEKTION_DEEP24_TOP_FRAME)

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
    tag="FT-KIT-PEN-BACK-PANEL", name='FÖRBÄTTRA seating face, 73 1/2 x 1/2 x 34"',
    footprint=(inch(73.5), inch(0.5)), height=inch(34), plan_symbol="sektion-cover-panel",
    product_ref=_PANEL,
    source=("Three 24 1/2-inch strips stood vertically, cut from two 25x80 panels; "
            "actual cover thickness 1/2 inch. Connector rails keep the north face at the "
            "cabinet backs. The remaining 25 inches are painted and edge-banded without "
            "projecting into the pantry door sweep."),
)


def _filler(tag: str, width_in: float, depth_in: float, label: str, where: str) -> FurnitureType:
    depth = "15 1/2" if depth_in == 15.5 else f"{depth_in:g}"
    return FurnitureType(
        tag=tag, name=f'FÖRBÄTTRA filler, {label} x {depth} x 34"',
        footprint=(inch(width_in), inch(depth_in)), height=inch(34),
        plan_symbol="sektion-cover-panel", product_ref=_PANEL,
        source=(f"{where} Site-cut from a 25x80 panel and faced to match the fronts, floor "
                "to slab. IKEA ships a filler piece with its corner bases for exactly this "
                "job; a FÖRBÄTTRA strip is the same piece in the run's finish."),
    )


LIVING_SOUTH_FILLER = _filler(
    "FT-LIV-E-FILLER-2125", 2.125, 15.5, "2 1/8",
    "Closes the living bank's south end against the SE corner.")
# The seating cantilever's hidden support (notes/kitchen_stock_cabinet_details.md K6). The
# section is the published hidden flat bar's: Original Granite Bracket and Iron Supports both
# rate 1/2 x 2 1/2 steel at ~325 lb a bracket; a 1/4 x 3 bar yields near 95 lb on a 12" arm.
PENINSULA_BAR_BRACKET = FurnitureType(
    tag="FT-KIT-CT-BRACKET-24", name='Hidden countertop flat bar, 1/2 x 2 1/2 x 24", steel',
    footprint=(inch(2.5), inch(24)), height=inch(0.5), plan_symbol="countertop-bracket",
    source=("A36 hidden flat bar, the Original Granite Bracket / Iron Supports section "
            "(325 lb each, spaced 16-20\", ending 3\" short of the edge). 12\" bears on "
            "the peninsula's 3/4 ply sub-top, routed flush; 12\" carries the stone."),
)
LIVING_EAST_RUN_TYPES = (LIVING_END_PANEL, PENINSULA_END_PANEL, PENINSULA_BACK_PANEL,
                         LIVING_SOUTH_FILLER, PENINSULA_BAR_BRACKET)
