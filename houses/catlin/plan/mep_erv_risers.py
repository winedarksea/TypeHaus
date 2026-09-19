# haus: editable
# Catlin MEP — the ERV's four VERTICAL runs: three risers up the chase at (1', 34'-6")
# and the two outdoor legs that leave it for the north facade.
#
# One list, DUCTS_ERV_RISERS, spread whole onto the main storey by plan/mep.py. The hoods
# these legs terminate on, and the wall penetrations they pass through, are in
# plan/mep_erv_outdoor.py. The system as a whole is documented once, in
# plan/mep_erv_l1.py's header.
from typehaus import (
    DuctRouting,
    DuctRun,
    DuctSystem,
    ft,
    inch,
    pt,
)
# ====================================== RISERS =======================================
#
# Three round risers up the radon/plumbing chase at (1', 34'-6"), the house's one continuous
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
#     DU-ERV-RISER-SUP   x  9 5/8"    6 5/8" .. 12 5/8"   y 33'-7 1/2", flush to the west face
#     DU-S-ERV-HP-FEED   x 12"        9"     .. 15"       y 33'-7 1/2", joins SUP's head
#     DU-ERV-RISER-EXH   x 18 5/8"   15 5/8" .. 21 5/8"   y 33'-7 1/2", 5/8" clear of HP-FEED
#     DU-ERV-EA          x  2'-0"    1'-8"  .. 2'-4"      y 35'-0", 8", basement to +17'-0"
#
# Three full-height risers on 9" centres fill the 24" exactly at y=33'-7 1/2", which is why
# a fourth could never join that row: HP-FEED is a 12 7/8" STANDPIPE between FS-ATTIC's
# bottom chord and the deck, not a riser, so it overlaps SUP in plan only across the 3/4" of
# z where the two are joined. That is a joint and not a clash, and it is the whole reason
# four ducts fit where four risers could not.
#
# ============ WHAT THE WEST FACADE COST, MEASURED AND THEN PAID OFF 2026-09-15 ============
#
# ** THE TWO OUTDOOR LEGS CARRIED TWELVE INTERPENETRATIONS BETWEEN THEM. ** Not near-misses
# — shared solid, measured off the resolved model as the overlap of swept envelopes, ducts
# and pipes together:
#
#                                             segs  worst shared solid
#     DU-ERV-OA entry @ +4'-0"  x RISER-SUP     2    6     x 2 1/2 x 6"
#     DU-ERV-OA entry @ +4'-0"  x RISER-EXH     1    6     x 2 1/2 x 6"
#     DU-ERV-EA exit  @ +17'-0" x RISER-SUP     1    6     x 2 1/2 x 8"
#     DU-ERV-EA exit  @ +17'-0" x RISER-EXH     2    6     x 2 1/2 x 8"
#     DU-ERV-EA basement leg    x PR-B-KITCH-DRAIN  3    2 x 51 x 6 5/16"  <- runs INSIDE it
#     DU-ERV-EA riser y=34'-8"  x PR-B-BATH-VENT    1    8 x 1 1/2 x 2"
#     DU-ERV-EA riser y=34'-8"  x PR-B-SAUNA-VENT   1    8 x 2 x 2 1/2"
#     DU-ERV-EA riser y=34'-8"  x PR-M-WC-VENT      1    8 x 2 x 2 7/16"
#                                            ----
#                                             12
#
# Both sweeps existed for ONE reason: the hoods were on the WEST facade, and the shaft lay
# between each run and its own hood. **Moving both hoods to the north wall removed every one
# of them.** DU-ERV-OA left the chase entirely — it runs main -> basement and never needed a
# continuous shaft — and DU-ERV-EA's riser moved from y=34'-8" to y=35'-0", out of the
# six-vent bundle that crosses at y=34'-6" and skewered it at five separate elevations.
# Re-scanned after the move, **both runs are clear of every duct and pipe in the house and of
# each other**, and the NW column's total fell from 45 interpenetrating pairs to 37.
#
# ** WHAT IT BOUGHT, BESIDES BUILDABILITY. ** DU-ERV-OA's riser at x=3'-4" in the open closet
# has room for 8" where the shaft's east lane did not: an 8" envelope there overran the
# shaft's east face by an inch, and notes/erv_static_budget.md §7 had the upsize blocked on
# that for weeks. At 8" the term falls 0.1318 -> 0.0315 and the delivered figure reaches
# 207.0 cfm against MN's 205.
#
# ** NOTHING GRADES ANY OF THIS, AND THAT IS STILL TRUE. ** There is no `mep.duct_interference`;
# the plan named one and it was never built. Two things block it, and both are worth writing
# down because they outlive this change:
#   * the main-storey radial layer is deliberately schematic — every radial is drawn on one
#     z=+9'-3 5/8" plane and about forty pairs of them cross there — so a guard has to be
#     scoped to full-height runs in a chase or it reports the drawing convention;
#   * `ResolvedConduit` carries no per-vertex elevations at all, only `z_start_m`/`z_end_m`,
#     so the chase's nine conduits are two-point schematics (CD-B-ATTIC-RISER "rises" 24 ft
#     while travelling 5'-6" horizontally). A duct cannot be proven clear of a conduit whose
#     elevation the model does not hold.
#
# The 37 pairs that remain in this column are pipe-against-pipe and pipe-against-radial, and
# none of them is this system's to fix. The six vents converging on (1'-0", 34'-6") cross the
# thirteen main-storey radial lanes at four elevations; PR-B-BATH-VENT and PR-B-SAUNA-VENT
# share solid with PR-B-KITCH-DRAIN. **They are recorded here because somebody measured them,
# not because this pass touched them.**
# ======================================================================================
#
# The supply and extract risers run the full height, basement manifolds to attic manifold.
# The outdoor-air and exhaust-air risers run the same way because their hoods are in the
# north gable; see EQUIPMENT_ERV_HOODS above for why.
#
# Filed on the MAIN storey so their authored elevations read as project-frame numbers
# directly (the main datum is 0'-0"). -19 7/16" is the basement manifolds' port level;
# +244" is 4" above the attic deck, the centreline of a 6" duct lying on it; +276" is the
# gable hoods' centreline, 3'-0" above that deck. Each of the two outdoor runs carries its
# hood-side vertex OUTSIDE the north wall (y=36'-6") rather than stopping at the inside face:
# `mep.erv_outdoor_terminals` decides which EXHAUST run is the machine's discharge by asking
# whether its last vertex lands outside every resolved room, which is the same probe
# `code.M1502_dryer_exhaust` uses for M1502.3 and is a fact about the geometry rather than a
# naming convention.
DUCTS_ERV_RISERS = [
    # ** IT STOPS UNDER THE DECK, AND ONLY THIS ONE DOES. ** +244" is the
    # centreline of a 6" duct lying on the attic deck, and it is right for the three risers
    # that surface east of x=11 1/2" — but this column is at x=0'-5", where the 6:12 underside
    # is 4" above that deck. A 6" duct cannot come up there; it would be 1.4" proud of the
    # rafters, which `integrity.element_above_roof` catches. So the riser tops out on
    # FS-ATTIC's bottom chord instead (231 7/8" = the deck less 8 7/8", the same datum
    # DU-S-ERV-HP-FEED uses) and its feed jogs the 7" east in the bay before standing up — the
    # same move VR-M-RADON-VENT makes, in the same shaft, at the same rake.
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
    DuctRun(uid="1BMFGSMKJY", tag="DU-ERV-RISER-SUP", system=DuctSystem.SUPPLY,
            path=(pt(ft(5, 10), ft(30, 6)), pt(ft(5, 10), ft(31, 8)),
                  pt(inch(9.625), ft(31, 8)), pt(inch(9.625), ft(33, 7.5)),
                  pt(inch(9.625), ft(33, 7.5))),
            elevations=(inch(-19.4375), inch(-19.4375), inch(-19.4375),
                        inch(-19.4375), inch(231.875)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            insulation="R-8 wrap", design_cfm=210),
    DuctRun(uid="GFTW5CBARX", tag="DU-ERV-RISER-EXH", system=DuctSystem.EXHAUST,
            path=(pt(ft(5), ft(34, 6)), pt(inch(18.625), ft(34, 6)),
                  pt(inch(18.625), ft(33, 7.5)), pt(inch(18.625), ft(33, 7.5)),
                  pt(inch(18.625), ft(29, 3)), pt(ft(5, 0), ft(29, 3)),
                  pt(ft(5, 10), ft(29, 3)), pt(ft(5, 10), ft(28, 8))),
            elevations=(inch(244), inch(244), inch(244), inch(-27),
                        inch(-27), inch(-19.4375),
                        inch(-19.4375), inch(-19.4375)),
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            insulation="R-8 wrap", design_cfm=210),
    # The outdoor side, which did not exist at all before this pass. Both legs carry
    # outdoor-temperature air through conditioned space, so both are insulated AND vapour
    # sealed — an uninsulated intake duct sweats all winter and rains on whatever is under
    # it, which here would be RM-S-BATH1's ceiling and RM-B-FURNACE's electrical.
    #
    # Authored hood-end first for the intake and hood-end last for the discharge:
    # `mep.erv_outdoor_terminals` reads an OUTDOOR_AIR run from its hood inward and an
    # EXHAUST run outward to its hood, which is the direction the air goes and the direction
    # a plan reader traces.
    # ** BOTH OUTDOOR LEGS STOP AT THE NW CHASE. ** See EQUIPMENT_ERV_HOODS_* above for why
    # the north-gable route is not viable. Each is a riser out of the basement manifold and
    # one straight penetration through the west wall: the intake at +4'-0" on the main
    # storey, the discharge at +17'-0" on the second.
    #
    # ** THE HOOD VERTEX IS x = -0'-8", AND -0'-6" WAS SHORT (corrected 2026-09-11). **
    # -6" was picked to clear `mep.erv_outdoor_terminals`, which decides which EXHAUST run is
    # the machine's discharge by asking whether the run's LAST vertex lands outside every
    # resolved room's `clear_face` — and `clear_face` sits on the wall AXIS, which for these
    # `face("sheathing-ext")` walls is x=0'-0". A run stopping at the interior face reads as
    # indoors, the check finds no discharge at all, the 10-ft test never runs, and the whole
    # thing degrades silently to a single PASS on hood height. -6" cleared the axis and the
    # check went green — but the axis is not the building. W-M-W1B / W-S-W1B resolve
    # 7 1/4" of wall outboard of it (foam, vent gap, girt, PBR-26 cladding to x=-0'-7 1/4"),
    # so BOTH ducts died 1 1/4" inside the cladding: a hood on the facade with no hole under
    # it. **Nothing in the engine grades a duct end against a wall's layers**, which is why a
    # check-driven number outlived the geometry it was standing in for.
    # -0'-8" carries each run 3/4" past the cladding, into the hood's collar.
    DuctRun(uid="MW0MY7GDME", tag="DU-ERV-OA", system=DuctSystem.OUTDOOR_AIR,
            # ** IT LEFT THE CHASE ENTIRELY ON 2026-09-15, AND THAT IS THE POINT. ** This run
            # only ever goes main -> basement; it is the one ERV leg that does NOT need a
            # continuous basement-to-attic shaft, and it was in the chase purely because its
            # hood was on the west facade and the chase was what lay between. Hood on the
            # NORTH wall, riser at x=3'-4", and it touches the chase nowhere.
            #
            # It is a straight drop, and every station is a measured clearance:
            #   x=3'-4"   — W-M-N3B's stud module. The wall frames on 16" centres off an 8"
            #               residue, so `structural.door_framing_module` takes an opening at
            #               x=2'-0", 3'-4", 4'-8" or 6'-0" and nowhere else without cutting a
            #               stud. 2'-0" is inside DU-ERV-RISER-EXH's lane; 4'-8" and 6'-0"
            #               put the riser through PR-B-KITCH-DRAIN (x 4'-5"..4'-7") and
            #               PR-B-CW-TRUNK (x 4'-11 3/8"..5'-0 5/8"). 3'-4" is the one legal
            #               station the duct can also stand on: at 8" its metal runs
            #               x 3'-0"..3'-8", 9" clear of the kitchen drain and 1'-3 3/8" of
            #               the cold-water trunk.
            #   y=33'-11" — 4 5/8" north of W-M-MECH-S's face (the wall spans y 33'-1 5/8"..
            #               33'-6 3/8"), so the duct's own edge clears it by 5/8"; and its
            #               north edge is 2" short of the y=34'-6" vent bundle, which
            #               crosses the closet at -15", -16 1/2", +112" and +117" and is
            #               what makes every other latitude in this bay unusable.
            #   +5'-0"    — NEC 110.26 over ED-M-HP3-DISC; see the hood.
            #   -2'-3"    — the basement radial layer, joined 4" short of the machine so the
            #               last leg is a straight east run onto the port.
            #
            # ** IT IS SHORTER AND STRAIGHTER THAN WHAT IT REPLACED. ** 13'-9" and four
            # elbows against the west-facade route's 14'-0" and six — which is why the 6" ->
            # 8" step buys more here than the note's §7 priced it at, and why the governing
            # side of the whole system moved back to extract when this landed.
            #
            # PR-M-S-BATH1-TUB-DRAIN looks like it is in this lane and is not: it drops at
            # (3'-3 1/4", 34'-1 1/2") but between +10'-0 3/4" and +9'-7 15/16", in the SECOND
            # storey's floor zone. It never reaches the main deck or this riser's +5'-0".
            path=(pt(ft(3, 4), ft(36, 8)), pt(ft(3, 4), ft(33, 11)),
                  pt(ft(3, 4), ft(33, 11)), pt(ft(3, 4), ft(31, 1)),
                  pt(ft(3, 8), ft(31, 1)), pt(ft(3, 8), ft(31, 1))),
            elevations=(inch(60), inch(60), inch(-27), inch(-27),
                        inch(-27), inch(-33.8375)),
            # ** 8", AND THE MOVE IS WHAT PAID FOR IT. ** notes/erv_static_budget.md §7 had
            # priced this upsize for weeks as the one remaining lever on what was then the
            # governing supply column, and it was blocked not by money but by the chase: at
            # the old x=2'-3 5/8" station an 8" envelope overran the shaft's east face by an
            # inch and no re-ordering of four risers avoided it. Out here the lane between
            # the chase conduits and PR-B-KITCH-DRAIN is 1'-10". The term fell 0.1318 ->
            # 0.0315, which took the governing side back to EXTRACT — so §7 is now spent and
            # the lever it named no longer exists.
            diameter=inch(8), routing=DuctRouting.CHASE, material="galvanized",
            insulation="R-8 wrap, vapour-sealed", design_cfm=210),
    DuctRun(uid="BYAVBJKRS6", tag="DU-ERV-EA", system=DuctSystem.EXHAUST,
            # Manifold first, hood last — the direction the air goes, and the direction
            # `erv_outdoor_terminals` reads an EXHAUST run.
            #
            # ** y=35'-0", AND IT IS THE VENT BUNDLE THAT SETS IT, NOT THE WALL. ** The
            # shaft clear is x 0'-6 5/8"..2'-6 5/8" by y 33'-3 1/4"..35'-5 3/8" — 24" x 26".
            # At y=35'-6" an 8" envelope would stand 4 5/8" inside W-S-N3B's stud cavity for
            # its whole height, so the north face bounds it at y=35'-1 3/8". The SOUTH bound
            # is the six-vent bundle that crosses the chase westward at y=34'-6": it is there
            # at -15", -16 1/2", +112", +117" and +232", so anything whose envelope reaches
            # y=34'-5" is skewered at five separate elevations. At y=35'-0" an 8" riser spans
            # y 34'-8"..35'-4": 1" clear of the bundle, 1 3/8" clear of the stud cavity.
            #
            # ** y=34'-8" WAS INSIDE THAT BUNDLE AND NOBODY SAID SO. ** The old station's
            # envelope reached y=34'-4", and three of the six vents run through it —
            # PR-B-BATH-VENT, PR-B-SAUNA-VENT and PR-M-WC-VENT, 8 x 1 1/2 x 2" and better.
            # The prose that chose y=34'-8" reasoned only about the north wall, because the
            # north wall is the thing a duct check looks at; nothing in this engine pairs a
            # duct against a pipe at all.
            #
            # ** THE JOG IS GONE. ** The riser used to turn south 8" at +17'-0" to reach a
            # hood on the WEST facade, and that turn is what swept x 1'-11"..-0'-8" through
            # both trunks. On the north wall the riser and its hood share one station: the
            # run goes straight up and straight out, two elbows fewer.
            #
            # ** THE BASEMENT LEG RIDES THE PORT ELEVATION, NOT THE RADIAL LAYER. ** It used
            # to rise to -2'-3" at the machine and run the radial layer; it now holds
            # -2'-9 7/8" — the port's own height — the whole way to the riser. That ducks it
            # under the vent bundle at -15", under the 4" radial field at -2'-3", and out of
            # PR-B-KITCH-DRAIN's lane, which it previously ran INSIDE for 4'-3". The cost is
            # headroom: the duct's underside sits 6'-7" over the basement floor in
            # RM-B-FURNACE, 17" below the 8'-0 15/16" ceiling. That is a mechanical room and
            # it is walkable, but it is lower than anything else down there and should be on
            # the drawing.
            path=(pt(ft(4, 7), ft(31, 1)), pt(ft(5, 2), ft(31, 1)),
                  pt(ft(5, 2), ft(35)), pt(ft(2), ft(35)),
                  pt(ft(2), ft(35)), pt(ft(2), ft(36, 8))),
            elevations=(inch(-33.8375), inch(-33.8375), inch(-33.8375), inch(-33.8375),
                        inch(204), inch(204)),
            # ** 8", NOT 6" (owner, in the measured package). ** This is the single biggest
            # lever in the static budget and the note prices it: the discharge leg is the
            # long one on the extract chain's worst path, and area goes as d^2 while friction
            # goes as V^2, so a 6" -> 8" step takes roughly two-thirds off this term. The
            # shaft was sized for THIS diameter months before it was bought.
            # `AO-S-ERV-EA` grows 7" -> 9" to match.
            diameter=inch(8), routing=DuctRouting.CHASE, material="galvanized",
            insulation="R-8 wrap, vapour-sealed", design_cfm=210),
]
