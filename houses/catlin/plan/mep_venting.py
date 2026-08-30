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
            # FX-M-BATH2-WC LEFT THIS RUN on 2026-08-29 and did not need replacing. It had
            # to be here while the bowl stood free in the middle of RM-M-BATH2's floor with
            # no wall to rise in; backing it onto W-M-HS1 gave it one, and W-S-SN1 stacks
            # directly over that wall on the storey above, so the vent now goes up in-wall
            # for two storeys instead of jogging into this chase. `mep.vent_reachability`
            # says so in as many words ("wall W-M-HS1 continues up for the vent"). Leaving
            # the tag here would have recorded a chase the bowl no longer uses.
            serves=("FX-M-BATH1-WC", "FX-M-BATH2-SH",
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
            path=(pt(ft(9, 8.4), ft(31)), pt(ft(5), ft(26, 6)), pt(ft(1), ft(26, 6)),
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
    # ** REWRITTEN THE SAME DAY FOR THE 6:12 ROOF, AND THE DUCK IS GONE. ** The profile used to
    # run 3'-6" / 6'-6" / 7'-0" / 4'-0", ducking 3'-0" at the last vertex because the old 4:12
    # roof over a 5'-0" knee wall left only 25'-4 3/4" at x=1'-0". The underside is
    # `20'-0" + 1 1/2" + x/2` now, which is 20'-8 1/4" at x=1'-0" — there is no duck deep
    # enough. So the run does not go to x=1'-0" at all: it ends on the riser, and since
    # 2026-08-30 the riser stands on THIS RUN'S OWN WET-WALL LINE at x=9'-7 1/2" (it detoured
    # to 13'-4" for a day; see VR-M-RADON-VENT below). That deletes the last leg rather than
    # shortening it — there is no turn east to meet the stack any more, because the stack is
    # already on the wall this vent climbs. The whole profile flattens to a 4" rise over 28',
    # which is what a dry vent wants anyway.
    #
    # The vertex at (9'-7 1/2", 20'-8") is what `mep.vent_reachability` reads — it requires a
    # vertex ON the served fixtures' wet wall (W-A-STU-W's axis). It used to be the only one
    # on that line, because the run doubled back east to reach the stack; now the whole north
    # leg is on it.
    #
    # Every vertex clears the flood-level rims by more than P3104.4's 6": the highest rim served
    # is the lavatory at ~2'-10" AFF (22'-10"), so 23'-4" is the floor for a dry horizontal vent
    # and the lowest vertex here is 23'-5". It rises monotonically into the stack, so condensate
    # drains back to the fixtures and there is no pocket to hold water. The last vertex at
    # 23'-9" ties in 1" BELOW the riser's 23'-10" exit, on the vertical part of the stack.
    PipeRun(uid="STFQKR8Q95", tag="PR-A-STUBATH-VENT", system=PipeSystem.VENT,
            path=(pt(ft(16, 2.625), ft(20, 8)), pt(ft(9, 7.5), ft(20, 8)),
                  pt(ft(9, 7.5), ft(34, 6))),
            diameter=inch(2),
            elevations=(ft(3, 5), ft(3, 6), ft(3, 9)),
            serves=("FX-A-STUBATH-WC", "FX-A-STUBATH-LAV", "FX-A-STUBATH-SH",
                    "FX-A-STUDIO-BAR-SINK")),
]

# ** THE STACK JOGS EAST INSIDE THE ATTIC SINCE 2026-08-29, AND IT DOES NOT MOVE. **
# `chase_position` is still (1'-0", 34'-6"): the shaft runs the full height of the house
# through RM-M-MECH's framed closet and RM-S-BATH1's NW notch, and relocating it would drag
# a penetration through every storey below to solve a problem that only exists in the top
# one. What changed is the top one. At x=1'-0" the 6:12 roof underside is 20'-8 1/4" — the
# riser cannot rise there at all, let alone reach the 23'-10" wall exit.
#
# So it jogs, and it jogs BELOW THE DECK: `chase_offset_elevation` 19'-6" is inside
# FS-ATTIC's 11 7/8" I-joist band (19'-0 7/8"..20'-0"), so the 3" pipe crosses through the
# joist WEBS — the ordinary place a stack offsets, and 12'-4" of it in a bay that already
# carries PR-A-STUBATH-VENT's line. It comes up at x=13'-4" and everything above is as it
# was: exit at 23'-10" through the gable, 2'-6" out, up the cladding to a derived
# termination. ** NO ROOF PENETRATION ANYWHERE **, which was the point.
#
# ** IT MOVED 13'-4" -> 9'-7 1/2" ON 2026-08-30, WEST OF WIN-A-N1 AND ONTO THE WET WALL. **
# At 13'-4" the riser stood on top of that window: WT-3036 is 30" wide on a 12'-0" centre, so
# its rough opening runs x 10'-9"..13'-3", and the riser is a PAIR of 3" pipes straddling its
# station about 7 3/4" overall — at 13'-4" that put pipe inside the opening it was meant to
# miss. Nothing failed, because no check grades a riser against a window it runs beside, but
# it is unbuildable as drawn: the standoff straps have no cladding to land on and the window
# trim has nowhere to die.
#
# ** MEASURE THE TERMINATION, DO NOT DERIVE IT IN A COMMENT. ** The station was first moved
# to 10'-6" on arithmetic that put the exhaust at 27'-2 3/8" and the pipe 1 1/4" clear of the
# opening. Both were wrong — the resolved termination is a foot higher than that hand figure,
# and the pair straddles its station rather than sitting on it, so 10'-6" actually OVERLAPPED
# the rough opening by about an inch. The numbers below are read off the resolved model.
#
# So the constraint is much looser than it looked. MN 1303.2402 subp. 5 wants the exhaust
# 2'-0" over WIN-A-N1's 25'-0" head or 10'-0" away in plan; the termination sits 12" over the
# rake, which measures 27'-8 3/4" at this station and falls 1/2" per inch travelled west, so
# subpart 5 holds anywhere east of x=8'-2". That is a six-foot band, not the 7 3/4" the first
# attempt thought it had.
#
# 9'-7 1/2" is chosen from inside that band because it is **PR-A-STUBATH-VENT's own wet-wall
# line**, which is where plans/ wanted this riser before the 13'-4" detour. Landing on it
# deletes that run's last leg outright: the bath vent now goes up the wet wall and straight
# into the stack instead of turning east for 3'-8" to meet it. Measured:
#   * riser pair x 9'-3 5/8"..9'-11 3/8", so 9 5/8" clear of WIN-A-N1's west jamb;
#   * termination 27'-8 3/4", 2'-8 3/4" over the window head (subpart 5 wants 2'-0");
#   * the under-deck jog is 8'-7 1/2" of 3" PVC in the FS-ATTIC band, down from 12'-4".
#
# One consequence follows the station: the wall it exits through is W-A-N2 again (x 10'..0'),
# not W-A-N2B — 9'-7 1/2" is west of the north gable's x=10'-0" split, so this reverts to the
# ref it carried before 2026-08-29. 115 1/2" is not 0 mod 16 and does not need to be: the
# riser is outboard of the sheathing on standoff straps and grips a girt, not a stud, and the
# jog crosses I-joist webs at 19'-6" whose 16" grid is fixed whatever this run does.
#
VENT_RISERS = [
    VentRun(uid="CMVR01AAAA", tag="VR-M-RADON-VENT",
            systems=(PipeSystem.RADON, PipeSystem.VENT), diameter=inch(3),
            chase_position=pt(ft(1), ft(34, 6)), start_elevation=ft(-8, -10),
            chase_offset=pt(ft(8, 7.5), ft(0)), chase_offset_elevation=ft(19, 6),
            exit_elevation=ft(23, 10), exit_offset=pt(ft(0), ft(2, 6)),
            wall_ref="W-A-N2", attachment="pipe_strap"),
]

# Through-panel straps fixing the exterior riser to the north gable siding. The riser spans
# 23'-10" to its derived termination, and the gable siding at x=9'-7 1/2" runs to a 26'-8 3/4"
# rake — so all three fixings, at 24'-4" / 24'-10" / 25'-4", sit on the pipe *and* on WALL
# cladding, not on roof, with 1'-4 3/4" to spare on the top one. That is the question that
# decides the part, and it was checked: a fixing that had landed above the rake would be on
# `standing-seam` roofing and would have stayed on the CanDuit ring.
#
# ** ALL THREE MOVED x 1'-0" -> 13'-4" ON 2026-08-29, THEN 13'-4" -> 9'-7 1/2" ON 2026-08-30 **
# with the riser, and the wall they connect to went W-A-N2B -> W-A-N2 with it: 9'-7 1/2" is
# west of the north gable's x=10'-0" split. The 6:12 rake is what bought the headroom in the
# first place — at the original x=1'-0" the gable stopped at 20'-8 1/4" and none of these three
# had any cladding at all to grip. Going back west spends part of that margin (2'-3" of rake
# clearance becomes 1'-4 3/4") and it is still the top clamp, at 25'-4", that decides it.
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
              position=pt(ft(9, 7.5), ft(37)), elevation=ft(24, 4), size="SS316-STANDOFF-STRAP #11",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
    Connector(uid="CMVC02AAAA", tag="CN-M-VENT-CLAMP2", kind=ConnectorKind.PIPE_STRAP,
              position=pt(ft(9, 7.5), ft(37)), elevation=ft(24, 10), size="SS316-STANDOFF-STRAP #11",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
    Connector(uid="CMVC03AAAA", tag="CN-M-VENT-CLAMP3", kind=ConnectorKind.PIPE_STRAP,
              position=pt(ft(9, 7.5), ft(37)), elevation=ft(25, 4), size="SS316-STANDOFF-STRAP #11",
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
