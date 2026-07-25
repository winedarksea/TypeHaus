# haus: editable
from library import (
    HOUSE_ROOF,
    HOUSE_WALL_2X4_WITH_CI,
    HOUSE_WALL_2X6_WITH_ZIPR,
    INT_2X4_PARTITION,
    STARTER_MATERIALS,
)

# The starter house uses library assemblies directly (no local overrides yet).
# HOUSE_WALL_2X4_WITH_CI is carried but unused: it is the alternative the "2x4-ci" variant
# (variants.toml) selects, and a swap can only reference an assembly the plan library holds.
MATERIALS = STARTER_MATERIALS
ASSEMBLIES = [HOUSE_WALL_2X6_WITH_ZIPR, HOUSE_WALL_2X4_WITH_CI, HOUSE_ROOF,
              INT_2X4_PARTITION]
EXT_WALL = "HOUSE_WALL_2X6_WITH_ZIPR"
