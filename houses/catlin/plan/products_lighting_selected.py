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
           "square, white reflector, no housing needed, 15 W (sheet and retailers agree). "
           "~$102 at one seller (2026-10-28). CONFIRM: the 3\" vs 3.5\" ceiling "
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
# --- H: up/down sconces ----------------------------------------------------------------------
WAC_ROLAND = Product(
    tag="PROD-WAC-WS-83212-BK", brand="WAC Lighting", model="WS-83212-BK",
    name="dweLED Roland LED up/down wall sconce, black",
    source=_READ + "WAC spec sheet: 15 W, 680 delivered lm, 3000 K, CRI 90, ELV + TRIAC, "
           "damp; 12 H x 4.5 W x 2.5 in. projection (retailer). CONFIRM the theatre units' "
           "DVCL-153P against the published TRIAC dimmer range.",
)
# --- J, J1: reading lights -------------------------------------------------------------------
WAC_STRETCH = Product(
    tag="PROD-WAC-BL-1660-BK", brand="WAC Lighting", model="BL-1660-BK",
    name="dweLED Stretch LED double swing-arm wall light, black",
    source=_READ + "WAC spec sheet: 17 W, 623 delivered lm, 3000 K, CRI 90, damp, hardwired, "
           "touch dimmer on the backplate; no wall dimmer. Reach is unpublished on the pages "
           "read (modelled folded, 8 x 4 in.). CONFIRM with WAC: is the touch plate a true "
           "on/off (mark J1 relies on it), and does the lamp come back ON after a wall switch "
           "cuts power (mark J relies on that)?",
)
# --- M1: the studio bar pendant (catalog-only) -----------------------------------------------
NUVO_BOWMAN_36 = Product(
    tag="PROD-NUVO-62-2271", brand="Nuvo Lighting", model="62-2271",
    name='Bowman 36" LED linear pendant, matte black',
    source=_READ + "Nuvo sheet (read for the nickel -2272; same body): 35.875 x 2 x 1.75 in. "
           "bar, 39 W, 3,315 lm, fixed 3000 K, CRI 90+, cETLus DRY; stems to 38 in. overall. "
           "Unplaced.",
)
# --- N: the 52" fans -------------------------------------------------------------------------
MODERN_FORMS_MYKONOS = Product(
    tag="PROD-MODERNFORMS-FR-W1819-52L", brand="Modern Forms", model="FR-W1819-52L-MB",
    name='Mykonos 52" DC ceiling fan with LED light, 3000K',
    source=_READ + "Modern Forms sheet: 3 blades, ETL WET, DC motor, 1,110 lm, ~14.75 in. "
           "with the 4.5 in. downrod. ** A DC FAN CANNOT BE SPEED-CONTROLLED BY A "
           "CONVENTIONAL WALL DIMMER: ** constant hot plus the wall control. Wet listing "
           "retires mark N2. The 3000 K SKU carries no CCT infix (-52L27 is 2700 K). CONFIRM "
           "the finish suffix (-MB matte black, -MW matte white).",
)
# --- R: exterior wall lights -----------------------------------------------------------------
WAC_TUBE_EXT = Product(
    tag="PROD-WAC-WS-W2605-BK", brand="WAC Lighting", model="WS-W2605-BK",
    name="Tube LED outdoor wall light, down light, 3000K, black",
    source=_READ + "WAC: Down Light, 3000 K, CRI 90, ETL wet, 120 V, ELV/0-10 V, 5 H x 4.5 "
           "in. dia (retailer). Fixes the old WS-W2506 typo. CONFIRM: watts and lumens "
           "differ between sources (16 W / 800 lm on the FM-W26 sheet is carried), "
           "dark-sky status, and the cold rating.",
)
# --- W: the garage's exterior tape, its channel and its drivers ------------------------------
SLL_COB_IP67 = Product(
    tag="PROD-SLL-SK512BB10-IP67-30", brand="SuperLightingLED", model="SK-512BB10DDWWZZ",
    name="24V COB LED tape, 3000K, CRI 90, IP67 silicone tube, 5 m reel",
    source=_READ + "Retailer page: 10 W/m, 1,150 lm/m at 3000 K, CRI 90+, 10 mm PCB, cut "
           "every 31.2 mm, -20 to +50 C, 'UL listed' (no file number). About $26 a reel "
           "plus $12 for the IP67 tube. Two reels per run, soldered; feed each run at its "
           "middle so neither half passes 4 m. Any same-size IP65/IP67 24V tape will do. "
           "Channel: any 1/2 in. aluminium U-channel with a clear cover (Muzata U1SW "
           "class, 0.5 x 0.25 in. inside, caps and clips in the box). CONFIRM the tube "
           "fits the channel's 0.5 in. inside width.",
)
MEANWELL_HLG_100H_24A = Product(
    tag="PROD-MEANWELL-HLG-100H-24A", brand="Mean Well", model="HLG-100H-24A",
    name="24V LED driver, 96 W, IP65",
    source=_READ + "Distributor pages: 96 W, 24 V / 4 A, IP65, UL 8750, $51-63. One per "
           "run, indoors; a 25.5 ft run at 3 W/ft is ~77 W, 80% of the driver.",
)
# --- Z: the attic's candle sconces -----------------------------------------------------------
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
    MODERN_FORMS_MYKONOS, WAC_TUBE_EXT, SLL_COB_IP67, MEANWELL_HLG_100H_24A, LIVEX_4451,
)
