"""Starter appliance catalog.

``APPL-WASHER`` used to live only in ``houses/catlin/plan/fixture_types.py`` — a shared
appliance kept house-local, so this catalog shipped a dryer with no washer beside it.
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

# A second cold box beside the refrigerator, for a household that buys and freezes in bulk.
# Same 3' door zone as the fridge: an upright freezer's door is the full face of the cabinet.
FREEZER_UPRIGHT = ApplianceType(
    tag="APPL-FREEZER-UPRIGHT", name="Upright freezer", footprint=(ft(3), ft(2, 10)),
    height=ft(6), plan_symbol="refrigerator", source=REFERENCE,
    needs=frozenset({Service.POWER_120}),
    ports=(ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(2))),),
    clearances=(front_zone(ft(3), ft(2, 10), ft(3), "freezer door swing"),),
)
# Recirculating by design, not by omission: a fully electric house with an induction cooktop
# has no combustion products to exhaust, and a ducted hood would punch the airtight envelope
# for a load the ERV already carries. Hence no duct service — only its circuit is declared.
HOOD_RECIRC = ApplianceType(
    tag="APPL-HOOD-RECIRC", name="Recirculating canopy hood", footprint=(inch(30), inch(20)),
    height=inch(18), plan_symbol="hood", source=REFERENCE,
    needs=frozenset({Service.POWER_120}),
    ports=(ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))),),
)

# The library shipped a dryer but no washer, so every house had to author its own — the
# one asymmetry in this catalog.
WASHER = ApplianceType(
    tag="APPL-WASHER", name="Clothes washer", footprint=(ft(2, 3), ft(2, 6)), height=ft(3),
    plan_symbol="washer", source=REFERENCE,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN, Service.POWER_240}),
)

# One object, two machines. A stack is not a washer with a dryer placed on top of it — it is
# a single 80"-tall tower with one footprint, one clearance zone and one set of anchors, and
# a laundry closet is sized against that tower rather than against either machine. Modelling
# it as two placeables would put a body inside a body and give the room two door zones where
# it has one.
#
# The dryer half is a *ventless heat pump*, which is what the ``needs`` set says and does not
# say: no exhaust, so the standing caveat on ``DRYER`` above — that a dryer's duct has no
# ``Service`` member — simply does not apply here. There is no duct to declare, no wall or
# roof penetration, and the moisture leaves as condensate down a drain instead of as air
# through a hood. It carries both power services because the two machines are on separate
# branch circuits (120V for the washer, 240V for the dryer) even though they read as one
# appliance.
WASHER_DRYER_STACKED = ApplianceType(
    tag="APPL-WASHER-DRYER-STACKED", name="Stacked washer / heat-pump dryer",
    footprint=(inch(28), inch(40)), height=inch(80),
    plan_symbol="washer-dryer-stacked", source=REFERENCE,
    # The paragraph above, said in a field the code check can read (2026-08-01). ``needs``
    # could only be silent about the exhaust, and silence is indistinguishable from an
    # oversight — code.M1502_dryer_exhaust read this product as a vented dryer missing its
    # duct. ``ductless=True`` is M1502.1's exemption stated outright.
    ductless=True,
    needs=frozenset({Service.WATER_HOT, Service.WATER_COLD, Service.DRAIN,
                     Service.POWER_120, Service.POWER_240}),
    ports=(ServicePort(tag="power-washer", service=Service.POWER_120,
                       position=(ft(0), ft(0), ft(0))),
           ServicePort(tag="power-dryer", service=Service.POWER_240,
                       position=(ft(0), ft(0), inch(43))),
           ServicePort(tag="supply-hot", service=Service.WATER_HOT,
                       position=(ft(0), ft(0), inch(36))),
           ServicePort(tag="supply-cold", service=Service.WATER_COLD,
                       position=(ft(0), ft(0), inch(36))),
           # The washer's discharge and the dryer's condensate both leave at the standpipe
           # band; neither is a sealed connection (see the air-gap notes on the instance).
           ServicePort(tag="drain", service=Service.DRAIN,
                       position=(ft(0), ft(0), inch(36)))),
    # Front-loaders swing a full-diameter door: 30" is the band a user needs to load the
    # lower machine, and it is RECOMMENDED so a laundry *closet* — where that band is the
    # doorway you stand in — still builds.
    clearances=(front_zone(inch(28), inch(40), inch(30),
                           "front-loader door swing and loading"),),
)

STARTER_APPLIANCE_TYPES = (REFRIGERATOR, GAS_RANGE, ELECTRIC_RANGE, DISHWASHER, DRYER,
                           MICROWAVE_OTR, FREEZER_UPRIGHT, HOOD_RECIRC, WASHER,
                           WASHER_DRYER_STACKED)
