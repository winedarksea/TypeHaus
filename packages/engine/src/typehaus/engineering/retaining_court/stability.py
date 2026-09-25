"""Service stability checks for revised courtyard soil profiles."""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.engineering.retaining_court.inputs import CourtDesignInput, PlantingProfile
from typehaus.engineering.retaining_court.loads import PressureResult, integrate_pressure

CONCRETE_PCF = 150.0


@dataclass(frozen=True)
class StabilityResult:
    case: str
    pressure: PressureResult
    vertical_weight_plf: float
    sliding_fs: float
    overturning_fs: float
    bearing_max_psf: float
    bearing_min_psf: float
    contact_loss: bool
    passes_screening: bool


def _raised_soil_overlap_ft(design: CourtDesignInput,
                            planting: PlantingProfile) -> float:
    heel = design.geometry.heel_ft
    if planting.layout in {"against-wall", "reference"}:
        return min(heel, planting.clear_width_ft)
    if planting.layout == "setback":
        return max(min(heel - planting.setback_ft, planting.clear_width_ft), 0.0)
    return 0.0


def analyse_stability(design: CourtDesignInput, planting: PlantingProfile, *,
                      case: str = "ordinary", wet: bool = False,
                      compaction_surcharge_psf: float = 0.0,
                      full_height_comparison: bool = False) -> StabilityResult:
    """Per-foot free body; stability uses service loads and effective wet weight."""

    geometry = design.geometry
    pressure = integrate_pressure(
        design, planting, wet=wet, compaction_surcharge_psf=compaction_surcharge_psf,
        full_height_comparison=full_height_comparison,
    )
    concrete_density = CONCRETE_PCF - (62.4 if wet else 0.0)
    soil_density = design.soil.unit_weight_pcf.value - (62.4 if wet else 0.0)
    stem_weight = (geometry.stem_thickness_in / 12.0
                   * geometry.concrete_stem_height_ft * concrete_density)
    footing_weight = geometry.footing_width_ft * geometry.footing_depth_ft * concrete_density
    ordinary_soil = geometry.heel_ft * design.soil.ordinary_retained_height_ft.value * soil_density
    raised_soil = (_raised_soil_overlap_ft(design, planting)
                   * planting.raised_height_ft * soil_density)
    weight = stem_weight + footing_weight + ordinary_soil + raised_soil

    toe = geometry.toe_ft
    stem_centroid = toe + geometry.stem_thickness_in / 24.0
    footing_centroid = geometry.footing_width_ft / 2.0
    ordinary_centroid = toe + geometry.stem_thickness_in / 12.0 + geometry.heel_ft / 2.0
    raised_width = _raised_soil_overlap_ft(design, planting)
    raised_centroid = toe + geometry.stem_thickness_in / 12.0 + raised_width / 2.0
    resisting = (stem_weight * stem_centroid + footing_weight * footing_centroid
                 + ordinary_soil * ordinary_centroid + raised_soil * raised_centroid)
    overturning = pressure.moment_at_footing_top_ftlb_per_ft + (
        pressure.thrust_plf * geometry.footing_depth_ft
    )
    resultant_from_toe = (resisting - overturning) / weight
    eccentricity = geometry.footing_width_ft / 2.0 - resultant_from_toe
    average = weight / geometry.footing_width_ft
    bearing_max = average * (1.0 + 6.0 * eccentricity / geometry.footing_width_ft)
    bearing_min = average * (1.0 - 6.0 * eccentricity / geometry.footing_width_ft)
    sliding = weight * design.soil.interface_friction.value / pressure.thrust_plf
    overturning_fs = resisting / overturning
    passes = (
        sliding >= 1.5 and overturning_fs >= 1.5 and bearing_min >= 0
        and bearing_max <= design.soil.allowable_bearing_psf.value
    )
    return StabilityResult(
        case=case, pressure=pressure, vertical_weight_plf=weight,
        sliding_fs=sliding, overturning_fs=overturning_fs,
        bearing_max_psf=bearing_max, bearing_min_psf=bearing_min,
        contact_loss=bearing_min < 0, passes_screening=passes,
    )
