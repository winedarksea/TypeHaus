# haus: editable
from library import (
    HOUSE_ROOF,
    HOUSE_WALL_2X6_WITH_ZIPR,
    INT_2X4_PARTITION,
    STARTER_MATERIALS,
)

# Library assemblies used directly: an exterior wall, an interior partition, a roof.
MATERIALS = STARTER_MATERIALS
ASSEMBLIES = [HOUSE_WALL_2X6_WITH_ZIPR, HOUSE_ROOF, INT_2X4_PARTITION]
EXT_WALL = "HOUSE_WALL_2X6_WITH_ZIPR"
