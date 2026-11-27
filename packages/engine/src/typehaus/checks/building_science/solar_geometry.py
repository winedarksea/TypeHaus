"""Sun position and clear-sky irradiance for the cooling design day (ASHRAE clear-sky model).

Surface azimuths are measured from SOUTH, positive west, in radians: a south face is 0, west
is +π/2, north is ±π. ``compass.true_bearing`` supplies the true bearing; ``surface_azimuth``
converts it. Nothing here names a facade, so a house rotated off axis is graded continuously.
"""

from __future__ import annotations

import math

# ASHRAE clear-sky coefficients for the 21st of the month (published table): ``A`` the
# apparent extraterrestrial direct normal irradiance (Btu/h·ft²), ``B`` the atmospheric
# extinction, ``C`` the diffuse sky factor. July is the northern cooling design month.
JULY_A = 346.1
JULY_B = 0.207
JULY_C = 0.136
# Solar declination on 21 July, degrees.
_JULY_DECLINATION_DEG = 20.6
# Ground reflectance: ASHRAE's 0.2 for ordinary ground (snow's 0.7 is not a cooling condition).
_GROUND_REFLECTANCE = 0.2


def surface_azimuth(true_bearing_rad: float) -> float:
    """Azimuth from south (positive west) of a vertical surface's outward true bearing."""
    azimuth = (true_bearing_rad - math.pi) % (2.0 * math.pi)
    return azimuth - 2.0 * math.pi if azimuth > math.pi + 1e-12 else azimuth


def solar_position(latitude_deg: float, solar_hour: float) -> tuple[float, float]:
    """``(altitude, azimuth-from-south)`` in radians for the cooling design date.

    ``sin β = cos L cos δ cos H + sin L sin δ`` and
    ``cos φ = (sin β sin L − sin δ) / (cos β cos L)``, signed by the hour angle so the
    morning sun is east of south. Standard spherical trigonometry, not a correlation.
    """
    latitude = math.radians(latitude_deg)
    declination = math.radians(_JULY_DECLINATION_DEG)
    hour_angle = math.radians(15.0 * (solar_hour - 12.0))
    sin_altitude = (math.cos(latitude) * math.cos(declination) * math.cos(hour_angle)
                    + math.sin(latitude) * math.sin(declination))
    sin_altitude = max(-1.0, min(1.0, sin_altitude))
    altitude = math.asin(sin_altitude)
    cos_altitude = math.cos(altitude)
    if abs(cos_altitude) < 1e-9:
        return altitude, 0.0
    cos_azimuth = ((sin_altitude * math.sin(latitude) - math.sin(declination))
                   / (cos_altitude * math.cos(latitude)))
    cos_azimuth = max(-1.0, min(1.0, cos_azimuth))
    azimuth = math.acos(cos_azimuth)
    return altitude, azimuth if solar_hour > 12.0 else -azimuth


def vertical_surface_irradiance(latitude_deg: float, solar_hour: float,
                                surface_azimuth_rad: float) -> tuple[float, float]:
    """``(total incident Btu/h·ft², wall-solar azimuth in radians)`` on a vertical surface.

    ``surface_azimuth_rad`` is the face's outward azimuth from south (:func:`surface_azimuth`).
    Direct + diffuse sky + ground-reflected, the three terms of the ASHRAE clear-sky model
    for a surface tilted 90°::

        E_b = A / exp(B / sin β)                 direct normal
        E_D = E_b cos θ,   cos θ = cos β cos γ   direct on the surface
        E_d = C E_b (1 + cos Σ)/2 = 0.5 C E_b    diffuse sky
        E_r = E_b (C + sin β) ρ (1 − cos Σ)/2    ground-reflected

    The wall-solar azimuth ``γ`` comes back with the total because the overhang shading needs
    it: a shadow line runs ``P tan β / cos γ`` down the glass, and that is not derivable from
    the irradiance alone.
    """
    altitude, azimuth = solar_position(latitude_deg, solar_hour)
    sin_altitude = math.sin(altitude)
    wall_solar_azimuth = azimuth - surface_azimuth_rad
    if sin_altitude <= 0.01:
        return 0.0, wall_solar_azimuth
    direct_normal = JULY_A / math.exp(JULY_B / sin_altitude)
    cos_incidence = math.cos(altitude) * math.cos(wall_solar_azimuth)
    direct = direct_normal * cos_incidence if cos_incidence > 0 else 0.0
    diffuse = JULY_C * direct_normal * 0.5
    reflected = direct_normal * (JULY_C + sin_altitude) * _GROUND_REFLECTANCE * 0.5
    return direct + diffuse + reflected, wall_solar_azimuth


def direct_on_surface(altitude: float, wall_solar_azimuth: float) -> float:
    """The direct-beam share of a vertical surface's incident total, Btu/h·ft²."""
    sin_altitude = math.sin(altitude)
    if sin_altitude <= 0.01:
        return 0.0
    cos_incidence = math.cos(altitude) * math.cos(wall_solar_azimuth)
    if cos_incidence <= 0:
        return 0.0
    return (JULY_A / math.exp(JULY_B / sin_altitude)) * cos_incidence


def horizontal_surface_irradiance(latitude_deg: float, solar_hour: float) -> float:
    """Total clear-sky irradiance on a HORIZONTAL surface, Btu/h·ft².

    Direct (``E_b sin β``) plus the whole sky's diffuse (``C E_b``, undiminished — a
    horizontal surface sees all of it) and no ground reflection, because a roof sees no
    ground.
    """
    altitude, _ = solar_position(latitude_deg, solar_hour)
    sin_altitude = math.sin(altitude)
    if sin_altitude <= 0.01:
        return 0.0
    direct_normal = JULY_A / math.exp(JULY_B / sin_altitude)
    return direct_normal * sin_altitude + JULY_C * direct_normal
