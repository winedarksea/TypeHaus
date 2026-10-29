"""An EXACT upward-facing port is left vertically before the route turns."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.cli import route_ports
from typehaus.cli.route_ports import attach_leads, stub_length_m, with_port_leads
from typehaus.cli.route_support import Endpoints
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_ports import PlacedPort

ROOT = (2.0, 3.0, 1.5)


def _port(**over):
    base = {"equipment_tag": "EQ-X", "port_tag": "hot", "service": "water_hot",
            "duct_system": None, "x_m": ROOT[0], "y_m": ROOT[1], "z_m": ROOT[2],
            "exact": True, "direction": (0.0, 0.0, 1.0)}
    return PlacedPort(**{**base, **over})


def _ends():
    return Endpoints(origin=(8.0, 3.0, 2.0), root=ROOT, radius_m=0.5 * 25.4e-3,
                     kind="pipe", system="water_hot", storey="basement",
                     diameter_m=25.4e-3, tie_is_the_goal=True)


def _lead(monkeypatch, port):
    monkeypatch.setattr(route_ports, "placed_ports", lambda _model: [port])
    return with_port_leads(SimpleNamespace(), _ends())


def test_upward_port_starts_with_a_vertical_stub(monkeypatch):
    ends = _lead(monkeypatch, _port())
    stub = stub_length_m(ends.radius_m)
    assert stub == pytest.approx(3.0 * M_PER_IN, abs=1e-6)  # 1" pipe + 2" allowance
    assert ends.root == (ROOT[0], ROOT[1], ROOT[2] + stub) and ends.root_lead.port == ROOT
    # Search ran riser -> tip with a turn after the stub; the printed run is reversed.
    found = [ends.origin, (8.0, 3.0, ends.root[2]), ends.root]
    points, notes, bends = attach_leads(found, ends)
    assert points[-1] == ROOT and points[-2] == ends.root and bends == 1
    assert "EQ-X.hot +z" in notes[0]
    assert points[::-1][0] == ROOT  # tie_is_the_goal reverses: the port is the first vertex


def test_stub_tip_that_the_route_continues_through_is_dropped(monkeypatch):
    ends = _lead(monkeypatch, _port())
    points, _notes, bends = attach_leads([(2.0, 3.0, 4.0), ends.root], ends)
    assert points == [(2.0, 3.0, 4.0), ROOT] and bends == 0


@pytest.mark.parametrize("over", [{"exact": False}, {"direction": None},
                                  {"direction": (0.7, 0.0, 0.7)}, {"service": "water_cold"}])
def test_approximate_obliqued_or_foreign_ports_do_not_constrain(monkeypatch, over):
    ends = _lead(monkeypatch, _port(**over))
    assert ends.root == ROOT and ends.root_lead is None
