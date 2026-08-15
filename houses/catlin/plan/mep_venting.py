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
    # wall), so `mep.vent_reachability` is still satisfied by the wet-wall path. x=32'-8" is
    # the riser's bay — clear of WIN-M-KITCH's RO (29'-5".."31'-8"), WIN-M-KITCH-N's RO
    # (33'-5".."34'-7") and, one storey up, WIN-S-HALL-N's RO (26'-9".."29'-3" since the
    # 2026-07-30 facade pass stacked it on WIN-M-KITCH's column) — rather than
    # x=30'-7" under the sink itself, which sits inside two stacked window ROs. From there it
    # turns west in the same FS-SECOND joist bay as before, y=24'-8" (bays are 8"+n*16"; this
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

VENT_RISERS = [
    VentRun(uid="CMVR01AAAA", tag="VR-M-RADON-VENT",
            systems=(PipeSystem.RADON, PipeSystem.VENT), diameter=inch(3),
            chase_position=pt(ft(1), ft(34, 6)), start_elevation=ft(-8.5),
            exit_elevation=ft(23, 10), exit_offset=pt(ft(0), ft(2, 6)),
            wall_ref="W-A-N2", attachment="standing_seam_clamp"),
]

# S-5! standing-seam clamps fixing the exterior riser to the north gable siding. The riser
# spans 23'-10" to its derived termination, and the gable siding at x=1' stops at the
# 25'-5.7" rake, so all three clamps sit on the pipe *and* on cladding they can actually
# grip. The riser rides W-A-N2, the west half of the north gable wall (x=0..18); W-A-N1
# is the east half.
# These hold a *pipe*, so the part is an S-5! CanDuit ring on an S-5! seam clamp, not the
# bare clamp — the same assembly the roof leaders use (LEADER_CLAMPS below). The ring is
# selected on outer diameter, and 3" PVC DWV is 3.5" OD, which is the #11 (3.4-3.7") size;
# the 4" leaders take #13. Authoring the bare "S-5!" here billed brackets and no rings.
VENT_CLAMPS = [
    Connector(uid="CMVC01AAAA", tag="CN-M-VENT-CLAMP1", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(1), ft(37)), elevation=ft(24, 4), size="S-5! CanDuit #11",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
    Connector(uid="CMVC02AAAA", tag="CN-M-VENT-CLAMP2", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(1), ft(37)), elevation=ft(24, 10), size="S-5! CanDuit #11",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
    Connector(uid="CMVC03AAAA", tag="CN-M-VENT-CLAMP3", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(1), ft(37)), elevation=ft(25, 4), size="S-5! CanDuit #11",
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
            elevations=(ft(1, 6), ft(7, 8), ft(7, 9), ft(7, 10), ft(8, 0.5), ft(8, 1)),
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
            elevations=(ft(0, 6), ft(7, 4), ft(7, 6), ft(7, 8), ft(8, 0.5), ft(8, 1)),
            serves=("FX-B-SAUNA-SH", "FX-B-SAUNA-FD")),
]
