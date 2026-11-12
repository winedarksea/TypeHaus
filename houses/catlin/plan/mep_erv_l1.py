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
    # y=27'-2 1/2" since 2026-11-11 (14 1/2" south): the return port's 13" leg under
    # DU-ERV-OA's row rises into its underside, and OA's row takes the old y=28'-5" slot.
    # The box is clear of PR-B-SAUNA-VENT's y=28'-8" leg now; it kept its 7'-1 3/8".
    Equipment(uid="CRN5GT0ECP", tag="EQ-B-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(6, 6), ft(27, 2.5)), footprint=(inch(36), inch(8)),
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
#          of air (that rake is gone: the drain drops straight on x=5'-0" since 2026-10-08).
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
# is at -20" and nothing passes under it at all inside the ceiling. That is why SAUNA-EXH
# still goes down the WEST corridor and east along y=3'-4", south of the vent's corner; the
# sauna supply (2026-11-11) crosses the vent's y=10'-6" run OVER it instead.
#
# REG-B-SUP2's radial is the short one on purpose: it stops in the play room's west wall,
# about nine feet short of the old (27', 27') position, and throws away from FURN-B-PLAY-TV
# on the east wall.
DUCTS_ERV_BASEMENT = [
    # ** THE MACHINE'S OWN TWO TRUNKS (2026-11-11, notes/erv_static_budget.md §10.22). **
    # Both 6", the machine's full 210 cfm, off the west half of its top. Each kit flex bends
    # at 70" (2" straight, R = 6") under DU-ERV-EA's and DU-ERV-OA's rows, runs 13" level
    # and turns up into its plenum: the supply north into EQ-B-ERV-MAN-SUP's underside, the
    # return south into EQ-B-ERV-MAN-EXH's. 13" is the flex's 6.6" out plus the 6" elbow.
    DuctRun(uid="225MZ1YDWB", tag="DU-B-ERV-SUP-TRUNK", system=DuctSystem.SUPPLY,
            path=(pt(inch(73.8125), inch(352.96875)), pt(inch(73.8125), inch(352.96875)),
                  pt(inch(73.8125), inch(365.96875)), pt(inch(73.8125), inch(365.96875))),
            elevations=(inch(62), inch(70), inch(70), ft(7, 2)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_SUP_TRUNK, adjustable_elbows=(2,)),
    DuctRun(uid="6BTCWW2S1V", tag="DU-B-ERV-RET-TRUNK", system=DuctSystem.RETURN,
            path=(pt(inch(75.5625), inch(339.59375)), pt(inch(75.5625), inch(339.59375)),
                  pt(inch(75.5625), inch(326.59375)), pt(inch(75.5625), inch(326.59375))),
            elevations=(inch(62), inch(70), inch(70), ft(7, 1.375)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_RET_TRUNK, adjustable_elbows=(2,)),
    # ** NEITHER RADIAL CROSSES ST-B2M ANY MORE (2026-09-22). ** Both used to ride the
    # y=29'-6"/30'-6" belt east over the stair, 1" (GYM) and 15 5/8" (PLAY) into the 6'-8"
    # headroom over the upper flight's nosings — `code.R311_7_2_stair_headroom` counts runs
    # now. The x=17'-0" "east chase" was only continuous by walking over the lower flight.
    #
    # Its collar moved to x=6'-10" (2026-11-01), clear of the supply trunk on Broan's port 2;
    # GYM and PLAY now leave the ceiling layer on 30° ramps, not 6" drops between two 90s.
    # THE GYM RADIAL GOES THROUGH THE WORKSHOP. South on x=9'-0", directly under
    # PR-B-SAUNA-VENT, the bath vent, and the HW-BATH and LSINK legs it crosses, at 84" past
    # the bath extract and laundry sink drain, then a 45° ramp to 90 1/8" by y=18'-2 3/8".
    # Through W-B-CW3 in its 8'-1"..9'-5" stud bay, 1 1/2" under the plates.
    # ** SOUTH OF EQ-B-WH SINCE 2026-11-09. ** A 45° offset takes it 4" east, off the vent's
    # x=9'-0" line, then south on x=9'-4" over PR-M-S-SUITE-DRAIN (1/2" clear) to y=13'-4",
    # and straight east over D-B-SHOP's flat head (5" over the head, 1 5/8" under the plates)
    # and the hall. The NE corner stays free for the tank's ducts and header; about the same
    # length as the old y=17'-4 3/4" leg.
    # ** x=17'-0" STAYS. ** W-B-CN/-CN2/W-B-CS2 are framed now, so the lane could move east,
    # but it already clears the hall's east face and nothing wants the move.
    #
    # ** IT RISES TO 90 1/8" AT x=17'-0" AND CROSSES `W-B-CS3` OVER `D-B-GYM`'s HEADER. ** The
    # header tops out at -22.19" and the double top plate starts at -16.44"; centred at
    # -19 5/16" the duct passes between the cripples at y=12'-4 3/16" and 13'-7 7/16" with
    # 7/8" to header and plate, and cuts nothing (`notes/framing_bore_limits.md` §6a is a
    # hole drilled IN a cripple; this is air between two). ** IT ENDS IN THAT BAY (2026-11-10):
    # REG-B-SUP1 is a sidewall valve on the gym face, centred on the duct. ** Nothing of it is
    # exposed in the gym any more.
    DuctRun(uid="CND5TE40W0", tag="DU-B-ERV-R-GYM", system=DuctSystem.SUPPLY,
            # Stock turns only: a 45 degree ramp and a 45 degree offset.
            path=(pt(ft(6, 10), ft(30, 2)), pt(ft(6, 10), ft(29, 8)), pt(inch(92.375), ft(29, 8)),
                  pt(inch(98.375), ft(29, 8)), pt(ft(9), ft(29, 8)),
                  pt(ft(9), inch(224.5)), pt(ft(9), inch(218.375)), pt(ft(9), inch(212)),
                  pt(inch(112), inch(208)),
                  pt(inch(112), ft(13, 4)), pt(ft(18), ft(13, 4))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 6), inch(84), inch(84), inch(84), inch(90.125),
                        inch(90.125), inch(90.125), inch(90.125), inch(90.125)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_R_GYM),
    # THE PLAY RADIAL GOES THROUGH SF-B-BATH. From the plenum's east end it drops to -25 7/16"
    # on x=9'-6" (east of the sauna vent, under everything), rises to 91 1/4" at
    # y=19'-7 1/4" and crosses W-B-STR2 in its 19'-4"..20'-8" bay under the top plate
    # (-15 5/8"). It eases down 1/2" on the eastbound leg to clear PR-B-LSINK-DRAIN's riser,
    # then jogs south over PR-B-BATH-VENT at x=12'-3" (the vent dropped 1 1/2" for it) and
    # leaves through W-B-BA-E at y=18'-6 3/4" — the one gap in that staggered wall south of
    # the bath's three risers (y 19'-3"..19'-10") wide enough for a 4" duct. Then 1'-5"
    # north up the hall at x=16'-9" and east at y=20'-6" into W-B-CN2's 240"..256" stud bay,
    # where it ends on REG-B-SUP2, a sidewall valve on the theater face (2026-11-10). The old
    # 45 onto 101 1/4" and the box over the plate are gone with the ceiling valve.
    DuctRun(uid="DMEQ946YAX", tag="DU-B-ERV-R-PLAY", system=DuctSystem.SUPPLY,
            path=(pt(ft(8), ft(30, 6)), pt(ft(9, 6), ft(30, 6)), pt(ft(9, 6), inch(355.625)),
                  pt(ft(9, 6), ft(19, 7.25)), pt(ft(9, 6), ft(19, 7.25)),
                  pt(ft(12, 3), ft(19, 7.25)), pt(ft(12, 3), ft(18, 6.75)),
                  pt(ft(16, 9), ft(18, 6.75)), pt(ft(16, 9), ft(20, 6)),
                  pt(ft(18), ft(20, 6))),
            elevations=(ft(7, 6), ft(7, 6), inch(84), inch(84), inch(91.25), inch(90.75),
                        inch(90.75), inch(90.75), inch(90.75), inch(90.75)),
            diameter=inch(4), routing=DuctRouting.SOFFIT, soffit_ref="SF-B-BATH",
            material="galvanized", design_cfm=DU_B_ERV_R_PLAY),
    # ** THE SAUNA SUPPLY IS A BRANCH OFF GYM'S y=13'-4" LEG (2026-11-11). ** It used to leave its
    # own plenum collar and go 49 1/2 ft: west, south down x=1'-7" and east along the south band.
    # Now it taps GYM at x=11'-2" (GYM carries its 20 cfm, plan/erv_balance.py) and runs 3 ft
    # south: a 45 ramp up to 94 3/4" over PR-B-SAUNA-VENT's y=10'-6" run (top 92 1/4"), over
    # W-B-SA-N's plates and the hung ceiling's foil, then 10 3/4" down to REG-B-SUP3 on the
    # 7'-0" face over the north end of the upper bench. The top stands 3/4" under the joists
    # (-11 7/8"); PR-B-SAUNA-FD-VENT (x=11'-11") is 8 1/2" east. EQ-B-ERV-MAN-SUP's collar-sauna
    # is spare: the shop leaves it uncut (or blanks it). Harvia wants the inlet near the heater;
    # the owner accepted the departure for the 41 ft it saves.
    DuctRun(uid="VXGA0P0V72", tag="DU-B-ERV-R-SAUNA-SUP", system=DuctSystem.SUPPLY,
            path=(pt(inch(134.4), ft(13, 4)), pt(inch(134.4), inch(156)),
                  pt(inch(134.4), inch(151.375)), pt(inch(134.4), inch(109.2)),
                  pt(inch(134.4), inch(109.2))),
            elevations=(inch(90.125), inch(90.125), inch(94.75), inch(94.75), ft(7)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_R_SAUNA_SUP),
    # ** THE BENCH HOOD IS A BRANCH OFF SAUNA-EXH'S x=1'-7" LEG (2026-11-11). ** It used to leave
    # its own plenum collar and run 25 ft down x=2'-0" beside it. It now takes off SAUNA-EXH's SIDE
    # at y=8'-6" (82 1/4"; SAUNA-EXH carries its 6 cfm), east 6" (the hood moved 1" east), then
    # drops to the hood at 5'-6". Side, never the bottom: the sauna's duct sweats and a bottom
    # take-off would drain it into the hood. Both are extract (RETURN joins EXHAUST,
    # `mep_envelopes.systems_join`). Closing the sauna hatches swings flow to the hood, so its
    # 4" balancing damper rides in the hood's collar (REG-T-ERV-BENCH-HOOD's part, billed).
    DuctRun(uid="MTVYDDP43W", tag="DU-B-ERV-R-BENCH", system=DuctSystem.RETURN,
            path=(pt(ft(1, 7), ft(8, 6)), pt(ft(2, 1), ft(8, 6)), pt(ft(2, 1), ft(8, 6))),
            elevations=(inch(82.25), inch(82.25), ft(6, 2)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_R_BENCH),
    # The basement bath's extract leaves the plenum's EAST end straight off its collar (6",
    # one elbow's take-off; it dropped 1 1/4" there until 2026-11-01), then south on x=8'-6"
    # and east on y=24'-0" to a sidewall grille in W-B-STR3B (REG-B-EXH1). At -19 7/16" it
    # crosses 2" OVER the GYM and PLAY lanes and 7/8" under PR-B-SAUNA-VENT, and passes
    # W-B-STR3B in its 23'-4"..24'-8" bay.
    #
    # ** IT USED TO GO THROUGH THE STAIR (until 2026-09-22). ** Its old leg ran south under
    # the upper flight to (12', 24'-1 5/8") through `stringer-upper-0`, `tread-upper-003` and
    # W-B-STR3's ledger. The flight's own structure is now inside the volume a router refuses.
    DuctRun(uid="03883CKF0H", tag="DU-B-ERV-R-BATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(8), ft(27, 2.5)), pt(ft(8, 6), ft(27, 2.5)),
                  pt(ft(8, 6), ft(24)), pt(inch(119.875), ft(24))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 6), ft(7, 6)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_R_BATH),
    # It leaves its collar 4" south and steps down on a 45° ramp to 82 1/4" before it turns
    # west, so it passes under PR-M-S-BATH1-DRAIN's x=5'-0" fall (2026-11-11, with the box). Its
    # collar is at x=5'-10", between that stack and PR-B-HW-SBATH's riser at x=5'-6 1/2".
    # The low pickup is 4" off the floor on W-B-SA-W. The route uses W-B-CW's x=1'-7" bay
    # (out of the panels' 110.26(E) space since 2026-10-31), clear of D-B-FURN's header,
    # then turns east at y=3'-4". (Until 2026-11-11 the sauna supply shared the lane, 1/4" over
    # this at 86 1/2".) At y=3'-4" it enters the centre of W-B-SA-W's 5 1/2" cavity and drops
    # between the studs to 4" AFF. The 2" shift to the register's y=3'-2" station stays
    # inside that stud bay. W-B-SA-W uses SAUNA_2X6 so the 4" section fits, 1/4" off
    # the west stud face and 1 1/4" off the east; its hot-side liner face stays fixed.
    DuctRun(uid="1Y457X9DMH", tag="DU-B-ERV-R-SAUNA-EXH", system=DuctSystem.EXHAUST,
            # (2026-11-07) The drop stands at x=116" (was 116 9/16"): the last stub to the
            # register is 6", the take-off of the 90 above it (was 5 7/16").
            path=(pt(ft(5, 10), inch(322.5)), pt(ft(5, 10), inch(318.5)), pt(ft(5, 10), inch(310.75)),
                  pt(ft(1, 7), inch(310.75)), pt(ft(1, 7), inch(40)),
                  pt(inch(116), inch(40)), pt(inch(116), inch(40)),
                  pt(inch(122), inch(40))),
            elevations=(ft(7, 6), ft(7, 6), inch(82.25), inch(82.25), inch(82.25), inch(82.25),
                        inch(4), inch(4)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_B_ERV_R_SAUNA_EXH),
]
