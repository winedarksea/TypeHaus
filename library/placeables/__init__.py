"""Small read-only starter catalog for plan-space studies and house prototypes.

Split into one module per domain once the catalog outgrew a single file; this package
re-exports every name the original ``library/placeables.py`` published, so existing import
sites keep working unchanged.
"""

from __future__ import annotations

from library.placeables.appliances import (DISHWASHER, DRYER, ELECTRIC_RANGE,
                                           FREEZER_UPRIGHT, GAS_RANGE, HOOD_RECIRC,
                                           MICROWAVE_OTR, REFRIGERATOR,
                                           STARTER_APPLIANCE_TYPES, WASHER)
from library.placeables.casework import (BAR_STOOL, BASE_15, BASE_24, BASE_30, BASE_36,
                                         ISLAND_60, OVER_APPLIANCE_36, PANTRY_CLOSET_24,
                                         PANTRY_CLOSET_48, PANTRY_CLOSET_72,
                                         BESTA_UNIT, SINK_BASE_36,
                                         STARTER_CASEWORK_TYPES, TALL_PANTRY_12,
                                         TALL_PANTRY_18, WALL_18, WALL_24, WALL_30, WALL_66)
from library.placeables.fixtures import (KITCHEN_SINK, LAVATORY, LAVATORY_COMPACT,
                                         SHOWER, STARTER_FIXTURE_TYPES, TOILET,
                                         TOILET_WALL_HUNG, TUB, TUB_SHOWER, VANITY,
                                         WALL_HYDRANT)
from library.placeables.furniture import (ARMCHAIR, BOOKCASE, CHEST, COFFEE_TABLE, DESK_CHAIR,
                                          DINING_CHAIR, DRESSER, EIGHT_SEAT_DINING_TABLE,
                                          END_TABLE, FULL_BED, KING_BED, LOVESEAT,
                                          MEDIA_CONSOLE, NIGHTSTAND, OFFICE_CHAIR, QUEEN_BED,
                                          ROUND_DINING_TABLE, SAUNA_BENCH_54,
                                          SAUNA_BENCH_TIERED_102, SECTIONAL,
                                          SIX_SEAT_DINING_TABLE, STANDARD_SOFA,
                                          MUDROOM_BENCH_36, STARTER_FURNITURE_TYPES,
                                          TV_65, TV_98, TWIN_BED, WORKBENCH_60,
                                          WRITING_DESK)

__all__ = [
    "STARTER_FURNITURE_TYPES", "STARTER_APPLIANCE_TYPES", "STARTER_FIXTURE_TYPES",
    "STARTER_CASEWORK_TYPES",
    # furniture
    "STANDARD_SOFA", "LOVESEAT", "SECTIONAL", "ARMCHAIR", "COFFEE_TABLE", "END_TABLE",
    "MEDIA_CONSOLE", "TV_65", "TV_98", "QUEEN_BED", "KING_BED", "FULL_BED", "TWIN_BED",
    "DRESSER", "CHEST", "NIGHTSTAND", "SIX_SEAT_DINING_TABLE", "EIGHT_SEAT_DINING_TABLE",
    "ROUND_DINING_TABLE", "DINING_CHAIR", "WRITING_DESK", "OFFICE_CHAIR", "DESK_CHAIR",
    "SAUNA_BENCH_TIERED_102", "SAUNA_BENCH_54", "WORKBENCH_60", "MUDROOM_BENCH_36",
    # casework
    "BESTA_UNIT", "BASE_15", "BASE_24", "BASE_30", "BASE_36", "SINK_BASE_36",
    "WALL_18", "WALL_24", "WALL_30", "WALL_66",
    "OVER_APPLIANCE_36", "TALL_PANTRY_12", "TALL_PANTRY_18", "PANTRY_CLOSET_24",
    "PANTRY_CLOSET_48", "PANTRY_CLOSET_72", "ISLAND_60", "BAR_STOOL",
    # appliances
    "REFRIGERATOR", "GAS_RANGE", "ELECTRIC_RANGE", "DISHWASHER", "DRYER", "MICROWAVE_OTR",
    "FREEZER_UPRIGHT", "HOOD_RECIRC", "WASHER",
    # plumbing fixtures
    "TOILET", "LAVATORY", "VANITY", "TUB", "TUB_SHOWER", "SHOWER", "KITCHEN_SINK",
    "TOILET_WALL_HUNG", "LAVATORY_COMPACT", "WALL_HYDRANT",
]
