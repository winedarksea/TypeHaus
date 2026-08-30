"""Design wind: the site's basis, and the ASCE 7 velocity pressure derived from it.

Until 2026-08-30 no part of this model carried a design wind speed, and half a dozen
docstrings and finding messages said so in their own words. ``Site`` now carries three
fields (``design_wind_speed_mph``, ``wind_exposure``, ``risk_category``) and this module is
the single place that reads them, so that "what wind is this house designed for" has one
answer and one wording.

**Carrying a wind speed is not the same as having computed a load**, and the distinction is
the whole reason this module is small. A connector-coverage check still cannot say a joint
is adequate: it now knows V but not the tributary area, the force coefficient, or the load
path share. What changed is the *reason* it cannot — from "the model has no wind speed at
all" to "the model has a wind speed and this check does not compute a demand from it" —
and those are different sentences to a reader deciding what work is left.

``velocity_pressure`` is ASCE 7-16 §26.10 and is the one piece of real arithmetic here. It
is oracled in ``tests/test_wind_loads.py`` against the hand-worked numbers in
``houses/catlin/notes/catlin_truss_engineering.md`` §2, which were computed independently
of this code and are the reference this file must reproduce.
"""

from __future__ import annotations

from dataclasses import dataclass

#: ASCE 7-16 Table 26.6-1, directionality factor for buildings' MWFRS and C&C, and for
#: solid freestanding walls and solid signs. 0.85 in every one of those rows.
K_D_BUILDINGS = 0.85
#: ASCE 7-16 §26.8.2: K_zt = 1.0 where none of the three topographic conditions of §26.8.1
#: is met. MN Rules 1309.0301's Table R301.2(1) answers "topographic effects: YES", meaning
#: they must be *considered*, not that they apply — a flat suburban parcel considers them
#: and gets 1.0.
K_ZT_FLAT = 1.0
#: ASCE 7-16 §2.4.1 load combination 5/6: wind acts at 0.6W in allowable-stress design.
#: Every capacity number this house cites (NDS, ICC-ES, IAPMO UES) is an ASD allowable, so
#: demand has to be brought to the same basis before the two are compared.
ASD_WIND_FACTOR = 0.6


@dataclass(frozen=True)
class WindBasis:
    """The site's design wind, complete enough to compute a velocity pressure from."""

    speed_mph: float
    exposure: str      # "B" | "C" | "D"
    risk_category: str  # "I" | "II" | "III" | "IV"

    def describe(self) -> str:
        return (f"V_ult = {self.speed_mph:.0f} mph, Exposure {self.exposure}, "
                f"Risk Category {self.risk_category}")


def wind_basis(site) -> WindBasis | None:
    """The site's wind basis, or ``None`` when it is not fully authored.

    Partial is treated as absent on purpose. A speed without an exposure cannot produce a
    K_z and therefore cannot produce a pressure, and silently defaulting the missing half
    (to C "because it is conservative", to II "because most things are") would put an
    assumed number into a calculation a reader would then read as sourced.
    """
    speed = getattr(site, "design_wind_speed_mph", None)
    exposure = getattr(site, "wind_exposure", None)
    risk = getattr(site, "risk_category", None)
    if speed is None or exposure is None or risk is None:
        return None
    return WindBasis(speed_mph=float(speed), exposure=exposure, risk_category=risk)


def capacity_caveat(site) -> str:
    """Why a coverage check still is not a capacity check, in this site's terms.

    Shared by ``checks/structural/uplift_path.py`` and ``checks/mep/deck_equipment.py`` so
    the two cannot drift into saying different things about the same model.
    """
    basis = wind_basis(site)
    if basis is None:
        return ("this model carries no design wind speed, so the capacity of the connection "
                "is not evaluated")
    return (f"this model carries a design wind ({basis.describe()}) but this check derives "
            f"no demand from it — no tributary area, force coefficient or load-path share "
            f"is computed here — so the capacity of the connection is not evaluated")


# --- ASCE 7-16 §26.10 velocity pressure ------------------------------------------------

#: ASCE 7-16 Table 26.10-1, exposure constants for the power-law K_z. z_g is the gradient
#: height in feet, alpha the exponent. Values are the standard's, transcribed, not fitted.
_EXPOSURE_CONSTANTS = {
    "B": (1200.0, 7.0),
    "C": (900.0, 9.5),
    "D": (700.0, 11.5),
}
#: Table 26.10-1 note 1 / §26.10.1: below 15 ft, Exposure B's K_z is held at its 15-ft value
#: for Case 2 (C&C and the low-rise MWFRS envelope procedure). Exposures C and D evaluate the
#: power law all the way down to their own 15-ft floor.
_MIN_HEIGHT_FT = {"B": 15.0, "C": 15.0, "D": 15.0}


def velocity_pressure_coefficient(height_ft: float, exposure: str) -> float:
    """K_z (or K_h at the mean roof height), ASCE 7-16 Table 26.10-1.

    ``K_z = 2.01 (z / z_g) ** (2 / alpha)``, with z floored at the exposure's minimum
    height. Raises on an unknown exposure rather than defaulting — an exposure this table
    does not have is a modelling error, not a case to guess through.
    """
    if exposure not in _EXPOSURE_CONSTANTS:
        raise ValueError(f"no ASCE 7-16 Table 26.10-1 row for exposure {exposure!r}")
    z_g, alpha = _EXPOSURE_CONSTANTS[exposure]
    z = max(float(height_ft), _MIN_HEIGHT_FT[exposure])
    return 2.01 * (z / z_g) ** (2.0 / alpha)


def velocity_pressure_psf(basis: WindBasis, height_ft: float, *,
                          k_zt: float = K_ZT_FLAT, k_d: float = K_D_BUILDINGS) -> float:
    """q_z in psf at ``height_ft``, ASCE 7-16 eq. 26.10-1 (strength level).

    ``q_z = 0.00256 · K_z · K_zt · K_d · K_e · V²``. K_e (ground elevation factor,
    Table 26.9-1) is taken as 1.0: §26.9 permits it for all elevations, and at this site's
    830 ft the tabulated value is 0.97, so 1.0 is the conservative side of a 3 % effect.
    """
    k_z = velocity_pressure_coefficient(height_ft, basis.exposure)
    return 0.00256 * k_z * k_zt * k_d * basis.speed_mph ** 2
