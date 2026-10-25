"""Purchased door hardware and the local framing that anchors it."""
from typing import Literal

from pydantic import Field, model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length

HARDWARE_BLOCKING_ANCHOR_ROLES = frozenset({
    "hinge", "passage", "deadbolt", "multipoint", "strike_reinforcement",
})


class DoorHardwareItem(HausModel):
    role: Literal["hinge", "passage", "deadbolt", "multipoint", "strike_reinforcement",
                  "viewer", "astragal", "fastener"]
    product_ref: str = Field(min_length=1)
    quantity: int = Field(default=1, gt=0)
    height: Length | None = None
    installation: str = Field(min_length=1)

    @model_validator(mode="after")
    def positive_height(self):
        if self.height is not None and self.height.meters <= 0:
            raise ValueError("hardware height must be above the leaf bottom")
        return self


class JambFraming(HausModel):
    kings: int = Field(ge=1)
    jacks: int = Field(ge=1)
    blocking: bool = False
    bay_fill_ref: str | None = Field(default=None, min_length=1)


for constructor in (DoorHardwareItem, JambFraming):
    register_constructor(constructor.__name__, constructor)
