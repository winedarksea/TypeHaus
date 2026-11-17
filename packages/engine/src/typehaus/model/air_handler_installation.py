"""Horizontal FLEXX installation setout, separate from manufacturer cabinet facts.

Every dimension is the house's selection: the engine ships no pan, rail or trap setout.
The cabinet datum is its low front bearing edge; points are cabinet-local inches.
"""

import math
from typing import NamedTuple

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.quantities import Length

Point = tuple[float, float, float]


class DrainFittings(HausModel):
    """One solvent-weld fitting line, read as centre-to-hub-end takeoffs."""

    pipe_outer_diameter: Length
    pipe_wall: Length
    hub_outer_diameter: Length
    adapter_projection: Length  # MPT x S adapter made up: cabinet face to hub end
    elbow_center_to_hub: Length  # 90 S x S
    tee_center_to_hub: Length  # tee S x S x S
    cap_length: Length
    cap_socket_depth: Length
    plug_projection: Length  # MPT plug flange beyond the face
    union_length: Length
    union_outer_diameter: Length
    source: str

    @model_validator(mode="after")
    def _sound(self):
        if 2 * self.pipe_wall.meters >= self.pipe_outer_diameter.meters:
            raise ValueError("pipe wall leaves no open bore")
        if min(self.hub_outer_diameter.meters,
               self.union_outer_diameter.meters) < self.pipe_outer_diameter.meters:
            raise ValueError("a fitting hub cannot be smaller than the pipe")
        if self.cap_socket_depth.meters >= self.cap_length.meters:
            raise ValueError("cap socket must be shallower than the cap")
        return self


class DrainSetout(NamedTuple):
    """Fitting centres of the primary feeder and trap, cabinet-local inches."""

    port: Point  # cabinet primary connection, on the pitched front face
    elbow: Point  # 90 turning the feeder along +x
    union: Point  # union centre on the sloped feeder
    inlet_tee: Point  # feeder enters its branch; cleanout up, trap leg down
    upper_bend: Point  # bottom 90 under the inlet leg
    lower_bend: Point  # bottom 90 under the outlet leg
    outlet_tee: Point  # vent up, outlet branch along -y (the routed drain)
    cleanout_top: Point  # pipe end inside the cap
    vent_top: Point  # open vent end


class AirHandlerInstallation(HausModel):
    pan_width: Length
    pan_depth: Length
    pan_height: Length
    pan_sheet: Length
    rail_height: Length
    rail_width: Length
    rail_wall: Length
    rail_centers: tuple[Length, ...]
    cabinet_slope_in_per_ft: float
    #: Feeder slope, adapter to inlet tee; IMC 307.2.1 sets its floor.
    feeder_slope_in_per_ft: float
    #: Cabinet face to the first elbow's centre, along -y.
    primary_elbow_offset: Length
    #: The inlet tee's x; the feeder runs from the port's x to here.
    trap_inlet_x: Length
    trap_leg_spacing: Length
    trap_outlet_drop: Length
    trap_seal_depth: Length  # outlet centreline to bottom centreline
    vent_rise_above_inlet: Length
    cleanout_rise_above_inlet: Length
    float_switch_x: Length
    float_switch_inset: Length
    float_switch_width: Length
    float_switch_depth: Length
    float_switch_height: Length
    float_trip_depth: Length
    fittings: DrainFittings
    float_switch_product_ref: str
    source: str

    @model_validator(mode="after")
    def _positive_dimensions(self):
        signed = {"rail_centers", "trap_inlet_x", "float_switch_x"}
        for name in type(self).model_fields:
            value = getattr(self, name)
            if name not in signed and isinstance(value, Length) and value.meters <= 0:
                raise ValueError(f"{name} must be positive")
        if (not self.rail_centers or self.cabinet_slope_in_per_ft < 0
                or self.feeder_slope_in_per_ft < 0):
            raise ValueError("installation needs support rails and nonnegative slopes")
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

    def drain_setout(self, port: Point) -> DrainSetout:
        """Adapter, 90, union, inlet tee, two-90 trap and outlet tee from ``port``."""
        x, y, z = port
        fall = self.feeder_slope_in_per_ft / 12
        offset = self.primary_elbow_offset.inches
        elbow = (x, y - offset, z - fall * offset)
        run = self.trap_inlet_x.inches - x
        tee = (x + run, elbow[1], elbow[2] - fall * run)
        union = ((elbow[0] + tee[0]) / 2, elbow[1], (elbow[2] + tee[2]) / 2)
        outlet_z = tee[2] - self.trap_outlet_drop.inches
        bottom = outlet_z - self.trap_seal_depth.inches
        outlet_y = tee[1] - self.trap_leg_spacing.inches
        return DrainSetout(
            port=port, elbow=elbow, union=union, inlet_tee=tee,
            upper_bend=(tee[0], tee[1], bottom), lower_bend=(tee[0], outlet_y, bottom),
            outlet_tee=(tee[0], outlet_y, outlet_z),
            cleanout_top=(*tee[:2], tee[2] + self.cleanout_rise_above_inlet.inches),
            vent_top=(tee[0], outlet_y, tee[2] + self.vent_rise_above_inlet.inches))
