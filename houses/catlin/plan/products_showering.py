"""Catlin showering products — valve, trims, heads, the BATH2 base (→ plan/products_interior.py).

Split out of ``products_interior.py`` for the 500-line rule in ``AGENTS.md`` on 2026-10-12,
when BATH2 went thermostatic. Same contract: identity only, never a price; the argument lives
in ``plan/fixture_types_wc.py`` and ``notes/bath2_shower.md``.

** HOUSE STANDARD: EVERY SHOWERHEAD IS ≤ 1.75 GPM ** (2026-10-12). The engine has no flow
field and nothing would read one, so the rating lives here, on each head's record.
"""

from __future__ import annotations

from typehaus.model import Product

DELTA_MULTICHOICE_ROUGH = Product(
    tag="PROD-DELTA-R10000-UNBX", brand="Delta", model="R10000-UNBX",
    name="MultiChoice universal shower rough-in valve body",
    source="Delta Faucet product page, read 2026-09-06. ** THE DECIDING FACT IS ON DELTA'S "
           "OWN PAGE: ** the body 'accepts single, dual, or dual thermostatic cartridge' -- "
           "the cartridge lives in the TRIM, not the rough. One rough-in part in all five "
           "wet walls, and the pressure-balance-vs-thermostatic choice stays reversible from "
           "OUTSIDE the tile in 2041. Moen makes you pick Posi-Temp vs Moentrol vs ExactTemp "
           "as three different bodies at rough-in; Kohler's Rite-Temp is pressure-balance "
           "only. ASSE 1016 -- see notes/interior_selections.md for why that listing is "
           "not negotiable and why this part is not the one to import. 2026-10-12: the "
           "reversal was used once -- RM-M-BATH2 takes a 17T thermostatic trim on this same "
           "rough (PROD-DELTA-T17T).",
)
DELTA_T14459_TRIM = Product(
    tag="PROD-DELTA-T14459-SS", brand="Delta", model="T14459-SS",
    name="Ashlyn Monitor 14 tub-and-shower trim with H2Okinetic head and spout, Stainless",
    source="Delta Faucet product page, read 2026-09-06. A COMPLETE trim -- valve trim, "
           "showerhead and tub spout in one box -- which removes the spout-matching problem "
           "and means the two 60\" combos need no separately specified head -- until "
           "2026-10-12, when PROD-DELTA-52535-SS (1.75 gpm) replaced the boxed head. Pressure "
           "balance (ASSE 1016), not thermostatic: every shower here is single-outlet, and a "
           "PB spool is nearly inert where a thermostatic element drifts and fails. Delta "
           "prices -SS at parity with chrome across most of the line, so the brushed-nickel "
           "premium being budgeted largely does not exist inside Delta. ** CONFIRM STOCK IN "
           "STAINLESS BEFORE THE PLUMBER ORDERS: ** Delta's stainless SHOWERING line is being "
           "thinned hard and several sibling SKUs came back discontinued.",
)
SPEAKMAN_HOTEL_HEAD = Product(
    tag="PROD-SPEAKMAN-S-2005-H", brand="Speakman", model="S-2005-H-1",
    name="Hotel Anystream showerhead, 2.5 gpm, Brushed Nickel",
    source="Speakman product page, read 2026-09-06. The only mechanism on the market that "
           "cleans INSIDE the orifice -- the Anystream plungers self-descale, where every "
           "other head is soft-nub-and-thumb or unscrew-and-soak. Nobody sells a consumer "
           "head with a user-removable faceplate. 2.5 gpm is the 2018 UPC Table 403.1 limit "
           "and Minnesota adds no flow amendment (4714.0408 is entirely receptor lining and "
           "pitch), so this is legal here and is NOT a CA/WA 1.8 gpm SKU. It looks "
           "utilitarian rather than designed; that is the trade. ** SUPERSEDED 2026-10-12: ** "
           "no fixture uses it -- BATH2 took a 1.75 gpm combo head (PROD-MOEN-26008) and "
           "every head in the house is now <= 1.75 gpm. Kept for the revert.",
)
MOEN_ENGAGE_MAGNETIX = Product(
    tag="PROD-MOEN-26010SRN", brand="Moen", model="26010SRN",
    name="Engage Magnetix two-in-one showerhead/handshower, Spot Resist Brushed Nickel",
    source="Moen product page, read 2026-09-06. ** ONE OUTLET, WHICH IS THE ENTIRE POINT. ** "
           "A fixed head plus a separate handshower is TWO outlets and needs a diverter and "
           "a second riser -- and that is true whether the handshower hangs on a slide bar "
           "or on a wall elbow with a hook. Swapping the bar for a hook saves the blocking, "
           "not the valve. This is a magnetic combo: no diverter, no second riser, no "
           "blocking, and you still get a handheld for cleaning. Spending ~$500 of valve and "
           "trim to put a handshower in a basement sauna rinse is bad value. 1.75 gpm max "
           "(Moen page, re-read 2026-10-12), so it meets the house's 1.75 gpm standard.",
)
MOEN_ATTRACT_MAGNETIX = Product(
    tag="PROD-MOEN-26008", brand="Moen", model="26008",
    name="Attract Magnetix six-function rainshower combo, Chrome",
    source="Moen product page and 26008 spec sheet, read 2026-10-12. RM-M-BATH2's one "
           "outlet: a 6 3/4\" rainshower with a magnetically docked handshower on a 60\" "
           "metal hose. 1.75 gpm at 80 psi for units made after 3/1/2018 (2.0 before), "
           "WaterSense. ** FINISH: ONLY CHROME AND 26008SRN (Spot Resist Brushed Nickel) "
           "WERE FOUND -- NO SPOT RESIST STAINLESS. ** Brushed nickel beside Delta Lumicoat "
           "stainless in one room is the mix this house rules out, so BATH2's showering parts "
           "go CHROME together: this head, the 17T trim and (2026-10-22) the T2759 filler."
)
DELTA_17T_THERMO_TRIM = Product(
    tag="PROD-DELTA-T17T", brand="Delta", model="T17T059",
    name="Trinsic TempAssure 17T Series valve-only thermostatic trim, Chrome",
    source="Delta Trinsic 17T listings, read 2026-10-22: T17T059 is the Trinsic valve-only "
           "17T trim (T17T259 shower-only, T17T459 tub/shower); trim only, on the existing "
           "PROD-DELTA-R10000-UNBX rough. Thermostatic cartridge in the TRIM; separate "
           "temperature and volume levers; no diverter, which one outlet does not need. "
           "Trinsic, not Ashlyn (owner 2026-10-22): no Ashlyn 17T exists, and Trinsic "
           "matches the room's T2759 filler. Chrome, with the 26008 head. The cartridge "
           "carries the ASSE 1016 mark the rough-in argument in fixture_types_wc.py requires.",
)
DELTA_UNIVERSAL_HEAD = Product(
    tag="PROD-DELTA-52535-SS", brand="Delta", model="52535-SS",
    name="Universal Showering 5-setting showerhead, Stainless",
    source="Delta 52535 spec sheet (DSP-B-52535), read 2026-10-12. 1.75 gpm max at 80 psi, "
           "WaterSense, ASME A112.18.1, 1/2\"-14 NPT, Touch-Clean nozzles. Replaces the head "
           "bundled in the T14459-SS box on RM-S-BATH1 and RM-S-SUITEBATH, which keeps the "
           "trim and spout; street ~$64-73. ABS body, not metal.",
)
SOLID_SURFACE_SHOWER = Product(
    tag="PROD-SOLID-SURFACE-SHOWER", brand="Swan", model="Swanstone SS-3636 + wall panels",
    name="Swanstone 36x36 single-threshold solid-surface shower pan and matching wall panels",
    url="https://swanstone.com/en/product/ss-3636-36%22-x-36%22-single-threshold-shower-pan_sw000123",
    source="Owner selection 2026-10-22 (family 2026-10-12). Swan product page, read "
           "2026-10-22: 36 x 36 x 5 1/2 in., 4 1/2 in. threshold, ~32 x 33 1/2 in. interior, "
           "CENTRE molded-in Fit-Flo drain, 3 in. drain hole, 36 in. max door. Base and "
           "panels from one Swanstone colour. Confirm before ordering: the colour, the "
           "flange and threshold sides against the W threshold, and a panel height that "
           "reaches the 106 in. ceiling above the base (or a top cap).",
)

# The stall-drying fan (notes/bath2_shower.md §7). A CLASS record: the WhisperLine
# FV-10NLF1E the hand calc read was DISCONTINUED 2024-04-02.
INLINE_FAN_4 = Product(
    tag="PROD-INLINE-FAN-4", brand="Panasonic / Fantech / Broan (class)",
    model="4\" insulated inline fan, ~120 cfm free air",
    name='4" remote-mount inline fan, insulated housing, ~1 sone',
    source="Read against the Panasonic WhisperLine FV-10NLF1E (120 cfm free air, ~1 sone, "
           "insulated housing, 4\" collars), discontinued 2024-04-02 per Panasonic "
           "distributors. CONFIRM a current 4\" equal (Fantech, Broan, Panasonic) with a "
           "published curve of >= 95 cfm at 0.3-0.4 in. w.g. and a moisture-rated housing.",
)

SHOWERING_PRODUCTS = (
    INLINE_FAN_4,
    DELTA_MULTICHOICE_ROUGH, DELTA_T14459_TRIM, SPEAKMAN_HOTEL_HEAD, MOEN_ENGAGE_MAGNETIX,
    MOEN_ATTRACT_MAGNETIX, DELTA_17T_THERMO_TRIM, DELTA_UNIVERSAL_HEAD, SOLID_SURFACE_SHOWER,
)
