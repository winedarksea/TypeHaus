"""The balcony's loads no tributary carries, against ``notes/balcony_moment_columns.md`` §20-§22.

Pure arithmetic first (the hand numbers are the note's), then the records they reach.
"""

from __future__ import annotations

import math

import pytest

from typehaus.engineering.balcony_loads import (
    PlanterAllowance,
    beam_reactions,
    deck_basis_text,
)
from typehaus.engineering.column_stem import StemDemand, plain_flexure_lb_in, prop_lb, stem_states
from typehaus.engineering.dowel_development import confinement_term, general_development_in
from typehaus.engineering.glulam_beam import bearing_adjustment

#: §20: the house's allowance. 11" x 16" of soil at 120 pcf saturated plus 25 plf of box.
_PLANTER = PlanterAllowance(soil_width_in=11.0, soil_depth_in=16.0, soil_saturated_pcf=120.0,
                            box_and_support_plf=25.0)


def test_the_planter_line_load_is_soil_plus_box() -> None:
    assert _PLANTER.soil_plf == pytest.approx(146.667, abs=0.001)
    assert _PLANTER.plf == pytest.approx(171.667, abs=0.001)


def test_a_beams_statics_do_not_split_its_load_equally() -> None:
    """§20a: 8" south, 88" back span, 20" north, a 9.75' strip. The north (rear) column takes
    more, the south (front) less than the equal split's 471 lb of dead (review B-03)."""
    dead, live, planter = beam_reactions(8 / 12, 88 / 12, 20 / 12, 9.75, _PLANTER.plf)
    assert dead == pytest.approx((406.99, 535.51), abs=0.05)
    assert sum(dead) == pytest.approx(97.5 * (8 + 88 + 20) / 12, abs=0.01)   # nothing lost
    assert live == pytest.approx((1701.82, 2153.86), abs=0.05)
    # The planter sits on the back span alone, so it splits evenly.
    assert planter == pytest.approx((629.44, 629.44), abs=0.01)


def test_the_bearing_adjustment_is_nds_3_10_4() -> None:
    assert bearing_adjustment(3.5, 6.25) == pytest.approx(1.1071, abs=0.0001)
    assert bearing_adjustment(3.0, 6.0) == pytest.approx(1.125)
    assert bearing_adjustment(6.0, 6.0) == 1.0          # 6" or longer: none
    assert bearing_adjustment(3.5, 2.0) == 1.0          # nearer than 3" to the end: none
    assert bearing_adjustment(3.5, None) == 1.0         # end distance unknown: not claimed


def test_dowel_development_on_the_general_equation() -> None:
    """§21: a #5, f'c 5,000, cb 1.90" half spacing, 3.31" cover to centre: 12.7", not the
    simplified row's 21.2"."""
    confinement = confinement_term(3.3125, 1.90, 0.625)
    assert confinement == 2.5                      # 1.90 / 0.625 = 3.04, capped
    ld = general_development_in(0.625, 5000.0, 60_000.0, confinement)
    assert ld == pytest.approx(3 / 40 * 60_000 / math.sqrt(5000) * 0.8 / 2.5 * 0.625, rel=1e-9)
    assert ld == pytest.approx(12.73, abs=0.01)
    assert 1.3 * ld == pytest.approx(16.55, abs=0.01)
    assert general_development_in(0.1, 5000.0, 60_000.0, 2.5) == 12.0     # §25.4.2.1's floor


def test_the_stem_rows_are_the_note_22_hand_numbers() -> None:
    """§22: M_u 4,612 lb-ft, V_u 320 lb, a 109.4" stem: prop = V + 3M/2H."""
    demand = StemDemand("1.2D + 1.0W + L", 4_612.0 * 12.0, 320.0)
    assert prop_lb(demand, 109.4375) == pytest.approx(320.0 + 1.5 * 4_612.0 * 12.0 / 109.4375,
                                                      abs=0.01)
    # Plain concrete, phi 0.60, 5 sqrt(f'c) S over 12 + 2 x 48 = 108" of a 12" stem.
    assert plain_flexure_lb_in(5000.0, 108.0, 12.0) == pytest.approx(
        0.6 * 5 * math.sqrt(5000) * 108 * 144 / 6, rel=1e-12)
    states, inputs, sentence = stem_states(
        tag="PT-X", wall_tag="W-X", fc_psi=5000.0, thickness_in=12.0, height_in=109.4375,
        column_width_in=12.0, embedment_in=48.0, demand=demand)
    below, strut = states
    assert below.capacity == pytest.approx(45_820.5, abs=1.0)          # lb-ft
    assert below.demand == pytest.approx(4_612.0, abs=0.01)
    assert below.ok and strut.ok and "PT-X" in sentence and inputs


def test_the_deck_basis_is_stated_once_with_the_balanced_snow_comparison() -> None:
    from types import SimpleNamespace

    ctx = SimpleNamespace(preferences=SimpleNamespace(structural=SimpleNamespace(
        deck_snow_psf=35.0, deck_balanced_snow_psf=42.0)))
    text = deck_basis_text(ctx)
    for fragment in ("40 psf live + 10 psf dead", "no snow, no drift", "42 psf",
                     "35 psf", "wind-swept", "owner"):
        assert fragment in text
