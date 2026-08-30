# haus: editable
# THE WEST ATTIC: an open stair volume and a guest studio (2026-08-29).
#
# Two changes at once, and the first one is the one to read first.
#
# ** THE VOID. ** FS-ATTIC used to deck the whole 36'x36' footprint, so the ST-M2S well and the
# hall band south of it were capped by a flat 5/8" gypsum ceiling at 9'-0". FO-A-HALL takes that
# deck away over x 10'-0"..18'-0", y 22'-6 3/8"..35'-5 3/8", and the stair hall runs open to the
# roof underside instead — 9'-0" at the void's west edge, ~20'-4" at the ridge.
#
# ** THE STUDIO. ** The rest of the west loft was 598 sf that nothing used, and
# plans/cost-options.md records why finishing it is worth doing: the attic is the cheapest square
# footage in the building, $69-125/sf against $138-289/sf house-wide. It becomes a guest suite —
# bedroom, bathroom, wet bar — specified as cheaply as the code allows. NOT an apartment: THERE IS
# NO COOKING APPLIANCE, deliberately, and that is the whole IRC R302.3 argument (see the wet bar in
# plan/fixtures.py). The engine has no R302.3 rule at all, so that argument lives in comments and in
# the permit narrative: write it down or it is not made.
#
# WHY ONE FILE FOR TWO STOREYS. The change straddles them — the opening and its partitions are
# attic elements, the beam that lets the opening exist is a second-storey one — and both host files
# are already past AGENTS.md's 500-line rule (attic.py 565, second.py 894). plan/mep_erv.py is the
# precedent for one file feeding two storeys, so this exports two lists and plan/manifest.py splices
# each into the right one. THE SPLIT HALVES (W-A-C2B, W-A-N2B, W-A-W1B) DELIBERATELY STAY IN
# attic.py beside their siblings — nobody reading a line should have to look in two files for a
# segment of it — and RB-HOUSE.bearing_refs sits right there with them.
from typehaus import (
    Alarm,
    AlarmKind,
    Beam,
    Door,
    FloorOpening,
    FloorOpeningPurpose,
    FollowRoof,
    Node,
    Occupancy,
    Room,
    StructuralRole,
    ToRoof,
    Wall,
    from_node,
    ft,
    pt,
)

# ============================== SECOND STOREY =========================================
# THE HALL-STUB BEAM. Between y=22'-4" and y=26'-4" the x=10'-0" line has no wall under it, and it
# can never have one: that 4'-0" gap is the mouth of the hall stub you stand in to open D-S-BATH1
# (hosted on W-S-BD-N1B at y=26'-4"). A partition there seals the hall bath off from the landing.
# So the cut ends of the attic joists land on a beam.
#
# 3-1.75x11.875 LVL, AND THE PLY COUNT IS A BEARING-WIDTH DIMENSION, NOT A BENDING ONE. The demand
# is trivial — a 4'-0" span picking up a 10' half-span of 11 7/8" I-joist field plus the attic
# partition over it, ~600 lb all told, which two plies carry many times over. But two plies is 3.5"
# wide and W-A-BA-E's 4.77" sole plate standing on it would overhang 0.65" each side. Three plies is
# 5.25" and is the same section as BM-S-HALL — one LVL depth on the job. Do not "optimise" it back.
#
# top_elevation=ft(20) is flush with the attic joist datum, exactly as BM-S-HALL: the vanity hall
# stub below keeps an unbroken 9'-0" ceiling and the cut joists land ON the beam rather than beside
# it. That is also what makes them HANG in it — see test_hardware_takeoff.py's flush-beam list.
SECOND_ELEMENTS = [
    # A bare tee on W-S-SN3, NOT a split of it. `resolve/rooms.py` nodes the linework with
    # `unary_union` before `polygonize`, so a node standing on a wall's axis closes the face without
    # the wall being cut — and test_condition_gates.py asserts the SN1 -> SN2 -> SN3 collinear run
    # and its assemblies verbatim. (The ATTIC tees below DO need real splits; a junction solver is a
    # different consumer from a room polygonizer.)
    Node(uid="547NS6BXQJ", tag="N-S-BA-S", position=pt(ft(10), ft(22, 4))),
    # bearing_refs names only the NORTH end (W-S-BD-N1B, W-S-BA-E1B — the x=10' bearing line's
    # own two segments). The SOUTH end sits at N-S-BA-S, on W-S-SN3's run, but does not bear on
    # it: this beam's own tiny reaction (~600 lb, and RM-A-POCKET above is STORAGE, not a
    # habitable live load) is the ordinary case of a header hung by joist hanger into the
    # doubled trimmer that already closes FO-A-HALL's south edge (see the FloorOpening below —
    # that trimmer runs the whole 8' from x=10' to x=18' regardless of what this beam does), so
    # it rides that joist to wherever IT bears rather than pushing a new point load down through
    # W-S-SN3. W-S-SN3 was BEARING from 2026-08-29 to 2026-08-30 on the opposite read of this;
    # see that wall's own comment in plan/storeys/second.py.
    Beam(uid="P77WQJ1MFM", tag="BM-S-BATH-E", start_node="N-S-BA-S", end_node="N-S-BA1",
         size="3-1.75x11.875 LVL",
         bearing_refs=("W-S-BD-N1B", "W-S-BA-E1B"),
         assembly="BEAM_LVL", top_elevation=ft(20)),
]

# ================================= THE VOID ===========================================
# One FloorOpening, and every one of its four edges is on a line chosen against the resolver rather
# than the obvious one:
#
#   minx 10'-0"     the wall AXIS. This is a header edge where joists are cut, and every bearing cut
#                   in the house is at an axis (resolve/floors.py). A 6.77" wall centred on x=10'
#                   leaves the cut joist 3.4" of plate against `_MIN_BEARING_IN` = 1.5".
#   maxx 18'-0"     the centreline axis; W-A-C2B stands on it and BM-S-HALL is under it.
#   miny 22'-6 3/8" the NORTH FACE of W-A-HALL-S, not its 22'-4" axis. A trimmer edge follows the
#                   finished face — FO-S-STAIR's own idiom — and on the axis the partition would
#                   hang 1.15" out over the hole.
#   maxy 35'-5 3/8" W-A-N2's inside gwb face, the same line FO-S-STAIR uses. At 36'-0" the opening
#                   swallows the last joist line and throws the trimmer pair outside the sheathing
#                   plane (structural.member_interference).
#
# purpose=STAIR, EXPLICITLY. `code.R312_1_guard` filters on exactly that, and
# `code.R312_1_guard_height` walks only `deck_outline` and never `deck_voids` — so with CHASE this
# void would get NO fall-protection check at all. STAIR is also honest: it is the ST-M2S well
# continued to the roof.
#
# bearing_refs closes both long edges CONTIGUOUSLY, which is what the edge test demands: x=10' is
# BM-S-BATH-E 22'-4"->26'-4", W-S-BA-E1B 26'-4"->33'-4", W-S-BA-E 33'-4"->36'; x=18' is BM-S-HALL
# 22'-4"->30'-10", W-S-C4B 30'-10"->36'. (Naming a Beam here only began working on 2026-08-29 —
# `_opening_edge_has_declared_bearing` used to look at `model.wall(tag)` alone and put a 13'-1"
# header under a beam that plainly carries it.) W-S-SN3 IN THIS TUPLE IS THE MINY EDGE, NOT A
# THIRD NAME FOR THE X=10' EDGE — `_opening_edge_has_declared_bearing` is purely geometric (does
# a ref's axis/footprint run along and cover the edge), so it does not care whether W-S-SN3 is
# itself BEARING; the wall's footprint covers y=22'-6 3/8" regardless, closing the miny edge and
# saving a redundant header there. Do not read this as the same claim as BM-S-BATH-E's — they
# cover two different edges of the same opening, and BM-S-BATH-E's own bearing_refs (above) does
# NOT include W-S-SN3.
#
# ** DO NOT ADD x=10' TO FS-ATTIC's joists.bearing_refs. ** That field is global to the deck:
# resolve/floors.py builds ONE boundaries list and cuts EVERY joist line on the storey at every one
# of them. Adding x=10' would cut all ~34 lines there, including the 17 over the suite where no wall
# stands below, and `integrity.floor_bearing_grid` would not catch it — it tests a wall's extent
# ALONG the joist axis, never across it. That is why the main deck is three FloorSystems.
#
# The joists run in x, so the resolver clips them at x=10' and x=18' and generates the doubled
# trimmer pair along both parallel edges by itself. THE SOUTH TRIMMER PAIR IS THE DOUBLE JOIST
# W-A-HALL-S NEEDS, and that matters: 22'-4" = 268" is 12" off the 16" module, so nothing else in
# the model would have put a joist under that sole plate. It is the same problem W-A-SN was
# thickened to solve.
FLOOR_OPENINGS = [
    FloorOpening(uid="ASQ865WVJK", tag="FO-A-HALL",
                 outline=(pt(ft(10), ft(22, 6.375)),
                          pt(ft(18), ft(22, 6.375)),
                          pt(ft(18), ft(35, 5.375)),
                          pt(ft(10), ft(35, 5.375))),
                 purpose=FloorOpeningPurpose.STAIR,
                 bearing_refs=("W-S-SN3", "BM-S-BATH-E", "W-S-BA-E1B", "W-S-BA-E",
                               "BM-S-HALL", "W-S-C4B")),
]

# ============================== NODES =================================================
# N-A-C3, N-A-N3 and N-A-PK-W are also the split points for W-A-C2, W-A-N2 and W-A-W1 (attic.py):
# a partition teeing into an existing wall mid-span leaves resolve/topology.py's junction solver
# without the shared endpoint it needs, and the two bands' solids overlap. N-A-N3 mirrors N-S-N2 and
# N-A-PK-W mirrors N-S-W2, so the attic's north and west walls finally segment where the storey
# below already does.
#
# ** THE BATH'S TWO COORDINATES ARE CHOSEN, NOT ROUNDED, AND THEY ARE THE COST ARGUMENT. **
#   x = 9'-7 1/2" is W-S-DC2's axis — the suite bath's INT_2X6_STAGGERED_PLUMBING drain wall one
#       storey down, 5.5" of continuous cavity with NO STUD TO BORE. Every drop out of this
#       bathroom lands in it. Stacking on that wall is the entire reason the bath is at this end of
#       the studio; move this line and you buy a new riser through a finished storey.
#   y = 17'-4" = 208" = 13 x 16 is a JOIST LINE, so W-A-BATH-S gets a joist directly under its sole
#       plate — which nothing else in the attic would have given it (see W-A-STU-N below for the
#       case where there is no such luck).
NODES = [
    Node(uid="PYHBAEGXSH", tag="N-A-H1", position=pt(ft(10), ft(22, 4))),
    Node(uid="7QWR9NMMP8", tag="N-A-C3", position=pt(ft(18), ft(22, 4))),
    Node(uid="TZSDYAK26N", tag="N-A-N3", position=pt(ft(10), ft(36))),
    Node(uid="DA9SJ6F8NQ", tag="N-A-PK-W", position=pt(ft(0), ft(22, 4))),
    # ** `open_end=True`, and it is the sanctioned escape rather than a shortcut. **
    # W-A-STU-W dies into W-A-STU-N's FACE 4 1/2" west of that wall's east end, so this node
    # carries one wall edge and `integrity.wall_loop_open` is an ERROR without the flag (its
    # own fix_hint names it). The alternative is splitting W-A-STU-N here, which would leave
    # a 4 1/2" second segment nobody can build. The room face still closes: `resolve/rooms.py`
    # nodes the linework with `unary_union` before `polygonize`, so an endpoint lying ON
    # another wall's line closes the polygon whether or not that wall is cut. Frame it as
    # W-A-VE/W-A-VN are framed — a free end tied to blocking in the through wall.
    Node(uid="03RVD22JMV", tag="N-A-WW-N", position=pt(ft(9, 7.5), ft(22, 4)),
         open_end=True),
    Node(uid="AM6103KT7M", tag="N-A-WW-S", position=pt(ft(9, 7.5), ft(17, 4))),
    Node(uid="CJ7WYX7XT3", tag="N-A-BW-E", position=pt(ft(18), ft(17, 4))),
]

# ============================== WALLS =================================================
# Five, all ToRoof, all NONBEARING. NONBEARING is a statement about the roof rather than a guess:
# RF-HOUSE is a structural ridge on x=18' bearing on the rafter PLATES at x=0/36 (2026-08-29 —
# they were 5'-0" knee walls), so the rafters span ridge -> plate and nothing needs support at
# x=10' or anywhere else in here. The plates carry no less than the knee walls did; what
# changed is that the load lands on the deck and the second-storey studs directly.
#
# ** DETAIL EVERY ToRoof TOP WITH A SLIP/DEFLECTION GAP ** so no partition picks up rafter load as
# the ridge deflects. The model has no field for it, so it lives here — exactly as it does for
# W-A-STU-N, the attic's other open-ended roof-height screen. (W-A-VE/W-A-VN were the precedent
# cited here until 2026-08-29; the 6:12 rake retired both — see plan/storeys/attic.py's WALLS.)
WALLS = [
    # VOID | POCKET. Stands on W-S-BA-E1B / W-S-BA-E and, over the 4'-0" hall stub, on BM-S-BATH-E.
    #
    # ** THE NODES ARE THE OTHER WAY ROUND SINCE 2026-08-30, AND THAT IS THE WHOLE EDIT. **
    # The framing solver lays a segment out from its START node, so which end that is decides
    # the grid. N-A-H1 sits at y=22'-4", a residue of 12" mod 16", and this wall was laying
    # out from there toward N-A-N3, which is on the grid — so every stud on it stood 12" off
    # the studs below. Starting from N-A-N3 instead puts the whole run in phase: **9 orphaned
    # studs down to 3.** No geometry moves, no check changes, and the BOM is identical — a
    # `from_node` offset is direction-independent, this wall hosts no openings, and
    # INT_2X4_PARTITION is symmetric, so reversing it is free in every sense.
    #
    # It is the highest-value edit in the stud-grid workstream and it is one line. The node
    # MOVES that were considered instead were all rejected on evidence (see
    # `haus explain module`): N-S-B1..B5 governs three walls that appear in no stack edge at
    # all, and N-S-D1..D4 is W-S-DC2's drain wall one storey down.
    Wall(uid="9WC345CCP1", tag="W-A-BA-E", start_node="N-A-N3", end_node="N-A-H1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING),
    # VOID | STUDIO (and, east of x=9'-7 1/2", void | bath).
    #
    # ** THIS IS NOT A LINE LOAD ON W-S-SN3, and it is what a reader will worry about. ** It stands
    # on the opening's doubled trimmer pair, which spans the 8'-0" from x=10' to x=18' and delivers
    # the wall to TWO POINTS — and, since 2026-08-30, neither of those two points reaches W-S-SN3 at
    # all: the trimmer is an ordinary doubled joist in the x-direction, and both the x=10' point
    # (BM-S-BATH-E, hung on it by joist hanger) and the x=18' point ride it to wherever the joist
    # itself already bears, not down through whatever wall happens to sit under a point along its
    # span. It remains true, and worth keeping, that the east half of W-S-SN3 sits over W-M-HS4 —
    # D-M-LAUN's 4'-0" pocket, which could not have taken a continuous line load at all — so even
    # the earlier (2026-08-29 to 2026-08-30) reading, which did send BM-S-BATH-E's reaction into
    # W-S-SN3, was never going to land it over the pocket.
    #
    # A 42" RAILING-INT-STAIR-GUARD (the RL-A-STAIR product at base_elevation=ft(20)) was priced
    # here instead and rejected: it satisfies R312.1 identically, cuts the trimmer's load, and turns
    # the studio's north end into a mezzanine over the double-height hall — better architecture,
    # worse separation. The studio is a SLEEPING ROOM, so separation wins.
    Wall(uid="RV6PJZ6WWM", tag="W-A-HALL-S", start_node="N-A-H1", end_node="N-A-C3",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING),
    # POCKET | STUDIO, y=22'-4", x 0..10'. With W-A-BA-E this is what makes the storage pocket a
    # closed face rather than the north end of a bedroom.
    #
    # FRAMING NOTE, and it is W-A-SN's: y=22'-4" is 268", which is 12" off FS-ATTIC's 16" module, so
    # there is no joist under this sole plate. East of x=10' the void's own trimmer pair solves
    # that; west of it nothing does. SOLID BLOCKING BETWEEN JOISTS under the full length of this
    # plate. (Contrast W-A-BATH-S, which was put on a joist line precisely to avoid this.)
    #
    # N-A-WW-N stands on this wall 4 1/2" west of its east end, where W-A-STU-W tees in. It is a
    # bare tee and the wall is NOT split for it: rooms polygonize off noded linework, so the face
    # closes, and a 4 1/2" second segment would be a stick nobody can build.
    Wall(uid="3TKS0Y8EH7", tag="W-A-STU-N", start_node="N-A-PK-W", end_node="N-A-H1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING),
    # ** THE WET WALL — the only 2x6 in this suite, and the reason the bath is where it is. **
    # INT_2X6_STAGGERED_PLUMBING gives the 5.5" cavity `preferences.toml`'s
    # `drain_stack_required_structure_in` wants behind a stack, and gives it with STAGGERED studs,
    # so the drop passes without a single stud bored. It stays NONBEARING, which is exactly what
    # `structural.wet_wall_bearing` wants of a staggered wall — it PASSes it as "non-bearing
    # staggered — continuous cavity, no bored studs". (Contrast the x=10'-0" line one storey down,
    # which had to go the other way on the same day: see plan/assemblies.py.)
    #
    # Everything that drains in this suite is on this wall — the water closet, the lavatory and the
    # shower on its east face, the wet-bar sink back-to-back on its WEST face — so one stack, one
    # vent and one cavity serve the whole storey addition.
    Wall(uid="ZEF56D047J", tag="W-A-STU-W", start_node="N-A-WW-S", end_node="N-A-WW-N",
         assembly="INT_2X6_STAGGERED_PLUMBING", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING),
    # STUDIO | BATH, y=17'-4" — a joist line (208" = 13 x 16), so this plate has a joist under it
    # and needs no blocking. Hosts D-A-STUBATH.
    Wall(uid="REREWJKFAZ", tag="W-A-BATH-S", start_node="N-A-WW-S", end_node="N-A-BW-E",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING),
]

# ============================== OPENINGS ==============================================
# Both leaves are DT-INT-SWING30, the house's standard 2'-6" interior door and what all three
# second-storey baths already use. R311.2's 32"-clear rule governs the EGRESS door, not these.
OPENINGS = [
    # Into the storage pocket, and its station is set by HEADROOM. W-A-STU-N is raked: it runs in x
    # under the west half of the gable, and since 2026-08-29 the roof underside there is
    #
    #     H(x) = 1 1/2" + x/2
    #
    # above the attic deck. ** THIS DOOR SHRANK RATHER THAN MOVED, AND IT HAD TO. ** It was a
    # 6'-8" DT-INT-SWING30 at x 6'-6"..9'-0", derived when the rake was 5'-0" + x/3 and gave
    # 7'-2"..8'-0" there. The same stations now give 4'-9" to 6'-0", and a 6'-8" head plus its
    # header needs 2 x (80 + 2) = 13'-8" of x — which this 10'-0" wall does not have ANYWHERE.
    # There is no station on W-A-STU-N that takes a full-height leaf.
    #
    # So it becomes a low ACCESS door: DT-INT-ACCESS24, 2'-0" x 3'-0", whose head needs
    # 2 x (36 + 2) = 76" and sits at x 6'-4"..8'-4" — with 5'-1 1/2" of rake over its east
    # jamb and 3'-11 1/2" over its west one, and 1'-3 1/2" clear of W-A-STU-W's tee studs at
    # x 9'-4 3/4". Going taller is what forces it east into that tee. `structural.member_interference` is the rule that decides this
    # — it named the old jacks and header coming out through the raked top plate the moment the
    # pitch changed, exactly as it did on this door's first attempt in 2026-08.
    #
    # It is still a DOOR and not a scuttle because this pocket is the ERV's service access — the
    # manifold EQ-A-ERV-MAN-EXH, the outdoor-air hood and VR-M-RADON-VENT's head all sit inside
    # it, and IRC M1305.1.3 wants a passageway, a platform, a light and a receptacle at the
    # appliance (hence ED-A-POCKET-LT1 and ED-A-POCKET-RC1). M1305.1.3's passageway minimum is
    # 30" high x 22" wide, so 24 x 42 clears it with room; the door is SMALLER but not
    # sub-code. `code.R807_1_attic_access` is storey-level and is satisfied by ST-S2A either way
    # — walling off the pocket CANNOT make that rule fail — so the leaf size is a buildability
    # call, not a code one.
    Door(uid="Y3R3YMXFVJ", tag="D-A-POCKET", host="W-A-STU-N", type_ref="DT-INT-ACCESS24",
         position=from_node("N-A-PK-W", ft(7))),
    # Into the bath off the studio. `flip_hinge` parks the leaf against the wall, clear of the
    # shower's SW corner.
    #
    # ** IT MOVED 2" WEST AND ITS SWING WAS SETTLED BY ELIMINATION ON 2026-08-29. ** Three
    # arrangements were tried and `integrity.door_swing_conflict` / `mep.pocket_occupancy`
    # decided between them:
    #   * INWARD, into the bath, sweeps FX-A-STUBATH-SH. The 36" pan is already in the NE
    #     corner — 16'-2 5/8"/20'-7 5/8" is the maximum x and y the bath box allows — and the
    #     door cannot move far enough west to miss it, because the 6:12 rake needs its low
    #     jamb at x >= 13'-8".
    #   * A POCKET has nowhere to go either way: 18" short of cavity to the east, and to the
    #     west the cavity is where PR-A-STUBATH-DRAIN, PR-A-CW/HW-STUBATH and
    #     PR-S-SUITEBATH-VENT all cross W-A-BATH-S. `mep.pocket_occupancy` named all four.
    #   * OUTWARD, into the studio, is what is left, and it works with 2" to spare once the
    #     leaf moves from x 14'-0" to 13'-10" — the arc then stops at 16'-4", clear of
    #     FX-A-STUDIO-BAR-SINK's 16'-5". APPL-A-STUDIO-FRIDGE moved south with it (see
    #     plan/placeables.py); the sink, its drain, its vent and its GFCI did not move.
    #
    # ** IT ALSO MOVED EAST ON THE SAME PASS, 11'-3 5/8" -> 13'-10" (leading jamb), FOR THE
    # RAKE ITSELF. ** W-A-BATH-S runs in x from 9'-7 1/2" to 18'-0" and the 6:12 underside is
    # `1 1/2" + x/2`, so a 6'-8" head plus its header needs 2 x (80 + 2) = 13'-8" of x at the
    # LOW (west) jamb. It stood at 11'-3 5/8", where there are only 5'-9 1/2", and the header
    # came out through the raked plate. At 13'-10" there are 7'-0 1/2" — 2" of margin — and
    # the leaf ends at 16'-4", clear of N-A-BW-E. This is also the move the bath wanted
    # anyway: the fixtures went east into the tall half on the same pass (plan/fixtures.py),
    # so the door now opens onto them rather than into the low strip behind them.
    Door(uid="ENHDGC87MN", tag="D-A-STUBATH", host="W-A-BATH-S", type_ref="DT-INT-SWING30",
         position=from_node("N-A-WW-S", ft(4, 1)), flip_hinge=False, flip_swing=True),
]

# ============================== ROOMS =================================================
# ** RM-A-STUDIO KEEPS uid CAR401AAAA. ** This is RM-A-WEST-UNFIN retagged and re-occupied, not a
# new room, so the IFC GlobalId follows it — the D-A-STUDY/DT-INT-BOOKCASE30 retype-in-place is the
# precedent. It moved out of attic.py and into this file with the rest of the suite, and that is
# safe for the same reason: a uid follows the ELEMENT, not the file it is authored in.
#
# Occupancy.BEDROOM is load-bearing four times over: it is what pulls IRC R310 in (PASSing on
# WIN-A-S-JUL-W with nothing added — WT-2764's raw opening is 27" x 64" = 12.0 sf against 5.7),
# what `_whole_house_ventilation_rate` counts, what makes R314/R315 want an alarm inside AND one
# outside, and what makes `electrical.receptacle_spacing` evaluate this room at all.
#
# ** LEAVE ALL THREE AT THE `NORMAL` HUMIDITY DEFAULT. ** Every other bath in the house is NORMAL;
# only RM-B-SAUNA is WET. Setting WET here would pull CATLIN_ROOF into the humid-room condensation
# walk on a hot roof, and would demand a vapour liner and non-paper board on all five bounding
# surfaces — a new building-science surface bought for nothing, on a shower one storey above three
# identical NORMAL ones. It was authored WET first and taken back out; do not "fix" it again.
#
# The pocket keeps `conditioned` at its default True — it is inside the hot-roof envelope. Setting
# it False would buy back ~3.9 cfm of whole-house ventilation margin if that ever gets tight.
ROOMS = [
    # Seed moved (9'-0", 20'-0") -> (7'-0", 8'-0"): the old point is now 4" west of the wet bar's
    # back wall. R305 PASSES on the sloped path and the margin is worth writing down: the rule needs
    # >=50% of the floor at 7'-0" and NO habitable area below 5'-0". The roof underside is
    # 5'-0" + x/3, so 7'-0" arrives at x=6'-0" and 12' of the 18' width clears it — 67%. The STORAGE
    # loft was already in scope for this rule (only UNCONDITIONED and GARAGE are out) and already
    # passed; the studio is a subset of the same x range and grades the same.
    #
    # `floor_finish=None` IS THE CHEAP MOVE AND IS HOW YOU SAY IT. FS-ATTIC's deck is already
    # `plywood-underlayment-sanded`, specified that grade PRECISELY because these rooms walk on it.
    # `takeoff/finishes.py` then skips the room entirely — no carpet, pad, tack strip or SF ordered
    # — while the room still appears on the schedule as a None row, so the area is not silently
    # missing. Two honest caveats: a sanded plugged panel is WALKABLE, not FINISHED (unsealed it
    # greys, stains and telegraphs its joints, hence the `finish-studio-floor-sealer` allowance),
    # and the priced alternative is one word — `floor_finish="carpet"`, ~357 SF at $3.35 ~ $1,200.
    # Present it to the owner that way rather than deciding it here.
    Room(uid="CAR401AAAA", tag="RM-A-STUDIO", seed=pt(ft(7), ft(8)),
         occupancy=Occupancy.BEDROOM, floor_finish=None,
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
    # ** THE TAG IS `RM-A-STUBATH`, NOT `RM-A-STUDIO-BATH`, AND THAT IS NOT COSMETIC. **
    # `electrical.room_lighting` matches devices to a room by NAME — `ED-{room.tag[3:]}-*` — so a
    # bath called RM-A-STUDIO-BATH would have its devices prefix-match RM-A-STUDIO as well, and the
    # two rooms' luminaire sets would silently merge. The three prefixes ED-A-STUDIO-,
    # ED-A-STUBATH- and ED-A-POCKET- must stay disjoint.
    #
    # `vinyl-sheet` is already the house's cheap waterproof answer (RM-M-BATH1, RM-M-LAUNDRY, the
    # main hall band): no grout, no backer, no threshold. R305 is not close here — across
    # x 9'-10 7/8"..17'-8 5/8" the roof underside runs 8'-3" to 11'-0" and 100% of the floor clears
    # 7'-0".
    Room(uid="ACQ0FY2BZD", tag="RM-A-STUBATH", seed=pt(ft(13), ft(20)),
         occupancy=Occupancy.BATHROOM, floor_finish="vinyl-sheet",
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
    # Occupancy.STORAGE keeps this out of `_HABITABLE`, which is what keeps R210.52 receptacle
    # spacing and the R303.1 glazing rule off a room nobody occupies.
    Room(uid="17XB5CH977", tag="RM-A-POCKET", seed=pt(ft(5), ft(30)),
         occupancy=Occupancy.STORAGE, floor_finish=None,
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
]

# ============================== ALARMS ================================================
# ** TWO ALARMS, AND GETTING THE PAIR ROUND THE WRONG WAY IS A FAIL. **
# `code.R314_R315_alarms` needs an alarm IN the bedroom AND a second on the same storey in a
# NON-SLEEPING room; `code.R315_co_every_sleeping_area` FAILs outright if every CO alarm on the
# storey is inside a bedroom. AL-A-COMBO was filed in RM-A-WEST-UNFIN — if it merely followed the
# retag it would satisfy the first half and fail the other two. So it moves to RM-A-STUDY (in
# attic.py, uid kept: the stair head, literally the "immediate vicinity of the bedrooms, outside the
# separate sleeping area" R315.3 describes) and this new one takes the bedroom.
#
# COMBO to match AL-S-BED1/2/3, and CKT-LT-BACKUP because every alarm in the house is on that
# always-on circuit — R314.4 FAILs an alarm naming no circuit.
ALARMS = [
    Alarm(uid="PFWCRKMZJZ", tag="AL-A-STUDIO", kind=AlarmKind.COMBO, room="RM-A-STUDIO",
          circuit="CKT-LT-BACKUP"),
]

# With all four sides walled, `code.R312_1_guard` grades the void's edges against attic-storey walls
# and returns PASS — "walls close the well". No railing, no `Wall.guard`. THE ONE THING THE MODEL
# CANNOT SAY: until these partitions are stood there is a ~109 sf hole with a 9'-0" drop in the
# middle of the attic deck. That is a job-site guard and a sequencing note, not an element.
ATTIC_ELEMENTS = [*NODES, *WALLS, *OPENINGS, *FLOOR_OPENINGS, *ROOMS, *ALARMS]
