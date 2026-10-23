"""Catlin kitchen's deep upper carcasses, made to the dimensions SEKTION does not sell.

IKEA's shallow wall frames are stock at 20, 30 and 40 inches high. Its 24-inch-deep
top cabinets are a smaller range of widths and heights. The remaining deep dimensions are
site-built millwork so the deep fronts align with the high pantry cabinets and the
refrigerator pair. The shop must coordinate the finish and door reveals with the
adjacent AXSTAD matte-white fronts before ordering.
"""

from typehaus import FurnitureType, inch


def _deep_upper(tag: str, width_in: int, height_in: int) -> FurnitureType:
    return FurnitureType(
        tag=tag,
        name=f'Custom deep kitchen upper, {width_in}x24x{height_in} in.',
        footprint=(inch(width_in), inch(24)),
        height=inch(height_in),
        plan_symbol="sektion-axstad-kitchen-wall",
        storage=True,
        source=("Site-built 3/4-inch plywood carcass; 24-inch nominal system depth and "
                "front alignment to adjacent SEKTION high cabinets. Confirm door "
                "material, hardware, rail and fastening on the cabinet shop drawings."),
    )


COLD_UPPER_SCRIBE = FurnitureType(
    tag="FT-KIT-COLD-SCRIBE-20", name='Matte-white cold-upper end scribe, 2 7/8 x 3/4 x 20 in.',
    footprint=(inch(2.875), inch(0.75)), height=inch(20), plan_symbol="sektion-cover-panel",
    source="Site-cut matching white front strip on cleats; fitting included in cold-upper prices.",
)
MIXER_GARAGE_24_20 = _deep_upper("FT-KIT-MIXER24-20", 24, 20).model_copy(update={
    "plan_symbol": "sektion-axstad-kitchen-garage",
    "source": ("Custom bottomless 3/4-inch plywood enclosure on the continuous 36-inch "
               "counter; 24x24x20 nominal, cap underside 55 1/4 inches AFF. No internal "
               "shelf. Stock AXSTAD 204.260.78 24x20 front with lift-up hardware; preserve "
               "18 inches clear above the maximum 1/4-inch appliance slider when open. "
               "Door, lift hardware and slider are priced in the garage fit-out allowance."),
})

STOCK_BASE_FRAME_UPPER = FurnitureType(
    tag="FT-KIT-STOCK24-30-HUNG", name='SEKTION 24x24x30" base frame installed above garage',
    footprint=(inch(24), inch(24)), height=inch(30), plan_symbol="sektion-axstad-kitchen-wall",
    storage=True, product_ref="PROD-IKEA-SEKTION-BASE24-30",
    source=("Stock 902.653.88 frame without legs or countertop, supported on the custom "
            "lower garage carcass at 56 inches and independently restrained to wall backing. "
            "Stock SEKT-TS24-15 above at 86 inches; finished stack top 101 inches. "
            "See notes/kitchen_stock_cabinet_details.md."),
)
KITCHEN_DEEP_CABINET_TYPES = (
    COLD_UPPER_SCRIBE, MIXER_GARAGE_24_20, STOCK_BASE_FRAME_UPPER,
)
