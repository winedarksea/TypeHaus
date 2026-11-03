"""§8 of `houses/catlin/notes/mep_drain_routing_basis.md`, reproduced numerically.

Two paths, one world, and a quarter of an inch. The cheap path is cheap because it rides a
bay; it is also 4 ft longer, and 4 ft of 1/4"/ft is exactly enough head to put it under the
truss web it has to pass through. Every number below is read off the note.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.routing.cost import RouteCost
from typehaus.routing.graph import Graph, Node
from typehaus.routing.gravity_search import (
    GravityProblem,
    GravityRefusal,
    sloped_route,
)
from typehaus.routing.search import shortest_route
from typehaus.routing.space import RoutingSpace

STEP = 24.0 * M_PER_IN

#: §8's four numbers, in inches.
CEILING_IN = 116.50
GRADE_IN_PER_FT = 0.25
REQUIRED_IN = 114.00
WINDOW_IN = (115.50, 116.50)


def _world() -> tuple[Graph, RoutingSpace]:
    """§8's two rows of four, with the upper row priced as a corridor at zero.

    Built by hand rather than derived, for §4's reason: this is a statement about the
    SEARCH, and handing it the lattice is what makes the arithmetic checkable.
    """
    coords = [(i * STEP, j * STEP) for j in range(2) for i in range(4)]
    nodes = [Node(index=k, x=x, y=y, z=0.0) for k, (x, y) in enumerate(coords)]
    # §8 prices every turn at 6", the level-to-level sweeps included.
    cost = RouteCost(bend_in=6.0, dwv_sweep_in=6.0, corridor_discount_per_ft=8.0)
    space = RoutingSpace(radius_m=0.0, clearance_m=0.0, cost=cost, hard=[], soft=[],
                         corridors=[], bbox=(0.0, 0.0, 3 * STEP, STEP),
                         storeys=("main",))
    graph = Graph(nodes=nodes)
    # The upper row (E-F-G-H) rides a bay: 24" of travel less 2 ft x 8"/ft of discount is
    # 8" an edge. B-C crosses a bedroom and pays 24" of room penalty on top of its travel.
    # Everything else is its own 24". The cheapest inch is therefore 1 - 8/12 = 1/3, which
    # is what `heuristic_floor()` returns and what keeps the A* heuristic admissible here —
    # priced any cheaper than the cost function admits and A* stops being optimal without
    # saying so, which is the failure this lattice would otherwise demonstrate by accident.
    bay = {(4, 5), (5, 6), (6, 7)}
    for a in nodes:
        for b in nodes:
            if b.index <= a.index:
                continue
            dx, dy = abs(b.x - a.x), abs(b.y - a.y)
            if abs(dx + dy - STEP) > 1e-9:
                continue
            axis = "x" if dx > dy else "y"
            weight = (8.0 if (a.index, b.index) in bay
                      else 48.0 if (a.index, b.index) == (1, 2) else 24.0)
            graph.edges.setdefault(a.index, {}).setdefault(axis, []).append(b.index)
            graph.edges.setdefault(b.index, {}).setdefault(axis, []).append(a.index)
            graph.weights[(a.index, b.index)] = weight
            graph.weights[(b.index, a.index)] = weight
            graph.terms[(a.index, b.index)] = {"travel_in": weight}
            graph.terms[(b.index, a.index)] = {"travel_in": weight}
    return graph, space


def _problem() -> GravityProblem:
    return GravityProblem(ceiling_m=CEILING_IN * M_PER_IN,
                          grade_in_per_ft=GRADE_IN_PER_FT, diameter_m=0.0,
                          required_m={3: REQUIRED_IN * M_PER_IN})


def _truss(a: int, b: int) -> list[tuple[float, float, float]]:
    """`FS-ORACLE` crosses the bay at the middle of edge F-G, and nowhere else."""
    if {a, b} == {5, 6}:
        return [(0.5, WINDOW_IN[0] * M_PER_IN, WINDOW_IN[1] * M_PER_IN)]
    return []


def test_the_plain_search_takes_the_cheap_lane_and_is_right_to() -> None:
    """L costs 84 against S's 96, and everything about that answer is correct as far as a
    search that does not know the elevation can see."""
    graph, space = _world()
    route = shortest_route(graph, space, 0, {3})
    assert route is not None
    assert route.nodes == [0, 4, 5, 6, 7, 3]
    assert route.cost == pytest.approx(84.0)
    assert route.bends == 2


def test_the_sloped_search_takes_the_dearer_lane_because_the_cheap_one_hits_a_truss(
) -> None:
    """§8's whole point. S is 12" of equivalent travel dearer and is the only one of the
    two that can be built."""
    graph, space = _world()
    route = sloped_route(graph, space, 0, {3}, _problem(), constraints=_truss)
    assert route is not None
    assert route.nodes == [0, 1, 2, 3]
    assert route.cost == pytest.approx(96.0)
    assert route.bends == 0


def test_the_long_lane_passes_a_head_budget_taken_at_the_GOAL() -> None:
    """Which is why the test has to be taken at the crossing. 10.00 ft x 0.25 = 2.50", so L
    arrives at exactly 114.00" — the tie, to the inch — and a post-check would pass it."""
    problem = _problem()
    at_goal = problem.invert_at(10.0) / M_PER_IN
    assert at_goal == pytest.approx(REQUIRED_IN)


def test_the_long_lane_is_a_quarter_inch_under_the_web_at_the_crossing() -> None:
    """5.00 ft developed at the middle of F-G, 1.25" of fall, 115.25" against the window's
    115.50" floor."""
    problem = _problem()
    at_truss = problem.invert_at(5.0) / M_PER_IN
    assert at_truss == pytest.approx(115.25)
    assert WINDOW_IN[0] - at_truss == pytest.approx(0.25)


def test_with_no_truss_in_the_way_the_cheap_lane_wins_again() -> None:
    """The constraint is doing the work, not the search preferring short routes."""
    graph, space = _world()
    route = sloped_route(graph, space, 0, {3}, _problem())
    assert route is not None
    assert route.nodes == [0, 4, 5, 6, 7, 3]


def test_a_tie_the_short_lane_cannot_reach_either_is_refused_with_the_number() -> None:
    """"No feasible route" is not actionable. Raise the tie to 115.50" and neither lane
    arrives: S is at 115.00", which is half an inch short, and the refusal says so."""
    graph, space = _world()
    problem = GravityProblem(ceiling_m=CEILING_IN * M_PER_IN,
                             grade_in_per_ft=GRADE_IN_PER_FT, diameter_m=0.0,
                             required_m={3: 115.50 * M_PER_IN})
    report = GravityRefusal()
    assert sloped_route(graph, space, 0, {3}, problem, constraints=_truss,
                        refusal=report) is None
    assert report.tightest is not None
    what, short = report.tightest
    assert "member window" in what or "tie" in what
    assert short == pytest.approx(0.25, abs=0.26)
    assert "no route falls" in report.sentence()


def test_a_rise_is_never_relaxed() -> None:
    """A drain falls. A lattice edge upward is not a lane, whatever it costs."""
    graph, space = _world()
    graph.nodes.append(Node(index=8, x=0.0, y=0.0, z=STEP))
    graph.edges.setdefault(0, {}).setdefault("z", []).append(8)
    graph.edges.setdefault(8, {}).setdefault("z", []).append(0)
    graph.weights[(0, 8)] = graph.weights[(8, 0)] = 0.0
    graph.terms[(0, 8)] = graph.terms[(8, 0)] = {"travel_in": 0.0}
    problem = GravityProblem(ceiling_m=CEILING_IN * M_PER_IN,
                             grade_in_per_ft=GRADE_IN_PER_FT, diameter_m=0.0,
                             required_m={8: 0.0})
    assert sloped_route(graph, space, 0, {8}, problem) is None


def _row_world(duct_in: tuple[float, float]):
    """§8a: A-B-C-D at 24" pitch, one inflated duct over x = 30"..42" of edge B-C."""
    from shapely.geometry import box

    from typehaus.routing.gravity_band import band_obstacles
    from typehaus.routing.obstacles import HardPrism

    nodes = [Node(index=k, x=k * STEP, y=0.0, z=0.0) for k in range(4)]
    graph = Graph(nodes=nodes)
    for a in range(3):
        graph.edges.setdefault(a, {}).setdefault("x", []).append(a + 1)
        graph.edges.setdefault(a + 1, {}).setdefault("x", []).append(a)
        for key in ((a, a + 1), (a + 1, a)):
            graph.weights[key] = 24.0
            graph.terms[key] = {"travel_in": 24.0}
    duct = HardPrism(tag="DU-ORACLE", kind="run",
                     footprint=box(30 * M_PER_IN, -6 * M_PER_IN, 42 * M_PER_IN, 6 * M_PER_IN),
                     z0_m=duct_in[0] * M_PER_IN, z1_m=duct_in[1] * M_PER_IN)
    space = RoutingSpace(radius_m=0.0, clearance_m=0.0, cost=RouteCost(bend_in=6.0),
                         hard=[], soft=[], corridors=[], bbox=(0.0, 0.0, 3 * STEP, 0.0),
                         storeys=("main",), banded=[duct])
    problem = GravityProblem(ceiling_m=CEILING_IN * M_PER_IN,
                             grade_in_per_ft=GRADE_IN_PER_FT, diameter_m=0.0,
                             required_m={3: REQUIRED_IN * M_PER_IN})
    return graph, space, problem, band_obstacles(space, graph)


@pytest.mark.parametrize(("duct_in", "start_in"), [
    ((114.50, 115.40), 116.275),  # row 1: the old plane search drew it through the duct
    ((114.50, 116.00), None),     # row 2: no start clears it and reaches the tie
    ((115.40, 116.20), 115.50),   # row 3: passes under at the arrival-anchored start
])
def test_a_banded_duct_is_passed_over_under_or_refused_as_section_8a_works_it(
        duct_in, start_in) -> None:
    graph, space, problem, obstacles = _row_world(duct_in)
    route = sloped_route(graph, space, 0, {3}, problem, obstacles=obstacles)
    if start_in is None:
        assert route is None
        return
    assert route is not None and route.nodes == [0, 1, 2, 3]
    # 2e-3": the duct is read 1/16" eroded (a run on its inflated edge is at clearance).
    assert route.start_m / M_PER_IN == pytest.approx(start_in, abs=2e-3)


def test_the_grid_allowance_covers_section_13s_three_legs() -> None:
    """§13: 5.1 + 3.3 + 2.0 ft at 1/4"/ft is 2.600" exact, 2.6875" on the grid."""
    from typehaus.cli.route_fall import _on_grid
    from typehaus.routing.gravity import grid_allowance
    from typehaus.routing.search import Route

    ft = 0.3048
    points = [(0.0, 0.0, 0.0), (5.1 * ft, 0.0, 0.0), (5.1 * ft, 3.3 * ft, 0.0),
              (7.1 * ft, 3.3 * ft, 0.0)]
    snapped = _on_grid(points, 0.25)
    assert abs(snapped[0][2] / M_PER_IN - 2.6875) < 1e-9
    allowance = grid_allowance(Route(nodes=[0, 1, 2, 3], points=points, cost=0.0),
                                0.25, 0.0)
    assert abs(allowance / M_PER_IN - 0.0875) < 1e-3  # plan snap: 61.2" is 61.1875"


def test_the_head_bound_at_b_is_section_13s_number() -> None:
    """§13: at B, 2 ft developed and 4 ft of plan to D: 114.00 + 0.25 x 6 = 115.50"."""
    from typehaus.routing.gravity import head_floor_fn

    graph, _space = _world()
    problem = _problem()
    floor = head_floor_fn(graph, {3}, problem.required_m, GRADE_IN_PER_FT)
    assert (floor(1) + problem.fall_over(2.0)) / M_PER_IN == pytest.approx(115.50)


def test_the_drop_into_the_tie_meets_a_heater_line_as_section_13_says() -> None:
    """§13: a plumb drop from -4.0" to -16.0" crosses PR-B-CW-WH's -9.61..-3.99" band."""
    from typehaus.routing.gravity import drop_blocker

    def at_node(_a: int, _b: int) -> list[tuple[float, float, float, float, str]]:
        return [(0.0, 1.0, -9.61 * M_PER_IN, -3.99 * M_PER_IN, "PR-B-CW-WH")]

    assert drop_blocker(at_node, 0, -4.0 * M_PER_IN, -16.0 * M_PER_IN) == "PR-B-CW-WH"
    assert drop_blocker(at_node, 0, -10.0 * M_PER_IN, -16.0 * M_PER_IN) is None
