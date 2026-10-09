"""Independent arithmetic from catlin's canopy_garage_diaphragm.md §5a (the column) and
canopy_west_band.md §5 (its head and base, both directions)."""

import pytest


def test_wet_southern_pine_column_stability() -> None:
    from typehaus.engineering.wood_roof_post import column_stability

    fce, cp = column_stability(74.125, 525.0 * 1.15)
    assert fce == pytest.approx(1990, rel=0.001)
    assert cp == pytest.approx(0.927, abs=0.001)
    assert 525.0 * 1.15 * cp * 5.5 ** 2 == pytest.approx(16937, rel=0.002)


def test_east_wood_post_carries_roof_and_owns_its_connections(catlin_ctx) -> None:
    from typehaus.engineering.item import Status

    record = catlin_ctx.engineering["wood_roof_post/PT-BW-RE"]
    assert record.status is Status.OK
    inputs = {value.name: value.value for value in record.inputs}
    assert inputs["roof_tributary_ft2"] == pytest.approx(40.0)
    assert inputs["post_length_in"] == pytest.approx(74.125)
    assert inputs["axial_lb"] == pytest.approx(3397, rel=0.001)
    assert inputs["uplift_lb"] == pytest.approx(428.93, abs=0.1)
    states = {state.name: state for state in record.limit_states}
    assert states["NDS wet-service axial"].ratio == pytest.approx(0.201, abs=0.001)
    assert states["NDS combined axial and bending"].ratio == pytest.approx(0.225, abs=0.001)
    assert states["ACE6Z head uplift"].capacity == 1950
    assert states["ACE6Z head, uplift + lateral along the beam"].ratio == pytest.approx(
        0.233, abs=0.001)
    # A cast-in base carries its own anchorage: no ACI Ch. 17 row stands in for it.
    assert not any("anchor tension" in name for name in states)


def test_the_open_front_now_computes_its_chord_force(catlin_ctx) -> None:
    """canopy_west_band.md §6: the pinned canopy's chord force is M / W', graded."""
    record = catlin_ctx.engineering["lateral_system/RF-BW-CANOPY"]
    values = {value.name: value.value for value in record.inputs}
    assert values["chord_force_open_front_lb"] == pytest.approx(86.7, abs=0.1)
    assert not any("computes no chord force" in note for note in record.notes)
