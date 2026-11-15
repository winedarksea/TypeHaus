"""The matte black aluminum wall handrails' types: RL-S-HANDRAIL-E/-W, RL-A-HANDRAIL,
RL-G-SERVICE (interior) and RL-BW-ENTRY (exterior); and RL-A-FLIGHT-SKIRT's painted panel.

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
           "solid stud. The manual spaces brackets 'every 4' to 6'' (EZ Round Handrail manual, "
           "Madden Mfg., p.8 step 15, images.homedepot-static.com/catalog/pdfImages/09/"
           "09daeb7d-0204-4503-b348-8a0d887be0ec.pdf, read 2026-11-06); the house uses 54 in. "
           "No load rating is published, and the kit's bracket count is not verified. No "
           "wall-to-rail standoff is published either: the paths set the rail centre ~2 1/2 in. "
           "off the finish (1.55-1.61 in. clear, R311.7.8.2 wants 1 1/2); confirm on a bracket.",
)

RAILING_INT_ALUM_HANDRAIL = RailingType(
    tag="RAILING-INT-ALUM-HANDRAIL",
    name="Matte black aluminum 1.9 in. round wall handrail",
    rail_diameter=inch(1.9),
    stock_length=ft(8),
    bracket_spacing_max=inch(54),
    product_ref=EZ_HANDRAIL_8_BLACK_KIT.tag,
    source="The rail's colour stays the RAILING_DARK_METAL assembly's. Spacing is the house's "
           "54 in. setting (owner 2026-11-06) within the manual's 4'-6' range, not a published "
           "load rating.",
)

RAILING_EXT_ALUM_HANDRAIL = RailingType(
    tag="RAILING-EXT-ALUM-HANDRAIL",
    name="Matte black aluminum 1.9 in. round exterior wall handrail",
    rail_diameter=inch(1.9),
    stock_length=ft(8),
    bracket_spacing_max=inch(54),
    product_ref=EZ_HANDRAIL_8_BLACK_KIT.tag,
    source="The interior rail's kit, outdoors: the listing reads 'ideal for both indoor and "
           "outdoor use', powder coat (superarbor.io EZA8KIT-HB listing, read 2026-11-15). "
           "On W-G-S: 304/316 stainless screws into the studs (not the kit's plated ones), and "
           "a sealed flat bearing pad under each EZA200 where it crosses the corrugated "
           "profile. 54 in. spacing as the interior type.",
)

# A board, not a guard kit: no posts, no rail (mount="panel", rail_count=0).
RAILING_INT_SKIRT_PANEL = RailingType(
    tag="RAILING-INT-SKIRT-PANEL",
    name="Painted 3/4 in. poplar stair skirt panel",
    infill_material="poplar-skirt-paint",
    panel_thickness=inch(0.75),
    source="Two 1x12 poplar skirt boards edge-glued and cut to the rake, finished with the "
           "stair skirts. Screwed to stringer-0's study face and to RL-A-FLIGHT-GUARD's newel "
           "post; no posts or brackets of its own.",
)

RAILING_TYPES = (RAILING_INT_ALUM_HANDRAIL, RAILING_EXT_ALUM_HANDRAIL, RAILING_INT_SKIRT_PANEL)
HANDRAIL_PRODUCTS = (EZ_HANDRAIL_8_BLACK_KIT,)
