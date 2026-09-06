"""Catlin lighting products — the 2026-09-06 interior pass (→ plan/products_interior.py).

Split off its parent for the 500-line rule, and the subject splits cleanly: everything here
is a luminaire, a tape or a driver, and every one of them answers to two house rules that no
plumbing fixture does.

** THE HOUSE STANDARD IS 3000 K, FIXED. ** Fixed rather than field-selectable: a 5CCT DIP
switch gets set wrong constantly, one can at 4000 K in a run of eight is a screaming defect,
and a dedicated 3000 K phosphor gives better R9 than a warm/cool blend. The one deliberate
exception is the 4000 K tap over the work surfaces, which is a separate schedule row so the
electrician can tell which module goes in which can.

** A DRIVER IS THE PART THAT DIES, NOT THE LED. ** Electrolytic capacitors are rated at 25 C
and halve their life per 10 C above it, so a 25,000-hour LED behind a captive driver in an
unventilated cavity is a 12-20 year fixture, not a lifetime one. Every choice below prefers a
replaceable lamp or an accessible, separately-purchasable driver over a sealed assembly, and
where that was not available (the lit mirror) the note says so plainly.
"""

from __future__ import annotations

from typehaus.model import Product

# --- Lighting -----------------------------------------------------------------------------
#
# The house standard is 3000 K, FIXED, everywhere it is not deliberately something else.
# Fixed rather than 5CCT selectable: the DIP switch gets set wrong constantly, one can at
# 4000 K in a run of eight is a screaming defect, and a dedicated 3000 K phosphor gives
# better R9 than a warm/cool blend.
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

KUZCO_SAMAR = Product(
    tag="PROD-KUZCO-CH57514", brand="Kuzco Lighting", model="CH57514-CH/OP",
    name="Samar 3-globe cascading pendant, chrome with opal glass",
    source="Kuzco Lighting product page, read 2026-09-06. Over the 20'-4\" stairwell void. "
           "** THE POINT IS THE SOCKET: 3 x REPLACEABLE E26, NO DRIVER. ** The E26 has been "
           "continuous since 1909 and a failed lamp costs six dollars, against a 2026 "
           "fixture with a proprietary LED board that is unsupportable in 2041. Cables "
           "adjust to 120\". ** THIS IS ALSO THE ARGUMENT AGAINST A CHANDELIER LIFT, ** "
           "which was considered and rejected: over this void a lift needs ~14 ft of travel, "
           "so a cascade whose bottom globe hangs 8 ft below its canopy ends up BELOW THE "
           "FLOOR before the canopy is reachable, and a lift package also wants 3 ft of "
           "accessible level cavity plumb above -- which a peaked trussed ridge does not "
           "have. (The ALL15/25/35/50 model numbers in the original brief do not exist; the "
           "real line is ALL200/300/700/1000.) ** FORM RULE FOR A 20 FT VOID: ** enclosed "
           "opal globes on thin cable. No crystal, no upward-facing candle sockets, no open "
           "drums, and NO horizontal rings or tiers -- a stairwell is the house's dust "
           "chimney and you look DOWN on this fixture from the upper landing, so every "
           "horizontal band is a visible top face.",
)
ROBERN_VITALITY_ROUND = Product(
    tag="PROD-ROBERN-YM0030CPFPD3", brand="Robern", model="YM0030CPFPD3",
    name='Vitality 30" round lighted mirror, Perimeter pattern, 3000K, with defogger',
    source="Robern spec sheet CR-229-1213 (Vitality_YM0030CPFPD_Spec.pdf) and installation "
           "sheet CB-209-1277, read 2026-09-06. 30\" dia x 1 3/4\" deep, 26\" mirror field, "
           "2\" lit band, 3000 K, CRI 90+ with R9 50+, 55 W (85 W with the defogger), 330 "
           "lux at 18\" from centre, dimmable to 1%, UL 962 + CSA C22.2, damp. ** IT IS "
           "FRONT-LIT, WHICH IS THE ONLY SPECIFICATION THAT MATTERS HERE. ** The market's "
           "default 'LED mirror' is BACKLIT -- a halo thrown at the wall behind the glass, "
           "which photographs beautifully and contributes almost nothing to a face. Tells "
           "for backlit: 'halo', 'ambient glow', 'floating'. This one's lit band is etched "
           "into the FRONT of the glass. An earlier pass concluded no round front-lit mirror "
           "existed; that was true of Seura and of Electric Mirror's premium lines and false "
           "in general. ** CLEANABILITY: ** polished-edge glass with the frame behind it, so "
           "the whole wiped surface is one plane, and there is NO capacitive touch button on "
           "the face -- which is the single strongest argument against the $90-400 tier, "
           "whose glass is bonded into a tray with an exposed silicone bead all round. "
           "** CLEAN WITH 50/50 WATER AND ISOPROPYL ON THE CLOTH, NEVER SPRAYED ON THE "
           "GLASS; ammonia and vinegar damage the mirror. ** ** NOT FIELD-SERVICEABLE, AND "
           "THE WARRANTY IS ONE YEAR: ** the LED module is permanently enclosed, reported "
           "failures cluster at five to six years, and the fix is a new mirror. Electric "
           "Mirror's Fusion has replaceable LED strips and a 7-year warranty but makes no "
           "round. CCT footnote: the spec sheet records the line moving from 2700 K to "
           "3000 K in 2021 and several dealer pages still print the old figure -- confirm "
           "on the box label at delivery.",
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
           "driver is one of the most common field causes of tape flicker, and the dining "
           "fixture wants its own DVELV-300P rather than being ganged with the kitchen cans.",
)

LIGHTING_PRODUCTS = (
    LOTUS_LL4SR_CAN, WESTGATE_VAPORTIGHT, KUZCO_SAMAR, ROBERN_VITALITY_ROUND,
    MODERN_FORMS_BANTAM, MODERN_FORMS_MYKONOS, CRAFTMADE_FORCE_XL,
    ARMACOST_RIBBONFLEX_COB, DIODE_VALENT_X, DIODE_OMNIDRIVE_X,
)
