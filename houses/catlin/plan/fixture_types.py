"""Permit-schedule plumbing fixture/appliance *type library* for Catlin (M3 WP3.4/WP3.10).

Non-editable on purpose: these are catalog type definitions (not placed instances), and
they use `frozenset(...)` service sets that the editable dialect disallows. The movable
Fixture/Appliance *instances* that reference these types live in the editable `fixtures.py`
so UI drags round-trip to source.
"""

from __future__ import annotations

from typehaus import (ApplianceType, ClearancePolicy, ClearanceZone, FixtureType,
                      Footprint2D, Service, ft, pt)

FIXTURE_TYPES = (
    FixtureType(tag="FX-TOILET", name="Water closet", footprint=(ft(2, 6), ft(2, 6)),
                height=ft(2, 6), needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
                clearances=(ClearanceZone(
                    footprint=Footprint2D(points=(pt(ft(-1, 3), ft(-1, 3)), pt(ft(1, 3), ft(-1, 3)),
                                                  pt(ft(1, 3), ft(3)), pt(ft(-1, 3), ft(3)))),
                    purpose="water-closet clearance", policy=ClearancePolicy.REQUIRED,
                    source="MN/IRC planning profile: 30 in side clearance and 21 in front clearance",
                    code_profile="MN/IRC",
                ),),
                source="Residential planning allowance; final fixture selection by owner."),
    FixtureType(tag="FX-LAV", name="Lavatory", footprint=(ft(2), ft(1, 9)), height=ft(3),
                needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN}),
                source="Residential planning allowance; final fixture selection by owner."),
    FixtureType(tag="FX-SHOWER", name="Shower", footprint=(ft(3), ft(3)), height=ft(7),
                needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN}),
                source="Residential planning allowance; final fixture selection by owner."),
)

APPLIANCE_TYPES = (
    ApplianceType(tag="APPL-WASHER", name="Clothes washer", footprint=(ft(2, 3), ft(2, 6)),
                  height=ft(3), needs=frozenset({Service.WATER_HOT, Service.WATER_COLD,
                                                  Service.DRAIN, Service.POWER_240}),
                  source="Residential planning allowance; final appliance selection by owner."),
)
