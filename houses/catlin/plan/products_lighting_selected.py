"""Catlin luminaire selections of 2026-10-28 (cans 2026-10-31) (plans/lighting-products.md §2).

Owner goals: long life, solid quality, fair price; no overpriced brands except the signature
pieces. "Sheet" in a source means the manufacturer spec sheet was read; anything else came
from retailer pages. Each open item is an explicit CONFIRM, to settle before ordering.
None of them blocks modelling.
"""

from __future__ import annotations

from typehaus.model import Product

_READ = "Read 2026-10-28. "

# --- A-C: the recessed cans (2026-10-31) ---------------------------------------------------
# One replaceable-lamp housing family for every can; the tier is the trim and the lamp, billed
# as separate part lines. Replaces the Lotus LL4SRG canless set (listed as overstock, and an
# integrated module is the whole fixture when it fails). Tape carries dimming and tunable CCT.
_READ31 = "Read 2026-10-31. "
NORA_NSIC_401QAT = Product(
    tag="PROD-NORA-NSIC-401QAT", brand="Nora Lighting", model="NSIC-401QAT",
    name='4" IC airtight line-voltage new-construction housing, double wall, E26',
    source=_READ31 + "Nora spec sheet: housing height 6 in., cutout 4-3/8 in., frame 8-1/2 "
           "in. long, IC, airtight, medium (E26) base, bar hangers. A 6 in. body needs a clear "
           "joist bay (electrical.ceiling_can_framing).",
)
NORA_NS_40P = Product(
    tag="PROD-NORA-NS-40P", brand="Nora Lighting", model="NS-40P",
    name='4" stepped baffle trim, white, for PAR20',
    source=_READ31 + "NS-40 series sheet: 50 W R20/PAR20 maximum, cULus damp with a "
           "compatible housing. CONFIRM the -P suffix against the NSIC-401QAT compatibility "
           "list.",
)
NORA_NS_12 = Product(
    tag="PROD-NORA-NS-12", brand="Nora Lighting", model="NS-12",
    name='4" adjustable gimbal trim, white, for PAR20',
    source=_READ31 + "Not read: CONFIRM the NS-12 is the 4 in. PAR20 gimbal for this housing, "
           "its tilt range, and its damp listing.",
)
NORA_NS_76W = Product(
    tag="PROD-NORA-NS-76W", brand="Nora Lighting", model="NS-76W",
    name='4" lensless shower baffle trim, white, wet location',
    source=_READ31 + "Retailer pages only: 4 in. lensless white baffle, shower flange, 3.5 in. "
           "tall. No sheet found. CONFIRM its wet listing with this housing and its lamp "
           "requirement before ordering; the fallback is the lensed NS-22 for those openings.",
)
PAR20_90_30K = Product(
    tag="PROD-BULBRITE-PAR20-90-30K", brand="Bulbrite", model="772262",
    name="PAR20 LED lamp, 6.5 W, 3000K, 90 CRI, 40 degree, enclosed and wet rated",
    source=_READ31 + "Retailer listing: 6.5 W, 500 lm, 3000 K, CRI 90, 40 deg, enclosed and "
           "wet rated, dimmable. CONFIRM the SKU number. Any 90-CRI enclosed-rated PAR20 of "
           "this output will do (PLT, Halco).",
)
PAR20_90_27K = PAR20_90_30K.model_copy(update={
    "tag": "PROD-BULBRITE-PAR20-90-27K", "model": "PAR20 2700K",
    "name": "PAR20 LED lamp, 2700K, 90 CRI, enclosed and wet rated",
    "source": _READ31 + "The 3000 K lamp's 2700 K sibling, BATH2's evening shower can. CONFIRM "
              "the SKU, its wet rating and its lumens (carried at 480)."})
PAR20_90_40K = PAR20_90_30K.model_copy(update={
    "tag": "PROD-BULBRITE-PAR20-90-40K", "model": "PAR20 4000K",
    "name": "PAR20 LED lamp, 4000K, 90 CRI, enclosed rated",
    "source": _READ31 + "The lounge's cool layer. CONFIRM a 4000 K enclosed-rated 90+ CRI "
              "PAR20 (95 CRI if one exists) and its lumens (carried at 520)."})
PAR20_90_50K = PAR20_90_30K.model_copy(update={
    "tag": "PROD-PAR20-90-50K-WET", "brand": "Bulbrite", "model": "PAR20 5000K",
    "name": "PAR20 LED lamp, 5000K, 90 CRI, wet rated",
    "source": _READ31 + "BATH2's day layer (>= 5000 K, high CRI). Not found yet: CONFIRM a "
              "wet-rated 5000 K PAR20 and its lumens (carried at 520). If none exists, those "
              "openings take the lensed NS-22 with a damp-rated lamp."})
SORAA_VIVID_PAR20 = Product(
    tag="PROD-SORAA-VIVID-PAR20-30K-36", brand="Soraa", model="Vivid PAR20 3000K 36",
    name="Vivid PAR20 LED lamp, 10.8 W, 3000K, 95 CRI, R9 95, 36 degree",
    source=_READ31 + "Bulbrite (Soraa) listings: 10.8 W, 540 lm at 3000 K, CRI 95, R9 95, "
           "enclosed rated, damp, dimmable leading and trailing edge. CONFIRM the ordering "
           "code for the 36 deg beam.",
)
SORAA_VIVID_PAR20_25 = SORAA_VIVID_PAR20.model_copy(update={
    "tag": "PROD-SORAA-VIVID-PAR20-30K-25", "model": "Vivid PAR20 3000K 25",
    "name": "Vivid PAR20 LED lamp, 10.8 W, 3000K, 95 CRI, R9 95, 25 degree",
    "source": _READ31 + "The 36 deg lamp's 25 deg beam, for the gimbals that light a wall or "
              "the mantel. CONFIRM the ordering code."})
JUNO_WF4_DREG = Product(
    tag="PROD-JUNO-WF4-DREG-B", brand="Juno", model="WF4 DREG B ALO19 SWW5 90CRI MW M6",
    name='4" deep-regressed wafer downlight, baffle, white, 90 CRI, set to 3000K',
    source=_READ31 + "Juno sheet and retailers: 14.5 W, lumen selectable 700/900/1100 "
           "(sources differ on the middle step), switchable 2700-5000 K set to 3000 K, about "
           "2-1/4 in. tall, IC, airtight, wet, JA8. Only where a 6 in. housing cannot fit.",
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
    tag="PROD-WAC-BL-23210-BK", brand="WAC Lighting", model="BL-23210-BK",
    name="Sprig LED swing-arm wall light, black",
    source=_READ + "WAC spec sheet (Jan 2022): 5 W, 287 delivered lm, 3000 K, CRI 90, 120 VAC, "
           "ELV/TRIAC 100-10%, damp, canopy on/off toggle, USB port under the canopy, 10 in. "
           "arm (modelled folded, 8 x 4 in.). CONFIRM it is hardwired (junction box); the "
           "sheet does not say.",
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
    NORA_NSIC_401QAT, NORA_NS_40P, NORA_NS_12, NORA_NS_76W, PAR20_90_30K, PAR20_90_27K,
    PAR20_90_40K, PAR20_90_50K, SORAA_VIVID_PAR20, SORAA_VIVID_PAR20_25, JUNO_WF4_DREG,
    WESTGATE_LP_2X4,
    SCHLUTER_SNLT, BARRON_VARIUS_AG90, WAC_LINE_24, WAC_ROLAND, WAC_STRETCH, NUVO_BOWMAN_36,
    MODERN_FORMS_MYKONOS, WAC_TUBE_EXT, SLL_COB_IP67, MEANWELL_HLG_100H_24A, LIVEX_4451,
)
