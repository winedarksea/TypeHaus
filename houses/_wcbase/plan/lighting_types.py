"""Catlin luminaire *type* catalog — the E-602 schedule's marks A through U.

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

Product references live in ``source`` so a substitution is a one-line, reviewable change.
"""

from __future__ import annotations

from plan.lighting_types_decor import DECORATIVE_LUMINAIRE_TYPES
from typehaus import ElectricalDeviceType, LuminaireForm, Service, ServicePort, ft, inch
from typehaus.model import LuminaireType

# Every line-voltage luminaire lands on a 120V branch; one port tuple serves them all
# (``electrical.circuit_refs`` checks poles against ports, and these are all 1-pole).
_POWER_120 = (ServicePort(tag="power", service=Service.POWER_120,
                          position=(ft(0), ft(0), ft(0))),)

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
    # Product is Lotus LL4SR-30K-WH (PROD-LOTUS-LL4SR-30K-WH) — 14.5 W, 900 lm, 3000 K, 90+
    # CRI, IC, airtight, and wet + IP54, ** which is what collapses mark B into the same
    # SKU: ** there is no separate wet trim to colour-match, only a separate schedule row.
    #
    # ** THE APERTURE IS THE OUTPUT LADDER, AND THAT IS DELIBERATE. ** 900 lm from a 4"
    # aperture is right over a counter and a basin and is genuinely glary in a hallway, so
    # the 4" cans light the rooms and the 3" mark C lights the circulation. A review of this
    # schedule proposed dropping the 3" for aperture consistency; that would push thirteen
    # hall, closet, laundry and stair cans from 650 lm to 900 and over-light every one of
    # them. The split stays. Every can in the house is on a dimmer, so trimming a living
    # room below 900 lm is a commissioning setting, not a different fixture.
    LuminaireType(tag="ED-T-LT-CAN4", name='4" recessed can, white regressed trim',
                  form=LuminaireForm.RECESSED_CAN, type_mark="A",
                  footprint=(inch(5), inch(5)), height=inch(6), plan_symbol="recessed-can",
                  lamp="LED module, field replaceable", watts=12.0, lumens=900.0,
                  cct_k=3000, cri=90, dimmable=True, load_va=12.0, ports=_POWER_120,
                  product_ref="PROD-LOTUS-LL4SR-30K-WH",
                  source="Lotus LL4SR-30K-WH, 4\" deeply regressed white trim, IC airtight, "
                         "wet + IP54, 14.5 W / 900 lm / 3000 K / 90+ CRI"),
    # A1 is mark A's housing with the field-selectable module set to 4000K instead of 3000K
    # — same can, same trim, same load, same part number. It is a separate mark and not a
    # per-can override because colour temperature is a *type* property everywhere it
    # matters (Revit's Initial Color Temperature, IFC's light source, the E-602 schedule):
    # two CCTs in one room have to read as two schedule rows or the electrician cannot tell
    # which module goes in which can. Do not "deduplicate" these two into one entry.
    LuminaireType(tag="ED-T-LT-CAN4-4000", name='4" recessed can, 4000K, white regressed trim',
                  form=LuminaireForm.RECESSED_CAN, type_mark="A1",
                  footprint=(inch(5), inch(5)), height=inch(6), plan_symbol="recessed-can",
                  lamp="LED module, field replaceable, set to 4000K", watts=12.0,
                  lumens=950.0, cct_k=4000, cri=90, dimmable=True, load_va=12.0,
                  ports=_POWER_120,
                  product_ref="PROD-LOTUS-LL4SR-30K-WH",
                  source="Lotus LL4SR class, 4\" deeply regressed white trim, in the 4000K "
                         "tap. ** BUY A FIXED-CCT MODULE, NEVER A 5CCT SELECTABLE ONE: ** "
                         "the DIP switch gets set wrong constantly, one can at the wrong "
                         "temperature in a run of eight is a screaming defect, and a "
                         "dedicated phosphor gives better R9 than a warm/cool blend. Two "
                         "schedule rows is how the electrician tells them apart, which is "
                         "the reason A1 exists at all."),
    # Same housing, wet-listed: a can over a tub or inside a shower enclosure is in a wet
    # location, and every bath can here is specified that way rather than sorting them by
    # which side of the curtain they fall on.
    LuminaireType(tag="ED-T-LT-CAN4-WET", name='4" recessed can, wet location, white regressed trim',
                  form=LuminaireForm.RECESSED_CAN, type_mark="B",
                  footprint=(inch(5), inch(5)), height=inch(6), plan_symbol="recessed-can",
                  lamp="LED module, field replaceable", watts=12.0, lumens=900.0,
                  cct_k=3000, cri=90, dimmable=True, damp_rated=True, wet_rated=True,
                  load_va=12.0, ports=_POWER_120,
                  product_ref="PROD-LOTUS-LL4SR-30K-WH",
                  source="Lotus LL4SR-30K-WH — the SAME SKU as mark A, which is already wet "
                         "+ IP54 listed, so this is a schedule row rather than a second "
                         "product and there is no separate wet trim to colour-match"),
    LuminaireType(tag="ED-T-LT-CAN3", name='3" recessed can, white regressed trim',
                  form=LuminaireForm.RECESSED_CAN, type_mark="C",
                  footprint=(inch(3.75), inch(3.75)), height=inch(5),
                  plan_symbol="recessed-can",
                  lamp="LED module, field replaceable", watts=9.0, lumens=650.0,
                  cct_k=3000, cri=90, dimmable=True, load_va=9.0, ports=_POWER_120,
                  source='3" deeply regressed white trim, IC airtight, in the Lotus '
                         'LL3SR class (no product_ref: the 3" SKU was not confirmed against '
                         'a datasheet, and only the 4" was). Halls, closets, the laundry and '
                         'the two stairs — 650 lm is the circulation tier and 900 would '
                         'over-light every one of them.'),

    # --- D: flat panels (kitchen, fitness, workshop, furnace) -------------------------
    LuminaireType(tag="ED-T-LT-PANEL", name="2x4 edge-lit LED flat panel",
                  form=LuminaireForm.PANEL, type_mark="D",
                  footprint=(ft(4), ft(2)), height=inch(1.5), plan_symbol="panel-light",
                  lamp="LED integrated", watts=40.0, lumens=4800.0, cct_k=4000, cri=80,
                  dimmable=True, load_va=40.0, ports=_POWER_120),

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

    # --- E1: the shower niche's lit shelf ---------------------------------------------
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
    LuminaireType(tag="ED-T-LT-NICHE-SNLT",
                  name="Lit shower niche, 24V tape in a KERDI-BOARD-SNLT channel",
                  form=LuminaireForm.STRIP, type_mark="E1",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED tape, 24V DC, IP67", watts_per_ft=3.0, lumens=250.0,
                  cct_k=3000, cri=90, voltage=24, dimmable=True, wet_rated=True,
                  source="Schluter-KERDI-BOARD-SNLT prefabricated bonded-waterproof niche "
                         "with an integrated LIPROTEC-LLP profile; LIPROTEC-ES 24V driver "
                         "(here the shared ED-T-LT-PSU-60 in the ceiling above)."),

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

    # --- F: the plant-room tubes ------------------------------------------------------
    # Growth-spectrum, hung on a cable suspension kit over the plants at the south windows.
    # Multi-watt selectable; specified at the 50 W setting because the point of putting them
    # here is supplementing a north-of-45 winter.
    #
    # WET rated and UL 8800 listed, not merely damp. Both are requirements, not
    # upgrades: NEC Article 410 Part XVI (added in the 2020 cycle) requires horticultural
    # lighting equipment to be *listed*, and UL 8800 is that listing — it admits only damp-
    # or wet-rated horticultural luminaires. RM-S-PLANT is held at 70% RH and is misted, so
    # these take the wet end of it.
    LuminaireType(tag="ED-T-LT-TUBE6",
                  name="6' suspended linear tube, wet, UL 8800 horticultural",
                  form=LuminaireForm.LINEAR_TUBE, type_mark="F",
                  footprint=(ft(6), inch(3)), height=ft(2, 3),
                  plan_symbol="suspended-linear-light",
                  lamp="T8 LED, multi-watt selectable 25/40/50 W", watts=50.0,
                  lumens=6000.0, cct_k=3500, cri=90, dimmable=True, damp_rated=True,
                  wet_rated=True, load_va=50.0, ports=_POWER_120,
                  source="6' linear LED grow tube, black, 120-277V, on a T8 harness + cable "
                         "suspension kit; specified UL 8800 listed and wet-location rated "
                         "per NEC 410 Part XVI (notes/plant_room.md)"),

    # --- G: the suite's over-bed wall lamp --------------------------------------------
    LuminaireType(tag="ED-T-LT-WALL-LINEAR", name="36\" linear LED wall lamp",
                  form=LuminaireForm.WALL_LAMP, type_mark="G",
                  footprint=(ft(3), inch(3)), height=inch(4), plan_symbol="linear-light",
                  lamp="LED integrated", watts=18.0, lumens=1500.0, cct_k=3000, cri=90,
                  dimmable=True, load_va=18.0, ports=_POWER_120,
                  source="3000K with the house standard (was 2700K): this lamp is in the "
                         "same sightline as the suite's cans, and 2700K makes white oak "
                         "read orange."),

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
                         source="Diode LED OMNIDRIVE X, 60 W — ELV + TRIAC + 0-10V in one part and, the spec that matters, NO MINIMUM LOAD: a cheap ELV driver with a 10-15 W minimum makes a short cove run shimmer or fail to strike. Load to <=80% of nameplate and keep it accessible and ventilated."),
    ElectricalDeviceType(tag="ED-T-LT-PSU-200", name="24V LED driver, 200 W, in-ceiling box",
                         footprint=(inch(12), inch(8)), height=inch(4),
                         load_va=200.0, ports=_POWER_120,
                         product_ref="PROD-DIODE-OMNIDRIVE-X",
                         source="Diode LED OMNIDRIVE X, 200 W. Same family as the 60 W; see that entry for the no-minimum-load argument."),
    ElectricalDeviceType(tag="ED-T-SWITCH-DIM", name="Wall dimmer, 120V LED-rated",
                         footprint=(inch(4), inch(2)), height=inch(2),
                         control="dimmer", ports=_POWER_120),
    # The plant room's tubes run on a schedule, not on somebody remembering — the notes
    # ask for it to be "smart" so it can be on a timer. A smart switch on a timer is the
    # same box; ``control`` records which behaviour was bought.
    ElectricalDeviceType(tag="ED-T-SWITCH-TIMER", name="Wall timer switch, smart, 120V",
                         footprint=(inch(4), inch(2)), height=inch(2),
                         control="timer", ports=_POWER_120),
)

# Part 1 (this file) then part 2 (plan/lighting_types_decor.py), then the supplies and
# switches. One catalog to the E-602 schedule; two files only for the 500-line rule.
LUMINAIRE_TYPES = (*AMBIENT_LUMINAIRE_TYPES, *DECORATIVE_LUMINAIRE_TYPES)

LIGHTING_TYPES = (*LUMINAIRE_TYPES, *LIGHTING_DEVICE_TYPES)
