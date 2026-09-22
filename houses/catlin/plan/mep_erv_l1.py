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
# THIS duct system costs and reads the curve at it: **0.350" w.g. worst path, 207 cfm
# delivered**, the worst path being DU-B-ERV-R-SAUNA-EXH on the EXTRACT side. The oracle is
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
# FO-S-STAIR (x 10'-3 3/8"..17'-8 5/8", y 26'-0 3/8"..35'-5 3/8") blocks every FS-S bay
# between those y values across the middle of the house; FO-A-STAIR (x 22'-5 3/8"..35'-5 3/8",
# y 5'-4"..8'-9 5/8"); FS-ATTIC's trimmer pack at y=5'-2 1/4"/5'-4" runs x 18'..35'-5 3/8".
#
# **One forced deviation from the port budget: REG-S-RET-BED3.** It was to be a level-2
# floor boot like BED1 and BED2. It cannot be: FO-S-STAIR blocks EVERY FS-S bay between
# y=26'-0 3/8" and y=35'-5 3/8" across x 10'-3 3/8"..17'-8 5/8", BED3 spans y 27'-36', and
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
    Equipment(uid="QGMYDXSMKH", tag="EQ-B-ERV-MAN-SUP", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(6, 6), ft(30, 6)), footprint=(inch(36), inch(8)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV-PLENUM-B-SUP",
              mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 2))),
    Equipment(uid="CRN5GT0ECP", tag="EQ-B-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(6, 6), ft(28, 6)), footprint=(inch(36), inch(8)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV-PLENUM-B-EXH",
              mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 2))),
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
#        * **y=29'-6" then x=17'-9", -20 7/16"** — the east chase: the belt between the two
#          plenums, then RM-B-STAIR's x 17'-6"..18'-0" strip, which is continuous from
#          y=36'-0" to y=10'-0" and is one of the two basement rooms whose ceiling the
#          owner leaves open.
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
    # THE GYM RADIAL TAKES THE EAST CHASE. Its register is at (19'-0", 13'-0") and the
    # straight line to it crosses the drain field; the belt at y=29'-6" and the x=17'-0"
    # lane miss it entirely and add four feet to a 4" duct carrying 18 cfm.
    # It drops 6" off its collar and stays there. Two things want that depth: PR-B-SAUNA-VENT
    # is at -16 7/16" where the belt crosses it at x=9'-0", and DU-B-ERV-R-PLAY shares the
    # x=17'-0" lane on the tier above for the four feet the two overlap. -25 7/16" leaves
    # 6'-10" of headroom under it in RM-B-STAIR, over the 6'-8" this house holds an exposed
    # service to.
    #
    # ** x=17'-0" AND NOT 17'-9", BECAUSE THE STRIP BESIDE THE STAIR IS THE POUR. **
    # W-B-CN / -CN2 / W-B-CS2 are one 12" cast wall on the x=18'-0" axis from the slab to
    # -13 7/16", so x 17'-6"..18'-6" is concrete for the whole depth of the house, and
    # RM-B-STAIR's ceiling polygon reaches over its west half. A lane at 17'-9" is inside
    # the pour with 5" of cover and `mep.run_in_slab` says so. 17'-0" leaves 4" between the
    # duct's east face and the concrete.
    #
    # ** IT RISES 6 1/8" AT x=17'-0" AND CROSSES `W-B-CS3` OVER `D-B-GYM`'s HEADER, NOT
    # THROUGH IT (2026-09-22). ** At -25 7/16" the east leg bored that header 4.00" — over
    # half the depth of a 2-2x8 carrying the gym door's whole tributary into two jacks, and
    # 7 7/16" from the north jack face. `W-B-CS3` is a 46" BEARING wall with a 36" opening
    # in it and has no clear bay at all, so there is no lane to move sideways into. What it
    # does have is the band ABOVE the header: the header tops out at -22.19" and the double
    # top plate starts at -16.44", which is 5 3/4" of open wall, and at y=13'-0" the nearest
    # cripples stand at y=12'-4 3/16" and y=13'-7 7/16" — 7.8" either side of a 4" duct.
    # Centred at -19 5/16" (90 1/8" over the slab) the duct leaves 7/8" of air to the header
    # top and 7/8" to the plate, and **cuts nothing at all**: no bore, no notch, no header.
    #
    # ** THIS IS NOT THE SHORT-CRIPPLE GAP AND THE DIFFERENCE IS THE WHOLE POINT. **
    # `notes/framing_bore_limits.md` §6a: a 4" hole through a 6 9/16" cripple leaves two
    # 1.28" slivers, and `stud_bore` now reads such a hole UNKNOWN (a member shorter than
    # two depths is a block, not a stud). That is a hole DRILLED IN a cripple. This duct passes
    # BETWEEN two whole cripples in air the framing never occupied — the ordinary
    # over-the-header detail — and the members it clears are graded, not exempted.
    #
    # The rise costs two bends on the supply side, which is not the governing one, and it
    # buys 6" of headroom in RM-B-GYM (`exposed_services`) rather than spending any.
    # The cast sleeve through `W-B-CS2`'s 12" pour was the other candidate and is NOT
    # taken: a crossing of air cuts nothing, where a sleeve is a pre-pour commitment
    # (`mep.sleeve_coverage` grades duct sleeves since 2026-09-22 — SP-B-CN-ERV-PLAY).
    DuctRun(uid="CND5TE40W0", tag="DU-B-ERV-R-GYM", system=DuctSystem.SUPPLY,
            path=(pt(ft(7, 3), ft(30, 2)), pt(ft(7, 3), ft(29, 6)),
                  pt(ft(7, 3), ft(29, 6)), pt(ft(17), ft(29, 6)),
                  pt(ft(17), ft(13)), pt(ft(17), ft(13)), pt(ft(19), ft(13))),
            elevations=(ft(7, 6), ft(7, 6), inch(84), inch(84), inch(84),
                        inch(90.125), inch(90.125)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=18),
    # The play room's radial leaves the plenum's EAST END, 18" nearer its own register than
    # the centre it used to start from and out of the other two supply radials' way at
    # birth. It now turns south at x=17'-0" — the same lane DU-B-ERV-R-GYM rides, 4 1/2"
    # above it — and enters RM-B-PLAY-N only on its last leg.
    #
    # ** ENTERING ONLY ON THE LAST LEG IS THE POINT, AND IT IS WORTH TWO FITTINGS. ** The
    # straight east run crossed the room boundary at x=18'-6" (W-B-CN's east face) and then
    # ran half a foot inside RM-B-PLAY-N before turning — and half a foot is exactly
    # `min_ceiling_exposure_ft`, so whether `mep.run_in_finished_volume` reported it came
    # down to the last bit of a float. The room has no ceiling cavity to hide it in either:
    # SL-M-DECK's soffit is 14 3/8" of solid concrete at -13 7/16" and the finished plane is
    # 5/8" under that, so there is nothing to lift into. A run that reaches its register on
    # its terminal leg is the connection rather than a transit, which is a fact about the
    # layout and not a threshold.
    DuctRun(uid="DMEQ946YAX", tag="DU-B-ERV-R-PLAY", system=DuctSystem.SUPPLY,
            path=(pt(ft(8), ft(30, 6)), pt(ft(17), ft(30, 6)), pt(ft(17), ft(26)),
                  pt(ft(19), ft(26))),
            start_elevation=ft(7, 6), end_elevation=ft(7, 6),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=30),
    # The sauna's supply comes west and runs south to the sauna along the west side of the
    # basement, then east along y=1'-8 1/2" — the southernmost foot of the house, where
    # nothing else is drawn at all.
    #
    # ** IT IS AT x=1'-8" AND NOT x=3'-3", AND THE REASON IS ONE MEMBER: W-B-CW's HEADER. **
    # The x=3'-3" corridor crosses W-B-CW at y=18'-0" dead on `D-B-FURN`'s west jack face,
    # 1/4" above the header's top — so this duct took a 1 3/4" NOTCH off the top of the one
    # member carrying that opening's whole tributary load into two jacks. No published chart
    # reaches it: Weyerhaeuser TJ-9000's ALLOWABLE HOLES page is ROUND HOLES ONLY, and a
    # notch is not a round hole at any depth (notes/framing_bore_limits.md §8).
    #
    # x=1'-0 1/2" crosses the same wall in its WEST clear bay, x 9 1/2"..15 1/4" between
    # `stud-000` and `stud-001`. The duct spans 10 1/2"..14 1/2" there, 1" clear of one stud
    # and 3/4" of the other, and NOTHING IS BORED, NOTCHED OR HEADED.
    #
    # ** WEST OF x=1'-5 1/2" IS NOT A PREFERENCE EITHER: IT IS `PR-B-SINK2-DRAIN`. ** That
    # drain rakes east-to-west across every north-south lane in this half of the basement,
    # so how much air a lane has is a function of x. Measured clearance at this tier
    # (-21.94"), lane by lane: 2.44" at x=1'-0 1/2", 1.32" at x=1'-3", 0.20" at x=1'-5 1/2",
    # and NEGATIVE from x=1'-6" east — which is what a first attempt at x=1'-8" found the
    # hard way, 0.5" inside SINK2. The wide bay to the east is the exhaust radial's, one
    # tier down, where the same drain has risen out of the way.
    # The detour costs about 3 1/2 ft of 4" duct, worth well under 0.001 in. w.g. on the
    # supply side, which is not the governing one.
    DuctRun(uid="VXGA0P0V72", tag="DU-B-ERV-R-SAUNA-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(5, 3), ft(30, 2)), pt(ft(5, 3), ft(30, 2)),
                  pt(ft(1, 0.5), ft(30, 2)), pt(ft(1, 0.5), ft(1, 8.5)),
                  pt(inch(199.75), ft(1, 8.5)), pt(inch(199.75), ft(1, 8.5))),
            elevations=(ft(7, 6), inch(87.5), inch(87.5), inch(87.5), inch(87.5), ft(7)),
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
    # The basement bath's extract leaves the plenum's EAST end, which is the one exit from
    # this box that no 6" port and no vent stands in, and drops 2" off the collar so it
    # passes under PR-B-SAUNA-VENT at x=9'-0" where the vent is still at -16 5/8" on its way
    # north.
    #
    # ** IT STEPS SOUTH TO y=27'-9" BEFORE IT GOES EAST, AND THAT STEP IS THE WHOLE BEARING
    # WALL. ** W-B-STR3 is the basement's centre BEARING partition and R602.6 allows a bore
    # of 40% of 5 1/2" in one of its studs — 2.20" against this duct's 4.00". On the plenum's
    # own y=28'-6" line the duct landed on king-0-l0 at y=28'-6 1/4" and stud-001 at
    # y=28'-8", which is two bearing studs cut for one branch. y=27'-9" is the middle of the
    # cripple space over the door head: 9 1/4" clear to the king on one side and 9" to
    # cripple-head-0-01 at y=27'-0" on the other, and the header itself is 8 3/4" below the
    # duct's underside. **Nothing is bored, nothing is headed, and the wall is untouched** —
    # which is the answer this campaign wanted and a `RoughOpening` would only have been the
    # second-best version of.
    DuctRun(uid="03883CKF0H", tag="DU-B-ERV-R-BATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(8), ft(28, 6)), pt(ft(8), ft(28, 6)),
                  pt(ft(8), ft(27, 9)), pt(ft(12), ft(27, 9)),
                  pt(ft(12), inch(289.625))),
            elevations=(ft(7, 6), inch(88), inch(88), inch(88), inch(88)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=20),
    # The sauna's low pickup is 4" off the floor on the WEST liner (the south face went to
    # EQ-B-SAUNA-HTR when the room rotated), so this radial runs the length of the house in
    # the ceiling chase and then drops seven feet down the wall. The drop is drawn — a
    # repeated plan point at two elevations — which it could not be before `DuctRun` carried
    # elevations. The drop moved 3'-10" east with the west liner on 2026-09-05: x=64" is
    # workshop floor now, not sauna wall.
    #
    # ** IT STEPS 2" SOUTH OF ITS COLLAR BEFORE IT DROPS, AND THAT 2" IS LOAD-BEARING. **
    # DU-ERV-RISER-EXH turns up into the plenum's underside on the y=28'-6" line; a drop on
    # the collar's own y=28'-2" is 4" from it and a 6" riser and a 4" radial need 5". The
    # step also puts the crossing of PR-B-KITCH-DRAIN at y=28'-0" rather than y=28'-2",
    # which is worth half an inch of clearance because the drain falls 8.8" per foot here.
    # The corridor tier is the plenum's own 7'-2": half an inch below is
    # PR-M-S-BATH1-DRAIN's rake at y=17'-0" and half an inch above is the drain.
    #
    # ** IT IS AT x=2'-4" AND NOT x=3'-9", FOR THE SAME MEMBER THAT MOVED THE SUPPLY. **
    # The x=3'-9" corridor crossed `W-B-CW` at x=45", inside `D-B-FURN`'s rough opening and
    # 1.25" under the header's top, taking a 3 1/4" NOTCH out of a 7 1/4" member — nearly
    # half its depth, off the compression face, over a door. TJ-9000's ALLOWABLE HOLES page
    # publishes round holes only and no chart on the market notches a header
    # (notes/framing_bore_limits.md §8), so the lane moves rather than the chart being
    # stretched to cover it.
    # ** IT STILL NOTCHES `W-B-CW`'s HEADER 3 1/4" AND THAT IS A RECORDED REFUSAL, NOT AN
    # OVERSIGHT (2026-09-22). ** At x=3'-9" this duct crosses the wall inside `D-B-FURN`'s
    # rough opening and 1 1/4" under the header's top face, taking 3 1/4" out of a 7 1/4"
    # member — 45% of its depth, off the compression face, over a door. TJ-9000's ALLOWABLE
    # HOLES page is round holes only, so no published chart reaches it
    # (notes/framing_bore_limits.md §8), and the supply radial solved the same problem by
    # moving. THIS ONE HAS NOWHERE TO MOVE TO, measured rather than assumed:
    #
    #   * `W-B-CW` has exactly two bays a 4" duct fits: x 9 1/2"..15 1/4" and
    #     x 16 3/4"..31 1/4". The supply took the west one; only one 4" duct fits it.
    #   * In the wide bay this duct's own tier (-23.44") is inside `PR-B-SINK2-DRAIN`'s
    #     rake. Measured clearance: 3.78" at x=1'-0 1/2", 0.43" at x=1'-8", 0.00" at
    #     x=1'-9", negative east of that; x=2'-4" (tried) lands 1.6"-3.2" inside SINK2, SH2
    #     and WC2 at once, and x=1'-8" straight lands inside SINK2 at y=15'-4".
    #   * Jogging east at any station between y=16'-2" and the wall crosses
    #     `PR-B-WC2-DRAIN`'s x=2'-6" lane at the same elevation — every half-inch of it.
    #   * Dropping under the drains in the wide bay runs into `DU-B-ERV-R-BENCH` at
    #     x=2'-0"/-27.94"; rising over them puts the duct in the deck.
    #   * The cripple zone over the header would pass this engine and must not be used:
    #     `stud_bore` grades a hole against a stud's DEPTH and says nothing about its
    #     LENGTH, so a 4" hole through a 6 9/16" cripple reads legal and is two slivers
    #     (notes/framing_bore_limits.md §6a).
    #
    # So the choice is a run-to-run interpenetration or a notched header, and neither is the
    # engine's to make. `haus route --counterfactual` lifts no movable blocker that opens a
    # lane: the blockers are a gravity drain network and a header. **The open question is
    # the owner's: a designed header over D-B-FURN, or the sauna's extract moving.**
    DuctRun(uid="1Y457X9DMH", tag="DU-B-ERV-R-SAUNA-EXH", system=DuctSystem.EXHAUST,
            path=(pt(ft(5, 3), ft(28, 2)), pt(ft(5, 3), ft(28)), pt(ft(5, 3), ft(28)),
                  pt(ft(3, 9), ft(28)), pt(ft(3, 9), ft(3, 2)),
                  pt(ft(9, 2), ft(3, 2)), pt(ft(9, 2), ft(3, 2))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 2), ft(7, 2), ft(7, 2), ft(7, 2),
                        inch(4)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=20),
]
