# haus: editable
# Catlin MEP — concrete penetrations — the sleeves and stubs cast into slabs and walls.
#
# Split out of the old 2,515-line plan/mep.py (AGENTS.md §1.1). Every element below moved
# verbatim; plan/mep.py still re-exports the storey lists, so the manifest is unchanged.
#
# Sleeve positions are the exact pre-pour centers the concrete crew works from — the resolver
# validates them against the fixture drain point they serve (`mep.sleeve_alignment`); nothing here
# is derived. Second-floor hall-bath drains drop through the framed floor into the existing
# INT_2X6_PLUMBING wet wall (W-S-BD-N) with no sleeve needed — only a cast concrete deck needs a
# pre-positioned penetration.

from typehaus import (
    PipeRun,
    Service,
    SleevePenetration,
    ft,
    inch,
    pt,
)
from typehaus.model import m

SLEEVES = [
    # BATH1's WC is wall-hung on an in-wall carrier (FX-TOILET-WH): the bowl bolts to a
    # steel carrier frame inside W-M-BAE's 2x6 stud bay and the 3" waste drops inside the
    # wall, so the pre-pour sleeve sits on that wall's centerline at the fixture's authored
    # drain_position — under the carrier, not under the bowl.
    SleevePenetration(uid="CMP901AAAA", tag="SP-M-WC1", host_ref="SL-M-DECK",
                      position=pt(ft(6), ft(22, 7)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-M-BATH1-WC"),
    # Re-pointed 2026-07-29 (plans/TODO.md): the BATH2 WC moved to the wet wall and its
    # routed drain (PR-B-WC2-DRAIN) now drops at the fixture's own flange, so the sleeve
    # finally sits where the pipe actually is instead of at the old (3', 18') position.
    SleevePenetration(uid="CMP902AAAA", tag="SP-M-WC2", host_ref="SL-M-DECK",
                      position=pt(m(0.686504), m(6.14439)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-M-BATH2-WC"),
    SleevePenetration(uid="CMP907AAAA", tag="SP-M-BATH2-SH", host_ref="SL-M-DECK",
                      position=pt(ft(1, 9), ft(17, 3)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-BATH2-SH"),
    SleevePenetration(uid="CMP908AAAA", tag="SP-M-BATH2-TUB", host_ref="SL-M-DECK",
                      position=pt(ft(7, 4), ft(19, 4.8)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-BATH2-TUB"),
    SleevePenetration(uid="CMP909AAAA", tag="SP-M-BATH2-SINK", host_ref="SL-M-DECK",
                      position=pt(ft(1), ft(16, 6)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-BATH2-SINK"),
    # Projection of FX-M-BATH1-LAV onto the W-M-BAE structure-layer centerline (x=6, from
    # storeys/main.py node coordinates N-M-BA1/N-M-BA2), at the lavatory's own y (nudged
    # +6" with it on 2026-07-29 for the BATH2 wall move).
    SleevePenetration(uid="CMP903AAAA", tag="SP-M-LAV1", host_ref="SL-M-DECK",
                      position=pt(ft(6), m(7.00891)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), serves_fixture="FX-M-BATH1-LAV"),
    # Projection of FX-M-LAUNDRY onto the W-M-BA2E centerline (x=8'). The wall tag in this
    # comment used to read "W-M-BA2E2", which spans y 13'-4"..18'-0" and so contains neither
    # this sleeve nor the fixture — a stale tag, corrected 2026-07-31 here and on the
    # fixture's own `wall_ref` (plan/fixtures.py). The position is unchanged: x=8' is the wet
    # wall's centreline and y=20' sits inside the stacked pair's band, so the standpipe and
    # the supply box land behind the machine rather than beside it. It survived the 8" move
    # north of 2026-08-03 without moving — the band is 18'-0 5/8"..21'-4 5/8" now and y=20'
    # is still well inside it, as are SP-M-CW-WASH (20'-7.2") and SP-M-HW-WASH (21'-2.4").
    SleevePenetration(uid="CMP904AAAA", tag="SP-M-WASH", host_ref="SL-M-DECK",
                      position=pt(ft(8), ft(20)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-LAUNDRY"),
    # The laundry tub's waste, straight down under its basin the way every other main-storey
    # fixture drops through this 9" cast deck. 2" rather than the 1 1/2" one sink would take,
    # because the branch below it is the tub's trap arm to the laundry stack and 2" is what
    # buys the 60" Table 1002.2 allows for the 45" it runs. Authored at exactly the fixture's
    # `drain_position`, which is what makes `mep.sleeve_alignment` read 0.00".
    SleevePenetration(uid="ZW630NFAAS", tag="SP-M-LSINK", host_ref="SL-M-DECK",
                      position=pt(ft(11, 9), ft(18, 9)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-LAUNDRY-SINK"),
    # The kitchen sink's waste through the 9" deck. Authored at exactly FX-M-KITCH-SINK's
    # `drain_position`, which is what makes `mep.sleeve_alignment` read 0.00". Moved to the
    # north wall 2026-07-30 with the sink, then re-centred the same day with the sink/
    # dishwasher flip — see plan/fixtures.py.
    SleevePenetration(uid="BFQH6F04VQ", tag="SP-M-KITCH", host_ref="SL-M-DECK",
                      position=pt(ft(28, 7), ft(35)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-KITCH-SINK"),
]

# Supply risers through the 9" concrete deck — every hot/cold branch that leaves the
# basement ceiling for a main- or second-storey wet wall crosses SL-M-DECK, and a PEX
# riser through cast concrete is a cast-in sleeve exactly like a waste drop
# (`mep.sleeve_coverage` holds every crossing to one). Positions sit on (or tight to) the
# wet wall each riser feeds, spaced >= 5" from every neighbouring penetration so the
# 4"-tolerance sleeve matcher can never confuse two.
SUPPLY_SLEEVES = [
    SleevePenetration(uid="CMPS01AAAA", tag="SP-M-CW-BATH1", host_ref="SL-M-DECK",
                      position=pt(ft(6), ft(23, 7.2)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    SleevePenetration(uid="CMPS02AAAA", tag="SP-M-HW-BATH1", host_ref="SL-M-DECK",
                      position=pt(ft(6), ft(24)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
    SleevePenetration(uid="CMPS03AAAA", tag="SP-M-CW-BATH2", host_ref="SL-M-DECK",
                      position=pt(ft(2, 3), ft(17, 2.4)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    SleevePenetration(uid="CMPS04AAAA", tag="SP-M-HW-BATH2", host_ref="SL-M-DECK",
                      position=pt(ft(2, 3), ft(16, 9.6)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
    SleevePenetration(uid="CMPS05AAAA", tag="SP-M-CW-WASH", host_ref="SL-M-DECK",
                      position=pt(ft(8), ft(20, 7.2)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    SleevePenetration(uid="CMPS06AAAA", tag="SP-M-HW-WASH", host_ref="SL-M-DECK",
                      position=pt(ft(8), ft(21, 2.4)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
    # Moved to the north wall 2026-07-30 with the sink, then re-centred with the sink/
    # dishwasher flip: same offset magnitude from the sink centre, but the along-wall
    # component now points *east* (toward the dishwasher's new spot) instead of west.
    SleevePenetration(uid="CMPS07AAAA", tag="SP-M-CW-KITCH", host_ref="SL-M-DECK",
                      position=pt(ft(29, 0.6), ft(34, 1.2)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    SleevePenetration(uid="CMPS08AAAA", tag="SP-M-HW-KITCH", host_ref="SL-M-DECK",
                      position=pt(ft(29, 6.6), ft(33, 7.2)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
    SleevePenetration(uid="CMPS09AAAA", tag="SP-M-CW-SBATH", host_ref="SL-M-DECK",
                      position=pt(ft(5, 7.2), ft(26, 4)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    # x=6'-2.4" -> 6'-4" (2026-08-02) with PR-B-HW-SBATH's riser below: RM-M-MUD-CLOSET's
    # east return now tees into N-M-BA1 and its corner pack took the old station — see the
    # note on that PipeRun.
    SleevePenetration(uid="CMPS10AAAA", tag="SP-M-HW-SBATH", host_ref="SL-M-DECK",
                      position=pt(ft(6, 4), ft(26, 4)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
    SleevePenetration(uid="CMPS11AAAA", tag="SP-M-CW-SUITE", host_ref="SL-M-DECK",
                      position=pt(ft(13, 7.2), ft(16, 10.8)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
    SleevePenetration(uid="CMPS12AAAA", tag="SP-M-HW-SUITE", host_ref="SL-M-DECK",
                      position=pt(ft(14, 2.4), ft(16, 10.8)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_HOT),
    # The two south-face wall hydrants' shared riser (2026-08-01). One crossing, not two:
    # both hydrants are fed from the second-floor joist space, so a single 3/4" branch
    # leaves the basement here and splits up there. y=13'-0" is W-M-BDN1's line — the
    # main-storey partition the riser stands inside — and it is over open basement ceiling
    # at x=6' (W-B-SA-N, the sauna's north partition, starts at x=8'-10"), so the
    # penetration lands in the deck rather than on top of a wall below it. Nothing else
    # crosses within 3' of it.
    SleevePenetration(uid="CMPS16AAAA", tag="SP-M-CW-HYD", host_ref="SL-M-DECK",
                      position=pt(ft(6), ft(13)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.WATER_COLD),
]

# Second-storey waste stacks. The upstairs bathrooms drain down through framed walls and
# floors — no sleeve needed there — but each stack still has to pass the one concrete
# plate in its way, the SL-M-DECK deck, on the way to the basement-ceiling collector.
STACK_SLEEVES = [
    SleevePenetration(uid="CMPS13AAAA", tag="SP-M-S-BATH1", host_ref="SL-M-DECK",
                      position=pt(ft(5), ft(26, 4)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-S-BATH1-WC"),
    SleevePenetration(uid="CMPS14AAAA", tag="SP-M-S-SUITE", host_ref="SL-M-DECK",
                      position=pt(ft(13), ft(16, 10.8)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-S-SUITEBATH-WC"),
    # The heat-pump condensate drop from the main-storey wall heads (master bedroom +
    # living room, both on the south wall by the centre line) down to the collected
    # air-gap line at the basement ceiling (plans/TODO.md §condensate).
    SleevePenetration(uid="CMPS15AAAA", tag="SP-M-COND", host_ref="SL-M-DECK",
                      position=pt(ft(17, 6), ft(1)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), purpose=Service.DRAIN),
]

# Slab-on-grade stub-ups. A fixture standing on grade has no wall drain stack — its trap
# arm runs *under* the slab — so the penetration is set before the pour exactly like the
# deck sleeves above. Each fixture authors this same point as its `drain_position` (or, where
# there is no override, as its own position), which is what makes the alignment check exact.
#
# Four of them now (2026-07-30). The basement went from one slab fixture to four in one
# decision: a bathroom at the foot of the stair, and the sauna's shower end resolved into a
# curbed pan plus a floor drain.
SLAB_STUBS = [
    # Was SP-B-UTILITY, FX-1's stub at (7', 19'-6"), until 2026-07-30. Same cast-in, moved
    # and upsized to 3" for the bathroom's water closet: the utility sink it used to serve is
    # gone and the fixture that replaced it is a WC, which needs a 3" closet bend rather than
    # a 1 1/2" trap arm. The uid rides along because it is the same penetration in the same
    # pour schedule, not a new one.
    SleevePenetration(uid="CBP901AAAA", tag="SP-B-BATH-WC", host_ref="SL-B-FLOOR",
                      position=pt(ft(11, 8), ft(20)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-B-BATH-WC"),
    SleevePenetration(uid="CBP904AAAA", tag="SP-B-BATH-LAV", host_ref="SL-B-FLOOR",
                      position=pt(ft(17), ft(20)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), serves_fixture="FX-B-BATH-LAV"),
    # The sauna's two. The pan's is under the centre of the 36" x 36" curbed shower; the floor
    # drain's is the drain body itself, which is why its position and the fixture's are the
    # same point with no `drain_position` override on either.
    SleevePenetration(uid="CBP905AAAA", tag="SP-B-SAUNA-SH", host_ref="SL-B-FLOOR",
                      position=pt(ft(15, 8.5), ft(12, 0.1875)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-B-SAUNA-SH"),
    SleevePenetration(uid="CBP906AAAA", tag="SP-B-SAUNA-FD", host_ref="SL-B-FLOOR",
                      position=pt(ft(13, 6), ft(12, 9)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-B-SAUNA-FD"),
    # Where the ceiling collector turns down to become the under-slab building drain
    # (2026-07-30; 4" since the 2026-07-31 building-drain upsize). A 4" waste through cast
    # concrete is a cast-in exactly like the fixture stubs; `mep.sleeve_coverage` holds the
    # crossing to it.
    SleevePenetration(uid="CBP902AAAA", tag="SP-B-SLAB-MAIN", host_ref="SL-B-FLOOR",
                      position=pt(ft(3), ft(15, 6)), pipe_diameter=inch(4),
                      sleeve_diameter=inch(6)),
    # The bathroom branch's two under-footing crossings on its way to the main (IRC P2604,
    # the same relieving-arch treatment PR-G-HYDRANT-CW gets under the garage footing).
    # `mep.footing_clearance` requires both: at each one the pipe's crown sits below the
    # footing's -9'-8" bearing plane, so it is a crossing *through* the footing, not a pipe
    # standing clear of its 45° influence line.
    #
    # This one was SP-B-CW-UTIL-DR (FX-1's 1 1/2" arm) until 2026-07-30. The crossing point is
    # unchanged — the new bathroom branch runs the same corridor down the mechanical room, so
    # the hole stays where the concrete crew already had it — but it carries the 3" bathroom
    # branch now. Invert at the crossing is -9'-11 1/8" project, so the centre is -9'-9 5/8" —
    # 1 5/8" below FT-B-CW3's -9'-8" bearing plane, which is what makes this an under-footing
    # crossing rather than a pipe standing inside the footing's 45 degree influence line.
    SleevePenetration(uid="CBP903AAAA", tag="SP-B-CW-BATH-DR", host_ref="FT-B-CW3",
                      position=pt(ft(7), ft(18)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), axis="horizontal",
                      center_elevation=ft(-9.8)),
    # Under FT-B-STR, where the branch leaves the bathroom westward into the mechanical room.
    # The stair shaft is boxed in cast concrete on three sides, so every service this room
    # gets has to cross one of them: the drain crosses here, below the footing, and the vent
    # and the two supplies cross the wall above (WALL_SLEEVES).
    SleevePenetration(uid="CBP907AAAA", tag="SP-B-STR-BATH-DR", host_ref="FT-B-STR2",
                      position=pt(ft(10), ft(20)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), axis="horizontal",
                      center_elevation=ft(-9.675)),
]

# Horizontal sleeves through the basement's cast concrete walls. The whole ceiling-level
# distribution — collector, branches, supply trunks, hydrant line — has to get past the
# y=18' centre cross walls and out the perimeter, and every one of those crossings is a
# cast-in-place hole the concrete crew sets before the pour (`mep.sleeve_coverage`).
# center_elevation is project-frame absolute (the walls span -9'..0'); positions along
# y=18' keep >= 5" between neighbours so the 4"-tolerance matcher stays unambiguous.
WALL_SLEEVES = [
    # W-B-CW (y=18', x 0..6'-9"), west centre wall — the mechanical wall of the house.
    # Split at N-B-ESS-S on 2026-08-02 for the ESS closet: the three sleeves east of
    # x=6'-9" (BATH1-CW at 7'-4.8", WASH-CW at 8'-0", SAUNA-VENT at 9'-0") now host on
    # W-B-CW3, the stub that forms the closet's south wall. Same concrete, same positions,
    # same runs through them — only the segment they name changed.
    SleevePenetration(uid="CBPW01AAAA", tag="SP-B-CW-WC2", host_ref="W-B-CW",
                      position=pt(m(0.686504), ft(18)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), axis="horizontal",
                      center_elevation=ft(-1.37)),
    SleevePenetration(uid="CBPW02AAAA", tag="SP-B-CW-SBATH-CW", host_ref="W-B-CW",
                      position=pt(ft(4), ft(18)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.87)),
    SleevePenetration(uid="CBPW03AAAA", tag="SP-B-CW-SBATH-DR", host_ref="W-B-CW",
                      position=pt(ft(4, 6.4), ft(18)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), axis="horizontal",
                      center_elevation=ft(-1.748)),
    SleevePenetration(uid="CBPW04AAAA", tag="SP-B-CW-HYD", host_ref="W-B-CW",
                      position=pt(ft(5), ft(18)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-6)),
    SleevePenetration(uid="CBPW05AAAA", tag="SP-B-CW-WH", host_ref="W-B-CW",
                      position=pt(ft(5, 6), ft(18)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.86)),
    # The collector's own crossing. centre = invert at y=18' (-1'-9.0" project) + half of
    # 4" — re-solved with the 2026-07-31 building-drain upsize.
    SleevePenetration(uid="CBPW06AAAA", tag="SP-B-CW-MAIN", host_ref="W-B-CW",
                      position=pt(ft(6), ft(18)), pipe_diameter=inch(4),
                      sleeve_diameter=inch(6), axis="horizontal",
                      center_elevation=ft(-1.587)),
    SleevePenetration(uid="CBPW07AAAA", tag="SP-B-CW-HW", host_ref="W-B-CW",
                      position=pt(ft(6, 6), ft(18)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_HOT, center_elevation=ft(-0.96)),
    # (SP-B-CW-COND stood at (7', 18') until 2026-07-30, for the condensate collector's run up
    # to FX-1's basin. PR-B-COND no longer crosses this wall at all — it now terminates over
    # the sauna's floor drain, which is south of y=18' — so the hole is retired rather than
    # left cast for a route nothing takes, the same call the SUITE drain sleeve got below.)
    # The sauna group's vent crossing, on its way north to the shared radon/vent chase. x=9'
    # is the one free slot on this wall: the supply and drain sleeves either side of it run
    # 2'-3" to 8' at 5"+ pitch, and 9' leaves 12" to the nearest of them and 6" to W-B-STR's
    # west face. Elevation is the run's own interpolated centreline where it passes through.
    SleevePenetration(uid="CBPW24AAAA", tag="SP-B-CW-SAUNA-VENT", host_ref="W-B-CW3",
                      position=pt(ft(9), ft(18)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), axis="horizontal",
                      purpose=Service.VENT, center_elevation=ft(-1.276)),
    SleevePenetration(uid="CBPW09AAAA", tag="SP-B-CW-BATH1-CW", host_ref="W-B-CW3",
                      position=pt(ft(7, 4.8), ft(18)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.87)),
    SleevePenetration(uid="CBPW10AAAA", tag="SP-B-CW-WASH-CW", host_ref="W-B-CW3",
                      position=pt(ft(8), ft(18)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.87)),
    # (There is no SUITE drain sleeve here. The ensuite stack drops at x=13' — east of this
    # wall's x 1'..10' extent — and its collector runs south of y=18' to the main, so it
    # never crosses W-B-CW. A sleeve was authored at (9', 18') for a route the run does not
    # take; `mep.sleeve_coverage` had it as the one unclaimed drain sleeve on this wall, and
    # a hole cast for nothing is the same defect as a missing one.)
    # W-B-STR (x=10', y 18'-6"..35'), the stair shaft's west wall — the stair-foot bathroom's
    # only way out to the mechanical room's trunks (2026-07-30). Three crossings at the
    # basement ceiling, spread 6"–18" apart along y so the 4"-tolerance sleeve matcher can
    # tell them apart, and all of them land inside the room's 18'-6"..21'-6" depth:
    #   vent  at y=21'-0", highest of the three (its riser stands 9" further north, inside
    #          the partition itself, and the leg turns west just south of it)
    #   cold   at y=20'-3"
    #   hot    at y=19'-9"
    # The fourth service, the drain, goes *under* the footing instead — SP-B-STR-BATH-DR.
    SleevePenetration(uid="CBPW23AAAA", tag="SP-B-STR-BATH-VENT", host_ref="W-B-STR2",
                      position=pt(ft(10), ft(21)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.VENT, center_elevation=ft(-1.25)),
    SleevePenetration(uid="CBPW25AAAA", tag="SP-B-STR-BATH-CW", host_ref="W-B-STR2",
                      position=pt(ft(10), ft(20, 3)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.9)),
    SleevePenetration(uid="CBPW26AAAA", tag="SP-B-STR-BATH-HW", host_ref="W-B-STR2",
                      position=pt(ft(10), ft(19, 9)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_HOT, center_elevation=ft(-1)),
    # The laundry tub's branch west to PR-B-MAIN-DRAIN (2026-07-31). Its own crossing at
    # y=18'-9", a foot south of the stair-bathroom group above and 3" clear of W-B-CW2's
    # north face, which is why the tub's waste drops at 18'-9" rather than under its own
    # centre — see plan/fixtures.py. PR-B-LSINK-DRAIN's invert at x=10' is -1'-1 3/4"
    # project, interpolated along its 1.32"/ft fall; the sleeve is cast at the pipe's
    # centerline, 1" (half a diameter) above that, which is what `mep.sewer_exit_invert`
    # matches to within 1/2".
    SleevePenetration(uid="HTE6ZE86KX", tag="SP-B-STR-LSINK-DR", host_ref="W-B-STR2",
                      position=pt(ft(10), ft(18, 9)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), axis="horizontal",
                      center_elevation=ft(-1.0594)),
    # W-B-CE (y=18', x 18..36) — the kitchen lines' way east. x-columns moved 2026-07-30 with
    # the sink to the north wall and again the same day with the sink/dishwasher flip (see
    # plan/placeables.py's kitchen header); y=18' is W-B-CE's own line and is unaffected.
    SleevePenetration(uid="CBPW12AAAA", tag="SP-B-CE-KITCH-DR", host_ref="W-B-CE",
                      position=pt(ft(28, 7), ft(18)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), axis="horizontal",
                      center_elevation=ft(-1.17)),
    SleevePenetration(uid="CBPW13AAAA", tag="SP-B-CE-KITCH-CW", host_ref="W-B-CE",
                      position=pt(ft(29, 0.6), ft(18)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.86)),
    SleevePenetration(uid="CBPW14AAAA", tag="SP-B-CE-KITCH-HW", host_ref="W-B-CE",
                      position=pt(ft(29, 6.6), ft(18)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_HOT, center_elevation=ft(-0.97)),
    # W-B-CS2 (x=18', y 13'-10"..18') — the kitchen drain's crossing of the centre line,
    # up at the ceiling well above D-B-GYM's 6'-8" head.
    SleevePenetration(uid="CBPW15AAAA", tag="SP-B-CS2-KITCH", host_ref="W-B-CS2",
                      position=pt(ft(18), ft(16, 6)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), axis="horizontal",
                      center_elevation=ft(-1.56)),
    SleevePenetration(uid="CBPW21AAAA", tag="SP-B-CS2-CW", host_ref="W-B-CS2",
                      position=pt(ft(18), ft(16)), pipe_diameter=inch(1.25),
                      sleeve_diameter=inch(2.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-0.86)),
    SleevePenetration(uid="CBPW22AAAA", tag="SP-B-CS2-HW", host_ref="W-B-CS2",
                      position=pt(ft(18), ft(15, 6)), pipe_diameter=inch(1),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_HOT, center_elevation=ft(-0.97)),
    # W-B-CS (x=18', y 0..13'-10") — the condensate collector's two crossings.
    # Re-levelled 2026-07-30 with PR-B-COND's new termination: same hole, same plan position,
    # 3/8" lower than the crossing it was cast for.
    SleevePenetration(uid="CBPW16AAAA", tag="SP-B-CS-COND", host_ref="W-B-CS",
                      position=pt(ft(18), ft(9)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      center_elevation=ft(-1.567)),
    SleevePenetration(uid="CBPW17AAAA", tag="SP-B-CS-COND2", host_ref="W-B-CS",
                      position=pt(ft(18), ft(1, 5.3)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      center_elevation=ft(-0.987)),
    # Perimeter exits.
    # The building drain leaves *under* FT-B-S1, not through W-B-S1 (2026-07-30): with the
    # sewer connection below the slab there is no wall left at that depth — the walls stop at
    # -9'-0", the slab top — so the exit is an under-footing protection sleeve set at the
    # footing centerline, y=0. center_elevation is the pipe centreline where it crosses:
    # PR-B-MAIN-DRAIN's invert there is -10'-6 1/4", so with the 4" building drain
    # (2026-07-31 upsize) the sleeve centre is invert + 2" = -10'-4 1/4" = ft(-10.356).
    # `mep.footing_clearance` is what requires this sleeve (IRC P2604) and matches the run to
    # it; `mep.sewer_exit_invert` holds the invert to the number cast in.
    SleevePenetration(uid="CBPW18AAAA", tag="SP-B-SEWER-EXIT", host_ref="FT-B-S1",
                      position=pt(ft(3), ft(0)), pipe_diameter=inch(4),
                      sleeve_diameter=inch(6), axis="horizontal",
                      center_elevation=ft(-10.356)),
    SleevePenetration(uid="CBPW19AAAA", tag="SP-B-S1-HYD", host_ref="W-B-S1",
                      position=pt(ft(5), ft(0, 6)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-6)),
    SleevePenetration(uid="CBPW20AAAA", tag="SP-B-N3-HYD", host_ref="W-B-N3",
                      position=pt(ft(5), ft(35, 6)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(1.5), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-6)),
]

# The hydrant line's garage-foundation protection (IRC P2604): the buried run passes under
# FT-GF-S-DR at its 6' bury — 22" below the footing's 4'-2" bearing plane, directly beneath
# it, so lateral offset zero — inside a protection sleeve. `mep.footing_clearance` requires
# it. Being *under* a footing is not clearance from it: the 45° cone opens downward, and a
# pipe on the footing's own centreline is the worst case in it, not the best.
#
# There were two other sleeves here.
#
# SP-G-HYDRANT-PED was the block-out through the 4" topping pedestal the barrel used to
# pass on its way up. The pedestal was retired 2026-08-03 (params/foundations.py) and its
# block-out went with it: the barrel now rises through SP-G-HYDRANT in SL-G-FLOOR and
# nothing else.
#
# SP-GF-W-HYD (deleted 2026-08-15) claimed to protect the rise where it encroached on
# FT-GF-W's influence line, and it protected nothing. It was authored at (0'-9.6", 61'-6"),
# which put its bore straight across FT-GF-W's 20" width — a 2" hole east-west through the
# footing line, at the 6' bury, with the actual pipe 8" away at x = 1'-6" and running
# *parallel* to that footing, never crossing it. A sleeve is the hole a pipe passes through;
# there was no pipe in this one.
#
# It graded PASS because `mep.footing_clearance` asked only that *some* sleeve on the pour
# sit within 0.3 m of the encroaching segment, and 8.4" is 0.213 m. That tolerance is now a
# real alignment test — the run has to actually thread the sleeve — so this could not come
# back silently (checks/mep/plumbing_concrete.py).
#
# The encroachment it was papering over was real, and the fix was to stop encroaching: the
# hydrant moved off the wall to (5'-0", 60'-0"), the run lost its west jog, and there is no
# longer any west-footing interaction to protect. → params/foundations.py.
GARAGE_SLEEVES = [
    SleevePenetration(uid="CGPW01AAAA", tag="SP-GF-S-HYD", host_ref="FT-GF-S-DR",
                      position=pt(ft(5), ft(41)), pipe_diameter=inch(0.75),
                      sleeve_diameter=inch(2), axis="horizontal",
                      purpose=Service.WATER_COLD, center_elevation=ft(-6)),
]
