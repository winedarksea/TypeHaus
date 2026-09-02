"""Starter appliance catalog."""

from __future__ import annotations

from library.placeables._zones import front_zone
from typehaus.model import ApplianceType, Service, ServicePort, ft, inch

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
    quick_closing=True,  # solenoid fill valve — P2903.5 wants an arrestor on its supply
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

WASHER = ApplianceType(
    tag="APPL-WASHER", name="Clothes washer", footprint=(ft(2, 3), ft(2, 6)), height=ft(3),
    plan_symbol="washer", source=REFERENCE,
    quick_closing=True,  # solenoid fill valves on both supplies — P2903.5
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
    # The paragraph above, said in a field the code check can read. ``needs``
    # could only be silent about the exhaust, and silence is indistinguishable from an
    # oversight — code.M1502_dryer_exhaust read this product as a vented dryer missing its
    # duct. ``ductless=True`` is M1502.1's exemption stated outright.
    ductless=True,
    quick_closing=True,  # the washer half's solenoid fill valves — P2903.5
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

# A disposer is the one kitchen appliance nobody sees: it hangs off the sink's drain
# fitting inside the base cabinet, so it has no plan symbol and no clearance zone — the
# cabinet around it already owns that floor. What it does have is a load and a drain
# connection, and those are the two facts a panel schedule and a DFU count need from it.
#
# ``needs`` is POWER_120 + DRAIN and deliberately not WATER_COLD: a disposer takes no
# supply of its own. The flushing water is the sink's, through the sink's faucet, on the
# sink's stop — modelling a cold connection here would put a second supply branch in the
# base cabinet that no plumber will ever run.
DISPOSAL = ApplianceType(
    tag="APPL-DISPOSAL", name='Food waste disposer, 3/4 HP',
    # The unit is a ~7" cylinder hanging under the bowl; the footprint is its bounding
    # square at the widest point of the grind chamber, and the height is the body below
    # the mounting flange. Both are catalog nominals for the size class, not a purchase
    # commitment to one model.
    footprint=(inch(7), inch(7)), height=inch(12.5),
    plan_symbol=None, source=REFERENCE,
    needs=frozenset({Service.POWER_120, Service.DRAIN}),
    ports=(ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))),
           ServicePort(tag="drain", service=Service.DRAIN,
                       position=(ft(0), ft(0), inch(12.5)))),
)

STARTER_APPLIANCE_TYPES = (REFRIGERATOR, GAS_RANGE, ELECTRIC_RANGE, DISHWASHER, DRYER,
                           MICROWAVE_OTR, FREEZER_UPRIGHT, HOOD_RECIRC, WASHER,
                           WASHER_DRYER_STACKED, DISPOSAL)
