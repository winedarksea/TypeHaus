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
DEEP_24_40 = _deep_upper("FT-KIT-DEEP24-40", 24, 40)

STOCK_BASE_FRAME_UPPER = FurnitureType(
    tag="FT-KIT-STOCK24-30-HUNG", name='SEKTION 24x24x30" base frame installed above garage',
    footprint=(inch(24), inch(24)), height=inch(30), plan_symbol="wall-cabinet",
    storage=True, product_ref="PROD-IKEA-SEKTION-BASE24-30",
    source=("Stock 902.653.88 frame without legs or countertop, supported on the custom "
            "lower garage carcass at 76 inches and independently restrained to wall backing. "
            "See notes/kitchen_stock_cabinet_details.md; finished top 106 inches."),
)
KITCHEN_DEEP_CABINET_TYPES = (
    DEEP_18_20, DEEP_24_40, STOCK_BASE_FRAME_UPPER,
)
