"""Horizontal FLEXX installation setout, separate from manufacturer cabinet facts.

Dimensions are coordination allowances until the shop pan, rail bearing and delivered
drain station are verified. The cabinet datum is its low front bearing edge.
"""

import math

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.quantities import Length, inch


class AirHandlerInstallation(HausModel):
    pan_width: Length = inch(49.5)
    pan_depth: Length = inch(27.25)
    pan_height: Length = inch(2)
    pan_sheet: Length = inch(0.0625)
    rail_height: Length = inch(3)
    rail_width: Length = inch(1.5)
    rail_wall: Length = inch(0.125)
    rail_centers: tuple[Length, ...] = (inch(-18), inch(18))
    cabinet_slope_in_per_ft: float = 0.125
    # East of both the cabinet and pan, preserving the front service rectangle.
    trap_inlet_x: Length = inch(27.25)
    trap_inlet_y: Length = inch(-14.6875)
    trap_leg_spacing: Length = inch(3)
    trap_outlet_drop: Length = inch(2)
    trap_seal_depth: Length = inch(3)
    pipe_outer_diameter: Length = inch(1.05)  # 3/4-inch Schedule 40 PVC
    pipe_wall: Length = inch(0.113)
    fitting_outer_diameter: Length = inch(1.375)  # reserved fitting envelope
    primary_elbow_offset: Length = inch(1.5)
    vent_rise_above_inlet: Length = inch(2.5)
    cleanout_rise_above_inlet: Length = inch(2.5)
    float_switch_x: Length = inch(-7.25)
    float_switch_inset: Length = inch(1)
    float_switch_width: Length = inch(1.6)
    float_switch_depth: Length = inch(1.58)
    float_switch_height: Length = inch(3.55)
    float_trip_depth: Length = inch(1)
    float_switch_product_ref: str
    source: str

    @model_validator(mode="after")
    def _positive_dimensions(self):
        signed = {"rail_centers", "trap_inlet_x", "trap_inlet_y", "float_switch_x"}
        for name in type(self).model_fields:
            value = getattr(self, name)
            if name not in signed and isinstance(value, Length) and value.meters <= 0:
                raise ValueError(f"{name} must be positive")
        if not self.rail_centers or self.cabinet_slope_in_per_ft < 0:
            raise ValueError("installation needs support rails and a nonnegative cabinet slope")
        if 2 * self.pipe_wall.meters >= self.pipe_outer_diameter.meters:
            raise ValueError("pipe wall leaves no open bore")
        if self.fitting_outer_diameter.meters < self.pipe_outer_diameter.meters:
            raise ValueError("fitting envelope cannot be smaller than the pipe")
        if 2 * self.rail_wall.meters >= min(self.rail_height.meters, self.rail_width.meters):
            raise ValueError("rail wall leaves no hollow section")
        if self.pan_sheet.meters >= self.pan_height.meters:
            raise ValueError("pan sheet leaves no usable depth")
        return self

    @property
    def cabinet_lift_in(self) -> float:
        return self.pan_sheet.inches + self.rail_height.inches

    @property
    def pitch_radians(self) -> float:
        return math.atan(self.cabinet_slope_in_per_ft / 12)

    def pitched_point_in(self, point, cabinet_depth_in=21.25):
        x, y, z = point
        front = -cabinet_depth_in / 2
        cosine, sine = math.cos(self.pitch_radians), math.sin(self.pitch_radians)
        return (x, front + (y - front) * cosine - z * sine,
                (y - front) * sine + z * cosine)

    def trap_outlet_in(self, primary_height_in: float):
        return (self.trap_inlet_x.inches,
                self.trap_inlet_y.inches - self.trap_leg_spacing.inches,
                primary_height_in - self.trap_outlet_drop.inches)
