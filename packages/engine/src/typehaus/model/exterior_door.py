"""Installation choices independent of the factory door and sill cross-sections."""
from typing import Literal

from pydantic import Field, model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch


class DoorCatalogDimensions(HausModel):
    """Nominal leaves and catalog unit envelope, distinct from DoorType's framed void."""
    nominal_width: Length
    nominal_height: Length
    unit_width: Length
    unit_height: Length
    source_url: str
    source_drawing: str
    assembly_confirmed: bool = False


class ExteriorDoorCatalogInstallation(HausModel):
    """Sourced product outline and separately declared project installation dimensions.

    A digitized outline documents clearance, not extrusion wall thickness or certification.
    Connection capacities are deliberately optional: missing evidence cannot become a pass.
    """
    source_url: str = Field(min_length=1)
    source_drawing: str = Field(min_length=1)
    sill_outline_m: tuple[tuple[float, float], ...]
    sill_extender_ref: str | None = None
    sill_extender_source_url: str | None = None
    sill_extender_depth: Length = inch(0)
    sill_extender_height: Length = inch(0)
    sill_extender_slope_degrees: float = Field(default=5, gt=0, lt=45)
    pan_product: str = "SureSill 4-9/16 inch sloped sill pan, 80 inch complete pack"
    pan_height: Length = inch(0.375)
    height_tolerance: Length = inch(0.25)
    approach_thickness: Length = inch(1.5)
    approach_board_width: Length = inch(6)
    approach_slope_ratio: float = Field(default=1 / 48, gt=0)
    approach_material_ref: str = "aluminum-deck"
    pan_material_ref: str = "fluid-applied-flashing"
    sill_material_ref: str = "aluminum-extrusion"
    frame_material_ref: str = Field(min_length=1)
    head_material_ref: str = Field(min_length=1)
    transition_material_ref: str = Field(min_length=1)
    support_ref: str = Field(min_length=1)
    support_kind: Literal["timber_outriggers", "concrete_cantilever"]
    support_spacing: Length = inch(12)
    support_width: Length = inch(1.5)
    support_depth: Length = inch(5.5)
    support_backspan: Length = inch(24)
    support_material_ref: str = "kdat"
    support_connection_capacity_lb: float | None = Field(default=None, gt=0)
    support_connection_source: str | None = None
    live_load_psf: float = Field(default=60, gt=0)
    dead_load_psf: float = Field(default=10, gt=0)
    concentrated_load_lb: float = Field(default=300, gt=0)
    timber_bending_psi: float = Field(default=575, gt=0)
    timber_shear_psi: float = Field(default=135, gt=0)
    timber_modulus_psi: float = Field(default=1_200_000, gt=0)
    movement_horizontal: Length = inch(0.25)
    movement_vertical: Length = inch(0.25)
    flashing_overlap: Length = inch(2)
    cross_bearer_width: Length = inch(1.5)
    cross_bearer_depth: Length = inch(3.5)
    minimum_drainage_clearance: Length = inch(0.125)
    concrete_strength_psi: float = Field(default=4000, gt=0)
    concrete_cover: Length = inch(2)
    reinforcement_area_in2: float = Field(default=0.2, gt=0)
    reinforcement_diameter: Length = inch(0.5)
    reinforcement_yield_psi: float = Field(default=60_000, gt=0)
    receiver_depth: Length = inch(1.375)
    receiver_diameter: Length = inch(0.625)
    receiver_pan_clearance: Length = inch(0.0625)

    @model_validator(mode="after")
    def valid_catalog_installation(self):
        from math import isfinite

        from shapely.geometry import Polygon

        if (not self.sill_outline_m or not all(isfinite(v) for p in self.sill_outline_m for v in p)
                or not Polygon(self.sill_outline_m).is_valid
                or Polygon(self.sill_outline_m).area <= 0):
            raise ValueError("catalog sill requires a finite simple coordination outline")
        extender_values = (self.sill_extender_ref, self.sill_extender_source_url)
        if self.sill_extender_depth.meters > 0:
            if not all(extender_values) or self.sill_extender_height.meters <= 0:
                raise ValueError(
                    "a sill extender needs its catalog reference, source and profile height"
                )
        elif any(extender_values) or self.sill_extender_height.meters:
            raise ValueError("sill extender profile dimensions require a positive extension depth")
        dimensions = (self.pan_height, self.height_tolerance, self.approach_thickness,
                      self.support_spacing, self.support_width, self.support_depth,
                      self.support_backspan, self.movement_horizontal, self.movement_vertical,
                      self.flashing_overlap, self.receiver_depth, self.receiver_diameter,
                      self.receiver_pan_clearance, self.cross_bearer_width, self.cross_bearer_depth,
                      self.minimum_drainage_clearance)
        if any(v.meters <= 0 for v in dimensions):
            raise ValueError("catalog installation dimensions must be positive")
        if self.support_connection_capacity_lb is not None and not self.support_connection_source:
            raise ValueError("a connection capacity requires published/design evidence")
        if (self.support_kind == "concrete_cantilever" and self.support_depth.meters
                <= self.concrete_cover.meters + self.reinforcement_diameter.meters / 2):
            raise ValueError("concrete support depth must exceed cover plus bar radius")
        return self


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
    catalog_installation: ExteriorDoorCatalogInstallation | None = None
    exterior_opening_ref: str | None = None
    seat_opening_ref: str | None = None
    approach_opening_refs: tuple[str, ...] = ()
    interior_material_ref: str = Field(min_length=1)
    drainage_gap: Length = inch(0.5)
    # Limit the search across an intentional drainage gap, never across a missing landing.
    landing_search: Length = inch(6)
    maximum_landing_drop: Length = inch(7.75)

    @model_validator(mode="after")
    def positive_dimensions(self):
        if self.sill_design and self.catalog_installation:
            raise ValueError("catalog installation replaces the schematic sill design")
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
register_constructor("ExteriorDoorCatalogInstallation", ExteriorDoorCatalogInstallation)

register_constructor("DoorCatalogDimensions", DoorCatalogDimensions)
