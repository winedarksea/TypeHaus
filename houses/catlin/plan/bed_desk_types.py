"""RM-M-BED desk: two 15" SEKTION drawer bases on the floor under one walnut glue-up top,
with a hidden back ledger carrying the top across the 31" knee. Prices live in prices.toml.
"""

from __future__ import annotations

from typehaus.library.placeables._zones import front_zone
from typehaus.model import FurnitureType, Product, ft, inch

# SKUs pending: confirm each against the IKEA US listing at order.
SEKTION_BASE_FRAME_15_30 = Product(
    tag="PROD-IKEA-SEKTION-BASE-15-24-30", brand="IKEA", model="SEKTION 15x24x30 base",
    name='SEKTION white base cabinet frame, 15 x 24 x 30"',
    source="IKEA SEKTION base frame; legs sold separately (not used here). SKU to confirm.",
)
MAXIMERA_DRAWER_15_24 = Product(
    tag="PROD-IKEA-MAXIMERA-MEDIUM-15-24", brand="IKEA", model="MAXIMERA medium 15x24",
    name='MAXIMERA medium drawer, white, 15 x 24"',
    source="Full-extension soft-close drawer for a 10\" front; three per base. SKU to confirm.",
)
AXSTAD_DRAWER_FRONT_15_10 = Product(
    tag="PROD-IKEA-AXSTAD-MATTE-15-10", brand="IKEA", model="AXSTAD matte white 15x10",
    name='AXSTAD matte white drawer front, 15 x 10"',
    source="Matches the room's AXSTAD; three per base. Knob/handle selected separately.",
)
BED_DESK_PRODUCTS = (SEKTION_BASE_FRAME_15_30, MAXIMERA_DRAWER_15_24, AXSTAD_DRAWER_FRONT_15_10)

BED_DESK_DRAWERS = FurnitureType(
    tag="FURN-M-BED-DESK-DRAWERS-15", name='SEKTION 15x24x30, three AXSTAD drawers, on the floor',
    footprint=(inch(15), inch(24.75)), height=inch(31), carcass_depth=inch(24),
    storage=True, work_surface=False, plan_symbol="sektion-axstad-drawers",
    product_ref=SEKTION_BASE_FRAME_15_30.tag,
    clearances=(front_zone(inch(15), inch(24.75), inch(21.375),
                           "MAXIMERA full-extension drawer"),),
    source=("SEKTION frame set on the floor, no legs or plinth, shimmed level; three medium "
            "MAXIMERA behind 15x10 AXSTAD fronts. The 1\" is the hosted walnut top "
            "(CT-M-BED-DESK), 31\" finished."),
)
# Carries the top's back edge across the knee, screwed to studs; the slab's one span host.
BED_DESK_LEDGER = FurnitureType(
    tag="FT-M-BED-DESK-LEDGER-31", name='Desk ledger, 3/4 x 2 1/2 x 31", poplar, painted',
    footprint=(inch(31), inch(0.75)), height=inch(2.5), plan_symbol="countertop-bracket",
    work_surface=True,
    clearances=(front_zone(inch(31), inch(0.75), ft(3), "desk chair pull-out",
                           occupant_types=("FURN-DESK-CHAIR",)),),
    source=("1x3 poplar painted wall white, two #10 x 3\" screws per stud, top flush "
            "with the cabinet frames. The walnut top screws up through it in slots."),
)
BED_DESK_TYPES = (BED_DESK_DRAWERS, BED_DESK_LEDGER)
