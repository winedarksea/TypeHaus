"""WP1 — lumber/engineered-member catalog: every profile string used in the repo
today parses into a sane cross-section, and the parser never mutates the string
(structural checks and ``haus ls`` key on it verbatim)."""

from __future__ import annotations

import math

import pytest

from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import (
    FLAT_LAID_TOLERANCE_M,
    RIDGE_BEAM_DEFAULT,
    cross_section,
    panel_profile,
    plan_cross_section_m,
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
    assert RIDGE_BEAM_DEFAULT == "2-1.75x14 LVL"
    assert section.shape == "rect"
    assert section.plies == 2
    assert section.width_m == pytest.approx(inch(3.5).meters, abs=1e-5)
    assert section.depth_m == pytest.approx(inch(14).meters, abs=1e-5)


def test_the_default_ridge_backs_an_i_joist_rafters_plumb_cut():
    """The depth is a hanger dimension, and this is the arithmetic that sets it.

    An 11 7/8" I-joist at 4:12 is cut PLUMB at the beam face, and the hanger's seat is at the
    bottom of that cut. 11.875 x hypot(1, 4/12) = 12.52", and the face sits half a beam width
    off the peak, another half-width x 4/12 down the plane. The old 3-1.75x11.875 default
    missed by an inch and a half and nothing noticed for a year.
    """
    section = cross_section(RIDGE_BEAM_DEFAULT)
    slope_factor = math.hypot(1.0, 4.0 / 12.0)
    plumb_in = 11.875 * slope_factor
    face_drop_in = (section.width_m / inch(1).meters / 2.0) * (4.0 / 12.0)
    assert plumb_in == pytest.approx(12.517, abs=1e-3)
    assert section.depth_m / inch(1).meters >= plumb_in + face_drop_in


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


def test_a_member_standing_its_own_thickness_tall_lies_on_its_wide_face():
    """A 2x6 plate/sill/block is 1.5" tall, so a plan cut sees its 5.5" face."""
    section = cross_section("2x6")
    assert plan_cross_section_m(section, section.width_m) == pytest.approx(section.depth_m)


def test_a_member_standing_its_own_depth_tall_shows_its_thin_face():
    """A 2x6 header/joist on edge is 5.5" tall, so a plan cut sees its 1.5" face."""
    section = cross_section("2x6")
    assert plan_cross_section_m(section, section.depth_m) == pytest.approx(section.width_m)


def test_an_extent_matching_neither_face_keeps_the_on_edge_default():
    """A seat cut, a tapered gable band: no constant section to read, so do not guess."""
    section = cross_section("2x6")
    odd = (section.width_m + section.depth_m) / 2
    assert plan_cross_section_m(section, odd) == pytest.approx(section.width_m)


def test_the_flat_test_tolerates_only_a_hair():
    """Wide enough for float noise, far narrower than the 0.021 m gap to the nearest
    on-edge member in either house — the margin the rule relies on to stay unambiguous."""
    section = cross_section("2x6")
    just_inside = section.width_m + FLAT_LAID_TOLERANCE_M * 0.9
    just_outside = section.width_m + FLAT_LAID_TOLERANCE_M * 1.1
    assert plan_cross_section_m(section, just_inside) == pytest.approx(section.depth_m)
    assert plan_cross_section_m(section, just_outside) == pytest.approx(section.width_m)


def test_lsl_is_its_own_family_and_does_not_fall_through_to_the_stud_fallback():
    """An LSL rim board is not a spelling of LVL and not a nominal size. Before it had a
    pattern, "1.75x11.875 LSL" hit the rectangular fallback and silently came back
    1 1/2" x 5 1/2" — a rim under a bearing line, drawn and billed as a stud."""
    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.quantities import inch

    section = cross_section("1.75x11.875 LSL")
    assert section.width_m == pytest.approx(inch(1.75).meters)
    assert section.depth_m == pytest.approx(inch(11.875).meters)
    assert section.plies == 1

    two_ply = cross_section("2-1.75x11.875 LSL")
    assert two_ply.width_m == pytest.approx(inch(3.5).meters)
    assert two_ply.plies == 2
