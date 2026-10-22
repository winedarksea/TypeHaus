"""The dark-steel wall handrails' type: RL-S-HANDRAIL-E/-W, RL-A-HANDRAIL, RL-G-SERVICE.

Owner 2026-10-22: a stock US retail handrail bracket is taken as meeting R301.5 at its
maker's stated spacing; the choice is the look, a matte black bracket to match the rail.
"""

from __future__ import annotations

from typehaus import RailingType, inch
from typehaus.model import Product

HILLMAN_HD_BRACKET_BLACK = Product(
    tag="PROD-HILLMAN-HD-RAIL-BRACKET-BLK", brand="Hillman",
    model="Heavy duty handrail bracket, matte black",
    name="Heavy-duty handrail bracket, matte black",
    url="https://www.farmandfleet.com/products/1580938-hillman-heavy-duty-handrail-bracket-matte-black.html",
    source="Retailer listing, read 2026-10-22: matte black, heavy duty, maximum 48 in. "
           "between brackets. Saddle screws into the rail's underside: drill and tap the "
           "steel rail at each bracket. Any equal matte black retail bracket will do.",
)

RAILING_INT_DARK_STEEL_HANDRAIL = RailingType(
    tag="RAILING-INT-DARK-STEEL-HANDRAIL",
    name="Dark steel 1 1/2\" round wall handrail on matte black brackets",
    rail_diameter=inch(1.5),
    bracket_spacing_max=inch(48),
    product_ref=HILLMAN_HD_BRACKET_BLACK.tag,
    source="The rail's colour stays the RAILING_DARK_METAL assembly's. Spacing is the "
           "bracket maker's stated maximum.",
)

RAILING_TYPES = (RAILING_INT_DARK_STEEL_HANDRAIL,)
HANDRAIL_PRODUCTS = (HILLMAN_HD_BRACKET_BLACK,)
