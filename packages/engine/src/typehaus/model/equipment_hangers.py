"""A hung machine's trapeze: two strut channels under the case on threaded rod.

Authored on ``Equipment.hangers``; the geometry is derived (``resolve/equipment_hangers.py``):
rods at the case's short-side corners, each struts' length the case's short side plus
``overhang`` at each end, and every rod's drop from the framing overhead to the strut top.
Each rod's top fixing is a strut bridge across the two joists either side of it, lagged up
into their bottom flanges. Graded by ``structural.equipment_hangers``.
"""

from __future__ import annotations

from pydantic import Field, field_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch


class EquipmentHangers(HausModel):
    """A strut trapeze: ``count`` rods, two per strut, one bridge per rod. The struts stand
    at the two short sides, any more evenly between them."""

    count: int = Field(default=4, ge=4)
    #: Product tags; a rating is read off ``Product.rated_load_lb``.
    rod_product_ref: str
    strut_product_ref: str
    #: The fastener lagging each bridge end into a joist's bottom flange.
    top_fixing_product_ref: str
    #: Strut past the case face at each end; the rod stands at its middle.
    overhang: Length = inch(2)
    source: str = ""

    @field_validator("count")
    @classmethod
    def _two_per_strut(cls, value: int) -> int:
        if value % 2:
            raise ValueError("EquipmentHangers.count must be even: two rods per strut")
        return value


register_constructor("EquipmentHangers", EquipmentHangers)
