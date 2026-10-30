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
from plan.products_showering import SHOWERING_PRODUCTS
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
# ``CT426CFGT40`` is the BOWL ONLY. The in-wall tank is a second line on the order, and the
# reason it is TOTO's DuoFit rather than a Geberit Duofix is the bidet seat: a WASHLET+ routes
# its supply CONCEALED through the bowl, and only TOTO's own carrier has that connection. Buy
# Geberit and a braided hose crosses the finished tile forever. Both frames are within an
# eighth of 500 mm across the uprights, so FX-TOILET-WH's ``carrier_bay_width`` holds either.
TOTO_AP_WALLHUNG = Product(
    tag="PROD-TOTO-CT426CFGT40", brand="TOTO", model="CT426CFGT40#01",
    name="AP wall-hung elongated bowl, CeFiONtect, Cotton White",
    source="TOTO SS-02352 v.01, read 2026-10-21: 14 15/16 x 21 1/4 in. overall. Bowl only -- "
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
MOEN_ALIGN_FILLER = Product(
    tag="PROD-MOEN-T393", brand="Moen", model="T393",
    name="Align three-hole Roman tub trim, chrome, without handshower",
    url="https://shop.moen.com/products/t393",
    source="Moen t393sp.pdf Rev. 1/18, read 2026-10-22. Deck mounted on "
           "PROD-MOEN-4794; trim and rough ordered together. Independent of tub brand: "
           "mounts on the constructed foot deck, not the Kohler shell. Final holes "
           "follow delivered trim and the actual tub template.",
)
MOEN_4794_ROUGH = Product(
    tag="PROD-MOEN-4794", brand="Moen", model="4794",
    name="M-PACT adjustable three-hole Roman tub rough, cold-expansion PEX adapters",
    url="https://shop.moen.com/products/4794",
    source="Moen 4794sp.pdf Rev. 9/15, read 2026-10-22: 10 in. minimum centres, "
           "2 3/4 in. maximum rough deck plus 1 1/4 in. finish; 24 in. hoses, "
           "1/2 in. PEX and included ASTM F1960 cold-expansion adapters. "
           "Rated 13 gpm at 45 psi, not a guaranteed installed flow. Requires an "
           "ASSE-conforming temperature-limiting device; manufacturer identifies "
           "separately purchased 104465 (ASSE 1070). Keep valve and hose connections "
           "serviceable through the foot-bay access panel. "
           "https://assets.moen.com/shared/docs/product-specifications/4794sp.pdf",
)
DELTA_ARVO_LAV_CHROME = Product(
    tag="PROD-DELTA-15840LF", brand="Delta", model="15840LF",
    name="Arvo single-hole bathroom faucet, chrome — Bath2",
    url="https://www.deltafaucet.com/bathroom/product/15840LF.html",
    source="Delta product page, read 2026-10-22. Chrome variant of the existing "
           "15840LF-SP selection, Bath2 only; retain single-hole drilling without deck plate.",
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
# RM-M-BATH2's one-piece deck, faces, splash, vanity top and stool (notes/bath2_tub_deck_finish.md),
# and RM-S-PLANT's four window stools (2026-10-22).
CORIAN_GLACIER_WHITE = Product(
    tag="PROD-CORIAN-GLACIER-WHITE", brand="Corian", model="Glacier White",
    name="Corian Glacier White or HI-MACS/Staron equal, 12 mm acrylic solid surface, shop-fabricated",
    source="Owner selection 2026-10-22, against a physical chip beside Swanstone Carrara. "
           "HI-MACS or Staron solid white of the same 12 mm acrylic class is an accepted "
           "equivalent. One fabricator and one lot for every Bath2 piece and the four "
           "plant-room window stools (moved off quartz for UV, 2026-10-22). Fabrication per "
           "Corian bulletins: >= 1/2 in. inside radius on L/U pieces, >= 3/16 in. on "
           "cutouts, router-cut only (notes/bath2_tub_deck_finish.md).",
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
           "carcass system only; kitchen fronts are PROD-IKEA-AXSTAD-WH. Frameless, which is what "
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
# Frame, front and drawer mechanism remain separate purchases. The configured symbols
# now record the kitchen's door/drawer divisions; prices.toml carries installed allowances.
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
           "kitchen where specified. The B12 and carousel corners use doors, not drawer "
           "boxes. Kitchen fronts and hardware are AXSTAD/BAGGANÄS (2026-10-22).",
)
TOPKNOBS_BAR_PULL = Product(
    tag="PROD-TOPKNOBS-BAR-SS", brand="Top Knobs", model="Solid Bar Pull, SS304",
    name="Round solid bar cabinet pull, stainless steel 304 (prior kitchen selection)",
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
IKEA_AXSTAD_WHITE = Product(
    tag="PROD-IKEA-AXSTAD-WH", brand="IKEA", model="AXSTAD matte white",
    name="AXSTAD matte white recessed-panel kitchen doors and drawer fronts",
    url="https://www.ikea.com/us/en/p/axstad-door-matte-white-50426048/",
    source="Owner selection 2026-10-22 replaces VOXTORP in the kitchen and connected living "
           "run. 3/4-inch fronts, 1/8-inch nominal reveals. Solid 15x20 doors above cold "
           "storage; AXSTAD glass is only listed in 30/40-inch heights, so glass is deferred.",
)
IKEA_BAGGANAS_KNOB_BLACK = Product(
    tag="PROD-IKEA-BAGGANAS-KNOB-BLACK", brand="IKEA", model="BAGGANÄS black knob",
    sku="903.384.17", name="BAGGANÄS black knob, 13/16-inch diameter",
    url="https://www.ikea.com/us/en/p/bagganaes-knob-black-90338417/",
    source="IKEA US read 2026-10-22: diameter 13/16, projection 15/16 inch; $7/2-pack. "
           "Selected for kitchen/living cabinet doors, at opening-edge rails.",
)
IKEA_BAGGANAS_PULL_BLACK = Product(
    tag="PROD-IKEA-BAGGANAS-PULL-BLACK", brand="IKEA", model="BAGGANÄS black handle",
    sku="803.384.13", name="BAGGANÄS black pull, 5 5/8 inches, with washers",
    url="https://www.ikea.com/us/en/p/bagganaes-handle-black-80338413/",
    source="IKEA US read 2026-10-22: length 5 5/8, hole spacing 5 1/16, projection 1 1/4, "
           "width 3/8 inch; $9/2-pack. One horizontal pull per kitchen drawer front. "
           "Use the included washers. The custom garage retains its lift/roll-up operation.",
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
MSI_Q_QUARTZ_SPECKLED = Product(
    tag="PROD-MSI-Q-QUARTZ-SPECKLED-WHITE", brand="MSI (M S International)",
    model="Q Quartz, Frost White, Group 1, 3 cm, polished",
    name="MSI Q Quartz Frost White engineered quartz slab, 3 cm, Group 1",
    source="Pencilled 2026-10-22 for cost: Frost White, with Iced White and Sparkling White as "
           "the consistently cheapest speckled whites. Public sources read 2026-10-22: Granite "
           "Selection lists MSI Q Quartz Frost White at $35-45/SF retail; no MSI source "
           "confirmed the Group 1 price level, and no MSI crystalline-silica figure was "
           "published in what was found. Conventional quartz runs ~90% silica, against <=40% "
           "for Silestone HybriQ, which the 2026-09-06 pick used. ** Get the MSI SDS and the "
           "fabricator's silica-control plan before cutting. ** Confirm the colour and the "
           "price level on the MSI sheet at order. Eased edge and polish are standard. ** THE "
           "#1 CAUSE OF YELLOWING IS HIGH-pH CLEANERS ** -- bleach, ammonia, glass cleaner, "
           "degreasers, scouring powder and melamine sponges. #2 is heat scorch, which is "
           "irreversible.",
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

KATELAUREL_ESTERO = Product(
    tag="PROD-KATELAUREL-221484", brand="Kate and Laurel", model="221484",
    name="Estero arch wall mirror with shelf, 20 x 28, gold",
    url="https://www.kateandlaurel.com/products/estero-metal-framed-arch-wall-mirror-with-shelf",
    source="Home Depot listing (HD 221484), read 2026-10-03: 20.12\" W x 28\" H x 5.5\" D, "
           "gold metal frame, MDF back, 4\" x 20\" shelf along the bottom. Retailer "
           "dimensions only; confirm on delivery. RM-S-SUITEBATH, over FX-S-SUITEBATH-LAV.",
)

DURAVIT_DCODE_070545 = Product(
    tag="PROD-DURAVIT-07054500002", brand="Duravit", model="07054500002",
    name="D-Code wall-mounted basin, single central faucet hole, white",
    source='Duravit US 07054500002, read 2026-10-21: 17 3/4 x 13 3/8 x 5 3/4 in.; '
           'interior 15 3/8 x 8 1/2 in.; overflow, glazed underside, cUPC listed. '
           'Two 240 mm-spaced mounting holes, 55 mm below rim. Solid 4x10 blocking '
           'on W-M-STOS, independent of the 3 in. stack. Duravit B.2 B21010001U10, '
           'single hole without deck plate; exposed 1 1/4 in. tubular P-trap. '
           'Installation specification: notes/main_bath1_basin_spec.md.',
)

DURAVIT_B2_POWDER_FAUCET = Product(
    tag="PROD-DURAVIT-B21010001U10", brand="Duravit", model="B21010001U10",
    name="B.2 S single-hole basin mixer with pop-up, chrome",
    source='Duravit US, read 2026-10-21: 4 in. reach, 3 5/8 in. outlet above deck, '
           '6 in. overall height, adjustable aerator, 3/8 in. compression hoses, '
           'WaterSense, cUPC; US pop-up/drain version. D-Code 070545 recommended mixer '
           'family B21010001. Powder room only, replacing the Arvo allowance here. '
           'https://pro.duravit.us/pro/html/default/402880943a1b6e1b013a1bd282eb0051.us-en.html'
           '?ncat=faucets&nser=1821&product=4147387',
)

# The toe joint of the PVC base in the four tile baths and the plant room's rubber cove base:
# white, to match the painted base above it. Not paintable, and need not be.
GE_SILICONE_2_KB_WHITE = Product(
    tag="PROD-GE-2812565", brand="GE", model="2812565",
    name="Advanced Silicone 2 Kitchen & Bath sealant, white, 10.1 oz",
    url="https://www.homedepot.com/p/317778410",
    source="Home Depot Internet # 317778410, model 2812565, read 2026-10-29: 100% silicone, "
           "mold-free, waterproof, shower-ready in 30 min.",
)

INTERIOR_PRODUCTS = (
    DURAVIT_DCODE_070545, DURAVIT_B2_POWDER_FAUCET, TOTO_AP_WALLHUNG, TOTO_DUOFIT_WT173M, TOTO_CARLYLE_II, TOTO_AQUIA_IV, TOTO_DRAKE,
    TOTO_WASHLET_S5, KOHLER_CACHET_SEAT,
    DELTA_ARVO_LAV,
    *SHOWERING_PRODUCTS,
    MOEN_ALIGN_FILLER, MOEN_4794_ROUGH, DELTA_ARVO_LAV_CHROME,
    KOHLER_CAXTON_BASIN, SWAN_CONTOUR_TOP, CORIAN_GLACIER_WHITE,
    HARVIA_CILINDRO_PC110E, HARVIA_XENIO_CX170, CARIITTI_FIBRE_KIT,
    IKEA_SEKTION, IKEA_VOXTORP_WHITE, IKEA_MAXIMERA, TOPKNOBS_BAR_PULL,
    IKEA_AXSTAD_WHITE, IKEA_BAGGANAS_KNOB_BLACK, IKEA_BAGGANAS_PULL_BLACK,
    SCHLAGE_LATITUDE, YALE_ASSURE_2,
    MSI_Q_QUARTZ_SPECKLED, MARAZZI_MODERN_FORMATION, TILEBAR_BRONX_WHITE,
    SCHLUTER_KERDI_LINE_VARIO, KATELAUREL_ESTERO, GE_SILICONE_2_KB_WHITE,
    *LIGHTING_PRODUCTS,
)
