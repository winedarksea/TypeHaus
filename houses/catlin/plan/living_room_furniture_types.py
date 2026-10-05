"""Living-room puzzle table selection and its sofa seating allowance."""

from typehaus.library.placeables._zones import front_zone
from typehaus.library.placeables.furniture import SOFA_84_SEAT_BAND
from typehaus.model import FurnitureType, Product, inch

PUZZLE_COFFEE_TABLE_WIDTH = inch(44.5)
PUZZLE_COFFEE_TABLE_DEPTH = inch(23.8)
SOFA_TO_COFFEE_TABLE_GAP = inch(18)
SOFA_SEAT_BAND_INSET = 0.72

PUZZLE_COFFEE_TABLE_PRODUCT = Product(
    tag="PROD-LIFT-TOP-PUZZLE-COFFEE-TABLE", brand="Breakwater Bay",
    sku="W120117949", name="Lift-top coffee table with removable puzzle tray, brown",
    url="https://www.wayfair.com/furniture/pdp/breakwater-bay-lift-top-coffee-table-with-removable-puzzle-tray-modern-wood-center-table-with-hidden-storage-power-strip-for-living-room-brown-w120117949.html",
    source="Owner-selected product reference, 2026-10-05. Also sold as GOUUN, Amazon "
           "ASIN B0HFJ5VTC3: https://www.amazon.com/Coffee-Table-Storage-Puzzle-Tray/dp/B0HFJ5VTC3?th=1",
)

PUZZLE_COFFEE_TABLE = FurnitureType(
    tag="FT-LIVING-PUZZLE-COFFEE-TABLE",
    name='Lift-top puzzle coffee table, 44.5" x 23.8", brown',
    footprint=(PUZZLE_COFFEE_TABLE_WIDTH, PUZZLE_COFFEE_TABLE_DEPTH),
    height=inch(18.3), storage=True, plan_symbol="coffee-table",
    product_ref=PUZZLE_COFFEE_TABLE_PRODUCT.tag,
    source="Wayfair W120117949 / Amazon B0HFJ5VTC3, read 2026-10-05: brown engineered "
           "wood, lift top with removable felt-lined puzzle tray stowed underneath, "
           "concealed divided storage and built-in power strip. Closed dimensions "
           "44.5 W x 23.8 D x 18.3 H in.; lifted height 23.6 in. per owner. Geometry "
           "shows the closed table; horizontal lift travel is not specified.",
)

# This gap serves seated access to the table; circulation goes around the sitting group.
# Keep the shared 30-inch walk-lane type intact for sofas without a coffee table.
SOFA_WITH_PUZZLE_COFFEE_TABLE = SOFA_84_SEAT_BAND.model_copy(update={
    "tag": "FT-LIVING-SOFA-84-TABLE-GAP",
    "name": "Standard sofa (puzzle-table seating gap)",
    "source": "Catlin living-room arrangement: 18-inch seated access gap to the puzzle "
              "coffee table across the approximately 60 1/2-inch seat span.",
    "clearances": (front_zone(
        *SOFA_84_SEAT_BAND.footprint, SOFA_TO_COFFEE_TABLE_GAP,
        "seated access in front of sofa", inset=SOFA_SEAT_BAND_INSET,
    ),),
})

LIVING_ROOM_FURNITURE_TYPES = (PUZZLE_COFFEE_TABLE, SOFA_WITH_PUZZLE_COFFEE_TABLE)
LIVING_ROOM_FURNITURE_PRODUCTS = (PUZZLE_COFFEE_TABLE_PRODUCT,)
