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
            # It lands on the plenum's NORTH FACE at x=5'-6" since D3 widened that box to
            # 36" — the face the leg is already arriving at, rather than the west end it
            # used to turn into. Four inches further west and four further south than
            # before, and still inside RM-B-ESS's x=6'-0" wall.
            # ** THE CHASE WAS RE-PACKED ON 2026-09-23. ** It stands at (1'-3.4", 33'-10.8")
            # in the chase's south band, between the branch-vent slot on the west and the
            # three conduits, south of the radon/vent bundle's 19'-6" jog lane.
            # ** WEST IN FS-M-MECH'S JOIST BAY SINCE 2026-09-24. ** At -1'-5 15/16" its
            # y=31'-8" leg crossed DU-ERV-OA's wrapped north-south leg, PR-B-KITCH-DRAIN and
            # PR-B-SAUNA-VENT, each at its own height; no single elevation cleared all three.
            # North off the plenum (1" west of its collar, 5/8" off W-B-ESS-W's face) to the
            # bay between the 32'-5.4" joist and FO-M-ERV-OA's trimmer pack, up into it (6",
            # under half the deck), west over everything, and down again at x=1'-3.4" onto
            # the riser's foot. Two more elbows: +0.033" w.g. (notes/erv_static_budget.md §6).
            # (2026-10-31) It drops out of the bay at x=1'-5 1/2", not under the riser:
            # at x=1'-3.4" the drop stood 1.6" into ED-B-BACKUP-ENCL's NEC 110.26(E)
            # dedicated space (x <= 14", y 382..398"). North to y=401 1/2", then west onto
            # the riser foot, at the old -17 15/16".
            # The 1 5/8" x-jog onto the riser foot is a PAIR OF 30 DEGREE bends (2026-11-05): two 90s
            # on a 6" duct want 6" between them and the jog had 1.7". It starts at y=399 1/8", past
            # the enclosure's y=398" space edge, so the duct never leaves x >= 14".
            path=(pt(inch(65), ft(30, 10)), pt(inch(65), inch(394.8)),
                  pt(inch(65), inch(394.8)), pt(inch(17.0625), inch(394.8)),
                  pt(inch(17.0625), inch(394.8)), pt(inch(17.0625), inch(399.1)),
                  pt(inch(15.4), inch(401.98)), pt(inch(15.4), inch(406.8)),
                  pt(inch(15.4), inch(406.8))),
            elevations=(inch(-19.4375), inch(-19.4375), inch(-7.4), inch(-7.4),
                        inch(-17.9375), inch(-17.9375), inch(-17.9375), inch(-17.9375),
                        inch(231.875)),
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
            # ** THE 9-DEGREE RAKE IS GONE (D3, 2026-09-19) AND SO IS THE PAIR IT MADE. **
            # The leg used to climb from -27" to port level over the 46" between x=1'-6 5/8"
            # and x=5'-0", which put its envelope right through PR-B-KITCH-DRAIN's x=4'-6"
            # fall line at -19" — and `mep.fitting_pattern` could not name the part either,
            # because a raked round duct is not a fitting anybody stocks. It now runs level
            # at -27 1/2" the whole way east, ten inches under the drain, and turns UP into
            # the plenum's underside at x=6'-1 1/2" on two 90s. Half an inch deeper than the
            # old -27" so that the return trunk, which shares this y=28'-6" line at the
            # machine's own -33 27/32", keeps 6 3/8" between the two envelopes; 78 15/16" of
            # headroom under it, still over R305.1.1's 76" basement projection floor.
            # The dry-fire lane lifts only the south approach to 83.5" AFF: rise at
            # y350", west of the lane and south of the sauna supply crossing. The
            # northern low tier stays below that radial; two extra elbows are budgeted.
            # Re-stationed at (2'-2.9", 33'-10.8") on 2026-09-23 — the east end of the chase's
            # south band, so DU-M-ERV-EXH-FEED arrives from the east with nothing between.
            # (2026-11-05) The two short jogs are gone: the 1 9/16" lift at y=350" and the 2 1/2"
            # rise into the box each sat between two 90s (a 6" duct wants 6" and 3"). It now
            # runs level at -28.4" (underside 78" AFF: the NEC 110.26(A) working spaces of ED-B-PANEL and
            # ED-B-BACKUP-ENCL) to x=34", climbs 6.4" on a pair of 30 degree bends, and enters the
            # extract plenum's WEST face at -22", stopping at x=59.8" so it does not reach
            # DU-B-ERV-R-SAUNA-EXH's collar at x=63". The box moved to y=27'-2 1/2" on
            # 2026-11-11 and the leg went with it; the x=26.9" drop is 14 1/2" longer.
            path=(pt(ft(4, 2), ft(34, 6)), pt(inch(26.9), ft(34, 6)),
                  pt(inch(26.9), inch(406.8)), pt(inch(26.9), inch(406.8)),
                  pt(inch(26.9), ft(27, 2.5)), pt(inch(34), ft(27, 2.5)),
                  pt(inch(45.26), ft(27, 2.5)), pt(inch(59.8), ft(27, 2.5))),
            elevations=(inch(244), inch(244), inch(244), inch(-28.4),
                        inch(-28.4), inch(-28.4), inch(-22), inch(-22)),
            # 164 cfm below the level-2 tap (attic 50 + level-2 114), 50 above it: the
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
                  pt(ft(2, 11), inch(406.8)), pt(inch(29.4), inch(406.8))),
            elevations=(inch(101.25), inch(93.5), inch(93.5), inch(93.5)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_M_ERV_EXH_FEED),
    # ===== THE SUPPLY FEED IS NOT DRAWN: NO 6" LANE LEAVES DU-ERV-RISER-SUP =====
    #
    # Re-measured 2026-11-12 with DU-ERV-EA's 1" wrap (notes/erv_static_budget.md §10.25).
    # Every obstacle is full height, so no elevation opens anything:
    #
    #     north: CD-B-SPARE-CHASE top 410.5" -> EA wrap 413.5"   = 3.0" (EXH crown alone 3.7")
    #     east:  SUP riser 18.4" -> EXH riser 23.9"              = 5.5", holding three conduits
    #     south: EXH riser 403.8" -> W-M-MECH-S finish 402.25"   = 1.55"
    #
    # The closet is 23 1/8" deep across the column; EXH + feed + EA stacked at 1/2"
    # clearances is 24", so no re-pack of this file's ducts around the conduits opens it.
    # The basement is fenced too: under FO-M-ERV-OA by DU-ERV-OA's leg, and east of its
    # header by CD-B-GARAGE (x 60.3") and PR-B-KITCH-DRAIN (x 65.3"), 5.0" apart, with a
    # joist bay (no drawn hole) above. `haus route` from the riser at +80": 80 of 12,881
    # nodes reachable, and lifting either chase conduit alone opens nothing. Until another
    # trade moves, `mep.manifold_feed` FAILs EQ-M-ERV-MAN-SUP, and the static budget charges
    # its paths the whole riser at 160 cfm (`erv_routes`' nearest-trunk rule).
]
