"""Catlin equipment catalog — the named HVAC/appliance products the owner has chosen.

NOT ``# haus: editable``, in the ``plan/fixture_types.py`` idiom: these are catalog type
definitions, not placed instances, so no UI drag ever writes back here. Splitting them out
of ``plan/electrical.py`` (2,412 lines, and editable) buys two things the heat-pump ratings
tables need and the editable dialect forbids: nesting beyond one level, and a ``source=``
string that may wrap across physical lines. The placed ``Equipment`` instances that
reference these tags stay in ``plan/electrical.py``, which is editable.
"""

from __future__ import annotations

from typehaus import (
    EquipmentType,
    HeatPumpRating,
    RatingBasis,
    Service,
    ServicePort,
    ft,
    inch,
)

EQUIPMENT_TYPES = (
    # RM-B-SAUNA's heated zone measures 555 cf off the resolved liner faces (8'-3 15/16" x
    # 8'-10 11/16" x 7'-6").
    #
    # ** THE 9 kW WAS UNDERSIZED, AND IT WAS THE "600 cf" CLAIM THAT WAS WRONG (2026-09-06).
    # ** The comment this replaces held 9 kW on the argument that the trade rule
    # (~1 kW / 45-50 cf, wanting 11.1-12.3 kW here) could be taken at its low end because the
    # room is basswood over foil-polyiso on all six surfaces, and that "the notes' heater is
    # rated 9 kW to 600 cf". No manufacturer researched publishes a 9 kW to 600 cf: every
    # one of their own tables puts 9 kW at 283-494 cf, and HUUM voids its warranty outright
    # if the room is dimensioned wrong. The glass partition in
    # notes/sauna_shower_basement_detail.md adds notional volume on top of the 555. The
    # comment even names the wall it is standing on — "600 cf is the wall this room is now
    # 45 cf from" — and the wall was in the wrong place.
    #
    # 10.5 kW, and it is a cascade rather than a swap. CKT-SAUNA moves 50 A -> 60 A and
    # 9000 -> 10500 VA (circuits.py), and the two sauna detail notes' sheet lines move with
    # it, because "240 V, 50 A, 10.5 kW max" was never arithmetic that closed: NEC 424.3(B)
    # makes this a continuous load at 125%, so 10500/240 = 43.75 A x 1.25 = 54.7 A and 50 A
    # will not carry it. (The 50 A WAS right for 9 kW — 37.5 x 1.25 = 46.9 A. It is the kW
    # that was wrong, not the sizing.)
    #
    # ** THE BODY IS 45" TALL AND FLOOR-STANDING, WHICH IS THE OTHER HALF OF THE CORRECTION.
    # ** The authored 18" x 16" x 30" was a placeholder box, and 30" is a height no heater in
    # this class has: they want 22-28" of width including listed clearance to combustibles
    # and 35-47" of CLEAR SPACE ABOVE. There is no heater niche in this model and none is
    # wanted — the placeholder was the heater itself — so this is a straight body-size
    # correction. The Cilindro's own numbers: 3.94" clearance all round, 37.4" of headroom
    # above, 78" minimum ceiling. RM-B-SAUNA is 7'-6" (90") clear, so the headroom closes.
    EquipmentType(tag="EQ-T-SAUNA-HEATER", name="Electric sauna heater, 10.5 kW",
                  footprint=(inch(16), inch(15)), height=inch(45),
                  plan_symbol="sauna-heater",
                  product_ref="PROD-HARVIA-PC110E",
                  source="Harvia Cilindro PC110E, 10.5 kW at 240 V 1-phase, 43.75 A nominal, rated 141-636 cf, ETL listed, 16 x 15 x 45 in., 264 lb of stone. The Xenio CX170 control (PROD-HARVIA-CX170) is MANDATORY and mounts outside the hot room - there is no built-in-control variant of this heater.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # The ERV is EQ-T-BROAN-B210E75RT in plan/mep_erv.py — an ERV with a modeled intake and
    # discharge, on `Service.OUTDOOR_AIR`/`EXHAUST_AIR`.
    # --- The three Gree heat-pump systems (plans/TODO.md §HVAC) ----------------------
    # Every unit below carries a real Gree model number and real submittal geometry; no
    # `TODO verify datasheet` remains in this file.
    #
    # ** THE SENTENCE THIS PARAGRAPH USED TO MAKE HAS BEEN OVERTURNED, AND IT IS KEPT HERE
    # ** BECAUSE IT WAS THE LOAD-BEARING CLAIM (CORRECTED 2026-09-18).
    #
    # It read: "`heating_capacity_at_design_btuh` is the number `mep.heating_capacity` sizes
    # each zone against, and it is a READ VALUE on all three systems, not an interpolation —
    # **the engine does no curve interpolation itself, so whatever is authored here IS the
    # machine as far as every check is concerned.**"
    #
    # That was an accurate description of the engine and a bad property for a model to have,
    # and it hid two defects that no amount of care in this file could have caught:
    #
    #  * A SCALAR CANNOT EXPRESS TURN-DOWN. An inverter's MINIMUM output RISES as it gets
    #    colder while the zone load falls, and where those cross is where the machine stops
    #    modulating and starts short-cycling. System 1's minimum is 10,800 Btu/h at 47 F
    #    against a 4,170 Btu/h zone load there: it cycles through most of the season, and
    #    `mep.heating_capacity` PASSED it with a +6,743 Btu/h margin because a single
    #    at-design number has nothing to say about a floor. `mep.heat_pump_turndown` is the
    #    check that can see it, and the ratings table is what it reads.
    #  * "AT DESIGN" IS A FACT ABOUT THE SITE, NOT THE TYPE. It depends on
    #    `Site.design_temp_heating`, which an `EquipmentType` has never known — so the
    #    authored number was right only for as long as nobody moved the house, and would
    #    have gone stale in silence. `takeoff/hvac.capacity_at` now reads the table at the
    #    site's own design temperature and REFUSES TO EXTRAPOLATE past either end of it
    #    (decision #76).
    #
    # So each type now carries `heating_ratings`, the published table, one row per outdoor
    # temperature with a `basis` and a REQUIRED `citation`. Every row is NEEP's ccASHP
    # listing except the two at -15 F: NEEP publishes -22, 5, 17 and 47 and nothing between,
    # and this site designs at -15, so Systems 1 and 2 carry a manufacturer row there rather
    # than an interpolation of two NEEP rows. **NEEP is the only public source that
    # publishes a MINIMUM column**, which is why it is the primary basis here even though
    # its maxima sometimes disagree with Gree's own: where they do, each row's citation
    # records the other figure in prose. THE RULE IS ONE ROW, ONE BASIS — never a blend, and
    # the validator refuses a repeated temperature so there is nowhere to hide one.
    #
    # Indoor heads still carry NO heating rating, by design: a multi's heads share one
    # compressor, and three head ratings summed would size a zone against capacity that
    # compressor cannot deliver simultaneously.
    #
    # System 1 — the concealed ducted air handler in RM-S-STUDY2's ceiling bulkhead
    # (SF-S-HP1) feeding the hallway trunk to the bedrooms plus the south branch and two
    # attic boots; FLEXX Ultra R32 outdoor unit. One 24k system covers the whole upstairs.
    #
    # ** IT REPLACED EQ-T-GREE-DUC24 / EQ-T-GREE-VIREO-GEN3, AND THAT PAIRING WAS SHORT. **
    # The DUC24/VIR24 record was wrong in three ways at once, all of them found by checking
    # it back against Gree's own submittals and Extended Ratings rather than against itself:
    #
    #  * AIRFLOW. `source=` claimed 577-1030 cfm. The real ceiling for the DUC24/VIR24 pair
    #    is 736 cfm at 0.8 in. w.c. — under the 750 cfm this duct system is sized to.
    #  * CAPACITY AT DESIGN. 13,500 Btu/h was a linear interpolation between two chart
    #    points; the read value at -15 F is 14,606. Either way the zone's 15,164 Btu/h block
    #    load was ABOVE it: 89% of load, and `mep.heating_capacity` only passed because
    #    EQ-S-HP1-STRIP's 6,800 Btu/h was being credited to the zone.
    #  * AUX HEAT. The DUC24 HAS NO AUX-HEAT TERMINAL. The strip heater the shortfall was
    #    covered with could not be interlocked with the heat pump at all, so the credit the
    #    check was granting described a machine that cannot be built.
    #
    # The FLEXX Ultra answers all three — 760 cfm, 21,000 Btu/h read at -15 F (138% of the
    # load, unaided), 24 VAC control with an aux-heat terminal — and is ENERGY STAR Cold
    # Climate certified where the Vireo is not. HSPF2 goes 9.0 -> 10.0.
    #
    # ** TWO MISREADS IN THAT SENTENCE, BOTH CORRECTED 2026-09-12 (BLD-08). ** Neither
    # changes the decision; both were the same kind of error as the DUC24 record above, which
    # is why they are written down rather than quietly fixed.
    #
    #  * "760 cfm AT 1.0 in. w.c." WAS THE WRONG COLUMN. The fan table gives 760 cfm at
    #    **speed 3, 0.5 in. ESP**. At 1.0 in. the only speed that reaches the duct system at
    #    all is speed 5, at 850 cfm. The 750 cfm this duct system is sized to is comfortably
    #    inside either reading, so the machine is still right; what was wrong was the claim
    #    about WHERE on the curve it sits, and a static budget built on 1.0 in. would have
    #    been built on nothing.
    #  * "A FACTORY HEAT KIT" IS A FIELD ACCESSORY. The cabinet ACCEPTS an electric heat kit
    #    (5 / 6 / 10 kW) and it is ordered and installed separately, not fitted at the works.
    #    ** The interlock argument is untouched by this ** and it is the argument that
    #    mattered: the cabinet has the aux-heat terminal the DUC24 lacked, so a strip heater
    #    here CAN be interlocked with the compressor, which is the whole reason the pairing
    #    changed. A field kit on a listed terminal interlocks exactly as a factory one would.
    #
    # WHY THIS UNIT AND NOT A SHALLOWER ONE. Connection geometry decides where a machine can
    # live: every concealed slim duct — Gree, LG, Samsung — puts supply on one long face and
    # return on the opposite long face, so air crosses the short depth and the long dimension
    # sits ACROSS the duct axis. The FLEXX Ultra keeps that geometry; what it costs is depth,
    # 18 1/8 in against the DUC24's 11 13/16, which is what drives SF-S-HP1 from a 17 in drop
    # to 21 in (storeys/second.py). It buys back nearly an inch of the box's GRADED axis in
    # exchange — 43 1/2 in wide against 44 1/2 — because `soffit_clear_section` measures every
    # occupant across the box's shorter plan dimension, and depth is not that dimension.
    #
    # A 36k FLEXX Ultra was REJECTED: its cabinet's smallest dimension is 21 1/4 in, needing a
    # 24 in drop, landing the soffit's underside exactly on IRC R305.1's 7'-0" floor, with
    # 3.5x cooling oversizing against a 10,145 Btu/h load and 1,000 cfm into 750-cfm ducts.
    # There is no 30k in the line (24 / 36 / 48 / 60 only).
    #
    # LG's KNUJB241A/LHN248HV1 remains the one real loss on FIT — 9 21/32 in tall would have
    # sat in the original 14 in drop — but its published heating range FLOOR is -13 F, two
    # degrees short of this site's design temperature. Worth revisiting only if LG publishes
    # a lower floor.
    EquipmentType(tag="EQ-T-GREE-FLEXX-ULTRA-24-AH",
                  name="Gree FLEXX Ultra R32 concealed ducted air handler, 24k",
                  footprint=(inch(43.5), inch(21.25)), height=inch(18.125),
                  cooling_capacity_btuh=24000,
                  # AHRI 215213329 rates the MATCHED PAIR, so the same two numbers sit on
                  # the air handler and on EQ-T-GREE-FLEXX-ULTRA-24-OD below. Both are read
                  # off this type's own source note; neither is derived from the other.
                  hspf2=10.0,
                  seer2=18.0,
                  source="Gree FLEXX Ultra R32 air handler FXU24HP230V1R32AH, matched to EQ-T-GREE-FLEXX-ULTRA-24-OD. Cabinet 18 1/8 x 21 1/4 x 43 1/2 in (W x D x H as shipped), net weight 135.6 lb, laid horizontally for ceiling mount with the 18 1/8 in face vertical — the orientation that minimises soffit depth, so `height` is 18 1/8 in and the 43 1/2 in dimension is the plan long axis. Airflow to 760 cfm against an external static pressure of 1.0 in. w.c., which is what lets it drive the 750 cfm this duct system is sized to with margin; the DUC24 it replaced claimed 1030 cfm in prose and really topped out at 736 at 0.8 in. w.c. HSPF2 10.0 / SEER2 18.0, ENERGY STAR Cold Climate (AHRI 215213329). 24 VAC thermostat terminals and a factory electric heat kit (4.6 / 5.5 / 9.2 kW) — the DUC24 had NEITHER, so EQ-S-HP1-STRIP could not physically be interlocked with the heat pump at all, which is the defect this retype closes. The indoor unit carries no heating rating of its own on purpose: the outdoor unit is what has to make heat at design temp, and mep.heating_capacity sizes the zone against the outdoor type.",
                  # Real face positions. Air crosses the cabinet the LONG way — in one
                  # 18 1/8 x 21 1/4 end and out the other — which is what the source note's
                  # "43 1/2 in H as shipped, laid horizontally" describes and what the coil
                  # and blower actually do. The ports were previously authored on the
                  # 43 1/2 x 18 1/8 faces, i.e. air crossing the 21 1/4" dimension, which
                  # contradicted the type's own note. Nothing in the engine checks port
                  # positions; this is documentation integrity, and leaving it made the plan
                  # self-contradictory under EQ-S-HP1-AH's rotation=deg(90).
                  # Local -x is supply, +x is return, both on the cabinet's centre height;
                  # power enters at the return-end top corner where the whip lands.
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(inch(21.75), inch(10.625), inch(18.125))),
                         ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                     position=(inch(-21.75), ft(0), inch(9.0625))),
                         ServicePort(tag="return", service=Service.RETURN_AIR,
                                     position=(inch(21.75), ft(0), inch(9.0625))))),
    EquipmentType(tag="EQ-T-GREE-FLEXX-ULTRA-24-OD",
                  name="Gree FLEXX Ultra R32 outdoor unit, 24k (-22F, cold climate)",
                  footprint=(inch(39), inch(14.5625)), height=inch(37.8125),
                  plan_symbol="heat-pump-outdoor",
                  heating_ratings=(
                      HeatPumpRating(outdoor_db_f=-22.0, minimum_btuh=13400,
                                     maximum_btuh=18000,
                                     cop_at_minimum=1.37, cop_at_maximum=1.36,
                                     return_db_f=70.0, basis=RatingBasis.NEEP,
                                     citation="NEEP ccASHP id 504980 (ashp.neep.org/api/products/504980/), AHRI 215213329, 70 F return, read 2026-09-18. Gree's own Extended Ratings GREE_FLEXX_ULTRA_EXTENDED RATINGS_08272024 gives the same 18,000 Btu/h here at a HIGHER COP (1.49 against 1.36); NEEP's is the conservative read and the capacity is identical either way, so nothing this house sizes against moves. NEEP states no rated column at this temperature."),
                      HeatPumpRating(outdoor_db_f=-15.0, rated_btuh=21000,
                                     cop_at_rated=1.57, return_db_f=70.0,
                                     basis=RatingBasis.MANUFACTURER,
                                     citation="Gree Extended Ratings GREE_FLEXX_ULTRA_EXTENDED RATINGS_08272024, model FXU24, 70 F return, the 'MAX OUTPUT' band, read verbatim. THE ONLY ROW HERE THAT IS NOT NEEP'S, and it is the row this site designs at: NEEP publishes -22, 5, 17 and 47 and nothing between, and `capacity_at` would otherwise interpolate the -22 and 5 maxima to 19,815 Btu/h at -15. 21,000 is a published read at the exact design temperature, which is better than an interpolation of two. THE BAND IS 'MAX OUTPUT', NOT AN AHRI TEST CONDITION: AHRI 215213329 certifies SEER2/EER2/HSPF2 and the 47 F and 17 F points ONLY, so this figure is a manufacturer rating with no certificate behind it and should be presented that way at plan review. No minimum is published at -15 F; the turndown check therefore reads the minimum column at the NEEP rows either side and does not interpolate one here. (This document's COP column is TRUE COP, W/W, unlike the All-Match Extended Ratings whose column is Btu/h per watt.)"),
                      HeatPumpRating(outdoor_db_f=5.0, minimum_btuh=14000,
                                     rated_btuh=25000, maximum_btuh=25000,
                                     cop_at_minimum=2.55, cop_at_rated=2.0,
                                     cop_at_maximum=2.0, return_db_f=70.0,
                                     basis=RatingBasis.NEEP,
                                     citation="NEEP ccASHP id 504980, AHRI 215213329, 70 F return, read 2026-09-18. NEEP's 25,000 here is ABOVE Gree's Extended Ratings, which give a flat 24,000 Btu/h from -5 F to 47 F, and the January 2026 submittal GREE_FXU24_230V_R32_SUB_01272026 agrees with NEEP (25,000 at 5 F, COP 2.0). Three documents, and the two newer ones agree; the 2024 Extended Ratings is the outlier."),
                      HeatPumpRating(outdoor_db_f=17.0, minimum_btuh=7100,
                                     rated_btuh=20600, maximum_btuh=21600,
                                     cop_at_minimum=2.77, cop_at_rated=2.7,
                                     cop_at_maximum=2.67, return_db_f=70.0,
                                     basis=RatingBasis.NEEP,
                                     citation="NEEP ccASHP id 504980, AHRI 215213329, 70 F return, read 2026-09-18. An AHRI-certified point, and the 20,600 rated figure matches the January 2026 submittal exactly. NOTE THE DIP: rated capacity here is BELOW both the 5 F and 47 F rows, and the minimum (7,100) is the lowest in the table while the 5 F minimum is the highest (14,000). That is what NEEP publishes and it is not transcription error — the validator deliberately does not enforce monotonicity in temperature."),
                      HeatPumpRating(outdoor_db_f=47.0, minimum_btuh=10800,
                                     rated_btuh=25000, maximum_btuh=25400,
                                     cop_at_minimum=5.11, cop_at_rated=3.59,
                                     cop_at_maximum=3.56, return_db_f=70.0,
                                     basis=RatingBasis.NEEP,
                                     citation="NEEP ccASHP id 504980, AHRI 215213329, 70 F return, read 2026-09-18. The AHRI rating point. NEEP's turndown_ratio field says 2.31 for this unit, which is 25,000/10,800 — so the MINIMUM here is 10,800 Btu/h, against a System 1 zone load of about 4,100 Btu/h at this temperature. That is the whole finding of `mep.heat_pump_turndown`."),
                  ),
                  cooling_capacity_btuh=24000,
                  min_operating_temp_f=-22.0,
                  hspf2=10.0,
                  seer2=18.0,
                  source="Gree FXU24HP230V1R32AO (FLEXX Ultra, R32). 39 x 37 13/16 x 14 9/16 in overall (W x H x D), foot pattern 29 3/4 in across the width by 15 9/16 in across the depth, net weight 187.4 lb. Electrical MCA 21 A / MOCP 25 A at 208-230 V, single phase. LOW-TEMPERATURE HEATING, read VERBATIM from Gree's Extended Ratings catalogue GREE_FLEXX_ULTRA_EXTENDED RATINGS_08272024, model FXU24, 70 F return, the 'MAX OUTPUT' band — not interpolated, unlike the VIR24 record this replaced: -22 F 18,000 Btu/h at COP 1.49; -20 F 19,500 at 1.53; -15 F 21,000 at 1.57; and a flat 24,000 Btu/h from -5 F all the way to 47 F. THAT BAND IS 'MAX OUTPUT', NOT AN AHRI TEST CONDITION, and the difference is worth knowing at a plan review: AHRI 215213329 certifies SEER2/EER2/HSPF2 and the 47 F and 17 F points ONLY, so the -15 F figure is a manufacturer rating and no certificate stands behind it. NEEP's ccASHP database lists this unit (id 504980) as ENERGY STAR Cold Climate and publishes a -22 F maximum of 18,000 Btu/h at COP 1.36 — the same capacity as Gree's own -22 F row, at a LOWER COP (1.36 against 1.49). Where the two disagree the NEEP figure is the conservative one; the capacity this house sizes against is identical either way. NOTE that this document's COP column is TRUE COP (W/W), unlike the All-Match Extended Ratings whose column is Btu/h per watt. HSPF2 10.0 / SEER2 18.0, ENERGY STAR Cold Climate certified; AHRI 215213329 is the certificate for those three seasonal ratings and the two AHRI points, and its scope stops there. min_operating_temp_f -22 F per the operating envelope. heating_capacity_at_design_btuh is the -15 F read value, so the unit covers its whole operating range unaided: at -22 F it still makes 18,000 Btu/h against a ~16,400 Btu/h load, which is what demotes EQ-S-HP1-STRIP from a design-condition necessity to true sub-lockout backup. WARRANTY IS AN OWNER CALL AND IS NOT SETTLED HERE: Gree's standard terms are 5 years parts / 7 years compressor; the 10/10 tier requires purchase AND installation by a Gree Select Dealer with registration inside 60 days. An owner-supplied unit is NOT void — it carries the standard tier — it simply cannot reach Select. Both tiers require a licensed installing contractor and both exclude labour and faulty installation.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # System 2 — Gree Multi Ultra, one 3-port outdoor unit driving three wall-mount heads
    # (basement gym, main-floor suite bedroom, living room). Rated to -22 F, which is what
    # makes it the unit carrying the three coldest-exposure rooms.
    EquipmentType(tag="EQ-T-GREE-MULTI-U30",
                  name="Gree Multi R32 3-port outdoor unit, 30k (-22F)",
                  footprint=(inch(40.16), inch(16.81)), height=inch(32.52),
                  plan_symbol="heat-pump-outdoor",
                  heating_ratings=(
                      HeatPumpRating(outdoor_db_f=-22.0, minimum_btuh=7000,
                                     maximum_btuh=21000,
                                     cop_at_minimum=1.49, cop_at_maximum=1.45,
                                     return_db_f=70.0, basis=RatingBasis.NEEP,
                                     citation="NEEP ccASHP id 392050 (ashp.neep.org/api/products/392050/), outdoor MUL30HP230V1R32AO, AHRI 215218915, 70 F return, read 2026-09-18. ** THE MINIMUM COLUMN DOES EXIST FOR THIS UNIT, WHICH WAS NOT CERTAIN. ** The plan that asked for this table listed the Multi's minimum as the high risk of the three — 'may not exist publicly' — and it does: NEEP publishes minimum and maximum at all four temperatures and a turndown_ratio of 3.29."),
                      HeatPumpRating(outdoor_db_f=-15.0, rated_btuh=23687,
                                     return_db_f=70.0,
                                     basis=RatingBasis.MANUFACTURER,
                                     citation="Gree Multi Ultra R32 Extended Ratings, 70 F return, the figure this house has sized System 2 against since the type was authored. NEEP publishes no -15 F row (it gives -22, 5, 17, 47), and interpolating its -22 and 5 maxima would give 22,556 Btu/h; 23,687 is a published read at the exact design temperature. A manufacturer rating, not AHRI-certified: 215218915 covers the non-ducted seasonal ratings and the AHRI test points. No minimum is published at -15 F."),
                      HeatPumpRating(outdoor_db_f=5.0, minimum_btuh=8800,
                                     rated_btuh=27000, maximum_btuh=27000,
                                     cop_at_minimum=2.2, cop_at_rated=2.07,
                                     cop_at_maximum=2.07, return_db_f=70.0,
                                     basis=RatingBasis.NEEP,
                                     citation="NEEP ccASHP id 392050, AHRI 215218915, 70 F return, read 2026-09-18."),
                      HeatPumpRating(outdoor_db_f=17.0, minimum_btuh=8800,
                                     rated_btuh=28000, maximum_btuh=31860,
                                     cop_at_minimum=2.96, cop_at_rated=2.45,
                                     cop_at_maximum=2.4, return_db_f=70.0,
                                     basis=RatingBasis.NEEP,
                                     citation="NEEP ccASHP id 392050, AHRI 215218915, 70 F return, read 2026-09-18. An AHRI rating point."),
                      HeatPumpRating(outdoor_db_f=47.0, minimum_btuh=8200,
                                     rated_btuh=30000, maximum_btuh=30400,
                                     cop_at_minimum=4.22, cop_at_rated=4.19,
                                     cop_at_maximum=3.32, return_db_f=70.0,
                                     basis=RatingBasis.NEEP,
                                     citation="NEEP ccASHP id 392050, AHRI 215218915, 70 F return, read 2026-09-18. The AHRI rating point; 30,000 Btu/h is the figure the type name is drawn from. A MULTI'S MINIMUM IS THE WHOLE OUTDOOR UNIT'S, not one head's: three heads share one compressor, so 8,200 Btu/h is the floor the zone as a whole must be able to absorb however the heads are staged."),
                  ),
                  cooling_capacity_btuh=28400,
                  min_operating_temp_f=-22.0,
                  # AHRI 215218915 (non-ducted). The three heads carry NO efficiency of
                  # their own for the same reason they carry no heating rating: the rating
                  # is the system's, and printing it three more times would read as four
                  # rated machines where there is one.
                  hspf2=10.0,
                  seer2=21.0,
                  source="Gree MUL30HP230V1R32AO. OUTLINE AND FEET, from the Gree Multi R32 Installation & Service Manual S3 outline diagram p.31 (the 30k has its own sheet; the 18/24k share a smaller one): 40 5/32 x 32 33/64 x 16 13/16 in overall, foot holes 25 in apart across the width and 15 19/32 in across the depth, net weight 145.5 lb. The record read 37 x 16 in until 2026-08-28 — 37 1/8 in is the width of the cabinet TOP, which is narrower than its base, and the 3 in of missing width put the unit within an inch of the balcony rim. RATINGS, from the 30 MBH submittal (AHRI 215218915 non-ducted): SEER2 21, EER2 13.6, HSPF2 10.0, MCA 23 A / MOCP 30 A, heating range -22 F to 75 F. Datasheet chart: 30,000 Btu/h at 47F, 27,000 Btu/h at 5F, ~24,500 Btu/h at -13F, ~21,500 Btu/h at -22F. ** -15F AT-DESIGN IS A READ VALUE SINCE 2026-08-31, NOT AN INTERPOLATION: 23,687 Btu/h from the Extended Ratings, replacing a 23,500 that was linearly interpolated between the -13F and -22F chart points. ** Cooling 28,400 Btu/h per datasheet. ** THE HARDWARE IS NOT CHANGING, and that was researched rather than assumed: no Gree single-zone below -22 F exists at 9-12k at any size, and the only real -31 F multi is R-410A — MULTIU36 makes 25,910 Btu/h at -22 F on 5.57 kW where this unit makes 22,600 on 3.70 kW, i.e. 50% more power for 15% more heat, while giving up HSPF2 10.0 -> 8.6 and SEER2 21 -> 16. This system already runs to -22 F, below the -20 F hard floor. **",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # No heating rating by design: three head ratings summed would size a zone against
    # capacity the shared compressor can't deliver simultaneously. Cooling capacity is kept
    # since it's what distinguishes the 9k from the 12k on a schedule.
    EquipmentType(tag="EQ-T-GREE-HEAD-9", name="Gree Multi R32 wall-mount head, 9k",
                  footprint=(inch(32.875), inch(7.875)), height=inch(10.828125),
                  cooling_capacity_btuh=9000,
                  source="Gree GWH09ATCXB-D6DNA3C/I, the Multi R32 9k wall-mounted indoor unit, from Gree's 'Wall Mounted Indoor Unit 09KBTU R32' submittal: 32 56/64 x 10 53/64 x 7 56/64 in (W x H x D), net weight 19.8 lb. The 9k and the 12k share ONE cabinet — see EQ-T-GREE-HEAD-12 — so nothing on a wall elevation distinguishes them and the cooling rating is what does. This replaced a REPRESENTATIVE PLACEHOLDER (32 x 8 x 12, 'TODO verify datasheet') on 2026-08-31. No heating rating BY DESIGN: three head ratings summed would size a zone against capacity the shared MUL30 compressor cannot deliver simultaneously.",
                  ports=()),
    EquipmentType(tag="EQ-T-GREE-HEAD-12", name="Gree Multi R32 wall-mount head, 12k",
                  footprint=(inch(32.875), inch(7.875)), height=inch(10.828125),
                  cooling_capacity_btuh=12000,
                  source="Gree GWH12ATCXB-D6DNA3A/I, the Multi R32 12k wall-mounted indoor unit, from Gree's 'Wall Mounted Indoor Unit 12KBTU R32' submittal: 32 7/8 x 10 53/64 x 7 7/8 in (W x H x D), net weight 19.8 lb — the SAME cabinet and the same weight as the 9k (EQ-T-GREE-HEAD-9), to within the 1/64 in the two sheets round to differently. That is a real fact about this line and not a copy-paste: Gree fits both capacities in one shell. This replaced a REPRESENTATIVE PLACEHOLDER (35 x 9 x 12, 'TODO verify datasheet') on 2026-08-31, and the placeholder had it 2 in wider than the 9k, which it is not.",
                  ports=()),
    # System 3 — Gree Sapphire R32, the high-efficiency unit over the stairs. True VFD
    # inverter: the soft start is why this is the one system on the backup battery circuit
    # (a hard-starting compressor is what a battery inverter cannot carry).
    EquipmentType(tag="EQ-T-GREE-SAPPHIRE-9",
                  name="Gree Sapphire R32 wall-mount head, 9.1k (VFD soft start)",
                  footprint=(inch(38.1875), inch(10.125)), height=inch(13.65625),
                  cooling_capacity_btuh=9100,
                  # AHRI 214802444, the matched pair — same numbers on the outdoor unit.
                  hspf2=11.2,
                  seer2=30.0,
                  source="Gree SAP09HP230V1R32AH, the Sapphire R32 9k wall-mounted indoor unit, from the Sapphire R32 9 MBH 230 V submittal (AHRI 214802444): 38 3/16 x 13 21/32 x 10 1/8 in (W x H x D), net weight 33.1 lb. It is a MUCH bigger head than the Multi R32 pair — 5 3/8 in wider, 2 7/8 in taller and 2 1/4 in deeper than EQ-T-GREE-HEAD-9 — which is what a SEER2 30 / HSPF2 11.2 coil costs in volume, and it matters here because this head hangs over the stair. This replaced a REPRESENTATIVE PLACEHOLDER (33 x 8 x 12, 'TODO verify datasheet') on 2026-08-31. True VFD inverter: the soft start is why this is the one system on the backup battery circuit. Heating is rated on EQ-T-GREE-SAPPHIRE-9-OD.",
                  ports=()),
    EquipmentType(tag="EQ-T-GREE-SAPPHIRE-9-OD",
                  name="Gree Sapphire R32 outdoor unit, 9.1k (-22F)",
                  footprint=(inch(34.375), inch(14.796875)), height=inch(21.859375),
                  plan_symbol="heat-pump-outdoor",
                  heating_ratings=(
                      HeatPumpRating(outdoor_db_f=-22.0, minimum_btuh=2600,
                                     maximum_btuh=7400,
                                     cop_at_minimum=4.23, cop_at_maximum=1.64,
                                     return_db_f=70.0, basis=RatingBasis.NEEP,
                                     citation="NEEP ccASHP id 393164 (ashp.neep.org/api/products/393164/), AHRI 214802444, 70 F return, read 2026-09-18. THIS DESIGN USES NEEP HERE and has since the type was authored, for a reason worth keeping: Gree's own low-ambient table gives about 9,130 Btu/h at -22 F at an implied COP of 2.62, and a COP of 2.62 at -22 F is not physically plausible for a residential air-source machine — the best cold-climate units published anywhere are near 1.5. NEEP's 7,400 at COP 1.64 is. ** THE AT-DESIGN CAPACITY IS NOW INTERPOLATED, WHERE THIS FILE USED TO USE 7,400 UNADJUSTED. ** The old record set `heating_capacity_at_design_btuh=7400` — the -22 F read used at a -15 F design temperature 'rather than interpolated upward, because the zone is 926 Btu/h and buying margin by interpolation would be spending credibility to gain nothing'. That reasoning was right about the credibility and is now unnecessary: `capacity_at` reads the table between -22 and 5 and reports 8,463 Btu/h, and it PRINTS 'interpolated between -22 F and 5 F' beside the number so nobody mistakes it for a read. A row authored at -15 F holding the -22 F value would be worse than either — it would claim to be a measurement at a temperature nobody measured."),
                      HeatPumpRating(outdoor_db_f=5.0, minimum_btuh=2600,
                                     rated_btuh=11500, maximum_btuh=11500,
                                     cop_at_minimum=4.23, cop_at_rated=2.11,
                                     cop_at_maximum=2.11, return_db_f=70.0,
                                     basis=RatingBasis.NEEP,
                                     citation="NEEP ccASHP id 393164, AHRI 214802444, 70 F return, read 2026-09-18. Agrees with the Gree submittal's 11,500 at 5 F."),
                      HeatPumpRating(outdoor_db_f=17.0, minimum_btuh=2800,
                                     rated_btuh=12000, maximum_btuh=13000,
                                     cop_at_minimum=4.32, cop_at_rated=2.3,
                                     cop_at_maximum=2.06, return_db_f=70.0,
                                     basis=RatingBasis.NEEP,
                                     citation="NEEP ccASHP id 393164, AHRI 214802444, 70 F return, read 2026-09-18. ** THIS ROW DISAGREES WITH THE SUBMITTAL AND IT IS THE BIGGEST GAP IN THE THREE TABLES. ** The Sapphire R32 9 MBH 230 V submittal states 8,900 Btu/h at 17 F; NEEP states 12,000 rated / 13,000 maximum. One row, one basis: the row authored is NEEP's, because every other row in this table is NEEP's and because this house's own record already chose NEEP over the manufacturer at -22 F for a physical reason. The submittal's 8,900 is recorded here and NOT blended in. ** IT IS ALSO A REAL BOOSTED LOW-AMBIENT MAP: ** 12,000 at 17 F and 11,500 at 5 F are both ABOVE the 10,600 rated at 47 F, i.e. capacity RISING as it gets colder. That is why `_check_heating_ratings` deliberately does not enforce monotonicity in temperature — a rule that did would refuse the machine this house bought."),
                      HeatPumpRating(outdoor_db_f=47.0, minimum_btuh=2700,
                                     rated_btuh=10600, maximum_btuh=16000,
                                     cop_at_minimum=5.28, cop_at_rated=4.38,
                                     cop_at_maximum=3.75, return_db_f=70.0,
                                     basis=RatingBasis.NEEP,
                                     citation="NEEP ccASHP id 393164, AHRI 214802444, 70 F return, read 2026-09-18. The AHRI rating point, and it agrees with the submittal's 10,600. NEEP's turndown_ratio is 4.26 for this unit — the best of the three, and still nowhere near enough for a 932 Btu/h zone: 2,700 Btu/h is the floor."),
                  ),
                  cooling_capacity_btuh=9100,
                  min_operating_temp_f=-22.0,
                  hspf2=11.2,
                  seer2=30.0,
                  source="Gree SAP09HP230V1R32AO, from the Sapphire R32 9 MBH 230 V submittal (AHRI 214802444): 34 3/8 x 21 27/32 x 14 51/64 in (W x H x D), net weight 78.3 lb, MCA 11 A / MOCP 15 A, SEER2 30.0, HSPF2 11.2, heating range -22 F to 86 F. The outline was 31 x 23 x 13 in until 2026-08-31 — 3 3/8 in narrow and 1 13/16 in shallow. PUBLISHED HEATING, read: 10,600 Btu/h at 47 F, 11,500 at 5 F, 8,900 at 17 F. That 17 F figure is the one the old record got worst: it carried '~11,500-13,000 Btu/h at 5F' and nothing at 17 F, which read as a machine making 12,000 in the middle of its range. It makes 8,900. ** WHICH NUMBER GOVERNS AT DESIGN, AND WHY IT IS NOT GREE'S. ** Gree's own low-ambient table gives ~9,130 Btu/h at -22 F at a 70 F return, at an implied COP of 2.62. A COP of 2.62 at -22 F is not physically plausible for a single-stage residential air-source machine — the best cold-climate units published anywhere are near 1.5 there — and the 8,200 the previous record carried was that table's 90 F-return column, which is a different measurement again. AHRI/NEEP's cold-climate listing says 7,400 Btu/h at 1.32 kW, COP 1.64, at -22 F. THIS DESIGN USES NEEP. heating_capacity_at_design_btuh is 7,400 — the -22 F read value, deliberately used unadjusted at the -15 F design temperature rather than interpolated upward, because the zone is 926 Btu/h and buying margin by interpolation would be spending credibility to gain nothing. min_operating_temp_f -22 F per the operating envelope.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # 1,500W/120V = 12.5A; x1.25 continuous = 15.6A needs a 20A breaker (not 15A). Hard-wired
    # Equipment, not a receptacle. Rated 5,118 Btu/h (1,500W x 3.412, no cold-weather derate).
    # `supplemental_heat` so it never opens its own HVAC zone — counts toward RM-M-LIVING's
    # zone (takeoff/hvac.py supplemental_heat_by_room).
    #
    # ** A REAL PRODUCT SINCE 2026-09-06: the Amantii BI-30-XTRASLIM (BI-X190030-1). ** It was
    # a generic 48" x 7" big-box cabinet; it is now the ~30" unit the owner asked for, and the
    # footprint authored here is the ROUGH OPENING (29" x 4 1/2" x 20 3/8" high), because the
    # rough opening is the hole cut in the W-M-FIRE-* brick and is therefore the thing that can
    # interfere with something. The body is 29 1/8 x 19 7/8 x 4" and the face only 3/8" wider
    # than the body.
    #
    # ** EVERY UNIT ON THE MARKET THAT IS 26-32" WIDE AND <= 6" DEEP AND HARDWIREABLE IS AN
    # AMANTII. ** That is the whole population, not a preference. Swept and ruled out: all
    # Modern Flames (nearest shallow unit 44"), Dimplex (the Multi-Fire SL Slim 36" is the
    # closest miss; the 30" Ignite Aspire is 18" DEEP), SimpliFire, Napoleon (Cineview 30 is
    # 7 3/4"), Flamerite, the 230 V British makers, and the Amazon-tier 30" units — which have
    # no hardwire procedure and no UL 2021 "fixed and location dedicated" listing.
    # ** FIELD-CONVERTING A CORD-CONNECTED APPLIANCE VOIDS ITS LISTING **, so that tier is out
    # on principle and not on price. Touchstone's Sideline 28 (80028, ~$359) is disqualified in
    # writing: manual rev 251114 p.17 says "the 80028 Sideline 28\" Electric Fireplace cannot be
    # hardwired"; the p.12 "Plug-in or Hardwire" drawing is boilerplate shared across models and
    # the model-named sentence governs.
    #
    # ** WHY THIS ONE AND NOT THE TRD-30-XTRASLIM. ** It is TRIMLESS, so the brick runs to the
    # glass edge — the entire point of a masonry surround — and it is the only unit in the
    # field with a published mantel rule. The TRD has 57% more glass but lands a 31 1/4" steel
    # flange on the brick face and demands a 10" floor clearance plus a PERMANENT AIR-INTAKE
    # SLOT CUT INTO THE MASONRY.
    #
    # ** 240 V WAS CONSIDERED AND BUYS NOTHING. ** No 26-32" unit at <= 6" depth exists in
    # 208/240 V at all: the 30"-class 240 V units are 11 5/8"-18" deep and the shallow 240 V
    # units start at 42". And 240 V is WATTAGE ONLY — Dimplex's XLF50 is the same SKU at
    # 1500 W/5118 Btu (120 V) and 2500 W/8530 Btu (240 V), SimpliFire ships one firebox with an
    # internal voltage selector, and Modern Flames' USA and 230 V manuals list identical
    # `LED 12V` and `12 VDC stepper motor` rows. The extra ~1,000-1,300 W would be resistance
    # heat at roughly 3x the heat pump's cost per Btu in a room the heat pump already serves.
    # Staying at 120 V also leaves the ServicePort POWER_120, CKT-FIREPLACE at poles=1 and
    # plan/circuits.py's whole 1,500 W / 12.5 A / 20 A justification untouched.
    #
    # ** NO ClearanceZone, AND THAT IS EARNED, NOT SKIPPED. ** A ClearanceZone is a PLAN
    # rectangle. Every clearance this unit publishes is VERTICAL — "mantel 4 inches from the
    # trim", combustible facing allowed, no floor clearance and no air slot — so any plan zone
    # authored here would be inventing a requirement the manufacturer does not state. The
    # mantel clearance is held instead by the elevation: SB-M-FIRE-MANTEL's underside at 64"
    # against the opening top at 44 3/8" is 19 5/8", about 5x the published 4". (It was
    # 11 5/8" and about 3x until 2026-09-11, when the owner reversed the sill back to 24" AFF
    # — see EQ-M-FIREPLACE below. The margin grew; nothing about this paragraph turns on it.)
    #
    # ** FOUR THINGS TO CONFIRM IN WRITING FROM AMANTII BEFORE FRAMING: ** (1) the mantel
    # PROJECTION the 4" is quoted at — unpublished industry-wide; ask specifically whether 4"
    # holds for a solid walnut shelf projecting 7-8". (2) Bottom, side and back combustible
    # clearances, which the manual simply omits. (3) That the left-side L/N/G junction block
    # stays serviceable through the glass opening once the unit is bricked in. (4) ** That the
    # unit ships with the 2022 CSA manual revision ** — the older manual under the same model
    # number says 1465 W / 5000 Btu and has NO mantel and NO hardwire section at all, i.e. an
    # inspector would find no permission to hardwire it. Note the Panorama warranty excludes
    # tray, front and back glass; and beware HVACDirect, which labels the APPLIANCE dimensions
    # "Framing Dimensions" (framing to those is too small) and sells a "BI-30-XTRASLIM-LUMINA"
    # at 110 lb that Amantii does not list — the manual weight is 50.7 lb.
    #
    # ** ON LOOKS, HONESTLY: no reliable evidence distinguishes any of these at 9-10 ft. **
    # Every "most realistic flame" page in this category is a retailer or an affiliate and none
    # addresses viewing distance. What IS verifiable is that neither Amantii publishes
    # anti-glare or low-iron glass — both are plain clear tempered and BOTH WILL MIRROR THE TWO
    # WINDOWS FLANKING THEM. Here glare is solved by the brick reveal and the mantel's shadow,
    # not by model choice. (The one glossy-LCD shallow unit with a verified owner glare
    # complaint, Modern Flames' HelioVision, starts at 52" and never reaches this decision.)
    EquipmentType(tag="EQ-T-FIREPLACE-EL",
                  name="Amantii BI-30-XTRASLIM electric fireplace, 1.5 kW built-in",
                  footprint=(inch(29), inch(4.5)), height=inch(20.375),
                  # Resistance heat, so a SCALAR and not a table: an element's output is
                  # flat with outdoor temperature, and no lockout is wired on this circuit
                  # (it is a fireplace somebody switches on), so its at-design contribution
                  # is its nameplate. 1,500 W x 3.412.
                  resistance_heating_btuh=5118,
                  supplemental_heat=True,
                  source="Amantii BI-30-XTRASLIM (BI-X190030-1), Panorama built-in series, from the 2022 CSA-revision installation manual: rough opening 29 x 20 3/8 x 4 1/2 in, appliance 29 1/8 x 19 7/8 x 4 in, trimless face 3/8 in wider than the body, viewing glass 25 1/4 x 11 7/8 in (300 sq in), 50.7 lb. Electrical 120 V, 1500 W, 5118 Btu/h, 12.5 A, dedicated 15 A circuit preferred (this house gives it a 20 A — see plan/circuits.py); HARDWIREABLE via an L/N/G block on the left side. Clearances: mantel 4 in from the trim, combustible facing allowed, no floor clearance and no air-intake slot. $1,499-1,539. Chosen because it is the only trimless unit in the 26-32 in x <= 6 in deep hardwireable field, which is entirely Amantii; the alternative TRD-30-XTRASLIM lands a 31 1/4 in steel flange on the brick and wants a permanent air slot cut into it. Replaced a generic 48 x 7 in 1.5 kW big-box insert on 2026-09-06",
                  ports=(ServicePort(tag="power", service=Service.POWER_120,
                                     position=(ft(0), ft(0), ft(0))),)),
    # System 1's electric heat kit (retyped from EQ-T-DUCT-HEATER-2KW, and it is a different
    # part doing a different job). The 2 kW inline element existed because the VIR24 made
    # 13,500 Btu/h at design against a 16,309 Btu/h block load — a shortfall
    # `mep.heating_capacity` was failing on. Two things were wrong with that answer: the
    # DUC24 has no aux-heat terminal, so nothing could stage the element with the compressor;
    # and covering a design-day deficit with resistance heat is a workaround, not a system.
    # The FLEXX Ultra covers its own load, and this kit is the factory part that stages off
    # its 24 VAC board for defrost recovery and for hours below the -22 F lockout.
    EquipmentType(tag="EQ-T-GREE-FLEXX-HEATKIT-46KW",
                  name="Gree FLEXX Ultra electric heat kit, 4.6 kW, 240V",
                  footprint=(inch(16), inch(10)), height=inch(10),
                  # ** AT-DESIGN IS ZERO, AND IT IS NOW DERIVED RATHER THAN ASSERTED. **
                  # 15,695 Btu/h is the nameplate (4.6 kW x 3,412, flat with outdoor
                  # temperature because resistance heat is). At this site's -15 F design
                  # temperature the kit delivers NONE of it: an outdoor thermostat (see
                  # CKT-HP1-AH in plan/circuits.py) enables the elements only below the
                  # compressor's -22 F cut-out, so the elements and the compressor are
                  # non-coincident loads and `mep.heating_capacity` must not credit the kit
                  # against the design-day block load — the margin it reports for System 1
                  # is the machine's own, unaided, which is the whole case for the retype.
                  #
                  # THIS FILE USED TO SAY THAT BY AUTHORING A ZERO, and a zero is a
                  # conclusion, not an input: move the site to a -30 F design temperature
                  # and the kit really would contribute, and the authored zero would have
                  # been silently wrong. `aux_lockout_above_f` states the CONTROL SETTING
                  # and `takeoff/hvac._resistance_at_design` does the comparison against
                  # `Site.design_temp_heating` (decision #76).
                  resistance_heating_btuh=15695,
                  aux_lockout_above_f=-22.0,
                  supplemental_heat=True,
                  source="Gree FLEXA2LHTR05KWD factory electric heat kit for the FLEXX Ultra air handler: 4.6 kW at 240 V (4.6 x 3,412 = 15,695 Btu/h, no cold-weather derate), MCA 29.9 A, maximum overcurrent device 35 A. It mounts INSIDE the EQ-T-GREE-FLEXX-ULTRA-24-AH cabinet on the discharge side of the coil and is staged by the air handler's own 24 VAC control, which is the whole point of the retype: the EQ-T-DUCT-HEATER-2KW it replaces was a generic inline element in the supply plenum, and the DUC24 it was drawn against had no aux-heat terminal to interlock it with. Its job also changed. It is no longer covering a design-temperature shortfall — the outdoor unit makes 21,000 Btu/h at -15 F against a 15,164 Btu/h zone load unaided — but is true backup for defrost recovery and for the hours below the -22 F compressor lockout. `supplemental_heat` like the fireplace: it counts toward its room's zone and opens none of its own.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),)),
    # Garage infrared heater lamp — same 1,500 W / 120V / 20A arithmetic as the fireplace.
    # It is hard-wired equipment rather than a fan-forced unit; RM-GARAGE stays
    # `conditioned=False` and therefore out of the 3 VA/ft2 general-lighting area.
    EquipmentType(tag="EQ-T-GARAGE-HEATER", name="Garage infrared heater lamp, 1.5 kW, 120V",
                  footprint=(inch(14), inch(9)), height=inch(15),
                  ports=(ServicePort(tag="power", service=Service.POWER_120,
                                     position=(ft(0), ft(0), ft(0))),)),
)
