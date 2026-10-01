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
# THIS duct system costs and reads the curve at it: **0.371" w.g. worst path, 207 cfm
# delivered**, the worst path being DU-B-ERV-R-PLAY on the SUPPLY side. The oracle is
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
# FO-S-STAIR (x 10'-3 1/4"..17'-8 5/8", y 26'-0 3/8"..35'-5 3/8") blocks every FS-S bay
# between those y values across the middle of the house; FO-A-STAIR (x 22'-5 3/8"..35'-5 3/8",
# y 5'-4"..8'-9 5/8"); FS-ATTIC's trimmer pack at y=5'-2 1/4"/5'-4" runs x 18'..35'-5 3/8".
#
# **One forced deviation from the port budget: REG-S-RET-BED3.** It was to be a level-2
# floor boot like BED1 and BED2. It cannot be: FO-S-STAIR blocks EVERY FS-S bay between
# y=26'-0 3/8" and y=35'-5 3/8" across x 10'-3 1/4"..17'-8 5/8", BED3 spans y 27'-36', and
# FS-S-EAST is I-joist so there is no north-south travel on the far side of the well. It is
# fed from **level 3** instead and becomes a ceiling grille rather than a floor boot — which
# for an extract is the better end of the room anyway. Nothing else moved cavity.
# ================================ ROUTING DECLARATIONS ================================
#
# `routing=CHASE` on the basement and attic radials is a *declaration*, not an escape hatch.
# A duct inside a modeled `Soffit` says so with `soffit_ref` and is graded by
# `mep.duct_soffit_occupancy`; CHASE means only a framed shaft that is not modeled as a
# `Soffit`:
#   * basement: boxed under the mixed SL-M-DECK / FS-M-* ceiling, the same status as the
#     rectangular trunks these replace;
#   * attic: a boxed floor chase along the west wall at x=1'-0" carries the north-south leg
#     on the FS-ATTIC deck, and the east-west leg rides an FS-ATTIC bay. One run cannot
#     declare two cavities, and splitting a single length of pipe into two elements to
#     satisfy an enum would be modelling the checker rather than the house.
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
# The catalog — the Broan, the two manifold sizes, the mixing box, the hoods and the bench
# hood — lives in plan/mep_erv_types.py. It is NOT re-exported from here: the editable
# dialect forbids `from plan import ...` (that is why plan/mep.py exists and is not
# editable), so the aggregator imports both modules and hands both to Library(...).
# ==================================== EQUIPMENT ======================================
#
# LEVEL 1 — at the machine, RM-B-FURNACE. EQ-B-ERV itself stays in plan/electrical.py with
# the rest of the equipment schedule; only its type changed. Both manifolds hang from the
# basement ceiling just south-east of it, ports down.
#
# **They are south of y=31'-6" because EQ-B-ESS-BATT's REQUIRED separation zone starts
# there** (x 49 1/4"..145 1/4", y 378"..460", off EQ-T-ESS-BATT — `advisory.ess_clearance`
# grades it with no room-or-wall exemption). The first attempt put the supply manifold at
# (7'-0", 32'-0") and the check added it to that zone's occupant list on the spot. They are
# also east of x=5'-0" to clear the ERV's own 24.8" x 21" case, and west of x=7'-6" to stay
# out of the room's north-east notch, which is the ESS closet.

#
# ** BOTH BOXES WENT 24" -> 36" ON 2026-09-19 (D3), AND THE COLLARS ARE DRAWN. ** They were
# library `EQ-T-ERV-MANIFOLD-6` plenums, which state a port COUNT and no layout, so every
# radial left from the box's own centre point and three of them shared each lane. The
# house-local types in plan/mep_erv_types.py put each radial on its own hole; the extra
# foot of length is what makes room for the 6" trunk and the 6" riser to turn up into the
# underside without landing within 5" of a collar's drop. The argument is in that file.
#
# The east end moves from x=7'-6" to x=8'-0" and nothing is in the way: RM-B-FURNACE runs
# to x=10'-0" at these y's, and EQ-B-ESS-BATT's separation zone starts at y=31'-6", eight
# inches north of the supply box's north face.
EQUIPMENT_ERV_BASEMENT = [
    # y=30'-5 1/2", not 30'-6": at 30'-6" the box's north face stood 3/8" inside
    # W-B-ESS-S's gypsum (structural.placeable_interference). Collars move 1/2", in tolerance.
    Equipment(uid="QGMYDXSMKH", tag="EQ-B-ERV-MAN-SUP", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(6, 6), ft(30, 5.5)), footprint=(inch(36), inch(8)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV-PLENUM-B-SUP",
              mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 2))),
    # 5/8" lower than its twin: PR-B-SAUNA-VENT's y=28'-8" leg crosses over this box at
    # 7'-10 7/16" and its top stood in the pipe (structural.placeable_interference).
    Equipment(uid="CRN5GT0ECP", tag="EQ-B-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(6, 6), ft(28, 6)), footprint=(inch(36), inch(8)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV-PLENUM-B-EXH",
              mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 1.375))),
]
# ============================== LEVEL 1 — BASEMENT RADIALS ============================
#
# Six 4" radials off the two plenums beside the machine, boxed under the basement ceiling.
#
# ** REDRAWN 2026-09-19 (D3). ** What was here before ran every radial from its plenum's
# centre point at one flat 7'-6", which put GYM and SAUNA-SUP on the same line for twenty
# feet, BATH and SAUNA-EXH on the same line for three, and all six through the middle of
# the drain field between y=18'-9" and y=20'-0". Twenty-three pairs. The fix is two moves
# and neither is a search result:
#
#   1. **Each radial leaves its own collar** (plan/mep_erv_types.py), so no two start at
#      one hole and no two are born collinear.
#   2. **The lanes move to the four corridors that are actually clear**, measured rather
#      than assumed — and they are not in FS-M-WEST's joist bays, which run east-west while
#      every one of these radials travels north-south. The band between the joists'
#      underside (-11 7/8") and the top of the drain zone is 2 3/4"; a 4" duct does not go
#      in it. The corridors that do work:
#
#        * **x=3'-3" and x=3'-9", -21 15/16" and -23 7/16"** — between PR-B-KITCH-DRAIN's
#          x=4'-6" fall line and the SH2/SINK2 pair that converge on (3'-0", 16'-6"). Each
#          holds one 4" duct and only one: the window is PR-B-WC1-DRAIN's tail at y=22'-0"
#          on top and PR-M-S-BATH1-DRAIN's rake at y=17'-0" underneath, about three inches
#          of air.
#        * **x=2'-0", -27 15/16"** — under everything, over PR-B-SINK2-DRAIN's -25.4"
#          at y=15'-9". 79 1/2" of headroom under it, in the workshop, where the ceiling is
#          open by design and the bench hood it feeds hangs at 5'-6" anyway.
#        * **x=9'-0", x=9'-6" and x=8'-0"** — the furnace room's east strip, for GYM, PLAY
#          and BATH, stacked by elevation (see each run). The old "east chase" over ST-B2M
#          is gone (2026-09-22): nothing crosses the stair.
#
# PR-B-SAUNA-VENT is the wall that shapes all of this. It runs the x=9'-0" line from
# y=10'-6" to y=34'-6", rising -20" to -15 1/2" as it goes, so every east-west lane in the
# west half crosses it and the crossing elevation depends on where. At y=29'-6" it is at
# -16 7/16" and a duct passes under it at -20 7/16" with 1 3/16" to spare; at y=10'-6" it
# is at -20" and nothing passes under it at all inside the ceiling. That is why the two
# sauna radials go down the WEST corridors and come east along y=1'-8 1/2" and y=3'-2",
# south of the vent's corner, where the floor is clear the full width of the house.
#
# REG-B-SUP2's radial is the short one on purpose. The play room's whole ceiling is
# SL-M-DECK's 14 3/8" solid concrete with NO cavity at all, so every foot of that run is
# surface-mounted; entering at the room's west edge and stopping just inside cuts about
# eight feet of exposed duct off the old (27', 27') position. It still throws away from
# FURN-B-PLAY-TV on the east wall.
DUCTS_ERV_BASEMENT = [
    # ** THE MACHINE'S OWN TWO TRUNKS. ** Both are 6", the machine's full 210 cfm, and both
    # leave its top.
    #
    # THE SUPPLY TRUNK RUNS EAST FIRST AND RISES SECOND, which is the reverse of how it was
    # drawn and is the whole of its fix. It used to stand straight up off the port at
    # x=4'-9" — 3" from PR-B-KITCH-DRAIN's x=4'-6" fall line, where a 6" trunk and a 3"
    # drain need 4 3/16" — and reported against it for 2 7/8" of elevation. Held at the
    # machine's own port level for the first 2'-0", it passes ten inches under the drain
    # instead and turns up into EQ-B-ERV-MAN-SUP's underside at x=6'-9", east of it.
    DuctRun(uid="225MZ1YDWB", tag="DU-B-ERV-SUP-TRUNK", system=DuctSystem.SUPPLY,
            path=(pt(ft(4, 9), ft(30, 4)), pt(ft(6, 9), ft(30, 4)),
                  pt(ft(6, 9), ft(30, 6)), pt(ft(6, 9), ft(30, 6))),
            elevations=(inch(75.6), inch(75.6), inch(75.6), ft(7, 2)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=210),
    # THE RETURN TRUNK NO LONGER HAS TO DODGE A RADIAL LANE. It used to leave the plenum's
    # east end, drop, cross UNDER the x=6'-6" lane that DU-B-ERV-R-GYM and -SAUNA-SUP
    # shared, and come back west at y=29'-9" — a detour around two ducts that are not there
    # any more. It now drops out of the plenum's underside at x=7'-4 1/2" and runs the
    # y=28'-6" line straight west at the machine's own port level, 7" under
    # DU-ERV-RISER-EXH's approach on the same line and three inches under the deepest
    # collar drop above it.
    DuctRun(uid="6BTCWW2S1V", tag="DU-B-ERV-RET-TRUNK", system=DuctSystem.RETURN,
            path=(pt(ft(7, 4.5), ft(28, 6)), pt(ft(7, 4.5), ft(28, 6)),
                  pt(ft(3, 8), ft(28, 6)), pt(ft(3, 8), ft(29, 9))),
            elevations=(ft(7, 2), inch(75.6), inch(75.6), inch(75.6)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=210),
    # ** NEITHER RADIAL CROSSES ST-B2M ANY MORE (2026-09-22). ** Both used to ride the
    # y=29'-6"/30'-6" belt east over the stair, 1" (GYM) and 15 5/8" (PLAY) into the 6'-8"
    # headroom over the upper flight's nosings — `code.R311_7_2_stair_headroom` counts runs
    # now. The x=17'-0" "east chase" was only continuous by walking over the lower flight.
    #
    # THE GYM RADIAL GOES THROUGH THE WORKSHOP. South on x=9'-0", directly
    # under PR-B-SAUNA-VENT and the bath vent,
    # HW-BATH and LSINK legs it crosses; through W-B-CW3 in its 8'-1"..9'-5" stud bay, over
    # the 2x8 backing (top 6'-7 1/4"); east on y=17'-4 3/4", 2 1/4" clear of
    # PR-M-S-SUITE-DRAIN's riser, through W-B-HALL-W's 16'-8"..18'-0" bay; then the hall's
    # x=17'-0" lane south of the stair to y=13'-0" as before. It rises to 88 1/2" before
    # crossing the hall so its lower face clears D-B-BATH's pocket header at 85 1/2".
    #
    # ** x=17'-0" AND NOT 17'-9", BECAUSE THE STRIP BESIDE THE STAIR IS THE POUR. **
    # W-B-CN / -CN2 / W-B-CS2 are one 12" cast wall on the x=18'-0" axis, so x 17'-6"..18'-6"
    # is concrete; 17'-0" leaves 4" between the duct's east face and it.
    #
    # ** IT RISES 6 1/8" AT x=17'-0" AND CROSSES `W-B-CS3` OVER `D-B-GYM`'s HEADER. ** The
    # header tops out at -22.19" and the double top plate starts at -16.44"; centred at
    # -19 5/16" the duct passes between the cripples at y=12'-4 3/16" and 13'-7 7/16" with
    # 7/8" to header and plate, and cuts nothing (`notes/framing_bore_limits.md` §6a is a
    # hole drilled IN a cripple; this is air between two). The cast sleeve through
    # `W-B-CS2` was the alternative and is not taken: a sleeve is a pre-pour commitment.
    DuctRun(uid="CND5TE40W0", tag="DU-B-ERV-R-GYM", system=DuctSystem.SUPPLY,
            path=(pt(ft(7, 3), ft(30, 2)), pt(ft(7, 3), ft(29, 6)),
                  pt(ft(7, 3), ft(29, 6)), pt(ft(9), ft(29, 6)),
                  pt(ft(9), ft(17, 4.75)), pt(ft(17), ft(17, 4.75)),
                  pt(ft(17), ft(13)), pt(ft(17), ft(13)), pt(ft(19), ft(13))),
            elevations=(ft(7, 6), ft(7, 6), inch(84), inch(84), inch(88.5), inch(88.5), inch(84),
                        inch(90.125), inch(90.125)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=18),
    # THE PLAY RADIAL GOES THROUGH SF-B-BATH. From the plenum's east end it drops to -25 7/16"
    # on x=9'-6" (east of the sauna vent, under everything), rises to -18 3/16" at y=19'-7 1/4"
    # and crosses W-B-STR2 in its 19'-4"..20'-8" bay under the top plate (-15 5/8"). In the
    # soffit it jogs south over PR-B-BATH-VENT at x=12'-3" (east of LSINK's riser; the vent
    # dropped 1 1/2" for it), and leaves through W-B-BA-E at y=18'-6 3/4" — the one gap in that
    # staggered wall south of the bath's three risers (y 19'-3"..19'-10") wide enough for a
    # 4" duct. Then 1'-5" north up the hall at x=16'-9" and east through W-B-CN2 at y=20'-0"
    # into REG-B-SUP2 on its last leg (the room's ceiling is SL-M-DECK's solid concrete; see
    # the register). It turned east at y=25'-0" until 2026-09-23; 5' less hall duct.
    DuctRun(uid="DMEQ946YAX", tag="DU-B-ERV-R-PLAY", system=DuctSystem.SUPPLY,
            path=(pt(ft(8), ft(30, 6)), pt(ft(9, 6), ft(30, 6)), pt(ft(9, 6), ft(30, 6)),
                  pt(ft(9, 6), ft(19, 7.25)), pt(ft(9, 6), ft(19, 7.25)),
                  pt(ft(12, 3), ft(19, 7.25)), pt(ft(12, 3), ft(18, 6.75)),
                  pt(ft(16, 9), ft(18, 6.75)), pt(ft(16, 9), ft(20)), pt(ft(19), ft(20))),
            elevations=(ft(7, 6), ft(7, 6), inch(84), inch(84), inch(91.25), inch(91.25),
                        inch(91.25), inch(91.25), inch(91.25), inch(91.25)),
            diameter=inch(4), routing=DuctRouting.SOFFIT, soffit_ref="SF-B-BATH",
            material="galvanized", design_cfm=30),
    # The sauna supply crosses W-B-CW at x=1'-0 1/2", in its west clear stud bay and west
    # of D-B-FURN's header. It travels south on that lane, then turns east along the clear
    # southern band to REG-B-SUP3.
    #
    # ** THE LAST LEG DROPS BEFORE W-B-SA-W. ** At y=1'-8 1/2", the route drops 3 1/2" to
    # 7'-0" and then crosses W-B-SA-W between studs at y=1'-8 1/2". The duct top is 1" below
    # that wall's top plates. This keeps the 4" branch in the wall bay rather than through
    # either top plate; the low south-band step is clear of the other authored services.
    DuctRun(uid="VXGA0P0V72", tag="DU-B-ERV-R-SAUNA-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(5, 3), ft(30, 2)), pt(ft(5, 3), ft(30, 2)),
                  pt(ft(1, 0.5), ft(30, 2)), pt(ft(1, 0.5), inch(20.5)),
                  pt(ft(1, 0.5), inch(20.5)), pt(inch(199.75), inch(20.5))),
            elevations=(ft(7, 6), inch(87.5), inch(87.5), inch(87.5), ft(7), ft(7)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=12),
    # The bench hood's pull. It drops out of the ceiling chase to the hood face at 5'-6",
    # which is the vertical leg that makes it a capture hood rather than a ceiling diffuser.
    # It steps south to y=27'-0" before turning west so that its own drop and the plenum's
    # two 6" underside ports are not in each other's way, then runs the deepest of the four
    # corridors: under PR-B-KITCH-DRAIN, under PR-B-WC1-DRAIN's tail, and under the SH2 and
    # SINK2 drops that used to be three of its four reported pairs.
    DuctRun(uid="MTVYDDP43W", tag="DU-B-ERV-R-BENCH", system=DuctSystem.RETURN,
            path=(pt(ft(6, 6), ft(28, 2)), pt(ft(6, 6), ft(27)), pt(ft(6, 6), ft(27)),
                  pt(ft(2), ft(27)), pt(ft(2), ft(8, 6)), pt(ft(2), ft(8, 6))),
            elevations=(ft(7, 6), ft(7, 6), inch(81.5), inch(81.5), inch(81.5), ft(6, 2)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=6),
    # The basement bath's extract leaves the plenum's EAST end and drops 1 1/4" off its
    # collar, then south on x=8'-0" and east on y=24'-0" to a sidewall grille in W-B-STR3B
    # (REG-B-EXH1). At -20 11/16" it crosses OVER the GYM and PLAY lanes (3/4" each) and
    # under PR-B-SAUNA-VENT (1 7/16"), and passes W-B-STR3B in its 23'-4"..24'-8" bay.
    #
    # ** IT USED TO GO THROUGH THE STAIR (until 2026-09-22). ** Its old leg ran south under
    # the upper flight to (12', 24'-1 5/8") through `stringer-upper-0`, `tread-upper-003` and
    # W-B-STR3's ledger. The flight's own structure is now inside the volume a router refuses.
    DuctRun(uid="03883CKF0H", tag="DU-B-ERV-R-BATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(8), ft(28, 6)), pt(ft(8), ft(28, 6)),
                  pt(ft(8), ft(24)), pt(inch(119.875), ft(24))),
            elevations=(ft(7, 6), inch(88.75), inch(88.75), inch(88.75)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=20),
    # The low pickup is 4" off the floor on W-B-SA-W. The route now uses the west clear bay
    # in W-B-CW at x=1'-0 1/2", clear of D-B-FURN's header, then turns east at y=3'-4".
    # Both sauna radials share the west lane at separate tiers: this one is at 6'-10", 5 1/2"
    # below supply. At y=3'-4" it enters the centre of W-B-SA-W's 5 1/2" cavity and drops
    # between the studs to 4" AFF. The 2" shift to the register's y=3'-2" station stays
    # inside that stud bay. W-B-SA-W uses SAUNA_2X6 so the 4" section fits with 3/4" each
    # side; its hot-side liner face stays fixed.
    DuctRun(uid="1Y457X9DMH", tag="DU-B-ERV-R-SAUNA-EXH", system=DuctSystem.EXHAUST,
            path=(pt(ft(5, 3), ft(28, 2)), pt(ft(5, 3), ft(28)), pt(ft(5, 3), ft(28)),
                  pt(ft(1, 0.5), ft(28)), pt(ft(1, 0.5), inch(40)),
                  pt(inch(116.5625), inch(40)), pt(inch(116.5625), inch(40)),
                  pt(inch(116.5625), ft(3, 2)), pt(inch(122), ft(3, 2))),
            elevations=(ft(7, 6), ft(7, 6), inch(82), inch(82), inch(82), inch(82),
                        inch(4), inch(4), inch(4)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=20),
]
