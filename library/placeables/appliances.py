"""Starter appliance catalog.

There is deliberately no shared ``APPL-WASHER`` here: ``houses/catlin/plan/fixture_types.py``
already owns that tag, and the two catalogs merge at load, so adding one would collide.
"""

from __future__ import annotations

from typehaus.model import ApplianceType, Service, ServicePort, ft, inch

from library.placeables._zones import front_zone

REFERENCE = "Residential planning allowance; final appliance selection by owner."

REFRIGERATOR = ApplianceType(
    tag="APPL-REFRIGERATOR", name="Refrigerator", footprint=(ft(3), ft(2, 10)), height=ft(6),
    plan_symbol="refrigerator", source=REFERENCE,
    needs=frozenset({Service.POWER_120}),
    ports=(ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(2))),),
    clearances=(front_zone(ft(3), ft(2, 10), ft(3), "refrigerator door swing"),),
)
GAS_RANGE = ApplianceType(
    tag="APPL-GAS-RANGE", name="Gas range", footprint=(ft(2, 6), ft(2, 6)), height=ft(3),
    plan_symbol="range", source=REFERENCE,
    needs=frozenset({Service.GAS, Service.POWER_120}),
    ports=(ServicePort(tag="gas", service=Service.GAS, position=(ft(0), ft(0), ft(0))),
           ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0)))),
)
ELECTRIC_RANGE = ApplianceType(
    tag="APPL-ELECTRIC-RANGE", name="Electric range", footprint=(ft(2, 6), ft(2, 6)), height=ft(3),
    plan_symbol="range", source=REFERENCE,
    needs=frozenset({Service.POWER_240}),
    ports=(ServicePort(tag="power", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))),),
)
DISHWASHER = ApplianceType(
    tag="APPL-DISHWASHER", name="Dishwasher", footprint=(ft(2), ft(2)), height=ft(2, 10),
    plan_symbol="dishwasher", source=REFERENCE,
    needs=frozenset({Service.WATER_HOT, Service.DRAIN, Service.POWER_120}),
    ports=(ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))),
           ServicePort(tag="supply", service=Service.WATER_HOT, position=(ft(0), ft(0), ft(0))),
           ServicePort(tag="drain", service=Service.DRAIN, position=(ft(0), ft(0), ft(0)))),
    clearances=(front_zone(ft(2), ft(2), ft(2), "dishwasher door swing"),),
)
DRYER = ApplianceType(
    tag="APPL-DRYER", name="Clothes dryer", footprint=(ft(2, 3), ft(2, 6)), height=ft(3, 2),
    # The dryer's exhaust duct has no ``Service`` member yet, so only its circuit is declared.
    plan_symbol="dryer", source=REFERENCE,
    needs=frozenset({Service.POWER_240}),
    ports=(ServicePort(tag="power", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))),),
)
# Over-the-range microwaves hang off the wall above the cooktop; the mount elevation is left
# to the placed instance, since it follows the cabinet run rather than the appliance.
MICROWAVE_OTR = ApplianceType(
    tag="APPL-MICROWAVE-OTR", name="Over-the-range microwave", footprint=(ft(2, 6), inch(15)),
    height=inch(17), plan_symbol="microwave", source=REFERENCE,
    needs=frozenset({Service.POWER_120}),
    ports=(ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))),),
)

STARTER_APPLIANCE_TYPES = (REFRIGERATOR, GAS_RANGE, ELECTRIC_RANGE, DISHWASHER, DRYER,
                           MICROWAVE_OTR)
