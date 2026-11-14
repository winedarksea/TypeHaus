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


def _tji() -> _Floor:
    """An 11 7/8" TJI (2 1/2" x 1 3/8" flanges): web window 1.375 .. 10.5 above its bottom."""
    floor = _Floor(tag="FS-TJI", across="y", kind="i_joist",
                   window=(1.375 * M_PER_IN, 10.5 * M_PER_IN))
    floor.joists = [(y * M_PER_IN, -10.0, 10.0, 0.0, 11.875 * M_PER_IN) for y in (16, 32)]
    floor.stations = [j[0] for j in floor.joists]
    floor.half_widths = [1.25 * M_PER_IN] * 2
    return floor


@pytest.mark.parametrize(("z_in", "expected"),
                         [(5.9, {"unpublished": 2}), (1.5, None), (10.4, None)])
def test_an_ijoist_is_bored_through_its_web_and_never_its_flanges(z_in, expected) -> None:
    """A 1/2" PEX envelope (r 0.3125") crosses at mid-web; its edge in a flange is refused.
    No lattice prism stands in the web: a body prism would hard-block every web bore."""
    cuts = _cuts(0.3125, floors=[_tji()]).cuts(_p(0, 8, z_in), _p(0, 40, z_in), "y")
    assert cuts == expected


@pytest.mark.parametrize(("y_in", "legal"), [(17.5, False), (17.6, True)])
def test_a_riser_clears_an_ijoist_by_its_flange_half_width(y_in, legal) -> None:
    """1.25 + 0.3125 = 1.5625" off the line: 1.5" is through the flange, 1.6" clear."""
    cuts = _cuts(0.3125, floors=[_tji()]).cuts(_p(0, y_in, -12), _p(0, y_in, 24), "z")
    assert (cuts is not None) is legal


def _strongback_floor() -> _Floor:
    """§15: a 2x6 on edge (plan 1 1/2", D 5 1/2") along y at x = 100", y 0..108", z 0..5 1/2"."""
    from typehaus.routing.floor_bars import Bar, FloorBars

    floor = _floor()
    floor.bars = FloorBars([Bar("y", 100 * M_PER_IN, 0.0, 108 * M_PER_IN, 0.75 * M_PER_IN,
                                0.0, 5.5 * M_PER_IN, "2x6", "FS-ORACLE strongback-1-1")])
    return floor


@pytest.mark.parametrize(("radius_in", "expected"),
                         [(0.83, {"joist": 1}), (0.95, None), (1.1875, None)])
def test_a_strongback_is_bored_to_d_over_three_across_the_joists(radius_in, expected) -> None:
    """§15: D/3 = 5.5/3 = 1.833". 1 1/4" PVC (1.660" OD) passes, 1 1/2" (1.900") and 2"
    (2.375") are refused, as ``mep.run_through_floor_member`` FAILs them."""
    cuts = _cuts(radius_in, floors=[_strongback_floor()])
    assert cuts.cuts(_p(60, 54, 2.75), _p(140, 54, 2.75), "x") == expected


def test_a_lane_over_a_strongback_or_a_riser_through_it() -> None:
    floor = _strongback_floor()
    assert _cuts(1.1875, floors=[floor]).cuts(_p(60, 54, 9), _p(140, 54, 9), "x") == {}
    assert _cuts(0.83, floors=[floor]).cuts(_p(101.5, 54, -4), _p(101.5, 54, 12), "z") is None
    assert _cuts(0.83, floors=[floor]).cuts(_p(102, 54, -4), _p(102, 54, 12), "z") == {}


def test_a_falling_run_passes_over_an_illegal_strongback_in_its_band() -> None:
    from types import SimpleNamespace

    from typehaus.routing.floor_bars import bar_prisms

    cut = _cuts(1.1875, floors=[_strongback_floor()])
    assert cut.cuts(_p(60, 54, 0), _p(140, 54, 0), "x", band=(0.0, 9 * M_PER_IN)) == {}
    space = SimpleNamespace(members=cut, radius_m=1.1875 * M_PER_IN, clearance_m=0.0)
    (prism,) = bar_prisms(space)
    assert prism.z1_m == pytest.approx((5.5 + 1.1875) * M_PER_IN)  # a lane over it is clear
    space.radius_m = 0.83 * M_PER_IN
    assert bar_prisms(space) == []
