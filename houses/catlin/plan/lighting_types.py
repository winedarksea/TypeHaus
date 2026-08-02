"""Catlin luminaire *type* catalog — the E-602 schedule's marks A through P.

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

    # --- F: the plant-room tubes ------------------------------------------------------
    # Damp rated and growth-spectrum, hung on a cable suspension kit over the plants at the
    # south windows. Multi-watt selectable; specified at the 50 W setting because the point
    # of putting them here is supplementing a north-of-45 winter.
    LuminaireType(tag="ED-T-LT-TUBE6", name="6' suspended linear tube, damp, growth spectrum",
                  form=LuminaireForm.LINEAR_TUBE, type_mark="F",
                  footprint=(ft(6), inch(3)), height=ft(2, 3),
                  plan_symbol="suspended-linear-light",
                  lamp="T8 LED, multi-watt selectable 25/40/50 W", watts=50.0,
                  lumens=6000.0, cct_k=3500, cri=90, dimmable=True, damp_rated=True,
                  load_va=50.0, ports=_POWER_120,
                  source="superiorlighting.com decorative linear LED tube, 6', black, "
                         "120-277V, on a T8 harness + cable suspension kit"),

    # --- G: the suite's over-bed wall lamp --------------------------------------------
    LuminaireType(tag="ED-T-LT-WALL-LINEAR", name="36\" linear LED wall lamp",
                  form=LuminaireForm.WALL_LAMP, type_mark="G",
                  footprint=(ft(3), inch(3)), height=inch(4), plan_symbol="linear-light",
                  lamp="LED integrated", watts=18.0, lumens=1500.0, cct_k=2700, cri=90,
                  dimmable=True, load_va=18.0, ports=_POWER_120),

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
