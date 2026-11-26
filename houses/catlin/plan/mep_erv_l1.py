# haus: editable
# Catlin MEP — the ERV: the machine, its outdoor side, its risers, its radial distribution.
#
# Split out of plan/mep_hvac.py (which keeps System 1's conditioned-air chase) because the
# ERV stopped being four rectangular trunks and became a system: a real machine with four
# ports, an outdoor side that did not exist before, three risers up one shaft and one beside
# it, five distribution plenums and twenty-three radials. mep_hvac.py was at its page budget
# with the trunks alone.
#
# =============================== THE SYSTEM, IN BRIEF ==================================
#
# **The machine** is a **Broan B210E75RT**: 6" round top ports, 24.8"W x 21.6"H x 21"D,
# MERV 8 filter, 81% SRE at 32 F and **65% SRE at -13 F**. EQ-B-ERV keeps its uid (IFC
# GlobalId stability) and its position.
#
# ** THE WHOLE FAN CURVE IS TYPED DATA NOW (2026-09-12, BLD-08), AND THE ARGUMENT IS OVER. **
# "210 at 0.2"" and "206 at 0.4"" were never two claims; they are two stations on one curve,
# and `EQ-T-BROAN-B210E75RT.fan_curve` carries all ten published points (214 @ 0.1" down to
# 176 @ 1.2", ceiling 1.3" where the core deforms). `mep.erv_static_budget` computes what
# THIS duct system costs and reads the curve at it: **0.374" w.g. worst path, 207 cfm
# delivered**, via DU-B-ERV-R-SAUNA-EXH on the EXTRACT side. The oracle is
# notes/erv_static_budget.md.
#
# ** THE 8" UPSIZE BROAN'S MANUAL ASKS FOR ABOVE 200 cfm IS NOW OBEYED IN FULL. ** Both
# outdoor legs went to 8" on 2026-09-15. DU-ERV-EA first, which moved the governing side
# from extract to supply and bought almost nothing because the two columns were 0.0086"
# apart; then DU-ERV-OA, which had been blocked on geometry rather than money until both
# hoods moved to the NORTH face and its riser left the chase. That one took 0.1318 -> 0.0315
# and handed the governing side back to extract. The delivered figure went 203 -> 205.7 ->
# 207.0 cfm against MN's 205. The note's §7 is now spent; §6 says the only large term left
# anywhere is DU-ERV-RISER-EXH, at 58% of the governing column on its own.
# `ventilation_cfm=210` stays authored — see plan/mep_erv_types.py for why moving it is a
# separate decision with a live verdict behind it. It is a design INTENT: 210 is the curve's
# value at 0.2" w.g. and no real duct system lands there. **205 (MN 1322 R403.5) is the
# number that governs**, and `code.N1103_6_whole_house_ventilation` is what grades it.
#
# The SRE goes 0.75 -> 0.65 and that is a *worse* number on purpose: -15 F is this site's
# heating design temperature (plan/site.py), so the -13 F certified figure is the honest one
# for the block load. It raises the ventilation term; `mep.heating_capacity` moves with it,
# and that movement is a fact about a real machine rather than a regression.
#
# **It is a home-run install, not trunk-and-branch, and since 2026-09-12 every part of it
# is a commodity.** Every rectangular ERV trunk is deleted. What replaces them is one **4"
# galvanized snap-lock** radial per terminal off a **fabricated galvanized plenum**, which is
# the whole labour argument: no tees to cut in, no branch takeoffs to seal, and every
# terminal balanceable at a butterfly damper on its own start collar rather than at the
# grille. Twenty-three radials at 5-30 cfm each, one run per terminal, nothing doubled.
#
# ** THE 75 mm SEMI-RIGID TUBE IS GONE AND IT WAS A SOURCING DECISION, NOT A PRESSURE ONE. **
# (plans/buildability.md BLD-08.) Radial semi-rigid at 75 mm has three US sellers — Zehnder,
# and Brink through 475 — and no Minnesota dealer for either; the owner's decision is no
# proprietary tube. The TOPOLOGY survives intact, because a home run off a dampered plenum is
# documented standard practice and needs no special part: an 8" plenum with 4" takeoffs,
# start collars with dampers, 4" bath-fan grilles, all off a shelf in Bloomington.
# ** 4" AND NOT 3" IS A CATALOGUE DECISION. ** A 3" branch carries these flows easily and 3"
# pipe, elbows and start collars are stocked — it is 3" DAMPERS and GRILLES that are a thin,
# Amazon-grade catalogue. At 4" every part is a bath-fan commodity. The lane spacing below
# did not have to change for it: `mep.duct_joist_bay_occupancy` reads the same UNKNOWN at 4"
# that it read at 3" (12 1/2" clear bay, two 4" runs leave 4 1/2"), and the check tally did
# not move by a single finding.
#
# **The manifolds map to CAVITIES, not storeys.** This is the finding that makes the layout
# cheap. A terminal is fed from whichever floor cavity it sits in, and there are three:
#
#   1. the basement ceiling, at the ERV in RM-B-FURNACE — the six basement terminals;
#   2. RM-M-MECH, the 15 sf shaft closet — main-storey CEILING grilles *and* second-storey
#      FLOOR boots, because both open into the one FS-S-WEST/EAST cavity;
#   3. the FS-ATTIC deck at the chase head — second-storey ceiling grilles, the attic
#      pickup, and the mixing-box feed.
#
# **Routing rule, forced by the deck construction.** Every floor system in this house runs
# its bays east-west (`direction="x"`). FS-S-WEST (x 0'-18') is open-web floor truss with an
# 8 7/8" chord-to-chord opening, so a 4" radial crosses joists there freely; FS-S-EAST and
# every I-joist field cannot be crossed. So each level-2 radial goes **north-south through
# the truss webs on the west half first, then turns east along a bay** — which is exactly
# why the level-2 manifolds belong in RM-M-MECH (x 0'-6') and not somewhere central. Bays
# continue across the x=18' split at a given y, so reaching the east half is a straight ride.
#
# Hard exclusions, all of them checked: W-M-HS4 (the laundry pocket) takes nothing ever;
# FO-S-STAIR (x 10'-3 1/8"..17'-8 5/8", y 26'-0 3/8"..35'-5 3/8") blocks every FS-S bay
# between those y values across the middle of the house; FO-A-STAIR (x 22'-5 3/8"..35'-5 3/8",
# y 5'-4"..8'-9 5/8"); FS-ATTIC's trimmer pack at y=5'-2 1/4"/5'-4" runs x 18'..35'-5 3/8".
#
# **One forced deviation from the port budget: REG-S-RET-BED3.** It was to be a level-2
# floor boot like BED1 and BED2. It cannot be: FO-S-STAIR blocks EVERY FS-S bay between
# y=26'-0 3/8" and y=35'-5 3/8" across x 10'-3 1/8"..17'-8 5/8", BED3 spans y 27'-36', and
# FS-S-EAST is I-joist so there is no north-south travel on the far side of the well. It is
# fed from **level 3** instead and becomes a ceiling grille rather than a floor boot — which
# for an extract is the better end of the room anyway. Nothing else moved cavity.
# ================================ ROUTING DECLARATIONS ================================
#
# `routing=CHASE` on the basement and attic radials is a *declaration*, not an escape hatch.
# A duct inside a modeled `Soffit` says so with `soffit_ref` and is graded by
# `mep.duct_soffit_occupancy`; CHASE means only a framed shaft that is not modeled as a
# `Soffit`:
#   * basement: boxed under the FS-M-* ceiling, the same status as the rectangular trunks
#     these replace;
#   * attic: an open deck chase along the west wall at x=1'-0" carries the north-south leg
#     on the FS-ATTIC deck (exposed in the studio eave, owner 2026-10-29), and the east-west
#     leg rides an FS-ATTIC bay. One run cannot declare two cavities, and splitting a single
#     length of pipe into two elements to satisfy an enum would be modelling the checker
#     rather than the house.
# The level-2 radials are `JOIST_BAY` with `floor_ref="FS-S-WEST"` and ARE graded.
from typehaus import (
    DuctRouting,
    DuctRun,
    DuctSystem,
    Equipment,
    EquipmentKind,
    Mount,
    MountKind,
    ft,
    inch,
    pt,
)

from .erv_balance import (
    DU_B_ERV_R_BATH,
    DU_B_ERV_R_BENCH,
    DU_B_ERV_R_GYM,
    DU_B_ERV_R_PLAY,
    DU_B_ERV_R_SAUNA_EXH,
    DU_B_ERV_R_SAUNA_SUP,
    DU_B_ERV_RET_TRUNK,
    DU_B_ERV_SUP_TRUNK,
)

# The catalog — the Broan, the two manifold sizes, the mixing box, the hoods and the bench
# hood — lives in plan/mep_erv_types.py. It is NOT re-exported from here: the editable
# dialect forbids `from plan import ...` (that is why plan/mep.py exists and is not
# editable), so the aggregator imports both modules and hands both to Library(...).
# ==================================== EQUIPMENT ======================================
#
# LEVEL 1 — at the machine, RM-B-FURNACE. EQ-B-ERV itself stays in plan/electrical.py with
# the rest of the equipment schedule. Both plenums hang beside it (2026-11-21, the move to
# the sink, notes/erv_static_budget.md §10.31):
#   * EQ-B-ERV-MAN-SUP straight over the supply port: the trunk is a vertical drop, no turn.
#     20" long, between the north-west trapeze rod and the radial lanes at x=9'-0"/9'-6".
#     DU-ERV-OA's row passes under its west end and DU-ERV-EA's under its east end.
#   * EQ-B-ERV-MAN-EXH south of DU-ERV-OA's row, 13" south of the return port.
# They stay south of EQ-B-ESS-BATT's separation zone (y >= 31'-6") as before.
EQUIPMENT_ERV_BASEMENT = [
    Equipment(uid="QGMYDXSMKH", tag="EQ-B-ERV-MAN-SUP", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(inch(92.25), inch(309.21875)), footprint=(inch(20), inch(8)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV-PLENUM-B-SUP",
              mount=Mount(kind=MountKind.CEILING, elevation=inch(86))),
    Equipment(uid="CRN5GT0ECP", tag="EQ-B-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(inch(82.8), inch(282.84375)), footprint=(inch(36), inch(8)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV-PLENUM-B-EXH",
              mount=Mount(kind=MountKind.CEILING, elevation=inch(85))),
]
# ============================== LEVEL 1 — BASEMENT RADIALS ============================
#
# Six 4" radials off the two plenums beside the machine, exposed under the basement ceiling
# (four collars; SAUNA-SUP and BENCH are branches). Each leaves its own collar. They travel
# north-south below FS-M-*'s east-west joists, in the corridors that are actually clear:
#
#   * x=9'-0" (GYM) and x=9'-6" (PLAY): the furnace room's east strip, south from the plenum,
#     84"/83 1/8" under DU-B-ERV-R-BATH and over HW-SBATH; x=9'-0" sits under PR-B-SAUNA-VENT.
#   * x=1'-7" (SAUNA-EXH): W-B-CW's bay, out of the panels' 110.26(E) space, south to y=3'-4".
#
# PR-B-SAUNA-VENT runs the x=9'-0" line from y=10'-6" to y=28'-8", rising -20" to -15 1/2", so
# SAUNA-EXH goes down the WEST corridor and east along y=3'-4", south of the vent's corner;
# the sauna supply (2026-11-11) crosses the vent's y=10'-6" run OVER it instead.
#
# REG-B-SUP2's radial is the short one on purpose: it stops in the play room's west wall and
# throws away from FURN-B-PLAY-TV on the east wall.
DUCTS_ERV_BASEMENT = [
    # ** THE MACHINE'S OWN TWO TRUNKS (2026-11-21, §10.31). ** Both 6", the full 210 cfm, off
    # the west half of its top. The supply rises straight off Broan port 2 into
    # EQ-B-ERV-MAN-SUP's underside. The return's kit flex bends at 69.6" (2" straight, R = 6")
    # under DU-ERV-OA's row, runs 13" south and turns up into EQ-B-ERV-MAN-EXH.
    DuctRun(uid="225MZ1YDWB", tag="DU-B-ERV-SUP-TRUNK", system=DuctSystem.SUPPLY,
            path=(pt(inch(86.75), inch(309.21875)), pt(inch(86.75), inch(309.21875))),
            elevations=(inch(61.6), inch(86)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_SUP_TRUNK),
    DuctRun(uid="6BTCWW2S1V", tag="DU-B-ERV-RET-TRUNK", system=DuctSystem.RETURN,
            path=(pt(inch(88.5), inch(295.84375)), pt(inch(88.5), inch(295.84375)),
                  pt(inch(88.5), inch(282.84375)), pt(inch(88.5), inch(282.84375))),
            elevations=(inch(61.6), inch(69.6), inch(69.6), inch(85)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_RET_TRUNK, adjustable_elbows=(2,)),
    # GYM leaves MAN-SUP's east end over DU-ERV-EA's lane, turns south on x=9'-0" and drops
    # on a 45 to 84" before DU-B-ERV-R-BATH. South under PR-B-SAUNA-VENT, the bath vent, and
    # the HW-BATH and LSINK legs it crosses, then a 45 ramp to 90 1/8" by y=18'-2 3/8",
    # through W-B-CW3 in its 8'-1"..9'-5" stud bay, 1 1/2" under the plates.
    # ** SOUTH OF EQ-B-WH SINCE 2026-11-09. ** A 45 offset takes it 4" east, off the vent's
    # x=9'-0" line, then south on x=9'-4" over PR-M-S-SUITE-DRAIN (1/2" clear).
    # ** OVER THE BATH CEILING SINCE 2026-11-25. ** At y=11'-3 1/2" it turns east through
    # W-B-BT-W's 127"..143" bay, across RM-B-BATH's 12 3/4" service cavity (south of BATH's
    # drop, so the two never cross), and ENDS in W-B-CS3's 128"..144" bay under the plates on
    # REG-B-SUP1, a sidewall valve on the gym face. It no longer crosses W-B-HALL-W or
    # D-B-GYM's king. SAUNA-SUP tees off it.
    DuctRun(uid="CND5TE40W0", tag="DU-B-ERV-R-GYM", system=DuctSystem.SUPPLY,
            # Stock turns only: two 45 degree ramps and a 45 degree offset.
            # x=9'-0 1/4" (2026-11-21): 2" of collar damper before the first elbow.
            path=(pt(inch(102.25), inch(308.21875)), pt(inch(108.25), inch(308.21875)),
                  pt(inch(108.25), inch(302)), pt(inch(108.25), inch(296)),
                  pt(inch(108.25), inch(224.5)), pt(inch(108.25), inch(218.375)),
                  pt(inch(108.25), inch(211.75)),
                  pt(inch(112), inch(208)),
                  pt(inch(112), inch(135.5)), pt(ft(18), inch(135.5))),
            elevations=(inch(90), inch(90), inch(90), inch(84), inch(84), inch(90.125),
                        inch(90.125), inch(90.125), inch(90.125), inch(90.125)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_R_GYM),
    # PLAY leaves MAN-SUP's north face, crosses the strip east at y=26'-7 1/4" (2" of collar
    # damper before its first elbow, 2026-11-21) over DU-ERV-EA and
    # D-B-CLOSET's swing, turns south on x=9'-6" and drops on a 45 to 83 1/8", under
    # DU-B-ERV-R-BATH. It rises to 91 1/4" at y=19'-7 1/4" and crosses W-B-STR2 in its
    # 19'-4"..20'-8" bay under the top plate (-15 5/8"), eases down 1/2" east to clear
    # PR-B-LSINK-DRAIN's riser, jogs south over PR-B-BATH-VENT at x=12'-3" and leaves through
    # W-B-BA-E at y=18'-6 3/4" (the one gap in that staggered wall south of the bath's three
    # risers wide enough for a 4" duct). Then 1'-5" north up the hall at x=16'-9" and east at
    # y=20'-6" into W-B-CN2's 240"..256" stud bay, where it ends on REG-B-SUP2, a sidewall
    # valve on the theater face. CHASE since SF-B-BATH retired (2026-11-25): the old bath it
    # crossed is the WH alcove and the hall, both exposed-service rooms now.
    DuctRun(uid="DMEQ946YAX", tag="DU-B-ERV-R-PLAY", system=DuctSystem.SUPPLY,
            path=(pt(inch(98.5), inch(313.21875)), pt(inch(98.5), inch(319.25)),
                  pt(ft(9, 6), inch(319.25)), pt(ft(9, 6), inch(310)),
                  pt(ft(9, 6), inch(303.15)),
                  pt(ft(9, 6), ft(19, 7.25)), pt(ft(9, 6), ft(19, 7.25)),
                  pt(ft(12, 3), ft(19, 7.25)), pt(ft(12, 3), ft(18, 6.75)),
                  pt(ft(16, 9), ft(18, 6.75)), pt(ft(16, 9), ft(20, 6)),
                  pt(ft(18), ft(20, 6))),
            elevations=(inch(90), inch(90), inch(90), inch(90), inch(83.15), inch(83.15),
                        inch(91.25), inch(90.75), inch(90.75), inch(90.75), inch(90.75),
                        inch(90.75)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_R_PLAY),
    # ** THE SAUNA SUPPLY IS A BRANCH OFF GYM'S BATH-CEILING LEG (2026-11-25). ** It taps GYM
    # at x=11'-0 1/2" and rises on a 45 to 94 3/4" (3/4" under the joists) to pass over the
    # bath's supply band (PR-B-CW-SAUNA at y=8'-7", top 92 7/8"; HW-SAUNA only reaches east
    # of x=12'-3") and W-B-SA-N's top (90"), between the sauna vent's riser (x=10'-7") and
    # CW-SAUNA's drop (x=11'-5 1/2"). Over the sauna's service cavity a 45 runs it to
    # x=16'-7 3/4", then 10 3/4" down to REG-B-SUP3 over the heater: Harvia's layout. x=16'-8"
    # straight south was the first try; the bath's lav and HW lines fill that crossing.
    DuctRun(uid="VXGA0P0V72", tag="DU-B-ERV-R-SAUNA-SUP", system=DuctSystem.SUPPLY,
            path=(pt(inch(132.5), inch(135.5)), pt(inch(132.5), inch(131.5)),
                  pt(inch(132.5), inch(126.875)), pt(inch(132.5), inch(96)),
                  pt(inch(199.75), inch(28.75)), pt(inch(199.75), inch(20.5)),
                  pt(inch(199.75), inch(20.5))),
            elevations=(inch(90.125), inch(90.125), inch(94.75), inch(94.75), inch(94.75),
                        inch(94.75), ft(7)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_R_SAUNA_SUP),
    # The bench extract is a branch off SAUNA-EXH's x=1'-7" leg (2026-11-11). It takes off the
    # SIDE at y=7'-9" (82 1/4"), never the bottom: the sauna's duct sweats. West 8" to over
    # REG-B-RET1, then the derived drop down W-B-W2's concrete face to the valve at 46" AFF
    # (2026-11-15; exposed, the workshop ceiling is open by design). Closing the sauna hatches
    # swings flow here, so a 4" balancing damper sits on the drop at ~62", reached from the floor.
    DuctRun(uid="MTVYDDP43W", tag="DU-B-ERV-R-BENCH", system=DuctSystem.RETURN,
            path=(pt(ft(1, 7), ft(7, 9)), pt(inch(11), ft(7, 9))),
            elevations=(inch(82.25), inch(82.25)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_R_BENCH, inline_dampers=(inch(28),)),
    # The basement bath's extract (2026-11-25, the bath north of the sauna; first laid by
    # `haus route`) leaves MAN-EXH's east end at 89", runs east to x=10'-8" and south through
    # the workshop: a 45 down to 86 1/2" under DU-B-ERV-R-PLAY's y=19'-7 1/4" leg, a 45 up to
    # 91 1/8" (4" over the collar, two elbows' take-off), through W-B-CW2's and W-B-BT-N's
    # stud bays, and down into REG-B-EXH1's ceiling collar north of GYM's bath leg. Still its
    # own collar-bath radial: the sauna extract it could tee onto is at 44 of 50 cfm.
    DuctRun(uid="03883CKF0H", tag="DU-B-ERV-R-BATH", system=DuctSystem.EXHAUST,
            path=(pt(inch(100.8), inch(282.84375)), pt(inch(128), inch(282.84375)),
                  pt(inch(128), inch(245)), pt(inch(128), inch(242.5)),
                  pt(inch(128), inch(230)), pt(inch(128), inch(225.375)),
                  pt(inch(128), inch(145)), pt(inch(128), inch(145))),
            elevations=(inch(89), inch(89), inch(89), inch(86.5), inch(86.5), inch(91.125),
                        inch(91.125), inch(87.125)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_R_BATH),
    # It leaves MAN-EXH's west end at 90 1/2", passes OVER PR-M-S-BATH1-DRAIN's x=5'-0" fall
    # (1/4" clear), drops on a 45 to 82 1/4" before ED-B-FURNACE-STRIP1 and runs west on
    # y=23'-6 27/32" to W-B-CW's x=1'-7" bay (out of the panels' 110.26(E) space), then
    # south and east at y=3'-4" into the centre of W-B-SA-W's 5 1/2" cavity and down between
    # the studs to the low pickup 4" off the floor. W-B-SA-W uses SAUNA_2X6 so the 4" section
    # fits, 1/4" off the west stud face and 1 1/4" off the east.
    DuctRun(uid="1Y457X9DMH", tag="DU-B-ERV-R-SAUNA-EXH", system=DuctSystem.EXHAUST,
            path=(pt(inch(64.8), inch(282.84375)), pt(inch(57.5), inch(282.84375)),
                  pt(inch(49.25), inch(282.84375)),
                  pt(ft(1, 7), inch(282.84375)), pt(ft(1, 7), inch(40)),
                  pt(inch(116), inch(40)), pt(inch(116), inch(40)),
                  pt(inch(122), inch(40))),
            elevations=(inch(90.5), inch(90.5), inch(82.25), inch(82.25), inch(82.25),
                        inch(82.25), inch(4), inch(4)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_R_SAUNA_EXH),
]
