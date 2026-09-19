# haus: editable
# Catlin MEP — the ERV on LEVEL 2: the two RM-M-MECH plenums and the thirteen radials
# that ride the FS-S-WEST truss field.
#
# The system as a whole — the machine, the home-run argument, the fan curve, the static
# budget — is documented once, in plan/mep_erv_l1.py's header. The routing declarations
# are there too. This file holds only what level 2 owns.
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
# LEVEL 2 — RM-M-MECH, the shaft closet (x 0'-0 5/8"..5'-11 3/8", y 33'-4 5/8"..35'-11 3/8").
# Wall-hung at 8'-0", under the 9'-0" plate.
#
# **Both manifolds are east of x=2'-8", and that is the whole siting argument.** The closet's
# west end is not free space. Measured off the resolved model on 2026-09-15, what stands
# there is:
#
#     DU-ERV-RISER-SUP    x  9 5/8"   y 33'-7 1/2"   full height
#     DU-S-ERV-HP-FEED    x 12"       y 33'-7 1/2"   attic standpipe off SUP's head
#     DU-ERV-RISER-EXH    x 18 5/8"   y 33'-7 1/2"   full height
#     DU-ERV-EA           x  2'-0"    y 35'-0"       full height, basement to +17'-0"
#     VR-M-RADON-VENT     x  1'-0"    y 34'-6"       radon + plumbing vent together
#     six plumbing vents  x  1'-0"    y 34'-6"       all landing on that one riser
#     nine conduits       x 1'-6"/2'-0"/2'-6", y 34'-6" (one at y=35'-3")
#
# What is left is a 39" x 31" bay along the closet's east end, and that is exactly where
# these hang. DU-ERV-OA is no longer in that list: its riser moved east to x=3'-4" on
# 2026-09-15 and now stands in the bay's own west edge, 5 1/2" clear of EQ-M-ERV-MAN-SUP's
# west end and 3'-0" below it.
#
# ** THIS BLOCK CARRIED THE PRE-REPACK ROW FOR ONE COMMIT AND IT WAS STALE THE WHOLE TIME. **
# It read "x=5", 12", 14" and 23", all on ONE line at y=33'-7 1/2"" and went on to say the
# clash between the 12" standpipe and the 14" riser "is NOT fixed here ... it is the
# re-pack's". The re-pack landed in the same session and this paragraph was never brought
# forward with it, so the file described a defect it had already corrected. The row above is
# the built one; 9 5/8"/12"/18 5/8" leaves 5/8" between HP-FEED and EXH, and HP-FEED overlaps
# SUP only across the 3/4" of z where the two are joined, which is a joint and not a clash.
#
# The supply manifold is the smaller because the main storey wants three fresh outlets while
# the extract side gathers eight wet and dry pickups off TWO storeys — the main storey's
# ceiling grilles and the second storey's floor boots open into one floor cavity, which is
# the finding that put a manifold here at all.
EQUIPMENT_ERV_MAIN = [
    Equipment(uid="NTBY655GF8", tag="EQ-M-ERV-MAN-SUP", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(3, 10), ft(34)), footprint=(inch(24), inch(8)),
              room="RM-M-MECH", type_ref="EQ-T-ERV-MANIFOLD-6",
              mount=Mount(kind=MountKind.WALL, elevation=ft(8))),
    Equipment(uid="9D1KYBNJ12", tag="EQ-M-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(4, 4), ft(35)), footprint=(inch(34), inch(8)),
              room="RM-M-MECH", type_ref="EQ-T-ERV-MANIFOLD-10",
              mount=Mount(kind=MountKind.WALL, elevation=ft(8))),
]
# ================= LEVEL 2 — RM-M-MECH RADIALS (FS-S-WEST JOIST BAY) =================
#
# Thirteen 4" radials, all `JOIST_BAY` against FS-S-WEST and all graded by
# `mep.duct_joist_bay`. Each has the same three moves and no others:
#
#   1. rise out of its own manifold port at 8'-4" above the main floor, straight up into the
#      bay field overhead;
#   2. run SOUTH down its own lane — one lane per radial, at the port's own x, so no two
#      share a line — crossing the open truss webs, which is legal because the chord-to-chord
#      opening is 8 7/8" and these are 4";
#   3. turn east or west along ONE bay centre to its terminal.
#
# **FILED ON THE SECOND STOREY, NOT THE MAIN ONE, AND THAT IS NOT COSMETIC.** These ducts run
# in FS-S-WEST's cavity, which is the second storey's floor and the main storey's ceiling.
# `resolve/mep_ducts.py::_containing_floor` matches a segment to a sibling FloorSystem *on
# the duct's own storey*, so a run filed on `main` with `floor_ref="FS-S-WEST"` gets graded
# against FS-M-WEST's joist lines instead — which sit on a different 16" phase, so every
# radial reported a straddle it did not have. Elevations are therefore second-relative:
# -20" is the manifold port at 8'-4" above the main floor, and -8 3/8" is the centreline of
# a 4" duct sitting on FS-S-WEST's bottom chord.
#
# ** THAT SECOND NUMBER WAS 1 1/2" LOW AND NOTHING GRADED IT UNTIL 2026-09-12. ** It read
# -9 7/8", derived against the truss's 108 1/8" bottom — which is the bottom of the bottom
# CHORD, not its top. The chord is 1 1/2" thick, so "sitting on the bottom chord" is an
# invert at **109 5/8"**, the floor of the 8 7/8" web window (the drain note's §3), and a
# centreline at 111 5/8" = -8 3/8" second-relative.
#
# For the twelve legs that ride a bay (every radial but BATH2, which has no east-west
# leg) the old number was harmless: a run travelling ALONG
# the members may use the full 108 1/8"..120" depth, because nothing is in the way along it.
# For the legs that run SOUTH ACROSS the trusses — which is every radial's first leg, and
# which the note below already says out loud — it put 1 1/2" of a 4" duct inside the bottom
# chord at every line it crossed. `mep.duct_joist_bay_occupancy` never saw it: that check
# asks whether the duct is DEEP enough to be a problem (4" <= 8 7/8", so no) and never
# where it sits. `mep.run_member_crossing` is the check that asks the second question, and
# it reported all thirteen.
#
# Bay centres are 8" + n*16". **Two of them are unusable and the check is what said so:**
# FO-S-STAIR's trimmers land at y=26'-0 3/8" and y=35'-5 3/8", so a duct centred on the
# 26'-0" or 35'-4" bay straddles one. The extract manifold therefore sits at y=35'-0" rather
# than 35'-4", and everything that would naturally have used the 26'-0" bay uses 24'-8".
#
# HONEST LIMITS, both real and neither graded by anything:
#   * The thirteen lanes leave the closet as TWO INTERLEAVED FAMILIES, NOT ONE 4" MODULE,
#     AND SEVEN PAIRS OVERLAP. Ten extract lanes: nine on a 4" module — x=36", 40", 44",
#     48", 52", 56", 60", 64", 68" — plus PLANT on its own at 34". On a 4" module 4" ducts
#     are TANGENT, zero clear, which is what the neck of a home-run bundle looks like off a
#     pair of manifolds in a 6'-0" closet. The three SUPPLY lanes are not on it:
#     LIVING/BED/STUDY at x=38", 46", 54" — the extract module's half-step, an 8" module
#     interleaved between its lanes. That puts seven pairs on 2" centres — PLANT/BATH1
#     (34/36), BATH1/LIVING (36/38), LIVING/VANITY (38/40), KITCH/BED (44/46), BED/BATH2
#     (46/48), SUITEBATH/STUDY (52/54) and STUDY/LAUNDRY (54/56) — and two 4" ducts on 2"
#     centres OVERLAP BY 2" (4" of radii less the 2" centre distance; it was 1" at 3").
#     They are drawn as straight lines because a lane is a straight line in this model and a
#     bundle is not; in the field the neck is dressed — a short 4" semi-rigid leg off each
#     start collar (DUCT-T-SEMIRIGID-4 is in the catalog for exactly this) lets the runs
#     pass each other before they go rigid, which is the whole reason the drawing is
#     tolerable rather than wrong.
#     **Nothing grades it.** `mep.duct_joist_bay_occupancy` pairs runs that share a bay
#     CENTRELINE, and these lanes run south ACROSS the bays; crossing runs are deliberately
#     not paired (a hanger-gap subtraction between them returns a meaningless number). It is
#     the along-bay case below that the check sees, and it reports that one UNKNOWN. If the
#     neck is ever to be modelled honestly rather than noted, the lever is a real Soffit or a
#     per-lane offset in the first 3'-0" — not a wider spacing all the way south, which would
#     move twelve terminals to buy clearance in one closet.
#   * Two pairs share part of one bay: STUDY and LAUNDRY both ride the 20'-8" bay from
#     x=4'-8" to x=14'-6", and BATH1/VANITY/KITCH all turn on 24'-8". The bay is 12 1/2"
#     clear (16" o.c. less a 3 1/2" chord), so two 4" ducts side by side leave 4 1/2" and
#     fit without argument. This is the one duct-against-duct case the engine does grade
#     outside a modeled Soffit: `mep.duct_joist_bay_occupancy` names STUDY and LAUNDRY on
#     FS-S-WEST and reports UNKNOWN — the bay is wide enough, but the model gives a run one
#     centreline per bay, so two lanes in one bay are necessarily drawn on top of each
#     other. UNKNOWN is the honest verdict; the prose is not the record of this any more.
_PORT_Z = inch(-20)
#: A 4" duct's centreline resting on FS-S-WEST's bottom chord: invert 109 5/8" (the web
#: window's floor), centreline 111 5/8", second-relative -8 3/8". See the derivation above.
_BAY_Z = inch(-8.375)

DUCTS_ERV_LEVEL2 = [
    DuctRun(uid="MRH0QZT6NN", tag="DU-M-ERV-R-LIVING", system=DuctSystem.SUPPLY,
            path=(pt(ft(3, 2), ft(34)), pt(ft(3, 2), ft(34)), pt(ft(3, 2), ft(12, 8)),
                  pt(ft(27), ft(12, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    DuctRun(uid="83MA15Q308", tag="DU-M-ERV-R-BED", system=DuctSystem.SUPPLY,
            path=(pt(ft(3, 10), ft(34)), pt(ft(3, 10), ft(34)), pt(ft(3, 10), ft(6)),
                  pt(ft(9), ft(6))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=15),
    # ** A CEILING RUN, FOUR POINTS, THE SHAPE EVERY OTHER LEVEL-2 CEILING RADIAL HAS. **
    # RM-M-STUDY is paired with a LOW extract instead (DU-M-ERV-R-LAUNDRY below), which is
    # what makes a ceiling supply work in a 148 cf box, feeding overhead by ED-M-STUDY-SPOT.
    #
    # ** IT RIDES THE 20'-8" BAY, AND THAT COSTS NOTHING BECAUSE IT IS ONE BAY. **
    # FS-S-WEST's JOISTS are at n*16", so its BAY CENTRES are at 8" + n*16" — this line read
    # the second formula onto the first until 2026-09-15, which got the right answer for the
    # wrong reason. 20'-8" is a bay centre, sitting between the joists at 20'-0" and 21'-4"
    # for the whole ride
    # from x=4'-6" to x=17'-2" — no jog, no crossing, one straight length of snap-lock pipe.
    # Stopping short of the joist at 21'-4" is also why the grille cannot sit on the
    # sconce's own 21'-5" line; the argument is on REG-M-SUP4 in plan/mep_registers.py.
    DuctRun(uid="2ZZ3MF5VAF", tag="DU-M-ERV-R-STUDY", system=DuctSystem.SUPPLY,
            path=(pt(ft(4, 6), ft(34)), pt(ft(4, 6), ft(34)), pt(ft(4, 6), ft(20, 8)),
                  pt(ft(17, 2), ft(20, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=15),
    DuctRun(uid="K04AT15S97", tag="DU-M-ERV-R-BATH1", system=DuctSystem.EXHAUST,
            path=(pt(ft(3), ft(35)), pt(ft(3), ft(35)), pt(ft(3), ft(24, 8)),
                  pt(ft(1, 2), ft(24, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    DuctRun(uid="B13Y04D9BP", tag="DU-M-ERV-R-VANITY", system=DuctSystem.EXHAUST,
            path=(pt(ft(3, 4), ft(35)), pt(ft(3, 4), ft(35)), pt(ft(3, 4), ft(24, 8)),
                  pt(ft(3), ft(24, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    # ** 24'-8" -> 22'-0" ON 2026-09-16: AT 24'-8" IT RAN THROUGH BM-M-HALL. ** The flush LVL
    # fills x=18' from y 22'-4" to 25'-10" (mep.run_through_beam). 22'-0" is the one bay south
    # of it a lane can reach without crossing STUDY's 20'-8" ride at the same z, and it crosses
    # x=18' over W-M-C3, through a 2x6 box in the bearing-line blocking. It turns at its own
    # port lane — no jog across the trusses' bearing ends, which the hole chart forbids.
    # 21'-9 3/4", with BED2 at 22'-1 3/4": the pair side by side in the bay, tangent, 2" off the
    # 21'-4" chord and 1/4" short of the beam's end. On one centreline KITCH's end would land
    # on BED2 and read as a tee (`ducts_are_joined`), hiding the pair from the bay check.
    DuctRun(uid="YEXGZK2KW2", tag="DU-M-ERV-R-KITCH", system=DuctSystem.RETURN,
            path=(pt(ft(3, 8), ft(35)), pt(ft(3, 8), ft(35)), pt(ft(3, 8), ft(21, 9.75)),
                  pt(ft(20, 10.7), ft(21, 9.75))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=6),
    DuctRun(uid="DPAS57TPCG", tag="DU-M-ERV-R-BATH2", system=DuctSystem.EXHAUST,
            # Three points, not four: this lane's x IS the terminal's, so the run rises and
            # goes straight south with no turn at the end. A fourth vertex repeating the
            # third would be a zero-length segment, and the sweep and the IFC emitter both
            # (correctly) drop one — which is a silent disagreement between the authored
            # path and the exported geometry, so it is not authored.
            path=(pt(ft(4), ft(35)), pt(ft(4), ft(35)), pt(ft(4), ft(18))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    DuctRun(uid="63W84CCNE4", tag="DU-M-ERV-R-SUITEBATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(4, 4), ft(35)), pt(ft(4, 4), ft(35)), pt(ft(4, 4), ft(19, 4)),
                  pt(ft(14), ft(19, 4))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    # ** THE ONE TWO-HEADED RADIAL IN THE HOUSE, AND THE PORT BUDGET IS WHY.
    # ** RM-M-STUDY needs a stale-air pickup. It cannot have its own lane:
    # EQ-M-ERV-MAN-EXH is an EQ-T-ERV-MANIFOLD-10 and all TEN of its ports are spoken for —
    # BATH1, VANITY, KITCH, BATH2, SUITEBATH, LAUNDRY, MUD, BED1, BED2, PLANT. There is no
    # -12 in the catalog, and the closet bay these hang in is 39" x 31" already holding a
    # 24" box and a 34" one, so a second extract manifold is not a thing that fits either.
    # The owner's own suggestion is the answer: give one radial two heads.
    #
    # ** REG-M-RET3 IS NOW A MID-RUN TAP, NOT THE END OF THE LANE. ** It sits on the fourth
    # vertex and the run carries on past it to RM-M-STUDY. Physically that is a two-port
    # grille plenum — the standard radial fitting, one spigot to the grille and one through
    # — not a sheet-metal tee cut into a trunk, so it costs a box and no fabrication.
    #
    # ** OF THE THREE PICKUPS THAT COULD HAVE SHARED, THE LAUNDRY IS THE RIGHT ONE, AND THE
    # REASON IS ACOUSTIC. ** DU-M-ERV-R-BATH2 already dead-ends at (4'-0", 18'-0") and would
    # have reached the study's wall along the 18'-0" bay with no jog at all — a shorter,
    # simpler route. It is the wrong one: a shared duct is a crosstalk path in both
    # directions, and the room at this end of it is a CALL BOOTH. RM-M-BATH2 is occupied and
    # wants privacy of its own; RM-M-LAUNDRY is a 4'-3" closet behind a door, unoccupied,
    # and taking a 5 cfm trickle. Fifteen feet of 4" snap-lock and four bends to a laundry
    # closet is the cheapest neighbour this booth could have been given.
    #
    # ** THE FLOW IS WHAT CAPS THE STUDY AT 10 cfm. ** 5 + 10 = 15 cfm on the shared length,
    # ~25 m3/h, and a 4" run is used to 50 cfm here (DUCT-T-GALV-4.max_cfm, a 600 fpm quiet
    # limit rather than a pressure one). The room is 15 cfm supply / 10
    # extract on purpose (booth stays positive — see REG-M-RET-STUDY), but the headroom to
    # take it to a balanced 15/15 later is only about 2 cfm, not 5. Anything past that is a
    # second lane, and there is no port for one.
    #
    # ** AND IT IS ALREADY AT THE SMALLEST SIZE THERE IS HERE. ** The owner asked whether a
    # small room could take a smaller duct: every radial in this house is one 4" SKU
    # already. The step below it (51 mm) would put 10 cfm at ~450 fpm in a tube ten inches
    # from a seated occupant's feet, against ~115 fpm at 4" — in the one room built to be
    # quiet, downsizing is the expensive direction.
    #
    # ** ONE CORNER, NOT THREE, ON A TWO-HEADED RUN WHOSE WHOLE RISK IS ACCUMULATED BEND
    # LOSS. ** REG-M-RET-STUDY sits at 14'-6" (out from under FURN-M-STUDY-DESK-LEAF's
    # stowed envelope — the argument is on the register), so the radial turns south once
    # and drops there. South from the 20'-8" bay cuts the joists at 20'-0" and 18'-8", legal
    # because FS-S-WEST is open-web with an 8 7/8" chord opening, clear of the trusses' east
    # bearing at W-M-C2/C3. -108" is storey-relative on the `second` datum (+10'-0"), i.e.
    # 12" above the main floor.
    DuctRun(uid="ANSKB7EGDH", tag="DU-M-ERV-R-LAUNDRY", system=DuctSystem.RETURN,
            path=(pt(ft(4, 8), ft(35)), pt(ft(4, 8), ft(35)), pt(ft(4, 8), ft(20, 8)),
                  pt(ft(10, 6), ft(20, 8)), pt(ft(14, 6), ft(20, 8)), pt(ft(14, 6), ft(18)),
                  pt(ft(14, 6), ft(18))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z, _BAY_Z, _BAY_Z,
                        inch(-108)),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=8),
    DuctRun(uid="YFDV1TGN1W", tag="DU-M-ERV-R-MUD", system=DuctSystem.RETURN,
            path=(pt(ft(5), ft(35)), pt(ft(5), ft(35)), pt(ft(5), ft(31, 4)),
                  pt(ft(4, 0.4), ft(31, 4))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=5),
    DuctRun(uid="164777V9JK", tag="DU-M-ERV-R-BED1", system=DuctSystem.RETURN,
            path=(pt(ft(5, 4), ft(35)), pt(ft(5, 4), ft(35)), pt(ft(5, 4), ft(14)),
                  pt(ft(29), ft(14))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=5),
    # ** IN THE 22'-0" BAY SINCE 2026-09-16, SIDE BY SIDE WITH KITCH (22'-1 3/4"). ** At 23'-4"
    # its east leg ran through BM-M-HALL (see KITCH above). Two 4" ducts in the 12 1/2" clear
    # bay fit. The cost is known: on 2026-09-12 a 4" duct at 22'-0" closed the last lane
    # `haus route` had for PR-M-S-SUITE-TUB-DRAIN. The authored drain is unchanged and checks;
    # only its re-derivation loses slack.
    DuctRun(uid="2QHYF71DBS", tag="DU-M-ERV-R-BED2", system=DuctSystem.RETURN,
            path=(pt(ft(5, 8), ft(35)), pt(ft(5, 8), ft(35)), pt(ft(5, 8), ft(22, 1.75)),
                  pt(ft(29), ft(22, 1.75))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=5),
    # THE PLANT ROOM'S EXTRACT. It keeps the DU-S-PLANT-EXH/DU-A-ERV-R-PLANT uid.
    #
    # ** IT IS DOWN HERE BECAUSE THE ATTIC'S DECK CHASE IS A FINISHED BEDROOM. ** Off
    # EQ-A-ERV-MAN-EXH it would run the x=1'-0" chase 21'-8" down the base of RM-A-STUDIO's
    # west knee wall. Down here it never enters the attic at all.
    #
    # ** THE TRUSSES ARE WHY THIS WORKS AND FS-ATTIC IS WHY IT DID NOT. ** Both floors span x,
    # so a north-south run crosses every joist in either — but FS-S-WEST is 11 7/8" OPEN-WEB
    # TRUSS, chosen (params/second_deck.py) precisely "so every second-floor plumbing stack,
    # supply riser and the radon/plumbing chase can cross the deck through the webs instead of a
    # soffit or chase". FS-ATTIC is I-joist, where the same crossing means ~16 bored webs, all
    # of them within a foot of the joists' west bearing, which is the one place the hole chart
    # does not allow.
    #
    # ** THE x=2'-10" LANE IS CHOSEN, NOT INHERITED. ** Going south there crosses exactly ONE
    # sibling radial (DU-M-ERV-R-BATH1's westward leg at y=24'-8", x 1'-2"..3'-0"). The obvious
    # lane at the manifold's east end, x=6'-0", would have crossed EIGHT. It is the tenth and
    # LAST free port on EQ-M-ERV-MAN-EXH, which is now full at 10 of 10.
    #
    # East leg at y=4'-8" (56" = 8 + 3 x 16, a bay centre) runs ALONG the trusses and is clear
    # of everything: no sibling radial reaches south of y=6'-0" except DU-M-ERV-R-BED, which
    # terminates at (9'-0", 6'-0").
    #
    # ** IT IS A HIGH TERMINAL. ** Humid air
    # stratifies, so the wettest air in RM-S-PLANT is the air overhead. The grille is not in
    # the ceiling — this duct is below the room, not above it — so it rises inside
    # W-S-C1 and discharges at 8'-6", six inches under the 9'-0" ceiling. W-S-C1 is
    # PLANT_INT_2X6_BRG_HUMID at 7.43": a 5 1/2" cavity, room for a 4" riser AND a
    # vapour-tight boot through the liner. W-S-PS1, the room's north wall, is 2x4 and is not.
    #
    # ** IT IS LONGER, NOT SHORTER: 55'-8" against the attic route's 47'-5". ** 45'-6" of plan
    # run plus a 9'-4" rise from the truss bottom chord to the grille, which is the part an
    # eyeballed estimate misses. That is affordable and it is worth saying why: HVI certifies
    # this machine at 206 cfm net supply at 0.4" w.g. (B210E75RT, HVI 2004940), so the "0.2"
    # w.g." this file quotes elsewhere is the model-name point off the fan curve, not the rating
    # point, and the real static budget is about double what those comments assume. This is
    # ** NO LONGER THE RADIAL WHOSE DROP THE INSTALLER MUST CHECK (2026-09-15). ** It was,
    # at 25 cfm: 0.0301 in. of duct plus 0.0424 through the RH damper, 16% of the whole
    # extract path and the governing radial in notes/erv_static_budget.md §6. The extract side
    # was rebalanced from 265 cfm to the machine's 210 and this room went to 5 cfm — the owner
    # wants it holding its own atmosphere on a slow turnover, not flushed — and a 5x cut in
    # flow is a 25x cut in friction, so both terms fell to about a thousandth. It is still the
    # longest radial on this manifold; that was never what made it matter.
    # -20" is the manifold port, -8 3/8" a 4" duct on the truss bottom chord.
    # ** THE RISER MUST NOT STAND IN D-S-PLANT'S CLEAR OPENING, AND `mep.duct_joist_bay`
    # DOES NOT CATCH IT. ** That door is centred on y=4'-0" in W-S-C1 with its jacks at
    # y=2'-8 1/4" and y=5'-3 3/4", so a riser at y=4'-8" would stand 7" inside the north
    # jamb: through the bearing wall's sole plate, 78 1/2" of bare 4" duct standing free in
    # the rough opening with nothing to strap it to and the leaf swinging through it, then a
    # 3" bore through a solid 2-ply 2x8 header. `mep.duct_joist_bay` grades the bay and never
    # asks what the riser stands in, so it would PASS.
    #
    # The fix is one bay north, and it is nearly free. y=7'-4" (88" = 8 + 5 x 16) is a truss
    # bay centre AND a stud bay centre in the same wall — the coincidence this file already
    # leans on at y=4'-8" — so the duct rides the bay east and stands up between the studs at
    # y=80" and y=96", clear of the door's kings at 65 1/4" and of ED-S-PLANT-SW one bay
    # south, at 53'-0" developed length: still W-S-C1, still the 5 1/2"
    # PLANT_INT_2X6_BRG_HUMID cavity that takes both the riser and a vapour-tight boot, still
    # a high sidewall terminal at 8'-6" for the stratification reason above. Supply/extract
    # throw across the room is 11'-7 1/2".
    #
    # The alternative bay, y=2'-0" south of the door, is 2'-8" LONGER and lands the riser in
    # the same stud bay as ED-S-PLANT-SW-TIMER's gasketed box — a 4" duct and a 2 1/2" box in
    # a 5 1/2" cavity is worse than zero clearance, and no check in the engine grades duct against device.
    #
    # There is no legal riser at y=4'-8" at all: the jacks, the full-width header and the one
    # cripple at y=49" between them leave no station in the opening, so jogging inside the
    # cavity at +8'-6" does not rescue it either. The register had to move with the riser.
    DuctRun(uid="CWMB7Q4E3W", tag="DU-M-ERV-R-PLANT", system=DuctSystem.EXHAUST,
            path=(pt(ft(2, 10), ft(35)), pt(ft(2, 10), ft(35)),
                  pt(ft(2, 10), ft(7, 4)), pt(ft(18), ft(7, 4)),
                  pt(ft(18), ft(7, 4))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _BAY_Z, inch(102)),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=5),
]
