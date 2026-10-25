"""Installation choices independent of the factory door and sill cross-sections."""
from typing import Literal

from pydantic import Field, model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch


class ExteriorDoorSillDesign(HausModel):
    """Project coordination envelope; never a verified factory extrusion or support design."""
    source_url: str = Field(min_length=1)
    source_drawing: str = Field(min_length=1)
    threshold_depth: Length
    threshold_height: Length
    cap_depth: Length
    cap_height: Length = inch(0.25)
    threshold_nose_height: Length = inch(0.5)
    leaf_clearance: Length = inch(0.125)
    seat_height: Length = inch(0.5)
    approach_plate_thickness: Length = inch(0.25)
    nosing_thickness: Length = inch(0.0625)
    pan_projection: Length = inch(0.125)
    approach_minimum_height: Length = inch(0.75)
    approach_landing_step: Length = inch(0.25)
    drainage_clearance: Length = inch(0.125)
    side_clearance: Length = inch(0.125)
    bearing_strip_width: Length = inch(1.5)
    bearing_strip_spacing: Length = inch(8)
    approach_slope: float = Field(default=1 / 48, gt=0)
    approach_material_ref: str = "aluminum-extrusion"
    bearing_material_ref: str = "kdat"

    @model_validator(mode="after")
    def positive_dimensions(self):
        dimensions = (self.threshold_depth, self.threshold_height, self.cap_depth,
                      self.cap_height, self.threshold_nose_height, self.leaf_clearance,
                      self.seat_height, self.approach_plate_thickness,
                      self.nosing_thickness, self.pan_projection,
                      self.approach_minimum_height, self.approach_landing_step,
                      self.drainage_clearance, self.side_clearance, self.bearing_strip_width,
                      self.bearing_strip_spacing)
        if any(value.meters <= 0 for value in dimensions):
            raise ValueError("sill design dimensions must be positive")
        if self.cap_depth.meters >= self.threshold_depth.meters:
            raise ValueError("sill cap must be shallower than the threshold")
        if self.cap_height.meters + self.threshold_nose_height.meters >= \
                self.threshold_height.meters:
            raise ValueError("sill nose must be below the cap underside")
        if self.bearing_strip_width.meters >= self.bearing_strip_spacing.meters:
            raise ValueError("bearing strips must leave drainage channels")
        return self


class ExteriorDoorInstallation(HausModel):
    mounting: Literal["structural_wall"] = "structural_wall"
    factory_frame_depth: Length | None = None
    return_thickness: Length = inch(0.75)
    casing_width: Length = inch(3.5)
    casing_thickness: Length = inch(0.75)
    exterior_material_ref: str = Field(default="kdat", min_length=1)
    exterior_wrap_material_ref: str | None = None
    exterior_wrap_thickness: Length = inch(0.024)
    wrap_isolation_material_ref: str = "fluid-applied-flashing"
    wrap_isolation_thickness: Length = inch(0.020)
    sill_design: ExteriorDoorSillDesign | None = None
    interior_material_ref: str = Field(min_length=1)
    drainage_gap: Length = inch(0.5)
    # Limit the search across an intentional drainage gap, never across a missing landing.
    landing_search: Length = inch(6)
    maximum_landing_drop: Length = inch(7.75)

    @model_validator(mode="after")
    def positive_dimensions(self):
        dimensions = (self.return_thickness, self.casing_width, self.casing_thickness,
                      self.drainage_gap, self.landing_search, self.maximum_landing_drop,
                      self.exterior_wrap_thickness, self.wrap_isolation_thickness)
        if any(value.meters <= 0 for value in dimensions):
            raise ValueError("door installation dimensions must be positive")
        if self.factory_frame_depth is not None and self.factory_frame_depth.meters <= 0:
            raise ValueError("factory frame depth must be positive")
        return self


register_constructor("ExteriorDoorInstallation", ExteriorDoorInstallation)
register_constructor("ExteriorDoorSillDesign", ExteriorDoorSillDesign)
