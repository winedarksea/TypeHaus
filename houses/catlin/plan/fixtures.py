# haus: editable
# Permit-schedule plumbing fixture/appliance *instances* for Catlin (M3 WP3.4/WP3.10).
# `# haus: editable` so UI drags (moving a toilet, the washer, …) round-trip to source.
# Their FixtureType/ApplianceType catalog lives in the non-editable `fixture_types.py`
# (it uses `frozenset(...)`, which the editable dialect forbids).

from typehaus import Appliance, Fixture, Mount, MountKind, deg, ft, inch, pt

# RM-M-BATH1's clear face is 3'-2" x 4'-3-1/4" (x 0'-6-5/8"..3'-8-5/8", y 21'-10-3/8"..
# 26'-1-5/8"). A 2'-6" water closet plus a 1'-9"-deep lavatory is 4'-3" of that 4'-3-1/4",
# so the two fixtures pack wall-to-wall down the room with ~1/8" at each end and nothing
# between them: the WC takes the south end, the lavatory the north-east corner hard against
# its W-M-BAE wet wall. This is the only arrangement that keeps both footprints inside the
# room, out of D-M-BATH1's swing, and off each other — the room is genuinely too small for
# both fixtures at these sizes, and the design fix is a bigger bath, not a better packing.
MAIN_FIXTURES = (
    Fixture(uid="CMQ801AAAA", tag="FX-M-BATH1-WC", type_ref="FX-TOILET", room="RM-M-BATH1",
            position=pt(ft(2), ft(23, 1.5)), wall_ref="W-M-BAE"),
    Fixture(uid="CMQ802AAAA", tag="FX-M-BATH1-LAV", type_ref="FX-LAV", room="RM-M-BATH1",
            position=pt(ft(2, 8.5), ft(25, 3)), wall_ref="W-M-BAE"),
    Fixture(uid="CMQ803AAAA", tag="FX-M-BATH2-WC", type_ref="FX-TOILET", room="RM-M-BATH2",
            position=pt(ft(3), ft(18)), wall_ref="W-M-BA2E"),
    Appliance(uid="CMQ804AAAA", tag="FX-M-LAUNDRY", type_ref="APPL-WASHER", room="RM-M-LAUNDRY",
              position=pt(ft(10, 6), ft(20)), wall_ref="W-M-BA2E2"),
    # Kitchen sink: dropped into the 36" base FURN-M-KIT-SINKBASE and centred on
    # WIN-M-KITCH (y=32'-8", 42" sill = counter height), so it centres in the 24" counter
    # depth at x=34'-5 3/8". rotation -90 turns its back (+y, where the faucet is) to the
    # east wall. W-M-E2 is the wet wall — a 2x6 exterior wall, deep enough for the stack,
    # and one that W-S-E3/E4/E5 stack on, so the vent rises inside it without an offset.
    # `drain_position` sets the trap 6 5/8" back from the bowl centre, over SP-M-KITCH.
    # The 21" mount is what drops the bowls into the counter instead of standing them on the
    # floor: the resolver reads the *instance* Mount, so the type's own recommendation has to
    # be restated here to take effect (deck lands at ~36", the base cabinet's top).
    Fixture(uid="WZRCBGNDFW", tag="FX-M-KITCH-SINK", type_ref="FX-KITCHEN-SINK-33", room="RM-M-LIVING",
            position=pt(ft(34, 5.375), ft(32, 8)), rotation=deg(-90), wall_ref="W-M-E2",
            mount=Mount(kind=MountKind.WALL, elevation=inch(21)),
            drain_position=pt(ft(35), ft(32, 8))),
)


SECOND_FIXTURES = (
    Fixture(uid="CSQ801AAAA", tag="FX-S-ENSUITE-WC", type_ref="FX-TOILET", room="RM-S-ENSUITE",
            position=pt(ft(5), ft(31)), wall_ref="W-S-BD-N"),
    Fixture(uid="CSQ802AAAA", tag="FX-S-ENSUITE-LAV", type_ref="FX-LAV", room="RM-S-ENSUITE",
            position=pt(ft(6), ft(31)), wall_ref="W-S-BD-N"),
    Fixture(uid="CSQ803AAAA", tag="FX-S-ENSUITE-SH", type_ref="FX-SHOWER", room="RM-S-ENSUITE",
            position=pt(ft(5), ft(33)), wall_ref="W-S-BD-N"),
)
