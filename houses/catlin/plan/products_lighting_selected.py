"""Catlin luminaire selections of 2026-10-28 (cans 2026-10-31).

Owner goals: long life, solid quality, fair price; no overpriced brands except the signature
pieces. "Sheet" in a source means the manufacturer spec sheet was read; anything else came
from retailer pages. Each open item is an explicit CONFIRM, to settle before ordering.
None of them blocks modelling.
"""

from __future__ import annotations

from typehaus.model import Product

_READ = "Read 2026-10-28. "
_READ7 = "Read 2026-11-07. "

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
    url="https://waclighting.com/storage/waclighting-images/inst_sheet/BL-23210_INSSHT.pdf",
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
    url="https://www.meanwell.com/Upload/PDF/HLG-100H/HLG-100H-SPEC.PDF",
    source=_READ7 + "Mean Well HLG-100H-SPEC (2026-07-24) pp. 1-2: 'Class 2 power unit' "
           "(series-wide), UL 8750 type HL, 24 V / 4 A / 96 W, A-type IP65 with Vo/Io pots, "
           "Tcase -40..+80 C, 220 x 68 x 38.8 mm. The printed unit label was not seen.",
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

# --- 2026-10-31 lighting review: tape families, drivers, controllers, utility fittings ----
# Products, not prices (#28). Every 24V family is plain 2- or 5-wire tape in a standard
# 12 mm channel, so a same-size tape can replace it; a controller sits beside its driver.
_REVIEW = "Lighting review 2026-10-31. "
# E4 (2026-11-07): no standard 12 mm RGB+CCT/RGBTW tape publishes a per-channel table near
# 250 lm/ft a white (GM LTR-S-COB-RGBTW 68/73, Diode VALENT RGBTW 100/113, American Lighting
# SPTL-RGBTW 410 total only), so the owner accepted this one at its measured output.
SLL_COB_RGBCCT = Product(
    tag="PROD-SLL-COB-RGBCCT-24V", brand="SuperLightingLED", model="DC24V RGB+CCT COB (p-4545)",
    name="24V RGB+CCT COB LED tape, 12 mm, 6-wire",
    url="https://www.superlightingled.com/dc24v-rgb-cct-color-changing-flexible-cob-led-strip-p-4545.html",
    source=_READ7 + "SLL spec page: 12 mm PCB, 2.2 mm tall (fits the 15.9 mm reveal), cut "
           "41.6 mm, whites 2800-6500 K, 20 W/m, 'CRI Ra>90'; order the IP20 adhesive. SLL "
           "spectrum test report FCOB-24V-RGBCCT (2024-08-12) pp. 4-5, "
           "https://superlightingled.com/PDF/RGBCCT-COB-LED-Spectrum-Test-Report.pdf: W "
           "2855 K Ra 92 R9 51, 334 lm @ 5.16 W; C 5897 K Ra 90.9, 340 lm; RGBCW 1088 lm @ "
           "20.32 W. The sample is ~1 m by inference, so ~102 lm/ft a white channel (the "
           "page's 1296/1342 lm/m disagree). Accepted as is (owner, 2026-11-07).",
)
SLL_COB_RGBW_IP67 = Product(
    tag="PROD-SLL-COB-RGBW-IP67-30", brand="SuperLightingLED", model="DC24V RGBW COB, IP67 tube, W 3000K",
    name="24V RGBW COB LED tape, IP67, 3000 K white channel",
    source=_REVIEW + "The garage linear (mark W) as RGBW with a 3000 K white channel, same "
           "1/2 in. U-channel. CONFIRM the IP67 SKU and watts per foot (white-channel "
           "CRI is a preference, owner 2026-11-07).",
)
COB_TUNABLE_24V = Product(
    tag="PROD-SLL-COB-CCT-24V", brand="SuperLightingLED", model="DC24V tunable-white COB, 2700-6500K",
    name="24V tunable-white COB LED tape, 10 mm, 3-wire",
    source=_REVIEW + "The second-floor hall cove (mark E6). CRI 90+ at both ends is a "
           "preference, not a gate (owner, 2026-11-07).",
)
GLEDOPTO_GL_C_001P = Product(
    tag="PROD-GLEDOPTO-GL-C-001P", brand="Gledopto", model="GL-C-001P",
    name="5-in-1 Zigbee 3.0 Pro LED controller (RGB/RGBW/RGBCCT/CCT/dim), 12-54 V",
    url="https://www.superlightingled.com/zigbee-5in1-led-light-controller-voiceapprf-remote-control-p-4521.html",
    source=_REVIEW + "The indoor coves (E4, E6), set to its mode once. Local in ZHA on the "
           "second ZBT-2 (Zigbee mode). Distributor tables (SLL; gledopto.eu), read "
           "2026-11-07, Gledopto's own pages 404: -20..+45 C, IP20, 5 A / 270 W max total; "
           "power-on lights by default, 'previous' settable.",
)
# The garage's six (mark W) since 2026-11-07: owner prefers Matter, and moisture is the
# concern, so the controller is Matter over Wi-Fi in a gasketed box beside its driver.
GLEDOPTO_GL_C_208M = Product(
    tag="PROD-GLEDOPTO-GL-C-208M", brand="Gledopto", model="GL-C-208M",
    name="Matter over Wi-Fi RGB+CCT LED controller, 5 x PWM (R, G, B, C, W), 12-24 V",
    url="https://www.matteralpha.com/gledopto/gledopto-smart-rgbcct-strip-controller-p3017",
    source=_READ7 + "Matter 1.3, CSA certificate CSA256C5MAT46615-24, firmware QUEC_1.0.1.0 "
           "(2025-09-14), part GL-C-208M (Matter Alpha's mirror of the CSA DCL; the CSA page "
           "was not reached). UNCONFIRMED (manuals.plus copy of the Gledopto manual, "
           "https://manuals.plus/asin/B0FC6BH6M3, seen only as a search quote 2026-11-07): "
           "12-24 VDC, 15 A a channel / 20 A total (Lectronz lists 10 A total), -20..+45 C, "
           "108 x 45 x 18 mm, IP20. No RGBW mode: the tape's W lead goes on the warm "
           "terminal, C unused, color_temp pinned at the warmest kelvin.",
)
NEMA_4X_BOX_GENERIC = Product(
    tag="PROD-NEMA4X-BOX-GENERIC", brand="generic",
    model="NEMA 4X non-metallic junction box, 6 x 6 x 4 in.",
    name="Gasketed PVC NEMA 4X junction box, 6 x 6 x 4 in., with sealed cord grips",
    url="https://static.elliottelectric.com/P/Item/TAB/E987R",
    source=_READ7 + "Any listed non-metallic NEMA 4X box (PVC, so Wi-Fi passes) that holds "
           "the 108 x 45 x 18 mm controller; grips in from below. E.g. Carlon E987R, 6 x 6 "
           "x 4 in., UL listed, NEMA 6P (Elliott Electric page).",
)
# A sealed box breathes or condenses: one pressure-compensating vent in its bottom wall.
ENCLOSURE_VENT_GENERIC = Product(
    tag="PROD-ENCLOSURE-VENT-GENERIC", brand="generic", model="M12 IP68 breather vent plug",
    name="Pressure-compensating breather vent plug, M12, IP68, polyamide",
    url="https://www.rapidonline.com/wiska-evsp-12-vent-plugs-m12-549410",
    source=_READ7 + "Any standard M12 IP68 enclosure vent plug, e.g. Wiska EVSP 12 "
           "(polyamide, pressure compensation, -40..+100 C; Rapid Electronics page). In the "
           "box's bottom wall, so the controller box neither sweats nor pumps water in.",
)
# The AC splice box on each HLG-100H-24A (PSU-96-WE): the A-type's AC side is a 3-conductor
# SJOW 17 AWG cable lead, a bare driver case (220 x 68 x 38.8 mm) that cannot go in a 4 in.
# box. One box, three parts, at every driver (owner, 2026-11-09).
RACO_752_BLANK = Product(
    tag="PROD-RACO-752", brand="RACO", model="752", name="4 in. square flat blank cover",
    url="https://hubbellcdn.com/specsheet/RACO-752-SPEC-EN.pdf",
    source=_READ7 + "Hubbell RACO 752 (distributor listings): 4 in. square flat blank cover, "
           "0.063 in. steel, for the RACO 232 box (30.3 in3).")
CORD_GRIP_GENERIC = Product(
    tag="PROD-CORD-GRIP-GENERIC", brand="generic", model="1/2 in. cord connector",
    name="1/2 in. knockout strain-relief cord connector, for 0.25-0.4 in. cord",
    source=_READ7 + "Any listed screw-in cord connector (non-metallic) for the driver's SJOW "
           "17 AWG x 3 lead. The lead enters one 1/2 in. KO; the branch NM enters the 3/4 in. KO "
           "on a clamp. Fill, worst case (14 AWG through-fed): 4 hots/neutrals + 1 ground + 1 "
           "clamp = 6 x 2.0 = 12 in3 of 30.3 in3. DC leads stay outside: no Class 2 in the box.")
HALCO_LED_READY_STRIP = Product(
    tag="PROD-HALCO-90511", brand="Halco", model="90511",
    name="4 ft LED-ready 2-lamp strip, non-shunted, Type B double-ended T8",
    source=_REVIEW + "Distributor pages: pre-wired for Type B (ballast-bypass) double-ended "
           "T8 tubes, 120-277 V, no ballast. The tubes are the lamp.",
)
WAVEFORM_T8_95 = Product(
    tag="PROD-WAVEFORM-T8-95-50K", brand="Waveform Lighting",
    model="CENTRIC DAYLIGHT T8 4024.50 (5000K, 4 ft; 4-pack 4024.50.4P)",
    name="4 ft T8 LED tube, 95 CRI, 5000 K, Type A+B, double-ended direct wire",
    url="https://store.waveformlighting.com/cdn/shop/files/"
        "CENTRIC_DAYLIGHT_Full_Spectrum_T8_LED_Tube_Light_Specification_Sheet.pdf",
    source=_READ7 + "Waveform spec sheet Rev 2.01 (2022-04-08): 'TriplePlay' Type A+B; "
           "direct wire single-ended non-shunted or double-ended shunted/non-shunted; 1,800 "
           "lm, 18 W, Ra 95+, R9 90+, G13, ETL 4008503, damp, not dimmable.",
)
CHANNEL_45_GENERIC = Product(
    tag="PROD-CHANNEL-45-GENERIC", brand="generic", model="45-degree aluminium LED channel, 8 ft",
    name="45-degree corner aluminium channel with frosted lens, caps and clips, 8 ft",
    source=_REVIEW + "Standard 16 mm-class 45-degree extrusion sold in multi-packs; replaces "
           "the Diode S45 bundle (avoid premium extrusions). Fits 10-12 mm tape.",
)
LEVITON_9880 = Product(
    tag="PROD-LEVITON-9880", brand="Leviton", model="9880",
    name="Keyless porcelain lampholder, E26, on a 4 in. box",
    source=_REVIEW + "Utility light for storage and equipment spaces (NEC 210.70(C)); takes "
           "an ordinary A19 LED.",
)
LEVITON_9726_C = Product(
    tag="PROD-LEVITON-9726-C", brand="Leviton", model="9726-C",
    name="Pull-chain porcelain lampholder, E26, 15 A 125 V grounding receptacle, 4 in. box",
    url="https://leviton.com/products/9726-c",
    source="Read 2026-11-15. Leviton product page: one-piece glazed porcelain, twist-lock to a "
           "3 1/4 or 4 in. box, two screws top wired, pull-chain on/off, grounding outlet "
           "(one feature line says non-grounding: CONFIRM on the box). ~$6 retail (owner).",
)
WAVEFORM_A19_95 = Product(
    tag="PROD-WAVEFORM-CENTRICHOME-A19-30K", brand="Waveform Lighting", model="CentricHOME A19 3000K",
    name="A19 LED bulb, E26, 800 lm, 3000 K, 95 CRI, R9 80+ (typ. 91), 10 W, not dimmable",
    url="https://store.waveformlighting.com/cdn/shop/files/"
        "CENTRIC_HOME_A19_10W_LED_Bulb_-_E26_Specification_Sheet.pdf",
    source=_READ7 + "Waveform spec sheet PN 4005C.30 Rev 2.0 (2021-06-14): 800 lm, 10 W, Ra "
           "95+, R9 rated 80+ (typical 91; owner accepts, 2026-11-07); damp; NOT for totally "
           "enclosed luminaires; NOT dimmable; UL E519490. The Karlie shades are open.",
)
HINKLEY_SOREN_50910BK = Product(
    tag="PROD-HINKLEY-50910BK", brand="Hinkley", model="50910BK",
    name="Soren medium sconce, black, clear fluted glass, 1 x E26",
    url="https://www.hinkley.com/50910bk.html",
    source="Owner, 2026-11-02. Hinkley spec sheet 'SOREN 50910BK' (generated 2026-05-07, "
           "https://images.salsify.com/image/upload/s--47g1yvQy--/"
           "c766b9dd1f24404b486bc0fcff80d6e3e7e98ae4.pdf), read 2026-11-07: Damp Rated; W 5 "
           "in., H 14.3 in., extension 4.8 in., 5 in. round backplate, TOP TO OUTLET 2.5 in.; "
           "1-6 W medium LED, 120 V; mounts up or down. Black or Heritage Brass only. The "
           "sheet says 'T-style bulbs required': keep the ModernVintage A19 (owner, "
           "2026-11-07), test-fit one before ordering three, and ask Hinkley whether "
           "T-style is fit or look.",
)
WAVEFORM_MODERNVINTAGE_A19_30K = Product(
    tag="PROD-WAVEFORM-MODERNVINTAGE-A19-30K", brand="Waveform Lighting",
    model="ModernVintage 95 CRI A19 5W filament, 3000K",
    name="A19 LED filament bulb, E26, 450 lm, 3000 K, 95 CRI, R9 80+",
    url="https://store.waveformlighting.com/cdn/shop/files/"
        "Ultra_High_95_CRI_A19_5W_LED_Filament_Bulb_for_Home_Residential_Specification_Sheet.pdf",
    source="Waveform spec sheet, read 2026-11-02: 5 W, 450 lm, 95 CRI, R9 > 80, dimmable, "
           "2400/2700/3000 K. Fits the Soren's 6 W cap; the filament reads well behind "
           "clear fluted glass.",
)

SELECTED_LIGHTING_PRODUCTS = (
    RACO_752_BLANK, CORD_GRIP_GENERIC,
    NORA_NSIC_401QAT, NORA_NS_40P, NORA_NS_12, NORA_NS_76W, PAR20_90_30K, PAR20_90_27K,
    PAR20_90_40K, PAR20_90_50K, SORAA_VIVID_PAR20, SORAA_VIVID_PAR20_25, JUNO_WF4_DREG,
    WESTGATE_LP_2X4,
    SCHLUTER_SNLT, BARRON_VARIUS_AG90, WAC_LINE_24, WAC_ROLAND, WAC_STRETCH, NUVO_BOWMAN_36,
    MODERN_FORMS_MYKONOS, WAC_TUBE_EXT, SLL_COB_IP67, MEANWELL_HLG_100H_24A, LIVEX_4451,
    SLL_COB_RGBCCT, SLL_COB_RGBW_IP67, COB_TUNABLE_24V,
    GLEDOPTO_GL_C_001P, GLEDOPTO_GL_C_208M, NEMA_4X_BOX_GENERIC, ENCLOSURE_VENT_GENERIC,
    HALCO_LED_READY_STRIP, WAVEFORM_T8_95,
    LEVITON_9880, LEVITON_9726_C, CHANNEL_45_GENERIC, WAVEFORM_A19_95, HINKLEY_SOREN_50910BK,
    WAVEFORM_MODERNVINTAGE_A19_30K,
)
