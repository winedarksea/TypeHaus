# haus: editable
# Catlin MEP — the ERV's catalog: the machine, its manifolds, its mixing box, its hoods.
#
# Split off plan/mep_erv.py (AGENTS.md's 500-line rule) at the seam the rest of this house
# already uses: type DEFINITIONS here, placed INSTANCES there. Nothing in this file is
# draggable, and the `# haus: editable` marker rides along only because the dialect linter
# reads the whole plan package as one dialect — there is no element here to write back.
#
# Read plan/mep_erv.py first; it is where the system is explained.

from typehaus import (
    EquipmentType,
    RegisterType,
    Service,
    ServicePort,
    ft,
    inch,
)

EQUIPMENT_TYPES_ERV = (
    # The machine. Ports are all on top and all 6" round, which is what makes the
    # 6" -> 160 mm manifold adapter (one per manifold) a real line in the BOM rather than a
    # shrug: the collared radial manifolds this system uses are 160 mm stock.
    #
    # OUTDOOR_AIR/EXHAUST_AIR are new `Service` members (2026-08-25). Until they existed the
    # outdoor side of this machine could not be spelled at all, and plan/electrical.py said
    # so in a comment — an ERV with no intake and no discharge is not modeled.
    # ** 210 IS THE MODEL-NAME NUMBER; 206 AT 0.4" W.G. IS THE CERTIFIED ONE. **
    # HVI certifies this machine at 206 cfm net supply at 0.4" w.g. (HVI ID 2004940). The
    # "210 CFM at 0.2 in. w.g." this file and plan/mep_erv.py used to quote as the rating
    # point is a point on the fan curve — the one the model number is named for — and taking
    # it as the rating point understated the static budget by about half.
    #
    # ** `ventilation_cfm` IS DELIBERATELY LEFT AT 210 (2026-09-01). ** It is not an
    # oversight and it is not a rounding choice. Moving it to 206 moves a LIVE VERDICT:
    # code.N1103_6_whole_house_ventilation reads 210 provided against 203 required, and at
    # 206 it reads 206 against 203 — still passing, but on a 3 cfm margin instead of 7 — and
    # tests/test_catlin_erv.py:30-33 asserts the current figure. Changing it is a ventilation
    # decision with a test and a code verdict behind it, which is a different pass from
    # correcting the prose. The name and the source string below carry the real number so
    # nobody re-derives 0.2" from this row.
    EquipmentType(tag="EQ-T-BROAN-B210E75RT",
                  name="Broan B210E75RT ERV, 206 CFM at 0.4\" w.g., 6\" top ports",
                  footprint=(inch(24.8), inch(21)), height=inch(21.6),
                  plan_symbol="erv",
                  product_ref="PROD-BROAN-B210E75RT",
                  ventilation_cfm=210,
                  # The -13 F certified figure, NOT the 32 F one. This is a -15 F design
                  # house; grading its block load against a 32 F recovery number would
                  # credit the ventilation term with heat the core does not recover on the
                  # day that sizes the equipment.
                  sensible_recovery_effectiveness=0.65,
                  source="Broan B210E75RT. HVI-certified 206 CFM net supply at 0.4 in. w.g. (HVI ID 2004940) — that is the rating point. The manufacturer's '210 CFM at 0.2 in. w.g.' is the model-name point off the fan curve and is NOT the certified rating; quoting it as one halves the apparent static budget. Six-inch round top ports, 24.8 in. W x 21.6 in. H x 21 in. D, MERV 8 filtration standard (MERV 13 optional), SRE 81% at 32 F and 65% at -13 F. The -13 F figure is the one authored above; see the note there.",
                  ports=(ServicePort(tag="power", service=Service.POWER_240,
                                     position=(ft(0), ft(0), ft(0))),
                         ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                     position=(ft(0), ft(0), inch(21.6))),
                         ServicePort(tag="return", service=Service.RETURN_AIR,
                                     position=(ft(0), ft(0), inch(21.6))),
                         ServicePort(tag="outdoor", service=Service.OUTDOOR_AIR,
                                     position=(ft(0), ft(0), inch(21.6))),
                         ServicePort(tag="exhaust", service=Service.EXHAUST_AIR,
                                     position=(ft(0), ft(0), inch(21.6))))),
    # Two manifold sizes, because a manifold is bought by its port count and the house needs
    # two counts. Both are 160 mm-collared with 75 mm radial takeoffs, and both therefore
    # take one 6" -> 160 mm adapter at the trunk end.
    EquipmentType(tag="EQ-T-ERV-MANIFOLD-6",
                  name="Radial air manifold, 160 mm trunk, 6 x 75 mm ports",
                  footprint=(inch(24), inch(8)), height=inch(8),
                  plan_symbol="erv",
                  source="Generic semi-rigid radial-duct manifold, 160 mm collar with six 75 mm outlets and a balancing damper at each. Sized from the port count the level it serves needs, not from a catalogue.",
                  ports=(ServicePort(tag="trunk", service=Service.SUPPLY_AIR,
                                     position=(ft(0), ft(0), inch(4))),)),
    EquipmentType(tag="EQ-T-ERV-MANIFOLD-10",
                  name="Radial air manifold, 160 mm trunk, 10 x 75 mm ports",
                  footprint=(inch(34), inch(8)), height=inch(8),
                  plan_symbol="erv",
                  source="As EQ-T-ERV-MANIFOLD-6, ten ports. The level-2 extract manifold is the only one in the house that needs this many: RM-M-MECH gathers both the main storey's wet rooms and the second storey's, because they share one floor cavity.",
                  ports=(ServicePort(tag="trunk", service=Service.RETURN_AIR,
                                     position=(ft(0), ft(0), inch(4))),)),
    # The mixing box: where the ERV's fresh leg joins System 1's return. A box and not a tee
    # because of the damper in it — a backdraft damper on the ERV leg is what keeps the
    # return working when the ERV is off, which is the behaviour the owner asked for and is
    # behaviour, not geometry.
    EquipmentType(tag="EQ-T-ERV-MIXING-BOX",
                  name="Return-air mixing box, 6\" ERV leg with backdraft damper",
                  footprint=(inch(10), inch(12)), height=inch(8),
                  plan_symbol="erv",
                  source="Fabricated plenum box: 6\" ERV inlet with a gravity backdraft damper, open to System 1's return plenum. The damper is the whole point — the ERV and the air handler run on independent schedules and each must breathe without the other.",
                  ports=(ServicePort(tag="fresh", service=Service.SUPPLY_AIR,
                                     position=(ft(0), ft(0), inch(4))),
                         ServicePort(tag="return", service=Service.RETURN_AIR,
                                     position=(ft(0), ft(0), inch(4))))),
    # The two exterior hoods. One type, two placements — an intake hood and a discharge hood
    # are the same casting with the damper reversed, and giving them one type is what keeps
    # the BOM row honest.
    EquipmentType(tag="EQ-T-ERV-HOOD-6",
                  name="Exterior ventilation hood, 6\" round, bird screen + backdraft damper",
                  footprint=(inch(12), inch(12)), height=inch(12),
                  plan_symbol="erv",
                  source="Generic 6\" wall/gable hood with 1/4\" bird screen and a gravity backdraft damper. Screen mesh is deliberately coarse: a fine mesh frosts shut on an intake at -15 F.",
                  ports=(ServicePort(tag="duct", service=Service.OUTDOOR_AIR,
                                     position=(ft(0), ft(0), inch(6))),)),
)

REGISTER_TYPES_ERV = (
    # The workshop's terminal stops being a 7" ceiling diffuser at 8'-0" and becomes what it
    # was always described as: an over-bench capture hood. A ceiling diffuser eight feet up
    # does not capture solder fume, it dilutes it into the room first — a quasi-fume hood
    # captures at the source, which is 24"-30" above a 34" bench top.
    #
    # HONEST LIMIT, and it belongs in the record rather than in an optimistic name:
    # FURN-B-WORKSHOP-BENCH-N/S run ten feet along the west wall and one 30" hood captures a
    # fraction of that. It is a bench hood, not bench-run coverage. It stays on the extract
    # (RETURN) side rather than getting a dedicated exhaust for the reason the old comment
    # gave and which still holds: light fumes, heat worth recovering, not a spray booth.
    RegisterType(tag="REG-T-ERV-BENCH-HOOD",
                 name="Over-bench capture hood, 30\" x 12\" face, 75 mm collar",
                 footprint=(inch(30), inch(12)), height=inch(8),
                 plan_symbol="register", ventilation_terminal=True,
                 source="Fabricated sheet capture hood over FURN-B-WORKSHOP-BENCH-N/S, hung at 5'-6\" — 24\" above the 34\" bench tops. Captures at the source instead of diluting into the room. One hood does not cover ten feet of bench; see the note in plan/mep_erv.py.",
                 ports=(ServicePort(tag="return", service=Service.RETURN_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
)

