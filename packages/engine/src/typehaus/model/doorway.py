"""Product sections and installation contracts for doorway bottoms.

Coordinates are metres in a section looking along the opening: x is wall normal,
with its positive direction explicitly installed below, and z is above the datum.
A product name without an approved section remains a documented unresolved selection.
"""
from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from typehaus.model.base import HausModel
from typehaus.model.exterior_door import ExteriorDoorInstallation
from typehaus.model.registry import register_constructor


class DoorwaySectionPart(HausModel):
    name: str = Field(min_length=1)
    material_ref: str = Field(min_length=1)
    polygon_m: tuple[tuple[float, float], ...]
    material_key: Literal["door_hardware", "door_frame", "shadow_gap"] = "door_hardware"

    @model_validator(mode="after")
    def valid_polygon(self):
        from shapely.geometry import Polygon

        if (len(self.polygon_m) < 3
                or not all(math.isfinite(v) for p in self.polygon_m for v in p)):
            raise ValueError("section requires at least three finite points")
        polygon = Polygon(self.polygon_m)
        if not polygon.is_valid or polygon.area <= 0:
            raise ValueError("section must be a simple polygon with positive area")
        return self


class DoorwayProductSpec(HausModel):
    product_ref: str = Field(min_length=1)
    variant: str = Field(min_length=1)
    role: Literal["sill", "track", "guide", "bottom_seal", "transition"]
    source_url: str = Field(min_length=1)
    source_drawing: str = Field(min_length=1)
    installation: str = Field(min_length=1)
    parts: tuple[DoorwaySectionPart, ...] = ()
    # Legacy complete-section flag; order confirmation is tracked independently below.
    verified: bool = False
    # A documented design selection can be modeled before the purchase is confirmed.
    section_documented: bool = False
    supplier_confirmed: bool = False
    datum: Literal["rough_opening", "lower_floor", "higher_floor"] = "rough_opening"
    elevation_offset_m: float = 0.0
    normal_offset_m: float = 0.0
    positive_normal_sign: Literal[-1, 1] = 1
    minimum_floor_difference_m: float = Field(default=0.0, ge=0)
    maximum_floor_difference_m: float | None = Field(default=None, ge=0)
    compatible_finish_pairs: tuple[tuple[str, str], ...] = ()
    expansion_gap_m: tuple[float, float] = (0.0, 0.0)
    purchase: Literal["separate", "factory_included", "kit_included"] = "factory_included"
    # Guides/seals occupy only their documented width; sills/tracks span the opening.
    span_m: float | None = Field(default=None, gt=0)
    along_offset_m: float = 0.0
    leaf_clearance_m: float = Field(default=0.0, ge=0)
    # Published termination elevations above the section origin.
    leaf_bottom_m: float | None = None
    jamb_bottom_m: float | None = None
    # Which side of the section (before installed normal sign) serves the higher floor.
    higher_floor_side: Literal[-1, 1] | None = None
    # Finished-floor contact planes at negative/positive section sides, above the section origin.
    floor_contact_heights_m: tuple[float, float] | None = None
    # Actual finish stops before expansion gaps; cap wings may overlap the flooring.
    floor_finish_edges_m: tuple[float, float] | None = None
    # Documented underside bearing locations in section coordinates, swept across the span.
    bearing_points_m: tuple[tuple[float, float], ...] = ()

    @model_validator(mode="after")
    def valid_installation(self):
        if (self.maximum_floor_difference_m is not None
                and self.maximum_floor_difference_m < self.minimum_floor_difference_m):
            raise ValueError("floor-height range is reversed")
        numbers = (self.elevation_offset_m, self.normal_offset_m, self.along_offset_m,
                   self.minimum_floor_difference_m,
                   self.leaf_clearance_m, *self.expansion_gap_m)
        if not all(math.isfinite(v) for v in numbers) or min(self.expansion_gap_m) < 0:
            raise ValueError("installation dimensions must be finite; gaps must be nonnegative")
        if any(v is not None and not math.isfinite(v)
               for v in (self.leaf_bottom_m, self.jamb_bottom_m, self.maximum_floor_difference_m,
                         self.span_m)):
            raise ValueError("termination elevations must be finite")
        if self.floor_contact_heights_m is not None and not all(
                math.isfinite(v) for v in self.floor_contact_heights_m):
            raise ValueError("floor contact heights must be finite")
        if self.floor_finish_edges_m is not None and (
                not all(math.isfinite(v) for v in self.floor_finish_edges_m)
                or self.floor_finish_edges_m[1] < self.floor_finish_edges_m[0]):
            raise ValueError("floor finish edges must be finite and ordered")
        if not all(math.isfinite(v) for point in self.bearing_points_m for v in point):
            raise ValueError("bearing points must be finite")
        if len({part.name for part in self.parts}) != len(self.parts):
            raise ValueError("section part names must be unique")
        if (self.verified or self.section_documented) and not self.parts:
            raise ValueError("verified product requires a sourced cross-section")
        if (self.role in ("guide", "bottom_seal") and (self.verified or self.section_documented)
                and self.span_m is None):
            raise ValueError("guide/seal requires a documented span")
        return self


class DoorwayTreatment(HausModel):
    floor_treatment: Literal["auto", "continuous", "transition"] = "auto"
    threshold: DoorwayProductSpec | None = None
    transition: DoorwayProductSpec | None = None
    exterior_installation: ExteriorDoorInstallation | None = None

    @model_validator(mode="after")
    def valid_roles(self):
        if self.threshold and self.threshold.role == "transition":
            raise ValueError("threshold must describe sill, track, guide or bottom seal")
        if self.transition and self.transition.role != "transition":
            raise ValueError("transition must describe a floor transition")
        if self.floor_treatment == "continuous" and self.transition:
            raise ValueError("continuous floor cannot also specify a transition")
        return self


for _constructor in (DoorwaySectionPart, DoorwayProductSpec, DoorwayTreatment):
    register_constructor(_constructor.__name__, _constructor)
