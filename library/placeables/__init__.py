"""Small read-only starter catalog for plan-space studies and house prototypes.

Split into one module per domain once the catalog outgrew a single file; this package
re-exports every name the original ``library/placeables.py`` published, so existing import
sites keep working unchanged.
"""

from __future__ import annotations

from library.placeables.appliances import (DISHWASHER, DRYER, ELECTRIC_RANGE, GAS_RANGE,
                                           MICROWAVE_OTR, REFRIGERATOR,
                                           STARTER_APPLIANCE_TYPES)
from library.placeables.fixtures import (KITCHEN_SINK, LAVATORY, SHOWER,
                                         STARTER_FIXTURE_TYPES, TOILET, TUB, VANITY)
from library.placeables.furniture import (ARMCHAIR, BOOKCASE, CHEST, COFFEE_TABLE,
                                          DINING_CHAIR, DRESSER, END_TABLE, FULL_BED,
                                          KING_BED, LOVESEAT, MEDIA_CONSOLE, NIGHTSTAND,
                                          OFFICE_CHAIR, QUEEN_BED, ROUND_DINING_TABLE,
                                          SECTIONAL, SIX_SEAT_DINING_TABLE, STANDARD_SOFA,
                                          STARTER_FURNITURE_TYPES, TV_65, TV_98, TWIN_BED,
                                          WRITING_DESK)

__all__ = [
    "STARTER_FURNITURE_TYPES", "STARTER_APPLIANCE_TYPES", "STARTER_FIXTURE_TYPES",
    # furniture
    "STANDARD_SOFA", "LOVESEAT", "SECTIONAL", "ARMCHAIR", "COFFEE_TABLE", "END_TABLE",
    "MEDIA_CONSOLE", "TV_65", "TV_98", "QUEEN_BED", "KING_BED", "FULL_BED", "TWIN_BED",
    "DRESSER", "CHEST", "NIGHTSTAND", "SIX_SEAT_DINING_TABLE", "ROUND_DINING_TABLE",
    "DINING_CHAIR", "WRITING_DESK", "OFFICE_CHAIR", "BOOKCASE",
    # appliances
    "REFRIGERATOR", "GAS_RANGE", "ELECTRIC_RANGE", "DISHWASHER", "DRYER", "MICROWAVE_OTR",
    # plumbing fixtures
    "TOILET", "LAVATORY", "VANITY", "TUB", "SHOWER", "KITCHEN_SINK",
]
