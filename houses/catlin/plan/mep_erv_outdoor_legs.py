# haus: editable
# Catlin MEP — the ERV's two OUTDOOR legs, DU-ERV-OA and DU-ERV-EA, from the machine's
# ports to the north-facade hoods.
#
# One list, DUCTS_ERV_OUTDOOR_LEGS, spread whole onto the main storey by plan/mep.py. Split
# out of plan/mep_erv_risers.py on 2026-11-12 for size; the chase risers and the level-2
# feeds stay there. The hoods these legs terminate on, and the wall penetrations they pass
# through, are in plan/mep_erv_outdoor.py.
from typehaus import (
    DuctDrain,
    DuctRouting,
    DuctRun,
    DuctSystem,
    ft,
    inch,
    pt,
)

from .erv_balance import (
    DU_ERV_EA,
    DU_ERV_OA,
)

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
# none of them is this system's to fix. The six vents converging on the chase cross the
# thirteen main-storey radial lanes at four elevations; PR-B-BATH-VENT and PR-B-SAUNA-VENT
# share solid with PR-B-KITCH-DRAIN. **They are recorded here because somebody measured them,
# not because this pass touched them.**
# ======================================================================================
#
# Filed on the MAIN storey so their authored elevations read as project-frame numbers
# directly (the main datum is 0'-0"). Each of the two outdoor runs carries its hood-side
# vertex OUTSIDE the north wall (y=36'-6") rather than stopping at the inside face:
# `mep.erv_outdoor_terminals` decides which EXHAUST run is the machine's discharge by asking
# whether its last vertex lands outside every resolved room, which is the same probe
# `code.M1502_dryer_exhaust` uses for M1502.3 and is a fact about the geometry rather than a
# naming convention.
DUCTS_ERV_OUTDOOR_LEGS = [
    # The outdoor side, which did not exist at all before this pass. Both legs carry
    # outdoor-temperature air through conditioned space, so both are insulated AND vapour
    # sealed — an uninsulated intake duct sweats all winter and rains on whatever is under
    # it, which here would be RM-S-BATH1's ceiling and RM-B-FURNACE's electrical.
    #
    # Authored hood-end first for the intake and hood-end last for the discharge:
    # `mep.erv_outdoor_terminals` reads an OUTDOOR_AIR run from its hood inward and an
    # EXHAUST run outward to its hood, which is the direction the air goes and the direction
    # a plan reader traces.
    # ** BOTH OUTDOOR LEGS LEAVE THROUGH THE NORTH WALL. ** See plan/mep_erv_outdoor.py for
    # why the gable route is not viable. Each is a riser off the machine and one straight
    # penetration: the intake at +5'-0" on the main storey, the discharge at +17'-0" on the
    # second. Both are wrapped end to end in 1" of closed-cell elastomeric (AP Armaflex, its
    # own vapour retarder, 25/50-rated; 2" until 2026-11-11, §10.22 and §10.13 a), mastic-sealed
    # under the wrap; the wrap stops in the stud bay (notes/air_distribution_products.md §9).
    #
    # ** THE HOOD VERTEX IS x = -0'-8", AND -0'-6" WAS SHORT (corrected 2026-09-11). **
    # -6" was picked to clear `mep.erv_outdoor_terminals`, which decides which EXHAUST run is
    # the machine's discharge by asking whether the run's LAST vertex lands outside every
    # resolved room's cell — and that cell was the wall AXIS, which for these
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
            # ** IT IS SHORTER THAN WHAT IT REPLACED. ** 18.07 ft on six elbows as built
            # (the 2026-10-17 ERV move added the east leg), against the west-facade route's
            # longer sweep — which is why the 6" -> 8" step bought what §7 priced it at.
            #
            # PR-M-S-BATH1-TUB-DRAIN looks like it is in this lane and is not: it drops at
            # (3'-3 1/4", 34'-1 1/2") but between +10'-0 3/4" and +9'-7 15/16", in the SECOND
            # storey's floor zone. It never reaches the main deck or this riser's +5'-0".
            # y=34'-1" since 2026-09-23: wrapped, 33'-11" stood 1/4" inside W-M-MECH-S.
            # (2026-10-31) Over the panels' NEC 110.26(A) working space (78" AFF): south of
            # y=31'-1" the wrap's underside is 78 1/2" AFF (centre -24 15/16"), down x=3'-4"
            # under DU-B-ERV-R-SAUNA-SUP and east on y=29'-3" beside EQ-B-ERV-MAN-EXH (moved
            # 1" south for it) to its port. It holds -21" north of 31'-1" to clear DU-ERV-EA's
            # west leg. Length and elbow count are unchanged.
            # (2026-11-05) The 3.9" step at y=31'-1" is two 30 degree bends, y=31'-8" to 31'-1".
            # (2026-11-11, §10.22) It lands EXACT on the 90-degree machine's south-east port:
            # down x=3'-4" to y=28'-5" and east on that row at 84 1/2", over the return
            # trunk's leg (top 73"), then down the port's kit lead (12" flex + the 90). The row
            # is 27/32" south of the port centre (the flex takes it, about 4 degrees) so the two
            # 10" wraps clear by 1/16" where Broan's ports stand 9 3/4" apart. (2026-11-14) Both
            # rows moved south for EQ-B-ERV's trapeze rod 2: DU-ERV-EA by 0.74", this one 1/2".
            path=(pt(ft(3, 4), ft(36, 8)), pt(ft(3, 4), ft(34, 1)),
                  pt(ft(3, 4), ft(34, 1)), pt(ft(3, 4), ft(31, 8)),
                  pt(ft(3, 4), inch(373.2)), pt(ft(3, 4), inch(340.5)),
                  pt(inch(83.6875), inch(340.5)), pt(inch(83.6875), inch(341.34375))),
            elevations=(inch(60), inch(60), inch(-21), inch(-21),
                        inch(-24.9375), inch(-24.9375), inch(-24.9375), inch(-47.4375)),
            # ** 8", AND THE MOVE IS WHAT PAID FOR IT. ** notes/erv_static_budget.md §7's
            # upsize was blocked by the chase (at the old x=2'-3 5/8" an 8" envelope overran
            # the shaft's east face). Out here the lane is 1'-10"; the term fell 0.1318 ->
            # 0.0315 and handed the governing side back to EXTRACT, so §7 is spent.
            diameter=inch(8), routing=DuctRouting.CHASE, material="galvanized",
            insulation='1" closed-cell elastomeric (AP Armaflex), R-4.2, vapour-sealed', design_cfm=DU_ERV_OA,
            adjustable_elbows=(6,)),
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
            # (2'-0 5/8", 34'-9.5") since 2026-09-23, the chase's NE corner: it tops out at
            # 17'-0", below the radon/vent jog at 19'-6", so it is the one riser that may
            # stand in the jog's lane, and the north strip it exits through is empty. At
            # 35'-0" its 12" wrapped section stood an inch inside W-B-N4.
            # (2026-11-11, §10.22) Off the 90-degree machine's north-east port, EXACT: up the
            # kit lead to 81" (port + 12" flex + the 90), west on y=29'-2 9/16" over the supply
            # trunk's leg (top 73"), down to 78" on 30 degree bends before the lane, and north
            # on x=58.5" under EQ-B-ERV-MAN-SUP's west end as before. Its row is north of
            # DU-ERV-OA's, which is why the two never cross. (2026-11-14) The row is 17/32" south
            # of the port, 0.74" further than before: EQ-B-ERV's trapeze rod 2 stood 0.65" inside
            # the wrap; 1/16" clear now (structural.equipment_hanger_clearance).
            path=(pt(inch(83.6875), inch(351.09375)), pt(inch(83.6875), inch(350.5625)),
                  pt(inch(72.87), inch(350.5625)), pt(inch(67.74), inch(350.5625)),
                  pt(inch(58.5), inch(350.5625)), pt(inch(58.5), inch(418.5)),
                  pt(inch(49.5), inch(418.5)),
                  pt(inch(44.37), inch(418.5)), pt(inch(24.625), inch(418.5)),
                  pt(inch(24.625), inch(418.5)), pt(inch(24.625), ft(36, 8))),
            # (2026-11-12, M1-114) Drain-back: from the 30 degree pair on, every leg falls
            # 1/8"/ft in the air's direction to the riser foot, and the hood leg 1/8"/ft out
            # to the hood. The 10.8" leg off the kit lead stays level: a fall there turns the
            # lead's 90 past 90 and the straight kit lead no longer fits (resolve/flex_bend).
            # The step at x=44.37" keeps its 2.3375" drop; the foot sits 1.10" lower (wrap
            # 69.6" AFF, 1.6" over EQ-B-ESS-INV) and the north leg's wrap leaves the dry-fire
            # lane at 72.3". The drain tee at the foot is capped, emptied by hand: no gravity
            # line reaches a receptor (the lane, the panels' working spaces and the ESS room
            # box the corner in).
            elevations=(inch(-47.4375), inch(-28.4375), inch(-28.4375), inch(-31.4),
                        None, None, None, inch(-34.6275), inch(-34.8332),
                        inch(204), None),
            slope_in_per_ft=0.125,
            drains=(DuctDrain(at=pt(inch(24.625), inch(418.5)),
                              product_ref="PROD-DUCT-DRAIN-TAP-8"),),
            # ** 8", NOT 6" (owner, in the measured package). ** This is the single biggest
            # lever in the static budget and the note prices it: the discharge leg is the
            # long one on the extract chain's worst path, and area goes as d^2 while friction
            # goes as V^2, so a 6" -> 8" step takes roughly two-thirds off this term. The
            # shaft was sized for THIS diameter months before it was bought.
            # `AO-S-ERV-EA` grows 7" -> 9" to match.
            diameter=inch(8), routing=DuctRouting.CHASE, material="galvanized",
            insulation='1" closed-cell elastomeric (AP Armaflex), R-4.2, vapour-sealed', design_cfm=DU_ERV_EA,
            adjustable_elbows=(1, 4, 5)),
]
