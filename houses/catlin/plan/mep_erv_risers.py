# haus: editable
# Catlin MEP — the ERV's chase risers and their level-2 feeds: DU-ERV-RISER-SUP/-EXH up the
# chase at (1', 35'-1.3"), and the feeds between them and the two RM-M-MECH plenums.
#
# One list, DUCTS_ERV_RISERS, spread whole onto the main storey by plan/mep.py. The two
# outdoor legs, DU-ERV-OA/-EA, are in plan/mep_erv_outdoor_legs.py (split 2026-11-12 for
# size); their hoods and wall penetrations are in plan/mep_erv_outdoor.py. The system as a
# whole is documented once, in plan/mep_erv_l1.py's header.
from typehaus import (
    DuctRouting,
    DuctRun,
    DuctSystem,
    ft,
    inch,
    pt,
)

from .erv_balance import (
    DU_ERV_RISER_EXH,
    DU_ERV_RISER_SUP,
    DU_M_ERV_EXH_FEED,
    DU_M_ERV_SUP_FEED,
)

# ====================================== RISERS =======================================
#
# Three round risers up the radon/plumbing chase at (1', 35'-1.3"), the house's one continuous
# basement-to-attic shaft: RM-M-MECH's floor on main, the 2'-9" x 2'-2 1/8" notch walled by
# W-S-CH-W/W-S-CH-S in RM-S-BATH1's NW corner on second, out onto the attic deck.
#
# ** MEASURED OFF WALL LAYERS, NOT ROOM POLYGONS. ** `resolve/rooms.py` polygonizes from
# wall AXES and insets only by the lining, and these walls are `face("sheathing-ext")`, so
# their axis IS the sheathing exterior: a room-polygon reading counts 6" of exterior-wall
# stud as shaft on each such face. Against the resolved wall LAYERS the notch is
# **x 0'-6 5/8"..2'-6 5/8" by y 33'-3 1/4"..35'-5 3/8" — 24" wide by 26 1/8" deep.**
#
# ** IT WAS FOUR RISERS THIS MORNING AND THE FOURTH IS WHY EVERYTHING ELSE MOVED. ** The
# measured pack, envelope by envelope:
#
#     DU-ERV-RISER-SUP   x  9 5/8"    6 5/8" .. 12 5/8"   y 33'-10 1/4", flush to the west face
#     DU-S-ERV-HP-FEED   x 12"        9"     .. 15"       y 33'-10 1/4", joins SUP's head
#     DU-ERV-RISER-EXH   x 18 5/8"   15 5/8" .. 21 5/8"   y 33'-10 1/4", 5/8" clear of HP-FEED
#     DU-ERV-EA          x  2'-0"    1'-8"  .. 2'-4"      y 35'-0", 8", basement to +17'-0"
#
# ** y=33'-10 1/4" SINCE 2026-09-23, NOT 33'-7 1/2". ** At 33'-7 1/2" both stood 1 1/4" in
# W-M-MECH-S's stud plane, on FS-S-WEST's y=33'-4" truss and on FS-M-MECH's 33'-9 3/8"
# joist. The legal band is 33'-9 3/8" (the partition's face) to 33'-11 1/8" (the radon
# stack), mid-bay in both upper decks; the cut joist is FO-M-ERV-OA's (plan/storeys/main.py).
#
# Three full-height risers on 9" centres fill the 24" exactly on one line, which is why
# a fourth could never join that row: HP-FEED is a short STANDPIPE from FS-ATTIC's
# joist bay up to the deck, not a riser, so it overlaps SUP in plan only across the 3/4" of
# z where the two are joined. That is a joint and not a clash, and it is the whole reason
# four ducts fit where four risers could not.
#
#
# The supply and extract risers run the full height, basement manifolds to attic manifold.
#
# Filed on the MAIN storey so their authored elevations read as project-frame numbers
# directly (the main datum is 0'-0"). -19 7/16" is the basement manifolds' port level;
# +244" is 4" above the attic deck, the centreline of a 6" duct lying on it.
DUCTS_ERV_RISERS = [
    # ** IT STOPS UNDER THE DECK, AND ONLY THIS ONE DOES. ** +244" is the
    # centreline of a 6" duct lying on the attic deck, and it is right for the three risers
    # that surface east of x=11 1/2" — but this column is at x=0'-5", where the 6:12 underside
    # is 4" above that deck. A 6" duct cannot come up there; it would be 1.4" proud of the
    # rafters, which `integrity.element_above_roof` catches. So the riser tops out low in the
    # FS-ATTIC bay instead (231 7/8", 3/8" over DU-S-ERV-HP-FEED's start) and its feed jogs
    # the 7" east in the bay before standing up — the
    # same move VR-M-STACK makes, in the same shaft, at the same rake.
    #
    # Moving the column east instead is not available: the chase's measured clear is 24" (see
    # the note above) and the three-in-a-row at x=5"/14"/23" already over-fills it by an inch.
    # ** BOTH RISERS REACH THE MANIFOLD THEY SERVE. ** The manifolds are at
    # x 5'-6"..7'-6", 61" and 73" of plan away, and the horizontal leg between is drawn.
    # `mep.duct_connectivity` is the check that grades it.
    #
    # THE SUPPLY LEG GOES ROUND THE NORTH of EQ-B-ERV: east at y=31'-8", which is 3 1/2"
    # clear of the machine's north face (y=376 1/2") and stops at x=5'-10", 2" short of
    # RM-B-ESS's x=6'-0" wall, then south into EQ-B-ERV-MAN-SUP's west end. The room's other
    # two through-routes are both taken — x=6'-6" is DU-B-ERV-R-GYM and -SAUNA-SUP's shared
    # lane for the whole depth of the basement, and y=30'-6" east of the manifold is
    # DU-B-ERV-R-PLAY's.
    #
    # THE EXTRACT LEG DROPS TO -27" FIRST, and that is the only reason these two do not
    # collide: it has to cross the supply leg's y=31'-8" lane to get south, and 6" ducts on
    # 7 9/16" centres do not share a crossing. -27" puts 1 5/8" between the two envelopes,
    # keeps 79 3/8" of headroom under it — over R305.1.1's 76" basement projection floor —
    # and rises back to the port level over the 46" of its east run, a 9 degree rake, rather
    # than jogging at the manifold. It reaches EQ-B-ERV-MAN-EXH from the NORTH at x=5'-10"
    # because the manifold's own west approach along y=28'-6" is DU-B-ERV-R-BENCH's.
    # ** BOTH ROOM-SIDE RISERS ARE BARE SINCE 2026-09-23 (owner decision). ** They carry
    # indoor-temperature air through conditioned space from end to end — basement, mech
    # closet, the second-floor chase, the attic floor — so IECC R403.3 asks nothing of them,
    # and 2" of R-8 wrap each made the NW chase unbuildable. DU-ERV-OA/-EA carry outdoor
    # air and keep theirs, vapour-sealed.
    DuctRun(uid="1BMFGSMKJY", tag="DU-ERV-RISER-SUP", system=DuctSystem.SUPPLY,
            # (2026-11-21, §10.31) It leaves the moved plenum's NORTH face over DU-ERV-EA,
            # climbs a 30 degree pair to 92.6" (over DU-ERV-OA's leg), west on y=27'-7.9" and
            # down a 45 to 87.6" before CD-B-GARAGE, then north up the west band on x=2'-7.9" (stacked over
            # DU-ERV-RISER-EXH, 0.1" off DU-ERV-OA) to the bay between the 32'-5.4" joist and
            # FO-M-ERV-OA's trimmer pack, and west in it to x=1'-5 1/2", down onto the foot.
            # Coming down WEST of DU-ERV-OA's drop is what lets it reach a plenum south of the
            # outdoor rows without crossing either.
            # (2026-10-31) It drops out of the bay at x=1'-5 1/2", not under the riser: at
            # x=1'-3.4" the drop stood 1.6" into ED-B-BACKUP-ENCL's NEC 110.26(E) dedicated
            # space (x <= 14", y 382..398").
            # (2026-11-12) The foot's 12" tail is one SKEWED leg, not a 30 degree jog: the drop stands
            # at x=17.9" and the tail runs 12.2" NNW onto the riser's x=15.4" (two stamped 90s want
            # 12", and the jog's three turns wanted 18"). The skew's edge stays 0.17" off
            # ED-B-BACKUP-ENCL's y=398" space edge (x 14") and 0.1" off CD-B-ATTIC-RISER's x=19.1" face.
            # The corner where it enters the bay is DU-M-ERV-SUP-FEED's tee.
            path=(pt(inch(92), inch(313.21875)), pt(inch(92), inch(319.9)),
                  pt(inch(92), inch(324.23)), pt(inch(92), inch(331.9)),
                  pt(inch(63.3), inch(331.9)), pt(inch(58.3), inch(331.9)),
                  pt(inch(31.9), inch(331.9)), pt(inch(31.9), inch(394.8)),
                  pt(inch(31.9), inch(394.8)), pt(inch(17.9), inch(394.8)),
                  pt(inch(17.9), inch(394.8)), pt(inch(15.4), inch(406.8)),
                  pt(inch(15.4), inch(406.8))),
            # (2026-11-12) The head stops at 230 1/4" (FS-ATTIC -9 3/4"), where DU-S-ERV-HP-FEED's
            # 30 degree skew leaves it.
            elevations=(inch(-19.4375), inch(-19.4375), inch(-16.8375), inch(-16.8375),
                        inch(-16.8375), inch(-21.8375), inch(-21.8375), inch(-21.8375),
                        inch(-6.4), inch(-6.4), inch(-18.4375), inch(-18.4375), inch(230.25)),
            # 150 cfm: the 210 at its foot less the basement plenum's 60. Its highest flow
            # anywhere (notes/erv_static_budget.md §10.6).
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_ERV_RISER_SUP),
    DuctRun(uid="GFTW5CBARX", tag="DU-ERV-RISER-EXH", system=DuctSystem.EXHAUST,
            # ** IT LEAVES THE PLENUM'S WEST END, NOT ITS CENTRE. ** The leg keeps the
            # box's own y=34'-6" centre line, and the station it starts from is what moved:
            # x=4'-2" instead of 5'-0". The four attic radials leave the SOUTH face at
            # y=34'-2" (D2) on collars from 4'-6" east, and a trunk leg that started at the
            # box's centre ran west THROUGH all four of their stations 4" away — 1" short of
            # the 5" a 6" trunk and a 4" radial need between them, and all three radials
            # that reach a lane reported against it. Starting west of every collar puts the
            # nearest pair 5.66" apart on the diagonal and crosses none of them.
            #
            # The north face was the other candidate and is worse: CD-B-SPARE-CHASE stands
            # up at (2'-6", 34'-10"), so a leg on y=34'-10" grazes it by a tenth of an inch.
            #
            # Re-stationed at (2'-2.9", 33'-10.8") on 2026-09-23 — the east end of the chase's
            # south band, so DU-M-ERV-EXH-FEED arrives from the east with nothing between.
            # (2026-11-21, §10.31) Down the west band at -28.4" (underside 78" AFF: the NEC
            # 110.26(A) working spaces) to y=27'-1.4", 0.7" north of PR-M-S-BATH1-DRAIN's riser,
            # east and up a 45 pair to 91 1/4" over DU-ERV-OA, east to x=5'-10", then south
            # stacked over OA's leg, down a 30 degree pair to 89" and into EQ-B-ERV-MAN-EXH's north face.
            # (2026-11-12) The attic jog is a 45 pair (7.2" south over 10 1/4" of the y=34'-6" lane):
            # two 90s need 12" between them and have 7.2". The ramp starts 0.5" east for the 90 before it.
            path=(pt(ft(4, 2), ft(34, 6)), pt(inch(42.6), ft(34, 6)),
                  pt(inch(35.4), inch(406.8)), pt(inch(26.9), inch(406.8)),
                  pt(inch(26.9), inch(406.8)),
                  pt(inch(26.9), inch(325.44)), pt(inch(36), inch(325.44)),
                  pt(inch(46.2), inch(325.44)), pt(inch(70), inch(325.44)),
                  pt(inch(70), inch(316.9)), pt(inch(70), inch(313.02)),
                  pt(inch(70), inch(286.84375))),
            elevations=(inch(244), inch(244), inch(244), inch(244), inch(-28.4),
                        inch(-28.4), inch(-28.4), inch(-18.2), inch(-18.2),
                        inch(-18.2), inch(-20.44), inch(-20.44)),
            # 146 cfm below the level-2 tap (attic 55 + level-2 91), 55 above it: the
            # basement's 46 never enters it (notes/erv_static_budget.md §10.6).
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_ERV_RISER_EXH),
    # ================== THE TWO LEVEL-2 MANIFOLD FEEDS (2026-09-20) ==================
    #
    # ** THE TWO MAIN-STOREY PLENUMS HAD NO DRAWN FEED AT ALL, AND THAT WAS A HOLE IN THE
    # MODEL AND NOT A SIMPLIFICATION. ** `mep.duct_connectivity` never said so, because it
    # grades a run's two ENDS and every run at level 2 has both of its ends right: the three
    # supply radials start on EQ-M-ERV-MAN-SUP's collars, the extract trunk starts on
    # EQ-M-ERV-MAN-EXH's. Nothing asks what FILLS the supply box or EMPTIES the extract one.
    # notes/erv_static_budget.md §9 is where it surfaced: both riser terms are worked at
    # 210 cfm over their whole length because there was no tap elevation to split them at,
    # and the note WITHDREW its segmented figure rather than back-derive one. These two runs
    # are that tap, drawn.
    #
    # Filed here on MAIN and not in plan/mep_erv_l2.py with the rest of level 2: they run in
    # RM-M-MECH's own volume, not in FS-S-WEST's cavity, so they carry no `floor_ref` and
    # their elevations are project-frame like everything else in this file. +101 1/4" is the
    # plenums' own port plane, derived exactly as plan/mep_erv_l2.py's `_PORT_Z` is — both
    # boxes are wall-hung at 8'-0" off a finished floor 1 1/4" over the storey datum, so each
    # case is 97 1/4"..105 1/4" and a port on its mid-height is +101 1/4". (`_PORT_Z` is that
    # same plane read from the SECOND storey, -18 3/4".)
    #
    # ** NEITHER FEED IS 4" OR 8", AND THE CENSUS IS PART OF WHY. ** `mep.erv_manifold_ports`
    # counts a BRANCH as a run landing in the case whose section equals the type's own
    # `port_diameter`. EQ-T-ERV-PLENUM-M-SUP is FULL at 2 of 2 4" collars and
    # EQ-T-ERV-PLENUM-M-EXH at 1 of 1 8" collar, so a feed drawn at either of those sizes
    # would read as a fourth radial or a second trunk and FAIL. An inlet is not a branch.
    #
    # ===================== THE CLOSET, MEASURED OFF THE RESOLVED MODEL =====================
    #
    # ** THE ROOM IS 63" x 23" OF CLEAR, NOT THE 70 3/4" x 30 3/4" A ROOM POLYGON REPORTS. **
    # `resolve/rooms.py` polygonizes from wall AXES, and three of the four walls here are
    # `face("sheathing-ext")` — their axis IS the sheathing exterior, so the polygon counts
    # the whole stud bay as shaft. Off the resolved LAYERS the inside faces are
    # **x 6 5/8"..69 5/8" by y 402 3/8"..425 3/8"**, and that reading is what these two runs
    # are laid against; the 39" x 31" "free bay" in the prose above is the loose number.
    #
    # What stands in it, floor to deck, at the port plane:
    #
    #     DU-ERV-RISER-SUP        x  6 5/8".. 12 5/8"   y 403 1/4"..409 1/4"
    #     DU-ERV-RISER-EXH        x 15 5/8".. 21 5/8"   y 403 1/4"..409 1/4"
    #     VR-M-STACK radon   x 10 1/2".. 13 1/2"   y 410 1/8"..413 1/8"
    #     VR-M-STACK vent    x 10 1/2".. 13 1/2"   y 414 7/8"..417 7/8"
    #     CD-B-ATTIC-RISER        x 17 1/8".. 18 7/8"   y 413 1/8"..414 7/8"
    #     CD-B-DATA-CHASE         x 23 1/4".. 24 3/4"   y 413 1/4"..414 3/4"
    #     CD-B-SPARE-CHASE        x 28 7/8".. 31 1/8"   y 412 7/8"..415 1/8"
    #     DU-ERV-EA               x 20"    .. 28"       y 416"    ..424"
    #
    # and the two boxes themselves, which are what the east end of the room is FOR:
    # SUP x 40"..64" by y 404"..412", EXH x 35"..69" by y 416"..424", both z 97 1/4"..105 1/4".
    #
    # ** THE NORTH HALF OF THE ROOM IS NOT A ROUTE. ** DU-ERV-EA is full height and 8" wide
    # at x 20"..28", the extract plenum runs x 35"..69" on the same latitudes, and north of
    # both there is 1 3/8" to the wall. Every lane across this closet is in the SOUTH band.
    #
    # ** AND THE SUPPLY RISER IS SEALED INTO ITS CORNER, WHICH IS THE ONE FACT THAT DECIDED
    # BOTH RUNS. ** It sits WEST of the exhaust riser on the same y, so anything leaving it
    # eastward on that line runs straight through DU-ERV-RISER-EXH. Round it to the north and
    # there are exactly two gaps, and both are narrower than a 6" pipe:
    #
    #     west wall face 6 5/8"  ->  radon west face 10 1/2"    =  3 7/8"
    #     exhaust riser top 409 1/4"  ->  radon south face 410 1/8"  =    7/8"
    #
    # So the EXTRACT feed below is drawn and the SUPPLY feed is not; the block at the foot
    # of this list is why, measured rather than asserted.
    DuctRun(uid="8BN9DXZBZS", tag="DU-M-ERV-EXH-FEED", system=DuctSystem.RETURN,
            # ** THE SHORT ONE, AND IT IS CLEAR OF EVERYTHING BY 7/8" OR BETTER. ** Off the
            # extract plenum's WEST END at x=2'-11", straight down 7 3/4", south down the
            # x=2'-11" lane (7/8" clear of CD-B-SPARE-CHASE's east face, 2" clear of the
            # supply plenum's west end), and west into DU-ERV-RISER-EXH.
            #
            # ** IT DROPS TO +93 1/2" FIRST, AND THAT IS TO LEAVE THE PORT PLANE FREE. **
            # The south band carries the closet's one through-lane, and the supply side has
            # no other candidate for it (see the foot of this list). At +93 1/2" a 6" pipe's
            # crown is 96 1/2" — 3/4" under the plenums' own underside and clear of anything
            # a future supply feed could want at the port plane — and 7'-6 1/2" of headroom
            # is left below it in a closet nobody stands in.
            #
            # ** IT LEAVES THE END FACE, NOT THE PORT. ** EQ-T-ERV-PLENUM-M-EXH states its
            # `riser` inlet at the case's own centre (4'-4", 35'-0") and `approximate`, which
            # is the type saying "somewhere on this box" rather than naming a station — and
            # the centre is the one place it cannot be, because the 8" trunk collar drops
            # through x 42 1/2"..50 1/2" and a feed drawn from the centre would run the length
            # of the box straight through it. `mep.duct_connectivity` reports the west end as
            # so many inches off the nominal port, exactly as it does for both basement
            # plenums, and that sentence is the truth about an undimensioned inlet.
            #
            # RETURN and not EXHAUST, because that is what the port declares and what the
            # type's own comment argues: this box is where the two halves of the extract side
            # meet — ten wet-and-dry takeoffs in on one 8" exhaust trunk, the sum of them out
            # on a 6" return riser. It closes `mep.equipment_port_service`'s standing UNKNOWN
            # on this box.
            #
            # The last vertex stops 2 1/2" short of the riser's axis, at its face: that
            # is where a branch tee's spigot ends, and `mep.duct_connectivity` reads it as
            # landing on the riser. Since 2026-09-23 it tees into the riser's EAST face on
            # y=33'-10", clear of the three conduit risers now standing on y=34'-2 3/8".
            path=(pt(ft(2, 11), ft(35)), pt(ft(2, 11), ft(35)),
                  pt(ft(2, 11), inch(406.8)), pt(inch(29), inch(406.8))),
            elevations=(inch(101.25), inch(93.5), inch(93.5), inch(93.5)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_M_ERV_EXH_FEED),
    # ===== THE SUPPLY FEED (2026-11-12, notes/erv_static_budget.md §10.25) =====
    #
    # No 6" lane leaves the riser in the closet: SUP, the three chase conduits, EXH and EA
    # leave 3.0" at best, and the closet is 23 1/8" deep against the 24" a re-pack needs. So
    # the feed tees off the riser's BASEMENT corner, where the riser turns up into its bay:
    # straight on north at -18 7/16" under the joists, in the lane between PR-B-CW-TRUNK
    # (x 57") and PR-B-KITCH-DRAIN's drop (x 66 1/2") that CD-B-GARAGE vacated, 0.4" over
    # the drain's leg at y=33'-7"; then one stamped 90 up through FO-M-ERV-SUP-FEED (the
    # 405-421" bay east of FO-M-ERV-OA's header) into the box's underside at y=412". In the
    # closet it stands 6 3/4" off W-M-MECH-S, behind the doorway's east end.
    DuctRun(uid="BKT25YWMSR", tag="DU-M-ERV-SUP-FEED", system=DuctSystem.SUPPLY,
            path=(pt(inch(31.9), inch(394.8)), pt(inch(62), inch(394.8)),
                  pt(inch(62), inch(394.8)), pt(inch(62), inch(412)),
                  pt(inch(62), inch(412))),
            elevations=(inch(-6.4), inch(-6.4), inch(-18.4375), inch(-18.4375), inch(98.5)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_M_ERV_SUP_FEED),
]
