# haus: editable
# Catlin MEP — the ERV on LEVEL 3: the attic extract plenum, the mixing box it does not
# feed, the three FS-ATTIC radials and the mixing-box feed.
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

from .erv_balance import (
    DU_A_ERV_R_ATTIC,
    DU_A_ERV_R_BATH1,
    DU_A_ERV_R_STUBATH,
    DU_S_ERV_HP_FEED,
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
    Equipment(uid="8PE9E87JX5", tag="EQ-S-ERV-MIX", kind=EquipmentKind.MIXING_BOX,
              position=pt(inch(311.75), inch(348)), footprint=(inch(27.5), inch(40)),
              room="RM-A-EAST-UNFIN", type_ref="EQ-T-ERV-MIXING-BOX",
              mount=Mount(kind=MountKind.FLOOR)),
]
# THE MIXING BOX — System 1's return plenum at EQ-S-HP1-AH's return end, on the attic deck
# since 2026-11-11 (it was in SF-S-HP1, retired with the unit's move). Fresh air may arrive
# only here, upstream of the coil and the internal heat kit: 100 cfm of -15 F air downstream
# of them would be delivered untempered.
#
# ** A BOX WITH A BACKDRAFT DAMPER, NOT A WYE. ** The ERV and the air handler run on their own
# schedules. AH running, ERV off: the return is negative and, undampered, pulls backwards
# through the 6" feed and a stopped (non-recovering, not airtight) ERV core. ERV running, AH
# off: 100 cfm enters a still chamber and leaves through the return grilles, so the ERV calls
# the AH fan (EQ-B-ERV.blower_interlock_ref, mep.erv_blower_interlock).
# `_pair_is_plumbed` excuses only equipment<->duct pairs, which is why the feed lands on
# equipment.
#
# 27 1/2" x 39" x 21" on the deck, x 24'-10"..27'-1 1/2", y 27'-5"..30'-8", 4" off the
# cabinet (its connector and a 1" collar): it takes the
# hall return riser (DU-S-HP-RET, from the y 352-368 bay), RM-S-SUITE's (y 336-352 bay),
# RM-S-BED3's deck leg on its north face, RM-A-EAST-UNFIN's 12x12 stub (DU-A-HP1-EAST-RET,
# damper-locked at 35 cfm) on its south face and the ERV feed (DU-S-ERV-HP-FEED)
# low on that same face, and
# gives the cabinet DU-A-HP1-RET-NECK on its west face. The tag keeps its `-S-`.
EQUIPMENT_ERV_SECOND = []
# ============================== LEVEL 3 — ATTIC RADIALS ==============================
#
# Four runs off the deck manifold at (5'-0", 34'-6"): three extracts and, separately below,
# the mixing-box feed. Each takes the open deck chase west to x=1'-0" and south along the
# west wall, then drops into its FS-ATTIC bay and rides it east to the terminal. `CHASE`,
# for the reason in the header — one run, two cavities, and the declaration is the honest
# one. FS-ATTIC is I-joist, so unlike level 2 there is no crossing the bays: all the
# north-south travel happens ON the deck, above the joists, where it costs nothing in DEPTH.
#
# ** THE x=1'-0" CHASE RUNS THE LENGTH OF A FINISHED BEDROOM, AND THE KNEE WALL AT ITS FOOT
# IS BARE. ** DU-S-ERV-HP-FEED turns east at y=22'-0" and reaches SF-S-HP1 up
# RM-A-EAST-UNFIN's deck instead of running the knee wall's length; DU-A-ERV-R-STUBATH's
# east leg rides the y=21'-8 1/2" bay, ALONG the joists, boring nothing. The west-eave floor receptacles have since been removed;
# electrical_attic.py records the rafter plate's unresolved electrical wall-space status.
#
# The remaining rejected alternative is unchanged: bore the FS-ATTIC I-joists and run
# north-south in the bays. The hole chart permits it, but at x=1'-0" every hole would fall
# within a foot of the joists' west bearing, which is the one place the chart does not — and
# that is before ~16 bored webs and a manufacturer sign-off.
#
# +2 3/4" is a 4" duct lying on the attic deck: the 3/4" ply's top (240 3/4") plus the
# radius (2026-11-07; +4" floated it 1 1/4" off the deck, and a deck saddle wants it bearing).
# Both are attic-relative, and negative because the attic datum is the top of FS-ATTIC's joists.
_ATTIC_DECK_Z = inch(2.75)
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
# -3" is a 4" duct in the TOP of a bay, stacked over a run hung low in it: 235"..239"
# against DU-S-ERV-HP-FEED's 228 1/2"..234 1/2", 1/2" between them and 1" under the deck. `mep_packing` grades a bay's width as a TIER, so two runs at different
# elevations do not share it — which is the only reason the 22'-0" bay can take a second duct
# at all (its free strip south of the 6" feed is 3 1/4", and a 4" duct does not go in 3 1/4").
_ATTIC_BAY_HIGH_Z = inch(-3)

DUCTS_ERV_ATTIC = [
    # ** THE WEST CHASE CARRIES ONE DUCT, AND THAT IS THE ROOF TALKING. ** At x=1'-0" the
    # 6:12 underside is `1 1/2" + x/2` = 7 1/2" over the deck, and a 4" duct on
    # _ATTIC_DECK_Z spans 3/4"..4 3/4" of it (2"..6" when this was written). There is no second tier at that station and there
    # never was — so the radials, DU-S-ERV-HP-FEED and the first 41" of
    # DU-ERV-RISER-EXH were all drawn on the one line, five and six deep, and
    # `mep.run_interference` reported fourteen duct-against-duct pairs for it.
    #
    # ** THE FIX IS WIDTH, BECAUSE SOUTH IS THE ONE DIRECTION A BAY CANNOT GO. ** FS-ATTIC
    # is 11 7/8" I-joist with NO web opening, so a duct rides ALONG a bay or it rides the
    # deck; travelling south means the deck, and the deck's usable band is whatever the
    # rake leaves. The chase widens to x 9"..38" — heights 6" to 20 1/2" — and carries its
    # lanes on their own stations instead of one line carrying every run:
    #
    #     x=1'-0"    DU-S-ERV-HP-FEED (6")   7 1/2" of roof
    #     x=2'-0"    STUBATH                13 1/2"
    #     x=2'-4 1/2" ATTIC                 15 3/4"
    #
    # The x=3'-0" lane was DU-A-ERV-R-BED3's and is free since 2026-11-11 (BED3 returns to
    # System 1 instead). A new lane there clears W-A-STU-N's 2'-8" stud by 1 1/4"; 2'-9" would
    # hit it. STUBATH (2'-0") and ATTIC (2'-4 1/2") fall in that wall's cavities — 5 1/4"
    # clear on both sides and 3/4" off the 2'-8" stud respectively.
    #
    # **Lane 1 starts at x=2'-0" and DU-ERV-RISER-EXH is why**: the riser drops at
    # x=1'-6 5/8" and is 6", so it owns 15 5/8"..21 5/8" and a 4" lane needs its centre 5"
    # clear of it. BATH1 uses no lane at all — it drops into the 32'-8" bay on its own
    # collar's station at x=5'-7 1/2" and runs the last 7 1/2" west to its terminal, so it
    # never enters the chase.
    #
    # ** EACH RADIAL LEAVES ITS OWN COLLAR AND CROSSES THE DECK ON ITS OWN y. ** The
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
    # ** CLOSED 2026-09-26: the grille came down to 3'-0", so the riser stops under the vent. **
    DuctRun(uid="WCH6Z4DZX0", tag="DU-A-ERV-R-STUBATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(4, 6), ft(34, 2)), pt(ft(4, 6), ft(33, 1)),
                  pt(ft(2), ft(33, 1)), pt(ft(2), ft(22, 2.25)),
                  pt(ft(2), ft(21, 8.5)), pt(ft(9, 7.5), ft(21, 8.5)),
                  pt(ft(9, 7.5), ft(21, 8.5))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_BAY_HIGH_Z, _ATTIC_BAY_HIGH_Z, inch(36)),
            # (2026-11-11) The 5 3/4" deck-to-bay drop is a 45 degree ramp (5 3/4" of run) with an
            # adjustable elbow at its foot: two stamped 90s need 12" and an adjustable pair 9 1/2".
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            adjustable_elbows=(4,), design_cfm=DU_A_ERV_R_STUBATH),
    # RETURN, like every stale-air pickup (REG-A-RET1 is a return); since 2026-11-11 it is
    # also the run that serves EQ-A-ERV-MAN-EXH's declared return port.
    DuctRun(uid="DYNQDC9ZMJ", tag="DU-A-ERV-R-ATTIC", system=DuctSystem.RETURN,
            # (2026-11-07) Stock turns only: the 6" vertical drop at the foot of the lane was
            # shorter than its two 90s' take-offs (12"). The lane turns west on the deck and
            # goes into the bay on a 54.7 degree ramp (the stamped 45's 10 degree snap): 9 1/8" of
            # straight over the 90 and ramp take-off (6" + 3.1"), 4 1/4" of ramp, 3 1/8" to the
            # terminal over its 3.1", 16 1/2" in all west of the lane.
            path=(pt(ft(4, 10.5), ft(34, 2)), pt(ft(4, 10.5), ft(32, 8)),
                  pt(ft(2, 4.5), ft(32, 8)), pt(ft(2, 4.5), ft(20, 8)),
                  pt(inch(19.375), ft(20, 8)), pt(inch(15.125), ft(20, 8)),
                  pt(ft(1), ft(20, 8))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_DECK_Z, inch(-2), inch(-2)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_A_ERV_R_ATTIC),
    DuctRun(uid="4YT114ADP3", tag="DU-A-ERV-R-BATH1", system=DuctSystem.EXHAUST,
            # The bearing deck leg ends over REG-S-EXH1 and drops 12 5/16" onto its collar on
            # one stock 90 (2026-11-10; the 7 1/2" leg under the deck is gone).
            path=(pt(ft(5, 7.5), ft(34, 2)), pt(ft(5, 7.5), ft(32, 8))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_A_ERV_R_BATH1),
]

# THE MIXING-BOX FEED — the one place fresh air enters the heat-pump loop.
#
# It keeps DU-S-ERV-HP-FEED's tag and uid. It comes off the supply riser's head on the attic
# deck, takes the open deck chase south, rides the FS-ATTIC bay at y=22'-0" east to x=25'-10",
# comes back up onto RM-A-EAST-UNFIN's deck and runs NORTH into the mixing box beside the air
# handler (2026-11-11; it used to drop into SF-S-HP1). Developed ~44'-3".
#
# 6" and not a 4" radial: ~100 of the machine's 210 authored cfm goes through here (206
# certified — see the header), which is half the house's fresh air arriving in one place, and
# a radial would run it at ~5,000 fpm.
#
# ** IT NEVER ENTERS THE GUEST STUDIO. ** Running the x=1'-0" deck chase south all the way
# would put 10'-11" of 6" duct along the base of a finished bedroom's knee wall — the single
# item that would set that chase's SECTION, where everything else on that wall is 4".
# It turns east in **y=22'-0"**: 264" = 8 + 16 x 16 is a bay centre, it sits under W-A-STU-N's sole plate so the
# partition is irrelevant, and it is the last bay south of FO-A-HALL, which severs every
# west-to-east route north of it.
#
# Route efficiency is graded by `mep.run_route_efficiency` against 2.5; the route has to go
# round FO-A-HALL.
DUCTS_ERV_MIX_FEED = [
    DuctRun(uid="CSDV02AAAA", tag="DU-S-ERV-HP-FEED", system=DuctSystem.SUPPLY,
            # ** ITS FIRST 7" IS IN THE BAY. ** It comes off the riser head on the deck at
            # x=0'-5", under 4" of roof. It picks the riser up low in the FS-ATTIC bay
            # instead and stands up at x=1'-0", where the underside is 7 1/2" and a bare 6"
            # duct on the deck clears by 1/2". The 7" east is ALONG a bay — FS-ATTIC's
            # I-joists span x — so nothing is bored; the north-south leg that follows stays
            # on the deck for the same reason.
            #
            # ** IT ENTERS EQ-S-ERV-MIX's SOUTH FACE HORIZONTALLY. ** The bay leg
            # runs on east to x=25'-10" (short of ED-S-BED2-LT's can), stands up there and
            # runs north on the deck, east of the walk to EQ-S-HP1-AH and of its service
            # zone, through the south face at y=328" (the end at y=331" is inside).
            #
            # -8 1/2" is a 6" duct strapped low in an FS-ATTIC bay, invert 228 1/2", 3/8"
            # off the ceiling board (2026-11-07; -8 7/8" laid it ON the board at 228 1/8":
            # an I-joist bay has no chord under a duct, only gypsum); +4" is the same duct
            # lying on the attic deck.
            # 21'-11 1/2", not the 22'-0" bay centre, since 2026-09-16: centred, the 6" duct
            # stood 3/8" into FO-A-HALL's outboard trimmer ply (face at 22'-2 5/8") for the
            # whole 8' it runs beside the hole. `mep.run_through_blocking` found it where
            # the leg crosses x=18'; 1/8" clear now.
            # (2026-11-10) The deck leg stands at x=12" again, 3.4" west of the riser's x=15.4".
            # The roof rose 1 1/2", W-A-STU-N grew a real stud at x=16", and a leg at 15.4"
            # stands in it; at 12" the duct clears the stud by 1/4".
            # (2026-11-12) That 3.4" is one SKEWED leg in the bay, not a level jog between two
            # 90s: off the riser head at -9 3/4", 30 degrees off vertical onto x=12" at -3 7/8"
            # (6.8" on two adjustable elbows set down, 1.6" take-off each), leaving 7 7/8" of
            # stand for the deck 90's 6" (notes/erv_static_budget.md §10.28).
            path=(pt(inch(15.4), inch(406.8)), pt(inch(12), inch(406.8)), pt(inch(12), inch(406.8)),
                  pt(inch(12), ft(21, 10.625)),
                  pt(inch(12), ft(21, 10.625)), pt(inch(310), ft(21, 10.625)),
                  pt(inch(310), ft(21, 10.625)), pt(inch(310), inch(331))),
            elevations=(inch(-9.75), inch(-3.875), inch(4), inch(4),
                        inch(-8.5), inch(-8.5),
                        inch(4), inch(4)),
            adjustable_elbows=(1,),
            # It names no soffit: CHASE, one run in two cavities (bay and deck).
            diameter=inch(6), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=DU_S_ERV_HP_FEED),
]
