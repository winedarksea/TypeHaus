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
              position=pt(ft(4, 4), ft(34)), footprint=(inch(24), inch(8)),
              room="RM-M-MECH", type_ref="EQ-T-ERV-PLENUM-M-SUP",
              mount=Mount(kind=MountKind.WALL, elevation=ft(8))),
    Equipment(uid="9D1KYBNJ12", tag="EQ-M-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              position=pt(ft(4, 4), ft(35)), footprint=(inch(34), inch(8)),
              room="RM-M-MECH", type_ref="EQ-T-ERV-PLENUM-M-EXH",
              mount=Mount(kind=MountKind.WALL, elevation=ft(8))),
]
# ============ LEVEL 2 — TRUNK AND BRANCH, AND THE ARITHMETIC THAT DECIDED IT ============
#
# ** THIRTEEN HOME-RUN LANES WILL NOT LEAVE THIS CLOSET, AND ON 2026-09-19 THE ENGINE COULD
# FINALLY SAY SO. ** Until that day `profiles.open_web_opening_m` gave FS-S-WEST an 8 7/8"
# chord-to-chord window and nothing narrowed it ALONG the span, so the model read an
# open-web floor truss as a CONTINUOUS SLOT and thirteen 4" ducts crossing every truss
# inside a 41" band all passed. The block that stood here said as much in prose — "SEVEN
# PAIRS OVERLAP", "two 4" ducts on 2" centres OVERLAP BY 2"" — and then noted that nothing
# graded it. `JoistSpec.web_panel_pitch` and `mep.open_web_panel` grade it now.
#
# THE COUNT, with the provisional panel datum in params/second_deck.py (24" pitch, 15"
# clear, 12" offset). A lane running SOUTH sits at one x, so it crosses every truss in the
# SAME opening, and three openings reach this closet:
#
#     opening      x band        usable 4" lanes     why
#     16 1/2..31 1/2   —         0                   the three risers, the radon/vent
#                                                    bundle and nine conduits stand in it
#     40 1/2..55 1/2   42 1/2..53 1/2   3 per tier   two tiers in the 8 7/8" window
#     64 1/2..79 1/2   66 1/2..69 3/8   1 per tier   the closet's east wall at 71 3/8"
#                                                    ---
#                                                     8
#
# Eight lanes, thirteen radials. Leaving EASTWARD along a bay instead is worse: nine runs
# would want one 12 1/2" bay, which takes three per tier. **The neck is structural**, and
# BLD-08's home-run install cannot be laid on this level.
#
# ** SO THE EXTRACT SIDE GOES TO A TRUNK AND THE SUPPLY SIDE DOES NOT. ** Three will lay
# and ten will not, and that asymmetry is the whole of the decision: every fresh-air outlet
# in the house still leaves its own collar on its own damper, which is what BLD-08 was
# actually arguing for. The ten extracts are tee'd off one 8" trunk with a butterfly damper
# at each takeoff — the same balancing point, one fitting further from the box.
#
# ** THE TRUNK RUNS SOUTH, NOT ALONG A BAY, AND FO-S-STAIR IS WHY. ** A trunk in the 35'-4"
# bay crosses no member at all and would have been better in every other way. The stair well
# is x 10'-3 3/8"..17'-8 5/8", y 26'-0 3/8"..35'-5 3/8", and a trunk in that bay spans 7.18
# ft of it with nothing to strap to; `mep.run_over_void` said so the first time it was drawn
# that way. South means it lives in ONE opening for its whole length, and 8" of the 15"
# leaves 5" beside it for DU-M-ERV-R-STUDY.
#
# Because the trunk runs south, **every takeoff is a pure bay leg**: it leaves the trunk at
# its own bay and rides that bay to its terminal, crossing no truss at all. Two exceptions
# turn south again near their terminal (LAUNDRY for the standpipe boot) and each does it in
# its own opening.
#
# ** THE TIER RULE: A LEG THAT CROSSES THE TRUSSES RIDES THE UPPER TIER, A LEG THAT RIDES A
# BAY THE LOWER. ** Every crossing in this cavity is then a south leg meeting a bay leg, on
# opposite tiers BY CONSTRUCTION — no case analysis, and nothing to re-derive when a
# terminal moves. The alternative (one tier per RUN) is not even available: the conflict
# graph is not two-colourable, because BED2, BED1 and PLANT cross one another in a triangle.
# The step is at the elbow where the duct turns anyway, and it is drawn as a repeated vertex
# so it is a VERTICAL step and not a ramp spread over thirty feet — which is how it was
# drawn for one round, and `mep.run_interference` reported eleven pairs for it.
#
# **FILED ON THE SECOND STOREY, NOT THE MAIN ONE, AND THAT IS NOT COSMETIC.** These ducts run
# in FS-S-WEST's cavity, which is the second storey's floor and the main storey's ceiling.
# `resolve/mep_ducts.py::_containing_floor` matches a segment to a sibling FloorSystem *on
# the duct's own storey*, so a run filed on `main` with `floor_ref="FS-S-WEST"` gets graded
# against FS-M-WEST's joist lines instead — which sit on a different 16" phase, so every
# radial reported a straddle it did not have.
#
# Bay centres are 8" + n*16". **Two of them are unusable and the check is what said so:**
# FO-S-STAIR's trimmers land at y=26'-0 3/8" and y=35'-5 3/8", so a duct centred on the
# 26'-0" or 35'-4" bay straddles one.
#
# WHAT THE REDESIGN LEFT BEHIND, measured rather than claimed: **no duct-against-duct pair
# on this level at all**, where thirteen radials on 2" centres had seven. Every remaining
# interference here is a duct against a PIPE or a CONDUIT, which is the plumbing campaign's
# and the conduit campaign's to answer, and every one of the thirteen is clear of every web,
# every bay and the stair void.
#: The plenums' collar station, and since 2026-09-19 it is DERIVED rather than chosen: both
#: boxes are wall-mounted at 8'-0" and resolve to 97 1/4"..105 1/4" (the mount is off the
#: FINISHED floor, which is 1 1/4" over the storey datum), so a collar on the case's
#: mid-height is at 101 1/4" — second-relative -18 3/4".
#:
#: It was -20" while the collars were an integer count with no positions, and a run that
#: started 1 1/4" under the hole it goes into was nobody's error because nothing could see
#: it. `mep.erv_manifold_ports` can now: it grades each radial against the collar it lands
#: on, within an inch.
_PORT_Z = inch(-18.75)
#: A 4" duct's centreline resting on FS-S-WEST's bottom chord: invert 109 5/8" (the web
#: window's floor), centreline 111 5/8", second-relative -8 3/8". See the derivation above.
#: **The LOWER of the two tiers the 8 7/8" web window admits**, and the one every leg that
#: rides ALONG a bay uses.
_BAY_Z = inch(-8.375)
#: The UPPER tier: a 4" duct's crown resting on the top chord, invert 114 1/2", centreline
#: 116 1/2". The window is 109 5/8"..118 1/2" and two 4" ducts stack in it with 7/8" to
#: spare, which is the whole of what makes the rule below work.
#:
#: ** THE RULE: A LEG THAT CROSSES THE TRUSSES RIDES THE UPPER TIER, A LEG THAT RIDES A BAY
#: THE LOWER. ** Every crossing in this cavity is therefore a south leg meeting a bay leg,
#: and the two are on opposite tiers BY CONSTRUCTION — no case analysis, nothing to
#: re-derive when a terminal moves. The conflict graph the alternative needs is not even
#: two-colourable: BED2, BED1 and PLANT cross each other in a triangle.
#:
#: The cost is one offset per takeoff, at the elbow where it turns anyway.
_CROSS_Z = inch(-3.5)
#: An 8" trunk centred in the same window: 110 1/16"..118 1/16", 7/16" clear of each chord.
#: It rides a BAY, so the window is not actually what constrains it — but centring it is
#: what lets a 4" takeoff leave it at either tier.
_TRUNK_Z = inch(-5.9375)

DUCTS_ERV_LEVEL2 = [
    # ** THE TRUNK. ** 8" galvanized, out of the extract plenum's one trunk collar, SOUTH
    # down the x=3'-10 1/2" lane from y=35'-0" to y=7'-4".
    #
    # ** IT RUNS SOUTH AND NOT ALONG A BAY, AND FO-S-STAIR IS WHY. ** A trunk in the
    # 35'-4" bay would have been better in every other way — a bay leg crosses no member at
    # all — but the stair well is x 10'-3 3/8"..17'-8 5/8", y 26'-0 3/8"..35'-5 3/8", and a
    # trunk in that bay spans 7.18 ft of it with nothing to strap to. `mep.run_over_void`
    # said so the first time it was drawn that way.
    #
    # South means it crosses every truss, so it lives in ONE panel opening for its whole
    # length: x=3'-10 1/2" puts an 8" duct at 42 1/2"..50 1/2" inside the 40 1/2"..55 1/2"
    # opening, with 5" of that opening still free beside it for DU-M-ERV-R-STUDY.
    #
    # One size the whole length. It is oversized at the south end (PLANT alone is 5 cfm in
    # 8" round, about 14 fpm) and that is the cheap direction: the alternative is two
    # reducing transitions to save a few feet of the commonest duct in the catalogue.
    DuctRun(uid="Y3G88SKSRG", tag="DU-M-ERV-EXH-TRUNK", system=DuctSystem.EXHAUST,
            path=(pt(ft(3, 10.5), ft(35)), pt(ft(3, 10.5), ft(35)),
                  pt(ft(3, 10.5), ft(7, 4))),
            elevations=(_PORT_Z, _TRUNK_Z, _TRUNK_Z),
            diameter=inch(8), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=114),

    # --- THE THREE SUPPLY RADIALS -------------------------------------------------------
    # Home-run, and BLD-08 survives intact on this side: every fresh-air outlet still leaves
    # its own collar on its own damper. Three will lay and ten will not, and that asymmetry
    # is the whole of why the level split.
    #
    # STUDY leaves straight south in the trunk's own opening, 6 1/2" east of it. LIVING and
    # BED jog east along the 33'-8" and 34'-4" bays to the NEXT opening (64 1/2"..79 1/2")
    # and go south from there — two 4" lanes in it, tangent, 8" of its 15".
    DuctRun(uid="2ZZ3MF5VAF", tag="DU-M-ERV-R-STUDY", system=DuctSystem.SUPPLY,
            path=(pt(ft(4, 5), ft(34)), pt(ft(4, 5), ft(34)), pt(ft(4, 5), ft(34)),
                  pt(ft(4, 5), ft(20, 6)), pt(ft(4, 5), ft(20, 6)),
                  pt(ft(17, 2), ft(20, 6))),
            elevations=(_PORT_Z, _BAY_Z, _CROSS_Z, _CROSS_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=15),
    DuctRun(uid="MRH0QZT6NN", tag="DU-M-ERV-R-LIVING", system=DuctSystem.SUPPLY,
            path=(pt(ft(4, 9), ft(33, 8)), pt(ft(4, 9), ft(33, 8)),
                  pt(ft(5, 7), ft(33, 8)), pt(ft(5, 7), ft(33, 8)),
                  pt(ft(5, 7), ft(12, 8)), pt(ft(5, 7), ft(12, 8)),
                  pt(ft(27), ft(12, 8))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _CROSS_Z, _CROSS_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    DuctRun(uid="83MA15Q308", tag="DU-M-ERV-R-BED", system=DuctSystem.SUPPLY,
            path=(pt(ft(5, 1), ft(34, 4)), pt(ft(5, 1), ft(34, 4)),
                  pt(ft(5, 11), ft(34, 4)), pt(ft(5, 11), ft(34, 4)),
                  pt(ft(5, 11), ft(6)), pt(ft(5, 11), ft(6)),
                  pt(ft(9), ft(6))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _CROSS_Z, _CROSS_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=15),

    # --- THE TEN EXTRACT TAKEOFFS -------------------------------------------------------
    # Every one leaves the trunk at its own bay and rides that bay to its terminal, so with
    # two exceptions below **a takeoff crosses no truss at all**. Every tag and uid is the
    # radial's; only what feeds it changed.
    DuctRun(uid="K04AT15S97", tag="DU-M-ERV-R-BATH1", system=DuctSystem.EXHAUST,
            path=(pt(ft(3, 10.5), ft(24, 6)), pt(ft(1, 2), ft(24, 6))),
            elevations=(_BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    DuctRun(uid="BKE5RKVE8Z", tag="DU-M-ERV-R-VANITY", system=DuctSystem.EXHAUST,
            path=(pt(ft(3, 10.5), ft(24, 10)), pt(ft(3), ft(24, 10))),
            elevations=(_BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    DuctRun(uid="0DMX0NM8XS", tag="DU-M-ERV-R-BATH2", system=DuctSystem.EXHAUST,
            path=(pt(ft(3, 10.5), ft(18)), pt(ft(4), ft(18))),
            elevations=(_BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    DuctRun(uid="P5H0GQ3E8N", tag="DU-M-ERV-R-MUD", system=DuctSystem.RETURN,
            path=(pt(ft(3, 10.5), ft(31, 4)), pt(ft(4, 0.4), ft(31, 4))),
            elevations=(_BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=5),
    DuctRun(uid="HGMQ4AWG3S", tag="DU-M-ERV-R-BED2", system=DuctSystem.RETURN,
            path=(pt(ft(3, 10.5), ft(22, 1.75)), pt(ft(29), ft(22, 1.75))),
            elevations=(_BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=5),
    DuctRun(uid="XA7NRRGJ50", tag="DU-M-ERV-R-BED1", system=DuctSystem.RETURN,
            path=(pt(ft(3, 10.5), ft(14)), pt(ft(29), ft(14))),
            elevations=(_BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=5),
    DuctRun(uid="DPAS57TPCG", tag="DU-M-ERV-R-SUITEBATH", system=DuctSystem.EXHAUST,
            path=(pt(ft(3, 10.5), ft(19, 4)), pt(ft(14), ft(19, 4))),
            elevations=(_BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=20),
    # LAUNDRY and KITCH are the two takeoffs that do cross a truss, and each crosses in its
    # own opening on the upper tier: LAUNDRY turns south at x=14'-5" (the 160 1/2"..175 1/2"
    # opening) to reach the standpipe boot, KITCH runs straight.
    DuctRun(uid="ANSKB7EGDH", tag="DU-M-ERV-R-LAUNDRY", system=DuctSystem.RETURN,
            path=(pt(ft(3, 10.5), ft(20, 10)), pt(ft(10, 6), ft(20, 10)),
                  pt(ft(14, 5), ft(20, 10)), pt(ft(14, 5), ft(20, 10)),
                  pt(ft(14, 5), ft(18, 4)), pt(ft(14, 5), ft(18, 4))),
            elevations=(_BAY_Z, _BAY_Z, _BAY_Z, _CROSS_Z, _CROSS_Z, inch(-108)),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=8),
    DuctRun(uid="YEXGZK2KW2", tag="DU-M-ERV-R-KITCH", system=DuctSystem.RETURN,
            path=(pt(ft(3, 10.5), ft(21, 9.75)), pt(ft(20, 10.7), ft(21, 9.75))),
            elevations=(_BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=6),
    DuctRun(uid="X05VC14PBH", tag="DU-M-ERV-R-PLANT", system=DuctSystem.EXHAUST,
            path=(pt(ft(3, 10.5), ft(7, 4)), pt(ft(18), ft(7, 4)),
                  pt(ft(18), ft(7, 4))),
            elevations=(_BAY_Z, _BAY_Z, inch(102)),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=5),
]
