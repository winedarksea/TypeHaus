"""Earth, finite-strip surcharge and water pressures for courtyard wall sections."""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.engineering.sunken_garden.inputs import PlantingProfile, SunkenGardenDesignInput


@dataclass(frozen=True)
class PressureResult:
    thrust_plf: float
    moment_at_footing_top_ftlb_per_ft: float
    peak_psf: float


def finite_strip_lateral_pressure_psf(*, surcharge_psf: float, depth_ft: float,
                                      near_edge_ft: float, width_ft: float) -> float:
    """FHWA NHI-06-089 Figure 10-14 strip-load pressure.

    ``p_h = 2q/pi [beta - sin(beta) cos(2 alpha)]`` with angles in radians.  The
    semi-empirical solution assumes an unyielding wall, appropriate to the court's braced
    screening case.  At the ground line the limiting adjacent-strip pressure is ``q``.
    """

    if surcharge_psf < 0 or depth_ft < 0 or near_edge_ft < 0 or width_ft <= 0:
        raise ValueError("strip surcharge, depth and dimensions must be nonnegative")
    if depth_ft == 0:
        return surcharge_psf if near_edge_ft == 0 else 0.0
    near_angle_from_vertical = math.atan(near_edge_ft / depth_ft)
    far_angle_from_vertical = math.atan((near_edge_ft + width_ft) / depth_ft)
    beta = far_angle_from_vertical - near_angle_from_vertical
    alpha = math.pi / 2.0 - (near_angle_from_vertical + far_angle_from_vertical) / 2.0
    return 2.0 * surcharge_psf / math.pi * (
        beta - math.sin(beta) * math.cos(2.0 * alpha)
    )


def pressure_at_height_psf(design: SunkenGardenDesignInput, planting: PlantingProfile,
                           height_above_footing_ft: float, *, wet: bool = False,
                           compaction_surcharge_psf: float = 0.0,
                           full_height_comparison: bool = False) -> float:
    """Service lateral pressure at one point; height is measured up from footing top."""

    soil = design.soil
    ordinary = soil.ordinary_retained_height_ft.value
    if full_height_comparison:
        direct = soil.at_rest_efp_pcf.value * max(
            design.geometry.concrete_stem_height_ft - height_above_footing_ft, 0.0)
    else:
        direct = soil.at_rest_efp_pcf.value * max(ordinary - height_above_footing_ft, 0.0)
        if planting.layout in {"against-wall", "reference"} and height_above_footing_ft > ordinary:
            direct = soil.at_rest_efp_pcf.value * max(
                ordinary + planting.raised_height_ft - height_above_footing_ft, 0.0)

    depth_below_yard = max(ordinary - height_above_footing_ft, 0.0)
    surcharge = 0.0
    if planting.raised_height_ft and depth_below_yard >= 0:
        near = 0.0 if planting.layout in {"against-wall", "reference"} else planting.setback_ft
        surcharge = finite_strip_lateral_pressure_psf(
            surcharge_psf=soil.unit_weight_pcf.value * planting.raised_height_ft,
            depth_ft=depth_below_yard, near_edge_ft=near, width_ft=planting.clear_width_ft,
        )
    if compaction_surcharge_psf:
        surcharge += compaction_surcharge_psf * (
            soil.at_rest_efp_pcf.value / soil.unit_weight_pcf.value)
    water = 0.0
    if wet:
        water_height = design.drainage.blocked_drain_water_height_ft.value
        water = 62.4 * max(water_height - height_above_footing_ft, 0.0)
    return direct + surcharge + water


def integrate_pressure(design: SunkenGardenDesignInput, planting: PlantingProfile,
                       *, wet: bool = False, compaction_surcharge_psf: float = 0.0,
                       full_height_comparison: bool = False,
                       subdivisions: int = 1200) -> PressureResult:
    """Integrate pressure and base moment by midpoint strips."""

    height = design.geometry.concrete_stem_height_ft
    dz = height / subdivisions
    def pressure(z: float) -> float:
        return pressure_at_height_psf(
            design, planting, z, wet=wet,
            compaction_surcharge_psf=compaction_surcharge_psf,
            full_height_comparison=full_height_comparison,
        )
    samples = [(index + 0.5) * dz for index in range(subdivisions)]
    values = [pressure(z) for z in samples]
    return PressureResult(
        thrust_plf=sum(values) * dz,
        moment_at_footing_top_ftlb_per_ft=sum(
            p * dz * z for p, z in zip(values, samples, strict=True)
        ),
        peak_psf=max(values, default=0.0),
    )
