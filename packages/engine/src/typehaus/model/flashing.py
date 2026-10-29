"""Optional formed-sheet geometry for authored flashing runs."""

from typing import Literal

from pydantic import Field, model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch


class FormedFlashingSection(HausModel):
    """Across-run dimensions, measured from inboard to outboard (``back_side``).

    The run's ``thickness`` is its overall width; ``top_elevation`` is the inboard
    underside. A positive slope falls outboard. ``cap`` adds an inboard downstand;
    ``counter`` turns the inboard leg upward instead.
    """

    profile: Literal["drip", "counter", "cap"] = "drip"
    sheet_thickness: Length = inch(0.032)
    slope: float = Field(default=0.0, ge=0, allow_inf_nan=False)
    upstand: Length = inch(3)
    drip: Length = inch(0.75)
    hem: Length = inch(0.25)
    #: A SlatBrace host: resolve its sill top and cut around its wood and hardware.
    fit_to_brace_sill: bool = False

    @model_validator(mode="after")
    def valid_section(self):
        if self.fit_to_brace_sill and self.profile != "cap":
            raise ValueError("a fitted brace sill requires a cap section")
        if self.sheet_thickness.meters <= 0:
            raise ValueError("flashing sheet thickness must be positive")
        if any(value.meters < 0 for value in (self.upstand, self.drip, self.hem)):
            raise ValueError("flashing legs must not be negative")
        return self


register_constructor("FormedFlashingSection", FormedFlashingSection)
