"""Catlin trim and coil stock: the products behind the trim materials' ``product_ref``.

Identity only, never a price (#28). Most of this is yard or colour-card stock with no maker
chosen, so ``brand`` names the stock and ``model`` its size; the BOM and the inspector print
exactly that. Nothing is invented: each ``source`` repeats what the material already says.
Not ``# haus: editable``: a catalog of definitions.

Two materials stay without a product: ``kdat`` and ``fluid-applied-flashing`` live in the
shared library, which may not name a house-owned ``Product``.
"""

from __future__ import annotations

from typehaus.model import Product

AZEK_CAPTIVATE_GRAPHITE_SHEET = Product(
    tag="PROD-AZEK-CAPTIVATE-GRAPHITE-SHEET", brand="AZEK", model="Captivate",
    name="Captivate Graphite Gray 3/4 in. x 48 in. x 96 in. smooth sheet trim",
    source="AZEK 2026 product guide AS03448096: 3/4 x 48 x 96 smooth sheet, Captivate Graphite "
           "Gray factory finish. Field-ripped for door returns and casing.",
)
MDF_CASING_1X4 = Product(
    tag="PROD-STOCK-MDF-1X4", brand="Stock primed MDF", model='3/4" x 3 1/2" S4S',
    name="Primed MDF door casing, painted in the wall colour",
    source="Primed MDF 1x4 from the yard. Kept out of the wet rooms: MDF swells at a cut edge.",
)
PVC_TRIM_1X4 = Product(
    tag="PROD-STOCK-PVC-1X4", brand="Stock cellular PVC trim (AZEK/Versatex class)",
    model='3/4" x 3 1/2" S4S', name="White cellular PVC trim, painted with the walls",
    source="White cellular PVC 1x4 (Azek/Versatex class). The bathrooms and the plant room; in "
           "the tile baths it goes in after tile, on stainless trim nails and PVC adhesive.",
)
PINE_FJ_BASE_1X4 = Product(
    tag="PROD-STOCK-PINE-FJ-1X4", brand="Stock primed finger-jointed pine",
    model='3/4" x 3 1/2" S4S', name="Primed finger-jointed pine base, painted in the wall colour",
    source="Primed finger-jointed pine 1x4 from the yard.",
)
DARK_TRIM_COIL = Product(
    tag="PROD-STOCK-DARK-TRIM-COIL", brand="Near-black prefinished metal trim coil",
    name="Near-black painted metal trim, brake-formed",
    source="RF-HOUSE rake, eave and ridge trim coil, opening casings and exterior guards; "
           "colour #1c1f24, shared with the K-style gutter coil so the eave line reads continuous.",
)
DARK_KSTYLE_COIL = Product(
    tag="PROD-STOCK-DARK-KSTYLE-COIL", brand="Near-black prefinished aluminium gutter coil",
    name="K-style gutter, roll-formed on site from colour-card coil",
    source="Garage south eave and balcony gutter and leaders; the same near-black as the trim "
           "coil but a different product, so prices.toml qualifies [drainage] on the tag.",
)

TRIM_STOCK_PRODUCTS = (
    AZEK_CAPTIVATE_GRAPHITE_SHEET, MDF_CASING_1X4, PVC_TRIM_1X4, PINE_FJ_BASE_1X4,
    DARK_TRIM_COIL, DARK_KSTYLE_COIL,
)
