"""Catlin interior-selection products — the 2026-09-06 pass (→ plan/products.py).

A second file rather than a longer one, for the 500-line rule in ``AGENTS.md``. The split is
not arbitrary: ``products.py`` is the machines — appliances, the water heater, the inverter,
the ERV — chosen one at a time as the systems were designed, and each carries the number a
check reads. This file is one exercise against one brief (easy to clean, then value, then
"popular, minimalist, just works"), and its argument lives in ``notes/interior_selections.md``.

Same contract as its parent: **identity only, never a price** (``plans/01-decisions.md`` #28),
the finish inside the model number, and ``source`` naming the datasheet and the date read.
``products.PRODUCTS`` concatenates the two, so the manifest and every ``product_ref`` see one
catalog and ``integrity.duplicate_catalog_tag`` proves the tags are disjoint.
"""

from __future__ import annotations

from plan.products_lighting import LIGHTING_PRODUCTS
from typehaus.model import Product

# =========================================================================================
#
# Everything below was chosen in one exercise against one brief -- easy to clean first, then
# value, then "popular, minimalist, just works" -- and the argument for each is in
# ``notes/interior_selections.md``. What lands HERE is only identity: brand, model, and the
# datasheet the number was read off. Prices are in ``prices.toml``, reasoning is in the note,
# and neither belongs in this file (``plans/01-decisions.md`` #28).
#
# The finish is inside the model number, as it has been since LG_WASHTOWER: TOTO's ``#01`` is
# Cotton White, Delta's ``-SS`` is Stainless and ``-SP`` is SpotShield Brushed Nickel, Moen's
# ``SRS``/``SRN`` are Spot Resist. Those letters are the order.

# --- Water closets ----------------------------------------------------------------------
#
# Four models, six bowls, and the split is deliberate rather than a failure to standardise.
# Wall-hung + skirted + rimless is the cleanability ceiling: it deletes the horizontal ledges
# a toilet has and lifts the china clear of the floor joint, which is what the large-format
# straight-set tile wants. It is also the most expensive way to buy a toilet, so it is bought
# where it is seen and used. The attic guest bath and the basement sauna rinse take the
# Drake: same Tornado Flush, same CeFiONtect glaze, half the money, and what it gives up is
# the skirt.
#
# ``CT449CFGT60`` is the BOWL ONLY. The in-wall tank is a second line on the order, and the
# reason it is TOTO's DuoFit rather than a Geberit Duofix is the bidet seat: a WASHLET+ routes
# its supply CONCEALED through the bowl, and only TOTO's own carrier has that connection. Buy
# Geberit and a braided hose crosses the finished tile forever. Both frames are within an
# eighth of 500 mm across the uprights, so FX-TOILET-WH's ``carrier_bay_width`` holds either.
TOTO_SP_WALLHUNG = Product(
    tag="PROD-TOTO-CT449CFGT60", brand="TOTO", model="CT449CFGT60#01",
    name="SP wall-hung elongated bowl, CeFiONtect, Cotton White",
    source="TOTO USA product listing and specification sheet, read 2026-09-06. Bowl only -- "
           "the in-wall tank and carrier is PROD-TOTO-WT173M, ordered with it. Rimless "
           "(CEFIONTECT glaze, no rim channel), 1.28/0.9 gpf dual flush.",
)
TOTO_DUOFIT_WT173M = Product(
    tag="PROD-TOTO-WT173M", brand="TOTO", model="WT173M",
    name="DuoFit in-wall tank and carrier system, 2x6 depth",
    source="TOTO USA DuoFit specification, read 2026-09-06. Carries the concealed WASHLET+ "
           "supply connection a Geberit Duofix does not. The wall must carry an 880 lb point "
           "load and the bay is purpose-framed with a header and sill -- see FX-TOILET-WH's "
           "``carrier_bay_width`` (19 3/4\") and resolve/framing/carriers.py. DEPTH IS A "
           "DIFFERENT PART NUMBER, not an adjustment: confirm the 2x6 variant on the order.",
)
TOTO_CARLYLE_II = Product(
    tag="PROD-TOTO-CST614CEFGAT40", brand="TOTO", model="CST614CEFGAT40#01",
    name="Carlyle II one-piece skirted elongated toilet, WASHLET+ ready, Cotton White",
    source="TOTO USA specification sheet, read 2026-09-06. One-piece skirted, 1.28 gpf "
           "Tornado Flush, CEFIONTECT. The ``AT40`` in the number is the WASHLET+ readiness "
           "(concealed supply for the S5 seat, PROD-TOTO-SW3446).",
)
TOTO_AQUIA_IV = Product(
    tag="PROD-TOTO-CST446CEMGN", brand="TOTO", model="CST446CEMGN#01",
    name="Aquia IV two-piece skirted dual-flush toilet, Cotton White",
    source="TOTO USA specification sheet, read 2026-09-06. Skirted trapway, 1.28/0.8 gpf "
           "dual flush, CEFIONTECT, DYNAMAX TORNADO FLUSH. ** THIS SKU IS REGULAR HEIGHT "
           "(14 15/16\" rim), NOT comfort height ** -- if universal height is wanted across "
           "the two, that is a different suffix and must be confirmed with the supplier "
           "before ordering. Two of these: RM-S-BATH1 and RM-S-SUITEBATH.",
)
TOTO_DRAKE = Product(
    tag="PROD-TOTO-CST776CEFG", brand="TOTO", model="CST776CEFG#01",
    name="Drake two-piece elongated toilet, Cotton White",
    source="TOTO USA specification sheet, read 2026-09-06. 1.28 gpf Tornado Flush and the "
           "same CEFIONTECT glaze as the showpieces; what it gives up is the skirt, which is "
           "why it is in the attic guest bath and the basement rather than on the main floor.",
)
TOTO_WASHLET_S5 = Product(
    tag="PROD-TOTO-SW3446", brand="TOTO", model="SW3446#01",
    name="WASHLET S5 bidet seat, instantaneous heater, Cotton White",
    source="TOTO USA specification sheet, read 2026-09-06. Tankless instantaneous water "
           "heater (no reservoir) and PREMIST, which wets the bowl before use and is a "
           "direct cleanability win. Needs a GFCI receptacle at the toilet, 6-12\" AFF, and "
           "draws ~1.2-1.4 kW while heating -- one 20 A circuit per bath, not both ganged. "
           "The C5/C2 seats are DISCONTINUED; remaining stock is clearing at inflated "
           "prices, so do not substitute one. The S7A adds a motorised lid, which on a "
           "cleanability brief is a negative.",
)
KOHLER_CACHET_SEAT = Product(
    tag="PROD-KOHLER-K-4636", brand="Kohler", model="K-4636-0",
    name="Cachet Quiet-Close elongated toilet seat, White",
    source="Kohler product listing, read 2026-09-06. Quiet-Close, Quick-Release for "
           "cleaning, Grip-Tight bumpers. ** FIT-CHECK BEFORE BUYING FOUR: ** TOTO's "
           "elongated rim profile differs from Kohler's and a lip at the rear corners is "
           "exactly the crevice quick-release exists to remove. The same-brand answer is "
           "TOTO SS234#01 at roughly five times the price.",
)

# --- Faucets, valves and showering ------------------------------------------------------
#
# ** SINGLE-HOLE ON ALL EIGHT LAVATORIES, NO EXCEPTIONS. ** A widespread is three deck
# penetrations and three seams in the splash zone; a single-hole is one. It is also cheaper
# in brushed nickel and it triples the drilling labour for a worse-cleaning result. This puts
# a requirement on the TOP order that has to be written down: order every vanity top DRILLED
# SINGLE-HOLE. Field-drilling a cast top chips it and voids its warranty.
DELTA_ARVO_LAV = Product(
    tag="PROD-DELTA-15840LF-SP", brand="Delta", model="15840LF-SP",
    name="Arvo single-hole bathroom faucet, SpotShield Brushed Nickel",
    source="Delta Faucet product page, read 2026-09-06. Single-hole, 7 15/16\" spout height, "
           "ships with a deck plate that covers a 3-hole 4\" top -- which is the recovery "
           "from the likeliest ordering error and part of why it was chosen. ** VERIFY the "
           "arc against the bar bowl's and the attic lav's actual depth ** before ordering "
           "eight; a low-spout faucet is the substitute in a shallow bowl.",
)
DELTA_ESSA_KITCHEN = Product(
    tag="PROD-DELTA-9113-AR-DST", brand="Delta", model="9113-AR-DST",
    name="Essa single-handle pull-down kitchen faucet, Arctic Stainless",
    source="Delta Faucet product page, read 2026-09-06. MagnaTite magnetic docking and "
           "DIAMOND Seal. The docking is the whole selection: it has no wear surface, where "
           "a counterweight-and-collar is the mechanism behind the near-universal "
           "five-to-ten-year sagging-wand complaint. ** VERIFY spout reach against the 33\" "
           "double-bowl layout ** if the faucet hole is offset from the divider.",
)
MOEN_ADLER_LAUNDRY = Product(
    tag="PROD-MOEN-87233SRS", brand="Moen", model="87233SRS",
    name="Adler single-handle pull-down kitchen faucet, Spot Resist Stainless",
    source="Moen product page, read 2026-09-06. Serves FX-M-LAUNDRY-SINK. ** THE BRIEF "
           "CANNOT BE MET AS WRITTEN: ** no mainstream pull-down sprayer is hose-threaded "
           "(sprayheads use proprietary threads) and every 3/4\"-hose-threaded utility "
           "faucet is a two-handle rigid spout with no spray. Take the sprayer and TEE A "
           "1/2\" HOSE BIBB OFF THE COLD AT THE LAUNDRY BOX -- a rough-in item that has to "
           "reach the plumber before the wall closes.",
)
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
           "not negotiable and why this part is not the one to import.",
)
DELTA_T14459_TRIM = Product(
    tag="PROD-DELTA-T14459-SS", brand="Delta", model="T14459-SS",
    name="Ashlyn Monitor 14 tub-and-shower trim with H2Okinetic head and spout, Stainless",
    source="Delta Faucet product page, read 2026-09-06. A COMPLETE trim -- valve trim, "
           "showerhead and tub spout in one box -- which removes the spout-matching problem "
           "and means the two 60\" combos need no separately specified head. Pressure "
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
           "utilitarian rather than designed; that is the trade.",
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
           "trim to put a handshower in a basement sauna rinse is bad value.",
)
DELTA_TRINSIC_FILLER = Product(
    tag="PROD-DELTA-T2759-SS", brand="Delta", model="T2759-SS",
    name="Trinsic 3-hole deck-mount Roman tub filler trim, Stainless",
    source="Delta Faucet product page, read 2026-09-06. Owner's call 2026-09-06: three "
           "holes, NO handshower -- the cleaner deck, and the shower next door already has "
           "one. ** THAT CHOICE DELETES A CODE PROBLEM: ** a DECK-mounted handshower needs "
           "an integral atmospheric vacuum breaker to ASME A112.18.1 at a required elevation "
           "above the flood rim, and with no deck handshower that condition does not exist. "
           "Roughs on PROD-DELTA-R2707. ** Delta's own page confusingly claims this trim "
           "includes a hand shower, which contradicts it being 3-hole trim -- confirm before "
           "ordering. **",
)
DELTA_R2707_ROUGH = Product(
    tag="PROD-DELTA-R2707", brand="Delta", model="R2707",
    name="Roman tub rough-in valve body, 3-hole",
    source="Delta Faucet product page, read 2026-09-06. ** ORDER IT WITH THE TRIM. ** They "
           "ship from different warehouses and the body is needed months earlier; ordering "
           "trim alone is the classic failure here. It roughs into the SL-M-TUBDK deck, "
           "which caps the stack-up at 2 1/8\" rough plus 1/4\"-1 1/4\" finished and needs "
           "the 20\" x 15\" access panel Kohler's own drawing calls for -- serving this "
           "body, the K-7272 waste-and-overflow and the Bask GFCI connection at once. "
           "Showing out of stock on Delta's site when read.",
)
KOHLER_CAXTON_BASIN = Product(
    tag="PROD-KOHLER-K-20000", brand="Kohler", model="K-20000-0",
    name="Caxton rectangle undermount bathroom sink, White",
    source="Kohler product page, read 2026-09-06. Chosen OVER the Verticyl K-2882 the 48\" "
           "and 54\" vanities were first specified against, and the reason is the reason for "
           "the whole brief: Verticyl's selling point is vertical sides and tight corner "
           "radii, which is exactly what stops a cloth reaching the corner in one pass. "
           "Caxton's softer sweep wipes in one motion. It is the less designed bowl and the "
           "more cleanable one.",
)
SWAN_CONTOUR_TOP = Product(
    tag="PROD-SWAN-CONTOUR", brand="Swan", model="Contour",
    name="Contour one-piece solid-surface vanity top with integral bowl",
    source="Swan product literature, read 2026-09-06. ** THIS REPLACES CULTURED MARBLE ON "
           "THE FOUR SMALL VANITIES AND IT IS THE BEST CLEANABILITY-PER-DOLLAR MOVE IN THE "
           "SCOPE. ** Same integral coved bowl, same price band, but cultured marble is a "
           "~0.020\" clear gelcoat over filled polyester: hot hair tools scorch it "
           "permanently, it yellows in sun, and a refinish lays down a THINNER gelcoat than "
           "the original. Compression-moulded solid surface is homogeneous -- a scratch or a "
           "scorch sands back to new instead of cutting through a skin -- and its matte "
           "finish reads better against white oak and hides water spots. ** ORDER DRILLED "
           "SINGLE-HOLE, IN WRITING: ** it ships single-hole with 4\"/8\" knockouts you "
           "simply never break out, and plugging holes with a deck plate defeats the whole "
           "reason for going single-hole.",
)

# --- The sauna ---------------------------------------------------------------------------
#
# ** THE 9 kW THIS HOUSE CARRIED WAS UNDERSIZED, AND THAT IS THE FINDING, NOT THE BRAND. **
# Every manufacturer's own table puts 9 kW at 283-494 cf. RM-B-SAUNA is 555 cf, and the glass
# partition notes/sauna_shower_basement_detail.md specifies adds notional volume on top. The
# rule of thumb (1 kW per 45-50 cf) wants 11-12 kW; HUUM voids its warranty outright if the
# room is dimensioned wrong. 10.5 kW is the honest answer and it cascades into CKT-SAUNA.
#
# The Cilindro is FLOOR-STANDING, 45" tall, and that matters to the model: EQ-T-SAUNA-HEATER
# carried an 18" x 16" x 30" body, and 30" is a height NO heater in this class has. Every
# listing researched wants 22-28" of width including clearance to combustibles and 35-47" of
# CLEAR SPACE ABOVE. There is no niche in this model -- the placeholder was the heater itself
# -- so this is a straight body-size correction, not a framing change.
HARVIA_CILINDRO_PC110E = Product(
    tag="PROD-HARVIA-PC110E", brand="Harvia", model="PC110E",
    name="Cilindro 10.5 kW electric sauna heater, floor standing, stainless",
    source="Harvia/Finnleo published specifications, read 2026-09-06. Rated 141-636 cf, "
           "which brackets RM-B-SAUNA's 555 cf where a 9 kW does not. ETL listed. Carries "
           "264 lb of stone -- two to six times anything near its price, and rock mass is "
           "what decides loyly quality and whether the room recovers when someone opens the "
           "door. 45\" tall, 3.94\" clearance all round, 37.4\" headroom above, 78\" "
           "minimum ceiling. ** NO BUILT-IN CONTROL VARIANT EXISTS: ** the Xenio CX170 "
           "(PROD-HARVIA-CX170) is mandatory, not an accessory. It is cheaper than a Virta "
           "HL90E that holds less than half the stone and is also undersized.",
)
HARVIA_XENIO_CX170 = Product(
    tag="PROD-HARVIA-CX170", brand="Harvia", model="Xenio CX170",
    name="Xenio CX170 sauna control unit",
    source="Harvia published specifications, read 2026-09-06. Mandatory with PC110E -- the "
           "heater has no onboard control. Mounts OUTSIDE the hot room.",
)
CARIITTI_FIBRE_KIT = Product(
    tag="PROD-CARIITTI-VPL30-G211", brand="Cariitti", model="Premium Glass Fiber 8-spot",
    name="Premium glass-fibre sauna lighting kit, 8 ferrules, dimmable 2700K projector",
    source="Cariitti published specifications, read 2026-09-06. ** NOTHING SOLD IN THE US IS "
           "BOTH IP65 AND 125 C, ** which is what picks the product: LED sconces top out at "
           "60-93 C and lamp-and-shade fixtures are limited by their cable. Glass fibre is "
           "rated 180 C and carries NO CURRENT, so the ferrules go in the CEILING and even "
           "over the heater while the projector lives outside the hot room. Never recess a "
           "can in a hot room -- it penetrates the vapour barrier at the hottest point and "
           "puts a driver in the hot cavity. ** CE-MARKED, NOT NRTL-LISTED: ** if the "
           "inspector wants an NRTL listing in the hot room this is the most likely permit "
           "snag in the house. Confirm in writing before ordering.",
)

# --- Kitchen and hardware -----------------------------------------------------------------
#
# ** POLAND IS A 'DON'T', AND THE OWNER'S OWN MILL IS WHY. ** Section 232 puts 25% on wooden
# cabinets, vanities AND PARTS THEREOF from 2025-10-14 (the scheduled 50% was delayed to
# 2027-01-01; the EU cap is 15%), EU carcasses are 600 mm deep and 870 mm high against a US
# 24" and 34.5", there is no warranty recourse across an ocean, and the whole reason to
# import is a wood front at a low price -- which $2/sf white oak off family land, in 4/4 and
# 8/4 up to 18" wide, beats outright with no lead time. If you want European engineering, buy
# the HARDWARE (Blum/Hettich) and put it in domestic boxes.
#
# SEKTION carcasses are manufactured in the US, so the box half of the kitchen is
# structurally insulated from the 25% while nearly every RTA competitor eats it. Fronts are
# imported. Time the order to the IKEA kitchen event, historically Feb-April.
IKEA_SEKTION = Product(
    tag="PROD-IKEA-SEKTION", brand="IKEA", model="SEKTION",
    name="SEKTION frameless kitchen cabinet system, US-manufactured carcasses",
    source="IKEA US product literature and 2025-26 tariff position, read 2026-09-06. The "
           "carcass system only -- fronts are PROD-IKEA-VOXTORP. Frameless, which is what "
           "makes a 24\" box give a 22 1/2\" clear opening and is why the Rev-A-Shelf "
           "5374-24FL swing-out in plan/placeables.py fits at all.",
)
IKEA_VOXTORP_WHITE = Product(
    tag="PROD-IKEA-VOXTORP-WH", brand="IKEA", model="VOXTORP matt white",
    name="VOXTORP matt white slab door and drawer front",
    source="IKEA US product listing, read 2026-09-06. Best cleanability of the slab lines: "
           "matte foil, wipes with a damp cloth, no fingerprints. A SLAB, not a shaker -- "
           "the inside corner of a shaker rail is where cooking grease lives, which is why "
           "AXSTAD loses on the top criterion despite being durable. RINGHULT high gloss is "
           "the worst possible surface beside an induction range and BODBYN's painted MDF "
           "chips (IKEA sells touch-up paint for exactly that reason). ** WATCH THE ONE "
           "WEAKNESS: ** the integrated edge pull collects grease on the underside where you "
           "cannot see it, which is why real pulls (PROD-TOPKNOBS-BAR-SS) are still bought. "
           "Do NOT pay IKEA $459 a door for VEDHAMN oak when you mill oak.",
)
# ** THE DRAWER BOX IS A SEPARATE PURCHASE FROM THE CABINET, AND THAT IS THE POINT. ** A
# SEKTION base frame arrives as a box with no interior: what goes in it is bought by the
# drawer, which is why the kitchen's drawer decision is a product here and not a geometry in
# the model. The model has no drawer vocabulary at all — one solid carcass per cabinet — so
# WHICH boxes are drawer stacks is recorded in prose, in prices.toml's SEKTION block and in
# plan/placeables.py beside the instances.
IKEA_MAXIMERA = Product(
    tag="PROD-IKEA-MAXIMERA", brand="IKEA", model="MAXIMERA",
    name="MAXIMERA soft-close full-extension drawer, high/medium/low",
    source="IKEA US product literature, read 2026-09-11. ** MAXIMERA, NOT FORVARA: ** "
           "FORVARA is the basic drawer and is what a SEKTION base ships with if nobody "
           "chooses; MAXIMERA is full-extension with integrated soft-close, and full "
           "extension is the whole argument for a drawer base over a door base — a drawer "
           "you cannot pull all the way out is a cupboard with a lid. Fronts sit on the "
           "5/10/15 in. ladder, so a 30 in. base is 5+10+15 or 10+10+10 and the fronts "
           "line up across a run either way. Fits every base and pantry width in this "
           "kitchen; the two it does NOT fit are a 12 in. base and a corner base, and this "
           "house has neither. Pulls are PROD-TOPKNOBS-BAR-SS, one size UP on a drawer.",
)
TOPKNOBS_BAR_PULL = Product(
    tag="PROD-TOPKNOBS-BAR-SS", brand="Top Knobs", model="Solid Bar Pull, SS304",
    name="Round solid bar cabinet pull, stainless steel 304",
    source="Top Knobs catalog, read 2026-09-06. SS304 is the same alloy as the appliances so "
           "it matches without a finish-code hunt, and there is NO PLATING TO WEAR THROUGH -- "
           "budget plated-brass 'satin nickel' wears to yellow at the thumb contact point in "
           "five to eight years, which is the failure mode this buys out of. ** FORM IS THE "
           "CLEANABILITY ARGUMENT: ** a ROUND bar at >=1 1/4\" standoff has no flat top face "
           "to hold aerosolised oil and a hand fits under it, which is why bar pulls dominate "
           "commercial kitchens; a square bar has that top face, and tab/edge pulls are the "
           "worst of all -- grease goes behind the tab into a gap no cloth reaches. Size "
           "ladder, pull ~1/3 of the front's width and one size UP on drawers: 96 mm small "
           "doors, 128 mm larger doors, 160 mm base drawers, 224 mm wide drawers and the "
           "sink-base false front, 12\"+ on the 24\" pantry doors.",
)
SCHLAGE_LATITUDE = Product(
    tag="PROD-SCHLAGE-LATITUDE-619", brand="Schlage", model="Latitude, square rose, 619",
    name="Latitude lever on square rose, satin nickel (619)",
    source="Schlage catalog, read 2026-09-06. ** SQUARE ROSE IS THE RIGHT CALL FOR A "
           "TRIMLESS HOUSE ** -- a round rose on a flush jamb reads as a leftover -- and "
           "that upcharge is essentially what Schlage's Custom collection sells. The lever "
           "tip RETURNS TO THE DOOR, which matters for a non-code reason: a straight tip "
           "catches pockets, belt loops and dog leashes. In stock across the Twin Cities and "
           "replaceable in fifteen years without a hunt, which Karcher/FSB are not -- "
           "European backsets, thin US dealer network, and a broken lever in year twelve is "
           "a special order from Europe. ** FINISH-CODE TRAP: satin nickel is US15 = 619; "
           "US15A is ANTIQUE nickel and a different colour. ** Buy levers and hinges from "
           "the same finish family and the same lot.",
)
YALE_ASSURE_2 = Product(
    tag="PROD-YALE-ASSURE-2-WIFI", brand="Yale", model="Assure Lock 2, Wi-Fi, keyed",
    name="Assure Lock 2 keypad deadbolt with Wi-Fi, keyed, satin nickel",
    source="Yale Home product listing, read 2026-09-06. ONE smart lock, on the door actually "
           "used -- four of them quadruples battery maintenance to solve a problem already "
           "solved once. Take the KEYED version, not key-free: in Minnesota you want a "
           "mechanical override. ** USE LITHIUM AA CELLS. ** Every keypad-lock cold-weather "
           "complaint traces to alkalines falling off a cliff below 0 F; lithium is rated to "
           "-40 F. It is a $12 fix nobody makes. The other exterior openings take a plain "
           "deadbolt-and-lever, KEYED ALIKE AT TIME OF PURCHASE -- rekeying later costs more "
           "than the discount.",
)

# --- Surfaces -----------------------------------------------------------------------------
#
# Named here rather than only on the Material because a slab and a tile are BOUGHT, with a
# model number, a finish and a lot -- and ``Material.product_ref`` exists for exactly this.
# These are the first Materials in the repo to use it.
SILESTONE_ET_CALACATTA = Product(
    tag="PROD-SILESTONE-ET-CALACATTA-GOLD", brand="Silestone (Cosentino)",
    model="Et Calacatta Gold, 3 cm, polished",
    name="Et Calacatta Gold engineered quartz slab, 3 cm",
    source="Cosentino published literature, read 2026-09-06. ** HybriQ: <=40% crystalline "
           "silica, against 90-95% for conventional quartz including Cambria. ** Cal/OSHA "
           "voted 2026-05-21 to initiate a prohibition on fabricating engineered stone over "
           "1% silica after 592 silicosis cases, 65 lung transplants and 31 deaths among "
           "California fabricators since 2019; Australia banned it outright. There is NO "
           "Minnesota or federal ban and quartz buys with zero friction here in 2026 -- but "
           "the low-silica choice is also the cheapest, which makes it free to take. 3 cm, "
           "no debate: 2 cm's saving evaporates into a plywood subtop plus a laminated edge "
           "and it cannot do a good mitre. Eased edge is included; a 2-3\" mitred apron on "
           "the exposed run is the most visible upgrade in a minimalist kitchen, and a "
           "waterfall is $700-1200 to kill knee space and date the room. ** THE #1 CAUSE OF "
           "YELLOWING IS NOT UV, IT IS HIGH-pH CLEANERS ** -- bleach, ammonia, glass cleaner, "
           "degreasers, scouring powder and melamine sponges all yellow light quartz across "
           "every brand. #2 is heat scorch, which is irreversible. A warm off-white with "
           "veining hides both where a stark solid white shows them worst.",
)
MARAZZI_MODERN_FORMATION = Product(
    tag="PROD-MARAZZI-MF01", brand="Marazzi", model="Modern Formation Peak White MF01",
    name='Modern Formation Peak White 24x24 matte rectified porcelain floor tile',
    source="Marazzi/Daltile specification sheet, read 2026-09-06. DCOF >= 0.42 (ANSI "
           "A326.3), absorption < 0.5%, RECTIFIED, USA made. ** 'RECTIFIED' IS THE "
           "HIGHEST-LEVERAGE WORD ON THE PAGE: ** ANSI A108.02 4.3.8.1 gives tile with any "
           "side over 15\" a 1/8\" minimum joint if rectified and 3/16\" if not, so a "
           "non-rectified 24x24 gives the same look and THREE TIMES THE GROUT. Confirm it on "
           "the spec sheet, not the sales copy. The price of rectified is that square "
           "arrises show lippage -- budget a levelling-clip system and a flat substrate, not "
           "fancier tile. ** V3 HIGH SHADE VARIATION: lay out eight pieces from a full box "
           "before committing. ** The mudroom takes the same tile in TEXTURED for a higher "
           "wet DCOF against snowmelt, salt and grit.",
)
TILEBAR_BRONX_WHITE = Product(
    tag="PROD-TILEBAR-BRONX-WHITE", brand="TileBar", model="Bronx White 12x24 matte",
    name='Bronx White 12x24 matte rectified porcelain wall tile',
    source="TileBar product page, read 2026-09-06. Rectified, DCOF 0.5. A flat quiet white "
           "with NO VEINING to fight the oak and no pattern repeat to manage. Smooth matte "
           "deliberately -- a DEEPLY TEXTURED matte holds soap film, and a gloss glaze on a "
           "wet wall shows every drip.",
)
SCHLUTER_KERDI_LINE_VARIO = Product(
    tag="PROD-SCHLUTER-KERDI-LINE-VARIO", brand="Schluter", model="KERDI-LINE-VARIO",
    name="KERDI-LINE-VARIO cut-to-length linear shower drain, brushed stainless",
    source="Schluter product literature, read 2026-09-06. Roughly a third the price of the "
           "classic KERDI-LINE. ** BRUSHED STAINLESS OVER MATTE BLACK, AND IT IS ALSO "
           "CHEAPER: ** Schluter's 'matte graphite black' is a PAINTED COATING ON ALUMINIUM "
           "that chips and exposes bright raw metal at a cut end, where satin anodised is "
           "through-surface. Take the PERFORATED grate, not the solid tileable one -- that "
           "one looks best and cleans worst.",
)

INTERIOR_PRODUCTS = (
    TOTO_SP_WALLHUNG, TOTO_DUOFIT_WT173M, TOTO_CARLYLE_II, TOTO_AQUIA_IV, TOTO_DRAKE,
    TOTO_WASHLET_S5, KOHLER_CACHET_SEAT,
    DELTA_ARVO_LAV, DELTA_ESSA_KITCHEN, MOEN_ADLER_LAUNDRY,
    DELTA_MULTICHOICE_ROUGH, DELTA_T14459_TRIM, SPEAKMAN_HOTEL_HEAD, MOEN_ENGAGE_MAGNETIX,
    DELTA_TRINSIC_FILLER, DELTA_R2707_ROUGH,
    KOHLER_CAXTON_BASIN, SWAN_CONTOUR_TOP,
    HARVIA_CILINDRO_PC110E, HARVIA_XENIO_CX170, CARIITTI_FIBRE_KIT,
    IKEA_SEKTION, IKEA_VOXTORP_WHITE, IKEA_MAXIMERA, TOPKNOBS_BAR_PULL,
    SCHLAGE_LATITUDE, YALE_ASSURE_2,
    SILESTONE_ET_CALACATTA, MARAZZI_MODERN_FORMATION, TILEBAR_BRONX_WHITE,
    SCHLUTER_KERDI_LINE_VARIO,
    *LIGHTING_PRODUCTS,
)
