"""Corrected gravity-beam screening for W-SG-BRKBM.

The historical note remains untouched. This calculation uses actual 5,000 psi concrete,
strength-design load factors, ACI's effective-span rule and both minimum-steel equations.
Connection restraint, compatibility torsion and long-term properties remain named limits.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class VeneerBeamResult:
    effective_span_ft: float
    service_load_plf: float
    factored_load_plf: float
    factored_moment_ftlb: float
    factored_shear_lb: float
    effective_depth_in: float
    required_steel_in2: float
    minimum_steel_in2: float
    provided_steel_in2: float
    flexure_ratio: float
    shear_ratio: float
    immediate_deflection_in: float
    long_term_deflection_in: float
    deflection_limit_in: float
    torsion_ftlb_per_ft: float
    unresolved: tuple[str, ...]


def check_veneer_beam(*, clear_span_ft: float = 19.0, bearing_in: float = 6.0,
                       width_in: float = 12.0, depth_in: float = 17.75,
                       fc_psi: float = 5000.0, fy_psi: float = 60000.0,
                       clear_cover_in: float = 2.0, stirrup_diameter_in: float = 0.375,
                       longitudinal_bar_diameter_in: float = 0.625,
                       provided_bar_count: int = 3, provided_bar_area_in2: float = 0.31,
                       veneer_load_plf: float = 308.0,
                       beam_load_plf: float = 222.0) -> VeneerBeamResult:
    d = depth_in - clear_cover_in - stirrup_diameter_in - longitudinal_bar_diameter_in / 2.0
    center_span_ft = clear_span_ft + bearing_in / 12.0
    effective_span_ft = min(clear_span_ft + d / 12.0, center_span_ft)
    service_load = veneer_load_plf + beam_load_plf
    factored_load = 1.2 * service_load
    moment = factored_load * effective_span_ft ** 2 / 8.0
    shear = factored_load * effective_span_ft / 2.0
    required = moment * 12.0 / (0.9 * fy_psi * 0.9 * d)
    minimum = max(
        3.0 * math.sqrt(fc_psi) * width_in * d / fy_psi,
        200.0 * width_in * d / fy_psi,
    )
    provided = provided_bar_count * provided_bar_area_in2
    a = provided * fy_psi / (0.85 * fc_psi * width_in)
    phi_mn_ftlb = 0.9 * provided * fy_psi * (d - a / 2.0) / 12.0
    phi_vc_lb = 0.75 * 2.0 * math.sqrt(fc_psi) * width_in * d

    span_in = effective_span_ft * 12.0
    inertia_in4 = width_in * depth_in ** 3 / 12.0
    modulus_psi = 57000.0 * math.sqrt(fc_psi)
    immediate = 5.0 * (service_load / 12.0) * span_in ** 4 / (
        384.0 * modulus_psi * inertia_in4
    )
    long_term = immediate * 3.0  # screening: sustained dead load, xi=2.0 plus immediate
    return VeneerBeamResult(
        effective_span_ft=effective_span_ft, service_load_plf=service_load,
        factored_load_plf=factored_load, factored_moment_ftlb=moment,
        factored_shear_lb=shear, effective_depth_in=d,
        required_steel_in2=required, minimum_steel_in2=minimum,
        provided_steel_in2=provided,
        flexure_ratio=moment / phi_mn_ftlb, shear_ratio=shear / phi_vc_lb,
        immediate_deflection_in=immediate, long_term_deflection_in=long_term,
        deflection_limit_in=span_in / 240.0,
        torsion_ftlb_per_ft=veneer_load_plf * 4.14 / 12.0,
        unresolved=(
            "verify beam-to-wall pocket restraint and bar development",
            "verify slab-to-beam compatibility before neglecting torsion",
            "confirm sustained-load fraction, cracking and shrinkage restraint",
            "design masonry anchors for the full insulated standoff",
        ),
    )
