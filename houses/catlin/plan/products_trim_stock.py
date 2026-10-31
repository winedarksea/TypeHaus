"""Catlin trim and coil stock: the products behind the trim materials' ``product_ref``.

Identity only, never a price (#28). Most of this is yard or colour-card stock with no maker
chosen, so ``brand`` names the stock and ``model`` its size; the BOM and the inspector print
exactly that. Nothing is invented: each ``source`` repeats what the material already says.
Not ``# haus: editable``: a catalog of definitions.

Two materials stay without a product: ``kdat`` and ``fluid-applied-flashing`` live in the
shared library, which may not name a house-owned ``Product``.
"""

from __future__ import annotations

from plan.exterior_palette import AZEK, METAL
from typehaus.model import Product

AZEK_CAPTIVATE_SHEET = Product(
    tag="PROD-AZEK-CAPTIVATE-SHEET", brand="AZEK", model="Captivate",
    name=f"Captivate {AZEK.colour} 3/4 in. x 48 in. x 96 in. smooth sheet trim",
    source=f"AZEK 2026 product guide AS03448096: 3/4 x 48 x 96 smooth sheet, Captivate "
           f"{AZEK.colour} factory finish (plan/exterior_palette.py). Field-ripped for door "
           "returns and casing.",
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
    tag="PROD-STOCK-DARK-TRIM-COIL", brand=METAL.maker, model=f"{METAL.line} {METAL.colour}",
    name=f"{METAL.colour} PVDF trim and flat stock, brake-formed",
    source="RF-HOUSE rake, eave and ridge trim coil, opening casings and exterior guards, in "
           "the house's one exterior dark (plan/exterior_palette.py); the K-style gutter coil "
           "is ordered to match so the eave line reads continuous.",
)
DARK_KSTYLE_COIL = Product(
    tag="PROD-STOCK-DARK-KSTYLE-COIL", brand="Prefinished aluminium gutter coil",
    name="K-style gutter, roll-formed on site from colour-card coil",
    source=f"Garage south eave and balcony gutter and leaders, colour-matched to {METAL.label} "
           "(Metal Sales publishes no K-style gutter line); a different product from the trim "
           "coil, so prices.toml qualifies [drainage] on the tag.",
)

TRIM_STOCK_PRODUCTS = (
    AZEK_CAPTIVATE_SHEET, MDF_CASING_1X4, PVC_TRIM_1X4, PINE_FJ_BASE_1X4,
    DARK_TRIM_COIL, DARK_KSTYLE_COIL,
)
