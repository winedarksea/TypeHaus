"""Catlin luminaire *type* catalog — the E-602 schedule's marks A to Z and their variants.

NOT ``# haus: editable``: like ``fixture_types.py`` these are catalog type definitions,
not placed instances, and ``ElectricalDeviceType.needs`` is a ``frozenset``, which the
editable dialect forbids. The movable instances that reference these tags live in
``plan/lighting_*.py`` (editable, so UI drags round-trip).

Every entry is a ``LuminaireType`` — an ``ElectricalDeviceType`` subclass, so it rides in
``Library.electrical_device_types`` beside the receptacles and the panel and needs no new
library collection. Plain ``ElectricalDeviceType`` entries come along for the ride: the
24V supplies the LED runs feed from and the tape controller. Switch types live in
``plan/device_types.py``.

Marks are the schedule letters and must stay unique — ``tests/test_lighting_takeoff.py``
pins that. I and O are skipped (they read as digits), and every letter is taken, so a new
type is a numbered variant of its family (A4, E4-E6, J2, P6, Q1, Q2, U1).

Two wattages, deliberately different:
- ``watts`` is the *lamp* load — what the photometric row means.
- ``load_va`` is the *connected* load the panel schedule sums, which for a fan-light
  includes the motor and for a 24V run's PSU is the supply's rating, not the tape's.

Every installed type names its ``Product`` through ``product_ref`` (2026-10-28 selections:
plan/products_lighting_selected.py), and E-602 prints its brand and model. A can's
``product_ref`` is its housing; its trim and lamp are ``parts``.
"""

from __future__ import annotations

from library.lighting import luminaire_class

from plan.closet_types import CLOSET_LUMINAIRE_TYPES, CLOSET_SUPPLY_TYPES
from plan.laundry_lighting_types import LAUNDRY_TRACK
from plan.lighting_types_decor import DECORATIVE_LUMINAIRE_TYPES
from typehaus import ElectricalDeviceType, LuminaireForm, Service, ServicePort, ft, inch
from typehaus.library.track_lighting import PUREEDGE_SUPPLY
from typehaus.model import LuminaireType, ProductPart

# Every line-voltage luminaire lands on a 120V branch; one port tuple serves them all
# (``electrical.circuit_refs`` checks poles against ports, and these are all 1-pole).
_POWER_120 = (ServicePort(tag="power", service=Service.POWER_120,
                          position=(ft(0), ft(0), ft(0))),)

# --- The recessed cans (2026-10-31) -----------------------------------------------------
# ONE housing everywhere, the Nora NSIC-401QAT (4", IC, airtight, E26, 6" tall); a tier is a
# trim and a lamp, billed as their own part lines. A replaceable lamp outlives the integrated
# module it replaces, and dims for free. The cans light the walls, not the floor; dimming and
# tunable CCT ride on the tape. Where a 6" body cannot fit (ccSPF roof bays, soffits, a run
# the layout cannot dodge) the can is mark C, the 2 1/4" wafer.
_HOUSING = "PROD-NORA-NSIC-401QAT"


def _can(tag: str, mark: str, name: str, trim: str, lamp: str, watts: float, lumens: float,
         cct_k: int, cri: int, source: str, **extra: object) -> LuminaireType:
    return LuminaireType(
        tag=tag, name=name, form=LuminaireForm.RECESSED_CAN, type_mark=mark,
        footprint=(inch(5), inch(5)), height=inch(6), plan_symbol="recessed-can",
        lamp="PAR20 LED, E26, replaceable", watts=watts, lumens=lumens, cct_k=cct_k,
        cri=cri, dimmable=True, load_va=watts, ports=_POWER_120, product_ref=_HOUSING,
        replaceable_lamp=True, lamp_base="E26",
        parts=(ProductPart(role="trim", product_ref=trim),
               ProductPart(role="lamp", product_ref=lamp)),
        source=source, **extra)


_STEPPED, _GIMBAL, _SHOWER = "PROD-NORA-NS-40P", "PROD-NORA-NS-12", "PROD-NORA-NS-76W"
_WET = {"damp_rated": True, "wet_rated": True}


AMBIENT_LUMINAIRE_TYPES = (
    # --- A-C: recessed cans --------------------------------------------------------------
    # A white stepped baffle, not black: the regress hides the lamp, the trim disappears in a
    # white ceiling, and a smooth step wipes clean.
    _can("ED-T-LT-CAN4", "A", '4" recessed can, white stepped baffle, PAR20 3000K',
         _STEPPED, "PROD-BULBRITE-PAR20-90-30K", 6.5, 500.0, 3000, 90,
         "Nora NSIC-401QAT + NS-40P + 90-CRI PAR20 40 deg: the cheap, efficient tier "
         "(halls, closets, basement, bedrooms, kitchen, mudroom, mechanical).",
         damp_rated=True),
    # A1: the lounge's day layer, over the puzzle table. CCT is a type property everywhere it
    # matters (E-602, IFC), so two CCTs in one room are two schedule rows. Do not fold this
    # into A. 5000 K since the 2026-10-31 review (the day layer is >= 5000 K; was 4000 K).
    _can("ED-T-LT-CAN4-5000", "A1", '4" recessed can, white stepped baffle, PAR20 5000K',
         _STEPPED, "PROD-PAR20-90-50K-WET", 6.5, 520.0, 5000, 90,
         "Mark A's housing and trim with a 5000 K 90-CRI lamp: RM-M-LIVING's day layer.",
         damp_rated=True),
    # A2/A3: the premium tier, RM-M-LIVING and RM-M-BED only. Same housing; the 95-CRI lamp.
    _can("ED-T-LT-CAN4-PREM", "A2", '4" recessed can, white stepped baffle, 95-CRI PAR20',
         _STEPPED, "PROD-SORAA-VIVID-PAR20-30K-36", 10.8, 540.0, 3000, 95,
         "Nora NSIC-401QAT + NS-40P + Soraa Vivid PAR20 (95 CRI, R9 95, 36 deg).",
         damp_rated=True),
    _can("ED-T-LT-CAN4-PREM-GIMBAL", "A3", '4" recessed can, white gimbal, 95-CRI PAR20',
         _GIMBAL, "PROD-SORAA-VIVID-PAR20-30K-25", 10.8, 540.0, 3000, 95,
         "Nora NSIC-401QAT + NS-12 gimbal + Soraa Vivid PAR20 25 deg, aimed at a wall, "
         "a bookcase or the mantel from 24-36 in. off it."),
    # A4: kitchen task cans (2026-10-31): mark A's stepped trim with the 25 deg 95-CRI lamp,
    # so the sink, range and peninsula get a tight pool where A's 40 deg spreads.
    _can("ED-T-LT-CAN4-TASK", "A4", '4" recessed can, white stepped baffle, 25 deg 95-CRI PAR20',
         _STEPPED, "PROD-SORAA-VIVID-PAR20-30K-25", 10.8, 540.0, 3000, 95,
         "Nora NSIC-401QAT + NS-40P + Soraa Vivid PAR20 25 deg: kitchen work zones.",
         damp_rated=True),
    # B/B1/B2: showers and tubs. The same housing behind the lensless wet trim.
    _can("ED-T-LT-CAN4-WET", "B", '4" recessed can, wet, white shower baffle, PAR20 3000K',
         _SHOWER, "PROD-BULBRITE-PAR20-90-30K", 6.5, 500.0, 3000, 90,
         "Nora NSIC-401QAT + NS-76W + wet-rated 90-CRI PAR20 (CONFIRM the NS-76W listing).",
         **_WET),
    # B1/B2: RM-M-BATH2's two layers (notes/bath2_lighting.md): 5000 K on the day toggle,
    # 2700 K on the evening toggle. Separate marks so the electrician knows which lamp
    # goes where.
    _can("ED-T-LT-CAN4-WET-5000", "B1", '4" recessed can, wet, white shower baffle, 5000K',
         _SHOWER, "PROD-PAR20-90-50K-WET", 6.5, 520.0, 5000, 90,
         "Mark B with a wet-rated 5000 K lamp: BATH2's day layer (CONFIRM the lamp).", **_WET),
    _can("ED-T-LT-CAN4-WET-2700", "B2", '4" recessed can, wet, white shower baffle, 2700K',
         _SHOWER, "PROD-BULBRITE-PAR20-90-27K", 6.5, 480.0, 2700, 90,
         "Mark B with a 2700 K lamp, on BATH2's evening toggle inside the shower glass.",
         **_WET),
    LuminaireType(tag="ED-T-LT-WAFER4",
                  replaceable_lamp=False, name='4" wafer downlight, deep regressed, wet',
                  form=LuminaireForm.RECESSED_CAN, type_mark="C",
                  footprint=(inch(5), inch(5)), height=inch(2.25), plan_symbol="recessed-can",
                  lamp="LED integrated, canless, set to 3000K", watts=14.5, lumens=900.0,
                  cct_k=3000, cri=90, dimmable=True, damp_rated=True, wet_rated=True,
                  load_va=14.5, ports=_POWER_120, product_ref="PROD-JUNO-WF4-DREG-B",
                  source="Juno WF4 DREG: only where the 6 in. housing cannot fit (a ccSPF "
                         "roof bay, a soffit, a run the layout cannot dodge)."),

    # --- D: flat panels (kitchen, fitness, workshop) ----------------------------------
    LuminaireType(tag="ED-T-LT-PANEL",
                  replaceable_lamp=False, name="2x4 LED flat panel, surface kit, 4000K",
                  form=LuminaireForm.PANEL, type_mark="D",
                  footprint=(inch(47.75), inch(23.75)), height=inch(2.5),
                  plan_symbol="panel-light", lamp="LED integrated, 0-10V", watts=60.0,
                  lumens=5100.0, cct_k=4000, dimmable=True, load_va=60.0, ports=_POWER_120,
                  product_ref="PROD-WESTGATE-LP-2X4-60W-40K-D",
                  source="Westgate LP-2X4-60W-40K-D (spec sheet), fixed 4000 K, on the "
                         "LP-SRFC-2X4 surface kit; 2.5\" depth with the kit is an allowance."),

    # --- E: the 24V tape (the basement stair rail; the coves are E4/E6 since 2026-10-31) --
    # No ports and no plan symbol: this type is never placed as a device. It is named by a
    # ``LightRun`` polyline, priced per lineal foot off ``watts_per_ft``, and fed at 24V
    # from a PSU rather than from a branch circuit — which is what makes it a UPS-backed
    # light source instead of one more 120V load.
    # ** COB, AND THAT IS A SPECIFICATION (2026-09-06). ** The dots a cove tape shows are
    # geometry, not quality: a diffuser only blends discrete emitters when the standoff is at
    # least one LED pitch, which at 60 LED/m is a 16-25 mm deep channel — and most "slim"
    # channels are 8-9 mm, which is why people buy slim channel plus a frosted lens and see
    # dots anyway. COB is a continuous phosphor strip with NO discrete emitters: dot-free in
    # a shallow channel with a light lens, and it does not pay the 15-30% (opal) or 40-60%
    # (smoked) lumen tax a deep diffuser charges.
    LuminaireType(tag="ED-T-LT-STRIP24",
                  replaceable_lamp=True, name="24V COB LED tape in aluminium cove channel",
                  form=LuminaireForm.STRIP, type_mark="E",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED tape, 24V DC, COB", watts_per_ft=3.0, lumens=250.0,
                  cct_k=3000, cri=90, voltage=24, dimmable=True,
                  product_ref="PROD-ARMACOST-RIBBONFLEX-COB",
                  source="Armacost RibbonFlex Pro 24V COB, 3000K: the basement stair rail "
                         "(and mark T's tape). The coves are E4/E6 since 2026-10-31."),

    # --- E3: RM-M-BATH2's evening glow (2026-10-12) ------------------------------------
    # Mark E's tape in a fixed 2700 K, damp-rated (silicone-coated), in the ceiling over the
    # tub (the cabinet run retired 2026-11-03). The evening layer, on a plain toggle; the
    # halo mirror is on its own plug. Prices on its
    # own [light_run_materials] keys.
    LuminaireType(tag="ED-T-LT-STRIP24-2700", replaceable_lamp=True,
                  name="24V COB LED tape, 2700K, damp, in aluminium channel",
                  form=LuminaireForm.STRIP, type_mark="E3",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED tape, 24V DC, COB, silicone-coated", watts_per_ft=3.0,
                  lumens=230.0, cct_k=2700, cri=90, voltage=24, dimmable=True,
                  damp_rated=True,
                  product_ref="PROD-ARMACOST-RIBBONFLEX-COB-2700",
                  source="Armacost RibbonFlex Pro 24V COB family in 2700K, silicone-coated "
                         "for a damp room (confirm the damp SKU). Ceiling over the tub in "
                         "RM-M-BATH2."),

    # --- E4/E6: the 2026-10-31 review's tape variants (E5 retired 2026-11-03) --------
    # E4: the lounge and dining coves in RGB+CCT. The white channels carry the room; colour
    # is a scene. Fed by a non-dimming HLG driver through a 5-in-1 controller, which dims.
    LuminaireType(tag="ED-T-LT-STRIP24-RGBCCT",
                  replaceable_lamp=True, color_mode="rgbcct", cct_range_k=(2700, 6500),
                  name="24V RGB+CCT COB LED tape in the shadow-gap reveal",
                  form=LuminaireForm.STRIP, type_mark="E4",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED tape, 24V DC, RGB+CCT COB, 12 mm", watts_per_ft=5.0, lumens=300.0,
                  cct_k=3000, cri=90, voltage=24, dimmable=True,
                  product_ref="PROD-SLL-COB-RGBCCT-24V",
                  source="SuperLightingLED DC24V RGB+CCT COB, 12 mm, white channels 2700-6500 K "
                         "CRI 90+; GL-C-001P controller in RGBCCT mode."),
    # E6: the second-floor hall cove in tunable white, with a low warm night preset.
    LuminaireType(tag="ED-T-LT-STRIP24-TUNABLE",
                  replaceable_lamp=True, color_mode="tunable", cct_range_k=(2700, 6500),
                  name="24V tunable-white COB LED tape in the shadow-gap reveal",
                  form=LuminaireForm.STRIP, type_mark="E6",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED tape, 24V DC, tunable-white COB, 10 mm", watts_per_ft=3.0,
                  lumens=250.0, cct_k=2700, cri=90, voltage=24, dimmable=True,
                  product_ref="PROD-SLL-COB-CCT-24V",
                  source="SuperLightingLED DC24V tunable COB 2700-6500 K, CRI 90+; GL-C-001P "
                         "in CCT mode. cct_k is the warm (night) end."),

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
        "replaceable_lamp": False,
        "source": "Schluter KB12SNLT2WW + LIPROTEC-ECD LTECD1W, 3000 K, ~118 lm. Dims only "
                  "from Schluter-listed dimmers (DVELV-300P)."}),

    # --- U: the kitchen's under-cabinet task tape -------------------------------------
    # A SEPARATE TYPE FROM E, NOT A LONGER RUN OF IT, and the whole reason is output.
    # ED-T-LT-STRIP24 is cove tape: 3 W/ft, ~250 lm/ft through the lens (Armacost lists 315
    # bare), right for washing a ceiling and not a task light. A work counter wants 350-500 lm/ft — 4 to 6 W/ft —
    # so this is 5 W/ft at roughly 400 lm/ft. Same 24V family so it shares the PSU idiom and
    # the per-lineal-foot pricing; a separate mark so a future reader cannot "simplify" the
    # cove tape and the task tape into one row, which would either underlight the counter or
    # triple the load on the cove runs.
    #
    # 0 ea since 2026-10-31: the kitchen is U1 MITTLED under A/A4 3000 K cans (A1 is the
    # 5000 K day can); this is the revert if the counters read short.
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
    LuminaireType(tag="ED-T-LT-STRIP24-TASK", replaceable_lamp=True,
                  name="24V COB LED task tape in aluminium channel, CRI 95",
                  form=LuminaireForm.STRIP, type_mark="U",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED tape, 24V DC, high-output COB", watts_per_ft=5.0, lumens=400.0,
                  cct_k=3000, cri=95, voltage=24, dimmable=True,
                  product_ref="PROD-DIODE-VALENT-X",
                  source="Diode LED VALENT X, 3000K, 95+ CRI / R9 90+, behind a light "
                         "rail/valance at the cabinet nose."),
    # U1: the owner's preferred under-cabinet light, IKEA MITTLED, fixed white on its own
    # TRADFRI driver. ~208 lm/ft at 2700 K against U's ~400 at 3000 K: U stays as the
    # fallback if the counter reads short (the 2026-10-31 rule: keep MITTLED unless it falls
    # well short of ~300 lm/ft). Billed by the foot as tape, like the closet's OVERSIDAN.
    LuminaireType(tag="ED-T-LT-MITTLED",
                  replaceable_lamp=False, name="IKEA MITTLED LED countertop strip, dimmable",
                  form=LuminaireForm.STRIP, type_mark="U1",
                  footprint=(inch(0.75), inch(0.5)), height=inch(0.4),
                  lamp="LED integrated strip, IKEA 24V system", watts_per_ft=2.8, lumens=208.0,
                  cct_k=2700, cri=90, voltage=24, dimmable=True,
                  product_ref="PROD-IKEA-MITTLED",
                  source="IKEA MITTLED: CRI > 90, 2700 K, 60 cm 410 lm / 5.5 W. TRADFRI 30 W "
                         "driver; Dirigera (Matter bridge) or plain on/off at the receptacle."),

    # --- W: the garage's exterior linear (eave soffits + the north gable) --------------
    # ** COMMODITY PARTS, STANDARD SIZE, 24V (2026-10-28). ** The WAC InvisiLED kit was
    # ~$2,900 of tape for 73.5 LF; this is an off-the-shelf IP67 COB tape in a generic
    # 1/2" aluminium U-channel with a clear cover, each run split in two halves, each half on
    # its own Class 2 HLG-100H (PSU-96-WE) INDOORS behind a GL-C-001P. No fixture listing is
    # claimed: the tape is cheap to swap, and the listed part is the Class 2 driver.
    #
    # ** damp_rated AND wet_rated ARE IP67, NOT A UL WET LISTING. ** Every run is under a
    # soffit, aperture down, in a closed channel; the gable run is the wet one (NEC 410.10).
    #
    # ** full_cutoff IS A MOUNTING INSTRUCTION AS MUCH AS A PRODUCT ATTRIBUTE. ** Aperture
    # DOWN: `advisory.dark_sky_lighting` exempts the soffit runs and grades the gable run on
    # this flag, so the flag and the detail must stay in step.
    # ** RGBW SINCE 2026-10-31 ** (owner): W = 3000 K holds the dark-sky white line; colour
    # is for occasions. One GL-C-001P (RGBW mode) beside each driver. The single-white
    # SK-512BB10 is the revert.
    LuminaireType(tag="ED-T-LT-LINEAR-EXT",
                  replaceable_lamp=True,
                  color_mode="rgbw", name="Exterior 24V RGBW COB tape in clear channel, IP67",
                  form=LuminaireForm.STRIP, type_mark="W",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.25),
                  lamp="RGBW COB LED tape, 24V DC, IP67 silicone tube, in a 1/2 in. U-channel",
                  watts_per_ft=4.5, lumens=300.0, cct_k=3000, cri=90, voltage=24,
                  dimmable=True, damp_rated=True, wet_rated=True, full_cutoff=True,
                  product_ref="PROD-SLL-COB-RGBW-IP67-30",
                  source="SuperLightingLED 24V RGBW COB, IP67 tube, W 3000 K; generic "
                         "aluminium U-channel, clear cover, aperture down. CONFIRM W/ft."),

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
    LuminaireType(tag="ED-T-LT-STRIP24-SAUNA", replaceable_lamp=True, type_mark="X",
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
    LuminaireType(tag="ED-T-LT-GROW-BAR",
                  replaceable_lamp=False, name='45" horticultural LED grow bar, UL 8800, damp',
                  form=LuminaireForm.LINEAR_TUBE, type_mark="F",
                  footprint=(inch(44.78), inch(2.5)), height=ft(2, 3),
                  plan_symbol="suspended-flat-bar",
                  lamp="LED integrated, on-board driver, 1-10V", watts=90.0, lumens=11280.0,
                  cri=92, dimmable=True, damp_rated=True, load_va=90.0, ports=_POWER_120,
                  product_ref="PROD-BARRON-AG90-W-001",
                  source="Barron Growlite Varius AG90-W-001 (spec sheet), ETL to UL 8800, "
                         "damp; hung on its safety cable. CCT and hanger kit CONFIRM."),

    # --- G: the suite's over-bed wall lamp --------------------------------------------
    LuminaireType(tag="ED-T-LT-WALL-LINEAR",
                  replaceable_lamp=False, name='24" linear LED wall light, brushed black',
                  form=LuminaireForm.WALL_LAMP, type_mark="G",
                  footprint=(inch(24), inch(2)), height=inch(4), plan_symbol="linear-light",
                  lamp="LED integrated, ELV", watts=22.0, lumens=1140.0, cct_k=3000, cri=90,
                  dimmable=True, damp_rated=True, load_va=22.0, ports=_POWER_120,
                  product_ref="PROD-WAC-WS-6724-30-BK",
                  source="WAC dweLED LINE WS-6724-30-BK (spec sheet), 3000 K with the house "
                         "standard: 2700 K makes white oak read orange."),

    # --- T: RM-M-PANTRY's jamb channels (2026-10-30) ------------------------------------
    # Four, one per inside face of the shelf uprights, 1" behind the shelf front, aimed into
    # the bay: each bay is lit from both sides, so the gable shades nothing. A WALL_LAMP and
    # not a LightRun because a vertical run has no length in plan (``LightRun.path`` is plan
    # only): the body's base is the mount elevation and ``height`` measures up from it.
    # Shop-fitted to the ply, so no wall box. Generic 90-CRI COB since 2026-10-31 (VALENT X
    # was over-spec for a pantry): mark E's tape, so all four (24 ft at 3 W/ft, 72 W) want
    # the 200 W OMNIDRIVE X, ED-M-PANTRY-LT-PSU.
    LuminaireType(tag="ED-T-LT-JAMB72",
                  replaceable_lamp=True, name='72" vertical 45-degree LED channel, shelf jamb',
                  form=LuminaireForm.WALL_LAMP, type_mark="T",
                  footprint=(inch(0.75), inch(0.75)), height=ft(6), plan_symbol="linear-light",
                  lamp="24V COB tape, 3 W/ft, in a 45-degree channel, remote driver",
                  watts=18.0, lumens=1500.0, cct_k=3000, cri=90, voltage=24, dimmable=True,
                  device_box=False, product_ref="PROD-ARMACOST-RIBBONFLEX-COB",
                  parts=(ProductPart(role="frame", product_ref="PROD-CHANNEL-45-GENERIC",
                                     length=inch(72)),),
                  source="Armacost RibbonFlex Pro 24V COB 3000 K (mark E's tape) in a "
                         "standard 45-degree channel cut to 72 in."),
)


# --- 24V supplies and the tape controller ----------------------------------------------
# Not luminaires, so plain ``ElectricalDeviceType``: a PSU is a junction box with a driver
# in it. The switch types live in plan/device_types.py.
#
# Per-area supplies rather than one central 24V bus. A house-wide 24V distribution would
# mean 24V home runs the length of the building, where the voltage drop that matters is on
# the *low* side: 3 W/ft of tape at 24V pulls real current, and a 40' run at that voltage
# needs conductors out of proportion to the load. Two supplies in the ceiling next to their
# runs keep the long wire at 120V. The alternative is documented, not built.
LIGHTING_DEVICE_TYPES = (
    ElectricalDeviceType(tag="ED-T-LT-PSU-60", name="24V LED driver, 60 W, in-ceiling box",
                         footprint=(inch(8), inch(6)), height=inch(3),
                         load_va=60.0, output_voltage=24, ports=_POWER_120,
                         product_ref="PROD-DIODE-OMNIDRIVE-X",
                         source="Diode LED OMNIDRIVE X, 60 W — ELV + TRIAC + 0-10V in one part "
                                "and, the spec that matters, NO MINIMUM LOAD: a cheap ELV "
                                "driver with a 10-15 W minimum makes a short cove run shimmer "
                                "or fail to strike. Load to <=80% of nameplate and keep it "
                                "accessible and ventilated."),
    ElectricalDeviceType(tag="ED-T-LT-PSU-200", name="24V LED driver, 200 W, in-ceiling box",
                         footprint=(inch(12), inch(8)), height=inch(4),
                         load_va=200.0, output_voltage=24, ports=_POWER_120,
                         product_ref="PROD-DIODE-OMNIDRIVE-X",
                         source="Diode LED OMNIDRIVE X, 200 W. Same family as the 60 W; see "
                                "that entry for the no-minimum-load argument."),
    ElectricalDeviceType(tag="ED-T-LT-PSU-96-WE", name="24V LED driver, 96 W, IP65",
                         footprint=(inch(9), inch(2.7)), height=inch(1.5),
                         load_va=96.0, output_voltage=24, ports=_POWER_120,
                         product_ref="PROD-MEANWELL-HLG-100H-24A",
                         source="Mean Well HLG-100H-24A: 96 W, 24 V / 4 A, IP65, UL 8750, "
                                "228 x 68 x 38.8 mm, not dimmable."),
    # The controller is on the 24V side: no branch circuit, no load of its own worth summing.
    ElectricalDeviceType(tag="ED-T-LT-CTRL-5IN1", name="5-in-1 Zigbee LED controller, 12-54 V",
                         footprint=(inch(4.5), inch(1.8)), height=inch(0.9),
                         needs=frozenset(), product_ref="PROD-GLEDOPTO-GL-C-001P",
                         source="Gledopto GL-C-001P, set once to RGBCCT (E4), CCT (E6) or "
                                "RGBW (W). Beside its driver, accessible."),
)



# Part 1 (this file) then part 2 (plan/lighting_types_decor.py), then the supplies and
# switches. One catalog to the E-602 schedule; two files only for the 500-line rule.
LUMINAIRE_TYPES = (*AMBIENT_LUMINAIRE_TYPES, *DECORATIVE_LUMINAIRE_TYPES,
                   *CLOSET_LUMINAIRE_TYPES, LAUNDRY_TRACK)

LIGHTING_TYPES = (*LUMINAIRE_TYPES, *LIGHTING_DEVICE_TYPES, *CLOSET_SUPPLY_TYPES, PUREEDGE_SUPPLY)
