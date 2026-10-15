"""A physical beam tail must not move its roof or truss bearing run."""

from types import SimpleNamespace

import pytest

from typehaus import Beam, ft
from typehaus.resolve.roof_bearing import roof_bearing


@pytest.mark.parametrize("axis", [((0, 0), (3, 4)), ((3, 4), (0, 0))])
def test_roof_bearing_insets_follow_the_authored_axis(monkeypatch, axis):
    from typehaus.resolve import roof_bearing as module

    beam = Beam(uid="TESTBEAM01", tag="BM", start_node="A", end_node="B",
                top_elevation=ft(8), roof_bearing_insets=(ft(1), ft(2)))
    model = SimpleNamespace(wall=lambda _: None,
                            plan=SimpleNamespace(by_tag=lambda _: beam))
    monkeypatch.setattr(module, "_beam_axis", lambda *_: axis)
    bearing = roof_bearing(model, "BM")
    assert bearing is not None
    (x0, y0), (x1, y1) = axis
    ux, uy = (x1 - x0) / 5, (y1 - y0) / 5
    assert bearing.axis[0] == pytest.approx((x0 + ux * ft(1).meters,
                                           y0 + uy * ft(1).meters))
    assert bearing.axis[1] == pytest.approx((x1 - ux * ft(2).meters,
                                           y1 - uy * ft(2).meters))
    assert bearing.z1_m == ft(8).meters


@pytest.mark.parametrize("insets", [(ft(-1), ft(0)), (ft(0), ft(-1)),
                                   (ft(10), ft(10)), (ft(11), ft(0))])
def test_invalid_roof_bearing_run_cannot_resolve(monkeypatch, insets):
    from typehaus.resolve import roof_bearing as module

    beam = Beam(uid="TESTBEAM01", tag="BM", start_node="A", end_node="B",
                top_elevation=ft(8), roof_bearing_insets=insets)
    model = SimpleNamespace(wall=lambda _: None,
                            plan=SimpleNamespace(by_tag=lambda _: beam))
    monkeypatch.setattr(module, "_beam_axis", lambda *_: ((0, 0), (ft(10).meters, 0)))
    assert roof_bearing(model, "BM") is None


def test_sawn_simple_span_rule_refuses_an_inset_load_run():
    from typehaus.engineering.item import Status
    from typehaus.engineering.roof_beam import _one

    beam = Beam(uid="TESTBEAM01", tag="BM", start_node="A", end_node="B", size="2-2x12",
                roof_bearing_insets=(ft(1), ft(0)))
    record = _one(None, SimpleNamespace(tag="RF"), beam, 80, 6)
    assert record.status is Status.INCOMPLETE
    assert record.missing == ("an inset-load envelope for a sawn roof beam",)
