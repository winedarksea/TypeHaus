"""Catlin kitchen's non-catalogue deep-upper items.

Every deep upper is now a stock SEKTION carcass; nothing custom remains here except the
cold-upper scribe, the hung base frame's installation spec and the pantries' exposed ends.
"""

from plan.bath1_storage_types import FORBATTRA_MATTE_WHITE_90
from plan.sektion_hardware import AXSTAD_HARDWARE
from plan.study_nook_types import FORBATTRA_MATTE_WHITE_30, FORBATTRA_MATTE_WHITE_80
from typehaus import FurnitureType, ProductPart, inch
from typehaus.library.placeables.sektion_parts import kitchen_layout, sektion_parts


COLD_UPPER_SCRIBE = FurnitureType(
    tag="FT-KIT-COLD-SCRIBE-20", name='Matte-white cold-upper end scribe, 3 1/8 x 3/4 x 20 in.',
    footprint=(inch(3.125), inch(0.75)), height=inch(20), plan_symbol="sektion-cover-panel",
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
# PANTRYC's south side faces the aisle: a stock cover above its 3 1/2" supports, and a
# toe-kick return under it, face flush with the cover, so the end reads as one notched panel.
PANTRY_END_COVER = FurnitureType(
    tag="FT-KIT-PANTRY-COVER-90", name='FÖRBÄTTRA matte white end cover, 1/2 x 24 5/8 x 90"',
    footprint=(inch(0.5), inch(24.625)), height=inch(90), plan_symbol="sektion-cover-panel",
    product_ref=FORBATTRA_MATTE_WHITE_90.tag,
    source='Whole panel, 3 1/2" to 93 1/2"; front flush with AXSTAD, 1/4" sealed gap at the wall.',
)
PANTRY_TOE_RETURN = FurnitureType(
    tag="FT-KIT-PANTRY-TOE-RETURN", name='FÖRBÄTTRA toe-kick return, 3/8 x 20 7/8 x 3 1/2"',
    footprint=(inch(0.375), inch(20.875)), height=inch(3.5), plan_symbol="sektion-cover-panel",
    parts=(ProductPart(role="toe_kick", product_ref="PROD-IKEA-FORBATTRA-TOEKICK-84",
                       length=inch(20.875)),),
    source=('Ripped from the pantry\'s own 84" FÖRBÄTTRA stick; wall to the front kick\'s '
            "face, clipped to the legs, covering the kick's end."),
)
# East pantry: S2's south side above the ash slab (frame + top cabinet, one piece) and S1's
# north side inside the microwave nook. Fronts flush with AXSTAD, backs 1/8" off the gwb.
PANTRY_S2_COVER = FurnitureType(
    tag="FT-KIT-PANTRY-S2-COVER", name='FÖRBÄTTRA matte white end cover, 1/2 x 24 5/8 x 64 1/4"',
    footprint=(inch(0.5), inch(24.625)), height=inch(64.25), plan_symbol="sektion-cover-panel",
    product_ref=FORBATTRA_MATTE_WHITE_80.tag,
    source='Cut from a 25x80; stands on CT-M-LIV-E-N (36 3/4") to the top cabinet\'s 101".',
)
PANTRY_S1_NOOK_COVER = FurnitureType(
    tag="FT-KIT-PANTRY-S1-NOOK-COVER", name='FÖRBÄTTRA matte white cover, 1/2 x 24 5/8 x 20"',
    footprint=(inch(0.5), inch(24.625)), height=inch(20), plan_symbol="sektion-cover-panel",
    product_ref=FORBATTRA_MATTE_WHITE_30.tag,
    source='Cut from a 25x30; CT-M-KIT-E (36") to the hung frame\'s underside (56").',
)
KITCHEN_DEEP_CABINET_TYPES = (COLD_UPPER_SCRIBE, STOCK_BASE_FRAME_UPPER, PANTRY_END_COVER,
                              PANTRY_TOE_RETURN, PANTRY_S2_COVER, PANTRY_S1_NOOK_COVER)
