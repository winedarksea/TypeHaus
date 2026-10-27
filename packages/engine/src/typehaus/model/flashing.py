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

    ``ventilated_hood`` uses the underside of the crown as ``top_elevation``;
    slope falls to both sides. Its straight path points from the exposed end
    towards ``roof_ref``; ``host_ref`` names that roof's supporting beam.
    """

    profile: Literal["drip", "counter", "cap", "ventilated_hood"] = "drip"
    sheet_thickness: Length = inch(0.032)
    slope: float = Field(default=0.0, ge=0, allow_inf_nan=False)
    upstand: Length = inch(3)
    drip: Length = inch(0.75)
    hem: Length = inch(0.25)
    #: A SlatBrace host: resolve its sill top and cut around its wood and hardware.
    fit_to_brace_sill: bool = False
    #: Ventilated hood: path runs from exposed end towards the referenced roof.
    roof_ref: str | None = None
    air_gap: Length = inch(0.5)
    end_drop: Length = inch(1.25)
    end_hem: Length = inch(0.125)
    apron_gap: Length = inch(0.5)
    apron_lap: Length = inch(1)
    apron_drip_clearance: Length = inch(0.125)

    @model_validator(mode="after")
    def valid_section(self):
        if self.fit_to_brace_sill and self.profile != "cap":
            raise ValueError("a fitted brace sill requires a cap section")
        if self.sheet_thickness.meters <= 0:
            raise ValueError("flashing sheet thickness must be positive")
        if any(value.meters < 0 for value in (self.upstand, self.drip, self.hem)):
            raise ValueError("flashing legs must not be negative")
        if self.profile == "ventilated_hood":
            if not self.roof_ref or self.slope <= 0:
                raise ValueError("a ventilated hood requires a roof_ref and positive crown slope")
            if self.air_gap.inches < 0.5:
                raise ValueError("a ventilated hood requires at least 1/2 inch air space")
            if any(value.meters <= 0 for value in (
                    self.end_drop, self.end_hem, self.apron_gap, self.apron_lap,
                    self.apron_drip_clearance, self.upstand, self.drip, self.hem)):
                raise ValueError("ventilated hood returns and apron dimensions must be positive")
            if self.upstand.meters <= self.apron_drip_clearance.meters:
                raise ValueError("hood upstand must overlap the apron drip")
        return self


register_constructor("FormedFlashingSection", FormedFlashingSection)
