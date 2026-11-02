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
    # y=28'-5" since 2026-10-31, 1" south, so DU-ERV-OA's port leg passes beside it at
    # 84 1/2" (over the panels' 78" working space) instead of under it.
    Equipment(uid="CRN5GT0ECP", tag="EQ-B-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(6, 6), ft(28, 5)), footprint=(inch(36), inch(8)),
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
# is at -20" and nothing passes under it at all inside the ceiling. That is why the two
# sauna radials go down the WEST corridors and come east along y=1'-8 1/2" and y=3'-2",
# south of the vent's corner, where the floor is clear the full width of the house.
#
# REG-B-SUP2's radial is the short one on purpose: it stops just inside the play room's west
# edge, about eight feet short of the old (27', 27') position, and throws away from
# FURN-B-PLAY-TV on the east wall. Its last leg rides FS-M-NE's truss space (2026-11-01).
DUCTS_ERV_BASEMENT = [
    # ** THE MACHINE'S OWN TWO TRUNKS. ** Both are 6", the machine's full 210 cfm, and both
    # leave its top.
    #
    # (2026-10-17) The ERV sits at x=6'-8 5/8", so both trunks leave its top inside the case.
    # The supply rises straight off Broan's port 2 into EQ-B-ERV-MAN-SUP's underside
    # (2026-11-01; it stood 4 5/8" off the collar).
    DuctRun(uid="225MZ1YDWB", tag="DU-B-ERV-SUP-TRUNK", system=DuctSystem.SUPPLY,
            path=(pt(inch(88.65625), inch(364.625)), pt(inch(88.65625), inch(364.625))),
            elevations=(inch(75.6), ft(7, 2)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=210),
    # (2026-10-17) Off the case's north-east top, under the collars. Nothing west of x=6'-0".
    DuctRun(uid="6BTCWW2S1V", tag="DU-B-ERV-RET-TRUNK", system=DuctSystem.RETURN,
            path=(pt(inch(86), ft(29, 2)), pt(ft(7, 4.5), ft(29, 2)),
                  pt(ft(7, 4.5), ft(28, 5)), pt(ft(7, 4.5), ft(28, 5))),
            elevations=(inch(75.6), inch(75.6), inch(75.6), ft(7, 2)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=210),
    # ** NEITHER RADIAL CROSSES ST-B2M ANY MORE (2026-09-22). ** Both used to ride the
    # y=29'-6"/30'-6" belt east over the stair, 1" (GYM) and 15 5/8" (PLAY) into the 6'-8"
    # headroom over the upper flight's nosings — `code.R311_7_2_stair_headroom` counts runs
    # now. The x=17'-0" "east chase" was only continuous by walking over the lower flight.
    #
    # Its collar moved to x=6'-10" (2026-11-01), clear of the supply trunk on Broan's port 2;
    # GYM and PLAY now leave the ceiling layer on 30° ramps, not 6" drops between two 90s.
    # THE GYM RADIAL GOES THROUGH THE WORKSHOP. South on x=9'-0", directly under
    # PR-B-SAUNA-VENT, the bath vent, and the HW-BATH and LSINK legs it crosses; it stays at
    # 84" past the bath extract and laundry sink drain, then rises to 88 1/2" from
    # y=18'-8" to 17'-4 3/4". Through W-B-CW3 in its 8'-1"..9'-5" stud bay, over the 2x8
    # backing (top 6'-7 1/4"); east on y=17'-4 3/4", 2 1/4" clear of PR-M-S-SUITE-DRAIN's
    # riser, through W-B-HALL-W's 16'-8"..18'-0" bay; then the hall's x=17'-0" lane south
    # of the stair to y=13'-0" as before. The east leg falls 89" -> 88 1/2" (2026-10-29, was level
    # at 88 1/2"), so its lower face clears D-B-BATH's flat head (84 7/8"; 86 3/8" until the
    # Eclisse kit dropped its track nailer, 2026-10-29).
    #
    # ** x=17'-0" STAYS (2026-11-01). ** The strip beside the stair was a 12" pour (x 17'-6"..
    # 18'-6") and 17'-9" would have been inside it; W-B-CN/-CN2/W-B-CS2 are framed now, with
    # the stair face furred to x=17'-6", so the lane could move east, but 4" of air to the
    # furring is the clearance the hall already has and nothing wants the lane.
    #
    # ** IT RISES 6 1/8" AT x=17'-0" AND CROSSES `W-B-CS3` OVER `D-B-GYM`'s HEADER. ** The
    # header tops out at -22.19" and the double top plate starts at -16.44"; centred at
    # -19 5/16" the duct passes between the cripples at y=12'-4 3/16" and 13'-7 7/16" with
    # 7/8" to header and plate, and cuts nothing. At y=13'-4" since 2026-10-31: REG-B-SUP1's
    # valve collar has to stand in the FS-M-EAST bay north of the y=13'-0" joist, and 13'-4"
    # is the one line clearing both the joist (3/4") and the north cripple (11/16") (`notes/framing_bore_limits.md` §6a is a
    # hole drilled IN a cripple; this is air between two). At y=13'-4" it is south of
    # `W-B-CS2` (y >= 13'-10"), so it crosses no wall on the x=18' line, and it runs on
    # exposed in the gym (`RM-B-GYM.exposed_services`) to the register.
    DuctRun(uid="CND5TE40W0", tag="DU-B-ERV-R-GYM", system=DuctSystem.SUPPLY,
            path=(pt(ft(6, 10), ft(30, 2)), pt(ft(6, 10), ft(29, 8)),
                  pt(inch(92.375), ft(29, 8)), pt(ft(9), ft(29, 8)),
                  pt(ft(9), ft(18, 8)), pt(ft(9), ft(17, 4.75)),
                  pt(ft(17), ft(17, 4.75)),
                  pt(ft(17), ft(13, 4)), pt(ft(17), ft(13, 4)), pt(ft(19), ft(13, 4))),
            elevations=(ft(7, 6), ft(7, 6), inch(84), inch(84), inch(84), inch(89),
                        inch(88.5), inch(84), inch(90.125), inch(90.125)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=18),
    # THE PLAY RADIAL GOES THROUGH SF-B-BATH. From the plenum's east end it drops to -25 7/16"
    # on x=9'-6" (east of the sauna vent, under everything), rises to 91 1/4" at
    # y=19'-7 1/4" and crosses W-B-STR2 in its 19'-4"..20'-8" bay under the top plate
    # (-15 5/8"). It eases down 1/2" on the eastbound leg to clear PR-B-LSINK-DRAIN's riser,
    # then jogs south over PR-B-BATH-VENT at x=12'-3" (the vent dropped 1 1/2" for it) and
    # leaves through W-B-BA-E at y=18'-6 3/4" — the one gap in that staggered wall south of
    # the bath's three risers (y 19'-3"..19'-10") wide enough for a 4" duct. Then 1'-5"
    # north up the hall at x=16'-9" and east through W-B-CN2 at y=20'-0"
    # into REG-B-SUP2 on its last leg. ** SINCE 2026-11-01 (decision #112) IT NO LONGER
    # CROSSES THE x=18' LINE THROUGH A SLEEVE. ** W-B-CN2 is a framed 2x6 bearing wall (a 4"
    # bore is 4.00" against R602.6's 2.20"), so the duct turns north up the hall at x=16'-9"
    # to y=20'-6" (the 241 3/4".. 250 1/4" truss bay and a FS-M-WEST joist bay), ramps at
    # 45 degrees onto 101 1/4" before the wall, and crosses over its plate through the 2x6 box
    # the resolver frames in the bearing blocking, in the cavity (99 1/16".. 107 15/16" window),
    # to the register. It turned east at y=25'-0" until 2026-09-23; 5' less hall duct.
    DuctRun(uid="DMEQ946YAX", tag="DU-B-ERV-R-PLAY", system=DuctSystem.SUPPLY,
            path=(pt(ft(8), ft(30, 6)), pt(ft(9, 6), ft(30, 6)), pt(ft(9, 6), inch(355.625)),
                  pt(ft(9, 6), ft(19, 7.25)), pt(ft(9, 6), ft(19, 7.25)),
                  pt(ft(12, 3), ft(19, 7.25)), pt(ft(12, 3), ft(18, 6.75)),
                  pt(ft(16, 9), ft(18, 6.75)), pt(ft(16, 9), ft(20, 6)),
                  pt(inch(211.5), ft(20, 6)), pt(ft(19), ft(20, 6))),
            elevations=(ft(7, 6), ft(7, 6), inch(84), inch(84), inch(91.25), inch(90.75),
                        inch(90.75), inch(90.75), inch(90.75), inch(101.25), inch(101.25)),
            diameter=inch(4), routing=DuctRouting.SOFFIT, soffit_ref="SF-B-BATH",
            material="galvanized", design_cfm=30),
    # The sauna supply crosses W-B-CW at x=1'-7", in its 1'-4 3/4"..2'-7 1/4" stud bay and
    # west of D-B-FURN's header. It travels south on that lane, then turns east along the
    # clear southern band to REG-B-SUP3.
    #
    # ** THE LAST LEG RIDES THE SAUNA'S SERVICE CAVITY (2026-11-01). ** At y=1'-8 1/2" it
    # rises 6" to 7'-8 1/2", over W-B-SA-W's top plates (+90") and above the hung ceiling's
    # foil (+87 5/16"), runs east in the cavity, and drops 8 1/2" to REG-B-SUP3 on the 7'-0"
    # face. At 7'-0" it ran through the shiplap, furring and foil, inside the sauna's
    # vapour layer.
    #
    # ** x=1'-7" SINCE 2026-10-31, OUT OF THE PANELS' NEC 110.26(E) SPACE. ** At 1'-0 1/2"
    # both sauna radials stood 1 1/2" over the three 4"-deep enclosures on W-B-W1 (x <= 12");
    # 1'-7" is the next W-B-CW bay. West at y=30'-2 1/2": 89" under CD-B-GARAGE and
    # PR-B-SAUNA-VENT, 92 1/2" over DU-ERV-OA's wrap (top 90 1/2"), 87 1/2" over
    # DU-ERV-RISER-EXH, then 86 1/2" down the lane to clear PR-B-SINK2-DRAIN's rake.
    DuctRun(uid="VXGA0P0V72", tag="DU-B-ERV-R-SAUNA-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(5, 3), inch(362.5)), pt(ft(5, 3), inch(362.5)),
                  pt(inch(48), inch(362.5)), pt(inch(48), inch(362.5)),
                  pt(inch(32), inch(362.5)), pt(inch(32), inch(362.5)),
                  pt(ft(1, 7), inch(362.5)), pt(ft(1, 7), inch(362.5)),
                  pt(ft(1, 7), inch(20.5)),
                  pt(ft(1, 7), inch(20.5)), pt(inch(199.75), inch(20.5)),
                  pt(inch(199.75), inch(20.5))),
            elevations=(ft(7, 6), inch(89), inch(89), inch(92.5), inch(92.5), inch(87.5),
                        inch(87.5), inch(86.5), inch(86.5), inch(92.5), inch(92.5), ft(7)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=12),
    # The bench hood's pull. It drops out of the ceiling chase to the hood face at 5'-6",
    # which is the vertical leg that makes it a capture hood rather than a ceiling diffuser.
    # It steps south to y=27'-0" before turning west so that its own drop and the plenum's
    # two 6" underside ports are not in each other's way, then runs the deepest of the four
    # corridors: under PR-B-KITCH-DRAIN, under PR-B-WC1-DRAIN's tail, and under the SH2 and
    # SINK2 drops that used to be three of its four reported pairs. The step down is a 45°
    # ramp (2026-11-01): a 7 1/2" drop between two 90s is shorter than their take-offs.
    DuctRun(uid="MTVYDDP43W", tag="DU-B-ERV-R-BENCH", system=DuctSystem.RETURN,
            path=(pt(ft(6, 6), ft(28, 1)), pt(ft(6, 6), inch(331.5)), pt(ft(6, 6), ft(27)),
                  pt(ft(2), ft(27)), pt(ft(2), ft(8, 6)), pt(ft(2), ft(8, 6))),
            elevations=(ft(7, 6), ft(7, 6), inch(82.5), inch(82.5), inch(82.5), ft(6, 2)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=6),
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
            path=(pt(ft(8), ft(28, 5)), pt(ft(8, 6), ft(28, 5)),
                  pt(ft(8, 6), ft(24)), pt(inch(119.875), ft(24))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 6), ft(7, 6)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=20),
    # It leaves its collar 6" south and steps down on a 30° ramp (2026-11-01; a 2" stub and
    # a 7 3/4" drop were shorter than their elbows' take-offs).
    # The low pickup is 4" off the floor on W-B-SA-W. The route uses W-B-CW's x=1'-7" bay
    # (out of the panels' 110.26(E) space since 2026-10-31), clear of D-B-FURN's header,
    # then turns east at y=3'-4". Both sauna radials share the lane at separate tiers: this
    # one at 82 1/4", 1/4" under the supply's underside. At y=3'-4" it enters the centre of W-B-SA-W's 5 1/2" cavity and drops
    # between the studs to 4" AFF. The 2" shift to the register's y=3'-2" station stays
    # inside that stud bay. W-B-SA-W uses SAUNA_2X6 so the 4" section fits with 3/4" each
    # side; its hot-side liner face stays fixed.
    DuctRun(uid="1Y457X9DMH", tag="DU-B-ERV-R-SAUNA-EXH", system=DuctSystem.EXHAUST,
            path=(pt(ft(5, 3), ft(28, 1)), pt(ft(5, 3), ft(27, 7)), pt(inch(49.5625), ft(27, 7)),
                  pt(ft(1, 7), ft(27, 7)), pt(ft(1, 7), inch(40)),
                  pt(inch(116.5625), inch(40)), pt(inch(116.5625), inch(40)),
                  pt(inch(116.5625), ft(3, 2)), pt(inch(122), ft(3, 2))),
            elevations=(ft(7, 6), ft(7, 6), inch(82.25), inch(82.25), inch(82.25), inch(82.25),
                        inch(4), inch(4), inch(4)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=20),
]
