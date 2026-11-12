"""``DuctRun.inline_dampers``: a station is developed length along the resolved path."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.resolve.duct_dampers import point_at_station


def test_a_station_walks_the_developed_path_and_refuses_off_the_run() -> None:
    """A level 0.5 m leg then a 0.3 m drop: 0.6 m is 0.1 m down the drop, pointing down;
    the start, the end and beyond are not on the run (``integrity.inline_damper``)."""
    duct = SimpleNamespace(path=((0.0, 0.0), (0.5, 0.0), (0.5, 0.0)), z_m=(2.0, 2.0, 1.7))
    point, axis = point_at_station(duct, 0.6)
    assert point == pytest.approx((0.5, 0.0, 1.9))
    assert axis == pytest.approx((0.0, 0.0, -1.0))
    assert point_at_station(duct, 0.0) is None
    assert point_at_station(duct, 0.8) is None
    assert point_at_station(duct, 1.0) is None
