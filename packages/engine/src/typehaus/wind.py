"""Design wind: the site's basis, and the ASCE 7 velocity pressure derived from it.

``Site`` carries three fields (``design_wind_speed_mph``, ``wind_exposure``,
``risk_category``) and this module is the single place that reads them, so that "what wind
is this house designed for" has one answer and one wording.

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

import math
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


# --- ASCE 7-16 Chapter 30 Part 1: C&C wall pressures -------------------------------------
# Shared by ``checks/structural/girt_fastening.py`` and ``cladding.py``: the panel
# and the screw behind it carry ONE suction, and two numbers for it would mean one is wrong.

#: ASCE 7-16 Table 26.13-1, enclosed building, applied with the sign that worsens the case.
GC_PI = 0.18

#: ASCE 7-16 Fig. 30.3-1, walls of an enclosed low-rise building, GC_p at the two ends of
#: the figure's log axis (10 and 500 ft2). Zone 5 = corner, Zone 4 = field.
_GCP_WALL_NEGATIVE = {
    "5": ((10.0, -1.4), (500.0, -0.8)),
    "4": ((10.0, -1.1), (500.0, -0.8)),
}
#: Fig. 30.3-1 positive (inward) GC_p: one curve for both zones.
_GCP_WALL_POSITIVE = {
    "5": ((10.0, 1.0), (500.0, 0.7)),
    "4": ((10.0, 1.0), (500.0, 0.7)),
}


def external_pressure_coefficient(area_ft2: float, zone: str = "5", *,
                                  sign: str = "negative") -> float:
    """Wall GC_p, log-interpolated across Fig. 30.3-1, held flat outside 10-500 ft2."""
    table = _GCP_WALL_POSITIVE if sign == "positive" else _GCP_WALL_NEGATIVE
    (small_area, small), (large_area, large) = table[zone]
    if area_ft2 <= small_area:
        return small
    if area_ft2 >= large_area:
        return large
    fraction = (math.log10(area_ft2) - math.log10(small_area)) / (
        math.log10(large_area) - math.log10(small_area))
    return small + fraction * (large - small)


def effective_wind_area_ft2(span_in: float) -> float:
    """ASCE 7-16 §26.2: span x effective width, the width not less than span/3.

    ``span/3`` is the SMALLER area and so the more severe GC_p; at every girt spacing on
    this house it lands under 10 ft2, where the figure is flat.
    """
    span_ft = span_in / 12.0
    return span_ft * (span_ft / 3.0)


#: How far from the building a spot elevation may stand and still be the ground its walls
#: stand beside. ASCE 7-16 §26.2 measures the mean roof height above the ground at the
#: building, so a far-off low spot (a neighbour's swale, a pond) is not it. 30 ft is a stated
#: judgement, about the building's own eave height and a court's width; a station beyond it
#: is ignored. Catlin's sunken-court floor stations are 20 ft off its south wall.
ADJACENT_GROUND_FT = 30.0


def footprint_bounds_m(model) -> tuple[float, float, float, float] | None:
    """(x0, x1, y0, y1) of the above-grade wall axes, metres, or ``None`` with no walls."""
    xs: list[float] = []
    ys: list[float] = []
    for wall in getattr(model, "walls", ()):
        if getattr(wall, "is_foundation", False):
            continue
        for x, y in wall.axis:
            xs.append(x)
            ys.append(y)
    return (min(xs), max(xs), min(ys), max(ys)) if xs else None


def lowest_ground_ft(site, footprint: tuple[float, float, float, float] | None = None) -> float:
    """Lowest ground adjacent to the building, ft in the main-floor-datum frame.

    The minimum of the site grade and every spot elevation within :data:`ADJACENT_GROUND_FT`
    of ``footprint`` (all of them when it is ``None``). z in ASCE 7's K_z is height above the
    ground *there*, and a sunken court shortens z if the grade is used instead — the wrong
    direction to be wrong in. A ``kind="structure"`` station (a court floor) counts: it is the
    ground the court-facing wall stands on. The same rule as ``engineering/balcony_wind``'s
    ``ground_below_ft``, less its reach past the site. No grade and no spots: the datum (0.0).
    """
    limit_m = ADJACENT_GROUND_FT * 0.3048
    candidates = []
    for spot in getattr(site, "spot_elevations", ()):
        if footprint is not None:
            x0, x1, y0, y1 = footprint
            px, py = spot.position.x.meters, spot.position.y.meters
            reach = math.hypot(max(x0 - px, 0.0, px - x1), max(y0 - py, 0.0, py - y1))
            if reach > limit_m:
                continue
        candidates.append(spot.elevation.meters)
    grade = getattr(site, "grade", None)
    if grade is not None:
        candidates.append(grade.meters)
    return min(candidates) / 0.3048 if candidates else 0.0


def mean_roof_height_ft(model) -> float | None:
    """h for q_h: mean of eave and ridge over the tallest roof, above the lowest ground.

    The model has no building grouping to ask, so the tallest roof is the conservative
    reading. ``roof.eave_z_m`` / ``ridge_z_m`` are main-floor-datum heights, so the lowest
    adjacent ground (:func:`lowest_ground_ft`) is taken off; catlin's is the sunken court,
    -9.12 ft, which governs conservatively.
    """
    heights = [(roof.eave_z_m + roof.ridge_z_m) / 2.0 for roof in model.roofs
               if roof.eave_z_m is not None and roof.ridge_z_m is not None]
    if not heights:
        return None
    ground = lowest_ground_ft(model.plan.project.site, footprint_bounds_m(model))
    return max(heights) / 0.3048 - ground


def cladding_pressure_asd_psf(q_h: float, area_ft2: float, zone: str = "5", *,
                              sign: str = "negative") -> tuple[float, float]:
    """(strength, ASD) wall C&C pressure magnitude, ``|q_h (GC_p -/+ GC_pi)|`` and 0.6x.

    GC_pi takes the sign that adds to the external coefficient: suction with internal
    pressure, inward push with internal suction.
    """
    gcp = external_pressure_coefficient(area_ft2, zone, sign=sign)
    strength = q_h * (abs(gcp) + GC_PI)
    return strength, ASD_WIND_FACTOR * strength
