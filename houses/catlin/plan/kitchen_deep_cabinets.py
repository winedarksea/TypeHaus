"""Catlin kitchen's deep upper carcasses, made to the dimensions SEKTION does not sell.

IKEA's shallow wall frames are stock at 20, 30 and 40 inches high. Its 24-inch-deep
top cabinets are a smaller range of widths and heights. The remaining deep dimensions are
site-built millwork so the deep fronts align with the high pantry cabinets and the
refrigerator pair. The shop must coordinate the finish and door reveals with the
adjacent VOXTORP fronts before ordering.
"""

from typehaus import FurnitureType, inch


def _deep_upper(tag: str, width_in: int, height_in: int) -> FurnitureType:
    return FurnitureType(
        tag=tag,
        name=f'Custom deep kitchen upper, {width_in}x24x{height_in} in.',
        footprint=(inch(width_in), inch(24)),
        height=inch(height_in),
        plan_symbol="wall-cabinet",
        storage=True,
        source=("Site-built 3/4-inch plywood carcass; 24-inch nominal system depth and "
                "front alignment to adjacent SEKTION high cabinets. Confirm door "
                "material, hardware, rail and fastening on the cabinet shop drawings."),
    )


DEEP_18_20 = _deep_upper("FT-KIT-DEEP18-20", 18, 20)
DEEP_30_30 = _deep_upper("FT-KIT-DEEP30-30", 30, 30)
DEEP_24_40 = _deep_upper("FT-KIT-DEEP24-40", 24, 40)

STOCK_BASE_FRAME_UPPER = FurnitureType(
    tag="FT-KIT-STOCK24-30-HUNG", name='SEKTION 24x24x30" base frame installed above garage',
    footprint=(inch(24), inch(24)), height=inch(30), plan_symbol="wall-cabinet",
    storage=True, product_ref="PROD-IKEA-SEKTION-BASE24-30",
    source=("Stock 902.653.88 frame without legs or countertop, supported on the custom "
            "lower garage carcass at 76 inches and independently restrained to wall backing. "
            "See notes/kitchen_stock_cabinet_details.md; finished top 106 inches."),
)
STOCK_SHALLOW_PLINTH_BASE = FurnitureType(
    tag="FT-LIV-E-STOCK12-PLINTH", name='SEKTION 12x15x30" wall frame on anchored plinth',
    footprint=(inch(12), inch(15.5)), height=inch(36), plan_symbol="sektion-plinth-wall-base",
    storage=True, work_surface=True, product_ref="PROD-IKEA-SEKTION-WALL12-30",
    source=("Stock 102.654.72 wall frame on a 3 1/2-inch anchored plinth, with a "
            "1/2-inch subtop and the shared 2-inch oak slab. One 12x30 VOXTORP door and "
            "fixed shelves; no MAXIMERA drawers. Nominal installed depth 15 1/2 inches, "
            "matching the living run. A 1/8-inch sealed joint separates it from S2."),
)

KITCHEN_DEEP_CABINET_TYPES = (
    DEEP_18_20, DEEP_30_30, DEEP_24_40, STOCK_BASE_FRAME_UPPER,
    STOCK_SHALLOW_PLINTH_BASE,
)
