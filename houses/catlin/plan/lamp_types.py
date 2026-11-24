"""Plug-in lamps (lighting review, 2026-11-23): reading, desk and table light that the
ceiling no longer chases. Prices live in prices.toml; instances in plan/lamps.py.

Owner rules: replaceable E26 (or the house's GU10) lamps, a plain receptacle, switched at the
lamp. A lamp is furniture, so it is not a body for ``advisory.luminaire_placement`` and does
not count in ``advisory.room_illuminance``. One bulb SKU per colour: SOLHETTA E26 globe,
1600 lm in the floor lamps, 800 lm elsewhere, 2700 K. The lounge day lamp and the NYMÅNE
bed-head lamps left on 2026-11-24 (owner: ceiling day cans, beds get rearranged).
IKEA US listings read 2026-11-24; IKEA publishes no CRI. Footprints marked ~ are not
dimensioned on the listing.
"""

from __future__ import annotations

from typehaus.model import FurnitureType, Product, inch

_READ = "IKEA US listing, read 2026-11-24. "

HEKTAR_FLOOR = Product(
    tag="PROD-IKEA-HEKTAR-FLOOR-DG", brand="IKEA", model="HEKTAR floor lamp", sku="702.165.44",
    name="HEKTAR floor lamp, dark gray",
    url="https://www.ikea.com/us/en/p/hektar-floor-lamp-dark-gray-70216544/",
    source=_READ + "$89.99; 71\" high; 13\" base; 12\" shade; E26, max 53 W; bulb sold "
           "separately.",
)
FADO_TABLE = Product(
    tag="PROD-IKEA-FADO-TABLE-WH", brand="IKEA", model="FADO table lamp", sku="700.963.77",
    name="FADO table lamp, white, 10\"",
    url="https://www.ikea.com/us/en/p/fado-table-lamp-white-70096377/",
    source=_READ + "$29.99; 10\" dia x 9\" high (25 x 24 cm on EU listings) glass globe on a "
           "plastic base; max 75 W; 6'-1\" cord; E26 (EU article E27).",
)
TERTIAL_WORK = Product(
    tag="PROD-IKEA-TERTIAL-DG", brand="IKEA", model="TERTIAL work lamp", sku="203.554.34",
    name="TERTIAL work lamp, dark gray",
    url="https://www.ikea.com/us/en/p/tertial-work-lamp-dark-gray-20355434/",
    source=_READ + "$19.99; E26, max 13 W; 7\" shade; clamp to 2 1/4\"; 4'-11\" cord.",
)
SOLHETTA_1600_27K = Product(
    tag="PROD-IKEA-SOLHETTA-E26-1600-27K", brand="IKEA", model="SOLHETTA E26 1600 lm",
    sku="905.915.45", name="SOLHETTA LED bulb E26 1600 lumen, dimmable, globe opal, 2700 K",
    url="https://www.ikea.com/us/en/p/solhetta-led-bulb-e26-1600-lumen-dimmable-globe-opal-90591545/",
    source=_READ + "$8.99; 10.5 W.",
)
SOLHETTA_800_27K = Product(
    tag="PROD-IKEA-SOLHETTA-E26-800-27K", brand="IKEA", model="SOLHETTA E26 800 lm",
    sku="605.839.43", name="SOLHETTA LED bulb E26 800 lumen, dimmable, globe opal, 2700 K",
    url="https://www.ikea.com/us/en/p/solhetta-led-bulb-e26-800-lumen-dimmable-globe-opal-60583943/",
    source=_READ + "$4.99 / 2 pack; 5 W; 25,000 h.",
)
LAMP_PRODUCTS = (HEKTAR_FLOOR, FADO_TABLE, TERTIAL_WORK, SOLHETTA_1600_27K, SOLHETTA_800_27K)

LAMP_FLOOR = FurnitureType(
    tag="FT-LAMP-FLOOR-HEKTAR", name="Floor reading lamp, HEKTAR + SOLHETTA 1600 lm 2700 K",
    footprint=(inch(13), inch(16)), height=inch(71), plan_symbol="ikea-hektar-floor-lamp",
    product_ref=HEKTAR_FLOOR.tag,
    source="13\" base; the shade overhangs ~10\" toward -y (its back is +y). Seated reading "
           "beside a sofa or chair; 1600 lm 2700 K bulb.",
)
LAMP_TABLE = FurnitureType(
    tag="FT-LAMP-TABLE-FADO", name="Table lamp, FADO + SOLHETTA 800 lm 2700 K",
    footprint=(inch(10), inch(10)), height=inch(9.5), plan_symbol="ikea-fado-table-lamp",
    product_ref=FADO_TABLE.tag,
    source="Glass globe; a warm, low night source on a counter.",
)
LAMP_DESK = FurnitureType(
    tag="FT-LAMP-DESK-TERTIAL", name="Desk lamp, TERTIAL + SOLHETTA 800 lm 2700 K",
    footprint=(inch(6.7), inch(19.8)), height=inch(17.4), plan_symbol="ikea-tertial-work-lamp",
    product_ref=TERTIAL_WORK.tag,
    source="Working pose: clamp at +y on the desk's back edge, shade ~20\" out toward -y, "
           "17.4\" high. Desk task light, switched at the lamp.",
)
LAMP_TYPES = (LAMP_FLOOR, LAMP_TABLE, LAMP_DESK)
