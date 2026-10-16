"""A shop-built furniture type's cut list (→ takeoff/hardwood_furniture.py).

A table is not one board, so the closet-board path (``MillworkStandard.board_furniture_refs``)
cannot schedule it. A type that authors ``cut_list`` is owner-built: each part is cut to a
finished T x W x L from custom-milled stock, once per placed occurrence. Grain runs the
length. Pricing stays in placeables.
"""

from __future__ import annotations

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length


class FurnitureCut(HausModel):
    """One part of a shop-built piece: ``count`` boards at a finished size."""

    part: str
    count: int
    thickness: Length
    width: Length
    length: Length
    # The stock, when it is not the type's ``wood_material_ref`` (thick legs off 12/4).
    material_ref: str | None = None

    @model_validator(mode="after")
    def positive(self) -> FurnitureCut:
        if self.count < 1 or min(self.thickness.meters, self.width.meters,
                                 self.length.meters) <= 0:
            raise ValueError(f"cut {self.part!r}: count and sizes must be positive")
        return self


register_constructor("FurnitureCut", FurnitureCut)
