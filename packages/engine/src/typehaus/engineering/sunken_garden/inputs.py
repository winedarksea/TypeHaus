"""Typed inputs for the revised courtyard study.

Every field that normally comes from a survey, geotechnical report, product submittal or
structural calculation carries that basis.  A planning assumption is usable for screening,
but remains visible as an unresolved requirement in the published comparison.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class BasedValue(Generic[T]):
    value: T
    basis: str
    measured: bool = False


@dataclass(frozen=True)
class SoilProfile:
    ordinary_retained_height_ft: BasedValue[float]
    unit_weight_pcf: BasedValue[float]
    at_rest_efp_pcf: BasedValue[float]
    active_efp_pcf: BasedValue[float]
    interface_friction: BasedValue[float]
    allowable_bearing_psf: BasedValue[float]
    vertical_support_pci: BasedValue[float | None]
    horizontal_support_pci: BasedValue[float | None]
    groundwater_height_ft: BasedValue[float | None]


@dataclass(frozen=True)
class CourtGeometry:
    clear_width_ft: float
    retained_side_length_ft: float
    concrete_stem_height_ft: float
    concrete_top_elevation_ft: float
    footing_depth_ft: float
    stem_thickness_in: float
    footing_width_ft: float
    toe_ft: float

    @property
    def heel_ft(self) -> float:
        return self.footing_width_ft - self.toe_ft - self.stem_thickness_in / 12.0


@dataclass(frozen=True)
class PlantingProfile:
    layout: str
    raised_height_ft: float
    clear_width_ft: float
    setback_ft: float


@dataclass(frozen=True)
class ConnectionAssumptions:
    grade_beam: BasedValue[str]
    veneer_beam: BasedValue[str]
    porch_bracing: BasedValue[str]
    monolithic_corners: BasedValue[bool]
    thermal_break_connection: BasedValue[str]
    balcony_reactions_lb: BasedValue[tuple[float, float, float, float] | None]


@dataclass(frozen=True)
class DrainageInputs:
    wall_drain_outlet: BasedValue[str]
    bearing_stone_outlet: BasedValue[str]
    sump_available: BasedValue[bool | None]
    infiltration_rate_in_hr: BasedValue[float | None]
    blocked_drain_water_height_ft: BasedValue[float]


@dataclass(frozen=True)
class SunkenGardenDesignInput:
    geometry: CourtGeometry
    soil: SoilProfile
    connections: ConnectionAssumptions
    drainage: DrainageInputs

    def unresolved_requirements(self) -> tuple[str, ...]:
        checks = (
            (self.soil.vertical_support_pci, "vertical soil-support modulus"),
            (self.soil.horizontal_support_pci, "horizontal soil-support modulus"),
            (self.soil.groundwater_height_ft, "seasonal groundwater elevation"),
            (self.connections.balcony_reactions_lb, "four balcony-column reactions"),
            (self.drainage.sump_available, "sump availability and emergency power"),
            (self.drainage.infiltration_rate_in_hr, "field infiltration rate"),
        )
        return tuple(name for item, name in checks if item.value is None)


def default_design_input(*, stem_thickness_in: float = 12.0,
                         footing_width_ft: float = 7.0,
                         toe_ft: float = 3.0) -> SunkenGardenDesignInput:
    """Catlin study basis. Site-dependent values stay explicitly unresolved."""

    return SunkenGardenDesignInput(
        geometry=CourtGeometry(
            clear_width_ft=19.0, retained_side_length_ft=16.0 + 4.0 / 12.0,
            concrete_stem_height_ft=9.1198, concrete_top_elevation_ft=0.0,
            footing_depth_ft=1.0, stem_thickness_in=stem_thickness_in,
            footing_width_ft=footing_width_ft, toe_ft=toe_ft,
        ),
        soil=SoilProfile(
            ordinary_retained_height_ft=BasedValue(5.0, "owner profile; verify by survey"),
            unit_weight_pcf=BasedValue(120.0, "midpoint of 110-130 pcf screening band"),
            at_rest_efp_pcf=BasedValue(60.0, "IBC 2018 Table 1610.1 presumptive SM"),
            active_efp_pcf=BasedValue(45.0, "IBC 2018 Table 1610.1 presumptive SM"),
            interface_friction=BasedValue(0.35, "IBC Table 1806.2 class 3 washed stone"),
            allowable_bearing_psf=BasedValue(3000.0, "IBC Table 1806.2 class 3; verify subgrade"),
            vertical_support_pci=BasedValue(None, "geotechnical report required"),
            horizontal_support_pci=BasedValue(None, "geotechnical report required"),
            groundwater_height_ft=BasedValue(None, "piezometer/seasonal observation required"),
        ),
        connections=ConnectionAssumptions(
            grade_beam=BasedValue("monolithic fixed connection", "authored pour sequence"),
            veneer_beam=BasedValue("fixed-ended until connection design", "screening model"),
            porch_bracing=BasedValue("excluded", "required no-credit comparison"),
            monolithic_corners=BasedValue(True, "authored single wall placement"),
            thermal_break_connection=BasedValue(
                "GFRP dowels transfer stated shear only; stiffness unresolved",
                "authored detail; manufacturer/engineer data required"),
            balcony_reactions_lb=BasedValue(None, "coupled gravity/lateral analysis required"),
        ),
        drainage=DrainageInputs(
            wall_drain_outlet=BasedValue("drywell with overflow to SM-B-RADON", "modelled network"),
            bearing_stone_outlet=BasedValue(
                "shared storage; invert survey required", "modelled section"),
            sump_available=BasedValue(None, "owner/MEP decision required"),
            infiltration_rate_in_hr=BasedValue(None, "field test required"),
            blocked_drain_water_height_ft=BasedValue(5.0, "credible blocked-collection envelope"),
        ),
    )
