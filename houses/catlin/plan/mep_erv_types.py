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
    DuctProductType,
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
    # ** 210 IS THE MODEL-NAME NUMBER; 206 AT 0.4" W.G. IS THE CERTIFIED ONE. **
    # HVI certifies this machine at 206 cfm net supply at 0.4" w.g. (HVI ID 2004940). The
    # "210 CFM at 0.2 in. w.g." on the box is a point on the fan curve — the one the model
    # number is named for — and taking it as the rating point understates the static budget
    # by about half.
    #
    # ** `ventilation_cfm` IS DELIBERATELY LEFT AT 210. ** Moving it to 206 moves a LIVE
    # VERDICT: code.N1103_6_whole_house_ventilation reads 210 provided against 205 required
    # (MN 1322 R403.5), and at 206 it reads 206 against 205 — still passing, but on a 1 cfm
    # margin instead of 5 — and tests/test_catlin_erv.py:30-33 asserts the current
    # figure. Changing it is a ventilation decision with a test and a code verdict
    # behind it, not a prose fix. The name and the source string below carry the real
    # number so nobody re-derives 0.2" from this row.
    EquipmentType(tag="EQ-T-BROAN-B210E75RT",
                  name="Broan B210E75RT ERV, 206 CFM at 0.4\" w.g., 6\" top ports",
                  footprint=(inch(24.8), inch(21)), height=inch(21.6),
                  plan_symbol="erv",
                  product_ref="PROD-BROAN-B210E75RT",
                  ventilation_cfm=210,
                  # ** THE WHOLE PUBLISHED CURVE, NOT THE ONE POINT THE BOX QUOTES. **
                  # (static in. w.g., net cfm) off the B210E75RT spec sheet. This is what
                  # closes plans/buildability.md open question 3: the distributor's
                  # "210 at 0.2" and the design's "206 at 0.4" are the SAME curve read at
                  # two stations, and neither contradicts the other. `mep.erv_static_budget`
                  # interpolates it against the static this house's own duct system makes,
                  # which is the only way a rating point becomes a verdict.
                  fan_curve=((0.1, 214.0), (0.2, 210.0), (0.3, 208.0), (0.4, 206.0),
                             (0.5, 201.0), (0.6, 199.0), (0.7, 195.0), (0.8, 191.0),
                             (1.0, 184.0), (1.2, 176.0)),
                  # A HARD CEILING, AND A DIFFERENT KIND OF STATEMENT FROM THE CURVE'S LAST
                  # POINT. Above 1.3 in. w.g. the core deforms; the machine is not merely
                  # off the bottom of the table, it is out of its operating envelope. The
                  # check draws a harder line here than it does at 1.2.
                  fan_curve_max_static_in_wg=1.3,
                  # The -13 F certified figure, NOT the 32 F one. This is a -15 F design
                  # house; grading its block load against a 32 F recovery number would
                  # credit the ventilation term with heat the core does not recover on the
                  # day that sizes the equipment.
                  sensible_recovery_effectiveness=0.65,
                  source="Broan B210E75RT. HVI-certified 206 CFM net supply at 0.4 in. w.g. (HVI ID 2004940) — that is the rating point. The manufacturer's '210 CFM at 0.2 in. w.g.' is the model-name point off the fan curve and is NOT the certified rating; quoting it as one halves the apparent static budget. Six-inch round top ports, 24.8 in. W x 21.6 in. H x 21 in. D, MERV 8 filtration standard (MERV 13 optional), SRE 81% at 32 F and 65% at -13 F. The -13 F figure is the one authored above; see the note there. The spec sheet publishes the whole fan curve (214 cfm at 0.1 in. w.g. falling to 176 at 1.2; 1.3 in. w.g. is the ceiling above which the core deforms), which is authored as `fan_curve` — the 0.2 in. and 0.4 in. figures are two stations on it, not two claims. Broan's installation manual carries one distribution instruction and this house obeys it: above 200 cfm with long runs or many elbows, take the trunk up to 8 in. See notes/erv_static_budget.md for where this house stands against that advice and what the upsize would cost.",
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
    # ** THREE FABRICATED PLENUMS, NOT A PROPRIETARY MANIFOLD (2026-09-12, BLD-08). **
    # These rows read "160 mm collar, 75 mm outlets" until today, and that part is sold in
    # the USA by exactly two importers (Zehnder and Brink via 475) with no Minnesota dealer
    # for either. The owner's decision is no proprietary tube, and the topology survives it
    # intact: a home-run plenum with individually dampered branches is documented standard
    # practice (an 8" plenum with 4" takeoffs), and every part of it is a commodity.
    #
    # So a manifold here is a **sheet-metal shop fabrication** — the same thing this house
    # already buys for EQ-T-ERV-MIXING-BOX: a galvanized box with one 8" inlet collar, N x 4"
    # start collars each with an integral butterfly damper, seams sealed with mastic. The
    # tags do not change, because five `type_ref`s, the price rows and the goldens key on
    # them; what changed is that the rows are now real specs rather than a shrug at a
    # catalogue nobody stocks.
    #
    # ** `duct_ports` AND `port_diameter` ARE WHAT MAKE "10 OF 10" A VERDICT. **
    # plan/mep_erv.py has said "all TEN of its ports are spoken for" in prose since the
    # level-2 layout was drawn. `mep.erv_manifold_ports` now counts the runs that actually
    # land in each box against the number it is fabricated with, so a twelfth radial cannot
    # be added to a ten-port plenum in silence.
    #
    # ** `static_loss_pa_at_cfm` IS INLET-TO-PORT, AT THE TRUNK FLOW, AND IT IS DERIVED. **
    # Not a manufacturer's test curve — there is no manufacturer. It is the abrupt-expansion
    # loss into the box plus the contraction and damper loss out of one start collar, worked
    # term by term in notes/erv_static_budget.md §4 from ASHRAE fitting coefficients on the
    # collar velocity pressure. It is worked at the house's LARGEST port flow (25 cfm,
    # DU-M-ERV-R-PLANT) and is therefore conservative at every other port. A submitted
    # shop drawing with a measured curve replaces these three points and nothing else.
    EquipmentType(tag="EQ-T-ERV-MANIFOLD-6",
                  name="Fabricated air plenum, 8\" inlet, 6 x 4\" dampered ports",
                  footprint=(inch(24), inch(8)), height=inch(8),
                  plan_symbol="erv",
                  duct_ports=6, port_diameter=inch(4),
                  static_loss_pa_at_cfm=((60.0, 0.5), (120.0, 1.8), (210.0, 5.5)),
                  source="Fabricated galvanized plenum from any sheet-metal shop: one 8 in. inlet collar, six 4 in. start collars each with an integral butterfly balancing damper, seams sealed with mastic. Sized from the port count the level it serves needs. Replaced a 160 mm/75 mm proprietary radial manifold on 2026-09-12 (plans/buildability.md BLD-08): the proprietary part has no Minnesota dealer, the topology does not need it, and every piece of this one is a commodity. Loss curve derived in notes/erv_static_budget.md §4, not published by a maker.",
                  ports=(ServicePort(tag="trunk", service=Service.SUPPLY_AIR,
                                     position=(ft(0), ft(0), inch(4))),)),
    EquipmentType(tag="EQ-T-ERV-MANIFOLD-10",
                  name="Fabricated air plenum, 8\" inlet, 10 x 4\" dampered ports",
                  footprint=(inch(34), inch(8)), height=inch(8),
                  plan_symbol="erv",
                  duct_ports=10, port_diameter=inch(4),
                  # The same 8" inlet in the same 8" section, so the same curve: the box is
                  # longer, not fatter, and the loss is set by the inlet velocity and one
                  # collar, neither of which the extra length moves.
                  static_loss_pa_at_cfm=((60.0, 0.5), (120.0, 1.8), (210.0, 5.5)),
                  source="As EQ-T-ERV-MANIFOLD-6, ten ports in a longer box. The level-2 extract plenum is the only one in the house that needs this many: RM-M-MECH gathers both the main storey's wet rooms and the second storey's, because they share one floor cavity. All ten are spoken for, which mep.erv_manifold_ports now grades rather than a comment asserting.",
                  ports=(ServicePort(tag="trunk", service=Service.RETURN_AIR,
                                     position=(ft(0), ft(0), inch(4))),)),
    # The same six-port manifold, cast for the EXTRACT side. Identical part, identical
    # price, one field different: the trunk carries stale air away from the house, so the
    # port is RETURN_AIR — which is what EQ-T-ERV-MANIFOLD-10 has always declared, this
    # house's only other extract manifold. Two placements used the supply type and
    # `mep.equipment_port_service` could only call them UNKNOWN, because a type that states
    # its direction once cannot describe a placement that reverses it, and a FAIL there
    # would have reported the catalog rather than the building.
    EquipmentType(tag="EQ-T-ERV-MANIFOLD-6-EXH",
                  name="Fabricated air plenum, 8\" inlet, 6 x 4\" dampered ports, extract",
                  footprint=(inch(24), inch(8)), height=inch(8),
                  plan_symbol="erv",
                  duct_ports=6, port_diameter=inch(4),
                  static_loss_pa_at_cfm=((60.0, 0.5), (120.0, 1.8), (210.0, 5.5)),
                  source="EQ-T-ERV-MANIFOLD-6's part on the extract side: same fabricated galvanized box, same 8 in. inlet collar, same six 4 in. dampered start collars, same price. It is a separate catalog row only because the trunk's service is the direction, and the direction is what a check reads.",
                  ports=(ServicePort(tag="trunk", service=Service.RETURN_AIR,
                                     position=(ft(0), ft(0), inch(4))),)),
    # The mixing box: where the ERV's fresh leg joins System 1's return. A box and not a tee
    # because of the damper in it — a backdraft damper on the ERV leg is what keeps the
    # return working when the ERV is off, which is the behaviour the owner asked for and is
    # behaviour, not geometry.
    #
    # ** IT GREW FROM 10 x 12 x 8 TO A REAL RETURN PLENUM ON 2026-09-04, AND THAT IS A FIX. **
    # It used to be a small box beside the return duct, and REG-S-HP-RET was a 30 x 16 ceiling
    # grille that lapped BOTH of them: 240 in2 of its face opened into the duct, 120 in2 into
    # this box, and the remaining 120 in2 into bare soffit cavity. A return drawing a quarter
    # of its face out of a framed cavity is IMC 601.5's building-cavity-as-plenum, and nothing
    # in the engine grades it. The box is now 12 x 29 1/2 x 18 — the full east lane of
    # SF-S-HP1 south of the air handler — and the grille sits WHOLLY inside it, which is what
    # makes the fresh air and the room air actually mix in a box instead of in a joist bay.
    #
    # 12" is the east lane less the 2" hanger gap off DU-S-HP-SUP; 29 1/2" stops it clear of
    # the cabinet's south face at y=30'-4 1/2"; 18" fills the 18 1/4" cavity. 750 cfm through
    # the 12 x 18 it presents to DU-S-HP-RET is 500 fpm, a duct velocity, and the grille's own
    # face is 336 in2 at 279 fpm.
    EquipmentType(tag="EQ-T-ERV-MIXING-BOX",
                  name="Return-air mixing plenum, 6\" ERV leg with backdraft damper",
                  footprint=(inch(12), inch(29.5)), height=inch(18),
                  plan_symbol="erv",
                  source="Fabricated plenum box, 12 x 29 1/2 x 18 in: System 1's return plenum, with a 6 in ERV inlet on a gravity backdraft damper and a filter-back return grille in its underside. The damper is the whole point — the ERV and the air handler run on independent schedules and each must breathe without the other. It was a 10 x 12 x 8 box until 2026-09-04, beside the return rather than containing it; the grille then lapped the box, the duct and 120 in2 of bare cavity at once.",
                  ports=(ServicePort(tag="fresh", service=Service.SUPPLY_AIR,
                                     position=(ft(0), ft(0), inch(4))),
                         ServicePort(tag="return", service=Service.RETURN_AIR,
                                     position=(ft(0), ft(0), inch(4))))),
    # The two exterior hoods, ONE CASTING ON TWO ROWS. An intake hood and a discharge hood
    # are the same part with the damper reversed; they were one type here for exactly that
    # reason, and the BOM argument was the wrong way round. A row's honesty is its rate, not
    # its count: these two rows carry the same $/ea, so one hood on each still orders the
    # same two castings and the same two flashed 6" penetrations. What the single row cost
    # was the only fact a check can read — which way the air goes. Stated once as
    # OUTDOOR_AIR, the discharge hood reached by an EXHAUST run could only be UNKNOWN, and
    # the UNKNOWN was about this catalog, not about the building. Split the row, keep the
    # rate, and the model says what the damper says.
    EquipmentType(tag="EQ-T-ERV-HOOD-6",
                  name="Exterior ventilation hood, 6\" round, bird screen + backdraft damper",
                  footprint=(inch(12), inch(12)), height=inch(12),
                  plan_symbol="erv",
                  # A hood IS a one-port fitting, and saying so is what keeps it out of
                  # `mep.erv_manifold_ports`'s UNKNOWN column. It carries EquipmentKind.
                  # DUCT_MANIFOLD because there is no HOOD kind in the enum, so the port
                  # census walks it; one 6" duct is exactly what may land on it, and a
                  # second would be a real defect this now reports.
                  duct_ports=1, port_diameter=inch(6),
                  source="Generic 6\" wall/gable hood with 1/4\" bird screen and a gravity backdraft damper. Screen mesh is deliberately coarse: a fine mesh frosts shut on an intake at -15 F.",
                  ports=(ServicePort(tag="duct", service=Service.OUTDOOR_AIR,
                                     position=(ft(0), ft(0), inch(6))),)),
    EquipmentType(tag="EQ-T-ERV-HOOD-6-EXH",
                  name="Exterior ventilation hood, 6\" round, discharge, bird screen + backdraft damper",
                  footprint=(inch(12), inch(12)), height=inch(12),
                  plan_symbol="erv",
                  duct_ports=1, port_diameter=inch(6),
                  source="EQ-T-ERV-HOOD-6 with the damper reversed — the same casting, the same screen, the same price, on the discharge side. The screen stays the coarse 1/4\" mesh: a discharge hood carries humid room air and a fine mesh frosts shut on it as readily as on an intake.",
                  ports=(ServicePort(tag="duct", service=Service.EXHAUST_AIR,
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
                 name="Over-bench capture hood, 30\" x 12\" face, 4\" collar",
                 footprint=(inch(30), inch(12)), height=inch(8),
                 plan_symbol="register", ventilation_terminal=True,
                 # A fabricated hood is a plenum with a collar, so the coefficient is higher
                 # than a diffuser's: K = 6 on the 4" collar velocity pressure
                 # (notes/erv_static_budget.md §5). 25 cfm is this terminal's design flow.
                 static_loss_pa_at_cfm=((10.0, 1.2), (25.0, 7.6), (40.0, 19.4)),
                 source="Fabricated sheet capture hood over FURN-B-WORKSHOP-BENCH-N/S, hung at 5'-6\" — 24\" above the 34\" bench tops. Captures at the source instead of diluting into the room; 4 in. collar since 2026-09-12, with the radial it hangs off. One hood does not cover ten feet of bench; see the note in plan/mep_erv.py.",
                 ports=(ServicePort(tag="return", service=Service.RETURN_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
)


# ============================ THE DUCT ITSELF, AS A PRODUCT ============================
#
# A `DuctRun` states a MATERIAL and a NOMINAL DIAMETER and nothing else about the pipe,
# which is right: those two are what an estimator orders on, and they are exactly the pair
# `prices.toml`'s `[ducts]` already qualifies its rows by. What they cannot tell a pressure
# calculation is the BORE (4" snap-lock really is 4.0" inside; 4" semi-rigid aluminium is
# not) or the ROUGHNESS, and each moves friction by more than the tolerance of the answer.
#
# So the pair is the key and a row here is the value. `mep.erv_static_budget` joins on
# (material, nominal diameter) — one join, the same join the price uses — and a run whose
# pair names no row is reported UNKNOWN by name rather than given a house-average epsilon.
#
# ** THE PHYSICS IS THE ENGINE'S; THE COEFFICIENTS ARE THIS HOUSE'S. ** Darcy-Weisbach with
# a Colebrook friction factor is public and lives in the check. The absolute roughness of
# galvanized steel and of semi-rigid aluminium, and the equivalent length of one 90-degree
# bend, are readings off ASHRAE Fundamentals Ch. 21 that belong to whoever authored the row
# — the same division `PublishedSpan` makes between a table read and a calculation. Every
# one of them is worked in notes/erv_static_budget.md §2 and §3.
DUCT_PRODUCT_TYPES_ERV = (
    # ** THE RADIAL, AND THE WHOLE POINT OF THE 2026-09-12 REDESIGN. ** Every radial in this
    # house was 3" semi-rigid until BLD-08; it is 4" galvanized snap-lock now. The size is
    # not a pressure decision — a 3" tube carries these flows — it is a CATALOGUE decision:
    # 3" pipe, elbows and start collars are stocked (Ferguson SHMKD260305, Menards 3" start
    # collar), but 3" dampers and grilles are a thin, Amazon-grade catalogue, while at 4"
    # every part is a bath-fan commodity off a shelf in Bloomington. Going up also bought
    # static back, which is how the system clears its budget on 6" trunks.
    DuctProductType(tag="DUCT-T-GALV-4",
                    name="4\" galvanized snap-lock round duct, 26 ga",
                    material="galvanized", nominal_diameter=inch(4),
                    # Snap-lock is a longitudinal seam, so the bore IS the nominal size.
                    bore_diameter=inch(4),
                    # ASHRAE Fundamentals Ch. 21 Table 1, galvanized steel with a
                    # longitudinal seam: "medium smooth", 0.0003 ft.
                    roughness_m=0.0000914,
                    # 600 fpm. NOT a pressure limit and not the pipe's capacity — 4" round
                    # carries 78 cfm before it is noisy in a duct sense. This is the QUIET
                    # limit for a branch running continuously ten feet from a pillow, which
                    # is the only limit a whole-house ventilation branch actually has.
                    max_cfm=50.0,
                    # 2'-6". ASHRAE Ch. 21's C = 0.22 for a smooth r/D = 1.5 elbow, converted
                    # to a length at this product's own friction factor: 0.22 x 0.333 ft /
                    # 0.0324 = 2.26 ft, rounded UP for a stamped adjustable elbow, which is
                    # rougher than the smooth radius the coefficient was measured on.
                    bend_equivalent_length=inch(30),
                    source="Commodity 26 ga galvanized snap-lock round pipe with stamped adjustable elbows and start collars — the bath-fan aisle, stocked by every Twin Cities supply house. Roughness and bend coefficient are ASHRAE Fundamentals Ch. 21 reads, worked in notes/erv_static_budget.md §2-3."),
    # ** THE FLEXIBLE LEG, AND IT IS A ROW WITH NO RUN NAMING IT TODAY. ** A radial threading
    # an FS-S-WEST truss web wants a short flexible tail rather than a made-up offset in
    # rigid pipe. No run in this house is authored as one — every radial is drawn rigid end
    # to end — so this row prices nothing and grades nothing. It is here because the note's
    # comparison of the two products has to be reproducible from typed data rather than from
    # a paragraph, and because the first run that needs one should find the row waiting.
    DuctProductType(tag="DUCT-T-SEMIRIGID-4",
                    name="4\" semi-rigid aluminium duct",
                    material="semi_rigid", nominal_diameter=inch(4),
                    # Corrugated wall: the bore is under the nominal size, which is half of
                    # why this product costs so much more static than the snap-lock above.
                    bore_diameter=inch(3.8),
                    # ASHRAE Ch. 21 Table 1, flexible metallic duct FULLY EXTENDED. A
                    # compressed one is several times worse and is not a product, it is a
                    # defect.
                    roughness_m=0.0009144,
                    max_cfm=40.0,
                    bend_equivalent_length=inch(42),
                    source="Semi-rigid corrugated aluminium, for a short leg through a floor-truss web where rigid pipe cannot be dressed. Referenced by no run today; kept so notes/erv_static_budget.md §6's rigid-versus-flexible comparison reads off typed data."),
    # ** THE TRUNK. ** Both risers, both basement trunks, the mixing-box feed and both
    # outdoor legs. 6" and not 8": Broan's manual asks for 8" above 200 cfm with long runs,
    # and notes/erv_static_budget.md §7 is where this house answers that — at 6" the worst
    # path lands inside the certified rating point, and the 8" upsize is PRICED there as the
    # fallback rather than built.
    DuctProductType(tag="DUCT-T-GALV-6",
                    name="6\" galvanized round duct, 26 ga",
                    material="galvanized", nominal_diameter=inch(6),
                    bore_diameter=inch(6),
                    roughness_m=0.0000914,
                    # 1,270 fpm — a TRUNK velocity, not the 600 fpm quiet-branch limit on
                    # the 4" row. These runs are in a chase and a joist bay, not over a bed.
                    max_cfm=250.0,
                    # 0.22 x 0.5 ft / 0.0225 = 4.89 ft, rounded to 4'-6" for the same
                    # stamped-elbow reason as the 4" row.
                    bend_equivalent_length=inch(54),
                    source="Commodity 26 ga galvanized round pipe. The OA and EA legs carry it inside an R-8 wrap with a sealed vapour jacket (DuctRun.insulation), which changes what the run costs and nothing about what it resists."),
    # ** THE REJECTED ALTERNATIVE, KEPT SO THE NOTE'S ARITHMETIC IS READABLE. ** Insulated
    # flex is what a Twin Cities contractor reaches for on a 6" ERV leg, and it is why this
    # system is built out of rigid pipe instead: at this roughness the OA and EA legs alone
    # cost about 0.44 in. w.g., which is most of the machine's whole budget, and the upsize
    # to 8" that would buy it back does not pay for itself. Referenced by no run.
    DuctProductType(tag="DUCT-T-FLEX-6",
                    name="6\" insulated flexible duct, R-8 jacket",
                    material="flex", nominal_diameter=inch(6),
                    bore_diameter=inch(6),
                    # ASHRAE Ch. 21, flexible metallic fully extended — an order of magnitude
                    # over snap-lock, and the entire argument.
                    roughness_m=0.0009144,
                    max_cfm=250.0,
                    bend_equivalent_length=inch(84),
                    source="Insulated flex, the conventional Twin Cities ERV trunk. REFUSED for this house: notes/erv_static_budget.md §6 works the same two runs both ways and flex costs about three times the static of rigid pipe in the same wrap. Named by no run; the row exists so that comparison rests on typed data."),
)
