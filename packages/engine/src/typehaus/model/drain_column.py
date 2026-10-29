"""A free-draining stone column against a foundation wall's soil face.

Not an element: it is the same excavation and the same order of stone as the bed it stands
beside, so it rides on ``FootingBedding.wall_column`` (→ ``resolve/wall_column.py``).
"""

from __future__ import annotations

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length


class DrainColumn(HausModel):
    """``width`` of washed stone square to the wall's exterior face, from the excavation
    floor beside the bed up to its top.

    The top is EITHER ``cap_below_grade`` under the strip grade the wall is backfilled
    against (the clayey cap then closes it), OR ``height`` above the bed top ``z1`` — the
    form a retaining wall's structural drainage is specified in. Exactly one is authored.
    """

    width: Length
    aggregate: str = "ASTM C33 #57 washed crushed stone"
    #: The library ``Material`` it draws and colours as (decision #57); ``aggregate`` bills.
    material_ref: str = "capillary-break-stone"
    cap_below_grade: Length | None = None
    height: Length | None = None
    #: Filter fabric on the soil side, folded over the top.
    geotextile: bool = True

    @model_validator(mode="after")
    def _one_top(self) -> DrainColumn:
        if (self.cap_below_grade is None) == (self.height is None):
            raise ValueError("DrainColumn needs exactly one of cap_below_grade and height")
        return self


register_constructor("DrainColumn", DrainColumn)
