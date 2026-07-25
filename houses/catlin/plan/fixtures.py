# haus: editable
# Permit-schedule plumbing fixture/appliance *instances* for Catlin (M3 WP3.4/WP3.10).
# `# haus: editable` so UI drags (moving a toilet, the washer, …) round-trip to source.
# Their FixtureType/ApplianceType catalog lives in the non-editable `fixture_types.py`
# (it uses `frozenset(...)`, which the editable dialect forbids).

from typehaus import Appliance, Fixture, ft, pt

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
)


SECOND_FIXTURES = (
    Fixture(uid="CSQ801AAAA", tag="FX-S-ENSUITE-WC", type_ref="FX-TOILET", room="RM-S-ENSUITE",
            position=pt(ft(5), ft(31)), wall_ref="W-S-BD-N"),
    Fixture(uid="CSQ802AAAA", tag="FX-S-ENSUITE-LAV", type_ref="FX-LAV", room="RM-S-ENSUITE",
            position=pt(ft(6), ft(31)), wall_ref="W-S-BD-N"),
    Fixture(uid="CSQ803AAAA", tag="FX-S-ENSUITE-SH", type_ref="FX-SHOWER", room="RM-S-ENSUITE",
            position=pt(ft(5), ft(33)), wall_ref="W-S-BD-N"),
)
