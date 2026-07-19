"""Permit-schedule plumbing fixtures for Catlin (M3 WP3.4/WP3.10)."""

from __future__ import annotations

from typehaus import Fixture, FixtureType, Service, ft, pt

FIXTURE_TYPES = (
    FixtureType(tag="FX-TOILET", name="Water closet", footprint=(ft(2, 6), ft(2, 6)),
                height=ft(2, 6), needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
                source="Residential planning allowance; final fixture selection by owner."),
    FixtureType(tag="FX-LAV", name="Lavatory", footprint=(ft(2), ft(1, 9)), height=ft(3),
                needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN}),
                source="Residential planning allowance; final fixture selection by owner."),
    FixtureType(tag="FX-SHOWER", name="Shower", footprint=(ft(3), ft(3)), height=ft(7),
                needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN}),
                source="Residential planning allowance; final fixture selection by owner."),
    FixtureType(tag="FX-WASHER", name="Clothes washer", footprint=(ft(2, 3), ft(2, 6)),
                height=ft(3), needs=frozenset({Service.WATER_HOT, Service.WATER_COLD,
                                                Service.DRAIN, Service.POWER_240}),
                source="Residential planning allowance; final appliance selection by owner."),
)

MAIN_FIXTURES = (
    Fixture(uid="CMQ801AAAA", tag="FX-M-BATH1-WC", type_ref="FX-TOILET", room="RM-M-BATH1",
            position=pt(ft(2), ft(24)), wall_ref="W-M-BAE"),
    Fixture(uid="CMQ802AAAA", tag="FX-M-BATH1-LAV", type_ref="FX-LAV", room="RM-M-BATH1",
            position=pt(ft(3, 6), ft(24)), wall_ref="W-M-BAE"),
    Fixture(uid="CMQ803AAAA", tag="FX-M-BATH2-WC", type_ref="FX-TOILET", room="RM-M-BATH2",
            position=pt(ft(3), ft(18)), wall_ref="W-M-BA2E"),
    Fixture(uid="CMQ804AAAA", tag="FX-M-LAUNDRY", type_ref="FX-WASHER", room="RM-M-LAUNDRY",
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
