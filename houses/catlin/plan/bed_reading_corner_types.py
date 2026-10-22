"""RM-M-BED reading chair: a STRANDMON wing chair. Prices live in prices.toml."""

from __future__ import annotations

from typehaus.model import FurnitureType, Product, inch

STRANDMON = Product(
    tag="PROD-IKEA-STRANDMON", brand="IKEA", model="STRANDMON wing chair",
    sku="604.928.15", name="STRANDMON wing chair, Kelinge beige",
    url="https://www.ikea.com/us/en/p/strandmon-wing-chair-kelinge-beige-60492815/",
    source=('IKEA US listing, read 2026-10-03: $399 (Kelinge beige; Sulviken 806.131.66 '
            'is $349); 32 1/4" W x 37 3/4" D x 39 3/4" H.'),
)
BED_READING_CORNER_PRODUCTS = (STRANDMON,)

ARMCHAIR_STRANDMON = FurnitureType(
    tag="FURN-ARMCHAIR-STRANDMON", name="IKEA STRANDMON wing chair",
    footprint=(inch(32.25), inch(37.75)), height=inch(39.75), plan_symbol="armchair",
    product_ref=STRANDMON.tag,
    source="IKEA STRANDMON 604.928.15; solid wood frame, pocket-spring seat.",
)
BED_READING_CORNER_TYPES = (ARMCHAIR_STRANDMON,)
