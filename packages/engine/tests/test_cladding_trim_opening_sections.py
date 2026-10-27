"""Window-first trim section contracts against the documented reveal."""

import pytest

from typehaus.resolve.cladding_trim.openings import window_jamb_section, window_sill_section


@pytest.mark.parametrize("reveal", [0.75, 0.875, 1.25])
def test_jamb_covers_buck_and_laps_frame_for_each_panel(reveal):
    section = window_jamb_section(reveal, 0.645)
    assert section.receiver_depth_in == reveal
    assert section.points_in[-1] == (1.645, 0)
    assert section.frame_lap_in >= 0.75


def test_sill_slopes_out_and_stays_below_unit():
    section = window_sill_section(1.25, 0.55)
    assert section.points_in[0] == (0, 0.42500000000000004)
    assert section.points_in[2][1] < section.points_in[1][1]
    assert section.points_in[3][1] == pytest.approx(section.points_in[2][1] - 0.5)


def test_sill_rejects_upstand_that_reaches_unit():
    with pytest.raises(ValueError):
        window_sill_section(1.25, 0.125)
