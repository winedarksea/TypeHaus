"""`notes/north_entry_piers.md` reproduced by hand — the oracle for `engineering/roof_beam.py`.

A calc that only agrees with itself is not verified. Every number below is worked here from
the note's own inputs, in this file, WITHOUT calling the module it checks; the module's
output is then compared against it. Where the two disagree, one of them is wrong and the
note is the one a person can argue with.

Follows `tests/test_pier_calcs.py`, which does the same job for the sunken garden.
"""

import math

import pytest
from _helpers import CATLIN


@pytest.fixture(scope="module")
def catlin_engineering(catlin_plan):
    """The engineering results WITH the house's preferences — `roof_beam` needs them."""
    from typehaus.checks.run import build_context

    ctx, _ = build_context(catlin_plan, CATLIN)
    return ctx


# --- §1 geometry, straight off the note --------------------------------------------------
_SPAN_FT = 5.719          # header bearing to bearing, 5'-8 5/8"
_CANOPY_AREA_FT2 = 160.0  # 26.667 x 6.000, the overhang-expanded plan footprint
_BEARING_LINES = 2

# --- §3 the design snow, ASCE 7-16 §7.7 --------------------------------------------------
_GROUND_SNOW_PSF = 50.0
_ROOF_STEP_FETCH_FT = 36.0   # l_u, the house roof upwind of the step
_DEAD_PSF = 10.0

# --- §5 section and material -------------------------------------------------------------
_PLIES = 3
_PLY_WIDTH_IN = 1.5
_DEPTH_IN = 11.25
_FB_PSI = 875.0          # SYP No. 2, NDS Supplement Table 4B
_FV_PSI = 175.0
_E_PSI = 1_400_000.0
_CD_SNOW = 1.15          # NDS Table 2.3.2
_CM_BENDING = 0.85       # NDS Table 4.3.8, wet service
_CM_SHEAR = 0.97
_CM_MODULUS = 0.90


def _snow_density_pcf(ground_psf: float) -> float:
    """ASCE 7-16 Eq. 7.7-1: gamma = 0.13 p_g + 14, capped at 30 pcf."""
    return min(0.13 * ground_psf + 14.0, 30.0)


def _drift_height_ft(fetch_ft: float, ground_psf: float) -> float:
    """ASCE 7-16 Fig. 7.6-1 leeward drift: h_d = 0.43 l_u^(1/3) (p_g + 10)^(1/4) - 1.5."""
    return 0.43 * fetch_ft ** (1 / 3) * (ground_psf + 10.0) ** 0.25 - 1.5


def test_the_drift_case_is_what_the_note_says_and_it_governs():
    """§3. The load is AUTHORED, so this is the one section worth checking hardest."""
    gamma = _snow_density_pcf(_GROUND_SNOW_PSF)
    assert gamma == pytest.approx(20.5, abs=0.05)

    # C_t = 1.2 for an unheated open canopy, C_e = I_s = 1.0.
    balanced = 0.7 * 1.0 * 1.2 * 1.0 * _GROUND_SNOW_PSF
    assert balanced == pytest.approx(42.0, abs=0.05)

    drift_h = _drift_height_ft(_ROOF_STEP_FETCH_FT, _GROUND_SNOW_PSF)
    assert drift_h == pytest.approx(2.45, abs=0.02)

    # The windward case is 3/4 of the same formula on the 25 ft across the passage, and it
    # does not govern -- stated so the choice is visible, not assumed.
    windward = 0.75 * (0.43 * 25.0 ** (1 / 3) * (_GROUND_SNOW_PSF + 10.0) ** 0.25 - 1.5)
    assert windward == pytest.approx(1.50, abs=0.03)
    assert windward < drift_h

    surcharge_at_wall = drift_h * gamma
    width = 4.0 * drift_h
    assert surcharge_at_wall == pytest.approx(50.3, abs=0.3)
    assert width == pytest.approx(9.8, abs=0.1)
    assert balanced + surcharge_at_wall == pytest.approx(92.0, abs=0.5)

    # ** THE TRIANGLE IS LONGER THAN THE PASSAGE. ** It runs 9.8 ft from the house wall and
    # the canopy is 6 ft deep, so the remaining 3.8 ft lands on the garage roof: its two
    # southernmost trusses are drift trusses. Pinned here so a canopy resize cannot quietly
    # move the fabricator's scope without this failing.
    canopy_south_ft, canopy_north_ft = 37.22, 43.22
    house_wall_ft = 36.604
    assert width > (canopy_north_ft - house_wall_ft)

    def surcharge_at(y_ft: float) -> float:
        return surcharge_at_wall * max(0.0, 1.0 - (y_ft - house_wall_ft) / width)

    south, north = surcharge_at(canopy_south_ft), surcharge_at(canopy_north_ft)
    assert south == pytest.approx(47.1, abs=0.4)
    assert north == pytest.approx(16.3, abs=0.4)
    average = (south + north) / 2.0
    assert balanced + average == pytest.approx(73.7, abs=0.5)


def test_the_house_authors_the_number_this_note_derives(catlin_engineering):
    """The engine reads the design load from the house and derives NO part of it."""
    structural = catlin_engineering.preferences.structural
    assert structural.roof_beam_snow_psf == pytest.approx(73.7)
    assert structural.roof_beam_dead_psf == pytest.approx(10.0)


def test_the_header_is_a_three_ply_2x12_and_bending_governs():
    """§5, worked here from first principles and compared to the module below."""
    total_psf = 73.7 + _DEAD_PSF
    tributary = _CANOPY_AREA_FT2 / _BEARING_LINES
    assert tributary == pytest.approx(80.0)

    w_plf = tributary * total_psf / _SPAN_FT
    assert w_plf == pytest.approx(1170.9, abs=2.0)

    moment = w_plf * _SPAN_FT ** 2 / 8.0
    shear = w_plf * _SPAN_FT / 2.0
    assert moment == pytest.approx(4787.0, abs=10.0)
    assert shear == pytest.approx(3348.0, abs=10.0)

    width_in = _PLIES * _PLY_WIDTH_IN
    section_modulus = width_in * _DEPTH_IN ** 2 / 6.0
    inertia = width_in * _DEPTH_IN ** 3 / 12.0
    assert section_modulus == pytest.approx(94.9, abs=0.1)
    assert inertia == pytest.approx(533.9, abs=0.5)

    # ** NO C_r. ** NDS Sec 4.3.9 wants members SPACED under 24" and joined by a
    # load-distributing element; a built-up beam's plies are in contact and share load
    # through their nails. Claiming it would buy 15% the section has not got.
    fb_allow = _FB_PSI * _CD_SNOW * _CM_BENDING
    moment_capacity = fb_allow * section_modulus / 12.0
    assert moment_capacity == pytest.approx(6766.0, abs=10.0)
    assert moment / moment_capacity == pytest.approx(0.71, abs=0.01)

    shear_stress = 1.5 * shear / (width_in * _DEPTH_IN)
    assert shear_stress / (_FV_PSI * _CD_SNOW * _CM_SHEAR) == pytest.approx(0.51, abs=0.01)

    w_live_in = (tributary * 73.7 / _SPAN_FT) / 12.0
    span_in = _SPAN_FT * 12.0
    deflection = 5.0 * w_live_in * span_in ** 4 / (384.0 * _E_PSI * _CM_MODULUS * inertia)
    assert deflection == pytest.approx(0.0369, abs=0.001)
    assert deflection / (span_in / 240.0) == pytest.approx(0.13, abs=0.01)


def test_ply_count_is_the_lever_and_two_plies_would_not_do():
    """§5's claim, checked rather than asserted: a 2-ply 2x12 is over in bending."""
    w_plf = (_CANOPY_AREA_FT2 / _BEARING_LINES) * (73.7 + _DEAD_PSF) / _SPAN_FT
    moment = w_plf * _SPAN_FT ** 2 / 8.0
    fb_allow = _FB_PSI * _CD_SNOW * _CM_BENDING
    for plies, depth_in, expected_over in ((2, 11.25, True), (2, 9.25, True), (3, 11.25, False)):
        capacity = fb_allow * (plies * _PLY_WIDTH_IN * depth_in ** 2 / 6.0) / 12.0
        assert (moment > capacity) is expected_over, (plies, depth_in)


def test_uplift_is_not_a_governing_case():
    """§4. Stated in the note as a number, so it is checked as one."""
    q_h_psf = 16.4
    net_uplift_psf = 1.3 * q_h_psf
    per_header_lb = net_uplift_psf * (_CANOPY_AREA_FT2 / _BEARING_LINES)
    dead_per_header_lb = _DEAD_PSF * (_CANOPY_AREA_FT2 / _BEARING_LINES)
    assert per_header_lb == pytest.approx(1706.0, abs=10.0)
    assert dead_per_header_lb == pytest.approx(800.0, abs=1.0)
    per_column = (0.6 * per_header_lb - 0.6 * dead_per_header_lb) / 2.0
    assert per_column == pytest.approx(272.0, abs=10.0)
    assert per_column < 1000.0, "an ABU66SS on a 5/8 in cast-in bolt covers this"


def test_the_pier_cage_is_the_aci_minimum_and_slenderness_must_be_computed():
    """§6. The cage is a detailing floor, not a load answer -- the note says so, so pin it."""
    gross_area = math.pi * (12.0 / 2.0) ** 2
    assert gross_area == pytest.approx(113.10, abs=0.05)
    assert 0.01 * gross_area == pytest.approx(1.131, abs=0.002)
    provided = 4 * 0.31            # (4) #5
    assert provided == pytest.approx(1.24)
    assert provided > 0.01 * gross_area
    assert provided / gross_area == pytest.approx(0.01096, abs=0.0001)
    # ACI 318-19 Sec 25.7.2.2: least of 16 db, 48 dt, h.
    assert min(16 * 0.625, 48 * 0.375, 12.0) == pytest.approx(10.0)

    unbraced_in = 92.0
    slenderness = 1.0 * unbraced_in / (0.25 * 12.0)
    assert slenderness == pytest.approx(30.7, abs=0.2)
    assert slenderness > 22.0, "past Sec 6.2.5's non-sway floor, so it is COMPUTED not neglected"
    e_c = 57000.0 * math.sqrt(5000.0)
    inertia_g = math.pi * 12.0 ** 4 / 64.0
    p_c = math.pi ** 2 * (0.4 * e_c * inertia_g / 1.6) / unbraced_in ** 2
    assert p_c / 1000.0 == pytest.approx(1196.0, rel=0.02)
    magnifier = 1.0 / (1.0 - 7765.0 / (0.75 * p_c))
    assert magnifier == pytest.approx(1.01, abs=0.01)


def test_the_footing_is_sized_for_the_load_and_the_retired_pad_was_not():
    """§6. 2'-0" square, and the reason the retired 1.78 ft2 pad does not cover it."""
    service_lb = 5283.0
    required_ft2 = service_lb / 2000.0
    assert required_ft2 == pytest.approx(2.64, abs=0.02)
    assert 2.0 ** 2 >= required_ft2
    assert 1.78 < required_ft2, "the retired PR-BW-* pad, and why it could not be reused"
    assert required_ft2 / 4.0 == pytest.approx(0.66, abs=0.02)


def test_the_module_agrees_with_this_note(catlin_engineering):
    """The comparison the whole file exists for: the encoded calc against the hand pass."""
    results = catlin_engineering.engineering
    records = {results[item].key: results[item] for item in results
               if item.startswith("roof_beam/")}
    assert set(records) == {"BM-BW-RW", "BM-BW-RE"}
    for record in records.values():
        states = {state.name: state for state in record.limit_states}
        assert set(states) == {"bending", "shear", "deflection"}
        assert states["bending"].demand == pytest.approx(4787.0, abs=15.0)
        assert states["bending"].capacity == pytest.approx(6766.0, abs=15.0)
        assert states["bending"].ratio == pytest.approx(0.71, abs=0.01)
        assert states["shear"].ratio == pytest.approx(0.51, abs=0.01)
        assert states["deflection"].ratio == pytest.approx(0.13, abs=0.01)
        assert max(s.ratio for s in states.values()) == states["bending"].ratio
