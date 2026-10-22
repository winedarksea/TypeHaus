"""Catlin lighting products — the 2026-09-06 interior pass (→ plan/products_interior.py).

Split off its parent for the 500-line rule, and the subject splits cleanly: everything here
is a luminaire, a tape or a driver, and every one of them answers to two house rules that no
plumbing fixture does.

** THE HOUSE STANDARD IS 3000 K, AND NO INSTALL-TIME SELECTABLE MODULES. ** A 5CCT DIP
switch gets set wrong constantly, one can at 4000 K in a run of eight is a screaming defect,
and a dedicated phosphor gives better R9 than a warm/cool blend. Each deliberate exception
(4000 K over the work surfaces, BATH2's 5000 K day and 2700 K evening layers) is its own
schedule row. A USER-ADJUSTABLE fixture with a live control (tunable white, RGB) is allowed
(2026-10-12): it records its working CCT in ``cct_k`` and its range in ``source``.

** A DRIVER IS THE PART THAT DIES, NOT THE LED. ** Electrolytic capacitors are rated at 25 C
and halve their life per 10 C above it, so a 25,000-hour LED behind a captive driver in an
unventilated cavity is a 12-20 year fixture, not a lifetime one. Every choice below prefers a
replaceable lamp or an accessible, separately-purchasable driver over a sealed assembly, and
the illuminated-mirror exception and its controls are documented in plan/mirror_types.py.
"""

from __future__ import annotations

from typehaus.model import Product
from typehaus.library.track_lighting import MAGNETIC_TRACK_PRODUCTS

# --- Lighting -----------------------------------------------------------------------------
#
# The house standard is 3000 K everywhere it is not deliberately something else, and never
# an install-time selectable (DIP) module: see the module docstring.
LOTUS_LL4SR_CAN = Product(
    tag="PROD-LOTUS-LL4SR-30K-WH", brand="Lotus LED Lights", model="LL4SR-30K-WH",
    name='4" deeply regressed LED downlight, white trim, 3000K',
    source="Lotus LED Lights specification sheet, read 2026-09-06. 14.5 W, 900 lm, 3000 K, "
           "90+ CRI, wet + IP54, IC rated, airtight. ** THE BLACK BAFFLE THIS REPLACES WAS "
           "SOLVING GLARE THE EXPENSIVE WAY. ** A black baffle in a white ceiling reads as a "
           "row of dark holes and a ribbed baffle traps dust and shows a grey halo; a white "
           "DEEPLY REGRESSED reflector hides the source by geometry instead, so the trim "
           "disappears into the ceiling and wipes clean. Same SKU serves the wet locations, "
           "so there is no separate shower trim to colour-match.",
)
WESTGATE_VAPORTIGHT = Product(
    tag="PROD-WESTGATE-LVTE-4FT", brand="Westgate", model="LVTE-4FT-30-46W-MCTP",
    name="4' vaportight linear LED, IP66, cold rated",
    source="Westgate specification sheet, read 2026-09-06. ** THE COLD RATING IS THE WHOLE "
           "STORY. ** Almost every consumer LED shop light is rated to -4 F and some to +14 "
           "F; it is the DRIVER, not the LEDs -- LEDs are happier cold, but electrolytic ESR "
           "climbs sharply below rating. Vaportight/cold-storage is the category that "
           "reliably publishes a cold rating, because it sells into freezer warehouses. IP66 "
           "keeps sawdust and cobwebs outside and the sealed lens wipes clean. HARDWIRE IT: "
           "plug-in linkable cords crack in cold and that is where the failures happen. Set "
           "4000 K, not 5000 K -- 5000 K makes airborne sawdust glare.",
)

DOLRIA_PC0008 = Product(
    tag="PROD-DOLRIA-PC0008", brand="dolria", model="PC0008-20T-G",
    name="20-light cascading cluster chandelier, gold with bubble-crystal globes",
    url="https://www.amazon.com/dp/B0B5G5PJDF",
    source="Amazon listing B0B5G5PJDF, read 2026-09-23; the owner's pick, 'very similar, "
           "perhaps the same' as Wayfair's Latitude Run W118039723. 23\" canopy, wires "
           "3.9\"-156\" each, 20 integrated LED, 100 W, AC 110-240 V, remote dimming and "
           "colour, 'Specification Met: UL'. ** THE LISTING SAYS UL; THE FIXTURE MUST. ** "
           "NEC 110.2/110.3(B) - find the UL/ETL mark on the canopy before it goes up. ** "
           "NOT REPLACEABLE, AND ACCEPTED (2026-09-23): ** the driver sits in a canopy 27' "
           "up, so its failure is a scaffold in the well. The Kuzco Samar it replaces had "
           "3 x E26 for exactly that reason, but 14\" of fixture could not fill a 27' void "
           "and 120\" of wire could not reach the hang.",
)
FLYACHILLES_DJ3616_2L = Product(
    tag="PROD-FLYACHILLES-DJ3616-2L", brand="Flyachilles", model="DJ3616-16 (2-light)",
    name='47.2" 2-light modern wave LED linear pendant, gold, dimmable',
    url="https://flyachilles.com/products/modern-wave-led-linear-pendant-light?variant=54059245109443",
    source="Flyachilles product page, read 2026-10-22; $348.99. 47.2\" long (the 2-light; the "
           "1-light is 39.4\" at 2,700 lm, and the page lists both under DJ3616-16). 5,400 lm, "
           "CRI >85, 3000 K to 6000 K stepless with remote (set 3000 K), dimmable by remote, "
           "110 V on the spec sheet, gold finish. ** NOT PUBLISHED: ** any UL/ETL/cETL mark, "
           "driver type or replaceability, wattage, strip count, and whether the gold is PVD or "
           "lacquered. ** BEFORE ORDERING: ** confirm the variant link is the 2-light, read the "
           "mark on the fixture, confirm 120 V, and budget a spare driver.",
)
MODERN_FORMS_BANTAM = Product(
    tag="PROD-MODERNFORMS-WS-38109", brand="Modern Forms", model="WS-38109-30-BK",
    name="Bantam LED wall sconce, 3000K, black",
    source="Modern Forms specification, read 2026-09-06. 393 lm, CRI 90, and ** ADA "
           "compliant at <=4\" projection, which genuinely matters on a stair ** -- a 6\" "
           "sconce there is both a shoulder hazard and a code problem. These three are not "
           "decoration: inverse-square means a 2,400 lm globe 12 ft up the stairwell "
           "delivers almost nothing to the treads, so the sconces are the stair's real light.",
)
MODERN_FORMS_MYKONOS = Product(
    tag="PROD-MODERNFORMS-FR-W1819", brand="Modern Forms", model="FR-W1819-52L-30-MB",
    name='Mykonos 52" DC ceiling fan with 3000K LED light kit',
    source="Modern Forms specification, read 2026-09-06. 150 CFM/W against a typical AC "
           "fan's 70-90; three flat blades and a smooth glass lens, so there is almost "
           "nothing to dust. ** DC IS WORTH IT FOR NOISE, NOT ENERGY ** -- the saving is "
           "$8-12/yr; the win is no line-frequency hum at 2 a.m. ** BUT A DC FAN CANNOT BE "
           "SPEED-CONTROLLED BY ANY CONVENTIONAL WALL DIMMER. ** Wire it to constant hot and "
           "buy the hardwired Bluetooth wall control alongside the remote; putting it on a "
           "Caseta dimmer will corrupt the receiver. That deliberately breaks the house "
           "dimming scheme and is correct. ** ORDER THE -30- SKU: ** CCT is baked into the "
           "model number and the common listing is 2700 K.",
)
CRAFTMADE_FORCE_XL = Product(
    tag="PROD-CRAFTMADE-FXL60DGT3", brand="Craftmade", model="FXL60DGT3",
    name='Force XL 60" wet-rated outdoor ceiling fan with 3000K LED',
    source="Craftmade specification, read 2026-09-06. The only current, in-stock, genuinely "
           "cETLus WET-rated 60\" fan with an integrated 3000 K light found. ** WET VERSUS "
           "DAMP IS NOT A TECHNICALITY IN MINNESOTA: ** the failure is not rain, it is a "
           "30 mph wind packing snow UP UNDER the porch roof into the motor housing, solar "
           "gain melting it onto the windings, then refreezing across 40-70 freeze-thaw "
           "cycles a season -- and damp-rated fans often use MDF-core blades that delaminate "
           "in one winter. Installing a damp-rated fixture subject to direct weather is an "
           "NEC 410.10 violation. ** The Modern Forms Woody 60\" is the most tempting wrong "
           "answer in this schedule: ** matte black and distressed koa is exactly this "
           "palette, and it is damp-only.",
)
ARMACOST_RIBBONFLEX_COB = Product(
    tag="PROD-ARMACOST-RIBBONFLEX-COB", brand="Armacost Lighting",
    model="RibbonFlex Pro 24V COB, 3000K",
    name="24V COB LED tape, 315 lm/ft, 3000K",
    source="Armacost published specifications, read 2026-09-06. ** COB, AND THAT RETIRES THE "
           "'DEEP FROSTED DIFFUSER' SPECIFICATION THIS HOUSE CARRIED. ** The dots are "
           "geometry: a diffuser only blends discrete emitters when the standoff is at least "
           "one LED pitch, which at 60 LED/m means a 16-25 mm deep channel -- and most "
           "'slim' channels are 8-9 mm, which is why people buy slim channel plus a frosted "
           "lens and still see dots. COB is a continuous phosphor strip with no discrete "
           "emitters: dot-free in a shallow channel with a light lens, and it does not pay "
           "the 15-30% (opal) or 40-60% (smoked) lumen tax a deep diffuser charges.",
)
DIODE_VALENT_X = Product(
    tag="PROD-DIODE-VALENT-X", brand="Diode LED", model="VALENT X, 3000K, 95+ CRI",
    name="24V high-output COB LED task tape, 3000K, CRI 95+ / R9 90+",
    source="Diode LED specification, read 2026-09-06. ** THE BEST-VALUE SPLURGE IN THE WHOLE "
           "SCHEDULE. ** This is the light food and white oak are seen under, so it is the "
           "one run where R9 -- the deep-red component every '90 CRI' number hides -- "
           "actually earns money, and the kitchen run is only ~16 ft, so the upgrade costs "
           "about eighty dollars. Also feeds the pantry slot. Mount tape at the FRONT edge "
           "of the cabinet: back-mounted lights the backsplash and leaves the counter dark.",
)
DIODE_OMNIDRIVE_X = Product(
    tag="PROD-DIODE-OMNIDRIVE-X", brand="Diode LED", model="OMNIDRIVE X",
    name="24V constant-voltage LED driver, ELV/TRIAC/0-10V, no minimum load",
    source="Diode LED specification, read 2026-09-06. ELV + TRIAC + 0-10 V in one part, "
           "0.1% dim-to-dark, and ** NO MINIMUM LOAD -- that last spec is the one that "
           "matters. ** Cheap ELV drivers carry a 10-15 W minimum and a short cove run then "
           "shimmers or will not strike. Load every driver to <=80% of nameplate, never "
           "exceed the published maximum run (~30 ft at 3.3 W/ft, ~16-20 ft at 5 W/ft; "
           "centre-feed doubles it), and ** put drivers somewhere accessible and ventilated "
           "** -- they are the part that fails and a plastered-in driver is a demolition "
           "job. ** The wall control is a Lutron DVELV-300P (reverse-phase), NOT the "
           "DVCL-153P used for the cans: ** mis-pairing an LED+ dimmer with an ELV tape "
           "driver is one of the most common field causes of tape flicker.",
)

LEDSUPPLY_SAUNA_STRIP = Product(
    tag="PROD-LEDSUPPLY-SAUNA-STRIP", brand="LEDsupply",
    model="Sauna LED Strip, fixed white 2700K",
    name="24V sauna-rated LED tape, silicone-jacketed IP68, 3 W/ft",
    source="LEDsupply published specifications (ledsupply.com/sauna-led-strip-lights), read "
           "2026-09-13. ** THE TEMPERATURE RATING IS THE WHOLE REASON THIS AND NOT THE "
           "ARMACOST TAPE. ** Published -30 C to +90 C; ordinary LED tape is a 60 C part and "
           "a sauna is not. 24V DC, 3 W/ft, up to 320 lm/ft, CRI 90, 120 LED/m, five fixed "
           "CCTs 2700-6500K (2700K taken), IP68 silicone jacket, 32.8 ft maximum continuous "
           "run. ** 90 C IS A CEILING NUMBER AND THIS TAPE GOES UNDER A BENCH LIP: ** a "
           "sauna is stratified, the 194 F löyly peak is at the ceiling, and the air at an "
           "18\" foot bench runs 40-60 F below it. Do not carry this rating up a wall. IP68 "
           "and not merely IP65 because the room is washed down; the silicone jacket is also "
           "what makes it survivable at humidity that condenses on every cooling surface. "
           "** CUT ONLY ON THE MARKED PITCH AND RE-SEAL THE CUT END ** -- an unsealed "
           "silicone jacket is an open conductor in a wet room. Driver is the shared "
           "OMNIDRIVE X 60 W above, OUTSIDE the hot room.",
)

# BATH2's two can layers (2026-10-12): the LL4SR in fixed 5000 K and 2700 K phosphors.
# ** CONFIRM BOTH SKUs: ** Lotus publishes 5000 K and 2700 K in its 4" round LL4R line; the
# square regressed LL4SR was only ever read at 3000 K. If either tap is not made, take the
# LL4R round in that CCT and keep the trim white.
LOTUS_LL4SR_CAN_50K = LOTUS_LL4SR_CAN.model_copy(update={
    "tag": "PROD-LOTUS-LL4SR-50K-WH", "model": "LL4SR-50K-WH",
    "name": '4" deeply regressed LED downlight, white trim, 5000K',
    "source": "BATH2's day layer, 2026-10-12: the LL4SR in a FIXED 5000 K phosphor, wet + "
              "IP54 as the 3000 K. CONFIRM THE SKU (LL4R-50K is published; LL4SR-50K was "
              "not found)."})
LOTUS_LL4SR_CAN_27K = LOTUS_LL4SR_CAN.model_copy(update={
    "tag": "PROD-LOTUS-LL4SR-27K-WH", "model": "LL4SR-27K-WH",
    "name": '4" deeply regressed LED downlight, white trim, 2700K',
    "source": "BATH2's evening shower can, 2026-10-12: the LL4SR in a FIXED 2700 K "
              "phosphor. CONFIRM THE SKU, as for the 5000 K."})
HUNTER_GALLEGOS = Product(
    tag="PROD-HUNTER-51583", brand="Hunter", model="Gallegos 51583",
    name='Gallegos 52" low-profile ceiling fan, matte black, no light kit',
    url="https://image.hunterfan.com/51583_specification_sheet.pdf",
    source="Hunter spec sheet and retailer listings, read 2026-10-22: 52 in., 3 blades, "
           "DC reversible motor, wall control included, ~10 9/16 in. overall flush-mounted, "
           "5,174 cfm high, ~43 W, ETL damp. Owner 2026-10-22: no light; blade span is "
           "flexible, the <= 11 in. height is not.",
)
# The sunken-garden flood (ED-M-PORCH-FLOOD): a 3" round adjustable trim whose 60 deg
# full-flood optic is the B60 code, in black, with the 0-30 deg tilt that aims the head
# 66 deg below horizontal (24 deg off the axis). Spec sheet read 2026-10-22.
ALCON_14119_GARDEN_FLOOD = Product(
    tag="PROD-ALCON-14119-3ND-TFBK-B60", brand="Alcon Lighting",
    model="14119-3ND-TFBK-B60-30K-NC-RB",
    name='3" round adjustable recessed LED flood, black trim, 60 deg, 3000K',
    url="https://www.alconlighting.com/14119-3nd-tfbk.html",
    source="Alcon 14119 Mini Recessed spec sheet (Rev 05/04/26) and product page, read "
           "2026-10-22. ** WET LISTED: ** cULus for damp AND wet locations, IC ordering "
           "option NC = non-IC frame kit, which suits an exterior soffit with no insulation "
           "above. 3000 K fixed (30K), 90+ CRI, 5-19 W selectable, 60 deg full flood (B60), "
           "0-30 deg tilt with 360 deg rotation, Triac and 0-10 V to 1%, 50,000 h, 5 yr. "
           "Black flange trim is TFBK with RB reflector. ** NOT PUBLISHED: ** 60 deg delivered "
           "lumens (the 3\" maximum is 1,700 lm at 19 W, read on the 24 deg beam), so the house's "
           "20 W / 1,800 lm allowance stands. ** OPEN: ** the 3\" aperture needs a hole in the "
           "waterproof balcony plank that the surface-hung design avoids; the sheet also lists a "
           "WL wet-location plate, to confirm for the soffit. Built to order, 3-7 business days "
           "per the product page.",
)

LIGHTING_PRODUCTS = (
    HUNTER_GALLEGOS,
    *MAGNETIC_TRACK_PRODUCTS,
    LOTUS_LL4SR_CAN, LOTUS_LL4SR_CAN_50K, LOTUS_LL4SR_CAN_27K, WESTGATE_VAPORTIGHT, DOLRIA_PC0008,
    MODERN_FORMS_BANTAM, MODERN_FORMS_MYKONOS, CRAFTMADE_FORCE_XL,
    ARMACOST_RIBBONFLEX_COB, DIODE_VALENT_X, DIODE_OMNIDRIVE_X,
    LEDSUPPLY_SAUNA_STRIP, ALCON_14119_GARDEN_FLOOD, FLYACHILLES_DJ3616_2L,
)
