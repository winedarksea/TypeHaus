"""RM-M-BED's bed: a Nectar japanese-joinery bamboo platform frame, King, natural.

Replaces the king at FURN-M-BED (plan/placeables.py). Identity and dimensions only; the price
lives in prices.toml.
"""

from __future__ import annotations

from typehaus.library.placeables._zones import front_zone, side_zone
from typehaus.model import FurnitureType, Product, inch

NECTAR_JAPANESE_BAMBOO_KING_NATURAL = Product(
    tag="PROD-NECTAR-JAPANESE-BAMBOO-KING-NATURAL", brand="Nectar",
    model="Japanese Joinery Bamboo Bed Frame, King, Natural",
    name="Japanese Joinery Bamboo Bed Frame, King, Natural",
    url="https://www.nectarsleep.com/bed-frames/japanese-joinery-bamboo-bed/size-king+color-natural",
    source=("Nectar product page, read 2026-10-14: 79.9\" W x 84.3\" L x 12.3\" H frame; 39.3\" H "
            "with bamboo headboard; no box spring needed. Add to Cart $898 with Natural selected. "
            "Headboard inclusion not stated on the page; the bamboo headboard adds $349."),
)

# Same side and foot access the library's beds take (library/placeables/furniture.py).
_WIDTH, _DEPTH = inch(79.9), inch(84.3)
_NIGHTSTAND_TAGS = ("FURN-NIGHTSTAND-24", "FURN-NIGHTSTAND-16")

NECTAR_JAPANESE_BAMBOO_KING = FurnitureType(
    tag="FURN-BED-JAPANESE-KING", name="Nectar Japanese joinery bamboo bed, King, natural",
    footprint=(_WIDTH, _DEPTH), height=inch(39.3), plan_symbol="bed",
    product_ref=NECTAR_JAPANESE_BAMBOO_KING_NATURAL.tag,
    clearances=(
        side_zone(_WIDTH, _DEPTH, inch(18), "bed side access", sign=1,
                  head_inset=inch(30), occupant_types=_NIGHTSTAND_TAGS),
        side_zone(_WIDTH, _DEPTH, inch(18), "bed side access", sign=-1,
                  head_inset=inch(30), occupant_types=_NIGHTSTAND_TAGS),
        front_zone(_WIDTH, _DEPTH, inch(18), "bed foot access"),
    ),
    source=("Nectar Japanese joinery bamboo platform bed, King, natural; 79.9 x 84.3 x 12.3 in. "
            "frame, 39.3 in. with bamboo headboard. Simplified planning model, footprint as listed."),
)

BED_FRAME_PRODUCTS = (NECTAR_JAPANESE_BAMBOO_KING_NATURAL,)
BED_FRAME_TYPES = (NECTAR_JAPANESE_BAMBOO_KING,)
