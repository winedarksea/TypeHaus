"""Installation choices independent of the factory door and sill cross-sections."""
from typing import Literal

from pydantic import Field, model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch


class ExteriorDoorInstallation(HausModel):
    mounting: Literal["structural_wall"] = "structural_wall"
    factory_frame_depth: Length | None = None
    return_thickness: Length = inch(0.75)
    casing_width: Length = inch(3.5)
    casing_thickness: Length = inch(0.75)
    exterior_material_ref: str = Field(default="kdat", min_length=1)
    interior_material_ref: str = Field(min_length=1)
    drainage_gap: Length = inch(0.5)
    # Limit the search across an intentional drainage gap, never across a missing landing.
    landing_search: Length = inch(6)
    maximum_landing_drop: Length = inch(7.75)

    @model_validator(mode="after")
    def positive_dimensions(self):
        dimensions = (self.return_thickness, self.casing_width, self.casing_thickness,
                      self.drainage_gap, self.landing_search, self.maximum_landing_drop)
        if any(value.meters <= 0 for value in dimensions):
            raise ValueError("door installation dimensions must be positive")
        if self.factory_frame_depth is not None and self.factory_frame_depth.meters <= 0:
            raise ValueError("factory frame depth must be positive")
        return self


register_constructor("ExteriorDoorInstallation", ExteriorDoorInstallation)
