"""The ColorGard wedge integral against its hand oracle.

``houses/catlin/notes/s5_snow_retention_review.md`` "Final clamp check" works the drift
triangle over the 45-degree wedge in closed form: 10,061.96 lb vertical, 3,181.87 lbf drag.
"""

import pytest

from typehaus.checks.structural.snow_retention import DriftTriangle, SnowWedge, wedge_drag_lbf


def test_catlin_canopy_wedge_drag_matches_the_hand_integral():
    rail_low = 37 + 10.25 / 12
    wedge = SnowWedge(rail_low=rail_low, rail_high=rail_low + 62.375 / 12,
                      run_low=37.21875, run_high=68.55208, upslope_ft=13.0, slope=4 / 12)
    drift = DriftTriangle(balanced_psf=42.0, surcharge_psf=50.3, width_ft=9.8,
                          sign=1.0, origin_ft=37.21875)
    drag, vertical = wedge_drag_lbf(wedge, drift)
    assert vertical == pytest.approx(10061.96, abs=0.01)
    assert drag == pytest.approx(3181.87, abs=0.01)
    assert drag / (4 * 863.0) == pytest.approx(0.922, abs=5e-4)
