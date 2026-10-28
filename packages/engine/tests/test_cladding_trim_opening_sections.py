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


def test_site_brake_girth_and_bends_match_the_hand_brake_gate():
    from typehaus.resolve.cladding_trim.openings import brake_girth_and_bends

    # PBR jamb: 1.0 lap + 1.25 reveal + 1.645 inboard leg; two bends.
    girth, bends = brake_girth_and_bends(window_jamb_section(1.25, 0.645).points_in)
    assert girth == pytest.approx(3.895, abs=0.01) and bends == 2
    # PBR sill: 0.425 upstand + 1.25 top + 0.5 drip + 0.25 hem; three bends.
    girth, bends = brake_girth_and_bends(window_sill_section(1.25, 0.55).points_in)
    assert girth == pytest.approx(2.43, abs=0.01) and bends == 3


def test_stock_pbr_jamb_leg_clears_the_rib_and_laps_the_frame():
    from typehaus.library.trim.metal_sales import PBR_WINDOW_JAMB

    points = PBR_WINDOW_JAMB.section_in
    reveal_leg = points[1][1]
    flange = points[-1][0]
    assert reveal_leg >= 1.25                  # PBR rib depth
    assert flange - 0.645 >= 0                 # inboard flange reaches the frame face
    assert PBR_WINDOW_JAMB.receiver_throat_in == reveal_leg
    assert PBR_WINDOW_JAMB.part_numbers[0][3] == "58208XX"
