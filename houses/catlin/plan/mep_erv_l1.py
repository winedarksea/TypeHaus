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

EQUIPMENT_ERV_BASEMENT = [
    Equipment(uid="QGMYDXSMKH", tag="EQ-B-ERV-MAN-SUP", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(6, 6), ft(30, 6)), footprint=(inch(24), inch(8)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV-MANIFOLD-6",
              mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 2))),
    Equipment(uid="CRN5GT0ECP", tag="EQ-B-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(6, 6), ft(28, 6)), footprint=(inch(24), inch(8)),
              room="RM-B-FURNACE", type_ref="EQ-T-ERV-MANIFOLD-6-EXH",
              mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 2))),
]
# ============================== LEVEL 1 — BASEMENT RADIALS ============================
#
# Six 4" radials off the two plenums beside the machine, boxed under the basement
# ceiling. Centreline at 7'-6" above the basement floor, inside the manifolds' own 7'-2"
# to 7'-10" band and clear of the 8'-0 15/16" underside.
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
    # THE SUPPLY TRUNK IS THE SIMPLE ONE: straight up 14 3/8" off the port to the radial
    # layer at 7'-6", then 19" east into EQ-B-ERV-MAN-SUP's west half at y=30'-4". It stays
    # 2" south of the manifold's own y=30'-6" centre so DU-B-ERV-R-PLAY's lane east of
    # x=6'-6" is untouched.
    #
    # THE RETURN TRUNK CANNOT GO STRAIGHT, and the reason is DU-B-ERV-R-BENCH: that radial
    # runs the whole width of the room at y=28'-6", which fences EQ-B-ERV-MAN-EXH off from
    # the machine at the 7'-6" layer. It leaves the manifold's east end at x=7'-0", drops to
    # 6'-10 7/16", crosses UNDER the x=6'-6" radial lane — the one DU-B-ERV-R-GYM and
    # -SAUNA-SUP share for the depth of the basement — and comes back west at y=29'-9",
    # 1 5/8" clear of the layer above it and 6 13/16" over the machine's case.
    DuctRun(uid="225MZ1YDWB", tag="DU-B-ERV-SUP-TRUNK", system=DuctSystem.SUPPLY,
            path=(pt(ft(4, 9), ft(30, 4)), pt(ft(4, 9), ft(30, 4)),
                  pt(ft(6, 4), ft(30, 4))),
            elevations=(inch(75.6), inch(90), inch(90)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=210),
    DuctRun(uid="6BTCWW2S1V", tag="DU-B-ERV-RET-TRUNK", system=DuctSystem.RETURN,
            path=(pt(ft(7), ft(28, 8)), pt(ft(7), ft(28, 8)),
                  pt(ft(7), ft(29, 9)), pt(ft(3, 8), ft(29, 9)),
                  pt(ft(3, 8), ft(29, 9))),
            elevations=(inch(90), inch(82.4375), inch(82.4375), inch(82.4375),
                        inch(75.6)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=210),
    DuctRun(uid="CND5TE40W0", tag="DU-B-ERV-R-GYM", system=DuctSystem.SUPPLY,
            path=(pt(ft(6, 6), ft(30, 6)), pt(ft(6, 6), ft(10, 6.6)), pt(ft(19), ft(10, 6.6)),
                  pt(ft(19), ft(13))),
            start_elevation=ft(7, 6), end_elevation=ft(7, 6),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=18),
    DuctRun(uid="DMEQ946YAX", tag="DU-B-ERV-R-PLAY", system=DuctSystem.SUPPLY,
            path=(pt(ft(6, 6), ft(30, 6)), pt(ft(19), ft(30, 6)), pt(ft(19), ft(26))),
            start_elevation=ft(7, 6), end_elevation=ft(7, 6),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=30),
    DuctRun(uid="VXGA0P0V72", tag="DU-B-ERV-R-SAUNA-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(6, 6), ft(30, 6)), pt(ft(6, 6), inch(20.5)),
                  pt(inch(199.75), inch(20.5)), pt(inch(199.75), inch(20.5))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 6), ft(7)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=12),
    # The bench hood's pull. It drops out of the ceiling chase to the hood face at 5'-6",
    # which is the vertical leg that makes it a capture hood rather than a ceiling diffuser.
    DuctRun(uid="MTVYDDP43W", tag="DU-B-ERV-R-BENCH", system=DuctSystem.RETURN,
            path=(pt(ft(6, 6), ft(28, 6)), pt(ft(2), ft(28, 6)), pt(ft(2), ft(8, 6)),
                  pt(ft(2), ft(8, 6))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 6), ft(6, 2)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=6),
    DuctRun(uid="03883CKF0H", tag="DU-B-ERV-R-BATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(6, 6), ft(28, 6)), pt(ft(12), ft(28, 6)),
                  pt(ft(12), inch(289.625))),
            start_elevation=ft(7, 6), end_elevation=ft(7, 6),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=20),
    # The sauna's low pickup is 4" off the floor on the WEST liner (the south face went to
    # EQ-B-SAUNA-HTR when the room rotated), so this radial runs the length of the house in
    # the ceiling chase and then drops seven feet down the wall. The
    # drop is drawn — a repeated plan point at two elevations — which it could not be before
    # `DuctRun` carried elevations. The drop moved 3'-10" east with the west liner on
    # 2026-09-05: x=64" is workshop floor now, not sauna wall.
    DuctRun(uid="1Y457X9DMH", tag="DU-B-ERV-R-SAUNA-EXH", system=DuctSystem.EXHAUST,
            path=(pt(ft(6, 6), ft(28, 6)), pt(inch(110), ft(28, 6)), pt(inch(110), ft(3, 2)),
                  pt(inch(110), ft(3, 2))),
            elevations=(ft(7, 6), ft(7, 6), ft(7, 6), inch(4)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=20),
]
