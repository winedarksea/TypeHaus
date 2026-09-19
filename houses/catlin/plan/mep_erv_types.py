# haus: editable
# Catlin MEP — the ERV's catalog: the machine, its manifolds, its mixing box, its hoods.
#
# Split off plan/mep_erv.py (AGENTS.md's 500-line rule; that file is itself now five,
# one per cavity) at the seam the rest of this house
# already uses: type DEFINITIONS here, placed INSTANCES there. Nothing in this file is
# draggable, and the `# haus: editable` marker rides along only because the dialect linter
# reads the whole plan package as one dialect — there is no element here to write back.
#
# Read plan/mep_erv_l1.py first; it is where the system is explained.

from typehaus import (
    DuctProductType,
    EquipmentType,
    PortCertainty,
    RegisterType,
    Service,
    ServicePort,
    ft,
    inch,
)

EQUIPMENT_TYPES_ERV = (
    # The machine. Ports are all on top and all 6" round. There is no adapter line in the
    # BOM any more: BLD-08 took the 160 mm collared radial manifold out with the 75 mm tube,
    # and what replaces it is an 8" fabricated plenum with 4" dampered ports, so the trunk
    # off the machine steps 6" -> 8" on a commodity reducer (library/hvac.py).
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
    # The same six-port manifold, cast for the EXTRACT side. Identical part, identical
    # price, one field different: the trunk carries stale air away from the house, so the
    # port is RETURN_AIR — which is what EQ-T-ERV-MANIFOLD-10 has always declared, this
    # house's only other extract manifold. Two placements used the supply type and
    # `mep.equipment_port_service` could only call them UNKNOWN, because a type that states
    # its direction once cannot describe a placement that reverses it, and a FAIL there
    # would have reported the catalog rather than the building.
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

    # ** THE TWO LEVEL-2 PLENUMS ARE HOUSE-LOCAL AND DIMENSIONED, AND THAT IS THE POINT. **
    # `library/hvac.py` carries the shared plenums and states a COUNT and no layout, because
    # a collar layout is a shop drawing for one fabricated box and a reusable catalog part
    # has no shop drawing behind it. These two have one. Stating where the collars are is
    # what lets `mep.erv_manifold_ports` grade each radial against the collar it lands on
    # rather than against a tally, and what stops `route_support` re-aiming a radial at its
    # neighbour's hole.
    #
    # Collar stations are in the product frame: origin at the footprint centre, +y toward
    # the back. `EquipmentType._check_collars` refuses two collars closer than their own
    # diameter — two 4" collars on 2" centres are one 6" hole — and refuses a layout that
    # disagrees with `duct_ports`.
    EquipmentType(tag="EQ-T-ERV-PLENUM-M-SUP",
                  name="Fabricated supply plenum, 8in inlet, 3 x 4in dampered collars",
                  footprint=(inch(24), inch(8)), height=inch(8), plan_symbol="erv",
                  duct_ports=3, port_diameter=inch(4),
                  static_loss_pa_at_cfm=((60.0, 0.5), (120.0, 1.8), (210.0, 5.5)),
                  source="Fabricated galvanized plenum for THIS house, 24 x 8 x 8 in: an 8 in trunk inlet and three 4 in dampered start collars at the stations below. The collar layout is a shop drawing and is authored here rather than in library/hvac.py for that reason. No submittal has been read; the stations are the design's and the fabricator confirms them.",
                  ports=(ServicePort(tag="trunk", service=Service.SUPPLY_AIR,
                                     position=(ft(0), ft(0), inch(4))),
                         ServicePort(tag="collar-study", service=Service.SUPPLY_AIR,
                                     position=(inch(1), inch(0), inch(4)),
                                     connection_size=inch(4),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="collar-living", service=Service.SUPPLY_AIR,
                                     position=(inch(5), inch(-4), inch(4)),
                                     connection_size=inch(4),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="collar-bed", service=Service.SUPPLY_AIR,
                                     position=(inch(9), inch(4), inch(4)),
                                     connection_size=inch(4),
                                     certainty=PortCertainty.EXACT))),
    # ** THE EXTRACT BOX IS NOT A MANIFOLD ANY MORE. ** Level 2 went trunk-and-branch on
    # 2026-09-19 — thirteen home-run lanes will not leave this closet, and the arithmetic is
    # in plan/mep_erv_l2.py's header — so what leaves this box is ONE 8" trunk, and the ten
    # takeoffs are tee'd off it out in the floor field. Typed as a one-port box at 8" so the
    # census reads what is built: one of one, full, with the 6" riser as the trunk collar.
    # Ordering a ten-port plenum nobody lands ten pipes on is the BOM error this prevents.
    EquipmentType(tag="EQ-T-ERV-PLENUM-M-EXH",
                  name="Fabricated extract plenum, 6in riser inlet, 1 x 8in trunk collar",
                  # The RISER is return air and the TRUNK is exhaust, which is not a
                  # contradiction: this box is where the two halves of the extract side meet.
                  # Eight of the ten takeoffs downstream are wet-room EXHAUST and two are
                  # dry-room RETURN, and the riser carries the sum of both to the machine.
                  footprint=(inch(34), inch(8)), height=inch(8), plan_symbol="erv",
                  duct_ports=1, port_diameter=inch(8),
                  static_loss_pa_at_cfm=((60.0, 0.5), (120.0, 1.8), (210.0, 5.5)),
                  source="Fabricated galvanized plenum for THIS house, 34 x 8 x 8 in: a 6 in riser inlet and one 8 in trunk collar. It keeps the 34 in case the ten-collar version had, because the riser lands on it at the same station and the box is also the transition the 6 in riser needs.",
                  ports=(ServicePort(tag="riser", service=Service.RETURN_AIR,
                                     position=(ft(0), ft(0), inch(4))),
                         ServicePort(tag="collar-trunk", service=Service.EXHAUST_AIR,
                                     position=(inch(-5.5), inch(0), inch(4)),
                                     connection_size=inch(8),
                                     certainty=PortCertainty.EXACT))),

    # ** THE TWO BASEMENT PLENUMS ARE 36" LONG AND THAT IS THE WHOLE DESIGN (D3). **
    # They were 24 x 8 library manifolds stating six ports and no layout, and every radial
    # left from the box's own centre point — three off each — which is why GYM and
    # SAUNA-SUP shared a lane for twenty feet and BATH and SAUNA-EXH shared one for three.
    #
    # ** 24" COULD NOT HOLD FIVE CONNECTIONS. ** Each box takes a 6" trunk AND a 6" riser
    # as well as three 4" collars: the basement plenums are where the machine's air and the
    # upstairs air meet, unlike level 2's, which have one inlet each. `run_interference`
    # wants 5" between a 6" duct and a 4" one and 6" between two 6"s, measured centre to
    # centre where their drops run side by side — and on a 24" box every arrangement put
    # some pair inside that. At 36" the two 6" ports sit 15" apart on the bottom face and
    # the nearest 4" collar drop is 6". Eight inches of extra galvanized is the cheapest
    # part of this campaign.
    #
    # ** THE 6" PORTS ARE ON THE BOTTOM FACE, THE 4" COLLARS ON THE SIDES. ** The trunk and
    # the return come up from the machine, which sits below and west; the radials leave
    # sideways into the ceiling layer, at the box's own mid-height. So the two big
    # connections turn up into the underside and the small ones stay on the 36" faces where
    # there is room to space them. Neither 6" port is a collar — no `connection_size`, so
    # `mep.equipment_port_service` grades them at service level the way it always has.
    EquipmentType(tag="EQ-T-ERV-PLENUM-B-SUP",
                  name="Fabricated supply plenum, 6in trunk + 6in riser, 3 x 4in dampered collars",
                  footprint=(inch(36), inch(8)), height=inch(8), plan_symbol="erv",
                  duct_ports=3, port_diameter=inch(4),
                  static_loss_pa_at_cfm=((60.0, 0.5), (120.0, 1.8), (210.0, 5.5)),
                  source="Fabricated galvanized plenum for THIS house, 36 x 8 x 8 in: a 6 in trunk inlet and a 6 in riser takeoff in the underside, and three 4 in dampered start collars at the stations below. The collar layout is a shop drawing and is authored here rather than in library/hvac.py for that reason. No submittal has been read; the stations are the design's and the fabricator confirms them.",
                  ports=(ServicePort(tag="trunk", service=Service.SUPPLY_AIR,
                                     position=(inch(3), inch(0), inch(0))),
                         ServicePort(tag="riser", service=Service.SUPPLY_AIR,
                                     position=(inch(-12), inch(4), inch(4))),
                         ServicePort(tag="collar-sauna", service=Service.SUPPLY_AIR,
                                     position=(inch(-15), inch(-4), inch(4)),
                                     connection_size=inch(4),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="collar-gym", service=Service.SUPPLY_AIR,
                                     position=(inch(9), inch(-4), inch(4)),
                                     connection_size=inch(4),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="collar-play", service=Service.SUPPLY_AIR,
                                     position=(inch(18), inch(0), inch(4)),
                                     connection_size=inch(4),
                                     certainty=PortCertainty.EXACT))),
    # The extract box is the same shell with the air going the other way: the riser brings
    # the upstairs extract DOWN into it and the trunk carries the sum out to the machine.
    # The collar on the east end is the only one that faces its terminal directly; the other
    # two step clear of the riser's and the trunk's drops before they turn.
    EquipmentType(tag="EQ-T-ERV-PLENUM-B-EXH",
                  name="Fabricated extract plenum, 6in trunk + 6in riser, 3 x 4in dampered collars",
                  footprint=(inch(36), inch(8)), height=inch(8), plan_symbol="erv",
                  duct_ports=3, port_diameter=inch(4),
                  static_loss_pa_at_cfm=((60.0, 0.5), (120.0, 1.8), (210.0, 5.5)),
                  source="Fabricated galvanized plenum for THIS house, 36 x 8 x 8 in: a 6 in riser inlet and a 6 in trunk outlet in the underside, and three 4 in dampered start collars at the stations below. Same shell as EQ-T-ERV-PLENUM-B-SUP; a separate row because the declared services differ and the BOM should read which box is which.",
                  ports=(ServicePort(tag="trunk", service=Service.RETURN_AIR,
                                     position=(inch(10.5), inch(0), inch(0))),
                         ServicePort(tag="riser", service=Service.RETURN_AIR,
                                     position=(inch(-4.5), inch(0), inch(0))),
                         ServicePort(tag="collar-sauna", service=Service.EXHAUST_AIR,
                                     position=(inch(-15), inch(-4), inch(4)),
                                     connection_size=inch(4),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="collar-bench", service=Service.RETURN_AIR,
                                     position=(inch(0), inch(-4), inch(4)),
                                     connection_size=inch(4),
                                     certainty=PortCertainty.EXACT),
                         ServicePort(tag="collar-bath", service=Service.EXHAUST_AIR,
                                     position=(inch(18), inch(0), inch(4)),
                                     connection_size=inch(4),
                                     certainty=PortCertainty.EXACT))),

    # The two exterior hoods and the three plenum types are NOT here: they were promoted to
    # library/hvac.py in e5b64fff because nothing about them is this house's. The argument
    # their comment used to make is the library's now — an intake hood and a discharge hood
    # are one casting with the damper reversed, and they are two ROWS so that a check can
    # read which way the air goes.
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
    # ** THE FLEXIBLE LEG, AND IT IS A ROW WITH NO RUN NAMING IT TODAY. ** A radial threading
    # an FS-S-WEST truss web wants a short flexible tail rather than a made-up offset in
    # rigid pipe. No run in this house is authored as one — every radial is drawn rigid end
    # to end — so this row prices nothing and grades nothing. It is here because the note's
    # comparison of the two products has to be reproducible from typed data rather than from
    # a paragraph, and because the first run that needs one should find the row waiting.
    # ** THE TRUNK. ** Both risers, both basement trunks, the mixing-box feed and both
    # outdoor legs. 6" and not 8": Broan's manual asks for 8" above 200 cfm with long runs,
    # and notes/erv_static_budget.md §7 is where this house answers that — at 6" the worst
    # path lands inside the certified rating point, and the 8" upsize is PRICED there as the
    # fallback rather than built.
    # ** THE DISCHARGE, AND THE ROW THAT SHOULD HAVE LANDED WITH THE UPSIZE. ** DU-ERV-EA
    # went 6" -> 8" for the static budget and no 8" row went with it, so
    # `mep.erv_static_budget` reported "no DuctProductType for (galvanized, 8.0")" and could
    # not resist the one leg the upsize was bought for — the check went UNKNOWN on exactly
    # the term the change was about. The take-off fell through to the un-diametered
    # `exhaust:galvanized` fallback at the same time, 29.3 LF of it.
    # ** THE REJECTED ALTERNATIVE, KEPT SO THE NOTE'S ARITHMETIC IS READABLE. ** Insulated
    # flex is what a Twin Cities contractor reaches for on a 6" ERV leg, and it is why this
    # system is built out of rigid pipe instead: at this roughness the OA and EA legs alone
    # cost about 0.44 in. w.g., which is most of the machine's whole budget, and the upsize
    # to 8" that would buy it back does not pay for itself. Referenced by no run.
)
