"""Catlin luminaire selections of 2026-10-28 (plans/lighting-products.md §2).

Owner goals: long life, solid quality, fair price; no overpriced brands except the signature
pieces. "Sheet" in a source means the manufacturer spec sheet was read; anything else came
from retailer pages. Each open item is an explicit CONFIRM, to settle before ordering.
None of them blocks modelling.
"""

from __future__ import annotations

from typehaus.model import Product

_READ = "Read 2026-10-28. "

# --- A, A1, B, B2: one can SKU family, the LL4SRG (wet, TRIAC), in three fixed CCTs -----
# The LL4SR named until 2026-10-28 is the 2nd generation and damp only; every can relinks.
LOTUS_LL4SRG_30K = Product(
    tag="PROD-LOTUS-LL4SRG-30K-WH", brand="Lotus LED Lights", model="LL4SRG-30K-WH",
    name='4" deeply regressed canless LED downlight, white, 3000K',
    source=_READ + "Lotus spec sheet: 14.5 W, 860 lm, 3000 K fixed, CRI 90+, IC rated, "
           "airtight, WET listed, TRIAC dimming. Replaces the damp-only LL4SR, so marks A "
           "and B are one SKU. CONFIRM the body is the LL4SR's 5 in. square x 2 in. deep.",
)
LOTUS_LL4SRG_41K = LOTUS_LL4SRG_30K.model_copy(update={
    "tag": "PROD-LOTUS-LL4SRG-41K-WH", "model": "LL4SRG-41K-WH",
    "name": '4" deeply regressed canless LED downlight, white, 4100K',
    "source": _READ + "Lotus product page (not a sheet): 900 lm, 4100 K fixed, otherwise the "
              "LL4SRG-30K. CONFIRM the -41K SKU and its lumens against a spec sheet."})
LOTUS_LL4SRG_27K = LOTUS_LL4SRG_30K.model_copy(update={
    "tag": "PROD-LOTUS-LL4SRG-27K-WH", "model": "LL4SRG-27K-WH",
    "name": '4" deeply regressed canless LED downlight, white, 2700K',
    "source": _READ + "Lotus LL4SRG family in a fixed 2700 K phosphor, 850 lm; BATH2's "
              "evening shower can."})
# --- B1: BATH2's day layer -------------------------------------------------------------
LOTUS_LD4S_50K = Product(
    tag="PROD-LOTUS-LD4S-50K-4S-WR-WT", brand="Lotus LED Lights", model="LD4S-50K-4S-WR-WT",
    name='4" square slim LED downlight, white reflector, 5000K',
    source=_READ + "Lotus spec sheet: fixed 5000 K, 1,420 lm, CRI 90+, IC, airtight, WET, "
           "square, white reflector, no housing needed. CONFIRM: wattage (not on the "
           "sheet read; 12 W carried), the distributor price, the 3\" vs 3.5\" ceiling "
           "clearance, and R9 (the day layer is the >=5000 K, high-CRI hard requirement).",
)
# --- D: the flat panels ------------------------------------------------------------------
WESTGATE_LP_2X4 = Product(
    tag="PROD-WESTGATE-LP-2X4-60W-40K-D", brand="Westgate", model="LP-2X4-60W-40K-D",
    name="2x4 LED flat panel, 60 W, 4000K, 0-10V, with LP-SRFC-2X4 surface kit",
    sku="LP-SRFC-2X4",
    source=_READ + "Westgate spec sheet: fixed 4000 K, 60 W, 5,100 lm, 0-10 V dimming, "
           "47.75 x 23.75 x 1.71 in. Ordered with the LP-SRFC-2X4 surface-mount kit "
           "(depth with the kit unpublished; modelled at 2.5 in.). Same maker as the "
           "garage's vaportights.",
)
# --- E1: the shower niche (catalog-only) ----------------------------------------------------
SCHLUTER_SNLT = Product(
    tag="PROD-SCHLUTER-KB12SNLT2WW", brand="Schluter Systems", model="KB12SNLT2WW",
    name="KERDI-BOARD-SNLT lit niche with LIPROTEC-ECD driver LTECD1W",
    sku="LTECD1W",
    source=_READ + "Schluter KERDI-BOARD-SNLT niche with integrated LIPROTEC profile, "
           "3000 K, ~118 lm; LIPROTEC-ECD driver LTECD1W. Unplaced. The ECD dims only from "
           "Schluter-listed dimmers (DVELV-300P).",
)
# --- F: the plant-room grow bars -------------------------------------------------------------
BARRON_VARIUS_AG90 = Product(
    tag="PROD-BARRON-AG90-W-001", brand="Barron Lighting Group", model="Growlite Varius AG90-W-001",
    name='45" horticultural LED bar, 90 W, white spectrum',
    source=_READ + "Barron AG90 sheet: 44.78 x 2.50 x 0.98 in. single extrusion, on-board "
           "driver, 90 W, ~11,280 lm, CRI >=92, ETL to UL 8800, DAMP, 1-10 V dimming, "
           "safety cable included, 12-36 in. above canopy. Owner: two bars at full output; "
           "damp is enough (the plant-room lights are never misted). CONFIRM: the CCT "
           "(spectrum code) and a ceiling hanger kit (the bar mounts by magnet to a rack "
           "frame, AG-FRAME, as published).",
)
# --- G: the suite's over-bed wall light --------------------------------------------------
WAC_LINE_24 = Product(
    tag="PROD-WAC-WS-6724-30-BK", brand="WAC Lighting", model="WS-6724-30-BK",
    name='dweLED LINE 24" LED wall light, 3000K, brushed black',
    source=_READ + "WAC spec sheet: 24 in., 22 W, 1,140 delivered lm, 3000 K, CRI 90, ELV "
           "dimming, damp. Projection was not on the pages read (modelled at 2 in.).",
)
# --- H: up/down sconces ------------------------------------------------------------------------
WAC_ROLAND = Product(
    tag="PROD-WAC-WS-83212-BK", brand="WAC Lighting", model="WS-83212-BK",
    name="dweLED Roland LED up/down wall sconce, black",
    source=_READ + "WAC spec sheet: 15 W, 680 delivered lm, 3000 K, CRI 90, ELV + TRIAC, "
           "damp; 12 H x 4.5 W x 2.5 in. projection (retailer). CONFIRM the theatre units' "
           "DVCL-153P against the published TRIAC dimmer range.",
)
# --- J, J1: reading lights ------------------------------------------------------------------------
WAC_STRETCH = Product(
    tag="PROD-WAC-BL-1660-BK", brand="WAC Lighting", model="BL-1660-BK",
    name="dweLED Stretch LED double swing-arm wall light, black",
    source=_READ + "WAC spec sheet: 17 W, 623 delivered lm, 3000 K, CRI 90, damp, hardwired, "
           "touch dimmer on the backplate; no wall dimmer. Reach is unpublished on the pages "
           "read (modelled folded, 8 x 4 in.). CONFIRM with WAC: is the touch plate a true "
           "on/off (mark J1 relies on it), and does the lamp come back ON after a wall switch "
           "cuts power (mark J relies on that)?",
)
# --- M1: the studio bar pendant (catalog-only) --------------------------------------------------
NUVO_BOWMAN_36 = Product(
    tag="PROD-NUVO-62-2271", brand="Nuvo Lighting", model="62-2271",
    name='Bowman 36" LED linear pendant, matte black',
    source=_READ + "Nuvo sheet (read for the nickel -2272; same body): 35.875 x 2 x 1.75 in. "
           "bar, 39 W, 3,315 lm, fixed 3000 K, CRI 90+, cETLus DRY; stems to 38 in. overall. "
           "Unplaced.",
)
# --- N: the 52" fans -------------------------------------------------------------------------------
MODERN_FORMS_MYKONOS = Product(
    tag="PROD-MODERNFORMS-FR-W1819-52L", brand="Modern Forms", model="FR-W1819-52L-MB",
    name='Mykonos 52" DC ceiling fan with LED light, 3000K',
    source=_READ + "Modern Forms sheet: 3 blades, ETL WET, DC motor, 1,110 lm, ~14.75 in. "
           "with the 4.5 in. downrod. ** A DC FAN CANNOT BE SPEED-CONTROLLED BY A "
           "CONVENTIONAL WALL DIMMER: ** constant hot plus the wall control. Wet listing "
           "retires mark N2. The 3000 K SKU carries no CCT infix (-52L27 is 2700 K). CONFIRM "
           "the finish suffix (-MB matte black, -MW matte white).",
)
# --- R: exterior wall lights -----------------------------------------------------------------------
WAC_TUBE_EXT = Product(
    tag="PROD-WAC-WS-W2605-BK", brand="WAC Lighting", model="WS-W2605-BK",
    name="Tube LED outdoor wall light, down light, 3000K, black",
    source=_READ + "WAC: Down Light, 3000 K, CRI 90, ETL wet, 120 V, ELV/0-10 V, 5 H x 4.5 "
           "in. dia (retailer). Fixes the old WS-W2506 typo. CONFIRM: watts and lumens "
           "differ between sources (16 W / 800 lm on the FM-W26 sheet is carried), "
           "dark-sky status, and the cold rating.",
)
# --- W: the garage's exterior tape, its channel and its drivers ------------------------------------
WAC_INVISILED_OD = Product(
    tag="PROD-WAC-T24-OD2-40-30", brand="WAC Lighting", model="T24-OD2-40-30",
    name="InvisiLED Outdoor 24V LED tape, 3000K, 40 ft reel",
    source=_READ + "WAC sheet: 24 V, 2.4 W/ft, 200+ lm/ft, 3000 K, CRI 90, IP65, UL wet, "
           "4 in. cut pitch, 40 ft maximum run; one reel cut per run. In clear channel "
           "T24-WE-CH5 (5 ft, 0.51 W x 0.23 in. H, aperture DOWN), 5 per run, with "
           "T24-WE-EC end caps and under-side clips. A plain 2-wire 24 V tape in a ~1/2 in. "
           "channel, so a same-size tape can replace it later with no new channel or "
           "wiring. Owner accepts the sheet's -4 F rating for now.",
)
WAC_INVISILED_DRIVER = Product(
    tag="PROD-WAC-PS-24DC-U96R-WE", brand="WAC Lighting", model="PS-24DC-U96R-WE",
    name="InvisiLED 24V remote driver, 96 W, ELV/TRIAC, IP67",
    sku="T24-WE-B072-BK",
    source=_READ + "WAC: 96 W, 24 V DC, 120-277 V AC in, ELV/TRIAC dimming, 8.375 x 2.8125 "
           "x 1.6875 in., IP67. One per run, INDOORS on a T24-WE-B072-BK 6 ft lead; a "
           "73.5 LF run at 2.4 W/ft is 58-61 W, ~63% of the driver.",
)
# --- Z: the attic's candle sconces ---------------------------------------------------------------
LIVEX_4451 = Product(
    tag="PROD-LIVEX-4451-04", brand="Livex Lighting", model="4451-04",
    name="1-light candle wall sconce, black",
    source=_READ + "Livex (retailer pages): plain black 1-light candle sconce, damp, 8.5 H x "
           "4.25 W x 7.75 in. projection, backplate 6 x 4.125 in., about $95-102. Lamp: Feit "
           "BPCFC40930CAFIL/4, 3000 K, CRI 90, 300 lm, 3.3 W. CONFIRM the E12 socket and the "
           "UL/ETL mark. Fallback: Kichler 52505BK (dry, 40 W).",
)

SELECTED_LIGHTING_PRODUCTS = (
    LOTUS_LL4SRG_30K, LOTUS_LL4SRG_41K, LOTUS_LL4SRG_27K, LOTUS_LD4S_50K, WESTGATE_LP_2X4,
    SCHLUTER_SNLT, BARRON_VARIUS_AG90, WAC_LINE_24, WAC_ROLAND, WAC_STRETCH, NUVO_BOWMAN_36,
    MODERN_FORMS_MYKONOS, WAC_TUBE_EXT, WAC_INVISILED_OD, WAC_INVISILED_DRIVER, LIVEX_4451,
)
