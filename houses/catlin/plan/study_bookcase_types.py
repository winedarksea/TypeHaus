"""The compact freestanding corner shelf chosen to fit between the study windows."""

from typehaus import FurnitureType, inch
from typehaus.model import Product

FRAILEY_CORNER_BOOKCASE_PRODUCT = Product(
    tag="PROD-TRIBESIGNS-JW0510", brand="Tribesigns", model="HOGA-JW0510",
    name="Frailey seven-tier corner bookcase, rustic brown/black",
    url=("https://www.homedepot.com/p/TRIBESIGNS-WAY-TO-ORIGIN-Frailey-23-6-in-Wide-"
         "Rustic-Brown-14-Shelf-Corner-Bookcase-7-Tier-Industrial-Corner-Shelf-"
         "Freestanding-Bookshelf-HD-GGJW0510/326090309"),
    source="Home Depot HD-GGJW0510; manufacturer manual/model JW0510, read 2026-10-14.",
)

FRAILEY_CORNER_BOOKCASE = FurnitureType(
    tag="FT-STUDY-CORNER-BOOKCASE", name="Tribesigns Frailey corner bookcase",
    footprint=(inch(23.62), inch(23.62)), height=inch(78.74), storage=True,
    plan_symbol="corner-bookcase", product_ref=FRAILEY_CORNER_BOOKCASE_PRODUCT.tag,
    source=("Tribesigns JW0510: 23.62 x 23.62 x 78.74 in., seven tiers / fourteen "
            "paired shelves; rustic-brown particleboard and black steel frame, open back. "
            "Anchor per manufacturer. Simplified shelf/frame geometry; the rectangular "
            "collision envelope conservatively includes the open corner. "
            "https://tribesigns.com/products/tribesigns-7-tier-corner-bookshelf-etagere-bookcase"),
)

STUDY_BOOKCASE_TYPES = (FRAILEY_CORNER_BOOKCASE,)
STUDY_BOOKCASE_PRODUCTS = (FRAILEY_CORNER_BOOKCASE_PRODUCT,)
