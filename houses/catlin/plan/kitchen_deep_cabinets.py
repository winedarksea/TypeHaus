"""Catlin kitchen's non-catalogue deep-upper items.

Every deep upper is now a stock SEKTION carcass; nothing custom remains here except the
cold-upper scribe and the hung base frame's installation spec.
"""

from plan.sektion_hardware import AXSTAD_HARDWARE
from typehaus import FurnitureType, inch
from typehaus.library.placeables.sektion_parts import kitchen_layout, sektion_parts


COLD_UPPER_SCRIBE = FurnitureType(
    tag="FT-KIT-COLD-SCRIBE-20", name='Matte-white cold-upper end scribe, 2 7/8 x 3/4 x 20 in.',
    footprint=(inch(2.875), inch(0.75)), height=inch(20), plan_symbol="sektion-cover-panel",
    source=("Site-cut matching white 3/4-inch strip on cleats (thicker than FÖRBÄTTRA, so "
            "shop stock, not an IKEA part); fitting in the cold-upper labour."),
)
STOCK_BASE_FRAME_UPPER = FurnitureType(
    tag="FT-KIT-STOCK24-30-HUNG", name='SEKTION 24x24x30" base frame hung on the wall',
    footprint=(inch(24), inch(24)), height=inch(30), plan_symbol="sektion-axstad-kitchen-wall",
    storage=True, product_ref="PROD-IKEA-SEKTION-BASE24-30",
    parts=sektion_parts(24, 24, kitchen_layout("sektion-axstad-kitchen-wall", 24, 30), "none",
                        AXSTAD_HARDWARE),
    source=("Stock 902.653.88 frame without legs or countertop, hung at 56 inches: top on "
            "the SEKTION suspension rail over BK-M-E1-MIXER-UPPER, bottom back rail screwed "
            "into BK-M-E1-MIXER-CAP. Nothing supports it from below; the exposed melamine "
            "underside gets a white cover panel if the leg-plate holes show. Stock "
            "SEKT-TS24-15 above at 86 inches; finished stack top 101 inches. "
            "See notes/kitchen_stock_cabinet_details.md."),
)
KITCHEN_DEEP_CABINET_TYPES = (COLD_UPPER_SCRIBE, STOCK_BASE_FRAME_UPPER)
