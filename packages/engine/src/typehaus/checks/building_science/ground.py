"""Below-grade heat loss: the soil is part of the assembly, not a boundary condition.

Oracled by ``houses/catlin/notes/block_load_basis.md`` §§1-3; the constants in
``tests/test_energy_ground.py`` are read off that note.

Three published methods, one per below-grade surface, and the reason there are three is that
a below-grade surface does not have a single ΔT or a single R-value:

* **A basement wall** loses heat along a path through the soil that lengthens with depth.
  Latta & Boileau's result (ASHRAE Fundamentals Ch. 18, "Heat loss below grade") is that the
  path length at depth *z* is ``π z / 2``, so the conductance there is
  ``U(z) = 1 / (R_assembly + π z / 2 k)``. Averaged over the buried depth *D* that
  integrates in closed form to ``(2k / πD) · ln(1 + πD / 2 k R)``.
* **A basement floor** is the bottom of the same path, and the dominant resistance is the
  soil itself: the shortest way out is up and sideways to the nearest exterior wall, so the
  answer depends on the floor's *shortest plan dimension* and its depth, not on its area.
* **A slab on grade** does not have an area term at all. Its loss is around its edge, which
  is why every code and standard publishes it as an **F-factor: Btu/h per linear foot of
  exposed perimeter per °F**, against the outdoor design *air*. An uninsulated slab's edge
  is 3 1/2" of concrete to the weather, and there is no soil path to speak of.

What the block load did before all of this was ``(A / R) · (T_in − soil_temp_f)`` for both
the wall and the floor — two errors fighting, the ΔT one winning. It **understated** a
basement wall about 1.5× (no depth resistance, but a 23 °F ΔT where the ground surface sees
45) and **overstated** a basement floor about 2× (R-21.7 where the soil adds R-25 more).
A slab on grade came out ~2× low insulated and ~10× low uninsulated, because an area term
with a soil ΔT is not the quantity the loss is proportional to.

**The ground design temperature is derived, not authored.** ``Site.soil_temp_f`` is the
annual *mean*, which is the right boundary for an annual energy model and the wrong one for
a 99% design hour: the ground surface swings about that mean by an amplitude the climate
publishes, and the heating design hour sits at the bottom of the swing. So
``T_ground_design = annual_mean − amplitude``, where the annual mean comes off
``Site.monthly_normals`` (the twelve figures a house already authors for the condensation
gate) and the amplitude is one new authored field read off one published map.
"""

from __future__ import annotations

import math

# Thermal conductivity of soil, Btu/h·ft·°F. ASHRAE Fundamentals Ch. 18's value for the
# below-grade method, and the one Latta & Boileau's charts are drawn at. Not authored per
# house: it is the constant the *method* is calibrated with, and a house that knows its own
# soil conductivity would need a different set of charts, not a different number here.
SOIL_CONDUCTIVITY_BTU_PER_HR_FT_F = 0.8


def annual_mean_outdoor_f(monthly_normals) -> float | None:
    """Mean annual outdoor dry-bulb from the twelve published monthly normals.

    ``None`` where a house authors none. Deliberately the plain twelve-month mean rather
    than a day-weighted one: the normals are themselves monthly means of a 30-year record
    and the month-length weighting moves the answer by under 0.05 °F.
    """
    temps = [normal.temp_f for normal in monthly_normals]
    if not temps:
        return None
    return sum(temps) / len(temps)


def ground_design_temp_f(
    monthly_normals, amplitude_f: float | None,
) -> tuple[float | None, str | None]:
    """``(design ground-surface temperature °F, the gap that stopped it)``.

    ``annual_mean − amplitude``. The amplitude is ASHRAE Fundamentals Ch. 18 Fig. 13's
    ground-surface temperature amplitude map — 22 °F for the North Central US — and is
    authored on ``Site`` beside ``ground_snow_load_psf`` because it is the same class of
    fact: one figure read off one published map for this location.
    """
    mean = annual_mean_outdoor_f(monthly_normals)
    if mean is None:
        return None, "Site.monthly_normals (the annual mean the ground temperature derives from)"
    if amplitude_f is None:
        return None, "Site.ground_surface_amplitude_f (ASHRAE Ch. 18 Fig. 13)"
    return mean - amplitude_f, None


def ground_summer_temp_f(
    monthly_normals, amplitude_f: float | None,
) -> tuple[float | None, str | None]:
    """The other end of the same swing, for the cooling season: ``annual_mean + amplitude``.

    Reported rather than assumed zero because a house in a hot climate really does gain
    through its basement wall, and the block load must not be the reason nobody notices.
    """
    mean = annual_mean_outdoor_f(monthly_normals)
    if mean is None or amplitude_f is None:
        return ground_design_temp_f(monthly_normals, amplitude_f)
    return mean + amplitude_f, None


def basement_wall_u_avg(r_assembly: float, depth_ft: float) -> float:
    """Depth-averaged conductance of a basement wall, Btu/h·ft²·°F (Latta & Boileau).

    ``U(z) = 1 / (R + π z / 2 k)`` averaged over ``0..D``::

        U_avg = (2 k / π D) · ln(1 + π D / (2 k R))

    Verified in the oracle note: catlin's R-21.7 wall buried 6.29 ft gives 0.0365
    (R_eff 27.4), against the 1/21.7 = 0.0461 the bare assembly would claim and the R-76 a
    misplaced π produces.

    ``depth_ft <= 0`` returns the bare assembly conductance — a wall with nothing buried has
    no soil in its path — so a caller need not special-case an above-grade band.
    """
    if r_assembly <= 0:
        raise ValueError("r_assembly must be > 0")
    if depth_ft <= 0:
        return 1.0 / r_assembly
    k = SOIL_CONDUCTIVITY_BTU_PER_HR_FT_F
    return ((2 * k) / (math.pi * depth_ft)) * math.log(
        1 + (math.pi * depth_ft) / (2 * k * r_assembly))


def basement_floor_u(r_assembly: float, short_dimension_ft: float,
                     depth_ft: float) -> float:
    """Conductance of a below-grade floor, Btu/h·ft²·°F (ASHRAE Fundamentals Ch. 18)::

        U = (2 k / π w) · ln( (w/2 + z/2 + k R / π) / (z/2 + k R / π) )

    ``w`` is the floor's **shortest plan dimension** and ``z`` its depth below grade. Both
    are there because the heat leaves sideways: a wide floor's middle is further from the
    exterior than a narrow one's, so it loses less per square foot, and a deeper floor is
    further still. The soil is most of the resistance — catlin's basement floor comes out
    near R-47 over an R-10 assembly — which is why billing it at ``A / R_assembly`` against
    a soil ΔT overstated it about 2×.

    An uninsulated floor is legitimate here: with ``r_assembly = 0`` the soil alone still
    gives R-35 at catlin's dimensions.
    """
    if short_dimension_ft <= 0:
        raise ValueError("short_dimension_ft must be > 0")
    if r_assembly < 0 or depth_ft < 0:
        raise ValueError("r_assembly and depth_ft must be >= 0")
    k = SOIL_CONDUCTIVITY_BTU_PER_HR_FT_F
    soil_r = k * r_assembly / math.pi
    near = depth_ft / 2 + soil_r
    if near <= 0:
        # A bare floor at grade: the formula's inner path length collapses to zero and the
        # loss is an edge loss, which is what ``slab_on_grade_q`` is for.
        raise ValueError("a floor at grade with no assembly R is a slab on grade")
    far = short_dimension_ft / 2 + near
    return ((2 * k) / (math.pi * short_dimension_ft)) * math.log(far / near)


# ASHRAE 90.1 Appendix A Table A6.3 / IECC Table R402.1.4's F-factors for an unheated
# slab on grade, Btu/h per linear foot of exposed perimeter per °F. TWO ROWS ONLY, and
# deliberately not interpolated: these are published values for two constructions, not
# samples of a curve, and a house whose slab edge is neither gets an UNKNOWN naming the gap
# rather than a number nobody published. (A *heated* slab has its own rows and is not
# modelled: no element here carries slab-embedded heat as a boundary condition.)
_UNHEATED_SLAB_F_FACTORS = ((0.0, 0.73), (10.0, 0.54))
# How far down or out the R-10 row's insulation has to run to be the construction the row
# was measured at, in inches. 90.1 states it as "R-10 for 24 in.".
SLAB_EDGE_INSULATION_REACH_IN = 24.0


def slab_on_grade_f_factor(edge_r: float | None) -> tuple[float | None, str | None]:
    """``(F-factor, the gap that stopped it)`` for an unheated slab on grade.

    ``edge_r`` is the R-value of the slab-edge insulation, ``None`` where the model does not
    say. Only the two published constructions answer; anything between them is named.
    """
    if edge_r is None:
        return None, "slab-edge insulation R-value (ASHRAE 90.1 Table A6.3 F-factor)"
    for r_row, f_factor in _UNHEATED_SLAB_F_FACTORS:
        if abs(edge_r - r_row) < 0.5:
            return f_factor, None
    return None, (f"slab-edge R-{edge_r:.0f} is neither published unheated-slab row "
                  "(R-0 or R-10 for 24 in.) — ASHRAE 90.1 Table A6.3 states no F-factor "
                  "for it")


def slab_on_grade_q(perimeter_ft: float, f_factor: float, air_delta_f: float) -> float:
    """Slab-on-grade heat loss, Btu/h. **Perimeter, not area**, against the outdoor design
    *air*, not the soil: the F-factor is defined that way because the loss is at the edge.
    """
    return perimeter_ft * f_factor * air_delta_f
