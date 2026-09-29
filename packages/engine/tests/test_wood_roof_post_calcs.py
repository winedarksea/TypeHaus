"""Independent arithmetic from catlin's canopy_garage_diaphragm.md §5a."""

import pytest


def test_wet_southern_pine_column_stability() -> None:
    from typehaus.engineering.wood_roof_post import column_stability

    fce, cp = column_stability(74.75, 525.0 * 1.15)
    assert fce == pytest.approx(1958, rel=0.001)
    assert cp == pytest.approx(0.926, abs=0.001)
    assert 525.0 * 1.15 * cp * 5.5 ** 2 == pytest.approx(16910, rel=0.002)


def test_east_wood_post_carries_roof_and_owns_its_connections(catlin_ctx) -> None:
    from typehaus.engineering.item import Status

    record = catlin_ctx.engineering["wood_roof_post/PT-BW-RE"]
    assert record.status is Status.OK
    inputs = {value.name: value.value for value in record.inputs}
    assert inputs["roof_tributary_ft2"] == pytest.approx(40.0)
    assert inputs["post_length_in"] == pytest.approx(74.75)
    assert inputs["axial_lb"] == pytest.approx(3397, rel=0.001)
    assert inputs["uplift_lb"] == pytest.approx(433.25, abs=0.1)
    states = {state.name: state for state in record.limit_states}
    assert states["NDS wet-service axial"].ratio == pytest.approx(0.201, abs=0.001)
    assert states["NDS combined axial and own drag"].ratio == pytest.approx(0.226, abs=0.001)
    assert states["CCQ46SDS2.5 head uplift"].capacity == 6785
    assert states["ABU66SS base uplift"].capacity == 2190
    anchor = states["PT-BW-RE base anchor tension (breakout / pullout / steel)"]
    assert anchor.ratio == pytest.approx(0.159, abs=0.001)
