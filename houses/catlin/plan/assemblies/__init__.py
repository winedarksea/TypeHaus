"""Catlin house assemblies — ported from catlin-house ifcplot (WP3.1).

Layer order is interior → exterior. The exterior wall family is one 2x6 stack on every
framed storey (sheathing / 4" closed-cell spray foam around a 2x4 truss / standing seam),
so the sheathing plane and every control layer are continuous with no stud-depth jog.

NOT # haus: editable: this only re-exports. The editable definitions live in the
sibling modules; the assembly editor adds to catalog.ASSEMBLIES and
materials.MATERIALS.
"""

from .catalog import (
    ASSEMBLIES,
    CONSTRUCTION_RULES,
)
from .envelope_masonry import (
    BASEMENT_BRICK_VENEER,
    BASEMENT_FIBER_CEMENT_SCREEN,
    FIREPLACE_BRICK_WYTHE,
)
from .envelope_roofs import (
    CANOPY_ROOF,
    GARAGE_ROOF,
    ROOF,
)
from .envelope_walls import (
    EXT_2X6,
    EXT_2X6_SWINBURNE,
    GARAGE_WALL_2X6,
    RAFTER_PLATE,
)
from .footings import (
    COURT_FOOTING_12,
    FOOTING_20,
    FOOTING_EXPOSED_20,
    PIER_BASE_12,
    PIER_CONCRETE_12,
)
from .foundation import (
    BASEMENT_8,
    BASEMENT_12,
    DECK_EPS_INT,
    GARAGE_ICF_6,
    GARAGE_ICF_CORE,
    GARAGE_ICF_EPS,
    SLAB_FLOOR,
)
from .interior import (
    ACCENT_GWB_LINING,
    INT_2X6_BRG_EXPOSED_PLY,
    SAUNA_2X4,
    SAUNA_2X6,
    SAUNA_LINER_INT_2X6_BRG,
    STAIRWALL_INT_2X6_BRG_TYPEX,
    STAIRWALL_INT_2X6_BRG_UNDERSTAIR,
    STAIRWELL_PARTITION_4H,
)
from .interior_wet import (
    PLANT_EXT_2X6_HUMID,
    PLANT_INT_2X4_HUMID,
    PLANT_INT_2X6_BRG_HUMID,
    TUBDECK_INT_2X4,
    TUBDECK_INT_PLY_CAP,
)
from .materials import (
    MATERIALS,
)
from .materials_ishtar import (
    MATERIALS_ISHTAR,
)
from .materials_metal import (
    MATERIALS_METAL,
)
from .members import (
    BEAM_WHITE_PAINT,
    ELM_TIMBER,
    EQUIP_STAND_ALUM,
    POST_WHITE_PAINT,
    POST_WHITE_PAINT_DF,
)
from .mixes import (
    BURIED_MIX,
    DECK_CAP_MIX,
    EXPOSED_MIX,
    INTERIOR_SLAB_MIX,
)
from .site import (
    ENTRY_STEP_TIER,
    GARAGE_STEP_6,
    GARDEN_COURT_SLAB,
    GARDEN_PUTTING_GREEN,
    GARDEN_STOOP,
    SG_VENEER_BEAM_14,
    SUNKEN_GARDEN_COLUMN_12,
    SUNKEN_GARDEN_GRADE_BEAM_12,
    SUNKEN_GARDEN_WALL,
    SUNKEN_GARDEN_WALL_DRAINED,
)
from .site_hardscape import (
    BALCONY_DECK_ALUMINUM,
    DRIVEWAY_FRC_CLASS5,
    ENTRY_SCREEN_SKIRT,
    ENTRY_SCREEN_WALL,
    GARAGE_SLAB_ON_GRADE,
    HP_PAD_ON_GRADE,
    PORCH_DECK_COMPOSITE,
    RAILING_DARK_METAL,
    RETAINING_BLOCK_12_WASHED,
    SIDEWALK_FRC_CLASS5,
)
from .walkout import (
    GARDEN_CURB_6,
    GARDEN_FRAMED_2X6,
    SAUNA_LINER_ON_GARDEN_CURB,
    SAUNA_LINER_ON_GARDEN_FRAMED,
)

__all__ = [
    "CONSTRUCTION_RULES",
    "ASSEMBLIES",
    "BASEMENT_BRICK_VENEER",
    "BASEMENT_FIBER_CEMENT_SCREEN",
    "FIREPLACE_BRICK_WYTHE",
    "ROOF",
    "GARAGE_ROOF",
    "CANOPY_ROOF",
    "EXT_2X6",
    "RAFTER_PLATE",
    "EXT_2X6_SWINBURNE",
    "GARAGE_WALL_2X6",
    "PIER_CONCRETE_12",
    "COURT_FOOTING_12",
    "FOOTING_20",
    "PIER_BASE_12",
    "FOOTING_EXPOSED_20",
    "BASEMENT_12",
    "BASEMENT_8",
    "SLAB_FLOOR",
    "DECK_EPS_INT",
    "GARAGE_ICF_EPS",
    "GARAGE_ICF_CORE",
    "GARAGE_ICF_6",
    "ACCENT_GWB_LINING",
    "SAUNA_2X4",
    "SAUNA_2X6",
    "SAUNA_LINER_INT_2X6_BRG",
    "INT_2X6_BRG_EXPOSED_PLY",
    "STAIRWALL_INT_2X6_BRG_UNDERSTAIR",
    "STAIRWALL_INT_2X6_BRG_TYPEX",
    "STAIRWELL_PARTITION_4H",
    "PLANT_EXT_2X6_HUMID",
    "PLANT_INT_2X6_BRG_HUMID",
    "PLANT_INT_2X4_HUMID",
    "TUBDECK_INT_2X4",
    "TUBDECK_INT_PLY_CAP",
    "MATERIALS",
    "MATERIALS_ISHTAR",
    "MATERIALS_METAL",
    "POST_WHITE_PAINT",
    "EQUIP_STAND_ALUM",
    "POST_WHITE_PAINT_DF",
    "ELM_TIMBER",
    "BEAM_WHITE_PAINT",
    "BURIED_MIX",
    "EXPOSED_MIX",
    "DECK_CAP_MIX",
    "INTERIOR_SLAB_MIX",
    "SUNKEN_GARDEN_WALL",
    "SUNKEN_GARDEN_WALL_DRAINED",
    "SUNKEN_GARDEN_GRADE_BEAM_12",
    "SG_VENEER_BEAM_14",
    "SUNKEN_GARDEN_COLUMN_12",
    "GARDEN_COURT_SLAB",
    "GARDEN_PUTTING_GREEN",
    "GARDEN_STOOP",
    "GARAGE_STEP_6",
    "ENTRY_STEP_TIER",
    "RETAINING_BLOCK_12_WASHED",
    "PORCH_DECK_COMPOSITE",
    "BALCONY_DECK_ALUMINUM",
    "ENTRY_SCREEN_WALL",
    "ENTRY_SCREEN_SKIRT",
    "RAILING_DARK_METAL",
    "GARAGE_SLAB_ON_GRADE",
    "HP_PAD_ON_GRADE",
    "SIDEWALK_FRC_CLASS5",
    "DRIVEWAY_FRC_CLASS5",
    "GARDEN_CURB_6",
    "SAUNA_LINER_ON_GARDEN_CURB",
    "GARDEN_FRAMED_2X6",
    "SAUNA_LINER_ON_GARDEN_FRAMED",
]
