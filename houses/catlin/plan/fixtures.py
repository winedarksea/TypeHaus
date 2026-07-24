# haus: editable
# Permit-schedule plumbing fixture/appliance *instances* for Catlin (M3 WP3.4/WP3.10).
# `# haus: editable` so UI drags (moving a toilet, the washer, …) round-trip to source.
# Their FixtureType/ApplianceType catalog lives in the non-editable `fixture_types.py`
# (it uses `frozenset(...)`, which the editable dialect forbids).

from typehaus import Appliance, Fixture, ft, pt
from typehaus.model import deg, m

MAIN_FIXTURES = (
    Fixture(uid="CMQ801AAAA", tag="FX-M-BATH1-WC", type_ref="FX-TOILET", room="RM-M-BATH1",
            position=pt(ft(2), ft(24)), wall_ref="W-M-BAE"),
    Fixture(uid="CMQ802AAAA", tag="FX-M-BATH1-LAV", type_ref="FX-LAV", room=None,
            position=pt(m(1.22992), m(7.17573)), wall_ref="W-M-BAE", rotation=deg(90)),
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
