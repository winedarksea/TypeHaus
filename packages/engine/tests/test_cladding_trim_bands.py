"""The +17'-4" BBD75 band: one Transition Trim per N/S wall segment, at the joint."""

from typehaus.quantities import M_PER_IN


def test_every_bbd75_wall_carries_a_transition_trim_at_the_band(catlin_model):
    bands = [s for s in catlin_model.solids
             if s.category == "cladding_trim" and s.product == "BBD_TRANSITION"]
    assert bands
    assert {s.host_ref[:3] for s in bands} == {"W-S"}
    for s in bands:
        assert s.z0_m / M_PER_IN < 208 < s.z1_m / M_PER_IN
        assert 0 < s.trim_length_m <= s.trim_stock_length_in * M_PER_IN + 1e-9
