"""RM-M-BED reading corner on W-M-W4: a two-unit SEKTION window seat between two 12" open
cabinets under walnut tops, plus a STRANDMON wing chair. The seat units are Study 2's
FURN-S-STUDY-NOOK-SEAT-24 on the same 3 1/2" 2x4 base; configured prices live in prices.toml.
"""

from __future__ import annotations

from plan.study_nook_types import FORBATTRA_MATTE_WHITE_30
from typehaus.model import FurnitureType, Product, inch

SEKTION_BASE_FRAME_12_30 = Product(
    tag="PROD-IKEA-SEKTION-BASE-12-24-30", brand="IKEA", model="SEKTION 12x24x30 base",
    sku="102.653.92", name='SEKTION white base cabinet frame, 12 x 24 x 30"',
    url="https://www.ikea.com/us/en/p/sektion-base-cabinet-white-10265392/",
    source=("IKEA US listing, read 2026-10-03: $53; 3/4\" melamine panels, adjustable "
            "shelf holes; legs sold separately (not used here)."),
)
STRANDMON = Product(
    tag="PROD-IKEA-STRANDMON", brand="IKEA", model="STRANDMON wing chair",
    sku="604.928.15", name="STRANDMON wing chair, Kelinge beige",
    url="https://www.ikea.com/us/en/p/strandmon-wing-chair-kelinge-beige-60492815/",
    source=('IKEA US listing, read 2026-10-03: $399 (Kelinge beige; Sulviken 806.131.66 '
            'is $349); 32 1/4" W x 37 3/4" D x 39 3/4" H.'),
)
BED_READING_CORNER_PRODUCTS = (SEKTION_BASE_FRAME_12_30, STRANDMON)

_BASE = ("3 1/2\" 2x4 base with a baseboard-matching kick; 1\" walnut top "
         "(CT-M-BED-NOOK-*), 36\" finished.")

BED_NOOK_END = FurnitureType(
    tag="FURN-M-BED-NOOK-END-12", name='SEKTION 12x24x30 open shelves, 34 1/2" installed',
    footprint=(inch(12), inch(24)), height=inch(34.5), carcass_depth=inch(24),
    storage=True, work_surface=False, plan_symbol="sektion-open-base",
    product_ref=SEKTION_BASE_FRAME_12_30.tag,
    source=("SEKTION 102.653.92, no fronts, shelves facing the room. " + _BASE + " One at "
            "each end of the seat; the south one is the backrest, 12\" over the cushion."),
)
BED_NOOK_COVER = FurnitureType(
    tag="FT-M-BED-NOOK-COVER-30", name='FÖRBÄTTRA matte white cover, 1/2 x 24 5/8 x 30"',
    footprint=(inch(0.5), inch(24.625)), height=inch(30), plan_symbol="sektion-cover-panel",
    product_ref=FORBATTRA_MATTE_WHITE_30.tag,
    source="Exposed end of a 30\" frame. Starts on the base.",
)
# 3" HR foam, as FT-S-STUDY-NOOK-CUSHION; held 1/2" behind the lift-up fronts.
BED_NOOK_CUSHION = FurnitureType(
    tag="FT-M-BED-NOOK-CUSHION", name='Window-seat cushion, 48 x 24 3/8 x 3"',
    footprint=(inch(48), inch(24.375)), height=inch(3), plan_symbol="seat-cushion",
    storage=False, work_surface=False,
    source=("Custom one-piece cushion: 3\" HR foam (2.5 lb/ft3, ILD ~35) in a zippered, "
            "welted performance-fabric cover, non-slip base. Runs cabinet to cabinet."),
)
ARMCHAIR_STRANDMON = FurnitureType(
    tag="FURN-ARMCHAIR-STRANDMON", name="IKEA STRANDMON wing chair",
    footprint=(inch(32.25), inch(37.75)), height=inch(39.75), plan_symbol="armchair",
    product_ref=STRANDMON.tag,
    source="IKEA STRANDMON 604.928.15; solid wood frame, pocket-spring seat.",
)
BED_READING_CORNER_TYPES = (BED_NOOK_END, BED_NOOK_COVER, BED_NOOK_CUSHION, ARMCHAIR_STRANDMON)
