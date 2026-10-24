"""RM-M-BED reading chair: a STRANDMON wing chair. Prices live in prices.toml."""

from __future__ import annotations

from typehaus.model import FurnitureType, Product, inch

STRANDMON = Product(
    tag="PROD-IKEA-STRANDMON", brand="IKEA", model="STRANDMON wing chair",
    sku="903.598.29", name="STRANDMON wing chair, Nordvalla dark gray",
    url="https://www.ikea.com/us/en/p/strandmon-wing-chair-nordvalla-dark-gray-90359829/",
    source=('IKEA US listing, read 2026-10-24; Nordvalla dark gray; '
            '32 1/4" W x 37 3/4" D x 39 3/4" H.'),
)
BED_READING_CORNER_PRODUCTS = (STRANDMON,)

ARMCHAIR_STRANDMON = FurnitureType(
    tag="FURN-ARMCHAIR-STRANDMON", name="IKEA STRANDMON wing chair",
    footprint=(inch(32.25), inch(37.75)), height=inch(39.75), plan_symbol="strandmon",
    product_ref=STRANDMON.tag,
    source="IKEA STRANDMON 903.598.29; Nordvalla dark gray upholstery, tinted solid wood legs.",
)
BED_READING_CORNER_TYPES = (ARMCHAIR_STRANDMON,)
