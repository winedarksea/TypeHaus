"""Starter plumbing-fixture catalog.

Tags are deliberately distinct from Catlin's house-local ``FX-TOILET`` / ``FX-LAV`` /
``FX-SHOWER``: both catalogs merge at load, and a duplicate tag is a hard error there.

A fixture's ``height`` is its **overall** height including the spout, because the generated
symbol keeps every part inside the declared box. That is why a lavatory is 40" and not 36" —
the deck plane lands where the counter is, and the faucet occupies the band above it.
"""

from __future__ import annotations

from typehaus.model import FixtureType, Mount, MountKind, Service, ft, inch

from library.placeables._zones import front_zone

REFERENCE = "Residential planning allowance; final fixture selection by owner."

TOILET = FixtureType(
    tag="FX-TOILET-STD", name="Water closet", footprint=(ft(1, 8), ft(2, 4)), height=ft(2, 6),
    plan_symbol="toilet", source=REFERENCE,
    needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(ft(1, 8), ft(2, 4), ft(1, 9), "water-closet front clearance"),),
)
LAVATORY = FixtureType(
    tag="FX-LAV-24", name="Lavatory", footprint=(ft(2), ft(1, 8)), height=ft(3, 4),
    plan_symbol="lavatory", source=REFERENCE,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
)
VANITY = FixtureType(
    tag="FX-VANITY-36", name="Vanity with sink", footprint=(ft(3), ft(1, 9)), height=ft(3, 6),
    plan_symbol="vanity", source=REFERENCE,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(front_zone(ft(3), ft(1, 9), ft(1, 9), "lavatory front clearance"),),
)
TUB = FixtureType(
    tag="FX-TUB-60", name="Alcove bathtub", footprint=(ft(5), ft(2, 6)), height=ft(1, 8),
    plan_symbol="tub", source=REFERENCE,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
)
SHOWER = FixtureType(
    tag="FX-SHOWER-36", name="Shower", footprint=(ft(3), ft(3)), height=ft(7),
    plan_symbol="shower", source=REFERENCE,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
)
# A drop-in sink's bowls hang below its deck, so the mount elevation puts that deck at the
# standard 36" counter height rather than leaving the fixture sitting on the floor.
KITCHEN_SINK = FixtureType(
    tag="FX-KITCHEN-SINK-33", name="Double-bowl kitchen sink", footprint=(ft(2, 9), ft(1, 10)),
    height=ft(1, 6), plan_symbol="kitchen-sink", source=REFERENCE,
    mount=Mount(kind=MountKind.WALL, elevation=inch(21)),
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.VENT}),
)

STARTER_FIXTURE_TYPES = (TOILET, LAVATORY, VANITY, TUB, SHOWER, KITCHEN_SINK)
