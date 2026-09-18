"""Below-grade heat loss, against ``houses/catlin/notes/block_load_basis.md``.

Every constant here is read off that note, section by section:

* **§1** — the ground design temperature is DERIVED (``annual_mean − amplitude``), and the
  annual mean derived from ``Site.monthly_normals`` reproduces the house's hand-computed
  ``soil_temp_f`` as a free self-check.
* **§2** — Latta & Boileau's depth-averaged basement-wall conductance, including the two
  misplaced-π forms the note names as the errors to watch for.
* **§3** — the below-grade floor, where the soil is four fifths of the resistance, and the
  slab-on-grade F-factor that is a different quantity entirely.

These are pure-function tests. The catlin figures they land on are pinned in
``test_energy_envelope_scope.py``, which walks the real house.
"""

from __future__ import annotations

import math

import pytest

from typehaus.checks.building_science.ground import (
    SOIL_CONDUCTIVITY_BTU_PER_HR_FT_F,
    annual_mean_outdoor_f,
    basement_floor_u,
    basement_wall_u_avg,
    ground_design_temp_f,
    ground_summer_temp_f,
    slab_on_grade_f_factor,
    slab_on_grade_q,
)
from typehaus.model import MonthlyNormal

# --- the note's own inputs -----------------------------------------------------------------

# MSP 1991-2020 monthly TAVG normals, January..December (§1). The same twelve figures
# ``houses/catlin/plan/site.py`` authors.
_MSP_TAVG_F = (16.2, 20.6, 33.3, 47.1, 59.5, 69.7, 74.3, 71.8, 63.5, 49.5, 34.8, 22.0)
_MSP_NORMALS = tuple(MonthlyNormal(temp_f=temp, rh=60.0) for temp in _MSP_TAVG_F)
# ASHRAE Fundamentals Ch. 18 Fig. 13, North Central US.
_AMPLITUDE_F = 22.0
# §1's derived figures.
_ANNUAL_MEAN_F = 46.858
_GROUND_DESIGN_F = 24.858
# §2's worked wall: W-B-E1.
_WALL_R = 21.8
_WALL_DEPTH_FT = 6.12
_WALL_U_AVG = 0.03653
# §3's worked floor: SL-B-FLOOR.
_FLOOR_R = 11.13
_FLOOR_SHORT_FT = 36.0
_FLOOR_DEPTH_FT = 6.286
_FLOOR_U = 0.0196524


# --- §1. the ground design temperature -----------------------------------------------------

def test_the_annual_mean_reproduces_the_houses_hand_computed_soil_temp() -> None:
    """§1. ``plan/site.py`` authors ``soil_temp_f=47.0`` and says it is the annual mean of
    the twelve normals beside it. Two independent statements of one fact; if this ever
    stops agreeing, one of them is wrong and the engine now says so."""
    assert annual_mean_outdoor_f(_MSP_NORMALS) == pytest.approx(_ANNUAL_MEAN_F, abs=0.001)
    assert round(annual_mean_outdoor_f(_MSP_NORMALS)) == 47


def test_a_house_with_no_normals_derives_no_ground_temperature() -> None:
    """Named and dropped, never guessed. Fails if a default annual mean appears."""
    assert annual_mean_outdoor_f(()) is None
    temp, gap = ground_design_temp_f((), _AMPLITUDE_F)
    assert temp is None and gap is not None and "monthly_normals" in gap


def test_a_house_with_normals_but_no_amplitude_names_the_map_it_wants() -> None:
    """The amplitude is one published figure, like the ground snow load. Without it there
    is no design ground temperature — not a zero swing, which would put the annual mean
    back and re-open the 23 °F ΔT this pass closed."""
    temp, gap = ground_design_temp_f(_MSP_NORMALS, None)
    assert temp is None
    assert gap is not None and "ground_surface_amplitude_f" in gap


def test_the_design_hour_sits_at_the_bottom_of_the_swing() -> None:
    """§1. 24.9 °F, so a 70 °F interior sees 45 °F — not the 23 °F an annual mean gives.

    The single most consequential number in this pass: it nearly doubles every below-grade
    surface's ΔT. Fails if anyone puts ``Site.soil_temp_f`` back in the ΔT.
    """
    temp, gap = ground_design_temp_f(_MSP_NORMALS, _AMPLITUDE_F)
    assert gap is None
    assert temp == pytest.approx(_GROUND_DESIGN_F, abs=0.001)
    assert 70.0 - temp == pytest.approx(45.14, abs=0.01)


def test_the_summer_end_of_the_swing_gives_a_basement_no_cooling_load() -> None:
    """The other end: 68.9 °F against a 75 °F cooling setpoint is a NEGATIVE ΔT, so a
    below-grade surface gains nothing in July. The old code charged it the 20 °F air ΔT,
    which is a basement heating the house in summer."""
    temp, gap = ground_summer_temp_f(_MSP_NORMALS, _AMPLITUDE_F)
    assert gap is None
    assert temp == pytest.approx(_ANNUAL_MEAN_F + _AMPLITUDE_F, abs=0.001)
    assert max(0.0, temp - 75.0) == 0.0


# --- §2. the basement wall ------------------------------------------------------------------

def test_the_latta_integral_gives_the_notes_worked_wall() -> None:
    """§2's hand pass on ``W-B-E1``: R-21.8 buried 6.12 ft is R_eff 27.4, not R-21.8.

    The soil adds R-5.6. Fails if the below-grade band is billed at ``1 / R_assembly``.
    """
    u_avg = basement_wall_u_avg(_WALL_R, _WALL_DEPTH_FT)
    assert u_avg == pytest.approx(_WALL_U_AVG, abs=0.00001)
    assert 1 / u_avg == pytest.approx(27.4, abs=0.05)


def test_the_closed_form_matches_a_numeric_integration_of_the_same_relation() -> None:
    """The algebra, independently. ``U_avg = (2k/πD)·ln(1 + πD/2kR)`` is the closed form of
    the average of ``U(z) = 1/(R + πz/2k)`` over ``0..D``; a midpoint sum over 10,000 slices
    must land on it. This is the test that would have caught either misplaced π."""
    k = SOIL_CONDUCTIVITY_BTU_PER_HR_FT_F
    slices = 10_000
    step = _WALL_DEPTH_FT / slices
    numeric = sum(
        1.0 / (_WALL_R + math.pi * (index + 0.5) * step / (2 * k))
        for index in range(slices)
    ) / slices
    assert basement_wall_u_avg(_WALL_R, _WALL_DEPTH_FT) == pytest.approx(numeric, rel=1e-6)


def test_the_two_misplaced_pi_forms_are_not_what_is_implemented() -> None:
    """§2 names both, because both were live errors in drafts: ``z/2k`` (π dropped) gives
    R-23.7 where the right form gives R-27.4, and ``π/(2kz)`` gives R-76. The first is
    close enough to the truth to pass unnoticed by eye, which is why it is pinned."""
    k = SOIL_CONDUCTIVITY_BTU_PER_HR_FT_F
    pi_dropped = ((2 * k) / _WALL_DEPTH_FT) * math.log(
        1 + _WALL_DEPTH_FT / (2 * k * _WALL_R))
    assert 1 / pi_dropped == pytest.approx(23.66, abs=0.05)
    assert basement_wall_u_avg(_WALL_R, _WALL_DEPTH_FT) != pytest.approx(pi_dropped, rel=0.01)
    # And the absurd form, kept as a gate on the magnitude rather than on the algebra.
    assert 1 / basement_wall_u_avg(_WALL_R, _WALL_DEPTH_FT) < 40


def test_a_deeper_wall_loses_less_per_square_foot() -> None:
    """Monotone in depth, because the soil path lengthens. Not a tautology of the formula:
    it is the property that makes a walkout's shallow band the expensive one."""
    shallow = basement_wall_u_avg(_WALL_R, 2.0)
    deep = basement_wall_u_avg(_WALL_R, 9.0)
    assert deep < shallow < 1 / _WALL_R


def test_nothing_buried_is_the_bare_assembly() -> None:
    """A wall standing wholly above its local grade has no soil in its path, so the caller
    need not special-case the above-grade band to avoid a divide-by-zero."""
    assert basement_wall_u_avg(_WALL_R, 0.0) == pytest.approx(1 / _WALL_R)
    assert basement_wall_u_avg(_WALL_R, -1.0) == pytest.approx(1 / _WALL_R)


def test_a_zero_r_assembly_is_refused_rather_than_divided_by() -> None:
    with pytest.raises(ValueError, match="r_assembly"):
        basement_wall_u_avg(0.0, _WALL_DEPTH_FT)


# --- §3. the basement floor and the slab on grade -------------------------------------------

def test_the_below_grade_floor_gives_the_notes_worked_slab() -> None:
    """§3's hand pass on ``SL-B-FLOOR``: R-11.1 of assembly becomes R-50.9 in the ground.

    The soil is four fifths of the resistance. Fails if the floor is billed at
    ``A / R_assembly``, which overstated this one about 2× — UA 116 against UA 25.5.
    """
    u_value = basement_floor_u(_FLOOR_R, _FLOOR_SHORT_FT, _FLOOR_DEPTH_FT)
    assert u_value == pytest.approx(_FLOOR_U, abs=0.000005)
    assert 1 / u_value == pytest.approx(50.88, abs=0.05)


def test_the_floor_reads_its_SHORT_dimension_and_its_depth() -> None:
    """Both terms earn their place: heat leaves a basement floor sideways, so a wider floor
    loses less per square foot and a deeper one loses less still. A floor billed on AREA
    would be monotone the other way."""
    narrow = basement_floor_u(_FLOOR_R, 12.0, _FLOOR_DEPTH_FT)
    wide = basement_floor_u(_FLOOR_R, 60.0, _FLOOR_DEPTH_FT)
    assert wide < narrow
    shallow = basement_floor_u(_FLOOR_R, _FLOOR_SHORT_FT, 1.0)
    deep = basement_floor_u(_FLOOR_R, _FLOOR_SHORT_FT, 12.0)
    assert deep < shallow


def test_an_uninsulated_below_grade_floor_still_has_the_soil() -> None:
    """R-0 of assembly is not U-infinity: at catlin's dimensions the ground alone is R-37.
    The number a reviewer should refuse is a bare slab reported as a hole in the envelope."""
    bare = basement_floor_u(0.0, _FLOOR_SHORT_FT, _FLOOR_DEPTH_FT)
    assert 1 / bare == pytest.approx(37.08, abs=0.05)


def test_a_slab_on_grade_is_a_perimeter_not_an_area() -> None:
    """§3. An F-factor is Btu/h per LINEAR FOOT per °F against outdoor design AIR. An
    uninsulated 120 ft perimeter at 85 °F ΔT is 7,446 Btu/h — which is why reading it as an
    area against a soil ΔT came out about 10× low."""
    assert slab_on_grade_q(120.0, 0.73, 85.0) == pytest.approx(7446.0, abs=1.0)


def test_only_the_two_published_slab_rows_answer() -> None:
    """ASHRAE 90.1 Table A6.3 publishes two unheated-slab constructions, not a curve. An
    edge R nobody published is a NAMED GAP, never an interpolation."""
    assert slab_on_grade_f_factor(0.0) == (0.73, None)
    assert slab_on_grade_f_factor(10.0) == (0.54, None)
    factor, gap = slab_on_grade_f_factor(5.0)
    assert factor is None and gap is not None and "neither published" in gap
    factor, gap = slab_on_grade_f_factor(None)
    assert factor is None and gap is not None and "F-factor" in gap
