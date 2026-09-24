# haus: editable
# Catlin MEP — the ERV on LEVEL 3: the attic extract plenum, the mixing box it does not
# feed, the four FS-ATTIC radials and the mixing-box feed.
#
# The system as a whole is documented once, in plan/mep_erv_l1.py's header; the routing
# declarations are there too. EQ-S-ERV-MIX is second-storey equipment and is filed here
# because DUCTS_ERV_MIX_FEED is the only thing that reaches it.
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
# LEVEL 3 — sitting ON the FS-ATTIC deck beside the chase head at (1', 35'-1.3"), fully
# accessible in RM-A-POCKET.
#
# ** THE MANIFOLD IS AT x=5'-0", AND M1305.1.3 IS WHY. ** At 6:12 off a rafter plate the
# roof underside is `1 1/2" + x/2`, so the code's passageway (not less than 30" high, with
# a level working space in front) governs the station: 5'-0" gives 31 1/2" at the box and
# 46 1/2" at the far side of a 30" working space, so a person can crawl to it and kneel at
# it. Extract only: the level's fresh-air duty is the mixing-box feed,
# which stays a full-size 6" branch off the supply riser rather than a radial, because it
# carries ~100 of the machine's 210 authored cfm on its own (206 certified — see the header).
EQUIPMENT_ERV_ATTIC = [
    Equipment(uid="3QT1F3F01A", tag="EQ-A-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(5), ft(34, 6)), footprint=(inch(24), inch(8)),
              # RM-A-POCKET, walled off as a storage pocket in the guest studio's west loft;
              # D-A-POCKET is a door rather than a scuttle precisely so this stays
              # serviceable.
              room="RM-A-POCKET", type_ref="EQ-T-ERV-MANIFOLD-6-EXH",
              mount=Mount(kind=MountKind.FLOOR)),
]
# THE MIXING BOX — inside SF-S-HP1, in the return chamber at the air handler's return
# face, which is the one place in this loop where fresh air may legally arrive, upstream of
# the coil, the strip heater and the unit's own filter-back grille. Injecting it anywhere
# downstream of the coil and the 2 kW strip heater would deliver 100 cfm of -15 F design
# outdoor air — half the house's fresh air — untempered.
#
# ** IT LOOKS LIKE A FITTING ONCE THE RETURN IS A PROPER PLENUM, AND A WYE WOULD NOT DO. **
# `plan/mep_registers.py` states the ERV enters the return "not a hard-coupled duct … so
# either machine can run alone", and this box is where that damper lives:
#   * AIR HANDLER RUNNING, ERV OFF — the return chamber is at negative pressure. With no
#     damper the blower pulls backwards through the 6" feed, through the attic sub-manifold
#     and out through a stopped, therefore non-recovering, ERV core and its outdoor intake.
#     A stopped ERV is not airtight. That is unrecovered -15 F air straight into the return,
#     plus depressurisation of the ERV's own ductwork.
#   * ERV RUNNING, AIR HANDLER OFF — 100 cfm enters a still chamber and leaves through
#     REG-S-HP-RET into the study, the only low-resistance path. The house still ventilates;
#     distribution to the other rooms depends on the AH fan turning. So the ERV calls the AH
#     fan: EQ-B-ERV.blower_interlock_ref (plan/electrical.py), graded by
#     mep.erv_blower_interlock. It matters
#     because code.N1103_6_whole_house_ventilation is already tight, 210 cfm provided against
#     205 required. (At the 206 cfm HVI actually certifies, tighter still: 206 against 205.
#     That is the live verdict `ventilation_cfm` moves, and why the field is left at 210
#     pending a deliberate decision — see plan/mep_erv_types.py.)
# Keeping it costs the second lane past the machine, which SF-S-HP1's width already carries.
#
# ** IT IS THE RETURN PLENUM NOW, NOT A BOX BESIDE THE RETURN (2026-09-04). ** It fills the
# east lane of SF-S-HP1 from the box's south end to the air handler's south face —
# x 20'-5 1/2"..21'-5 1/2", y 27'-10 1/2"..30'-4", z on the cavity floor and 18" tall — and
# REG-S-HP-RET's whole 336 in2 face is inside it. What that replaced: a 10 x 12 box with a
# 30 x 16 ceiling grille lapping it, the return duct and 120 in2 of bare soffit cavity all at
# once. A return drawing a quarter of its face out of a framed cavity is IMC 601.5's
# building-cavity-as-plenum; nothing in the engine grades it, and it was wrong.
#
# So the airflow is now what the drawing says it is: room air in through the grille, ERV
# fresh air in through the 6" drop and its damper, the two mixing across 29 1/2" of plenum,
# then north up DU-S-HP-RET past the cabinet to its return face. Still upstream of the coil
# and of EQ-S-HP1-STRIP, which is SOUTH of the cabinet in the discharge — the ordering that
# matters (fresh -> mix -> coil -> strip) is preserved end to end.
#
# ** IT IS ON THE RETURN AND NOT ON THE TRUNK, AND THAT IS FORCED. ** `_pair_is_plumbed`
# excuses only equipment<->duct pairs; a duct riser landing on another duct is always a
# clash. The ERV feed therefore has to land on a piece of EQUIPMENT, and this plenum is it.
#
# ** THE THREE DIMENSIONS ARE EACH A CLEARANCE, NOT A CHOICE. ** 12" across is the east lane
# less the 2" HANGER_GAP_M off DU-S-HP-SUP (which runs x 18'-9"..20'-3"), leaving 1/2" to the
# cavity's east face. 29 1/2" along stops it clear of the cabinet's south face at
# y=30'-4 1/2": overlap the cabinet along the box by even an inch and the pair is graded
# across it, where the gap is 7/8" and the check FAILs. 18" fills the 18 1/4" cavity.
EQUIPMENT_ERV_SECOND = [
    Equipment(uid="8PE9E87JX5", tag="EQ-S-ERV-MIX", kind=EquipmentKind.MIXING_BOX,
              position=pt(inch(251.5), inch(349.25)), footprint=(inch(12), inch(29.5)),
              room="RM-S-HALL", type_ref="EQ-T-ERV-MIXING-BOX",
              soffit_ref="SF-S-HP1",
              mount=Mount(kind=MountKind.CEILING)),
]
# ============================== LEVEL 3 — ATTIC RADIALS ==============================
#
# Four runs off the deck manifold at (5'-0", 34'-6"): three extracts and, separately below,
# the mixing-box feed. Each takes the boxed floor chase west to x=1'-0" and south along the
# west wall, then drops into its FS-ATTIC bay and rides it east to the terminal. `CHASE`,
# for the reason in the header — one run, two cavities, and the declaration is the honest
# one. FS-ATTIC is I-joist, so unlike level 2 there is no crossing the bays: all the
# north-south travel happens ON the deck, above the joists, where it costs nothing in DEPTH.
#
# ** THE x=1'-0" CHASE RUNS THE LENGTH OF A FINISHED BEDROOM, AND THE KNEE WALL AT ITS FOOT
# IS BARE. ** DU-S-ERV-HP-FEED turns east at y=22'-0" and reaches SF-S-HP1 up
# RM-A-EAST-UNFIN's deck instead of running the knee wall's length; DU-A-ERV-R-STUBATH's
# east leg rides the y=21'-8 1/2" bay, ALONG the joists, boring nothing; DU-A-ERV-R-PLANT feeds
# from FS-S-WEST's trusses (DU-M-ERV-R-PLANT in DUCTS_ERV_LEVEL2), rising inside W-S-C1's
# 5 1/2" cavity to a HIGH SIDEWALL grille at 8'-6" — still in the warm wet air at the top of
# the room, so the stratification argument is unaffected; only the direction the boot
# arrives from changed. ED-A-STUDIO-RC8/RC9 stay: the wall is in the 210.52 test on its own
# merits whatever is or is not lying at its foot.
#
# The remaining rejected alternative is unchanged: bore the FS-ATTIC I-joists and run
# north-south in the bays. The hole chart permits it, but at x=1'-0" every hole would fall
# within a foot of the joists' west bearing, which is the one place the chart does not — and
# that is before ~16 bored webs and a manufacturer sign-off.
#
# +4" is a 4" duct lying on the attic deck at 240". Both are attic-relative, and negative
# because the attic datum is the top of FS-ATTIC's joists.
_ATTIC_DECK_Z = inch(4)
#: ** -8 1/2", RE-DERIVED 2026-09-20; IT WAS -9 7/8", WHICH IS LEVEL 2'S OLD ERROR COPIED. **
#: A 4" duct's centreline resting on FS-ATTIC's bottom FLANGE. The band, attic-relative:
#: 240" top of joists (datum, 3/4" ply deck over it) / -1 3/8" top flange / -10 1/2" top of
#: the bottom flange = 229 1/2" absolute / -11 7/8" underside of the joists = 228 1/8" /
#: 5/8" gwb ceiling under that. So invert 229 1/2", crown 233 1/2", centreline 231 1/2" =
#: attic-relative -8 1/2".
#:
#: -9 7/8" put the INVERT at 228 1/8" — the joists' underside, i.e. lying on the ceiling
#: board, with the bottom flange beside it rather than under it. That is the same mistake
#: `_BAY_Z` in plan/mep_erv_l2.py records having corrected on 2026-09-12; only the
#: correction differs, because FS-S-WEST's floor truss has a 1 1/2" chord and FS-ATTIC's
#: 11 7/8" I-joist a 1 3/8" flange (`resolve/framing/profiles.py`). +1 3/8", not +1 1/2",
#: so this datum is level 2's neighbour and not its twin.
#:
#: It is also exactly the floor of `resolve/mep_crossings.member_window`'s i_joist window
#: (bottom + one flange), which is what a bore is graded against — so a bay leg on this
#: line and a leg that crosses a joist read the same number.
_ATTIC_BAY_Z = inch(-8.5)
# -3" is a 4" duct in the TOP of a bay, stacked over a run already lying on the bottom
# chord: 235"..239" against DU-S-ERV-HP-FEED's 228 1/8"..234 1/8", 7/8" between them and 1"
# under the deck. `mep_packing` grades a bay's width as a TIER, so two runs at different
# elevations do not share it — which is the only reason the 22'-0" bay can take a second duct
# at all (its free strip south of the 6" feed is 3 1/4", and a 4" duct does not go in 3 1/4").
_ATTIC_BAY_HIGH_Z = inch(-3)

DUCTS_ERV_ATTIC = [
    # ** THE WEST CHASE CARRIES ONE DUCT, AND THAT IS THE ROOF TALKING. ** At x=1'-0" the
    # 6:12 underside is `1 1/2" + x/2` = 7 1/2" over the deck, and a 4" duct on
    # _ATTIC_DECK_Z spans 2"..6" of it. There is no second tier at that station and there
    # never was — so the four radials, DU-S-ERV-HP-FEED and the first 41" of
    # DU-ERV-RISER-EXH were all drawn on the one line, five and six deep, and
    # `mep.run_interference` reported fourteen duct-against-duct pairs for it.
    #
    # ** THE FIX IS WIDTH, BECAUSE SOUTH IS THE ONE DIRECTION A BAY CANNOT GO. ** FS-ATTIC
    # is 11 7/8" I-joist with NO web opening, so a duct rides ALONG a bay or it rides the
    # deck; travelling south means the deck, and the deck's usable band is whatever the
    # rake leaves. The chase widens to x 9"..38" — heights 6" to 20 1/2" — and carries four
    # lanes on their own stations instead of one line carrying five runs:
    #
    #     x=1'-0"    DU-S-ERV-HP-FEED (6")   7 1/2" of roof
    #     x=2'-0"    STUBATH                13 1/2"
    #     x=2'-4 1/2" ATTIC                 15 3/4"
    #     x=3'-0"    BED3                   19 1/2"
    #
    # BED3's lane is at 3'-0" and not the 2'-9" the 4 1/2" module would give, because these
    # lanes cross W-A-STU-N on the deck and that partition's studs stand at 2'-8" and 4'-0":
    # a 4" duct on 2'-9" spans 2'-7"..2'-11" and takes the first of them, which is the one
    # `mep.run_through_stud` returns UNKNOWN for. 3'-0" clears it by 1 1/4". STUBATH (2'-0")
    # and ATTIC (2'-4 1/2") already fall in cavities — 5 1/4" clear on both sides and 3/4"
    # off the same 2'-8" stud respectively.
    #
    # **Lane 1 starts at x=2'-0" and DU-ERV-RISER-EXH is why**: the riser drops at
    # x=1'-6 5/8" and is 6", so it owns 15 5/8"..21 5/8" and a 4" lane needs its centre 5"
    # clear of it. BATH1 uses no lane at all — it drops into the 32'-8" bay on its own
    # collar's station at x=5'-7 1/2" and runs the last 7 1/2" west to its terminal, so it
    # never enters the chase.
    #
    # ** EACH RADIAL LEAVES ITS OWN COLLAR AND CROSSES THE DECK ON ITS OWN y. ** The four
    # collars are on the plenum's SOUTH face at 4 1/2" centres (EQ-T-ERV-PLENUM-A-EXH), and
    # each run drops to its own east-west line before turning west, so no two share a
    # station anywhere. The ordering is not free: the collar that turns west FURTHEST NORTH
    # takes the WESTMOST lane, which is what keeps a west leg from crossing a neighbour's
    # south leg. Going the other way round makes three crossings out of nothing.
    #
    # ** THE RISER STANDS AT y=21'-8 1/2", BETWEEN THE 21'-4" AND 22'-0" STUDS, AND EVERY
    # OTHER STATION IN THIS WALL IS SPOKEN FOR. ** W-A-STU-W is the only 5 1/2" cavity the
    # bath touches (its two other walls are 2x4 partitions, where a 4" duct is a framed
    # opening, not a bore) and it is the suite's wet wall: on the x=9'-7 1/2" axis
    # PR-A-BAR-DRAIN holds y 16'-2 5/8"..19'-4" and PR-A-STUBATH-LAV-DRAIN y 19'-4"..21'-4 5/8",
    # both in the joist band at 19'-3 1/2"..20'-0 3/4" — which is the band this riser has to
    # cross to get out of its bay. So the riser has to stand NORTH of the lavatory drop, and
    # 21'-8 1/2" is the first station that does: 3 7/8" from that drop's 2" riser, 7/8" of
    # air between them.
    #
    # ** IT BORES NOTHING. ** The staggered 2x4s sit at 8" centres on alternating faces —
    # 21'-4" on the west row, 22'-0" on the east — so the clear gap between them is
    # 21'-4 3/4"..21'-11 1/4" and a 4" duct on the axis spans 21'-6 1/2"..21'-10 1/2",
    # 1 3/4" and 3/4" clear. The old station at 19'-4" landed ON the 19'-4" stud and
    # `mep.run_through_stud` returned UNKNOWN for it, because a 4" penetration is wider than
    # a 2x4 is deep and nothing in this engine grades the header that would need.
    #
    # ** WHAT IS STILL IN THE WAY IS PLUMBING, AND IT IS PHASE 3'S. ** PR-A-BAR-VENT
    # (y 17'-4"..20'-8") and PR-A-STUBATH-VENT (y 20'-8" north) run the FULL length of this
    # wall on the same axis at 23'-5"..23'-6", so a riser reaching a grille at 4'-4" crosses
    # one of them wherever it stands — there is no duct-side answer, and moving the duct is
    # what this campaign is allowed to do. The pair that survives here is
    # DU-A-ERV-R-STUBATH x PR-A-STUBATH-VENT; the fix is on the vent (jog its north leg off
    # the axis for the 20" it is inside this wall, or drop the grille below 3'-6"), and the
    # two BAR pairs this station DID clear are the measure of what the duct could do.
    DuctRun(uid="WCH6Z4DZX0", tag="DU-A-ERV-R-STUBATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(4, 6), ft(34, 2)), pt(ft(4, 6), ft(33, 10)),
                  pt(ft(2), ft(33, 10)), pt(ft(2), ft(21, 8.5)),
                  pt(ft(2), ft(21, 8.5)), pt(ft(9, 7.5), ft(21, 8.5)),
                  pt(ft(9, 7.5), ft(21, 8.5))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_BAY_HIGH_Z, _ATTIC_BAY_HIGH_Z, inch(52)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=20),
    DuctRun(uid="DYNQDC9ZMJ", tag="DU-A-ERV-R-ATTIC", system=DuctSystem.EXHAUST,
            path=(pt(ft(4, 10.5), ft(34, 2)), pt(ft(4, 10.5), ft(33, 5.5)),
                  pt(ft(2, 4.5), ft(33, 5.5)), pt(ft(2, 4.5), ft(20, 8)),
                  pt(ft(2, 4.5), ft(20, 8)), pt(ft(1), ft(20, 8))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        inch(-2), inch(-2)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=5),
    # ** BED3 RIDES THE 18'-0" BAY, AND IT IS THE ONLY ONE OF THE FOUR THAT IS FREE. **
    # DU-S-ERV-HP-FEED is already in the 22'-0" bay at y=21'-11 1/2", 1/8" off
    # FO-A-HALL's trimmer ply at 22'-2 5/8" (its own note says so), leaving 2 3/4" south of
    # it — a 4" duct does not go in 2 3/4". And the 19'-4" bay carries PR-A-STUBATH-DRAIN's
    # 10'-0" drop on the wet-wall axis at (9'-7 1/2", 19'-4"): a bay leg at 19'-2 1/8" passed
    # straight through a 3" stack, which is the pair D2 was sent here to remove. Shifting
    # within that bay does not help — PR-A-STUBATH-LAV-DRAIN's own leg runs its line too,
    # and at 19'-8" the two are 1/8" inside each other.
    #
    # 20'-8" is no better, and that was measured rather than assumed: the shower waste, the
    # lavatory waste and PR-A-CW-STUBATH's riser all cross that bay on the same axis, three
    # of them within 1 1/2" of this duct. **18'-0" is what is left**, and only the bar sink's
    # waste comes near it — PR-A-BAR-DRAIN's north leg crosses 1" over this duct's crown,
    # perpendicular. It is the bay DU-A-ERV-R-STUBATH vacated, and nothing else wants it.
    #
    # ** IT COMES OUT OF THE BAY AT x=21'-0" AND RUNS THE LAST LEG ON THE DIAGONAL. ** The
    # trip south to 18'-0" is a detour of 15 ft that `mep.run_route_efficiency` charges for:
    # squared off to x=29'-0" and then north, this run develops 59.9 ft against 23.9 ft of
    # straight line — 2.50 against the house's 2.50, a FAIL by a hair. x=21'-0" is where
    # DU-S-ERV-HP-FEED already leaves the bays for RM-A-EAST-UNFIN's deck, and east of it
    # nothing is finished and nothing is in the way for more than 2" in any direction, so the
    # last leg goes straight at the grille instead of round two sides of a rectangle: 54.0 ft
    # and a ratio of 2.26. REG-S-RET-BED3 is a CEILING grille in the storey below, so this
    # deck leg is over an unfinished floor from end to end.
    DuctRun(uid="73FJZH564X", tag="DU-A-ERV-R-BED3", system=DuctSystem.RETURN,
            path=(pt(ft(5, 3), ft(34, 2)), pt(ft(5, 3), ft(33, 1)),
                  pt(ft(3), ft(33, 1)), pt(ft(3), ft(18)),
                  pt(ft(3), ft(18)), pt(ft(21), ft(18)),
                  pt(ft(21), ft(18)), pt(ft(29), ft(31, 4))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_BAY_Z, _ATTIC_BAY_Z,
                        _ATTIC_DECK_Z, _ATTIC_DECK_Z),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=5),
    DuctRun(uid="4YT114ADP3", tag="DU-A-ERV-R-BATH1", system=DuctSystem.EXHAUST,
            path=(pt(ft(5, 7.5), ft(34, 2)), pt(ft(5, 7.5), ft(32, 8)),
                  pt(ft(5, 7.5), ft(32, 8)), pt(ft(5), ft(32, 8))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_BAY_Z, _ATTIC_BAY_Z),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=20),
]

# THE MIXING-BOX FEED — the one place fresh air enters the heat-pump loop.
#
# It keeps DU-S-ERV-HP-FEED's tag and uid. It comes off the supply riser's head on the attic
# deck, takes the boxed floor chase south, rides the FS-ATTIC bay at y=22'-0" east, comes
# back up onto RM-A-EAST-UNFIN's deck and runs NORTH to the mixing box, dropping onto it
# through SF-S-HP1's lid.
#
# ** THE 12'-2" SOFFIT TAIL IS GONE. ** Until 2026-09-04 the box sat at the far south end of
# SF-S-HP1 in RM-S-STUDY2's ceiling, and this run had to travel the length of SF-S-DUCT
# beside the trunk, cross a seam, jog east across three lanes with 1 1/8" to spare, and come
# back south. Nine vertices now instead of twelve; the tail, both of its turns and the pinch
# are all gone. Developed ~43'-7" against ~61'-2".
#
# 6" and not a 4" radial: ~100 of the machine's 210 authored cfm goes through here (206
# certified — see the header), which is half the house's fresh air arriving in one place, and
# a radial would run it at ~5,000 fpm.
#
# ** IT NEVER ENTERS THE GUEST STUDIO. ** Running the x=1'-0" deck chase south all the way
# would put 10'-11" of 6" duct along the base of a finished bedroom's knee wall — the single
# item that would set that chase's SECTION, where everything else on that wall is 4".
# It turns east in **y=22'-0"** — the same bay DU-A-ERV-R-BED3 takes, and for the same
# reason: 264" = 8 + 16 x 16 is a bay centre, it sits under W-A-STU-N's sole plate so the
# partition is irrelevant, and it is the last bay south of FO-A-HALL, which severs every
# west-to-east route north of it.
#
# ** ROUTE EFFICIENCY: ~2.05 AGAINST `mep.run_route_efficiency`'S 2.5. WATCH IT. ** It was
# 1.54 before, and it got WORSE only because the destination moved 27 ft closer to the
# origin while the route still has to go round FO-A-HALL. The margin is 0.45, not 0.96.
DUCTS_ERV_MIX_FEED = [
    DuctRun(uid="CSDV02AAAA", tag="DU-S-ERV-HP-FEED", system=DuctSystem.SUPPLY,
            # ** ITS FIRST 7" IS IN THE BAY. ** It comes off the riser head on the deck at
            # x=0'-5", under 4" of roof. It picks the riser up on FS-ATTIC's bottom chord
            # instead and stands up at x=1'-0", where the underside is 7 1/2" and a bare 6"
            # duct on the deck clears by 1/2". The 7" east is ALONG a bay — FS-ATTIC's
            # I-joists span x — so nothing is bored; the north-south leg that follows stays
            # on the deck for the same reason.
            #
            # ** THE DECK LEG TURNS DOWN AT y=28'-9", INSIDE THE PLENUM. ** It has to land
            # within EQ-S-ERV-MIX's footprint (y 27'-10 1/2"..30'-4") for
            # `mep.duct_connectivity` to read the joint, and 28'-9" is comfortably inside it
            # rather than on an edge. It was y=27'-9" while the plenum was a 12"-deep box.
            #
            # This run names NO soffit (below), so the old "stop exactly here or the attic
            # legs get graded" constraint is gone with it — but the drop still has to land
            # IN the plenum, so moving the plenum in y means moving this vertex with it.
            #
            # -8 7/8" is a 6" duct on FS-ATTIC's bottom chord; +4" is the same duct lying on
            # the attic deck; -24 7/8" is 6" above SF-S-HP1's cavity floor, unchanged by the
            # move because the 21" drop keeps that floor at 209 1/8" absolute.
            # 21'-11 1/2", not the 22'-0" bay centre, since 2026-09-16: centred, the 6" duct
            # stood 3/8" into FO-A-HALL's outboard trimmer ply (face at 22'-2 5/8") for the
            # whole 8' it runs beside the hole. `mep.run_through_blocking` found it where
            # the leg crosses x=18'; 1/8" clear now.
            path=(pt(inch(15.4), inch(406.8)), pt(inch(15.4), inch(406.8)),
                  pt(ft(1), inch(406.8)), pt(ft(1), ft(21, 10.625)),
                  pt(ft(1), ft(21, 10.625)), pt(ft(21), ft(21, 10.625)),
                  pt(ft(21), ft(21, 10.625)), pt(ft(21), ft(28, 9)),
                  pt(ft(21), ft(28, 9))),
            elevations=(inch(-8.875), inch(4), inch(4), inch(4),
                        inch(-8.875), inch(-8.875),
                        inch(4), inch(4), inch(-24.875)),
            # ** IT NAMES NO SOFFIT, AND THAT IS THE 2026-09-04 CHANGE THAT COSTS SOMETHING. **
            # It used to name SF-S-HP1. `duct_occupants` clips a run's extent ALONG the box
            # it names and deliberately not ACROSS it — and SF-S-HP1 now spans y
            # 27'-8"..35'-5 3/8", which is the same y band the x=1'-0" attic chase and the
            # riser head run through, twenty feet west of the box and fourteen inches above
            # its lid. Named, those three attic legs are graded as occupants of a cavity
            # they never enter: a hard FAIL against geometry that is correct.
            # What is given up is the grading of the final 12" drop, and that costs little:
            # the drop lands inside EQ-S-ERV-MIX's own 10 x 12 footprint, which IS a graded
            # occupant of the box, in the east lane with 1" to the cavity face. Nothing else
            # of this run is in the box at all — the 12'-2" tail that used to be is gone.
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=100),
]
