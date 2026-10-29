"""Catlin luminaire *type* catalog — the E-602 schedule's marks A through X.

NOT ``# haus: editable``: like ``fixture_types.py`` these are catalog type definitions,
not placed instances, and ``ElectricalDeviceType.needs`` is a ``frozenset``, which the
editable dialect forbids. The movable instances that reference these tags live in
``plan/lighting.py`` (editable, so UI drags round-trip).

Every entry is a ``LuminaireType`` — an ``ElectricalDeviceType`` subclass, so it rides in
``Library.electrical_device_types`` beside the receptacles and the panel and needs no new
library collection. Two plain ``ElectricalDeviceType`` entries come along for the ride: the
24V supplies the LED runs feed from, and the two controlled switches (dimmer, timer).

Marks are the schedule letters and must stay unique — ``tests/test_lighting_takeoff.py``
pins that. I is skipped (it reads as a 1 on a drawing), which is why the sequence runs
…H, J, K…; a numbered suffix (J1, N1, P1) is a variant of the mark before it.

Two wattages, deliberately different:
- ``watts`` is the *lamp* load — what the photometric row means.
- ``load_va`` is the *connected* load the panel schedule sums, which for a fan-light
  includes the motor and for a 24V run's PSU is the supply's rating, not the tape's.

Every installed type names its ``Product`` through ``product_ref`` (2026-10-28 selections:
plan/products_lighting_selected.py), and E-602 prints its brand and model.
"""

from __future__ import annotations

from library.lighting import luminaire_class

from plan.closet_types import CLOSET_LUMINAIRE_TYPES, CLOSET_SUPPLY_TYPES
from plan.laundry_lighting_types import LAUNDRY_TRACK
from plan.lighting_types_decor import DECORATIVE_LUMINAIRE_TYPES
from typehaus import ElectricalDeviceType, LuminaireForm, Service, ServicePort, ft, inch
from typehaus.library.track_lighting import PUREEDGE_SUPPLY
from typehaus.model import LuminaireType

# Every line-voltage luminaire lands on a 120V branch; one port tuple serves them all
# (``electrical.circuit_refs`` checks poles against ports, and these are all 1-pole).
_POWER_120 = (ServicePort(tag="power", service=Service.POWER_120,
                          position=(ft(0), ft(0), ft(0))),)

# Mark B, held as a name so B1/B2 below are copies of it rather than restatements.
_CAN4_WET = LuminaireType(
    tag="ED-T-LT-CAN4-WET", name='4" recessed can, wet location, white regressed trim',
    form=LuminaireForm.RECESSED_CAN, type_mark="B",
    footprint=(inch(5), inch(5)), height=inch(2), plan_symbol="recessed-can",
    lamp="LED integrated, canless, driver in its connection box", watts=14.5, lumens=860.0,
    cct_k=3000, cri=90, dimmable=True, damp_rated=True, wet_rated=True,
    load_va=14.5, ports=_POWER_120,
    product_ref="PROD-LOTUS-LL4SRG-30K-WH",
    source="Lotus LL4SRG-30K-WH, the SAME SKU as mark A (wet listed), so this is a "
           "schedule row rather than a second product")


AMBIENT_LUMINAIRE_TYPES = (
    # --- A/B/C: recessed cans (plans/electrical_notes.md, "Recessed cans") ------------
    # ** THE BLACK BAFFLE WENT WHITE ON 2026-09-06, AND THE GLARE ARGUMENT SURVIVES INTACT —
    # IT IS JUST SOLVED BY GEOMETRY INSTEAD. ** The old spec (ELCO EL49LDICA/EL39LDICA, black
    # baffle) was buying glare control with a dark absorbing ring, and it costs three things
    # this brief will not pay: a black trim in a white ceiling reads as a row of dark holes,
    # a RIBBED baffle traps dust and shows a grey halo where it collects, and the trim
    # announces itself in every room. A ** deeply regressed white reflector ** hides the
    # source behind the aperture's own depth, so it controls glare at least as well, the trim
    # disappears into the ceiling, and there is a smooth surface to wipe.
    #
    # Product is Lotus LL4SRG-30K-WH (2026-10-28): 14.5 W, 860 lm, 3000 K, 90+ CRI, IC,
    # airtight, wet, TRIAC — ** which is what collapses mark B into the same SKU. ** The
    # LL4SR named until then is the damp-only 2nd generation. Since 2026-10-28 the 4" can is
    # also the circulation can: mark C (3") was retyped to A on the owner's one-SKU call, and
    # every can is on a dimmer, so a hall that wants less than 860 lm is a trim setting.
    # ** HEIGHT IS 2", NOT 6" — CORRECTED 2026-09-06 AGAINST THE PUBLISHED SHEET. ** All
    # three marks below carried height=inch(6), a generic can housing, while the product
    # they name has been a canless fixture since it was specified. Lotus's LL4SR sheet:
    # "ID 4" OD 5" Sq", "2" Deep - Install Where Ceiling Space Is Limited", "Ceiling
    # Clearance Required: 2"", "Type IC Rated - No Housing Required", "Driver Inside
    # Connection Box - No Junction Box Needed", Approved Location "Insulated Ceilings, Open
    # Plenum, Wet". ** THE 6" WAS NOT A ROUNDING ERROR, IT WAS A DIFFERENT PRODUCT, ** and
    # it is what made thirteen cathedral cans read as unbuildable: a 6" housing eats the
    # whole 6 7/8" batt zone of the ROOF assembly and lands on the 5" of ccSPF that is the
    # only air barrier R806.5 compliance rests on, where a 2" one sits inside the batt and
    # never reaches it. Nothing in the engine grades a ceiling-recessed body against its
    # host's depth (resolve/placeables.py special-cases floor and wall mounts only), so the
    # wrong number cost nothing and bought nothing until somebody measured it.
    LuminaireType(tag="ED-T-LT-CAN4", name='4" recessed can, white regressed trim',
                  form=LuminaireForm.RECESSED_CAN, type_mark="A",
                  footprint=(inch(5), inch(5)), height=inch(2), plan_symbol="recessed-can",
                  lamp="LED integrated, canless, driver in its connection box", watts=14.5,
                  lumens=860.0, cct_k=3000, cri=90, dimmable=True, load_va=14.5,
                  ports=_POWER_120, product_ref="PROD-LOTUS-LL4SRG-30K-WH",
                  source="Lotus LL4SRG-30K-WH, 4\" deeply regressed white trim, IC airtight, "
                         "wet, TRIAC, 14.5 W / 860 lm / 3000 K / 90+ CRI (spec sheet)"),
    # A1 is mark A's housing with the field-selectable module set to 4000K instead of 3000K
    # — same can, same trim, same load, same part number. It is a separate mark and not a
    # per-can override because colour temperature is a *type* property everywhere it
    # matters (Revit's Initial Color Temperature, IFC's light source, the E-602 schedule):
    # two CCTs in one room have to read as two schedule rows or the electrician cannot tell
    # which module goes in which can. Do not "deduplicate" these two into one entry.
    #
    # ** THE BAN IS ON INSTALL-TIME SELECTABLE MODULES, NOT ON ADJUSTABLE LIGHT ** (owner,
    # 2026-10-12). A 5CCT DIP switch is set once, blind, by the electrician, and is wrong
    # constantly. A user-adjustable fixture with a live control (tunable white, RGB) is
    # allowed: it records its working CCT in `cct_k` and its range in `source`.
    LuminaireType(tag="ED-T-LT-CAN4-4000", name='4" recessed can, white regressed trim, 4100K',
                  form=LuminaireForm.RECESSED_CAN, type_mark="A1",
                  footprint=(inch(5), inch(5)), height=inch(2), plan_symbol="recessed-can",
                  lamp="LED integrated, canless, driver in its connection box", watts=14.5,
                  lumens=900.0, cct_k=4100, cri=90, dimmable=True, load_va=14.5,
                  ports=_POWER_120, product_ref="PROD-LOTUS-LL4SRG-41K-WH",
                  source="Lotus LL4SRG-41K-WH, the 4100 K phosphor (product page, CONFIRM the "
                         "SKU). ** A FIXED-CCT MODULE, NEVER AN INSTALL-SELECTABLE 5CCT ONE. ** "
                         "Two schedule rows is how the electrician tells them apart."),
    # Same housing, wet-listed: a can over a tub or inside a shower enclosure is in a wet
    # location, and every bath can here is specified that way rather than sorting them by
    # which side of the curtain they fall on.
    _CAN4_WET,
    # B1/B2: RM-M-BATH2's two layers (2026-10-12, notes/bath2_lighting.md). Same wet can as
    # B, each in ONE fixed phosphor: B1 5000 K on the plain day toggle, B2 2700 K on the
    # evening dimmer. Separate marks so the electrician knows which module goes where.
    _CAN4_WET.model_copy(update={
        "tag": "ED-T-LT-CAN4-WET-5000", "type_mark": "B1",
        "name": '4" square slim downlight, wet location, white reflector, 5000K',
        "lamp": "LED integrated, canless", "watts": 15.0, "load_va": 15.0,
        "lumens": 1420.0, "cct_k": 5000, "dimmable": False,
        "product_ref": "PROD-LOTUS-LD4S-50K-4S-WR-WT",
        "source": "Lotus LD4S-50K-4S-WR-WT (spec sheet), fixed 5000 K, 1,420 lm, CRI 90+, on a "
                  "plain toggle: BATH2's day layer. 15 W (sheet and retailers, 2026-10-28)."}),
    _CAN4_WET.model_copy(update={
        "tag": "ED-T-LT-CAN4-WET-2700", "type_mark": "B2",
        "name": '4" recessed can, wet location, white regressed trim, 2700K',
        "cct_k": 2700, "lumens": 850.0, "product_ref": "PROD-LOTUS-LL4SRG-27K-WH",
        "source": "Lotus LL4SRG-27K-WH, fixed 2700 K, 850 lm, on BATH2's evening dimmer, "
                  "inside the shower glass."}),

    # --- D: flat panels (kitchen, fitness, workshop) ----------------------------------
    LuminaireType(tag="ED-T-LT-PANEL", name="2x4 LED flat panel, surface kit, 4000K",
                  form=LuminaireForm.PANEL, type_mark="D",
                  footprint=(inch(47.75), inch(23.75)), height=inch(2.5),
                  plan_symbol="panel-light", lamp="LED integrated, 0-10V", watts=60.0,
                  lumens=5100.0, cct_k=4000, dimmable=True, load_va=60.0, ports=_POWER_120,
                  product_ref="PROD-WESTGATE-LP-2X4-60W-40K-D",
                  source="Westgate LP-2X4-60W-40K-D (spec sheet), fixed 4000 K, on the "
                         "LP-SRFC-2X4 surface kit; 2.5\" depth with the kit is an allowance."),

    # --- E: the 24V cove tape (shadow-gap ceilings, stair railing) --------------------
    # No ports and no plan symbol: this type is never placed as a device. It is named by a
    # ``LightRun`` polyline, priced per lineal foot off ``watts_per_ft``, and fed at 24V
    # from a PSU rather than from a branch circuit — which is what makes it a UPS-backed
    # light source (electrical_notes.md lines 13-15) instead of one more 120V load.
    # ** COB, AND THAT IS A SPECIFICATION (2026-09-06). ** The dots a cove tape shows are
    # geometry, not quality: a diffuser only blends discrete emitters when the standoff is at
    # least one LED pitch, which at 60 LED/m is a 16-25 mm deep channel — and most "slim"
    # channels are 8-9 mm, which is why people buy slim channel plus a frosted lens and see
    # dots anyway. COB is a continuous phosphor strip with NO discrete emitters: dot-free in
    # a shallow channel with a light lens, and it does not pay the 15-30% (opal) or 40-60%
    # (smoked) lumen tax a deep diffuser charges.
    LuminaireType(tag="ED-T-LT-STRIP24", name="24V COB LED tape in aluminium cove channel",
                  form=LuminaireForm.STRIP, type_mark="E",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED tape, 24V DC, COB", watts_per_ft=3.0, lumens=250.0,
                  cct_k=3000, cri=90, voltage=24, dimmable=True,
                  product_ref="PROD-ARMACOST-RIBBONFLEX-COB",
                  source="Armacost RibbonFlex Pro 24V COB, 3000K, on the shadow-gap ceilings "
                         "and the stair rail. Nobody reads by a cove, which is why the "
                         "R9-grade tape is spent on the kitchen (mark U) and not here."),

    # --- E3: RM-M-BATH2's evening glow (2026-10-12) ------------------------------------
    # Mark E's tape in a fixed 2700 K, damp-rated (silicone-coated) because it runs under the
    # vanity, the over-toilet cabinet and in the ceiling over the tub. Soft, low, widespread: the
    # evening layer, on the dimmer with the halo mirror. Prices on its own
    # [light_run_materials] keys.
    LuminaireType(tag="ED-T-LT-STRIP24-2700",
                  name="24V COB LED tape, 2700K, damp, in aluminium channel",
                  form=LuminaireForm.STRIP, type_mark="E3",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED tape, 24V DC, COB, silicone-coated", watts_per_ft=3.0,
                  lumens=230.0, cct_k=2700, cri=90, voltage=24, dimmable=True,
                  damp_rated=True,
                  product_ref="PROD-ARMACOST-RIBBONFLEX-COB",
                  source="Armacost RibbonFlex Pro 24V COB family in 2700K, silicone-coated "
                         "for a damp room (confirm the damp SKU). Toe kick, cabinet underside "
                         "and ceiling over the tub in RM-M-BATH2."),

    # --- E1: the shower niche's lit shelf ---------------------------------------------
    # ZERO INSTANCES since 2026-10-12: both niches were dropped (notes/superseded/
    # shower_niche.md). Kept as a named revert, priced on the bare light-run keys.
    # A variant of E, not a new family: same 24V tape, same driver, same per-foot pricing.
    # Mark "E1" because "Q" — the next free single letter — is the garage shop light, and
    # the E-602 schedule is keyed on the mark.
    #
    # What it is not is a niche. Schluter's KERDI-BOARD-SNLT is the *board*: a prefabricated,
    # bonded-waterproof niche with a channel moulded into its head for a tape. The niche is
    # a hole in a wall, which the model has no element for and does not need one for — what
    # a schedule and a BOM need is the light and the board it comes in, and naming the board
    # here bills the two together, the way they are actually bought.
    #
    # ``wet_rated`` rather than ``damp_rated``: this is inside the tub-shower's own alcove,
    # in the zone water is directed at. ``electrical.wet_location`` walks LightRuns as well
    # as fixtures, so it grades this one without any extension.
    luminaire_class("ED-T-LT-NICHE-SNLT").model_copy(update={
        "type_mark": "E1", "lumens": 118.0, "product_ref": "PROD-SCHLUTER-KB12SNLT2WW",
        "source": "Schluter KB12SNLT2WW + LIPROTEC-ECD LTECD1W, 3000 K, ~118 lm. Dims only "
                  "from Schluter-listed dimmers (DVELV-300P)."}),

    # --- U: the kitchen's under-cabinet task tape -------------------------------------
    # A SEPARATE TYPE FROM E, NOT A LONGER RUN OF IT, and the whole reason is output.
    # ED-T-LT-STRIP24 is cove tape: 3 W/ft lands near 120 lm/ft, which is right for washing
    # a ceiling and is not a task light. A work counter wants 350-500 lm/ft — 4 to 6 W/ft —
    # so this is 5 W/ft at roughly 400 lm/ft. Same 24V family so it shares the PSU idiom and
    # the per-lineal-foot pricing; a separate mark so a future reader cannot "simplify" the
    # cove tape and the task tape into one row, which would either underlight the counter or
    # triple the load on the cove runs.
    #
    # 3000K and CRI 90 match the cove tape: food has to look like food, and the kitchen's
    # cans are the 3000K ED-T-LT-CAN4, not the 4000K A1 variant.
    # ** THE "DEEP FROSTED DIFFUSER" THIS TYPE USED TO SPECIFY IS RETIRED, AND COB IS WHY
    # (2026-09-06). ** The reasoning behind it was right — a bare tape reflects as a row of
    # dots in a polished counter, and an unshielded diode line is visible from a seated
    # position at the peninsula — but a deep diffuser is the expensive way to solve it,
    # costing 15-60% of the light to fix a problem COB does not have. The valance stays; the
    # diffuser gets lighter.
    #
    # ** CRI 95 AND R9 90+ HERE, AND ONLY HERE. ** This is the light food and white oak are
    # seen under, so it is the one run where R9 — the deep-red component every "90 CRI"
    # number hides — earns money. The run is ~16 ft, so the upgrade costs about eighty
    # dollars: the best-value splurge in the schedule. Mount at the cabinet's FRONT edge;
    # back-mounted tape lights the backsplash and leaves the working counter dark.
    LuminaireType(tag="ED-T-LT-STRIP24-TASK",
                  name="24V COB LED task tape in aluminium channel, CRI 95",
                  form=LuminaireForm.STRIP, type_mark="U",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED tape, 24V DC, high-output COB", watts_per_ft=5.0, lumens=400.0,
                  cct_k=3000, cri=95, voltage=24, dimmable=True,
                  product_ref="PROD-DIODE-VALENT-X",
                  source="Diode LED VALENT X, 3000K, 95+ CRI / R9 90+, behind a light "
                         "rail/valance at the cabinet nose."),

    # --- W: the garage's exterior linear (eave soffits + the north gable) --------------
    # ** COMMODITY PARTS, STANDARD SIZE, 24V (2026-10-28). ** The WAC InvisiLED kit was
    # ~$2,900 of tape for 73.5 LF; this is an off-the-shelf IP67 COB tape in a generic
    # 1/2" aluminium U-channel with a clear cover, two 5 m reels per run, each run on its
    # own Mean Well driver INDOORS (ED-T-LT-PSU-96-WE below). No fixture listing is claimed:
    # the tape is cheap to swap, and the listed part is the driver.
    #
    # ** damp_rated AND wet_rated ARE IP67, NOT A UL WET LISTING. ** Every run is under a
    # soffit, aperture down, in a closed channel; the gable run is the wet one (NEC 410.10).
    #
    # ** full_cutoff IS A MOUNTING INSTRUCTION AS MUCH AS A PRODUCT ATTRIBUTE. ** Aperture
    # DOWN: `advisory.dark_sky_lighting` exempts the soffit runs and grades the gable run on
    # this flag, so the flag and the detail must stay in step.
    LuminaireType(tag="ED-T-LT-LINEAR-EXT", name="Exterior 24V COB tape in clear channel, IP67",
                  form=LuminaireForm.STRIP, type_mark="W",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.25),
                  lamp="COB LED tape, 24V DC, IP67 silicone tube, in a 1/2 in. U-channel",
                  watts_per_ft=3.0, lumens=350.0, cct_k=3000, cri=90, voltage=24,
                  dimmable=False, damp_rated=True, wet_rated=True, full_cutoff=True,
                  product_ref="PROD-SLL-SK512BB10-IP67-30",
                  source="SuperLightingLED SK-512BB10DDWWZZ, IP67 tube option (retailer "
                         "page): 10 W/m, 1,150 lm/m at 3000 K, CRI 90+, -20 to +50 C; "
                         "generic aluminium U-channel, clear cover, aperture down."),

    # --- X: the sauna's under-bench tape (2026-09-13) ---------------------------------
    # ** THIS REPLACES THE FIBRE-OPTIC KIT, AND THE REASON IS MONEY, NOT PHYSICS. **
    # Mark V (ED-T-LT-SAUNA-VT, plan/lighting_types_decor.py) was $1,500-2,250 installed —
    # by a wide margin the most expensive luminaire in the house, for one 92 SF room. It is
    # kept in the catalog, unreferenced, as a named revert; see that file for why fibre was
    # the only construction that could sit in the CEILING of a löyly peak.
    #
    # ** UNDER THE BENCHES IS NOT A COMPROMISE, IT IS WHAT THE NOTES ALWAYS SAID. **
    # notes/sauna_basement_wall_detail.md and notes/sauna_shower_basement_detail.md both
    # specify "light strips under the lower bench lip; keep drivers and transformers out of
    # the hot zone". The fibre kit was the thing that departed from the notes.
    #
    # ** 90 C IS THE PUBLISHED RATING AND UNDER A BENCH IS WHY IT IS ENOUGH. ** A sauna is
    # a stratified room: the 194 F (90 C) löyly peak is a CEILING number, and the air at the
    # 18" foot-bench lip runs 40-60 F below it. This tape cannot go where the ferrules went
    # and does not have to. Nothing electrical is left in the hot room at all — the driver is
    # a surface box on the workshop face of W-B-SA-N and the dimmer is in the gym.
    #
    # ** 2700K, AND THAT ARGUMENT IS CARRIED OVER FROM MARK V, NOT INVENTED HERE: ** the
    # room is basswood-lined and read by firelight standards, and a bright fixture in a small
    # hot room is glare rather than light. It is the one deliberate departure from the
    # house's fixed 3000K standard, and it survived the product change.
    #
    # ``wet_rated`` is mandatory, not decorative: RM-B-SAUNA is Occupancy.BATHROOM and
    # `electrical.wet_location` walks LightRuns as well as point fixtures (the E1 precedent).
    # No ports, no plan_symbol, no load_va — a run is named by a LightRun and fed by a PSU,
    # the same convention E / E1 / U follow.
    LuminaireType(tag="ED-T-LT-STRIP24-SAUNA", type_mark="X",
                  name="Sauna under-bench LED strip, 24V IP68 silicone",
                  form=LuminaireForm.STRIP,
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED tape, 24V DC, silicone-jacketed IP68, -30..90 C",
                  watts_per_ft=3.0, lumens=320.0, cct_k=2700, cri=90,
                  voltage=24, dimmable=True, wet_rated=True,
                  product_ref="PROD-LEDSUPPLY-SAUNA-STRIP",
                  source="LEDsupply sauna LED strip, fixed white 2700K: 24V DC, 3 W/ft, up "
                         "to 320 lm/ft, CRI 90, 120 LED/m, IP68, rated -30 C to 90 C. Under "
                         "the lower bench lip on all three benches, which is the coolest air "
                         "in a stratified room; driver and dimmer both outside the hot room. "
                         "2700K stays deliberate: the room is basswood-lined and read by "
                         "firelight standards, and a bright fixture in a small hot room is "
                         "glare rather than light."),

    # --- F: the plant-room grow bars ----------------------------------------------------
    # Two 45" bars at full output over the plants at the south windows (owner, 2026-10-28).
    # UL 8800 is the listing NEC 410 Part XVI asks of horticultural equipment. DAMP, not wet:
    # the plant-room lights are never misted.
    LuminaireType(tag="ED-T-LT-GROW-BAR", name='45" horticultural LED grow bar, UL 8800, damp',
                  form=LuminaireForm.LINEAR_TUBE, type_mark="F",
                  footprint=(inch(44.78), inch(2.5)), height=ft(2, 3),
                  plan_symbol="suspended-flat-bar",
                  lamp="LED integrated, on-board driver, 1-10V", watts=90.0, lumens=11280.0,
                  cri=92, dimmable=True, damp_rated=True, load_va=90.0, ports=_POWER_120,
                  product_ref="PROD-BARRON-AG90-W-001",
                  source="Barron Growlite Varius AG90-W-001 (spec sheet), ETL to UL 8800, "
                         "damp; hung on its safety cable. CCT and hanger kit CONFIRM."),

    # --- G: the suite's over-bed wall lamp --------------------------------------------
    LuminaireType(tag="ED-T-LT-WALL-LINEAR", name='24" linear LED wall light, brushed black',
                  form=LuminaireForm.WALL_LAMP, type_mark="G",
                  footprint=(inch(24), inch(2)), height=inch(4), plan_symbol="linear-light",
                  lamp="LED integrated, ELV", watts=22.0, lumens=1140.0, cct_k=3000, cri=90,
                  dimmable=True, damp_rated=True, load_va=22.0, ports=_POWER_120,
                  product_ref="PROD-WAC-WS-6724-30-BK",
                  source="WAC dweLED LINE WS-6724-30-BK (spec sheet), 3000 K with the house "
                         "standard: 2700 K makes white oak read orange."),

    # --- T: RM-M-PANTRY's vertical slot -----------------------------------------------
    # ** A POINT DEVICE, AND A ``LightRun`` CANNOT BE ONE. ** ``LightRun.path`` is a PLAN
    # polyline under ONE ``Mount`` elevation (model/mep.py), so a vertical run degenerates
    # to two identical points: ``length_m == 0``, ``electrical.light_run_psu`` sizes the
    # supply at 0 W, the per-foot takeoff bills 0 lineal feet and the plan renderer draws a
    # dot. It fails SILENTLY, which is the worst of the options.
    # ``LuminaireForm.STRIP``'s own docstring says it "is the one form with no point
    # instance", so STRIP is spoken for, and extending the engine for one fixture is not
    # the trade.
    #
    # The model already has the honest article: ``resolve/placeables.py``'s
    # ``resolved_mount_elevation`` returns the BASE of the body and ``LuminaireType.height``
    # measures up from it, so a 6'-0" WALL_LAMP on a 2" x 2" footprint IS a vertical slot.
    # ED-T-LT-WALL-LINEAR (mark G) is the same construction lying down.
    #
    # 120V with an integral driver, deliberately: the 3 1/2" of partition at the slot's end
    # of the pantry is king stud and jack stud, with no cavity for a 24V PSU.
    #
    # A vertical strip is the RIGHT fixture for a shallow reach-in, not a stylistic choice:
    # it lights the depth behind whatever is on each shelf, and overhead alone is the worst
    # option here because every shelf below the top sits in its own shadow.
    # ** BUILD IT, DO NOT BUY IT (2026-09-06). ** A manufactured slot sconce is $700-1,500
    # with a captive driver and an unreplaceable five-year LED; an aluminium channel cut to
    # 72" with the house's own VALENT X tape and a 60 W OMNIDRIVE X is $400-570 out of parts
    # already on the order. That also fixes the cavity problem the note above records rather
    # than working around it: the driver leaves the 3 1/2" of king-and-jack stud entirely and
    # goes somewhere accessible, which is where a driver belongs. Caveat worth stating: a
    # tape slot is a linear GLOW, not a downlight — plan a small downlight for the shelves too.
    LuminaireType(tag="ED-T-LT-SLOT72", name='72" vertical linear LED slot, site-built',
                  form=LuminaireForm.WALL_LAMP, type_mark="T",
                  footprint=(inch(2), inch(2)), height=ft(6), plan_symbol="linear-light",
                  lamp="24V COB tape in an aluminium channel, remote driver", watts=24.0,
                  lumens=2000.0, cct_k=3000, cri=95, dimmable=True, load_va=24.0,
                  ports=_POWER_120,
                  product_ref="PROD-DIODE-VALENT-X",
                  source="Diode LED A1 channel cut to 72\" + VALENT X tape + a 60 W "
                         "OMNIDRIVE X, against $700-1,500 for a manufactured slot sconce "
                         "with a captive driver."),
)


# --- 24V supplies and controlled switches ----------------------------------------------
# Not luminaires, so plain ``ElectricalDeviceType``: a PSU is a junction box with a driver
# in it, and a dimmer is a switch.
#
# Per-area supplies rather than one central 24V bus. A house-wide 24V distribution would
# mean 24V home runs the length of the building, where the voltage drop that matters is on
# the *low* side: 3 W/ft of tape at 24V pulls real current, and a 40' run at that voltage
# needs conductors out of proportion to the load. Two supplies in the ceiling next to their
# runs keep the long wire at 120V. The alternative is documented, not built.
LIGHTING_DEVICE_TYPES = (
    ElectricalDeviceType(tag="ED-T-LT-PSU-60", name="24V LED driver, 60 W, in-ceiling box",
                         footprint=(inch(8), inch(6)), height=inch(3),
                         load_va=60.0, ports=_POWER_120,
                         product_ref="PROD-DIODE-OMNIDRIVE-X",
                         source="Diode LED OMNIDRIVE X, 60 W — ELV + TRIAC + 0-10V in one part "
                                "and, the spec that matters, NO MINIMUM LOAD: a cheap ELV "
                                "driver with a 10-15 W minimum makes a short cove run shimmer "
                                "or fail to strike. Load to <=80% of nameplate and keep it "
                                "accessible and ventilated."),
    ElectricalDeviceType(tag="ED-T-LT-PSU-200", name="24V LED driver, 200 W, in-ceiling box",
                         footprint=(inch(12), inch(8)), height=inch(4),
                         load_va=200.0, ports=_POWER_120,
                         product_ref="PROD-DIODE-OMNIDRIVE-X",
                         source="Diode LED OMNIDRIVE X, 200 W. Same family as the 60 W; see "
                                "that entry for the no-minimum-load argument."),
    # Mark W's driver: one per garage exterior run, indoors. On/off only (relay switch).
    ElectricalDeviceType(tag="ED-T-LT-PSU-96-WE", name="24V LED driver, 96 W, IP65",
                         footprint=(inch(9), inch(2.7)), height=inch(1.5),
                         load_va=96.0, ports=_POWER_120,
                         product_ref="PROD-MEANWELL-HLG-100H-24A",
                         source="Mean Well HLG-100H-24A: 96 W, 24 V / 4 A, IP65, UL 8750, "
                                "228 x 68 x 38.8 mm, not dimmable."),
)



# Part 1 (this file) then part 2 (plan/lighting_types_decor.py), then the supplies and
# switches. One catalog to the E-602 schedule; two files only for the 500-line rule.
LUMINAIRE_TYPES = (*AMBIENT_LUMINAIRE_TYPES, *DECORATIVE_LUMINAIRE_TYPES,
                   *CLOSET_LUMINAIRE_TYPES, LAUNDRY_TRACK)

LIGHTING_TYPES = (*LUMINAIRE_TYPES, *LIGHTING_DEVICE_TYPES, *CLOSET_SUPPLY_TYPES, PUREEDGE_SUPPLY)
