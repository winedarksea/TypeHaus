"""The NCMA/Allan Block gravity free body of a segmental unit wall — plain numbers only.

Coulomb active thrust with wall friction ``δ = ⅔φ`` on a back face battered by ``ω`` (the
unit's setback), resolved at ``δ − ω`` to the horizontal so its vertical component presses
the unit down; sliding at ``μ(W + P_v)``; overturning about the toe with the battered
prism's lean in the restoring arm. ``segmental_wall`` reads the model and calls this.

The retained soil's φ is read back off the code's equivalent fluid pressure at a soil unit
weight (``phi_from_efp``): IBC 1610.1 publishes a pressure, not an angle.

**A drainage zone** (AB's 12" of wall rock behind the unit) makes the backfill two
materials, so no closed form applies: ``trial_wedge`` maximises the Coulomb wedge force over
planes through the heel, the plane's friction the length-weighted ``tan φ`` of the rock it
crosses near the heel and the native beyond (uniform normal stress along the plane — the
rock carries the deeper, more heavily loaded part, so this under-credits it). With no zone
it reproduces ``coulomb_ka`` exactly; ``δ`` stays ⅔ of the NATIVE φ either way.

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
class DrainageZone:
    """Free-draining aggregate behind the unit: horizontal width, feet, and its φ."""

    width_ft: float
    phi_deg: float


@dataclass(frozen=True)
class Wedge:
    """The critical trial wedge through the heel."""

    thrust_plf: float
    plane_deg: float           # from horizontal
    reach_ft: float            # plane's exit at the surface, measured from the heel
    zone_share: float          # fraction of the plane's length inside the zone
    phi_equiv_deg: float


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
    wedge: Wedge | None = None


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


def _wedge_force(plane: float, height: float, soil_pcf: float, phi_deg: float,
                 delta_deg: float, batter_deg: float, zone: DrainageZone | None
                 ) -> tuple[float, float, float]:
    """``(P, zone share, φ_eq)`` on one trial plane ``plane`` rad from horizontal."""
    lean = math.tan(math.radians(batter_deg))
    rise = math.tan(plane)
    area = 0.5 * height * height * (1.0 / rise - lean)
    share = 0.0
    tan_phi = math.tan(math.radians(phi_deg))
    if zone is not None and zone.width_ft > 0.0:
        # The zone's back boundary is parallel to the battered face, ``width`` behind it.
        z_exit = min(zone.width_ft * rise / (1.0 - rise * lean), height)
        share = z_exit / height
        tan_phi = share * math.tan(math.radians(zone.phi_deg)) + (1.0 - share) * tan_phi
    phi_eq = math.atan(tan_phi)
    tilt = math.radians(delta_deg - batter_deg)
    if area <= 0.0 or plane <= phi_eq:
        return 0.0, share, phi_eq
    return (soil_pcf * area * math.sin(plane - phi_eq) / math.cos(plane - phi_eq - tilt),
            share, phi_eq)


def trial_wedge(height: float, soil_pcf: float, phi_deg: float, batter_deg: float,
                zone: DrainageZone | None = None, min_plane_deg: float = 0.0) -> Wedge:
    """The largest wedge force over planes through the heel (a 0.1° scan, then golden
    section to 1e-7 rad). ``min_plane_deg`` restricts the search to steeper planes."""
    delta = WALL_FRICTION_RATIO * phi_deg
    lean = math.tan(math.radians(batter_deg))
    top = min(89.9, math.degrees(math.atan(1.0 / lean)) - 0.01) if lean > 0.0 else 89.9

    def force(deg: float) -> float:
        return _wedge_force(math.radians(deg), height, soil_pcf, phi_deg, delta,
                            batter_deg, zone)[0]

    lo_deg = max(min_plane_deg, 1.0)
    grid = [lo_deg + 0.1 * i for i in range(int((top - lo_deg) / 0.1) + 1)]
    best = max(grid, key=force)
    a, b = max(best - 0.1, lo_deg), min(best + 0.1, top)
    golden = (math.sqrt(5.0) - 1.0) / 2.0
    while b - a > 1e-5:
        c, d = b - golden * (b - a), a + golden * (b - a)
        if force(c) >= force(d):
            b = d
        else:
            a = c
    plane = (a + b) / 2.0
    thrust, share, phi_eq = _wedge_force(math.radians(plane), height, soil_pcf, phi_deg,
                                         delta, batter_deg, zone)
    return Wedge(thrust, plane, height / math.tan(math.radians(plane)), share,
                 math.degrees(phi_eq))


def analyse(section: Section, soil_pcf: float, phi_deg: float,
            base_friction: float, zone: DrainageZone | None = None) -> FreeBody:
    h, b = section.height_ft, section.unit_depth_ft
    omega = section.batter_deg
    delta = WALL_FRICTION_RATIO * phi_deg
    lean = math.tan(math.radians(omega))
    tilt = math.radians(delta - omega)
    wedge = trial_wedge(h, soil_pcf, phi_deg, omega, zone)
    if zone is None:
        ka = coulomb_ka(phi_deg, delta, omega)
        thrust = 0.5 * soil_pcf * ka * h * h
    else:
        thrust = wedge.thrust_plf
        ka = thrust / (0.5 * soil_pcf * h * h)

    def horizontal(height: float) -> float:
        if height <= 0.0:
            return 0.0
        if zone is None:
            return 0.5 * soil_pcf * ka * height * height * math.cos(tilt)
        return trial_wedge(height, soil_pcf, phi_deg, omega, zone).thrust_plf * math.cos(tilt)

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
        course_shear_plf=horizontal(max(h - section.course_ft, 0.0)), wedge=wedge,
    )
