"""Catlin luminaire types, part 2 — sconces, hanging fixtures, fans, exterior, mirrors.

Split from ``lighting_types.py`` for the 500-line rule in ``AGENTS.md``. The split is by
what a fixture IS rather than by where it goes: part 1 is the anonymous ambient and task
layer (cans, the panel, the tapes, the grow bars, the vertical slots) and this file is the
fixtures somebody actually looks at, plus the fans and the exterior. ``LUMINAIRE_TYPES``
concatenates the two, so the E-602 schedule and its mark-uniqueness test see one catalog.

Marks continue the same sequence and must stay unique across BOTH files —
``tests/test_lighting_takeoff.py`` pins that, and it is the reason a variant takes a
numbered suffix (J1, N1, N3, P1) rather than the next free letter.
"""

from __future__ import annotations

from library.lighting import luminaire_class

from typehaus import LuminaireForm, Service, ServicePort, ft, inch
from typehaus.model import LuminaireType

from .porch_lighting_types import GARDEN_FLOOD_TYPE

_POWER_120 = (ServicePort(tag="power", service=Service.POWER_120,
                          position=(ft(0), ft(0), ft(0))),)

_STRETCH_BODY = dict(
    footprint=(inch(8), inch(4)), height=inch(8), plan_symbol="sconce-swing-arm",
    lamp="LED integrated, toggle on the canopy", watts=5.0, lumens=287.0,
    cct_k=3000, cri=90, dimmable=True, damp_rated=True, load_va=5.0, ports=_POWER_120,
    product_ref="PROD-WAC-BL-23210-BK")
_STRETCH = LuminaireType(
    tag="ED-T-LT-SCONCE-SPOT", name="Swing-arm LED reading light, black",
    form=LuminaireForm.SCONCE, type_mark="J", **_STRETCH_BODY,
    source="WAC Sprig BL-23210-BK (spec sheet), drawn folded. Retyped from the Stretch "
           "BL-1660-BK 2026-10-29 (plain, cheaper; no touch dimmer). Leave the canopy "
           "toggle ON so the wall switch rules; CONFIRM it is hardwired (junction box).")

DECORATIVE_LUMINAIRE_TYPES = (
    # --- H/J/K: sconces ---------------------------------------------------------------
    # Up-and-down for the basement theatre, on a dimmer: the traditional answer for a room
    # you want lit enough to walk through and dark enough to watch something in.
    LuminaireType(tag="ED-T-LT-SCONCE-UD", name="Slim up/down LED wall sconce, black",
                  form=LuminaireForm.SCONCE, type_mark="H",
                  footprint=(inch(4.5), inch(2.5)), height=inch(12),
                  plan_symbol="sconce-slim-updown", lamp="LED integrated, ELV + TRIAC",
                  watts=15.0, lumens=680.0, cct_k=3000, cri=90, dimmable=True,
                  damp_rated=True, load_va=15.0, ports=_POWER_120,
                  product_ref="PROD-WAC-WS-83212-BK",
                  source="WAC dweLED Roland WS-83212-BK (spec sheet). The theatre units sit "
                         "on a DVCL-153P: CONFIRM it against the TRIAC range."),
    # J and J1 are one product (WAC Sprig): J is wall-switched, J1 uses the canopy toggle.
    # J2 (the plant room's wet copy) retyped to J; damp is enough there.
    _STRETCH,
    LuminaireType(tag="ED-T-LT-SPOT-SW", name="Swing-arm LED reading light, switch on fixture",
                  form=LuminaireForm.SCONCE, type_mark="J1", **_STRETCH_BODY,
                  integral_switch=True,
                  source="WAC Sprig BL-23210-BK, switched at its canopy toggle (a true on/off)."),
    LuminaireType(tag="ED-T-LT-SAUNA-VT",
                  name="Sauna fibre-optic lighting, 8 ferrules on a remote projector",
                  form=LuminaireForm.SCONCE, type_mark="V",
                  footprint=(inch(5), inch(4)), height=inch(7), plan_symbol="sconce",
                  lamp="Glass fibre, 180 C rated, remote LED projector", watts=6.0,
                  lumens=400.0, cct_k=2700, cri=90, dimmable=True,
                  damp_rated=True, wet_rated=True, load_va=6.0, ports=_POWER_120,
                  product_ref="PROD-CARIITTI-VPL30-G211",
                  source="CATALOG-ONLY since 2026-09-13, retained as the named revert for "
                         "ED-T-LT-STRIP24-SAUNA (mark X); nothing references it. Cariitti "
                         "Premium Glass Fiber 8-spot with a dimmable 2700K "
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

    # Z: a plain black candle sconce (Livex 4451-04, 2026-10-28), replacing the gothic iron
    # one the owner found too ornate. Storage room only (RM-A-EAST-UNFIN): no R303.1 floor.
    LuminaireType(tag="ED-T-LT-SCONCE-CANDLE", name="Plain black candle wall sconce, E12 LED",
                  form=LuminaireForm.SCONCE, type_mark="Z",
                  footprint=(inch(4.25), inch(7.75)), height=inch(8.5),
                  plan_symbol="sconce-candle",
                  lamp="E12 LED filament candle, Feit BPCFC40930CAFIL/4, 3000K", watts=3.3,
                  lumens=300.0, cct_k=3000, cri=90, dimmable=True, damp_rated=True,
                  load_va=3.3, ports=_POWER_120, product_ref="PROD-LIVEX-4451-04",
                  source="Livex 4451-04 (retailer pages): plainer than the gothic iron it "
                         "replaces (owner, 2026-10-28). CONFIRM the E12 socket and the UL/ETL "
                         "mark."),

    LuminaireType(tag="ED-T-LT-CHANDELIER", name="20-globe cascade over the stairwell",
                  form=LuminaireForm.CHANDELIER, type_mark="L",
                  footprint=(inch(23), inch(23)), height=ft(6), plan_symbol="cluster-pendant",
                  lamp="20 x LED integrated, not replaceable", watts=100.0,
                  cct_k=3000, dimmable=False, load_va=100.0, ports=_POWER_120,
                  max_overall_height=inch(156), canopy_diameter=inch(23),
                  product_ref="PROD-DOLRIA-PC0008",
                  source="dolria PC0008-20T-G: 23\" canopy, 20 globes on wires adjustable "
                         "3.9\"-156\", 100 W integrated LED with its own remote dimmer. "
                         "The stair SCONCES (mark K) are the stair's real light; this is "
                         "decorative."),
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
    # ** PRODUCT PICKED (owner, 2026-10-22): Flyachilles 2-light, 47.2",
    # `FLYACHILLES_DJ3616_2L`.** It is dimmable, so its 5,400 lm is a ceiling and it runs in
    # the 2000-3500 band; the listing's 3000-6000 K range is set to 3000 K on the remote. No
    # UL mark is published, so confirm it ON THE FIXTURE before ordering. A sealed extrusion
    # has almost nothing to dust, which matters more here than anywhere else because a
    # dining fixture in an open plan collects airborne COOKING GREASE and grease-plus-dust
    # does not dry-dust off. That rules out multi-sleeve fixtures (twelve sleeves to dust
    # individually), crackle glass (the texture IS the dust feature) and
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
    # its own remote; the wall control is a plain switch (ED-M-DINING-SW), not a dimmer.
    #
    # The look (2026-09-26): a WAVE chandelier — five flat LED strips side by side, each
    # rising and falling out of phase with its neighbours, off one canopy, brushed gold. The
    # gold must be PVD or lacquered, never raw brass, for the grease reason above. 16" is
    # the strips' spread.
    luminaire_class("ED-T-LT-PENDANT").model_copy(update={
        "type_mark": "M", "name": '48" LED wave chandelier', "plan_symbol": "wave-chandelier",
        "footprint": (ft(4), inch(16)),
        "product_ref": "PROD-FLYACHILLES-DJ3616-2L", "lumens": 5400.0,
        "source": "Owner selection 2026-09-26, unit picked 2026-10-22: Flyachilles DJ3616-16 "
                  "2-light, 47.2\" long, 5,400 lm max, dimmable, 3000 K by remote, CRI >85, "
                  "gold. OPEN BEFORE ORDER: a UL/ETL/cETL mark ON THE FIXTURE (none is "
                  "published), 120 V, a replaceable ELV/TRIAC driver with a spare, and whether "
                  "the gold is PVD or lacquered. It dims by its own remote; the wall control "
                  "(ED-M-DINING-SW) is a plain switch."}),

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
    # person at the bowl stands in it. ED-A-STUDIO-BAR-TASK is a wall-mounted ED-T-LT-MIRROR
    # now; adjustable track on the rake was reviewed and left as an option, not selected.
    # The placement in plan/lighting_attic.py records the clearance and task-light rationale.
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
    LuminaireType(tag="ED-T-LT-PENDANT-BAR", name='36" LED linear bar pendant, matte black',
                  form=LuminaireForm.CHANDELIER, type_mark="M1",
                  footprint=(inch(35.875), inch(2)), height=ft(2, 6),
                  plan_symbol="suspended-linear-light", lamp="LED integrated",
                  watts=39.0, lumens=3315.0, cct_k=3000, cri=90, dimmable=True,
                  load_va=39.0, ports=_POWER_120, product_ref="PROD-NUVO-62-2271",
                  source="Nuvo Bowman 36\" 62-2271 (sheet read for the -2272), cETLus dry. "
                         "Unplaced."),

    # N2 (the plant room's wet copy) retyped to N: the Mykonos is itself ETL wet.
    LuminaireType(tag="ED-T-LT-FAN52", name='52" 3-blade DC ceiling fan with LED light, wet',
                  form=LuminaireForm.CEILING_FAN_LIGHT, type_mark="N",
                  footprint=(inch(52), inch(52)), height=inch(14.75),
                  plan_symbol="ceiling-fan-light-3",
                  lamp="LED integrated light kit", watts=17.0, lumens=1110.0, cct_k=3000,
                  cri=90, dimmable=False, damp_rated=True, wet_rated=True, load_va=60.0,
                  ports=_POWER_120, product_ref="PROD-MODERNFORMS-FR-W1819-52L",
                  source="Modern Forms Mykonos FR-W1819-52L (spec sheet), ETL wet. Watts and "
                         "load are the class allowance, CONFIRM. ** A DC FAN CANNOT BE "
                         "SPEED-CONTROLLED BY ANY CONVENTIONAL WALL DIMMER: ** wire it to "
                         "constant hot with its wall control; never a Caseta dimmer."),
    luminaire_class("ED-T-LT-FAN52-FLUSH").model_copy(update={
        "type_mark": "N3", "name": 'Hunter Gallegos 52" low-profile fan, no light',
        "height": inch(10.5625), "lamp": None, "watts": None, "lumens": None, "cct_k": None,
        "cri": None, "load_va": 43.0, "product_ref": "PROD-HUNTER-51583",
        "integral_switch": True,
        "source": "Hunter Gallegos 51583 (plan/products_lighting.py), flush-mounted, "
                  "modelled at 10 9/16\" overall (Hunter: 9.64\" ceiling to fan bottom, "
                  "7.97\" to blade bottom). In RM-B-GYM the blades sit ~7'-4 1/4\" over "
                  "the stall mats, 4 1/4\" above the 7'-0\" minimum. ** NEVER ON A LAMP "
                  "DIMMER: ** constant hot plus its included wall control."}),
    # N1: the 60" wet-listed porch fan.
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
    # the garage face and open-sided balcony edge both see wind-driven weather.
    #
    # R is the garage-door light: a shielded down-only wall sconce beside D-G-OVERHEAD.
    # `form=SCONCE` rather than a new enum kind — the enum docstring discourages new
    # kinds, and a wall pack is a sconce that grew a cutoff hood.
    LuminaireType(tag="ED-T-LT-SCONCE-EXT", name="Exterior LED tube wall light, down, black",
                  form=LuminaireForm.SCONCE, type_mark="R",
                  footprint=(inch(4.5), inch(5)), height=inch(5), plan_symbol="sconce-tube",
                  lamp="LED integrated, ELV/0-10V", watts=16.0, lumens=800.0, cct_k=3000,
                  cri=90, dimmable=True, damp_rated=True, wet_rated=True, full_cutoff=True,
                  load_va=16.0, ports=_POWER_120, product_ref="PROD-WAC-WS-W2605-BK",
                  source="WAC Tube WS-W2605-BK, Down Light, ETL wet. Watts/lumens from the "
                         "FM-W26 sheet; dark-sky status and cold rating CONFIRM."),
    GARDEN_FLOOD_TYPE,
    # Mark P (a 24" mirror bar) retired 2026-10-28: the studio's wet-bar light is P1, the
    # Karlie 54622BN (plan/mirror_types.py).
)
