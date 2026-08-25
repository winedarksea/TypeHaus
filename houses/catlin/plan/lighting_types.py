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

from typehaus import ElectricalDeviceType, LuminaireForm, Service, ServicePort, ft, inch
from typehaus.model import LuminaireType

# Every line-voltage luminaire lands on a 120V branch; one port tuple serves them all
# (``electrical.circuit_refs`` checks poles against ports, and these are all 1-pole).
_POWER_120 = (ServicePort(tag="power", service=Service.POWER_120,
                          position=(ft(0), ft(0), ft(0))),)

LUMINAIRE_TYPES = (
    # --- A/B/C: recessed cans (plans/electrical_notes.md, "Recessed cans") ------------
    # The notes name the product family outright: ELCO 4" and 3" IC-airtight housings with
    # a black baffle trim and a replaceable field-selectable LED module. Black baffle is
    # the point — it kills the bright-ring glare a white trim gives at eye level.
    LuminaireType(tag="ED-T-LT-CAN4", name='4" recessed can, black baffle trim',
                  form=LuminaireForm.RECESSED_CAN, type_mark="A",
                  footprint=(inch(5), inch(5)), height=inch(6), plan_symbol="recessed-can",
                  lamp="LED module, field replaceable", watts=12.0, lumens=900.0,
                  cct_k=3000, cri=90, dimmable=True, load_va=12.0, ports=_POWER_120,
                  source="ELCO Lighting EL49LDICA, 4\" IC airtight, black baffle"),
    # A1 is mark A's housing with the field-selectable module set to 4000K instead of 3000K
    # — same can, same trim, same load, same part number. It is a separate mark and not a
    # per-can override because colour temperature is a *type* property everywhere it
    # matters (Revit's Initial Color Temperature, IFC's light source, the E-602 schedule):
    # two CCTs in one room have to read as two schedule rows or the electrician cannot tell
    # which module goes in which can. Do not "deduplicate" these two into one entry.
    LuminaireType(tag="ED-T-LT-CAN4-4000", name='4" recessed can, 4000K, black baffle trim',
                  form=LuminaireForm.RECESSED_CAN, type_mark="A1",
                  footprint=(inch(5), inch(5)), height=inch(6), plan_symbol="recessed-can",
                  lamp="LED module, field replaceable, set to 4000K", watts=12.0,
                  lumens=950.0, cct_k=4000, cri=90, dimmable=True, load_va=12.0,
                  ports=_POWER_120,
                  source="ELCO Lighting EL49LDICA, 4\" IC airtight, black baffle (4000K tap)"),
    # Same housing, wet-listed: a can over a tub or inside a shower enclosure is in a wet
    # location, and every bath can here is specified that way rather than sorting them by
    # which side of the curtain they fall on.
    LuminaireType(tag="ED-T-LT-CAN4-WET", name='4" recessed can, wet location, black baffle',
                  form=LuminaireForm.RECESSED_CAN, type_mark="B",
                  footprint=(inch(5), inch(5)), height=inch(6), plan_symbol="recessed-can",
                  lamp="LED module, field replaceable", watts=12.0, lumens=900.0,
                  cct_k=3000, cri=90, dimmable=True, damp_rated=True, wet_rated=True,
                  load_va=12.0, ports=_POWER_120,
                  source="ELCO Lighting EL49LDICA + wet-location shower trim"),
    LuminaireType(tag="ED-T-LT-CAN3", name='3" recessed can, black baffle trim',
                  form=LuminaireForm.RECESSED_CAN, type_mark="C",
                  footprint=(inch(3.75), inch(3.75)), height=inch(5),
                  plan_symbol="recessed-can",
                  lamp="LED module, field replaceable", watts=9.0, lumens=650.0,
                  cct_k=3000, cri=90, dimmable=True, load_va=9.0, ports=_POWER_120,
                  source="ELCO Lighting EL39LDICA, 3\" IC airtight, black baffle"),

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
    LuminaireType(tag="ED-T-LT-STRIP24", name="24V LED tape in aluminium cove channel",
                  form=LuminaireForm.STRIP, type_mark="E",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED tape, 24V DC", watts_per_ft=3.0, lumens=250.0,
                  cct_k=3000, cri=90, voltage=24, dimmable=True),

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
    LuminaireType(tag="ED-T-LT-STRIP24-TASK",
                  name="24V LED task tape in aluminium channel, deep frosted diffuser",
                  form=LuminaireForm.STRIP, type_mark="U",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED tape, 24V DC, high-output", watts_per_ft=5.0, lumens=400.0,
                  cct_k=3000, cri=90, voltage=24, dimmable=True,
                  source="High-output 24V task tape in an aluminium channel with a DEEP "
                         "FROSTED diffuser, behind a light rail/valance at the cabinet "
                         "nose. Both are spec, not trim: a bare tape reflects as a row of "
                         "dots in a polished counter, and an unshielded diode line is "
                         "visible from a seated position at the peninsula."),

    # --- F: the plant-room tubes ------------------------------------------------------
    # Growth-spectrum, hung on a cable suspension kit over the plants at the south windows.
    # Multi-watt selectable; specified at the 50 W setting because the point of putting them
    # here is supplementing a north-of-45 winter.
    #
    # WET rated and UL 8800 listed, not merely damp (2026-08-18). Both are requirements, not
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
                  lamp="LED integrated", watts=18.0, lumens=1500.0, cct_k=2700, cri=90,
                  dimmable=True, load_va=18.0, ports=_POWER_120),

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
    LuminaireType(tag="ED-T-LT-SLOT72", name='72" vertical linear LED slot',
                  form=LuminaireForm.WALL_LAMP, type_mark="T",
                  footprint=(inch(2), inch(2)), height=ft(6), plan_symbol="linear-light",
                  lamp="LED integrated, integral 120V driver", watts=24.0, lumens=2000.0,
                  cct_k=3000, cri=90, dimmable=True, load_va=24.0, ports=_POWER_120),

    # --- H/J/K: sconces ---------------------------------------------------------------
    # Up-and-down for the basement theatre, on a dimmer: the traditional answer for a room
    # you want lit enough to walk through and dark enough to watch something in.
    LuminaireType(tag="ED-T-LT-SCONCE-UD", name="Up/down wall sconce",
                  form=LuminaireForm.SCONCE, type_mark="H",
                  footprint=(inch(6), inch(4)), height=inch(12),
                  plan_symbol="sconce-updown",
                  lamp="LED integrated, 2 x 6 W", watts=12.0, lumens=700.0, cct_k=2700,
                  cri=90, dimmable=True, load_va=12.0, ports=_POWER_120),
    # Down-spot for the studies. Set back from the window wall so it lights the desk
    # without putting a lit head in the glass after dark (notes: "more privacy at night").
    LuminaireType(tag="ED-T-LT-SCONCE-SPOT", name="Adjustable down-spot wall sconce",
                  form=LuminaireForm.SCONCE, type_mark="J",
                  footprint=(inch(5), inch(4)), height=inch(9), plan_symbol="sconce-spot",
                  lamp="LED integrated", watts=8.0, lumens=600.0, cct_k=3000, cri=90,
                  dimmable=True, load_va=8.0, ports=_POWER_120),
    # Same fixture with the switch on it. RM-A-DEN is a 43 ft2 attic nook reached by a
    # hatch — there is no wall on the way in to put a switch on, so the fixture carries it.
    # ``integral_switch`` is what exempts it from ``electrical.lighting_controls``.
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
                  source="ED-T-LT-SCONCE-SPOT in a wet-location housing (notes/plant_room.md)"),
    LuminaireType(tag="ED-T-LT-SPOT-SW", name="Down-spot wall sconce, switch on fixture",
                  form=LuminaireForm.SCONCE, type_mark="J1",
                  footprint=(inch(5), inch(4)), height=inch(9), plan_symbol="sconce-spot",
                  lamp="LED integrated", watts=8.0, lumens=600.0, cct_k=3000, cri=90,
                  integral_switch=True, load_va=8.0, ports=_POWER_120),
    LuminaireType(tag="ED-T-LT-SCONCE-STAIR", name="Stair wall sconce",
                  form=LuminaireForm.SCONCE, type_mark="K",
                  footprint=(inch(5), inch(4)), height=inch(8), plan_symbol="sconce",
                  lamp="LED integrated", watts=6.0, lumens=400.0, cct_k=2700, cri=90,
                  dimmable=True, load_va=6.0, ports=_POWER_120),

    # --- L/M: hanging fixtures --------------------------------------------------------
    # ``height`` on a hanging fixture is the *whole assembly* — canopy, drop, shade — which
    # is what lets ``Mount(CEILING, drop=height)` land the canopy on the ceiling and read
    # the bottom of the shade off the same number (→ placeable_symbols/lighting.pendant).
    LuminaireType(tag="ED-T-LT-CHANDELIER", name="6-arm chandelier over the stairwell",
                  form=LuminaireForm.CHANDELIER, type_mark="L",
                  footprint=(inch(30), inch(30)), height=ft(4), plan_symbol="chandelier",
                  lamp="6 x E12 LED candelabra", watts=24.0, lumens=2400.0, cct_k=2700,
                  cri=90, dimmable=True, load_va=24.0, ports=_POWER_120),
    LuminaireType(tag="ED-T-LT-PENDANT", name="Dining pendant",
                  form=LuminaireForm.PENDANT, type_mark="M",
                  footprint=(inch(18), inch(18)), height=ft(3, 6), plan_symbol="pendant",
                  lamp="LED integrated", watts=15.0, lumens=1200.0, cct_k=2700, cri=90,
                  dimmable=True, load_va=15.0, ports=_POWER_120),

    # --- N: ceiling fans with a light kit ---------------------------------------------
    # A fan-light is a luminaire here, not Equipment: there is no fan ``EquipmentKind``, no
    # HVAC check reads one, and every form in this catalog exports as the same
    # ``IfcLightFixture`` regardless. ``load_va`` carries motor *and* light; ``watts`` is
    # the light kit alone, because that is what the photometric row means.
    LuminaireType(tag="ED-T-LT-FAN52", name='52" ceiling fan with LED light kit',
                  form=LuminaireForm.CEILING_FAN_LIGHT, type_mark="N",
                  footprint=(inch(52), inch(52)), height=ft(1, 6),
                  plan_symbol="ceiling-fan-light",
                  lamp="LED integrated light kit", watts=17.0, lumens=1400.0, cct_k=3000,
                  cri=90, dimmable=True, load_va=60.0, ports=_POWER_120),
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
                  cri=90, dimmable=True, damp_rated=True, wet_rated=True, load_va=60.0,
                  ports=_POWER_120,
                  source="NEC 2023 damp/wet location; RM-S-PLANT is a damp location throughout and wet where it is misted (notes/plant_room.md)"),
    # The porch fan. Damp rated because it lives under the balcony deck, open on three
    # sides — not wet rated: nothing lands on it, the deck above is the roof.
    LuminaireType(tag="ED-T-LT-FAN60", name='60" porch ceiling fan with LED light kit, damp',
                  form=LuminaireForm.CEILING_FAN_LIGHT, type_mark="N1",
                  footprint=(inch(60), inch(60)), height=ft(1, 6),
                  plan_symbol="ceiling-fan-light",
                  lamp="LED integrated light kit", watts=17.0, lumens=1400.0, cct_k=3000,
                  cri=90, dimmable=True, damp_rated=True, load_va=75.0, ports=_POWER_120),

    # --- Q: the garage shop light -----------------------------------------------------
    # A garage is an unconditioned, unheated space that cars drive snow into, so the shop
    # light is damp rated even though nothing rains on it. This replaced the generic
    # ED-T-LIGHT the whole house used to run on — a fixture with no lamp, no lumens and no
    # listing is not something a schedule can print a row for.
    LuminaireType(tag="ED-T-LT-SHOP4", name="4' LED shop light, damp, surface mount",
                  form=LuminaireForm.LINEAR_TUBE, type_mark="Q",
                  footprint=(ft(4), inch(5)), height=inch(3), plan_symbol="linear-light",
                  lamp="LED integrated", watts=40.0, lumens=4400.0, cct_k=4000, cri=80,
                  damp_rated=True, load_va=40.0, ports=_POWER_120),

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
    # The master's lit mirror. Three things from the brief are specifications, not taste:
    # front-lit (most rings are edge-lit, which backlights the face and is useless for
    # shaving or makeup), a controller that remembers its last setting, and a status LED
    # dim enough to sleep beside. Hardwired — which is why plan/lighting.py also puts a
    # GFCI receptacle in the wall behind it (electrical_notes.md line 80).
    LuminaireType(tag="ED-T-LT-MIRROR-RING", name='36" front-lit LED ring mirror, tunable',
                  form=LuminaireForm.MIRROR_LIGHT, type_mark="P1",
                  footprint=(inch(36), inch(3)), height=inch(36), plan_symbol="linear-light",
                  lamp="LED integrated, front-lit, memory controller", watts=40.0,
                  lumens=2600.0, cct_k=4000, cri=95, dimmable=True, damp_rated=True,
                  load_va=40.0, ports=_POWER_120),
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
                         source="Mean Well LPV-60-24 (IP67) in a 4-11/16\" ceiling box"),
    ElectricalDeviceType(tag="ED-T-LT-PSU-200", name="24V LED driver, 200 W, in-ceiling box",
                         footprint=(inch(12), inch(8)), height=inch(4),
                         load_va=200.0, ports=_POWER_120,
                         source="Mean Well LPV-200-24 (IP67) in a ceiling enclosure"),
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

LIGHTING_TYPES = (*LUMINAIRE_TYPES, *LIGHTING_DEVICE_TYPES)
