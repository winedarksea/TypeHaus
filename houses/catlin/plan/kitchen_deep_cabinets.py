"""Catlin kitchen's deep upper carcasses, made to the dimensions SEKTION does not sell.

IKEA's shallow wall frames are stock at 20, 30 and 40 inches high. Its 24-inch-deep
top cabinets are a smaller range of widths and heights. These five dimensions are
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
        source=("Site-built 3/4-inch plywood carcass; 24-inch finished depth and "
                "front alignment to adjacent SEKTION high cabinets. Confirm door "
                "material, hardware, rail and fastening on the cabinet shop drawings."),
    )


DEEP_18_20 = _deep_upper("FT-KIT-DEEP18-20", 18, 20)
DEEP_24_20 = _deep_upper("FT-KIT-DEEP24-20", 24, 20)
DEEP_30_30 = _deep_upper("FT-KIT-DEEP30-30", 30, 30)
DEEP_24_40 = _deep_upper("FT-KIT-DEEP24-40", 24, 40)
DEEP_24_30 = _deep_upper("FT-KIT-DEEP24-30", 24, 30)

KITCHEN_DEEP_CABINET_TYPES = (
    DEEP_18_20, DEEP_24_20, DEEP_30_30, DEEP_24_40, DEEP_24_30,
)
