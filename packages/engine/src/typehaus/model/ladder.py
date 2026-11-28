"""A permanently affixed escape ladder (IRC R310.3.2.1 / R310.2.3.1 rung rules).

Rides on ``FurnitureType.ladder``: the type's W x D x H is the overall envelope (rails and
stand-off), the placeable is wall-hosted, and the rung geometry here is what the escape check
grades. Heights are above the ladder's base, which stands on the floor it climbs from.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch


class LadderSpec(HausModel):
    rung_inside_width: Length  # between rails; R310.3.2.1 wants >= 12"
    rung_projection: Length  # clear stand-off from the wall; R310.3.2.1 wants >= 3"
    rung_spacing: Length  # on centre, vertically; R310.3.2.1 wants <= 18"
    rung_count: int = Field(gt=0)
    first_rung_height: Length = inch(12)
    # How the user leaves the top: stepping sideways off the rail extension, or over the top.
    exit: Literal["side_step", "top"] = "side_step"
    rail_extension: Length = inch(14)  # rail above the top rung (the hand hold at the exit)
    rated_load_lb: float = Field(default=300.0, gt=0)

    @property
    def top_rung_height(self) -> Length:
        return self.first_rung_height + self.rung_spacing * (self.rung_count - 1)

    @model_validator(mode="after")
    def _envelope(self) -> LadderSpec:
        if self.rung_inside_width.meters <= 0 or self.rung_spacing.meters <= 0:
            raise ValueError("ladder rung width and spacing must be positive")
        return self


register_constructor("LadderSpec", LadderSpec)
