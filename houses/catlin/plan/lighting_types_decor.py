"""Catlin luminaire types, part 2 — sconces, hanging fixtures, fans, exterior, mirrors.

Split from ``lighting_types.py`` for the 500-line rule in ``AGENTS.md``. The split is by
what a fixture IS rather than by where it goes: part 1 is the anonymous ambient and task
layer (cans, the panel, the tapes, the grow tubes, the vertical slots) and this file is the
fixtures somebody actually looks at, plus the fans and the exterior. ``LUMINAIRE_TYPES``
concatenates the two, so the E-602 schedule and its mark-uniqueness test see one catalog.

Marks continue the same sequence and must stay unique across BOTH files —
``tests/test_lighting_takeoff.py`` pins that, and it is the reason a variant takes a
numbered suffix (J1, J2, N1, N2, P1) rather than the next free letter.
"""

from __future__ import annotations

from typehaus import LuminaireForm, Service, ServicePort, ft, inch
from typehaus.model import LuminaireType

_POWER_120 = (ServicePort(tag="power", service=Service.POWER_120,
                          position=(ft(0), ft(0), ft(0))),)

DECORATIVE_LUMINAIRE_TYPES = (
    # --- H/J/K: sconces ---------------------------------------------------------------
    # Up-and-down for the basement theatre, on a dimmer: the traditional answer for a room
    # you want lit enough to walk through and dark enough to watch something in.
    LuminaireType(tag="ED-T-LT-SCONCE-UD", name="Up/down wall sconce",
                  form=LuminaireForm.SCONCE, type_mark="H",
                  footprint=(inch(6), inch(4)), height=inch(12),
                  plan_symbol="sconce-updown",
                  lamp="LED integrated, 2 x 6 W", watts=12.0, lumens=700.0, cct_k=3000,
                  cri=90, dimmable=True, load_va=12.0, ports=_POWER_120,
                  source="3000K with the house standard (was 2700K)."),
    # Down-spot for the studies. Set back from the window wall so it lights the desk
    # without putting a lit head in the glass after dark (notes: "more privacy at night").
    LuminaireType(tag="ED-T-LT-SCONCE-SPOT", name="Adjustable down-spot wall sconce",
                  form=LuminaireForm.SCONCE, type_mark="J",
                  footprint=(inch(5), inch(4)), height=inch(9), plan_symbol="sconce-spot",
                  lamp="LED integrated", watts=8.0, lumens=600.0, cct_k=3000, cri=90,
                  dimmable=True, load_va=8.0, ports=_POWER_120),
    # ``integral_switch`` is what exempts it from ``electrical.lighting_controls``.
    # ED-A-STUDIO-SCONCE sits in RM-A-STUDIO, 30' from the loft's own switching, so the
    # integral switch is a convenience there rather than a necessity.
    # J2: the plant room's spot. Same adjustable down-spot as J, wet-location listed with a
    # gasketed lens and a corrosion-resistant housing — RM-S-PLANT is a damp location
    # throughout and a wet one where it is misted, and this one is 6'-0" up a wall the room
    # condenses against.
    LuminaireType(tag="ED-T-LT-SCONCE-SPOT-WET",
                  name="Adjustable down-spot wall sconce, wet location",
                  form=LuminaireForm.SCONCE, type_mark="J2",
                  footprint=(inch(5), inch(5)), height=inch(7), plan_symbol="sconce-spot",
                  lamp="LED integrated", watts=9.0, lumens=700.0, cct_k=3000, cri=90,
                  dimmable=True, damp_rated=True, wet_rated=True, load_va=9.0,
                  ports=_POWER_120,
                  source="ED-T-LT-SCONCE-SPOT in a wet-location housing (notes/plant_room.md). "
                         "** NOT UNUSED: ** placed once, as ED-S-PLANT-SPOT in "
                         "plan/placeables.py, not in a lighting*.py file. A review that "
                         "greps only the lighting files reads this row as dead and it is "
                         "not."),
    # ** J1 IS NOT A DUPLICATE OF J WITH A SWITCH ON IT. ** Both its uses are places that
    # deliberately CANNOT take a wall switch: a 43 sf attic nook with no wall on the way in
    # (plan/lighting_attic.py) and the under-stair closet (plan/lighting.py).
    # ``integral_switch=True`` is exactly what exempts both from
    # ``electrical.lighting_controls`` — deleting J1 means adding two switches with nowhere
    # to put them.
    LuminaireType(tag="ED-T-LT-SPOT-SW", name="Down-spot wall sconce, switch on fixture",
                  form=LuminaireForm.SCONCE, type_mark="J1",
                  footprint=(inch(5), inch(4)), height=inch(9), plan_symbol="sconce-spot",
                  lamp="LED integrated", watts=8.0, lumens=600.0, cct_k=3000, cri=90,
                  integral_switch=True, load_va=8.0, ports=_POWER_120),
    # V: the sauna. A hot room needs its own listing — an ordinary damp-rated sconce is
    # rated to 40 C ambient and the ceiling of a 194 F löyly peak is roughly 90 C.
    #
    # ** RE-SPECIFIED 2026-09-06: NOTHING SOLD IN THE US IS BOTH IP65 AND 125 C, WHICH
    # PICKS THE PRODUCT FOR US. ** The type this replaces asked for a gasketed wood-shaded
    # sconce at 125 C ambient, and that combination does not exist as a consumer luminaire:
    # LED sconces top out at 60-93 C, and lamp-and-shade fixtures are limited by their cable,
    # not their shade. The only construction that clears the temperature is ** fibre optic **,
    # because there are no electronics in the hot zone at all — glass fibre is rated 180 C
    # and carries no current, so the ferrules can go in the CEILING and even over the heater
    # while the dimmable projector lives outside the room.
    #
    # That inverts two things the old spec had backwards. It is no longer mounted low in the
    # corner diagonally opposite the heater — that placement existed to keep a fixture out of
    # the hottest air, and a fibre ferrule does not care. And it IS dimmable, because the
    # dimming happens at the projector in cool air; the old "not dimmable" note was a
    # property of a potted driver in the hot room, which there no longer is.
    #
    # ** NEVER RECESS A CAN IN A HOT ROOM ** — it penetrates the vapour barrier at the
    # hottest point in the building and puts a driver in the hot cavity. And never cedar for
    # a shade: it bleeds resin onto basswood.
    #
    # ** THE ONE LIVE RISK, AND IT IS A PERMIT RISK: ** Cariitti and Harvia are CE-marked
    # European products, not NRTL-listed. If the inspector wants an NRTL listing inside the
    # hot room this is the most likely snag in the house — confirm in writing before ordering.
    LuminaireType(tag="ED-T-LT-SAUNA-VT",
                  name="Sauna fibre-optic lighting, 8 ferrules on a remote projector",
                  form=LuminaireForm.SCONCE, type_mark="V",
                  footprint=(inch(5), inch(4)), height=inch(7), plan_symbol="sconce",
                  lamp="Glass fibre, 180 C rated, remote LED projector", watts=6.0,
                  lumens=400.0, cct_k=2700, cri=90, dimmable=True,
                  damp_rated=True, wet_rated=True, load_va=6.0, ports=_POWER_120,
                  product_ref="PROD-CARIITTI-VPL30-G211",
                  source="Cariitti Premium Glass Fiber 8-spot with a dimmable 2700K "
                         "projector mounted OUTSIDE the hot room "
                         "(notes/sauna_basement_wall_detail.md). 2700K and 400 lm stay "
                         "deliberate: the room is basswood-lined and read by firelight "
                         "standards, and a bright fixture in a small hot room is glare "
                         "rather than light."),
    # ** <= 4" OF PROJECTION IS A SPECIFICATION, NOT A STYLE. ** On a stair a 6" sconce is
    # a shoulder hazard and a code problem; the ADA reach-range limit is the right number to
    # hold even where the ADA does not apply. 393 lm against the 400 authored here is within
    # a rounding error, and these three are the stair's REAL light — mark L twelve feet up
    # the void delivers almost nothing to the treads. 2700 K -> 3000 K with the house.
    LuminaireType(tag="ED-T-LT-SCONCE-STAIR", name="Stair wall sconce, ADA projection",
                  form=LuminaireForm.SCONCE, type_mark="K",
                  footprint=(inch(5), inch(4)), height=inch(8), plan_symbol="sconce",
                  lamp="LED integrated", watts=6.0, lumens=400.0, cct_k=3000, cri=90,
                  dimmable=True, load_va=6.0, ports=_POWER_120,
                  product_ref="PROD-MODERNFORMS-WS-38109",
                  source="Modern Forms Bantam WS-38109-30-BK, 393 lm, CRI 90, <=4\" "
                         "projection. ** NOT A STYLING DUPLICATE OF MARK J: ** the "
                         "projection limit above is a specification, this is a real and "
                         "different product, and J's head stands 9\" tall — which is the "
                         "hazard this row exists to avoid."),

    # --- L/M: hanging fixtures --------------------------------------------------------
    # ``height`` on a hanging fixture is the *whole assembly* — canopy, drop, shade — which
    # is what lets ``Mount(CEILING, drop=height)` land the canopy on the ceiling and read
    # the bottom of the shade off the same number (→ placeable_symbols/lighting.pendant).
    # ** RE-SPECIFIED 2026-09-06, AND THE LAMP IS THE WHOLE DECISION. ** 3 x REPLACEABLE
    # E26, not six integrated candelabra: over a 20'-4" void the fixture is unreachable, and
    # the question is not "how long does the LED last" — at 3 h/day, 25,000 h is 23 years, so
    # every LED fixture "never needs relamping" — but "what dies first". The answer is the
    # DRIVER: electrolytic capacitors rated at 25 C, halving per 10 C above, sitting at the
    # ridge of a 20 ft stack-effect chimney. Realistic life there is 12-20 years, and a lift
    # would not fix obsolescence anyway. An E26 socket has been continuous since 1909 and the
    # failure costs six dollars. 2400 lm was already right; 2700 K was not — it pushes white
    # paint yellow and makes white oak read orange, which is exactly this palette's failure
    # mode, so this joins the house's 3000 K standard.
    LuminaireType(tag="ED-T-LT-CHANDELIER", name="3-globe cascading pendant over the stairwell",
                  form=LuminaireForm.CHANDELIER, type_mark="L",
                  footprint=(inch(30), inch(30)), height=ft(4), plan_symbol="chandelier",
                  lamp="3 x E26 LED, field replaceable", watts=28.0, lumens=2400.0,
                  cct_k=3000, cri=90, dimmable=True, load_va=28.0, ports=_POWER_120,
                  product_ref="PROD-KUZCO-CH57514",
                  source="Kuzco Samar CH57514-CH/OP, opal globes on cables adjustable to "
                         "120\". No integral driver — a standard 120 V phase dimmer runs it. "
                         "The stair SCONCES (mark K) are the stair's real light: "
                         "inverse-square means 2400 lm twelve feet up delivers almost "
                         "nothing to the treads, and this fixture is decorative."),
    # ** RE-TYPED FROM A ROUND PENDANT TO A 48" LINEAR CHANDELIER, 2026-09-06, AND THE
    # ARITHMETIC IS WHY. ** The round-fixture rule sizes off a table's NARROW dimension, so
    # over a 40 x 84 table it gives a 20"-27" fixture with ~28" of dark tabletop at each end
    # — and sizing up to cover the length overhangs the width into head-strike. 48" of
    # fixture over a 72"-84" table is the answer, hung with its bottom 30"-36" above the
    # tabletop (+3" per foot over an 8' ceiling). 1200 lm was a single-pendant number and is
    # too low for a dining chandelier: 2400 lm is the middle of the 2000-3500 band, and the
    # domestic fixture to price against is the VC Dessau 48 at 2261 lm / 36 W.
    #
    # 2700 K was ** a live defect, not a preference **: this fixture and the kitchen's 3000 K
    # cans are seen at once across an open plan, and a CCT mismatch in one sightline reads as
    # a construction error.
    #
    # ** NO product_ref: THE OWNER IS IMPORTING THIS ONE AND HAS NOT PICKED THE UNIT. ** A
    # sealed extrusion has almost nothing to dust, which matters more here than anywhere
    # else because a dining fixture in an open plan collects airborne COOKING GREASE and
    # grease-plus-dust does not dry-dust off. That rules out multi-sleeve fixtures (twelve
    # sleeves to dust individually), crackle glass (the texture IS the dust feature) and
    # unlacquered brass over a table (it patinas unevenly wherever grease lands, and the fix
    # is polishing rather than wiping).
    #
    # ** THE IMPORT RISK HERE IS REAL AND IT IS NOT THE PLUMBING RISK. ** A luminaire is
    # HARDWIRED equipment, so NEC 110.2 / 110.3(B) require it to be listed and installed per
    # its listing — an unlisted or merely CE-marked import is a genuine inspection exposure
    # in a way a showerhead never is. Buy only a fixture with a real UL/ETL/cETLus mark and
    # ** verify the mark is ON THE FIXTURE, not merely claimed in the listing text ** ("FCC
    # certified" is a radio-emissions declaration and means nothing here). Confirm 120 V, not
    # 220-240. Confirm the driver is ELV/TRIAC-dimmable AND replaceable — a captive
    # proprietary driver is the part that dies at 12-20 years and on an import there is no
    # replacement channel at all, so ** budget a spare driver with the order. ** Dim it on
    # its own Lutron DVELV-300P, never ganged with the kitchen cans.
    LuminaireType(tag="ED-T-LT-PENDANT", name='48" linear dining chandelier',
                  form=LuminaireForm.CHANDELIER, type_mark="M",
                  footprint=(ft(4), inch(4)), height=ft(3, 6), plan_symbol="pendant",
                  lamp="LED integrated, replaceable ELV/TRIAC driver", watts=36.0,
                  lumens=2400.0, cct_k=3000, cri=90, dimmable=True, load_va=36.0,
                  ports=_POWER_120,
                  source="Owner selection 2026-09-06: an imported linear fixture, unit not "
                         "yet chosen. TARGET THE SPECS, NOT THE LOOK — ~48\" long, "
                         "2000-3500 lm, 3000 K, CRI 90+, dimmable, 120 V, and a REAL "
                         "UL/ETL/cETLus mark on the fixture itself."),

    # M1: the attic studio's bar pendant (2026-09-06). A separate mark from M, not a second
    # instance of it: M is a 4'-0" dining fixture and this would have hung over a 4'-7" bar
    # run in a 356 sf room, where a 48" linear would read as the dining room's fixture put
    # somewhere it does not belong.
    #
    # ** M1 IS CATALOG-ONLY SINCE 2026-09-10, AND IS DELIBERATELY KEPT ** — the same
    # convention mark N is held under, and for the same purpose: it is the stated revert if
    # the owner wants a decorative fitting at this bar after all. `luminaire_schedule` builds
    # its rows from placements, so an unplaced type prints on no sheet and bills nothing.
    #
    # ** WHY IT CAME OUT: A PENDANT DOES NOT FIT UNDER THIS RAKE. ** The bar moved onto
    # W-A-BATH-S and FURN-A-STUDIO-BAR-BASE is 54 3/4" tall under a 6:12 underside that is
    # 4'-11 1/4" at the unit's west end and 6'-5 3/4" over the bowl — 17"-23" of air, and the
    # person at the bowl stands in it. ED-A-STUDIO-BAR-PEND is a wall-mounted ED-T-LT-MIRROR
    # now; the whole derivation is on the placement in plan/lighting_attic.py.
    #
    # ** AND THE LUMEN ARGUMENT BELOW IS RETIRED OUTRIGHT (2026-09-10). ** The "357 lm of
    # slack" was stale when this was written (it counted five sconces) and the 1,450 lm that
    # replaced it lasted a day: `code.R303_1_light_and_ventilation` divides by R304.3's
    # 146 sf now, RM-A-STUDIO passes on glazing, and Exception 1 is not adjudicated. **No
    # lumen floor binds that room**, so M1's 1,800 lm is a brightness choice and not a code
    # number. The rest of the spec still binds if M1 is ever placed: TARGET THE SPECS, NOT
    # THE LOOK.
    #
    # 2'-6" assembly, not M's 3'-6": the ceiling over the bar's ORIGINAL centre-wall station
    # was 8'-6 3/4" (the 6:12 plane at x=16'-9"), and a 3'-6" drop would have left the shade
    # bottom at 5'-0 3/4" — head height at a counter you stand at.
    LuminaireType(tag="ED-T-LT-PENDANT-BAR", name='36" linear bar pendant',
                  form=LuminaireForm.CHANDELIER, type_mark="M1",
                  footprint=(ft(3), inch(4)), height=ft(2, 6), plan_symbol="pendant",
                  lamp="LED integrated, replaceable ELV/TRIAC driver", watts=24.0,
                  lumens=1800.0, cct_k=3000, cri=90, dimmable=True, load_va=24.0,
                  ports=_POWER_120,
                  source="Owner selection 2026-09-06 for the attic studio's bar, unit not "
                         "yet chosen. TARGET THE SPECS, NOT THE LOOK — ~36\" long, "
                         "1800 lm or better (a brightness choice since 2026-09-10, NOT "
                         "the code number it was), 3000 K, CRI 90+, dimmable, 120 V, and a REAL "
                         "UL/ETL/cETLus mark on the fixture itself."),

    # --- N: ceiling fans with a light kit ---------------------------------------------
    # A fan-light is a luminaire here, not Equipment: there is no fan ``EquipmentKind``, no
    # HVAC check reads one, and every form in this catalog exports as the same
    # ``IfcLightFixture`` regardless. ``load_va`` carries motor *and* light; ``watts`` is
    # the light kit alone, because that is what the photometric row means.
    #
    # ** dimmable=False ON EVERY FAN HERE, 2026-09-06. ** These read True while their own
    # ``source`` said in capitals that a DC fan cannot be speed-controlled by a wall
    # dimmer. The plan was already right (a plain ED-T-SWITCH); the flag was the lie, and
    # it prints to the E-602 schedule an electrician orders from.
    #
    # ** MARK N IS CATALOG-ONLY SINCE 2026-09-06 AND IS DELIBERATELY KEPT. ** ED-B-GYM-LT
    # was its one placement and retyped to N3 for blade headroom. `luminaire_schedule`
    # builds its rows from placements, so an unplaced type prints on no sheet and bills
    # nothing — the same convention `glazed-green-brick` and `EXT_2X6_SWINBURNE` are held
    # under, and N is N3's stated revert if no flush-mount SKU can be sourced.
    LuminaireType(tag="ED-T-LT-FAN52", name='52" ceiling fan with LED light kit',
                  form=LuminaireForm.CEILING_FAN_LIGHT, type_mark="N",
                  footprint=(inch(52), inch(52)), height=ft(1, 6),
                  plan_symbol="ceiling-fan-light",
                  lamp="LED integrated light kit", watts=17.0, lumens=1400.0, cct_k=3000,
                  cri=90, dimmable=False, load_va=60.0, ports=_POWER_120,
                  product_ref="PROD-MODERNFORMS-FR-W1819",
                  source="Modern Forms Mykonos FR-W1819-52L-30-MB. ** A DC FAN CANNOT BE "
                         "SPEED-CONTROLLED BY ANY CONVENTIONAL WALL DIMMER: ** wire it to "
                         "constant hot and buy the hardwired Bluetooth wall control with "
                         "the remote. Do NOT put it on a Caseta dimmer — it will corrupt "
                         "the receiver. This deliberately breaks the house dimming scheme, "
                         "and that is correct."),
    # The gym's fan. ** A HUGGER, AND THAT IS THE WHOLE POINT: ** RM-B-GYM's resolved
    # clear_height_m is 2.42253 = 95 3/8", and mark N's 18" assembly leaves the blades at
    # ~6'-5 3/8" in a room people swing their arms in. 11" of assembly puts them at
    # 7'-0 3/8", clearing the 7'-0" blade-to-floor minimum every fan IFU states. N3 rather
    # than a drop change on N: a flush-mount fan is a different product, not a shorter
    # downrod — the Mykonos of mark N is a downrod fan and does not hug.
    #
    # ** NO product_ref ON PURPOSE. ** Follow ED-T-LT-CAN3: state the requirement and say
    # the SKU is unconfirmed rather than invent a datasheet. TARGET THE SPECS — 52",
    # flush/hugger mount, <= 11" overall, DC motor, 1400 lm 3000 K CRI 90 integrated light,
    # and the same constant-hot + wall-control wiring as N.
    LuminaireType(tag="ED-T-LT-FAN52-FLUSH",
                  name='52" flush-mount ceiling fan with LED light kit',
                  form=LuminaireForm.CEILING_FAN_LIGHT, type_mark="N3",
                  footprint=(inch(52), inch(52)), height=inch(11),
                  plan_symbol="ceiling-fan-light",
                  lamp="LED integrated light kit", watts=17.0, lumens=1400.0, cct_k=3000,
                  cri=90, dimmable=False, load_va=60.0, ports=_POWER_120,
                  source="Low-ceiling hugger for RM-B-GYM (no product_ref: no flush-mount "
                         "SKU has been confirmed against a datasheet). ** <= 11\" OVERALL "
                         "IS THE SPECIFICATION: ** the room's 95 3/8\" clear leaves nothing "
                         "spare against the 7'-0\" blade-to-floor minimum. ** A DC FAN "
                         "CANNOT BE SPEED-CONTROLLED BY ANY CONVENTIONAL WALL DIMMER: ** "
                         "constant hot plus the hardwired wall control, as mark N."),
    # The plant room's fan. Same 52" fan as N, in a wet-location listed housing with a
    # corrosion-resistant (sealed, non-ferrous) motor and gasketed light kit. N2 rather than
    # a retype of N: this is a different product on the quote, and the reason it is here —
    # a room that runs at 70% RH and condenses on its own glass — is not a reason the
    # bedrooms' fans should cost more.
    LuminaireType(tag="ED-T-LT-FAN52-WET",
                  name='52" ceiling fan with LED light kit, wet location',
                  form=LuminaireForm.CEILING_FAN_LIGHT, type_mark="N2",
                  footprint=(inch(52), inch(52)), height=ft(1, 6),
                  plan_symbol="ceiling-fan-light",
                  lamp="LED integrated light kit", watts=17.0, lumens=1400.0, cct_k=3000,
                  cri=90, dimmable=False, damp_rated=True, wet_rated=True, load_va=60.0,
                  ports=_POWER_120,
                  source="NEC 2023 damp/wet location; RM-S-PLANT is a damp location throughout and wet where it is misted (notes/plant_room.md)"),
    # The porch fan. Damp rated because it lives under the balcony deck, open on three
    # sides — not wet rated: nothing lands on it, the deck above is the roof.
    # ** UPGRADED FROM DAMP TO WET, 2026-09-06, AND IN MINNESOTA THAT IS NOT A
    # TECHNICALITY. ** The comment this replaces reasoned that nothing lands on the fan
    # because the balcony deck above is the roof. The failure mode is not rain: it is a
    # 30 mph wind packing snow UP UNDER an open-sided porch roof into the motor housing,
    # solar gain melting it onto the windings, then refreezing across 40-70 freeze-thaw
    # cycles a season. Damp-rated fans also commonly use MDF-core blades that delaminate in
    # one winter. Installing a damp-rated luminaire subject to direct weather is an NEC
    # 410.10 violation, and a porch open on three sides is subject to weather.
    LuminaireType(tag="ED-T-LT-FAN60", name='60" porch ceiling fan with LED light kit, wet',
                  form=LuminaireForm.CEILING_FAN_LIGHT, type_mark="N1",
                  footprint=(inch(60), inch(60)), height=ft(1, 6),
                  plan_symbol="ceiling-fan-light",
                  lamp="LED integrated light kit", watts=17.0, lumens=1400.0, cct_k=3000,
                  cri=90, dimmable=False, damp_rated=True, wet_rated=True, load_va=75.0,
                  ports=_POWER_120,
                  product_ref="PROD-CRAFTMADE-FXL60DGT3",
                  source="Craftmade Force XL FXL60DGT3, cETLus WET rated, 3000K integrated "
                         "light. ** The Modern Forms Woody 60\" is the tempting wrong "
                         "answer: ** matte black and distressed koa is exactly this "
                         "palette, and it is damp-only."),

    # --- Q: the garage shop light -----------------------------------------------------
    # A garage is an unconditioned, unheated space that cars drive snow into, so the shop
    # light is damp rated even though nothing rains on it.
    #
    # ** THE COLD RATING IS THE WHOLE STORY, AND ALMOST NO CONSUMER SHOP LIGHT PUBLISHES ONE
    # THAT SURVIVES A MINNESOTA GARAGE. ** The common products stop at -4 F and some at
    # +14 F. It is the DRIVER, not the LEDs — LEDs are *happier* cold, but electrolytic ESR
    # climbs sharply below rating. The one category that reliably publishes a cold rating is
    # vaportight/cold-storage, because it sells into freezer warehouses; IP66 is a bonus
    # here rather than the point, keeping sawdust and cobwebs outside a lens that wipes.
    # ** HARDWIRE IT: ** plug-in linkable cords crack in cold and that is where failures
    # start. 4000 K rather than 5000 K — 5000 K makes airborne sawdust glare. And note that
    # wall-box occupancy sensors are typically rated to 32 F minimum, so this room takes a
    # cold-rated ceiling PIR or a plain switch.
    LuminaireType(tag="ED-T-LT-SHOP4", name="4' vaportight LED shop light, IP66, cold rated",
                  form=LuminaireForm.LINEAR_TUBE, type_mark="Q",
                  footprint=(ft(4), inch(5)), height=inch(3), plan_symbol="linear-light",
                  lamp="LED integrated", watts=46.0, lumens=4400.0, cct_k=4000, cri=80,
                  damp_rated=True, wet_rated=True, load_va=46.0, ports=_POWER_120,
                  product_ref="PROD-WESTGATE-LVTE-4FT",
                  source="Westgate LVTE-4FT-30-46W-MCTP, IP66 vaportight, cold rated"),

    # --- R/S: exterior fixtures, both full cutoff ------------------------------------
    # Both are dark-sky fixtures by specification, not accident: `full_cutoff=True` says
    # the housing emits nothing above the horizontal, which is what
    # `advisory.dark_sky_lighting` grades every exterior luminaire on, and both hold the
    # house's 3000K warm line — the other half of the same advisory. Wet rated outright:
    # each hangs in the open (a garage face, a freestanding porch pillar), not under a
    # soffit deep enough to argue damp.
    #
    # R is the garage-door light: a shielded down-only wall sconce beside D-G-OVERHEAD.
    # `form=SCONCE` rather than a new enum kind — the enum docstring discourages new
    # kinds, and a wall pack is a sconce that grew a cutoff hood.
    LuminaireType(tag="ED-T-LT-SCONCE-EXT", name="Exterior wall sconce, full cutoff, wet",
                  form=LuminaireForm.SCONCE, type_mark="R",
                  footprint=(inch(6), inch(5)), height=inch(9), plan_symbol="sconce",
                  lamp="LED integrated", watts=12.0, lumens=900.0, cct_k=3000, cri=90,
                  damp_rated=True, wet_rated=True, full_cutoff=True, load_va=12.0,
                  ports=_POWER_120,
                  source="WAC WS-W2506 full-cutoff outdoor wall light, black, 3000K"),
    # S is the porch flood: a narrow-throw spot aimed down off the balcony's centre
    # pillar. Same reasoning on the form — an adjustable exterior spot is the sconce-spot
    # family in a wet housing — and the cutoff is in the aiming shroud, which is why the
    # narrow beam is the point: it lights the deck, not the neighbourhood.
    LuminaireType(tag="ED-T-LT-FLOOD-NARROW",
                  name="Narrow-throw LED flood, full cutoff shroud, wet",
                  form=LuminaireForm.SCONCE, type_mark="S",
                  footprint=(inch(5), inch(5)), height=inch(8), plan_symbol="sconce-spot",
                  lamp="LED integrated, 25 deg beam", watts=20.0, lumens=1800.0,
                  cct_k=3000, cri=90, damp_rated=True, wet_rated=True, full_cutoff=True,
                  load_va=20.0, ports=_POWER_120,
                  source="RAB LFLED26 narrow flood + full-cutoff visor, black, 3000K"),

    # --- P: mirror lighting -----------------------------------------------------------
    LuminaireType(tag="ED-T-LT-MIRROR", name='24" LED mirror light bar, damp',
                  form=LuminaireForm.MIRROR_LIGHT, type_mark="P",
                  footprint=(inch(24), inch(2)), height=inch(3), plan_symbol="linear-light",
                  lamp="LED integrated", watts=16.0, lumens=1300.0, cct_k=3000, cri=90,
                  dimmable=True, damp_rated=True, load_va=16.0, ports=_POWER_120),
    # The primary bath's lit mirror — the owner's requirement is an integrated LED mirror,
    # not a plain mirror flanked by sconces.
    #
    # ** FRONT-LIT IS THE ONLY SPECIFICATION THAT MATTERS, AND IT IS THE ONE THE MARKET
    # OBSCURES. ** The default "LED mirror" is BACKLIT: a halo thrown at the wall behind the
    # glass, which photographs beautifully and puts almost nothing on a face. The tells are
    # "halo", "ambient glow", "floating"; front-lit copy says "task lighting" or "shines
    # through the glass". This one's lit band is etched into the FRONT of the pane.
    #
    # ** BROUGHT TO EARTH FROM THE BRIEF, 2026-09-06. ** The authored 36" / tunable / CRI 95
    # spec described no product that exists: front-lit mirrors are not tunable, and CRI 90+
    # is the market's ceiling. A first research pass concluded no ROUND front-lit mirror
    # existed at all — true of Seura and of Electric Mirror's premium lines, false in
    # general. Robern's Vitality Perimeter is round, front-lit, 3000 K (matching the house),
    # CRI 90+ with R9 50+, and carries a defogger. 30", not 36".
    #
    # ** IT IS CORD-AND-PLUG, WHICH IS WHY plan/lighting.py PUTS A CONCEALED GFCI RECEPTACLE
    # IN THE WALL BEHIND IT ** (electrical_notes.md line 80) — that receptacle is not
    # optional and it must not land where a mounting cleat or the bottom bracket goes. Two
    # switch legs, not one: Robern requires the DEFOGGER to be switched separately from the
    # lights. Block a full-width flat 2x band behind it — the two outer brackets sit only
    # ±5" from the centreline and will not find 16" o.c. studs at an arbitrary vanity centre.
    #
    # ** AND IT IS NOT FIELD-SERVICEABLE. ** The LED module is permanently enclosed, the
    # warranty is one year, and reported failures cluster at five to six years — the driver
    # cooking in a sealed 1 3/4" aluminium cavity, not the LEDs. There is no version of this
    # product category that is repairable at this price; the one line with replaceable LED
    # strips and a 7-year warranty (Electric Mirror Fusion) makes no round. Buying it is
    # buying a consumable, and that is stated rather than discovered in 2032.
    LuminaireType(tag="ED-T-LT-MIRROR-RING",
                  name='30" round front-lit LED mirror with defogger',
                  form=LuminaireForm.MIRROR_LIGHT, type_mark="P1",
                  footprint=(inch(30), inch(1.75)), height=inch(30),
                  plan_symbol="linear-light",
                  lamp="LED integrated, front-lit etched perimeter band", watts=55.0,
                  lumens=2600.0, cct_k=3000, cri=90, dimmable=True, damp_rated=True,
                  load_va=85.0, ports=_POWER_120,
                  product_ref="PROD-ROBERN-YM0030CPFPD3",
                  source="Robern Vitality YM0030CPFPD3, 30\" circle, Perimeter pattern. "
                         "``load_va`` is 85 W — lights plus defogger, the connected load the "
                         "panel schedule sums — where ``watts`` is the 55 W light alone, "
                         "which is what the photometric row means. Dim on a Lutron "
                         "MACL-153M, named by Robern; trim the low end at commissioning, "
                         "because most \"flickering LED mirror\" complaints are an "
                         "untrimmed dimmer rather than a defective mirror."),)
