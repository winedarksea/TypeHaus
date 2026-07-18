# haus: editable
from library import (
    HOUSE_ROOF,
    HOUSE_WALL_2X6_WITH_ZIPR,
    INT_2X4_PARTITION,
    STARTER_MATERIALS,
)

# The starter house uses library assemblies directly (no local overrides yet).
MATERIALS = STARTER_MATERIALS
ASSEMBLIES = [HOUSE_WALL_2X6_WITH_ZIPR, HOUSE_ROOF, INT_2X4_PARTITION]
EXT_WALL = "HOUSE_WALL_2X6_WITH_ZIPR"
