# haus: editable
# Catlin MEP — venting — the vent branches, the shared radon/plumbing riser and its clamps.
#
# Split out of the old 2,515-line plan/mep.py (AGENTS.md §1.1). Every element below moved
# verbatim; plan/mep.py still re-exports the storey lists, so the manifest is unchanged.
#
# `mep.vent_reachability` grades the authored path — nothing here is inferred, so an unvented
# fixture fails loudly rather than quietly. The fixtures these serve drain through
# plan/mep_drainage.py.

from typehaus import (
    Connector,
    ConnectorKind,
    PipeRun,
    PipeSystem,
    Service,
    VentRun,
    ft,
    inch,
    pt,
)

# --- Vent branches: wet wall -> shared chase ----------------------------------------
# None of the water-closet wet walls continues to the storey above (W-M-BAE and W-M-BA2E
# die at the main-floor top plate; W-S-BD-N dies under the cathedral attic), so no vent can
# simply rise inside them. They don't have to: VR-M-RADON-VENT below is already a shared
# radon/plumbing chase running the full height of the house at (1', 34'-6") — moved to the
# NW corner 2026-07-28, inside RM-M-MECH's framed closet and RM-S-BATH1's NW notch (was
# (3', 33'), floating in open mudroom floor space) — and a vent may run horizontally once
# it is above every served fixture's flood-level rim. These are the runs that get it
# there — authored, because the engine never routes pipe on its own, and validated by
# `mep.vent_reachability` (must touch the wet wall, must land on the chase).
#
# Both runs sit inside the floor system over their storey's 9' top plate, drilled through
# the I-joist webs, and fall ~1/8"/ft back toward the fixtures so condensate returns to the
# drainage system rather than pooling in the horizontal leg.
VENT_BRANCHES_MAIN = [
    # Bath2 takeoff on W-M-BA2E (x=8') -> across the hall -> bath1 takeoff on W-M-BAE
    # (x=6') -> north through the storage-room ceiling -> chase. 2" for two water closets.
    PipeRun(uid="CMP906AAAA", tag="PR-M-WC-VENT", system=PipeSystem.VENT,
            path=(pt(ft(2, 3.6), ft(17, 3.6)), pt(ft(8), ft(18)), pt(ft(8), ft(24)), pt(ft(6), ft(24)),
                  pt(ft(6), ft(34, 6)), pt(ft(1), ft(34, 6))),
            diameter=inch(2), start_elevation=ft(9, 3), end_elevation=ft(9, 5.5),
            # FX-M-BATH1-LAV joined on 2026-07-30, when FX-LAV-COMPACT finally declared
            # Service.VENT. No new pipe: this run's x=6' leg is W-M-BAE's own stud bay and it
            # passes 1'-0" north of the lavatory's drain point at (6', 23'), so the trap arm
            # ties into the leg already drawn there — well inside Table 1002.2's 42" for 1.5".
            # FX-M-LAUNDRY-SINK joined on 2026-07-31, on the same terms: this run's x=8' leg is
            # W-M-BA2E's own stud bay and PR-B-LSINK-DRAIN arrives against that wall 3" south
            # of the leg's start, so the tub wet-vents off the laundry stack with no new pipe.
            # The trap arm is the 45" that branch runs below the deck, inside Table 1002.2's
            # 60" for 2". The washer itself needs no entry — an Appliance declares no
            # Service.VENT — but its standpipe (PR-M-WASH-STANDPIPE) is the physical riser
            # this tee sits beside.
            serves=("FX-M-BATH2-WC", "FX-M-BATH1-WC", "FX-M-BATH2-SH",
                    "FX-M-BATH2-TUB", "FX-M-BATH1-LAV", "FX-M-LAUNDRY-SINK")),
    # Kitchen sink. Re-routed 2026-07-30 with the sink's move to the north wall: W-M-N1
    # *does* continue to the storey above at this x (W-S-N1 stacks on it, into RM-S-BED3's
    # wall), so `mep.vent_reachability` is still satisfied by the wet-wall path. x=32'-8"
    # does not move with the 2026-08-26 sink/column move — it stays clear of WIN-M-KITCH's
    # RO (28'-2 1/2".."30'-5 1/2"), WIN-M-KITCH-N's RO (33'-5".."34'-7", unaffected — that
    # corner window did not move) and, one storey up, WIN-S-HALL-N's RO (28'-1".."30'-7"
    # since its column moved to 29'-4" with WIN-M-KITCH) — rather than under the sink
    # itself, which sits inside two stacked window ROs. From there it
    # turns west in the same joist bay as before (FS-S-EAST here, FS-S-WEST once it crosses
    # x=18'), y=24'-8" (bays are 8"+n*16"; this
    # one passes south of FO-S-STAIR, which starts at y=25'-2 3/8", and north of both trunk
    # ducts at 20'-8" and 23'-4"), then north to the shared radon/vent chase at (1', 34'-6").
    # It rises 6" over its length so condensate drains back to the fixture.
    PipeRun(uid="ZTQRPPRATP", tag="PR-M-KITCH-VENT", system=PipeSystem.VENT,
            path=(pt(ft(32, 8), ft(35, 9)), pt(ft(32, 8), ft(24, 8)),
                  pt(ft(1), ft(24, 8)), pt(ft(1), ft(34, 6))),
            diameter=inch(1.5), start_elevation=ft(9, 3), end_elevation=ft(9, 9),
            serves=("FX-M-KITCH-SINK",)),
]

VENT_BRANCHES_SECOND = [
    # Hall-bath takeoff on W-S-BD-N (y=26'-4") -> west to the chase line -> north to the
    # chase.
    PipeRun(uid="CSP901AAAA", tag="PR-S-BATH1-VENT", system=PipeSystem.VENT,
            path=(pt(ft(9, 8.4), ft(31)), pt(ft(5), ft(26, 4)), pt(ft(1), ft(26, 4)),
                  pt(ft(1), ft(34, 6))),
            diameter=inch(2), start_elevation=ft(9, 3), end_elevation=ft(9, 4),
            serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    # The suite bath's own vent: takeoff on its west wet wall W-S-DC2 (x=9'-7 1/2"), north
    # through the landing and the hall bath, then west along y=34'-6" to the shared
    # radon/plumbing chase. It runs up the x=9'-7 1/2" line rather than joining the hall
    # bath's run at x=1' so the two branches never share a leg.
    #
    # The chase here is VR-M-RADON-VENT's, at (1', 34'-6") — now the *same* shaft as the
    # 2'x2' mechanical chase in the hall bath's NW corner (W-S-CH-W/CH-S, moved there
    # 2026-07-28 from the NE corner specifically so it could carry this riser; storeys/
    # second.py).
    PipeRun(uid="CSP902AAAA", tag="PR-S-SUITEBATH-VENT", system=PipeSystem.VENT,
            path=(pt(ft(13, 10), ft(16)), pt(ft(9, 7.5), ft(20)),
                  pt(ft(9, 7.5), ft(34, 6)), pt(ft(1), ft(34, 6))),
            diameter=inch(2), start_elevation=ft(9, 3), end_elevation=ft(9, 5),
            serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
]

VENT_BRANCHES_ATTIC = [
    # The guest studio's bath and wet bar (2026-08-29).
    #
    # ** AN OFFSET VENT IS MANDATORY HERE, NOT A CHOICE. ** `mep.vent_reachability` passes a
    # fixture outright when its `wall_ref` is in `stacked_lower` — and NO ATTIC WALL CAN EVER
    # BE, because nothing stacks on the top storey. Every fixture up here needs an authored run.
    #
    # ** IT STARTS OVER THE SHOWER, AND THAT IS `mep.trap_arm_length`, NOT AESTHETICS. ** The
    # check measures to the nearest point of the serving run. Starting it at the wet-wall axis
    # x=9'-7 1/2" would give the shower a 6'-7 1/8" arm against Table 1002.2's 5'-0" for 2" — a
    # FAIL. Starting at (16'-2 5/8", 20'-8"), directly over the pan, makes the shower's arm ~0
    # and leaves the others clear: WC 1'-5 3/8" (limit 6'-0"), lav 10 3/8" (limit 3'-6"), bar
    # sink ~1'-0".
    #
    # From there it runs west to the W-A-STU-W axis, north through the pocket at ~7'-0", and
    # west to VR-M-RADON-VENT at (1'-0", 34'-6"), which carries PipeSystem.VENT to the roof. It
    # mirrors PR-S-SUITEBATH-VENT one storey down — same x=9'-7 1/2" leg, same y=34'-6" turn,
    # same chase.
    #
    # ** DO NOT INSTEAD ADD THESE FIXTURES TO PR-S-SUITEBATH-VENT.serves. ** `vent_path.py` is
    # purely 2D and would PASS it — but that run sits at 9'-3", BELOW these fixtures' flood-level
    # rims. That is gaming the check. This run is 32' of 2" PVC and it is real.
    # ** ELEVATIONS ARE STOREY-RELATIVE AND THE ATTIC DATUM IS ft(20). ** Authored as project
    # elevations (27'-0"/27'-6") until 2026-08-29, this run resolved 20'-0" too high and hung
    # over the roof. Nothing caught it: `_resolve_pipe_run` adds the datum silently and no check
    # grades a pipe against the roof plane it sits under.
    #
    # The profile is per-vertex rather than a start/end ramp because THE RAKE FORCES A DUCK AT
    # THE WEST END. RF-HOUSE bears at 25'-0" over a 5'-0" knee wall and rises 4:12 to the x=18'
    # ridge, so its underside is 28'-10" at x=9'-7 1/2" but only 25'-4 3/4" at x=1'-0". The
    # plan's "~7'-0" through the pocket" holds on the north leg and cannot hold on the last one.
    #
    # Every vertex clears the flood-level rims by more than P3104.4's 6": the highest rim served
    # is the lavatory at ~2'-10" AFF (22'-10"), so 23'-4" is the floor for a dry horizontal vent
    # and the lowest vertex here is 23'-6". Vertex 3 is the high point; condensate drains off it
    # both ways — back to the fixtures on one side, into the stack on the other — so there is no
    # pocket to hold water.
    PipeRun(uid="STFQKR8Q95", tag="PR-A-STUBATH-VENT", system=PipeSystem.VENT,
            path=(pt(ft(16, 2.625), ft(20, 8)), pt(ft(9, 7.5), ft(20, 8)),
                  pt(ft(9, 7.5), ft(34, 6)), pt(ft(1), ft(34, 6))),
            diameter=inch(2),
            elevations=(ft(3, 6), ft(6, 6), ft(7), ft(4)),
            serves=("FX-A-STUBATH-WC", "FX-A-STUBATH-LAV", "FX-A-STUBATH-SH",
                    "FX-A-STUDIO-BAR-SINK")),
]

VENT_RISERS = [
    VentRun(uid="CMVR01AAAA", tag="VR-M-RADON-VENT",
            systems=(PipeSystem.RADON, PipeSystem.VENT), diameter=inch(3),
            chase_position=pt(ft(1), ft(34, 6)), start_elevation=ft(-8, -10),
            exit_elevation=ft(23, 10), exit_offset=pt(ft(0), ft(2, 6)),
            wall_ref="W-A-N2", attachment="pipe_strap"),
]

# Through-panel straps fixing the exterior riser to the north gable siding. The riser spans
# 23'-10" to its derived termination, and the gable siding at x=1' stops at the 25'-5.7"
# rake — so all three fixings, at 24'-4" / 24'-10" / 25'-4", sit on the pipe *and* on WALL
# cladding, not on roof. That is the question that decides the part, and it was checked:
# a fixing that had landed above the rake would be on `standing-seam` roofing and would
# have stayed on the CanDuit ring. The riser rides W-A-N2, the west half of the north gable
# wall (x=0..18); W-A-N1 is the east half.
#
# These hold a *pipe*, and until 2026-08-26 the part was an S-5! CanDuit #11 ring on an
# S-5! seam clamp. The gable wall is now `pbr-panel-26`, an exposed-fastener panel with no
# seam, and the ring's `requires_role=ROLE_STANDING_SEAM_CLAMP` would order a bracket with
# nothing to grip — so this follows the roof leaders (plan/mep_electrical.py LEADER_CLAMPS)
# onto the 316 stainless standoff strap, screwed through the panel into the girt.
#
# Sizing is unchanged and is still on OUTER diameter: 3" PVC DWV is 3.5" OD, which is the
# **#11** (3.4-3.7") size; the 4" leaders take #13. Authoring a bare part family here once
# billed brackets and no rings, which is why the size suffix stays.
VENT_CLAMPS = [
    Connector(uid="CMVC01AAAA", tag="CN-M-VENT-CLAMP1", kind=ConnectorKind.PIPE_STRAP,
              position=pt(ft(1), ft(37)), elevation=ft(24, 4), size="SS316-STANDOFF-STRAP #11",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
    Connector(uid="CMVC02AAAA", tag="CN-M-VENT-CLAMP2", kind=ConnectorKind.PIPE_STRAP,
              position=pt(ft(1), ft(37)), elevation=ft(24, 10), size="SS316-STANDOFF-STRAP #11",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
    Connector(uid="CMVC03AAAA", tag="CN-M-VENT-CLAMP3", kind=ConnectorKind.PIPE_STRAP,
              position=pt(ft(1), ft(37)), elevation=ft(25, 4), size="SS316-STANDOFF-STRAP #11",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
]
# The basement's two plumbing vents. Both are offset vents to VR-M-RADON-VENT's shared
# radon/plumbing chase at (1', 34'-6"), because neither room has a wet wall that continues to
# the storey above: every wall around the stair-foot bathroom except its own north partition
# is 12" cast concrete stopping at the main-floor deck, and the sauna's are a 2x4 partition,
# the centre concrete wall and the foundation. `mep.vent_reachability` grades the authored
# path — nothing here is inferred, so an unvented fixture would still fail loudly.
#
# Both share the same vertical band: the tee sits low, the riser goes up inside the room's own
# stud cavity, and the horizontal leg tops out at 8'-1" basement-relative rather than 8'-3",
# because the "basement ceiling" here is 9" of cast concrete and a run at the deck's underside
# would be cast into it (which `mep.sleeve_coverage` caught the first time it was tried). Each
# rises a few inches over its length to the chase so condensate drains back to the fixtures.
#
# Neither shares a leg with the other — the bathroom's runs north at x=7', the sauna's at
# x=9' — the same rule PR-S-SUITEBATH-VENT follows against the hall bath's branch.
VENT_BRANCHES_BASEMENT = [
    # RM-B-BATH. Was PR-B-UTIL-VENT, FX-1's vent, until 2026-07-30: same uid, same corridor
    # north at x=7' to the chase, new fixtures at the near end. The riser now stands in a real
    # stud cavity for the first time — W-B-BA-N, the bathroom's INT_2X6_STAGGERED_PLUMBING
    # north partition — instead of boxed onto a concrete face, which is what that wall's
    # assembly was chosen for. It crosses W-B-STR's concrete through SP-B-STR-BATH-VENT.
    #
    # The riser stands on the partition's line at (16', 21'-9 3/8"); the leg west runs 9"
    # south of it at y=21'-0", so its crossing of W-B-STR2 stays clear of the node the
    # partition tees into. Trap arms measured to that leg: 1'-0" from the water closet's
    # flange and 1'-5" from the lavatory's trap, against Table 1002.2's 6'-0" for 3" and
    # 3'-6" for 1 1/2".
    PipeRun(uid="CBPV01AAAA", tag="PR-B-BATH-VENT", system=PipeSystem.VENT,
            path=(pt(ft(16), ft(21, 9.375)), pt(ft(16), ft(21, 9.375)),
                  pt(ft(16), ft(21)), pt(ft(7), ft(21)), pt(ft(7), ft(34, 6)),
                  pt(ft(1), ft(34, 6))),
            diameter=inch(1.5), material="pvc",
            elevations=(ft(1, 3.4375), ft(7, 5.4375), ft(7, 6.4375), ft(7, 7.4375), ft(7, 9.9375), ft(7, 10.4375)),
            serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    # RM-B-SAUNA's shower group. 2" for 4 DFU, rising at (17'-4", 13'-0") — inside W-B-CS's
    # 3 1/2" liner build-up, in the pan's own east wall, 6" south of the north liner and clear
    # of the mixer's two supply drops at 11'-10" and 12'-2". That is both fixtures' declared
    # wet wall (plan/fixtures.py) and the one basement wet wall that carries a framed wall on
    # the storey above, so the vent has a true stack path as well as this drawn one.
    #
    # Trap arms as the check measures them: 14" from the pan's drain and 23" from the floor
    # drain, against Table 1002.2's 5'-0" for a 2" arm. Above the sauna's hung ceiling the run leaves
    # the build-up north over W-B-SA-N, crosses the aisle west, and passes W-B-CW through
    # SP-B-CW-SAUNA-VENT at x=9'.
    PipeRun(uid="CBPV02AAAA", tag="PR-B-SAUNA-VENT", system=PipeSystem.VENT,
            path=(pt(ft(17, 4), ft(13)), pt(ft(17, 4), ft(13)),
                  pt(ft(17, 4), ft(14, 8)), pt(ft(9), ft(14, 8)),
                  pt(ft(9), ft(34, 6)), pt(ft(1), ft(34, 6))),
            diameter=inch(2), material="pvc",
            elevations=(ft(0, 3.4375), ft(7, 1.4375), ft(7, 3.4375), ft(7, 5.4375), ft(7, 9.9375), ft(7, 10.4375)),
            serves=("FX-B-SAUNA-SH", "FX-B-SAUNA-FD")),
]
