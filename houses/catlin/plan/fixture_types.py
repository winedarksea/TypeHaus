"""Permit-schedule plumbing fixture/appliance *type library* for Catlin (M3 WP3.4/WP3.10).

Non-editable on purpose: these are catalog type definitions (not placed instances), and
they use `frozenset(...)` service sets that the editable dialect disallows. The movable
Fixture/Appliance *instances* that reference these types live in the editable `fixtures.py`
so UI drags round-trip to source.
"""

from __future__ import annotations

from typehaus import (ApplianceType, ClearancePolicy, ClearanceZone, FixtureType,
                      Footprint2D, Service, ft, inch, pt)

FIXTURE_TYPES = (
    FixtureType(tag="FX-TOILET", name="Water closet", footprint=(ft(2, 6), ft(2, 6)),
                height=ft(2, 6), plan_symbol="toilet", needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
                clearances=(ClearanceZone(
                    footprint=Footprint2D(points=(pt(ft(-1, 3), ft(-1, 3)), pt(ft(1, 3), ft(-1, 3)),
                                                  pt(ft(1, 3), ft(3)), pt(ft(-1, 3), ft(3)))),
                    purpose="water-closet clearance", policy=ClearancePolicy.REQUIRED,
                    source="MN/IRC planning profile: 30 in side clearance and 21 in front clearance",
                    code_profile="MN/IRC",
                ),),
                source="Residential planning allowance; final fixture selection by owner."),
    FixtureType(tag="FX-LAV", name="Lavatory", footprint=(ft(2), ft(1, 9)), height=ft(3),
                plan_symbol="lavatory", needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN}),
                source="Residential planning allowance; final fixture selection by owner."),
    FixtureType(tag="FX-SHOWER", name="Shower", footprint=(ft(3), ft(3)), height=ft(7),
                plan_symbol="shower", needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN}),
                source="Residential planning allowance; final fixture selection by owner."),
    # --- BATH1-only compacts -----------------------------------------------------------
    # RM-M-BATH1's clear face is 3'-2" x 4'-3 1/4"; the shared FX-TOILET + FX-LAV pair
    # packed it wall-to-wall with ~1/8" to spare, so this room takes purpose-picked compact
    # types instead. The shared types stay untouched — they serve three other rooms.
    # Wall-hung WC in the TOTO RP compact class: 15" wide x 19.3" deep at the bowl, tank and
    # steel in-wall carrier frame inside the 2x6 wet wall (the carrier is why the instance
    # authors its drain_position on the wall line rather than under the bowl). The clearance
    # zone restates the same code minimums as FX-TOILET's — 30" between finished side walls,
    # 21" in front of the rim — measured from this smaller footprint.
    FixtureType(tag="FX-TOILET-WH", name="Wall-hung water closet (compact)",
                footprint=(inch(15), inch(19.3)), height=inch(21),
                plan_symbol="toilet", needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
                clearances=(ClearanceZone(
                    footprint=Footprint2D(points=(pt(ft(-1, 3), inch(-9.65)), pt(ft(1, 3), inch(-9.65)),
                                                  pt(ft(1, 3), inch(30.65)), pt(ft(-1, 3), inch(30.65)))),
                    purpose="water-closet clearance", policy=ClearancePolicy.REQUIRED,
                    source="MN/IRC planning profile: 30 in side clearance and 21 in front clearance",
                    code_profile="MN/IRC",
                ),),
                source="TOTO RP compact wall-hung class, 15\" x 19.3\", on an in-wall carrier in the 2x6 wet wall (W-M-BAE); BATH1 only."),
    FixtureType(tag="FX-LAV-COMPACT", name="Compact lavatory", footprint=(ft(1, 6), inch(14)),
                height=ft(2, 10), plan_symbol="lavatory",
                needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN}),
                source="Compact powder-room lavatory, 18\" x 14\"; BATH1 only, final fixture selection by owner."),
    # Frost-free wall hydrant for the garage wash-down area. The whole point of the type is
    # what is *not* in `needs`: only WATER_COLD. A hydrant drains through its own weep at the
    # buried shutoff, not into the sanitary system — and because `needs` carries no
    # Service.DRAIN, `_missing_sleeve_findings` (checks/mep/plumbing.py) correctly declines
    # to fire a "no sleeve serving it" FAIL against a fixture that has no drain to sleeve.
    # The slab penetration it *does* need is the supply sleeve, SP-G-HYDRANT.
    #
    # Footprint is the escutcheon, not the buried barrel: what a plan can draw is the head at
    # the wall. Height is the handle height above the garage slab.
    FixtureType(tag="FX-HYDRANT-Y34SS", name="Frost-free wall hydrant, 3/4\" stainless",
                footprint=(inch(6), inch(6)), height=ft(2, 6), plan_symbol="hydrant",
                needs=frozenset({Service.WATER_COLD}),
                source="Y34SS-class frost-free wall hydrant, 3/4\" stainless, 6' bury. "
                       "Specified with the manufacturer's supplemental epoxy coating over "
                       "the buried barrel (the garage floor runs salt slush all winter and "
                       "the standard finish is not rated for chloride immersion), and a "
                       "screw-on hose-bib vacuum breaker on the outlet — required backflow "
                       "protection for a hose connection. NO floor drain: see "
                       "notes/garage_hydrant.md."),
)

APPLIANCE_TYPES = (
    ApplianceType(tag="APPL-WASHER", name="Clothes washer", footprint=(ft(2, 3), ft(2, 6)),
                  height=ft(3), plan_symbol="washer", needs=frozenset({Service.WATER_HOT, Service.WATER_COLD,
                                                  Service.DRAIN, Service.POWER_240}),
                  source="Residential planning allowance; final appliance selection by owner."),
)
