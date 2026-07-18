"""Type:Haus shared library — the community contribution seam (→ 02 §Git topology).

Assemblies, materials, and types here are referenced by house plans via ``from library
import ...``. Each item is declarative wherever possible so the dialect trust claim holds.
"""

from __future__ import annotations

from library.assemblies import (
    GARAGE_ICF,
    HOUSE_ROOF,
    HOUSE_WALL_2X4_WITH_CI,
    HOUSE_WALL_2X6_WITH_ZIPR,
    INT_2X4_PARTITION,
    STARTER_FLOOR,
)
from library.materials import STARTER_MATERIALS

__all__ = [
    "STARTER_MATERIALS",
    "HOUSE_WALL_2X4_WITH_CI",
    "HOUSE_WALL_2X6_WITH_ZIPR",
    "GARAGE_ICF",
    "HOUSE_ROOF",
    "INT_2X4_PARTITION",
    "STARTER_FLOOR",
]
