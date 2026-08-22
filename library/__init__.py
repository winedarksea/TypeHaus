"""Type:Haus shared library — the community contribution seam (→ 02 §Git topology).

Assemblies, materials, and types here are referenced by house plans via ``from library
import ...``. Each item is declarative wherever possible so the dialect trust claim holds.
"""

from __future__ import annotations

from library.assemblies import (
    FOUNDATION_WALL_8_INT,
    FOUNDATION_WALL_8_XPS4,
    FOUNDATION_WALL_8_XPS4_CORE,
    FOUNDATION_WALL_12_INT,
    FOUNDATION_WALL_12_XPS4,
    FOUNDATION_WALL_12_XPS4_CORE,
    GARAGE_ICF,
    HOUSE_ROOF,
    HOUSE_WALL_2X4_WITH_CI,
    HOUSE_WALL_2X6_WITH_ZIPR,
    INT_2X4_DOUBLE_STUD_MINERAL_WOOL,
    INT_2X4_PARTITION,
    INT_2X4_RC,
    INT_2X4_RC_DOUBLE_GWB,
    INT_2X4_STAGGERED_DOUBLE_GWB,
    STARTER_FLOOR,
)
from library.hardware import STRUCTURAL_HARDWARE
from library.materials import STARTER_MATERIALS
from library.placeables import (STARTER_APPLIANCE_TYPES, STARTER_CASEWORK_TYPES,
                                STARTER_FIXTURE_TYPES, STARTER_FURNITURE_TYPES)
from library.railings import STARTER_RAILING_TYPES

__all__ = [
    "STARTER_MATERIALS",
    "STRUCTURAL_HARDWARE",
    "HOUSE_WALL_2X4_WITH_CI",
    "HOUSE_WALL_2X6_WITH_ZIPR",
    "GARAGE_ICF",
    "FOUNDATION_WALL_8_INT",
    "FOUNDATION_WALL_12_INT",
    "FOUNDATION_WALL_8_XPS4",
    "FOUNDATION_WALL_12_XPS4",
    "FOUNDATION_WALL_8_XPS4_CORE",
    "FOUNDATION_WALL_12_XPS4_CORE",
    "HOUSE_ROOF",
    "INT_2X4_PARTITION",
    "INT_2X4_RC",
    "INT_2X4_RC_DOUBLE_GWB",
    "INT_2X4_STAGGERED_DOUBLE_GWB",
    "INT_2X4_DOUBLE_STUD_MINERAL_WOOL",
    "STARTER_FLOOR",
    "STARTER_FURNITURE_TYPES",
    "STARTER_CASEWORK_TYPES",
    "STARTER_APPLIANCE_TYPES",
    "STARTER_FIXTURE_TYPES",
    "STARTER_RAILING_TYPES",
]
