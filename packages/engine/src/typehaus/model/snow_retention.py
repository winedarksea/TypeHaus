"""Authored extent and product choices for a provisional snow-retention row."""

import math
from typing import Literal

from pydantic import field_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length


class SnowRetentionSpec(HausModel):
    """A rail centred on its Connector; supports follow the host roof's seams.

    This describes hardware and coverage, not a load-based system design.
    """

    length: Length
    crossmember: Literal["ColorGard 2.0 Unpunched"] = "ColorGard 2.0 Unpunched"
    clamp: Literal["S-5-N"] = "S-5-N"
    attachment: Literal["VersaClip 2.0"] = "VersaClip 2.0"
    snow_clip: Literal["SnoClip 2.0 II"] | None = "SnoClip 2.0 II"

    @field_validator("length")
    @classmethod
    def positive_length(cls, value: Length) -> Length:
        if not math.isfinite(value.meters) or value.meters <= 0:
            raise ValueError("snow-retention length must be positive")
        return value


register_constructor("SnowRetentionSpec", SnowRetentionSpec)
