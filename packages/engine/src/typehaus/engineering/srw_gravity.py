"""The NCMA/Allan Block gravity free body of a segmental unit wall — plain numbers only.

Coulomb active thrust with wall friction ``δ = ⅔φ`` on a back face battered by ``ω`` (the
unit's setback), resolved at ``δ − ω`` to the horizontal so its vertical component presses
the unit down; sliding at ``μ(W + P_v)``; overturning about the toe with the battered
prism's lean in the restoring arm. ``segmental_wall`` reads the model and calls this.

The retained soil's φ is read back off the code's equivalent fluid pressure at a soil unit
weight (``phi_from_efp``): IBC 1610.1 publishes a pressure, not an angle.

Oracle: ``notes/raised_garden_srw.md`` §2-§5, reproduced by ``tests/test_segmental_wall.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

#: NCMA/AB: interface friction between the unit and the retained fill, as a fraction of φ.
WALL_FRICTION_RATIO = 2.0 / 3.0


@dataclass(frozen=True)
class Section:
    """The wall as the free body sees it, feet and pcf."""

    retained_ft: float
    embedment_ft: float
    unit_depth_ft: float
    unit_weight_pcf: float
    batter_deg: float = 0.0
    course_ft: float = 0.5

    @property
    def height_ft(self) -> float:
        return self.retained_ft + self.embedment_ft


@dataclass(frozen=True)
class FreeBody:
    soil_phi_deg: float
    ka: float
    thrust_plf: float          # P_a, along its line of action
    thrust_h_plf: float
    thrust_v_plf: float
    weight_plf: float
    friction: float
    resisting_moment: float
    overturning_moment: float
    fs_sliding: float
    fs_overturning: float
    #: Resultant's distance from the toe; <= 0 means off the base.
    resultant_ft: float
    eccentricity_ft: float
    #: Peak toe pressure, psf; ``None`` where the resultant is off the base.
    bearing_psf: float | None
    course_shear_plf: float


def phi_from_efp(efp_psf_per_ft: float, soil_pcf: float) -> float:
    """φ, degrees, whose Rankine ``K_a`` reproduces the EFP at this unit weight."""
    ka = efp_psf_per_ft / soil_pcf
    return math.degrees(math.asin((1.0 - ka) / (1.0 + ka)))


def coulomb_ka(phi_deg: float, delta_deg: float, batter_deg: float) -> float:
    """Coulomb ``K_a``, level backfill, in AB's form with the back face at ``β = 90° − ω``."""
    phi, delta, beta = (math.radians(v) for v in (phi_deg, delta_deg, 90.0 - batter_deg))
    numerator = math.sin(beta - phi) / math.sin(beta)
    denominator = (math.sqrt(math.sin(beta + delta))
                   + math.sqrt(math.sin(phi + delta) * math.sin(phi) / math.sin(beta)))
    return (numerator / denominator) ** 2


def analyse(section: Section, soil_pcf: float, phi_deg: float,
            base_friction: float) -> FreeBody:
    h, b = section.height_ft, section.unit_depth_ft
    omega = section.batter_deg
    delta = WALL_FRICTION_RATIO * phi_deg
    ka = coulomb_ka(phi_deg, delta, omega)
    lean = math.tan(math.radians(omega))
    tilt = math.radians(delta - omega)

    def horizontal(height: float) -> float:
        return 0.5 * soil_pcf * ka * height * height * math.cos(tilt)

    thrust = 0.5 * soil_pcf * ka * h * h
    p_h, p_v = thrust * math.cos(tilt), thrust * math.sin(tilt)
    weight = section.unit_weight_pcf * b * h
    normal = weight + p_v
    overturning = p_h * h / 3.0
    resisting = weight * (b / 2.0 + h / 2.0 * lean) + p_v * (b + h / 3.0 * lean)
    x = (resisting - overturning) / normal
    e = b / 2.0 - x
    if x <= 0.0:
        bearing = None
    elif e <= b / 6.0:
        bearing = normal / b * (1.0 + 6.0 * e / b)
    else:
        bearing = 2.0 * normal / (3.0 * x)
    return FreeBody(
        soil_phi_deg=phi_deg, ka=ka, thrust_plf=thrust, thrust_h_plf=p_h, thrust_v_plf=p_v,
        weight_plf=weight, friction=base_friction, resisting_moment=resisting,
        overturning_moment=overturning, fs_sliding=base_friction * normal / p_h,
        fs_overturning=resisting / overturning, resultant_ft=x, eccentricity_ft=e,
        bearing_psf=bearing,
        course_shear_plf=horizontal(max(h - section.course_ft, 0.0)),
    )
