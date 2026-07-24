"""WP1 — lumber/engineered-member catalog: every profile string used in the repo
today parses into a sane cross-section, and the parser never mutates the string
(structural checks and ``haus ls`` key on it verbatim)."""

from __future__ import annotations

import pytest

from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import (
    RIDGE_BEAM_DEFAULT,
    cross_section,
    panel_profile,
)
from typehaus.resolve.framing.tables import LUMBER_ACTUAL


@pytest.mark.parametrize("nominal", list(LUMBER_ACTUAL))
def test_nominal_lumber_matches_tables_actuals(nominal):
    thickness_in, depth_in = LUMBER_ACTUAL[nominal]
    section = cross_section(nominal)
    assert section.shape == "rect"
    assert section.width_m == pytest.approx(inch(thickness_in).meters)
    assert section.depth_m == pytest.approx(inch(depth_in).meters)
    assert section.plies == 1


@pytest.mark.parametrize("profile,plies,depth_in", [
    ("2-2x6", 2, 5.5), ("2-2x8", 2, 7.25), ("2-2x10", 2, 9.25), ("2-2x12", 2, 11.25),
])
def test_multi_ply_nominal_header(profile, plies, depth_in):
    section = cross_section(profile)
    assert section.shape == "rect"
    assert section.plies == plies
    assert section.width_m == pytest.approx(inch(1.5 * plies).meters)
    assert section.depth_m == pytest.approx(inch(depth_in).meters)


@pytest.mark.parametrize("profile,depth_in,flange_width_in", [
    ("9.5 I-joist", 9.5, 2.5),
    ("11.875 I-joist", 11.875, 2.5),
    ("14 I-joist", 14.0, 3.5),
    ("16 I-joist", 16.0, 3.5),
])
def test_i_joist_series(profile, depth_in, flange_width_in):
    section = cross_section(profile)
    assert section.shape == "i_joist"
    assert section.depth_m == pytest.approx(inch(depth_in).meters)
    assert section.width_m == pytest.approx(inch(flange_width_in).meters)
    assert section.flange_width_m == pytest.approx(inch(flange_width_in).meters)
    assert section.flange_thickness_m == pytest.approx(inch(1.375).meters)
    assert section.web_thickness_m == pytest.approx(inch(0.375).meters)


@pytest.mark.parametrize("profile,width_in,depth_in", [
    ("3.5x11.875 LVL", 3.5, 11.875),  # Beam default (structure.py)
    ("5.5x11.875 LVL", 5.5, 11.875),  # authored catlin RB-HOUSE size (pre-WP4)
])
def test_single_ply_lvl(profile, width_in, depth_in):
    section = cross_section(profile)
    assert section.shape == "rect"
    assert section.plies == 1
    assert section.width_m == pytest.approx(inch(width_in).meters)
    assert section.depth_m == pytest.approx(inch(depth_in).meters)


def test_multi_ply_lvl_ridge_beam_default():
    section = cross_section(RIDGE_BEAM_DEFAULT)
    assert RIDGE_BEAM_DEFAULT == "3-1.75x11.875 LVL"
    assert section.shape == "rect"
    assert section.plies == 3
    assert section.width_m == pytest.approx(0.13335, abs=1e-5)
    assert section.depth_m == pytest.approx(0.3016, abs=1e-4)


def test_rim_board():
    section = cross_section("1.25x11.875 rim")
    assert section.shape == "rect"
    assert section.plies == 1
    assert section.width_m == pytest.approx(inch(1.25).meters)
    assert section.depth_m == pytest.approx(inch(11.875).meters)


def test_panel_sheet_good():
    """Sheet goods (soffit panels, heel/gable closure bands) carry arbitrary dimensions."""
    section = cross_section(panel_profile(13.625, 0.5))
    assert section.shape == "rect"
    assert section.plies == 1
    assert section.width_m == pytest.approx(inch(13.625).meters)
    assert section.depth_m == pytest.approx(inch(0.5).meters)


def test_engineered_lvl_fallback_is_sane():
    section = cross_section("engineered-LVL")
    assert section.shape == "rect"
    assert section.width_m > 0 and section.depth_m > 0


def test_unknown_profile_falls_back_safely():
    section = cross_section("mystery-material")
    assert section.shape == "rect"
    assert section.width_m == pytest.approx(inch(1.5).meters)
    assert section.depth_m == pytest.approx(inch(5.5).meters)
