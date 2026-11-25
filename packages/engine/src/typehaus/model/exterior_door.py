"""Installation choices independent of the factory door and sill cross-sections."""
from typing import Literal

from pydantic import Field, model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, inch


class DoorCatalogDimensions(HausModel):
    """A published unit envelope and its clear opening. The nominal leaf is
    ``DoorType.width``/``height``; the published RO is ``DoorType.rough_opening``."""
    unit_width: Length
    unit_height: Length
    # The maker's clear opening, leaf at 90 degrees, and installed clear height. They win
    # over the estimate in ``resolve/door_sizing``.
    clear_width_90: Length | None = None
    clear_height: Length | None = None
    source_url: str
    source_drawing: str
    assembly_confirmed: bool = False


class ApproachBearing(HausModel):
    """The approach rests at both ends; nothing cantilevers, nothing crosses the joint fixed.

    House end: the threshold, and past the sheathing draining strips on the truss wall's
    buck sill over its girt sill course (``girt_course``). Outer end: ``landing="gap"``
    stops short of the landing by an open movement gap, the landing's plank ends on its own
    member; ``"slip_pad"`` rests on the landing deck over its nearest member on a pad;
    ``"cover"`` bridges the open gap with a removable cover fixed on the landing member's
    inner part and sliding on a ``cover_seat`` ledge on the sill beam's face, below its drip.
    """
    landing_ref: str = Field(min_length=1)
    landing: Literal["gap", "slip_pad", "cover"] = "gap"
    cover_material_ref: str | None = None
    cover_seat_material_ref: str = "kdat"
    cover_seat: Length = inch(1.5)
    cover_seat_thickness: Length = inch(0.75)
    cover_min_bearing: Length = inch(0.5)
    # Added to the catalog's movement allowance, each way, for the cover's range.
    cover_tolerance: Length = inch(0.25)
    # Where the water dropping through the cover goes: an element tag that must resolve.
    cover_discharge_ref: str | None = None
    girt_course: bool = True
    minimum_bearing: Length = inch(1)
    slip_pad_material_ref: str | None = None
    maximum_pad_thickness: Length = inch(1.5)
    # Plank ends at the door must sit this far onto the landing's member.
    plank_bearing: Length = inch(0.75)
    # The point load the girt sill course's screws are graded for, anywhere along it.
    concentrated_load_lb: float = Field(default=300, gt=0)

    @model_validator(mode="after")
    def slip_pad_named(self):
        if self.landing == "slip_pad" and not self.slip_pad_material_ref:
            raise ValueError("a slip-pad landing names its pad material")
        if self.landing == "cover" and not (self.cover_material_ref and self.cover_discharge_ref):
            raise ValueError("a cover landing names its cover material and discharge")
        return self


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
    pan_source_url: str = "https://www.suresill.com/faq"
    approach_source_url: str = "https://wahoobuildingproducts.com/ariddek-installation-guide/"
    head_source_url: str = "https://www.suresill.com/product/headflash"
    transition_source_url: str = (
        "https://www.tremcosealants.com/resource/download/Proglaze_ETA_System_1_AI.pdf"
    )
    # Design envelopes pending installed sections; these are not certified product dimensions.
    stock_head_flashing: bool = True
    head_cap_depth: Length = inch(1.375)
    head_upstand_height: Length = inch(1.5)
    head_end_dam_height: Length = inch(0.5)
    head_profile_thickness: Length = inch(0.020)
    independent_landing_flashing: bool = False
    transition_adapter_width: Length = inch(0.375)
    transition_adapter_thickness: Length = inch(0.020)
    transition_adapter_material_ref: str = "aluminum-extrusion"
    transition_strip_width: Length = inch(6)
    transition_sheet_thickness: Length = inch(0.020)
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
    # ``foam_bed``: one tread laid continuously on rated foam, not fastened to anything; its
    # bearing is graded at ``foam_rated_psi / foam_creep_divisor`` and it has no root
    # connection or bar development to document.
    # ``girt_bridge``: a catalog extender on draining strips over the truss wall's buck sill
    # and girt sill course (``ExteriorDoorInstallation.approach_bearing``); no approach boards.
    support_kind: Literal["timber_outriggers", "concrete_cantilever", "foam_bed", "girt_bridge"]
    support_spacing: Length = inch(12)
    support_width: Length = inch(1.5)
    support_depth: Length = inch(5.5)
    support_backspan: Length = inch(24)
    support_material_ref: str = "kdat"
    foam_rated_psi: float | None = Field(default=None, gt=0)
    # foam_bed: a flat plate under the tread spreads its load over the full footprint; the
    # foam course thins by its thickness. Without one, a profiled underside needs an authored
    # contact area or its bearing is UNKNOWN.
    bearing_plate_material_ref: str | None = None
    bearing_plate_thickness: Length = inch(0)
    approach_profiled_underside: bool = False
    approach_contact_area_in2: float | None = Field(default=None, gt=0)
    foam_creep_divisor: float = Field(default=3.0, gt=1)
    foam_course_depth: Length = inch(1)
    # The water layer under the approach; the pan's own membrane when not stated.
    apron_material_ref: str | None = None
    # foam_bed: the sheet runs this far back under the pan, which laps over it (shingled, no
    # bond claimed), and stops at the tread's outer face.
    sheet_lap_under_pan: Length = inch(2)
    # foam_bed: the slot lets go down an isolation joint. ``joint_drain_wall_ref``'s joint
    # layer is cut across the reveal (a blind opening) and filled with
    # ``joint_drain_material_ref`` down to ``joint_drain_bed_ref``'s stone.
    joint_drain_wall_ref: str | None = None
    joint_drain_material_ref: str | None = None
    joint_drain_bed_ref: str | None = None
    # foam_bed, no joint to drain down: the tread's nose drips onto ``drain_slab_ref``'s top,
    # at least ``drain_slab_clearance`` in from that slab's own edge (the joint to the host).
    drain_slab_ref: str | None = None
    drain_slab_clearance: Length = inch(0.5)
    # Box sides sealed to separately supported masonry: the joint must take the reserved
    # house/court movement at the sealant's ASTM C920 class (0.5 = Class 50).
    box_side_sealant_ref: str | None = None
    box_side_joint_width: Length = inch(0.5)
    box_side_sealant_class: float = Field(default=0.5, gt=0, le=1)
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
    # The passive leaf's lower bolt receiver: a cup in a hole drilled into the cap, at
    # ``receiver_station`` from the outline's rear edge, at least ``receiver_depth`` deep.
    receiver_depth: Length = inch(1.375)
    receiver_diameter: Length = inch(0.625)
    receiver_station: Length = inch(1.0)
    receiver_source: str = ("Endura Flip-Lever astragal field instructions #211159-FL-I-FP, "
                            "step 1d (Z-adjustable cap sill): 5/8 in hole at least 1-3/8 in deep")
    # A digitized outline's height accuracy: a hole within it of the body's underside is in.
    outline_tolerance: Length = inch(0.1)

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
                      self.receiver_station, self.outline_tolerance, self.cross_bearer_width,
                      self.cross_bearer_depth,
                      self.minimum_drainage_clearance, self.approach_board_width,
                      self.head_cap_depth, self.head_upstand_height, self.head_end_dam_height,
                      self.head_profile_thickness, self.transition_adapter_width,
                      self.transition_adapter_thickness, self.transition_strip_width,
                      self.transition_sheet_thickness)
        if any(v.meters <= 0 for v in dimensions):
            raise ValueError("catalog installation dimensions must be positive")
        if self.support_connection_capacity_lb is not None and not self.support_connection_source:
            raise ValueError("a connection capacity requires published/design evidence")
        if (self.bearing_plate_material_ref is None) != (self.bearing_plate_thickness.meters <= 0):
            raise ValueError("a bearing plate names its material and a positive thickness")
        if self.support_kind == "foam_bed" and self.foam_rated_psi is None:
            raise ValueError("a foam-bed approach needs the foam's rated compressive psi")
        drain = (self.joint_drain_wall_ref, self.joint_drain_material_ref,
                 self.joint_drain_bed_ref)
        if any(drain) and not all(drain):
            raise ValueError("a joint drain names its wall, its material and its stone bed")
        if self.drain_slab_ref and any(drain):
            raise ValueError("a tread drains down a joint or onto a slab, not both")
        if self.drain_slab_clearance.meters <= 0:
            raise ValueError("the slab drip clearance must be positive")
        if self.sheet_lap_under_pan.meters <= 0 or self.box_side_joint_width.meters <= 0:
            raise ValueError("sheet lap and box-side joint must be positive")
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
    #: True: the pan falls at the flashing slope across the RO only (back dam to the
    #: frame's outer face) and runs level from there to its outlet, so the threshold
    #: seats lower than on a pan sloped all the way out (R311.3.1's 1.5" interior rise).
    pan_across_ro: bool = False
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
    # Run the exterior returns past the host's face to the back of a masonry reveal, so the
    # box sides close the veneer cavity at the opening.
    exterior_return_to_reveal_back: bool = False
    # The exterior returns' own stock thickness where it differs from the interior's.
    exterior_return_thickness: Length | None = None
    exterior_wrap_thickness: Length = inch(0.024)
    wrap_isolation_material_ref: str = "fluid-applied-flashing"
    wrap_isolation_thickness: Length = inch(0.020)
    # Explicit schematic selection for early coordination, never a catalog failure fallback.
    sill_design: ExteriorDoorSillDesign | None = None
    catalog_installation: ExteriorDoorCatalogInstallation | None = None
    exterior_opening_ref: str | None = None
    seat_opening_ref: str | None = None
    approach_opening_refs: tuple[str, ...] = ()
    interior_material_ref: str = Field(min_length=1)
    # The no-cantilever approach (``girt_bridge`` catalog doors, and schematic sills).
    approach_bearing: ApproachBearing | None = None
    drainage_gap: Length = inch(0.5)
    # Limit the search across an intentional drainage gap, never across a missing landing.
    landing_search: Length = inch(6)
    maximum_landing_drop: Length = inch(7.75)

    @model_validator(mode="after")
    def positive_dimensions(self):
        if self.sill_design and self.catalog_installation:
            raise ValueError("catalog installation replaces the schematic sill design")
        bridge = (self.catalog_installation is not None
                  and self.catalog_installation.support_kind == "girt_bridge")
        if bridge and (self.approach_bearing is None
                       or not self.catalog_installation.sill_extender_ref):
            raise ValueError("a girt-bridge catalog door needs its approach bearing and extender")
        if (self.approach_bearing is not None and self.catalog_installation is not None
                and not bridge):
            raise ValueError("an approach bearing replaces the catalog door's own supports")
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
register_constructor("ApproachBearing", ApproachBearing)
