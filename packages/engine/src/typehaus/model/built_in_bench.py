"""Fabrication and fit inputs for an independently supported upholstered booth bench."""
from __future__ import annotations

import math
from typing import Literal

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch

BENCH_ENVELOPE_TOLERANCE_M = .0001


class BuiltInBenchSpec(HausModel):
    width: Length
    effective_seat_depth: Length
    deck_height: Length
    back_height: Length
    panel_thickness: Length
    seat_cushion_thickness: Length
    back_pad_thickness: Length
    lumbar_projection: Length
    lumbar_height_above_seat: Length
    occupied_seat_height: Length
    back_angle_degrees: float
    toe_height: Length
    toe_recess: Length
    cap_thickness: Length
    carcass_material_ref: str
    front_material_ref: str
    trim_material_ref: str
    upholstery_material_ref: str
    front_stock_kind: Literal["panel", "solid wood"] = "panel"
    internal_partition_count: int = 2
    seat_foam_density_lb_ft3: float = 2.5
    seat_foam_ifd_min_lbf: float = 35
    seat_foam_ifd_max_lbf: float = 45
    lumbar_adjustment_min: Length = inch(6)
    lumbar_adjustment_max: Length = inch(9)
    front_roundover_radius: Length = inch(.25)
    cushion_front_radius: Length = inch(1)

    @model_validator(mode="after")
    def _validate_construction(self) -> BuiltInBenchSpec:
        for name, value in self.__dict__.items():
            if isinstance(value, Length) and value.meters <= 0:
                raise ValueError(f"bench {name} must be positive")
        if not 90 < self.back_angle_degrees <= 110:
            raise ValueError("bench back angle must be above 90 and at most 110 degrees")
        if self.internal_partition_count < 1:
            raise ValueError("bench needs internal seat supports")
        if self.width.meters <= (self.internal_partition_count + 2) * self.panel_thickness.meters:
            raise ValueError("bench width must exceed its support thicknesses")
        if not (self.toe_height.meters < self.deck_height.meters - self.panel_thickness.meters
                and self.deck_height.meters + self.seat_cushion_thickness.meters
                < self.back_height.meters - self.cap_thickness.meters):
            raise ValueError("bench toe, deck, cushion and cap elevations must be ordered")
        if not (self.deck_height.meters < self.occupied_seat_height.meters
                < self.deck_height.meters + self.seat_cushion_thickness.meters):
            raise ValueError("occupied seat must lie within the unloaded cushion")
        if not (self.lumbar_adjustment_min.meters <= self.lumbar_height_above_seat.meters
                <= self.lumbar_adjustment_max.meters):
            raise ValueError("lumbar center must lie within its adjustment range")
        if not (self.deck_height.meters + self.seat_cushion_thickness.meters
                < self.lumbar_elevation
                < self.back_height.meters - self.cap_thickness.meters):
            raise ValueError("lumbar center must lie within the back pad")
        if not (0 < self.seat_foam_ifd_min_lbf <= self.seat_foam_ifd_max_lbf
                and self.seat_foam_density_lb_ft3 > 0):
            raise ValueError("foam density and ordered IFD range must be positive")
        if self.cushion_front_radius.meters >= self.seat_cushion_thickness.meters / 2:
            raise ValueError("cushion front radius must be less than half its thickness")
        if self.toe_recess.meters >= self.effective_seat_depth.meters:
            raise ValueError("toe recess must lie inside the bench")
        deck_depth = (self.overall_depth_m + self.back_front_y(self.deck_height.meters)
                      - self.panel_thickness.meters)
        cushion_depth = (self.overall_depth_m + self.back_front_y(
            self.deck_height.meters + self.seat_cushion_thickness.meters)
            - self.back_pad_thickness.meters / math.cos(self.recline_radians))
        if deck_depth <= 0 or cushion_depth <= 2 * self.cushion_front_radius.meters:
            raise ValueError("bench depth must accommodate the deck and cushion nose")
        return self

    @property
    def recline_radians(self) -> float:
        return math.radians(self.back_angle_degrees - 90)

    @property
    def lumbar_elevation(self) -> float:
        return self.occupied_seat_height.meters + self.lumbar_height_above_seat.meters

    def back_front_y(self, elevation: float) -> float:
        """Front of plywood at z; rear of cap is the temporary y=0 datum."""
        return ((elevation - self.back_height.meters + self.cap_thickness.meters)
                * math.tan(self.recline_radians)
                - self.panel_thickness.meters / math.cos(self.recline_radians))

    @property
    def overall_depth_m(self) -> float:
        lumbar_y = (self.back_front_y(self.lumbar_elevation)
                    - self.back_pad_thickness.meters / math.cos(self.recline_radians)
                    - self.lumbar_projection.meters)
        return self.effective_seat_depth.meters - lumbar_y

    @property
    def material_refs(self) -> tuple[str, ...]:
        return (self.carcass_material_ref, self.front_material_ref,
                self.trim_material_ref, self.upholstery_material_ref)


register_constructor("BuiltInBenchSpec", BuiltInBenchSpec)
