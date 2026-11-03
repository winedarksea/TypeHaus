"""``routing/members.py`` against ``notes/framing_bore_limits.md`` §10, on hand-built framing."""

from __future__ import annotations

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.routing.cost import RouteCost
from typehaus.routing.members import Penetrations, _Floor, _Wall


def _cuts(radius_in: float, walls=(), floors=()) -> Penetrations:
    out = Penetrations.__new__(Penetrations)
    out.radius_m = out.cavity_radius_m = radius_in * M_PER_IN
    out.walls, out.floors = {}, list(floors)
    for wall in walls:
        for key in range(int((wall.perp[0] - 0.05) / 0.0254),
                         int((wall.perp[1] + 0.05) / 0.0254) + 1):
            out.walls.setdefault((wall.axis, key), []).append(wall)
    return out


def _partition(bearing: bool = False) -> _Wall:
    wall = _Wall(tag="W-ORACLE", axis="x", bearing=bearing, z0=0.0, z1=96 * M_PER_IN,
                 perp=(0.0, 3.5 * M_PER_IN), along=(-4 * M_PER_IN, 64 * M_PER_IN))
    wall.studs = [(x * M_PER_IN, 1.75 * M_PER_IN, 1.75 * M_PER_IN, 96 * M_PER_IN, "2x4", 0.0)
                  for x in (0, 16, 32, 48)]
    wall.stations = [s[0] for s in wall.studs]
    return wall


def _p(x: float, y: float, z: float) -> tuple[float, float, float]:
    return (x * M_PER_IN, y * M_PER_IN, z * M_PER_IN)


def test_a_lane_along_the_cavity_bores_each_stud_it_passes() -> None:
    cuts = _cuts(0.3125, walls=[_partition()]).cuts(_p(8, 1.75, 48), _p(56, 1.75, 48), "x")
    assert cuts == {"stud": 3}
    travel = 48.0
    assert travel + cuts["stud"] * RouteCost().cut_cost("stud") == pytest.approx(84.0)


@pytest.mark.parametrize(("offset_in", "legal"), [(0.8125, True), (1.0, False)])
def test_a_lane_that_leaves_under_five_eighths_of_stud_is_refused(offset_in, legal) -> None:
    y = 1.75 + offset_in
    cuts = _cuts(0.3125, walls=[_partition()]).cuts(_p(8, y, 48), _p(56, y, 48), "x")
    assert (cuts is not None) is legal


def test_a_two_inch_drain_cannot_bore_a_bearing_two_by_four() -> None:
    cuts = _cuts(1.1875, walls=[_partition(bearing=True)])
    assert cuts.cuts(_p(8, 1.75, 48), _p(56, 1.75, 48), "x") is None


def _floor() -> _Floor:
    floor = _Floor(tag="FS-ORACLE", across="y", kind="solid_sawn",
                   window=(2 * M_PER_IN, 7.25 * M_PER_IN))
    floor.joists = [(y * M_PER_IN, -10.0, 10.0, 0.0, 9.25 * M_PER_IN) for y in (16, 32)]
    floor.stations = [j[0] for j in floor.joists]
    floor.profile = "2x10"
    return floor


@pytest.mark.parametrize(("z_in", "expected"), [(4.625, {"joist": 2}), (7.0, None)])
def test_a_floor_crossing_bores_each_joist_inside_its_window(z_in, expected) -> None:
    cuts = _cuts(1.1875, floors=[_floor()]).cuts(_p(0, 8, z_in), _p(0, 40, z_in), "y")
    assert cuts == expected


@pytest.mark.parametrize(("y_in", "legal"), [(1.75, True), (3.0, False), (4.4, True)])
def test_a_riser_in_a_wall_sits_wholly_in_its_cavity_or_clear_of_it(y_in, legal) -> None:
    """§10: 1 1/4" vent, radius 0.83": centred (1.75") fits the 3 1/2" bay; at 3.0" its
    envelope stands 0.33" into the stud plane's face; at 4.4" it is 0.07" clear of it."""
    cuts = _cuts(0.83, walls=[_partition()]).cuts(_p(8, y_in, 24), _p(8, y_in, 72), "z")
    assert (cuts is not None) is legal


@pytest.mark.parametrize(("y_in", "legal"), [(16.0, False), (17.5, False), (24.0, True)])
def test_a_riser_through_a_floor_misses_every_member_line(y_in, legal) -> None:
    """A 2x10 joist (3/4" half-width) at y=16": 1 1/4" vent centred on it or 1 1/2" off
    (0.83 + 0.75 = 1.58") is through it; in the bay at y=24" it is clear."""
    floor = _floor()
    floor.half_widths = [0.75 * M_PER_IN] * len(floor.joists)
    cuts = _cuts(0.83, floors=[floor]).cuts(_p(0, y_in, -12), _p(0, y_in, 24), "z")
    assert (cuts is not None) is legal
