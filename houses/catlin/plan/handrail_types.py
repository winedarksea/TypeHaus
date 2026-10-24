"""The matte black aluminum wall handrails' type: RL-S-HANDRAIL-E/-W, RL-A-HANDRAIL, RL-G-SERVICE.

Owner 2026-10-24: aluminum, for durability and price (the dark steel rail had no stock source).
Owner 2026-10-22: a stock US retail handrail bracket is taken as meeting R301.5 at its
maker's stated spacing; the choice is the look, a matte black bracket to match the rail.
"""

from __future__ import annotations

from typehaus import RailingType, ft, inch
from typehaus.model import Product

EZ_HANDRAIL_8_BLACK_KIT = Product(
    tag="PROD-EZ-HANDRAIL-EZA8KIT-HB", brand="EZ Handrail (Madden Manufacturing)",
    model="EZA8KIT-HB, 8 ft textured black round straight kit",
    name="EZ Handrail 8 ft textured black aluminum round straight handrail kit",
    url="https://homedepot.com/p/EZ-Handrail-8-ft-Textured-Black-Aluminum-Round-Straight-Handrail-Kit-EZA8KIT-HB/205903439",
    source="Home Depot listing, $158, read 2026-10-24. Manual: 1.9 in. OD aluminum rail; wall "
           "bracket EZA200 on 2-1/4 in. Tapcon and 1 in. stainless pan-head fasteners into a "
           "solid stud. The manual spaces brackets 'every 4' to 6''; the house uses 4' (48 in.). "
           "No load rating is published, and the kit's bracket count is not verified.",
)

RAILING_INT_ALUM_HANDRAIL = RailingType(
    tag="RAILING-INT-ALUM-HANDRAIL",
    name="Matte black aluminum 1.9 in. round wall handrail",
    rail_diameter=inch(1.9),
    stock_length=ft(8),
    bracket_spacing_max=inch(48),
    product_ref=EZ_HANDRAIL_8_BLACK_KIT.tag,
    source="The rail's colour stays the RAILING_DARK_METAL assembly's. Spacing is the house's "
           "4' setting within the manual's 4'-6' range, not a published load rating.",
)

RAILING_TYPES = (RAILING_INT_ALUM_HANDRAIL,)
HANDRAIL_PRODUCTS = (EZ_HANDRAIL_8_BLACK_KIT,)
