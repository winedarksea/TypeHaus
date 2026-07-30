# haus: editable
# Permit-schedule plumbing fixture/appliance *instances* for Catlin (M3 WP3.4/WP3.10).
# `# haus: editable` so UI drags (moving a toilet, the washer, …) round-trip to source.
# Their FixtureType/ApplianceType catalog lives in the non-editable `fixture_types.py`
# (it uses `frozenset(...)`, which the editable dialect forbids).

from typehaus import Appliance, Fixture, Mount, MountKind, deg, ft, inch, pt
from typehaus.model import m

# RM-M-BATH1's clear face is 3'-2" x 4'-3-1/4" (x 0'-6-5/8"..3'-8-5/8", y 21'-10-3/8"..
# 26'-1-5/8") — too small to pack the shared FX-TOILET + FX-LAV pair without running them
# wall-to-wall, so this room takes the BATH1-only compact types (fixture_types.py).
# The WC is a wall-hung compact (15" x 19.3") whose back sits 1/8" off W-M-BAE's west
# finish face at the room's south end; rotation 90 turns its back (-y local) east onto
# that wall. Its steel in-wall carrier lives in the INT_2X6_PLUMBING stud bay — which is
# what that wet wall is *for* — so drain_position is the carrier outlet on the wall's
# centerline (x=6', shifted 2' east with W-M-BAE on 2026-07-28), where SP-M-WC1 is
# authored, not a point under the bowl. The compact lavatory (18" x 14") backs against
# the same wet wall beside the WC; its trap arm reaches W-M-BAE directly. A south-wall
# layout was tried and reverted (2026-07-28) — W-M-HS1 is a plain 3.5" partition, not a
# wet wall, so it can't carry either fixture's drain stack (`advisory.wet_wall_depth`),
# and PR-M-WC-VENT (plan/mep.py) already takes off at W-M-BAE's x=6' line.
MAIN_FIXTURES = (
    Fixture(uid="CMQ801AAAA", tag="FX-M-BATH1-WC", type_ref="FX-TOILET-WH", room="RM-M-BATH1",
            position=pt(m(1.296633), m(7.80786)), rotation=deg(90), wall_ref="W-M-BAE",
            drain_position=pt(ft(6), ft(22, 7))),
    # y nudged +6" (2026-07-29, with N-M-W2/N-M-C2's north push for the BATH2 wall move):
    # the room's south face moved with it and the lavatory's old y left it poking through
    # into the hall (test_bath1_fixtures_sit_inside_the_room_and_clear_of_each_other).
    Fixture(uid="CMQ802AAAA", tag="FX-M-BATH1-LAV", type_ref="FX-LAV-COMPACT", room="RM-M-BATH1",
            position=pt(m(1.315138), m(7.00891)), wall_ref="W-M-BAE", rotation=deg(180)),
    # Backs east onto W-M-BA2E — the INT_2X6_PLUMBING wet wall it has always drained into,
    # now actually sitting against it instead of floating 4' away mid-room. rotation 90
    # turns its back (-y local) east onto the wall; the centre at x=6'-8 3/8" puts the
    # tank edge on the room's 7'-11 3/8" east clear face. Footprint x 5'-5 3/8"..7'-11 3/8",
    # y 17'-3"..19'-9"; its 30"/21" REQUIRED clearance zone (x 3'-8 3/8"..7'-11 3/8",
    # same y band) holds nothing else — the room's only other object is the door swing.
    # The `drain_position` override is gone as of 2026-07-29: it was parked on SP-M-WC2's
    # old (3', 18') position — the corner fitting where PR-B-MAIN-DRAIN turns — to keep the
    # pre-pour sleeve contract holding while the WC moved to this wall. The plumbing pass
    # re-pointed both the sleeve and PR-B-WC2-DRAIN at the real closet flange, which for a
    # floor-mounted WC is simply under the bowl, so the convention (fixture position) is now
    # correct and an override would only be a second place to keep in sync.
    Fixture(uid="CMQ803AAAA", tag="FX-M-BATH2-WC", type_ref="FX-TOILET-STD", room="RM-M-BATH2",
            position=pt(m(0.686504), m(6.14439)), rotation=deg(0), wall_ref="W-M-BA2E"),
    # BATH2 has separate bathing fixtures: the 36" shower sits north of the door swing,
    # while the 60" tub runs north/south along the east plumbing wall. They are intentionally
    # separate instances/types rather than a tub-shower combination, so the permit schedule
    # and future owner selections can treat them independently.
    Fixture(uid="CMQ805AAAA", tag="FX-M-BATH2-SH", type_ref="FX-SHOWER-36", room="RM-M-BATH2",
            position=pt(m(1.88387), m(4.58801)), wall_ref="W-M-BA2E",
            drain_position=pt(ft(1, 9), ft(17, 3))),
    # Shifted 6" north (2026-07-29) with the W-M-HS1..4 wall move that gave BATH2 8" more
    # depth: the old position overlapped FX-M-BATH2-SH by ~1.3" (`advisory.fixture_overlap`);
    # this clears it with a 4.7" gap and still leaves 4" to the room's new north face.
    Fixture(uid="CMQ806AAAA", tag="FX-M-BATH2-TUB", type_ref="FX-TUB-60", room="RM-M-BATH2",
            position=pt(m(1.96436), m(5.91312)), rotation=deg(90), wall_ref="W-M-BA2E",
            drain_position=pt(ft(7, 4), ft(19, 4.8))),
    # RM-M-BATH2's double-basin sink uses the shared kitchen-sink catalog type rather than
    # a house-local surrogate. Its 27" mount puts the library sink's deck at the intended
    # lavatory height; rotation +90 turns the back of the symbol toward the west wall.
    Fixture(uid="CMQ807AAAA", tag="FX-M-BATH2-SINK", type_ref="FX-KITCHEN-SINK-33",
            room="RM-M-BATH2", position=pt(ft(1), ft(16, 6)), rotation=deg(90),
            wall_ref="W-M-W3", mount=Mount(kind=MountKind.WALL, elevation=inch(27)),
            drain_position=pt(ft(1), ft(16, 6))),
    Appliance(uid="CMQ804AAAA", tag="FX-M-LAUNDRY", type_ref="APPL-WASHER", room="RM-M-LAUNDRY",
              position=pt(ft(10, 6), ft(20)), wall_ref="W-M-BA2E2"),
    # Kitchen sink: dropped into the 36" base FURN-M-KIT-SINKBASE and centred on
    # WIN-M-KITCH (y=32'-8", 42" sill = counter height), so it centres in the 24" counter
    # depth at x=34'-5 3/8". rotation -90 turns its back (+y, where the faucet is) to the
    # east wall. W-M-E2 is the wet wall — a 2x6 exterior wall, deep enough for the stack,
    # and one that W-S-E3/E4/E5 stack on, so the vent rises inside it without an offset.
    # `drain_position` sets the trap 6 5/8" back from the bowl centre, over SP-M-KITCH.
    # The 27" mount is what drops the bowls into the counter instead of standing them on the
    # floor: the resolver reads the *instance* Mount, so the type's own recommendation has to
    # be restated here to take effect. The symbol's deck sits at half its 18" height, so 27"
    # lands the rim exactly on the 36" counter, 9" of bowl hanging into the base below it.
    Fixture(uid="WZRCBGNDFW", tag="FX-M-KITCH-SINK", type_ref="FX-KITCHEN-SINK-33", room="RM-M-LIVING",
            position=pt(ft(34, 5.375), ft(32, 8)), rotation=deg(-90), wall_ref="W-M-E2",
            mount=Mount(kind=MountKind.WALL, elevation=inch(27)),
            drain_position=pt(ft(35), ft(32, 8))),
)


# RM-S-BATH1 is the *hall* bath (the source's 80.73 sf "Bathroom" in the NW corner); the
# tag predates the suite's own bath and is kept — see storeys/second.py's header.
#
# Layout (the de-overlap pass storeys/second.py's FLOOR_HEAT comment used to ask for):
# the tub-shower stays in the room's centre-north (its SL-D-SHOWER detail slice cuts the
# unit at x=5', so it must keep crossing that plane); the WC backs onto the west
# exterior 2x6 (rotation -90 turns its back west onto W-S-W1 — an exterior wet wall by the
# same reasoning as FX-M-KITCH-SINK's W-M-E2), sitting low enough that its 30"-wide /
# 21"-front REQUIRED clearance zone (x 0'-3"..4'-6", y 28'-9"..31'-3") stops 3" south of
# the tub-shower; the lav backs east onto W-S-BA-E1B (INT_2X6_PLUMBING, rotation 90), its
# back at the room's 9'-11 3/8" east face, south of the chase's y=33'-3 3/8" cut line.
# Footprints — WC x 0'-3"..2'-9" y 28'-9"..31'-3", tub-shower (FX-TUBSHOWER, 5'x2'-6")
# x 0'-8"..5'-8" y 32'-9"..35'-3", lav x 8'-2"..9'-11" y 30'-0"..32'-0" — are pairwise
# disjoint with 9"+ between any two.
SECOND_FIXTURES = (
    Fixture(uid="CSQ801AAAA", tag="FX-S-BATH1-WC", type_ref="FX-TOILET-STD", room="RM-S-BATH1",
            position=pt(m(0.560313), m(9.2783)), rotation=deg(90), wall_ref="W-S-W1"),
    Fixture(uid="CSQ802AAAA", tag="FX-S-BATH1-LAV", type_ref="FX-LAV-24", room="RM-S-BATH1",
            position=pt(ft(9, 0.5), ft(31)), rotation=deg(90), wall_ref="W-S-BA-E1B"),
    Fixture(uid="CSQ803AAAA", tag="FX-S-BATH1-SH", type_ref="FX-TUBSHOWER-60", room="RM-S-BATH1",
            position=pt(m(1.66988), m(10.4013)), wall_ref="W-S-BD-N"),
    # The suite's own bath (source: 46.01 sf). Both walls it drains into are
    # INT_2X6_PLUMBING — W-S-DC2 west, W-S-SBS south — which is what `advisory.wet_wall_depth`
    # measures against preferences.toml's 5.5" drain-stack requirement.
    # D-S-SUITEBATH's 2'-6" leaf is hinged at the room's SW jamb and sweeps a quarter disc
    # to (12'-8", 18'-5"), so nothing sits in the room's SW quadrant: the WC goes north of
    # the swing on the west wet wall, the lav east of it on the south one, the shower in the
    # NE corner. Every wall_ref here is a 5 1/2" wall — INT_2X6_PLUMBING west and south,
    # CATLIN_INT_2X6_BRG east — because `advisory.wet_wall_depth` holds a drain stack to
    # preferences.toml's 5.5", which a 2x4 partition cannot give it.
    Fixture(uid="CSQ804AAAA", tag="FX-S-SUITEBATH-WC", type_ref="FX-TOILET-STD",
            room="RM-S-SUITEBATH", position=pt(m(3.42422), m(6.34259)), wall_ref="W-S-DC2"),
    Fixture(uid="CSQ805AAAA", tag="FX-S-SUITEBATH-LAV", type_ref="FX-LAV-24",
            room="RM-S-SUITEBATH", position=pt(m(4.21659), m(6.46046)), wall_ref="W-S-SBS"),
    # The suite bath takes a tub-shower rather than the 36" pan it used to: the room's clear
    # face is 9'-8 1/8" x 22'-3 3/8" .. 15'-11 5/8" (x 9.677'..17.948', y 15.969'..22.281'),
    # and the east wall has 5'-0 of run to give a 60" x 30" alcove. Rotated -90 the back
    # (+y local) turns east onto W-S-C2C, so the footprint is x 15'-2"..17'-8",
    # y 17'-0"..22'-0": the same north and east edges the old pan had, extended south.
    # It clears the WC's REQUIRED zone (which reaches x 12'-7 3/4"), the lav on the south
    # wall (x 13'..15', y 16'-2 1/2"..17'-11 3/8"), and D-S-SUITEBATH's swing (out to
    # x 12'-8"). The plumbing end is north, where the pan's drain already was.
    Fixture(uid="CSQ809AAAA", tag="FX-S-SUITEBATH-TUBSH", type_ref="FX-TUBSHOWER-60",
            room="RM-S-SUITEBATH", position=pt(m(4.99282), m(5.96387)), rotation=deg(-90),
            wall_ref="W-S-C2C"),
    # The double-vanity alcove off the landing (source: 18.23 sf, two lavatories), backed
    # onto W-S-BD-N — the same 2x6 wet wall the hall bath drains into.
    Fixture(uid="CSQ807AAAA", tag="FX-S-VANITY-LAV1", type_ref="FX-LAV-24", room="RM-S-VANITY",
            position=pt(ft(1, 9), ft(25, 2)), wall_ref="W-S-BD-N"),
    Fixture(uid="CSQ808AAAA", tag="FX-S-VANITY-LAV2", type_ref="FX-LAV-24", room="RM-S-VANITY",
            position=pt(ft(4), ft(25, 2)), wall_ref="W-S-BD-N"),
)


# The garage wash-down hydrant. On the west wall near the NW corner: that wall carries only
# EQ-G-HEATER (at y=48', mounted 6'-0"), and the corner is clear of both north windows and
# of both EV receptacles at y=41.5'. Standing 1'-6" off the wall line puts it on its
# pedestal (PAD-G-HYDRANT) rather than in the salt slush the floor runs all winter, and
# leaves room to swing a hose onto it.
#
# The handle at 2'-6" is the type's height; everything below the slab — the 6' barrel, the
# buried shutoff, the supply run and the sleeve — is authored in params/foundations.py and
# plan/mep.py, none of which is UI-movable. This instance is, which is why it is here:
# the loader raises loader.uneditable_movable_element for a Fixture in a non-editable
# module, and fixture_types.py is not editable (it uses frozenset).
GARAGE_FIXTURES = (
    Fixture(uid="CGQ801AAAA", tag="FX-G-HYDRANT", type_ref="FX-HYDRANT-Y34SS",
            room="RM-GARAGE", position=pt(ft(1, 6), ft(62)), wall_ref="W-G-W"),
)
