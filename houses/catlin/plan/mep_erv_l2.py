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
from typehaus.model import Location, WallAttachment, deg

from .erv_balance import (
    DU_M_ERV_EXH_TRUNK,
    DU_M_ERV_R_BATH1,
    DU_M_ERV_R_BATH2,
    DU_M_ERV_R_BED,
    DU_M_ERV_R_BED1,
    DU_M_ERV_R_BED2,
    DU_M_ERV_R_KITCH,
    DU_M_ERV_R_LAUNDRY,
    DU_M_ERV_R_LIVING,
    DU_M_ERV_R_MUD,
    DU_M_ERV_R_RET3,
    DU_M_ERV_R_STUDY,
    DU_M_ERV_R_SUITEBATH,
    DU_M_ERV_R_VANITY,
)

# LEVEL 2 — RM-M-MECH, the shaft closet (x 0'-0 5/8"..5'-11 3/8", y 33'-4 5/8"..35'-11 3/8").
# Wall-hung at 8'-0", under the 9'-0" plate.
#
# **Both manifolds are east of x=2'-8", and that is the whole siting argument.** The closet's
# west end is not free space. Measured off the resolved model on 2026-09-15, what stands
# there is:
#
#     DU-ERV-RISER-SUP    x  9 5/8"   y 33'-10 1/4"  full height
#     DU-S-ERV-HP-FEED    x 12"       y 33'-10 1/4"  attic standpipe off SUP's head
#     DU-ERV-RISER-EXH    x 18 5/8"   y 33'-10 1/4"  full height
#     DU-ERV-EA           x  2'-0"    y 35'-0"       full height, basement to +17'-0"
#     VR-M-STACK     x  1'-0"    y 35'-1.3"     radon + plumbing vent (y 34'-6" till 09-23)
#     six plumbing vents  x  1'-0"    y 35'-1.3"     all landing on that one riser
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
              footprint=(inch(24), inch(11.5)),
              room="RM-M-MECH", type_ref="EQ-T-ERV-PLENUM-M-SUP",
              mount=Mount(kind=MountKind.WALL, elevation=ft(8)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-MECH-S", face="left", distance_from_start=inch(52),
                  normal_gap=inch(1.625), rotation_offset=deg(0)))),
    Equipment(uid="9D1KYBNJ12", tag="EQ-M-ERV-MAN-EXH", kind=EquipmentKind.DUCT_MANIFOLD,
              footprint=(inch(34), inch(8)),
              room="RM-M-MECH", type_ref="EQ-T-ERV-PLENUM-M-EXH",
              mount=Mount(kind=MountKind.WALL, elevation=ft(8)),
              location=Location(attachment=WallAttachment(
                  wall_ref="W-M-MECH-E", face="left", distance_from_start=inch(20),
                  normal_gap=inch(0.625), rotation_offset=deg(-90)))),
]
# ============ LEVEL 2 — TRUNK AND BRANCH ============
#
# **Thirteen home-run lanes will not leave this closet** through FS-S-WEST's open-web trusses,
# so the extract side is trunk-and-branch and the supply side is not: every fresh-air outlet
# still leaves its own damper collar (BLD-08), and the ten extracts tee off one trunk.
#
# **The trunk is FLAT and runs in the D pockets at x=27" (owner, 2026-11-07; re-routed
# 2026-11-08).** TrimJoist J12 (decision #117) gives each truss 5" D pockets with a 9x4 R2 and
# one 16x8 R1. R1 does not line up across the deck (x 54-70" north of the stair, 101-117" south
# of it, the BATH1 stack between), but the D pockets do at x=27", from y=0 to the chase. Every
# run that crosses a truss holds the height its pocket admits, and `mep.open_web_panel` keeps
# one run per pocket:
#
#     x (in)   run                     height over the chord   pocket
#     27       DU-M-ERV-EXH-TRUNK 8x4  3 7/8"                   D1/D2 R2
#     83 3/4   DU-M-ERV-R-BED          7 1/2"                   D6
#     106 7/8  DU-M-ERV-R-STUDY        7.9"                     D8 north, R1 south
#
# (DU-M-ERV-R-LIVING had the x=42 1/4" lane, 8" over the chord, until 2026-11-11; it tees off BED now.)
# The supply radials ride the upper tier, so every extract takeoff rides its own bay low and
# crosses them underneath. The neck crosses the chase trimmers in R1 at x=57 1/2".
#
# **Filed on the second storey, not the main one.** These ducts run in FS-S-WEST's cavity;
# `resolve/mep_ducts.py::_containing_floor` matches a segment to a FloorSystem on the duct's own
# storey, so a run filed on `main` would be graded against FS-M-WEST's joists instead.
#: The plenums' collar station: both boxes hang at 8'-0" and resolve to 97 1/4"..105 1/4", so
#: a collar at mid-height is 101 1/4", second-relative -18 3/4" (`mep.erv_manifold_ports`).
_PORT_Z = inch(-18.75)
#: A 4" duct resting on FS-S-WEST's bottom chord (invert 109 5/8", centreline 111 5/8"): the
#: low tier every extract takeoff rides along its bay.
_BAY_Z = inch(-8.375)
#: The flat trunk's centreline in TrimJoist J12's D pockets: an 8x4 passes their 9x4 R2 at
#: x=27" only between 3.85" and 3.9" over the chord (`resolve/open_web.grade_crossing`).
_TRUNK_Z = inch(-8)
#: A 4" radial's upper-tier heights in the D pockets: 7.5" over the chord at x=83 3/4", 7.9"
#: at 106 7/8" (over the BATH1 lav drain), 8.0" at x=42 1/4" (1/8" over the trunk's crown).
_UP_Z = inch(-4.375)
_STUDY_Z = inch(-3.975)
_HI_Z = inch(-3.875)
#: Under PR-B-HW-SUITE by STUDY's valve and PR-M-S-SUITE-WC-DRAIN on STUDY's and LAUNDRY's legs.
_LOW_Z = inch(-9.625)
_LAUNDRY_Z = inch(-9.875)
#: KITCH passes under PR-M-S-SUITE-WC-DRAIN's south leg at x=12'-0".
_KITCH_Z = inch(-9.125)
#: A level end over a ceiling valve: 6" over a 107" ceiling's collar top, a stock 90 down onto
#: it (`resolve/terminal_drops.py`). LIVING and KITCH climb to it past their last crossing.
_DROP_Z = inch(-4)
#: The 6x4 neck's centreline where it crosses joist-0-026-1, the chase trimmers and the
#: 32' truss: 7.9" over the chord, the one height all four pass a 6x4 at x 57 1/8"..58 5/8".
_NECK_Z = inch(-3.975)

DUCTS_ERV_LEVEL2 = [
    # ** THE TRUNK IS FLAT AND RUNS IN THE D POCKETS AT x=27" (owner, 2026-11-07). ** The 8"
    # round fit no published J12 opening. R1 does not line up: x 54-70" north of the stair,
    # 101-117" south of it, and the BATH1 stack stands in the bay between. The D pockets'
    # 9x4 R2 do line up, at x=27" from y=0 to the chase, so an 8x4 runs straight south in
    # them. De 6.1" (Huebscher) at 114 cfm: notes/erv_static_budget.md §10.14.
    #
    # The 6x4 NECK reaches it from the plenum: up into the 413 3/4"..427 1/8" bay, south
    # across the chase trimmers and the 32' truss (the only lane an R2 shares with their R1),
    # west in the 352"..368" bay, then the 6x4-to-8x4 transition and a 30-degree drop to the
    # D-pocket height. Every takeoff leaves the trunk's side on a 4" spin collar and rides its
    # own bay.
    DuctRun(uid="AJKBQGRJTP", tag="DU-M-ERV-EXH-NECK", system=DuctSystem.EXHAUST,
            path=(pt(inch(57.5), inch(420)), pt(inch(57.5), inch(420)),
                  pt(inch(57.5), inch(360)), pt(inch(51.5), inch(360))),
            # (2026-11-12) The neck ends at x=51.5" (was 54"): the rect 90 at x=57.5" wants 6" of
            # straight before the transition, and the trunk's ramp starts there.
            elevations=(inch(-14.75), _NECK_Z, _NECK_Z, _NECK_Z),
            width=inch(6), depth=inch(4), routing=DuctRouting.JOIST_BAY,
            floor_ref="FS-S-WEST", material="galvanized", design_cfm=DU_M_ERV_EXH_TRUNK),
    DuctRun(uid="Y3G88SKSRG", tag="DU-M-ERV-EXH-TRUNK", system=DuctSystem.EXHAUST,
            # Capped 6" past BED2's take-off since the plant extract went (2026-11-12).
            path=(pt(inch(51.5), inch(360)), pt(inch(46), inch(360)), pt(inch(27), inch(360)),
                  pt(inch(27), ft(13, 6))),
            elevations=(_NECK_Z, _TRUNK_Z, _TRUNK_Z, _TRUNK_Z),
            width=inch(8), depth=inch(4), routing=DuctRouting.JOIST_BAY,
            floor_ref="FS-S-WEST", material="galvanized", design_cfm=DU_M_ERV_EXH_TRUNK),

    # --- THE THREE SUPPLY RADIALS -------------------------------------------------------
    # Home-run, and BLD-08 survives intact on this side: every fresh-air outlet still leaves
    # its own collar on its own damper. Three will lay and ten will not, and that asymmetry
    # is the whole of why the level split.
    #
    # Each rises off its own collar into the chase-trimmer bay and takes its own pocket lane
    # south on the upper tier (header table). STUDY and BED pass under the neck first.
    DuctRun(uid="2ZZ3MF5VAF", tag="DU-M-ERV-R-STUDY", system=DuctSystem.SUPPLY,
            # Under the neck to x 65", up at 25 deg to the upper tier, south in R1's x=106 7/8"
            # lane (the trusses' south chase, east of the vent string), over DU-M-ERV-R-LAUNDRY,
            # then a 45 down to the low tier in its own bay, north of LAUNDRY: the suite's pipes
            # fill the upper tier. Past PR-M-S-SUITE-TUB-DRAIN (x=155.8") it climbs 4.8" (to
            # just under PR-A-HW-STUBATH at x=168.7") and drops 4.76" onto REG-M-SUP4. The
            # stamped 90 needs 6"; the adjustable's 4.75" fits, there and at vertex 6
            # (2026-11-10, owner: "adjustable is fine"; notes/erv_static_budget.md §10.16).
            path=(pt(inch(58), inch(408.5)), pt(inch(58), inch(408.5)),
                  pt(inch(65.125), inch(408.5)), pt(inch(74.5), inch(408.5)),
                  pt(inch(106.875), inch(408.5)), pt(inch(106.875), inch(254.25)),
                  pt(inch(106.875), inch(248.6)), pt(inch(158.5), inch(248.6)),
                  pt(inch(163.325), inch(248.6)), pt(ft(14, 8), inch(248.6))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _STUDY_Z, _STUDY_Z, _STUDY_Z, _LOW_Z, _LOW_Z,
                        inch(-4.8), inch(-4.8)),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_STUDY, adjustable_elbows=(6, 9)),
    DuctRun(uid="MRH0QZT6NN", tag="DU-M-ERV-R-LIVING", system=DuctSystem.SUPPLY,
            # A BRANCH OF BED since 2026-11-11 (owner): a 4x4 tee on BED's x=83 3/4" pocket lane
            # at the 12'-8" bay, east in that bay, down 4" to the low tier under PR-M-CW-HYD-DIST's
            # x=96.5" leg and back up to _DROP_Z for the valve. It had its own collar, the 42 1/4"
            # lane south and a jog (46.6 ft, five turns); this is 20.7 ft. `collar-living` is
            # gone from EQ-T-ERV-PLENUM-M-SUP: the shop cuts two collars, not three.
            path=(pt(inch(83.75), ft(12, 8)), pt(inch(88), ft(12, 8)), pt(inch(94), ft(12, 8)),
                  pt(inch(99.5), ft(12, 8)), pt(inch(103.875), ft(12, 8)),
                  pt(ft(27), ft(12, 8))),
            elevations=(_UP_Z, _UP_Z, _BAY_Z, _BAY_Z, _DROP_Z, _DROP_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_LIVING),
    # 1/4" south of 34'-1" (2026-10-30): CD-M-DATA-KITCH-TRUNK's 1" EMT needs the 1" between
    # this duct's face and the truss at y=34'-4".
    DuctRun(uid="83MA15Q308", tag="DU-M-ERV-R-BED", system=DuctSystem.SUPPLY,
            # East under the neck, up over CD-M-DATA-KITCH, south in the D pockets at
            # x=83 3/4" on the upper tier, and straight down onto the valve in its own bay.
            path=(pt(inch(62), inch(404.125)), pt(inch(62), inch(404.125)),
                  pt(inch(67.4), inch(404.125)), pt(inch(74.4), inch(404.125)),
                  pt(inch(83.75), inch(404.125)), pt(inch(83.75), inch(71.25))),
            elevations=(_PORT_Z, _BAY_Z, _BAY_Z, _UP_Z, _UP_Z, _UP_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_BED),

    # --- THE TEN EXTRACT TAKEOFFS -------------------------------------------------------
    # Every one leaves the trunk (MUD the neck) on a 4x4 side tap at its own bay and rides that
    # bay low to its terminal; only BED2 and LAUNDRY cross a truss, each in its own D pocket.
    # A ceiling valve's run climbs past its last crossing and drops onto the collar (>= 2").
    DuctRun(uid="K04AT15S97", tag="DU-M-ERV-R-BATH1", system=DuctSystem.EXHAUST,
            path=(pt(inch(27), ft(24, 6)), pt(inch(22), ft(24, 6)),
                  pt(inch(17.625), ft(24, 6)), pt(ft(1), ft(24, 6))),
            elevations=(_BAY_Z, _BAY_Z, _DROP_Z, _DROP_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_BATH1),
    DuctRun(uid="BKE5RKVE8Z", tag="DU-M-ERV-R-VANITY", system=DuctSystem.EXHAUST,
            path=(pt(inch(27), ft(24, 10)), pt(ft(3), ft(24, 10))),
            elevations=(_BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_VANITY),
    DuctRun(uid="0DMX0NM8XS", tag="DU-M-ERV-R-BATH2", system=DuctSystem.EXHAUST,
            # A 45 pair 3" up, 5.7" before the valve's 90 (the stamped 45's 1.66" + the 90's 4").
            path=(pt(inch(27), inch(186.25)), pt(inch(43.3), inch(186.25)),
                  pt(inch(46.3), inch(186.25)), pt(ft(4, 4), inch(186.25))),
            elevations=(_BAY_Z, _BAY_Z, inch(-5.375), inch(-5.375)),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_BATH2),
    DuctRun(uid="P5H0GQ3E8N", tag="DU-M-ERV-R-MUD", system=DuctSystem.RETURN,
            # Off the neck's west face, level 5 1/2" to over the valve, and down onto it.
            path=(pt(inch(57.5), ft(31, 4)), pt(ft(4, 4), ft(31, 4))),
            elevations=(_NECK_Z, _NECK_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_MUD),
    # BED1 and BED2 end at floor boots (2026-10-02; mep_registers_second.py), each in an
    # FS-S-EAST bay, because I-joists take no north-south run. BED2's 18'-4" bay is not clear
    # west of x=16' (LAUNDRY, SUITEBATH, the suite WC and STUBATH drains, KITCH-VENT), so it
    # leaves the trunk in the 14'-0" bay and crosses north at x=16'-1 3/4"; since 2026-11-11
    # BED1 tees off that crossing and its boot is on BED1's north side (y=16'-8").
    # Both tails extend 4" east with the boots for the east PAX frames (2026-10-03).
    DuctRun(uid="HGMQ4AWG3S", tag="DU-M-ERV-R-BED2", system=DuctSystem.RETURN,
            # North on the low tier in the x=193 3/4" D pockets, between PR-M-KITCH-VENT and
            # PR-B-HW-SUITE's riser.
            path=(pt(inch(27), ft(14)), pt(inch(193.75), ft(14)), pt(inch(193.75), ft(18, 4)),
                  pt(ft(28, 1), ft(18, 4))),
            elevations=(_BAY_Z, _BAY_Z, _BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_BED2),
    DuctRun(uid="XA7NRRGJ50", tag="DU-M-ERV-R-BED1", system=DuctSystem.RETURN,
            # A BRANCH OF BED2 since 2026-11-11 (owner): a 4x4 tee on BED2's x=193 3/4" pocket
            # crossing, east in the 16'-8" bay (y 16'-1 1/4".."17'-2 7/8") to the north-side boot.
            # It left the trunk at y=9'-9" and ran 25.8 ft; this is 11.9 ft. REG-S-RET-BED1 moved
            # to y=16'-8", inside the room (y<17'-5"), clear of the y=17'-4" joist line.
            path=(pt(inch(193.75), ft(16, 8)), pt(ft(28, 1), ft(16, 8))),
            elevations=(_BAY_Z, _BAY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_BED1),
    DuctRun(uid="DPAS57TPCG", tag="DU-M-ERV-R-SUITEBATH", system=DuctSystem.EXHAUST,
            # Same lower-tier bay, now ending in W-S-DC2 rather than the wet floor
            # before the sink. The riser stays inside the 5 1/2" staggered cavity.
            # End at the bottom inlet of TH-ERV-SUITEBATH-BOOT-01, not at the
            # valve centre: the boot contains the final turn (notes/suitebath_extract.md).
            path=(pt(inch(27), inch(196)), pt(inch(115.5), inch(196)),
                  pt(inch(115.5), inch(196))),
            elevations=(_BAY_Z, _BAY_Z, inch(95.78125)),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_SUITEBATH),
    DuctRun(uid="ANSKB7EGDH", tag="DU-M-ERV-R-LAUNDRY", system=DuctSystem.RETURN,
            # Low tier the whole way, in the south half of its bay so DU-M-ERV-R-STUDY's 45
            # comes down north of it; south in the x=172 3/8" D pockets to the standpipe boot.
            path=(pt(inch(27), inch(244)), pt(inch(152), inch(244)),
                  pt(inch(172.375), inch(244)),
                  pt(inch(172.375), ft(18)), pt(inch(172.375), ft(18))),
            elevations=(_LAUNDRY_Z, _LAUNDRY_Z, _BAY_Z, _BAY_Z, inch(-108)),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_LAUNDRY),
    # REG-M-RET3 off LAUNDRY's crown (2026-11-10): a ceiling collar takes a run end, so the
    # valve moved into the next bay south and this branch reaches it up through R1's
    # x=106 7/8" opening at STUDY's height, where STUDY's lane stops one bay short.
    DuctRun(uid="J3E13FS8VT", tag="DU-M-ERV-R-RET3", system=DuctSystem.RETURN,
            path=(pt(inch(106.875), inch(244)), pt(inch(106.875), inch(244)),
                  pt(inch(106.875), ft(19, 4))),
            elevations=(_LAUNDRY_Z, _STUDY_Z, _STUDY_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_RET3),
    DuctRun(uid="YEXGZK2KW2", tag="DU-M-ERV-R-KITCH", system=DuctSystem.RETURN,
            # Under the suite's pipes, then up to _DROP_Z past PR-B-HW-SUITE (x=201.8").
            path=(pt(inch(27), ft(21, 9.75)), pt(inch(205), ft(21, 9.75)),
                  pt(inch(210.125), ft(21, 9.75)), pt(ft(20, 10.7), ft(21, 9.75))),
            elevations=(_KITCH_Z, _KITCH_Z, _DROP_Z, _DROP_Z),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=DU_M_ERV_R_KITCH),
]
