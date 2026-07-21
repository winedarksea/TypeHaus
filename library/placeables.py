"""Small read-only starter catalog for plan-space studies and house prototypes."""

from typehaus.model import (ApplianceType, ClearancePolicy, ClearanceZone, Footprint2D,
                            FurnitureType, Service, ServicePort, ft, pt)


STANDARD_SOFA = FurnitureType(
    tag="FURN-SOFA-84", name="Standard sofa", footprint=(ft(7), ft(2, 11)), height=ft(2, 10),
)
QUEEN_BED = FurnitureType(
    tag="FURN-QUEEN-BED", name="Queen bed planning envelope", footprint=(ft(5, 4), ft(7)), height=ft(2),
)
SIX_SEAT_DINING_TABLE = FurnitureType(
    tag="FURN-DINING-6", name="Six-seat dining table", footprint=(ft(6), ft(3)), height=ft(2, 6),
    clearances=(ClearanceZone(
        footprint=Footprint2D(points=(pt(ft(-4), ft(-3)), pt(ft(4), ft(-3)),
                                      pt(ft(4), ft(3)), pt(ft(-4), ft(3)))),
        purpose="chair-use zone", policy=ClearancePolicy.RECOMMENDED, source="planning standard",
    ),),
)
WRITING_DESK = FurnitureType(
    tag="FURN-DESK-48", name="Writing desk", footprint=(ft(4), ft(2)), height=ft(2, 6),
)

REFRIGERATOR = ApplianceType(
    tag="APPL-REFRIGERATOR", name="Refrigerator", footprint=(ft(3), ft(2, 10)), height=ft(6),
    needs=frozenset({Service.POWER_120}),
    ports=(ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(2))),),
)
GAS_RANGE = ApplianceType(
    tag="APPL-GAS-RANGE", name="Gas range", footprint=(ft(2, 6), ft(2, 6)), height=ft(3),
    needs=frozenset({Service.GAS, Service.POWER_120}),
    ports=(ServicePort(tag="gas", service=Service.GAS, position=(ft(0), ft(0), ft(0))),
           ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0)))),
)
ELECTRIC_RANGE = ApplianceType(
    tag="APPL-ELECTRIC-RANGE", name="Electric range", footprint=(ft(2, 6), ft(2, 6)), height=ft(3),
    needs=frozenset({Service.POWER_240}),
    ports=(ServicePort(tag="power", service=Service.POWER_240, position=(ft(0), ft(0), ft(0))),),
)

STARTER_FURNITURE_TYPES = (STANDARD_SOFA, QUEEN_BED, SIX_SEAT_DINING_TABLE, WRITING_DESK)
STARTER_APPLIANCE_TYPES = (REFRIGERATOR, GAS_RANGE, ELECTRIC_RANGE)
