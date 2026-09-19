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
# LEVEL 3 — sitting ON the FS-ATTIC deck beside the chase head at (1', 34'-6"), fully
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
#     distribution to the other rooms depends on the AH fan turning. That was true of the old
#     design too and it wants a CONTROLS INTERLOCK (blower continuous, or on ERV call), which
#     the schema has no field for — so it is written here and in plans/TODO.md. It matters
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
# east leg rides the y=19'-4" bay, ALONG the joists, boring nothing; DU-A-ERV-R-PLANT feeds
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
# +4" is a 4" duct lying on the attic deck at 240"; -9 7/8" is its centreline sitting on
# FS-ATTIC's bottom chord at 228 1/8". Both are attic-relative, and negative because the
# attic datum is the deck top.
_ATTIC_DECK_Z = inch(4)
_ATTIC_BAY_Z = inch(-9.875)

DUCTS_ERV_ATTIC = [
    DuctRun(uid="4YT114ADP3", tag="DU-A-ERV-R-BATH1", system=DuctSystem.EXHAUST,
            path=(pt(ft(5), ft(34, 6)), pt(ft(1), ft(34, 6)), pt(ft(1), ft(32, 8)),
                  pt(ft(1), ft(32, 8)), pt(ft(5), ft(32, 8))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_BAY_Z, _ATTIC_BAY_Z),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=20),
    # THE ATTIC'S OWN PICKUP, at the studio's NW corner, not the walled storage pocket —
    # REG-A-RET1 must not extract a guest bedroom's air through a closed door.
    #
    # It takes the x=1'-0" chase south past W-A-STU-N to the boot at (1'-0", 20'-8"); this
    # run's 1'-7" inside the studio is most of what remains of that chase. All of it is ON
    # the deck: FS-ATTIC is I-joist, so there is no crossing bays here and the north-south
    # travel costs nothing in depth. Developed length ~15' — the shortest radial on this
    # manifold, so it takes nobody's pressure headroom.
    DuctRun(uid="DYNQDC9ZMJ", tag="DU-A-ERV-R-ATTIC", system=DuctSystem.RETURN,
            path=(pt(ft(5), ft(34, 6)), pt(ft(1), ft(34, 6)), pt(ft(1), ft(20, 8)),
                  pt(ft(1), ft(20, 8))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z, inch(-2)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=5),
    # THE GUEST BATH'S EXTRACT. Same chase south to y=19'-0",
    # then east on the deck to the W-A-STU-W axis at x=9'-7 1/2" and UP inside that wall's
    # 5 1/2" staggered cavity to REG-A-STUBATH-EXH at 7'-0". The rise is the whole reason the
    # terminal is a wall grille rather than a floor boot: this room follows the roof and has no
    # ceiling plenum, and the wet wall is the only chase between a high pickup and the deck.
    #
    # 20 cfm continuous, matching every other bath terminal in the house — and small enough
    # that the extra run costs the machine nothing measurable.
    #
    # ** THE EAST LEG MUST NOT LIE ACROSS THE DECK. ** From x=1'-0" to the wet
    # wall, laying it across RM-A-STUDIO's floor at y=19'-0" would put 8'-7" of duct across
    # the middle of a bedroom. It rides the FS-ATTIC bay instead, which costs nothing: the
    # leg runs EAST, and FS-ATTIC's I-joists span x, so travelling east is travelling ALONG
    # a bay. Nothing is bored.
    #
    # y=19'-4" (232" = 8 + 14 x 16) is a bay centre; REG-A-STUBATH-EXH is the same 4" over so
    # the riser meets its grille. 19'-4" is
    # well inside RM-A-STUBATH (y 17'-4 3/4" .. 22'-3 3/8"), and it is a different bay from the
    # one PR-A-STUBATH-DRAIN takes at 20'-8", so the two do not share a cavity.
    DuctRun(uid="WCH6Z4DZX0", tag="DU-A-ERV-R-STUBATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(5), ft(34, 6)), pt(ft(1), ft(34, 6)), pt(ft(1), ft(19, 4)),
                  pt(ft(1), ft(19, 4)), pt(ft(9, 7.5), ft(19, 4)),
                  pt(ft(9, 7.5), ft(19, 4))),
            # ** THE RISER TOP MUST FOLLOW ITS GRILLE. ** REG-A-STUBATH-EXH is at 4'-4"; a
            # riser topping out higher rises past its own boot and out through the rake,
            # which at x=9'-7 1/2" is 4'-11 1/4" above the deck. `integrity.element_above_roof`
            # catches that; `mep.register_duct_match` only grades the pair in plan, where they
            # agree regardless of elevation.
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_BAY_Z, _ATTIC_BAY_Z, inch(52)),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized",
            design_cfm=20),
    # RM-S-BED3's extract, forced up here by FO-S-STAIR — see the header. It becomes a ceiling
    # grille rather than a floor boot, which for stale air is the better end of the room anyway.
    #
    # ** THERE IS NO WAY ROUND THE NORTH. ** A bay leg crossing x 10'..18' at y=31'-4" would
    # hit FO-A-HALL, which spans that whole band to the north gable — FO-A-HALL's maxy IS
    # W-A-N2's inside gwb face, so the strip between the void and the wall is wall, not deck.
    # EVERY west-to-east route north of the studio is severed.
    #
    # So it goes down the x=1'-0" chase to y=22'-0" (264" = 8 + 16 x 16, a bay centre, and below
    # W-A-STU-N's sole plate so the partition is irrelevant), east under the studio floor to
    # x=29', then north on the east loft's deck to the existing grille. **~53'-6", not the
    # longest radial in the house** — DU-M-ERV-R-PLANT is 55'-8" on the FS-S-WEST trusses.
    # Length was never the criterion anyway — BED3 carries 5 cfm (~102 fpm in
    # 4", where 21 extra feet costs thousandths of an inch w.g.), and since the 2026-09-15
    # rebalance PLANT carries 5 cfm too and costs the same nothing. Neither is the run whose
    # drop the installer must check any more; that is DU-B-ERV-R-SAUNA-EXH, where a motorised
    # damper and not a duct is the number. The two are on different machine ports:
    # BED3 on EQ-A-ERV-MAN-EXH, PLANT on EQ-M-ERV-MAN-EXH. Re-filing BED3 onto the main-storey
    # manifold is blocked by FO-S-STAIR, and that manifold is full at 10 of 10.
    DuctRun(uid="73FJZH564X", tag="DU-A-ERV-R-BED3", system=DuctSystem.RETURN,
            path=(pt(ft(5), ft(34, 6)), pt(ft(1), ft(34, 6)), pt(ft(1), ft(22)),
                  pt(ft(1), ft(22)), pt(ft(29), ft(22)),
                  pt(ft(29), ft(22)), pt(ft(29), ft(31, 4))),
            elevations=(_ATTIC_DECK_Z, _ATTIC_DECK_Z, _ATTIC_DECK_Z,
                        _ATTIC_BAY_Z, _ATTIC_BAY_Z,
                        _ATTIC_DECK_Z, _ATTIC_DECK_Z),
            diameter=inch(4), routing=DuctRouting.CHASE, material="galvanized", design_cfm=5),
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
            path=(pt(inch(9.625), ft(33, 7.5)), pt(ft(1), ft(33, 7.5)), pt(ft(1), ft(33, 7.5)),
                  pt(ft(1), ft(21, 11.5)),
                  pt(ft(1), ft(21, 11.5)), pt(ft(21), ft(21, 11.5)),
                  pt(ft(21), ft(21, 11.5)), pt(ft(21), ft(28, 9)),
                  pt(ft(21), ft(28, 9))),
            elevations=(inch(-8.875), inch(-8.875), inch(4), inch(4),
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
