# haus: editable
# Catlin MEP — venting — the vent branches, the shared radon/plumbing riser and its clamps.
#
# plan/mep.py re-exports the storey lists below (AGENTS.md §1.1), so the manifest is
# unchanged.
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
# radon/plumbing chase running the full height of the house at (1', 35'-1.3"), inside
# RM-M-MECH's framed closet and RM-S-BATH1's NW notch, and a vent may run horizontally once
# it is above every served fixture's flood-level rim. These are the runs that get it
# there — authored, because the engine never routes pipe on its own, and validated by
# `mep.vent_reachability` (must touch the wet wall, must land on the chase).
#
# Both runs sit inside the floor system over their storey's 9' top plate, drilled through
# the I-joist webs, and fall ~1/8"/ft back toward the fixtures so condensate returns to the
# drainage system rather than pooling in the horizontal leg.
VENT_BRANCHES_MAIN = [
    # W-M-BAE (x=6') and W-M-BA2E (x=8'-2") -> UP W-S-SN2 -> the hall-bath vent. 2" for
    # the two water closets' worth of fixtures, plus the kitchen sink tied in below.
    # ** IT RISES THROUGH THE SECOND STOREY SINCE 2026-09-24. ** DU-M-ERV-EXH-TRUNK fills
    # FS-S-WEST's truss window at x=3'-10 1/2", so nothing crosses to the chase in-band. Upper
    # tier east on y=25'-0" to W-M-BA2E's line, south to 22'-4 7/8", up W-S-SN2's cavity, then
    # north in FS-ATTIC's band onto PR-S-BATH1-VENT's first leg, rising all the way.
    PipeRun(uid="CMP906AAAA", tag="PR-M-WC-VENT", system=PipeSystem.VENT,
            path=(pt(inch(74.5), inch(300)), pt(inch(98.5), inch(300)),
                  pt(inch(98.5), inch(268.9)), pt(inch(98.5), inch(268.9)),
                  pt(inch(98.5), inch(354.9))),
            diameter=inch(2),
            elevations=(inch(115.9), inch(116), inch(116.05), inch(231), inch(231.1)),
            # FX-M-BATH1-LAV: no new pipe needed — this run starts over W-M-BAE, 2'-0" north
            # of the lavatory's drain point at (6', 23'), so the trap arm rises into it —
            # well inside Table 1002.2's 42" for 1.5". FX-M-LAUNDRY-SINK, same terms: the
            # x=8'-2 1/2" leg runs over W-M-BA2E and PR-B-LSINK-DRAIN arrives against that
            # wall, so the tub wet-vents off the laundry stack with no new pipe. The
            # trap arm is the 45" that branch runs below the deck, inside Table 1002.2's 60"
            # for 2". The washer itself needs no entry — an Appliance declares no
            # Service.VENT — but its standpipe (PR-M-WASH-STANDPIPE) is the physical riser
            # this tee sits beside.
            # FX-M-BATH2-WC is NOT on this run: it backs onto W-M-HS1, and W-S-SN1 stacks
            # directly over that wall on the storey above, so the vent goes up in-wall for
            # two storeys instead of jogging into this chase. `mep.vent_reachability` says
            # so in as many words ("wall W-M-HS1 continues up for the vent").
            serves=("FX-M-BATH1-WC", "FX-M-BATH1-LAV")),
    # BATH2's shower and tub and the laundry sink: from 58" east of the shower's authored
    # drain point (1'-9", 17'-3") along the 16'-8" bay, then up W-M-BA2E's line on the upper
    # tier onto WC-VENT's riser foot. On one run with WC-VENT their trap arms were 99" and
    # 61" against Table 1002.2's 60" (2026-09-24).
    PipeRun(uid="YTKPDYS5YV", tag="PR-M-BATH2-VENT", system=PipeSystem.VENT,
            path=(pt(inch(79), inch(204)), pt(inch(98.5), inch(204)),
                  pt(inch(98.5), inch(266.5))),
            diameter=inch(2), start_elevation=inch(115.9), end_elevation=inch(116),
            serves=("FX-M-BATH2-SH", "FX-M-BATH2-TUB", "FX-M-LAUNDRY-SINK")),
    # Kitchen sink. The takeoff is on W-M-N1 at x=32'-8", clear of WIN-M-KITCH's RO
    # (28'-2 1/2".."30'-5 1/2") and WIN-M-KITCH-N's (33'-5".."34'-7"); south to y=19'-4",
    # which crosses x=18' over W-M-C3 (24'-8" ran through BM-M-HALL's flush LVL).
    # ** INTO PR-M-BATH2-VENT SINCE 2026-09-24, NOT THE CHASE ** (`haus route --run
    # PR-M-KITCH-VENT --hold-upstream 1`); the old way crossed ten things. West at 19'-4",
    # held low (1/32"/ft) under PR-B-CW-SUITE, south in the 15'-4 1/2" opening, west at
    # 17'-8 3/4" over DU-M-ERV-R-SUITEBATH, and up at x=8'-2 1/2".
    PipeRun(uid="ZTQRPPRATP", tag="PR-M-KITCH-VENT", system=PipeSystem.VENT,
            path=(pt(ft(32, 8), ft(35, 9)), pt(ft(32, 8), ft(19, 4)),
                  pt(ft(15, 7.3125), ft(19, 4)), pt(ft(15, 7.3125), ft(17, 8.75)),
                  pt(inch(98.5), ft(17, 8.75)), pt(inch(98.5), ft(17, 8.75))),
            diameter=inch(1.5),
            elevations=(ft(9, 3), ft(9, 4), inch(112.5), inch(114.45), inch(115.9), inch(116)),
            serves=("FX-M-KITCH-SINK",)),
]

VENT_BRANCHES_SECOND = [
    # Hall-bath takeoff on W-S-BD-N (y=26'-4") -> west to the chase line -> north to the
    # chase.
    PipeRun(uid="CSP901AAAA", tag="PR-S-BATH1-VENT", system=PipeSystem.VENT,
            # ** IT TIES INTO THE STACK'S JOG SINCE 2026-09-23, NOT THE CHASE. ** North on
            # x=3'-4" in FS-ATTIC's joist band to the vent riser's 19'-6" jog, east of the
            # chase hole — a run that spanned FO-A-ERV-CHASE had nothing to strap to.
            path=(pt(ft(9, 8.4), ft(31)), pt(ft(5), ft(26, 6)), pt(ft(3, 4), ft(26, 6)),
                  pt(ft(3, 4), inch(412.9))),
            diameter=inch(2),
            elevations=(ft(9, 3), ft(9, 3.3), ft(9, 3.5), ft(9, 6)),
            serves=("FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
                    "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")),
    # The suite bath's own vent. THE TAKEOFF IS ON W-S-SN3, THE NORTH WALL: all three of
    # this room's fixtures stand against the north wall or the east one; NOT ONE touches
    # W-S-DC2 (`plan/fixtures.py`). So the run is a header ALONG SN3, at y=21'-11" — 1 5/8"
    # inboard of SN3's 264 5/8" face, in the bath's own ceiling, which is where a vent header
    # is actually run — taking off at x=16'-4 1/2" directly over the tub-shower, picking up
    # all three fixtures on its way west, and turning north at N-S-D4:
    #   * every trap arm is short: the header measures 39" to the tub-shower against Table
    #     1002.2's 72" for 3"; the lav's is 0" (the header passes straight over its basin)
    #     and the WC's is 17".
    #   * the x=9'-7 1/2" riser bores no FS-ATTIC joists — the header runs *along* a bay,
    #     y=21'-11" sitting inside the 22'-0" bay.
    #   * it does not run inside W-S-DC2 at all — the riser is entirely NORTH of that wall,
    #     which ends at y=22'-4".
    # THAT DOES NOT FREE W-S-DC2 TO BECOME A THIN WALL. It still carries the attic studio
    # bath's own risers — PR-A-STUBATH-DRAIN drops 10'-0" inside it and PR-A-CW/HW-STUBATH
    # rise through it into W-A-STU-W — so it stays a full-depth 5.5" cavity for their sake,
    # not for this run's. See plan/fixtures.py.
    #
    # THE HEADER IS 1 5/8" OFF THE WALL RATHER THAN ON ITS AXIS: y=22'-4" itself is the axis
    # W-M-HS3/W-M-HS4 share ONE STOREY DOWN, and x 12'-4"..16'-5" of that line is D-M-LAUN's
    # pocket, the cavity CLAUDE.md says nothing may ever enter. `mep.pocket_occupancy` is
    # purely 2D — `_pocket_bands` buffers the pocket wall's axis in plan and tests every
    # `PipeRun` segment against it with no storey and no elevation filter, so a vent sitting
    # 9'-3" above the SECOND floor trips a pocket on the MAIN one. Physically there is no
    # conflict whatever — but routing round it costs nothing and is the better line anyway
    # (it is what takes the tub-shower's arm to 39"). If that check is ever made
    # storey-aware, this header may go back on the axis.
    #
    # It turns north on the x=9'-7 1/2" line rather than joining the hall bath's run at x=1',
    # and at x=9'-7 1/2" that north leg is well clear of the pocket's x 12'-4"..16'-5" band.
    #
    # ** IT IS NOT BECAUSE "THE TWO BRANCHES MAY NEVER SHARE A LEG". ** That argument stood
    # here and it was wrong: two branch vents on a common vent is ordinary IRC P3104 work,
    # and the owner overruled it on 2026-09-18. What replaced it is a MEASUREMENT, and the
    # measurement says the merge costs rather than saves.
    #
    # `haus route --run PR-S-BATH1-VENT` (which can now propose a merge at all — see
    # `cli/route_support._vent_siblings`) reports that PR-S-BATH1-VENT's FIRST vertex
    # (9'-8.4", 31'-0") already stands 0.9" off this run's north leg. That reads like an
    # 18.5 ft saving and it is not one: that vertex is the hall-bath run's far EAST end and
    # it serves nothing. Its five fixtures are all at x ~ 1'-10" (fixtures.py) and are picked
    # up on its (1', 26'-6") leg. Joining here would take the header 8'-7" EAST to this line,
    # which then carries it 8'-7" back WEST to the chase at (1', 35'-1.3") that both runs
    # already reach — about 17 ft added, four trap arms (WC 94", SH 85", LAV1 108", LAV2 83")
    # pushed past P3105.1, and `mep.vent_reachability` broken on three fixtures, because that
    # check wants the fixture's OWN run to end at the chase and does not follow a merge.
    # Measured 2026-09-18 by making the edit and running `haus check`; reverted.
    #
    # ** THE HALL-BATH RUN'S FIRST VERTEX AND ITS OWN COMMENT DISAGREE. ** That comment says
    # the takeoff is "on W-S-BD-N (y=26'-4")"; the authored path starts at (9'-8.4", 31'-0").
    # Whatever that vertex is for, it is not the takeoff the prose describes, and a merge is
    # the wrong tool for reconciling them. The chase is VR-M-RADON-VENT's, at
    # (1', 35'-1.3") — the *same* shaft as the 2'x2' mechanical chase in the hall bath's NW
    # corner (W-S-CH-W/CH-S, moved there 2026-07-28 from the NE corner specifically so it
    # could carry this riser; storeys/second.py).
    # ** IT APPROACHES THE CHASE FROM THE NORTH SINCE 2026-09-19, AND THE RADON RISER IS
    # WHY. ** The run used to turn west at y=34'-6" and travel the last 8'-7 1/2" to the
    # chase on that line. So does `VR-M-RADON-VENT`'s own `chase_offset` jog, at 19'-6" —
    # and this run arrived at 19'-5". Two pipes, one line, one inch apart, collinear the
    # whole way: `mep.run_interference` reported it twice, once against the chase's RADON
    # riser and once against its VENT riser, which are the same physical 3" pipe carrying
    # two systems.
    #
    # ** RAISING THE ARRIVAL ELEVATION CANNOT FIX IT, AND THAT IS THE USEFUL PART. ** This
    # run RISES to the chase so condensate drains back to the fixtures; the chase jog is
    # LEVEL. A rising run collinear with a level one always crosses it — moving
    # `end_elevation` to 9'-9", 9'-10" or 9'-11" leaves the pair count unchanged and only
    # moves the station where the two pass through each other. Measured, all three.
    #
    # So the approach moves in PLAN, and it goes round the EAST side through a window
    # FOUR AND A HALF INCHES WIDE. The chase jog occupies y=34'-6" from x=1'-0" to
    # x=9'-7 1/2" with the riser standing at its east end, so a leg crossing y=34'-6"
    # anywhere between those two x is inside it and only x > 9'-7 1/2" is clear. But
    # `FO-A-HALL`, the stair void, starts at x=10'-0" — and a vent hanging over an open
    # well is `mep.run_over_void`, which the first attempt at this (crossing at x=10'-6")
    # duly earned. So the crossing stands at **x=9'-10 1/2"**, which is the only station
    # that satisfies both: 3" clear of the 3" riser, where a 2" pipe beside it needs
    # 2 15/16", and its own outside 3/8" short of the void's edge. ** DO NOT NUDGE THIS
    # EITHER WAY. **
    #
    # The run therefore holds x=9'-7 1/2" to y=34'-0", steps 3" east, crosses the jog at
    # x=9'-10 1/2", runs west north of the jog and drops south into the chase.
    # ** SINCE 2026-09-23 THE CHASE IS AT (1'-0", 35'-1.3") ** (FS-S-WEST's truss moved off
    # it), so the jog's two pipes span y 34'-9.4"..35'-1.2" and the west leg moved from
    # y=35'-0" to 35'-7 1/2", 1" clear of the vent pipe; the stub south is 6.2".
    #
    # The south stub is the only thing on x=1'-0" north of the chase, so it does not
    # touch PR-S-BATH1-VENT, which arrives on that same line from the SOUTH. -2 pairs, and
    # both of this run's remaining clashes are at its terminals, where a re-route cannot
    # reach them. The header's three trap arms (39" to the tub-shower, 0" to the lav, 17" to
    # the WC at y=21'-11") are measured off it; see the header note below for 2026-09-24.
    PipeRun(uid="CSP902AAAA", tag="PR-S-SUITEBATH-VENT", system=PipeSystem.VENT,
            # ** IT MEETS THE STACK AT ITS JOG CORNER SINCE 2026-09-23. ** It ran on to y=35'-7.5"
            # — inside W-S-N3's framing — and back west to the chase. The stack now turns up at
            # (9'-7 1/2", 34'-4.9") at +19'-6", so this rises into that corner from the south.
            # North on x=9'-0" onto the jog's crown just west of FO-A-VENT-STACK (a run
            # inside that hole has nothing to strap to).
            # ** HEADER AT +19'-8", y=22'-1", SINCE 2026-09-24 **: over DU-S-ERV-HP-FEED
            # rather than beside it, on W-S-SN3's cavity face; clears PR-S-BATH1-VENT by 3".
            path=(pt(ft(16, 4.5), inch(265)), pt(ft(9), inch(265)),
                  pt(ft(9), inch(412.9))),
            diameter=inch(2),
            elevations=(inch(116), inch(116.3), inch(116.7)),
            serves=("FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                    "FX-S-SUITEBATH-TUBSH")),
]

VENT_BRANCHES_ATTIC = [
    # The guest studio's bath and wet bar.
    #
    # ** AN OFFSET VENT IS MANDATORY HERE, NOT A CHOICE. ** `mep.vent_reachability` passes a
    # fixture outright when its `wall_ref` is in `stacked_lower` — and NO ATTIC WALL CAN EVER
    # BE, because nothing stacks on the top storey. Every fixture up here needs an authored run.
    #
    # ** IT STARTS OVER THE SHOWER, AND THAT IS `mep.trap_arm_length`, NOT AESTHETICS. ** The
    # check measures to the nearest point of the serving run. Starting it at the wet-wall axis
    # x=9'-7 1/2" would give the shower a 6'-7 1/8" arm against Table 1002.2's 5'-0" for 2" — a
    # FAIL. Starting at (16'-2 5/8", 20'-8"), directly over the pan, makes the shower's arm ~0
    # and leaves the others clear: WC 1'-5 3/8" (limit 6'-0"), lav 10 3/8" (limit 3'-6"). The
    # ** THE BAR SINK IS NAMED HERE AND ON PR-A-BAR-VENT, AND BOTH ARE TRUE. ** Its revent
    # tees into this run's vertical and this run carries it the rest of the way to the
    # chase, so both pipes carry its vent air. `mep.trap_arm_length` takes the NEAREST point
    # of any serving run, so the arm is measured to its own riser, not to this line — which
    # is what the revent was built for. Dropping this run from `serves` FAILs
    # `mep.vent_reachability`: `vent_path.py` wants a run landing on a VentRun, and
    # PR-A-BAR-VENT lands on a PipeRun.
    #
    # From there it runs west to the W-A-STU-W axis, north through the pocket at ~7'-0", and
    # west to VR-M-RADON-VENT at (1'-0", 35'-1.3"), which carries PipeSystem.VENT to the roof. It
    # mirrors PR-S-SUITEBATH-VENT one storey down — same x=9'-7 1/2" leg, same chase.
    #
    # ** DO NOT INSTEAD ADD THESE FIXTURES TO PR-S-SUITEBATH-VENT.serves. ** `vent_path.py` is
    # purely 2D and would PASS it — but that run sits at 9'-3", BELOW these fixtures' flood-level
    # rims. That is gaming the check. This run is 32' of 2" PVC and it is real.
    # ELEVATIONS ARE STOREY-RELATIVE AND THE ATTIC DATUM IS ft(20): `_resolve_pipe_run` adds
    # the datum silently and no check grades a pipe against the roof plane it sits under, so
    # a project elevation authored here would resolve 20'-0" too high and hang over the roof.
    #
    # The run ends on the riser rather than turning east to meet the stack, because the
    # riser stands on THIS RUN'S OWN WET-WALL LINE at x=9'-7 1/2" — the stack is already on
    # the wall this vent climbs. The whole profile is a 4" rise over 28', which is what a
    # dry vent wants. The underside here is `20'-0" + 1 1/2" + x/2`, 20'-8 1/4" at x=1'-0" —
    # too shallow for any duck, which is why the run stops well east of that station.
    #
    # The vertex at (9'-7 1/2", 20'-8") is what `mep.vent_reachability` reads — it requires a
    # vertex ON the served fixtures' wet wall (W-A-STU-W's axis).
    #
    # Every vertex clears the flood-level rims by more than P3104.4's 6": the highest rim served
    # is the lavatory at ~2'-10" AFF (22'-10"), so 23'-4" is the floor for a dry horizontal vent
    # and the lowest vertex here is 23'-5". It rises monotonically into the stack, so condensate
    # drains back to the fixtures and there is no pocket to hold water. The last vertex at
    # 23'-9" ties in 1" BELOW the riser's 23'-10" exit, on the vertical part of the stack.
    # ** IT STILL CROSSES DU-A-ERV-R-STUBATH'S RISER (2026-09-24). ** Both stand in W-A-STU-W's
    # one 5 1/2" cavity, which cannot hold them side by side, and over the duct's elbow into
    # its 4'-4" grille the vent would be in the partition's top plates. The fix is the grille:
    # REG-A-STUBATH-EXH below 3'-2" (plan/mep_registers.py) lets this pass over the duct.
    PipeRun(uid="STFQKR8Q95", tag="PR-A-STUBATH-VENT", system=PipeSystem.VENT,
            # Ends ON the vent riser at the stack's upper station (2026-09-23), the south one
            # of the pair; the radon riser 6.2" north is no longer in its way.
            path=(pt(ft(16, 2.625), ft(20, 8)), pt(ft(9, 7.5), ft(20, 8)),
                  pt(ft(9, 7.5), inch(412.9))),
            diameter=inch(2),
            elevations=(ft(3, 5), ft(3, 6), ft(3, 9)),
            serves=("FX-A-STUBATH-WC", "FX-A-STUBATH-LAV", "FX-A-STUBATH-SH",
                    "FX-A-STUDIO-BAR-SINK")),
    # ** THE BAR'S OWN REVENT, AND IT IS WHAT MAKES THE KITCHENETTE ROBUST RATHER THAN
    # MARGINAL. ** FX-A-STUDIO-BAR-SINK used to ride PR-A-STUBATH-VENT above, whose nearest
    # point is over the shower; with the bowl at the SUNNERSTA's east end (plan/fixtures.py)
    # that arm lands within an inch of Table 1002.2's 60" on dimensions nobody has measured,
    # and holding it under 60" without a revent forces D-A-STUBATH so far east that it opens
    # onto a 19 1/4" strip in front of the shower.
    #
    # ** IT COSTS NO BORED STUD AND NO BEARING WALL. ** The unit backs onto W-A-BATH-S, a 2x4
    # NONBEARING partition that already carries pipe at its west end. The 2" rises in that
    # cavity behind the bowl at x=12'-8 1/2" and runs WEST inside the same wall to the stack,
    # tying into PR-A-STUBATH-VENT on the vertical at (9'-7 1/2", 20'-8"). It stops at that
    # tee rather than running a duplicate 14' north to the chase, which is why the fixture
    # names both runs (see above) — the pipe billed here is the pipe that gets built.
    #
    # The repeated first vertex is the riser — the idiom PR-A-STUBATH-DRAIN uses. Elevations
    # are STOREY-RELATIVE (the attic datum is ft(20); see the note above on what an absolute
    # would do here) and rise monotonically from -4 1/4", PR-A-BAR-DRAIN's own head in the
    # joist band, to 3'-6" — which is exactly PR-A-STUBATH-VENT's elevation at the plan point
    # they share, so the two profiles meet rather than pass.
    #
    # ** THE HORIZONTAL MUST STAY 6" ABOVE THE BOWL'S FLOOD RIM, P3104.4, AND THAT IS THE
    # WORKTOP MEASUREMENT. ** At the authored 27" mount the rim is ~2'-3" AFF and the 3'-4"
    # horizontal clears it by 13"; if the SUNNERSTA's top measures nearer 36" the rim climbs
    # with it and this run has to climb too. The vertex on x 9'-7 1/2" is what `mep.vent_reachability` reads —
    # it wants a vertex on the served fixture's wet wall (W-A-STU-W's axis) — so keep it.
    PipeRun(uid="VK3C96KFRF", tag="PR-A-BAR-VENT", system=PipeSystem.VENT,
            # ** IT RISES CLEAR OF THE WALL, THEN STEPS IN (2026-09-23). ** W-A-BATH-S sits on
            # joist-0-013 (y=17'-4"), so a riser in its cavity came up through that joist's
            # top flange. It leaves the bay at 16'-11 3/8", behind the unit's back panel and
            # clear of the wall's finished face, and enters the wall at the horizontal's 3'-4".
            path=(pt(inch(152.5), inch(203.375)), pt(inch(152.5), inch(203.375)),
                  pt(inch(152.5), ft(17, 4)),
                  pt(ft(9, 7.5), ft(17, 4)), pt(ft(9, 7.5), ft(20, 8))),
            diameter=inch(2),
            elevations=(inch(-4.25), ft(3, 3.875), ft(3, 4), ft(3, 5), ft(3, 6)),
            serves=("FX-A-STUDIO-BAR-SINK",)),
]

# THE STACK JOGS EAST INSIDE THE ATTIC. `chase_position` is (1'-0", 35'-1.3"): the shaft
# runs the full height of the house through RM-M-MECH's framed closet and RM-S-BATH1's NW
# notch, and relocating it would drag a penetration through every storey below to solve a
# problem that only exists in the top one. At x=1'-0" the 6:12 roof underside is 20'-8 1/4"
# — the riser cannot rise there at all, let alone reach the 23'-10" wall exit.
#
# So it jogs, and it jogs BELOW THE DECK: `chase_offset_elevation` 19'-6" is inside
# FS-ATTIC's 11 7/8" I-joist band (19'-0 1/8"..20'-0"), so the 3" pipe crosses through the
# joist WEBS — the ordinary place a stack offsets, and 12'-4" of it in a bay that already
# carries PR-A-STUBATH-VENT's line. It comes up at x=13'-4" and everything above is as it
# was: exit at 23'-10" through the gable, 1'-10.7" out, up the cladding to a derived
# termination. NO ROOF PENETRATION ANYWHERE, which was the point.
#
# THE RISER IS AT x=9'-7 1/2", WEST OF WIN-A-N1 AND ON THE WET WALL. At x=13'-4" — the
# station the stub bath's own line would suggest — the riser would land on that window's
# trim: WT-3036 is 30" wide, its centre moved 13'-4" -> 12'-0" on 2026-09-06, so the rough
# opening now runs x 10'-9"..13'-3" and a PAIR of 3" pipes straddling 13'-4" (about 7 3/4"
# overall, x 13'-0 1/8"..13'-7 7/8") would lap its east jamb by 3". Before that move the
# same station sat dead centre in the glass. Nothing fails either way, because no check
# grades a riser against a window it runs beside, but it is unbuildable: the standoff
# straps have no cladding to land on and the window trim has nowhere to die.
#
# MN 1303.2402 subp. 5 wants the exhaust 2'-0" over WIN-A-N1's 25'-0" head or 10'-0" away in
# plan; the termination sits 12" over the rake, which measures 27'-8 3/4" at this station and
# falls 1/2" per inch travelled west, so subpart 5 holds anywhere east of x=8'-2" — a
# six-foot band.
#
# 9'-7 1/2" is chosen from inside that band because it is **PR-A-STUBATH-VENT's own wet-wall
# line**. Landing on it deletes that run's last leg outright: the bath vent goes up the wet
# wall and straight into the stack instead of turning east for 3'-8" to meet it. Measured:
#   * the bundled pair spreads in Y, across the jog, so BOTH risers stand on x=9'-7 1/2" and
#     the pair is one pipe wide in plan: x 9'-5 3/4"..9'-9 1/4", y 34'-9.4"..35'-5.2".
#     It used to spread in X — perpendicular to the wall EXIT — which put the two pipes on
#     one line for the whole 8'-7 1/2" jog (they cannot share a bore through a joist web)
#     and drove the east one to 9'-9 9/10", 1 2/5" into W-A-BA-E's 2x4 studs. That was a 3"
#     bore in a 2x4 and `mep.run_through_stud` reported it the day a VentRun first resolved
#     an envelope; `resolve/vent_termination.riser_polylines` now spreads across the LONGEST
#     horizontal leg. W-A-BA-E's stud face at x=10'-0"-1 3/4" is 1" clear of the pair;
#   * 11 3/4" clear of WIN-A-N1's west jamb (it was 9 5/8" while the pair spread in x, and
#     2'-1 5/8" until the window moved a bay west on 2026-09-06). A further move west of
#     that window has nowhere to go (see attic.py's rake note), but if one is ever
#     attempted, check this first;
#   * termination 27'-8 3/4", 2'-8 3/4" over the window head (subpart 5 wants 2'-0");
#   * the under-deck jog is 8'-7 1/2" of 3" PVC in the FS-ATTIC band.
#
# One consequence follows the station: the wall it exits through is W-A-N2 (x 10'..0'), not
# W-A-N2B — 9'-7 1/2" is west of the north gable's x=10'-0" split. 115 1/2" is not 0 mod 16
# and does not need to be: the riser is outboard of the sheathing on standoff straps and
# grips a girt, not a stud, and the jog crosses I-joist webs at 19'-6" whose 16" grid is
# fixed whatever this run does.
#
VENT_RISERS = [
    VentRun(uid="CMVR01AAAA", tag="VR-M-RADON-VENT",
            # ** THE CHASE WAS RE-PACKED ON 2026-09-23. ** VENT first so it spreads SOUTH
            # (y 34'-4.9"), the side the branch vents arrive from up the chase's west slot;
            # the radon riser is north (34'-11.1"). 6.2" apart so the two STRADDLE FS-ATTIC's
            # y=34'-8" I-joist the 19'-6" jog runs east beside — one riser in each bay —
            # which frees the chase's south band for the ERV risers and conduits that climb
            # past the jog, and leaves the north strip clear for DU-ERV-EA's exit.
            systems=(PipeSystem.VENT, PipeSystem.RADON), diameter=inch(3),
            bundle_spacing=inch(6.2),
            # (1', 35'-1.3") since 2026-09-23, out of FO-M-ERV-OA's trimmers and into the
            # grown FO-M-ERV-EA; exit_offset shrank to keep the exterior riser at y=37'-0".
            # PR-B-RADON-LEG (mep_drainage.py) arrives at its foot from the pit since 2026-09-23.
            chase_position=pt(inch(10), inch(416)), start_elevation=ft(-8, -10),
            chase_offset=pt(ft(8, 9.5), ft(0)), chase_offset_elevation=ft(19, 6),
            exit_elevation=ft(23, 10), exit_offset=pt(ft(0), inch(28.7)),
            wall_ref="W-A-N2", attachment="pipe_strap"),
]

# Through-panel straps fixing the exterior riser to the north gable siding. The riser spans
# 23'-10" to its derived termination, and the gable siding at x=9'-7 1/2" runs to a 26'-8 3/4"
# rake — so all three fixings, at 24'-4" / 24'-10" / 25'-4", sit on the pipe *and* on WALL
# cladding, not on roof, with 1'-4 3/4" to spare on the top one. That is the question that
# decides the part, and it was checked: a fixing that had landed above the rake would be on
# `standing-seam` roofing and would have stayed on the CanDuit ring.
#
# These hold a *pipe*, not a seam: the gable wall is `pbr-panel-24`, an exposed-fastener
# panel with no seam, so an S-5! CanDuit ring's `requires_role=ROLE_STANDING_SEAM_CLAMP`
# would order a bracket with nothing to grip. This follows the roof leaders
# (plan/mep_electrical.py LEADER_CLAMPS) onto the 316 stainless standoff strap, screwed
# through the panel into the girt.
#
# Sizing is on OUTER diameter: 3" PVC DWV is 3.5" OD, which is the **#11** (3.4-3.7") size;
# the 4" leaders take #13. The size suffix stays because a bare part family once billed
# brackets and no rings.
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
# radon/plumbing chase at (1', 35'-1.3"), because neither room has a wet wall that continues to
# the storey above: the stair-foot bathroom's four sides are two runs of framed stair wall,
# a dry 2x4 partition and its own east wet wall, none of which is a stack, and the sauna's
# are 2x4 partitions, the centre bearing wall and the foundation.
# `mep.vent_reachability` grades the authored
# path — nothing here is inferred, so an unvented fixture would still fail loudly.
#
# Both share the same vertical band: the tee sits low, the riser goes up inside the room's own
# stud cavity, and the horizontal leg tops out at **7'-10 7/16" basement-relative**. The
# ceiling over both of them is FS-M-WEST's 11 7/8" I-joists, not a pour — SL-M-DECK's cast
# deck starts at x=18'-0" and these run at x=7' and x=9' — so the constraint is the joist
# soffit at 8'-1 9/16", which the band clears by 3 1/8". (The older note here said 9" of cast
# concrete; that was true of an x=18'-plus station this pair has never had.) Each rises a few
# inches over its length to the chase so condensate drains back to the fixtures.
#
# Neither shares a leg with the other — the bathroom's runs north at x=7', the sauna's at
# x=9' — the same rule PR-S-SUITEBATH-VENT follows against the hall bath's branch.
VENT_BRANCHES_BASEMENT = [
    # RM-B-BATH: same corridor north at x=7' to the chase. The riser stands in a real stud
    # cavity — W-B-BA-E, the rotated bathroom's INT_2X6_STAGGERED_PLUMBING east partition,
    # which is the room's one wet wall and the only 5 1/2" cavity it has. Both fixtures name
    # it in `wall_ref`, and `mep.vent_reachability` reads that field rather than geometry.
    #
    # The riser stands at (13'-10 11/16", 19'-3"), between the two fixtures, 15" clear of
    # N-B-STR
    # and 2'-6" clear of N-B-BA-W, so the leg west at the same y bores W-B-STR2 mid-panel
    # rather than at a node the wall tees into. Trap arms measured to it: 5'-3" from the
    # water closet's flange and 2'-1" from the lavatory's trap, against Table 1002.2's
    # 6'-0" for 3" and 3'-6" for 1 1/2".
    # ** A COMMON VENT INTO PR-B-SAUNA-VENT SINCE 2026-09-23. ** It ran north on x=7'-0"
    # and west on y=34'-6" to the chase; the re-packed chase leaves one lane in at the
    # basement ceiling, which the 2" sauna vent takes, and this 1 1/2" ties into that 2" line
    # at x=9'-0", rising all the way. The notes below describe the retired x=7' leg.
    PipeRun(uid="CBPV01AAAA", tag="PR-B-BATH-VENT", system=PipeSystem.VENT,
            path=(pt(inch(166.6875), ft(19, 3)), pt(inch(166.6875), ft(19, 3)),
                  pt(ft(9), ft(19, 3))),
            diameter=inch(1.5), material="pvc",
            # ** IT RUNS TWO AND A HALF INCHES LOWER THAN THE SAUNA VENT SINCE 2026-09-19
            # (P1), AND THAT IS THE WHOLE FIX. ** Both vents used to arrive at the chase on
            # the y=34'-6" line at the same 7'-9 15/16", collinear for six feet, and both
            # passed through PR-B-KITCH-DRAIN's x=4'-6" fall line on the way. This one drops
            # under: 7'-5 7/16" through the laundry branch and 7'-7 7/16" at the chase,
            # which puts it 2 1/2" under PR-B-SAUNA-VENT the whole way west and 4/5" under
            # the kitchen drain where it crosses.
            #
            # The east leg goes flat-ish (7'-4 15/16" -> 7'-5 7/16", about 1/16"/ft) and the
            # north leg carries the grade instead (2" over 15'-3", an eighth an inch a foot,
            # which is what this file's header asks for). Staying deep through y=19'-5" and
            # y=20'-0" is what clears PR-B-TUB2-DRAIN and PR-B-WASH-DRAIN, which fall west
            # across this lane on their way to the stack — 1 1/3" and 1/3" of air now, where
            # both were interpenetrating.
            #
            # ** THE EAST LEG DROPPED 1 1/2" ON 2026-09-22 ** so DU-B-ERV-R-PLAY can cross it
            # flat inside SF-B-BATH (1 1/4" of air) instead of hopping over it on four
            # elbows; the north leg's grade steepens to 4" over 15'-3". GYM passes under it at
            # x=9' with 3/8" to spare, and the two drains above get 1 1/2" more air.
            # Riser top 7'-0 15/16" since 2026-09-24, 2" lower: the straight rise west then
            # passes 1/4" under DU-B-ERV-R-PLAY's x=12'-3" leg.
            elevations=(ft(1, 3.4375), inch(84.94), ft(7, 9.25)),
            serves=("FX-B-BATH-WC", "FX-B-BATH-LAV")),
    # RM-B-SAUNA's shower group. 2" for 4 DFU, rising at (17'-4", 8'-2 3/16") — inside
    # W-B-CS's 3 1/2" liner build-up, in the pan's own east wall, on the pan-and-floor-drain
    # centre line and clear of the mixer's two supply drops. That is both fixtures' declared
    # wet wall (plan/fixtures.py) and the one basement wet wall that carries a framed wall on
    # the storey above, so the vent has a true stack path as well as this drawn one.
    #
    # Trap arms as the check measures them, both well inside Table 1002.2's 5'-0" for a 2"
    # arm. Above the sauna's hung ceiling the run leaves the build-up north over W-B-SA-N,
    # crosses the workshop west at y=10'-6", and passes W-B-CW at x=9'.
    # ** INTO THE RE-PACKED CHASE FROM THE SOUTH (2026-09-23). ** North on x=9'-0" only to
    # y=29'-4", west to x=5'-1 1/2", north between the ERV cabinet (x<=5'-0") and
    # DU-ERV-RISER-SUP's port, west on y=33'-4" just under FS-M-MECH's joists — 1" north of
    # the backup enclosure's 110.26 dedicated space, over the supply duct's leg — and north
    # onto the vent riser at x=10". PR-B-BATH-VENT ties into it at (9'-0", 19'-3").
    PipeRun(uid="CBPV02AAAA", tag="PR-B-SAUNA-VENT", system=PipeSystem.VENT,
            path=(pt(ft(17, 4), inch(98.1875)), pt(ft(17, 4), inch(98.1875)),
                  pt(ft(17, 4), ft(10, 6)), pt(ft(9), ft(10, 6)),
                  pt(ft(9), ft(19)), pt(ft(9), ft(28, 8)), pt(inch(51.5), ft(28, 8)),
                  pt(inch(51.5), inch(400)), pt(inch(10), inch(400)),
                  pt(inch(10), inch(412.9))),
            diameter=inch(2), material="pvc",
            # ** THE NORTH LEG BREAKS AT y=19'-0" NOW (P1, 2026-09-19). ** It used to climb
            # 7'-1 7/16" to 7'-9 15/16" in one straight ramp over twenty-four feet, which
            # put it at 7'-5 1/4" where PR-B-LSINK-DRAIN falls west across x=9'-0" — inside
            # it by 1.85". A vent has to be graded to drain back to the drainage pipe
            # (P3104.1) so it cannot dip under one thing and climb over the next; what it
            # can do is take its rise EARLY. It now gains 3 3/4" in the first 8'-6" and
            # coasts the remaining 15'-6", which clears the laundry drain by a third of an
            # inch and — the part worth noting — buys back half an inch over
            # DU-B-ERV-R-PLAY at y=30'-6", where D3 left it 2 1/2 thousandths of an inch.
            elevations=(ft(0, 3.4375), ft(7, 1.4375), ft(7, 3.4375), ft(7, 5.4375),
                        ft(7, 9.25), ft(7, 10.4375), ft(7, 11.14), ft(7, 11.54),
                        ft(8, 0.0375), ft(8, 0.1375)),
            serves=("FX-B-SAUNA-SH", "FX-B-SAUNA-FD")),
]
