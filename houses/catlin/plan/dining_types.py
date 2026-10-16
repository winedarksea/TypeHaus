"""FURN-M-DINING: an ash top on bought metal legs, the catalog table's size and chair zone.

Only the top is milled: 1 1/2" off 8/4, glued up to 42" wide. The legs are a purchased
metal base, priced with the table in placeables.
"""

from __future__ import annotations

from typehaus.library.placeables.furniture import DINING_8_OPEN_CORNERS
from typehaus.model import FurnitureCut, inch

DINING_ASH = DINING_8_OPEN_CORNERS.model_copy(update=dict(
    tag="FT-CATLIN-DINING-ASH", name="Eight-seat dining table, ash top on metal legs",
    wood_material_ref="ash-8q",
    source="Owner-milled white ash top, hardwax oil; bought metal base. "
           + (DINING_8_OPEN_CORNERS.source or ""),
    cut_list=(FurnitureCut(part="dining table top", count=1, thickness=inch(1.5),
                           width=inch(42), length=inch(96)),),
))

DINING_TYPES = (DINING_ASH,)
