"""The escape graph and its search, on synthetic worlds where the answer is known by hand.

`test_routing_oracle.py` reproduces the house's own note. These are the properties that
have to hold on any world, checked where nothing else is in the way: the shape of a detour,
that a corridor discount actually pulls a route, and that the size guard raises rather than
coarsening.
"""

from __future__ import annotations

import math

import pytest

from typehaus.routing.corridors import Corridor
from typehaus.routing.cost import RouteCost
from typehaus.routing.graph import build_graph
from typehaus.routing.obstacles import HardPrism
from typehaus.routing.search import shortest_route
from typehaus.routing.space import MAX_LATTICE_NODES, RoutingSpace, RoutingSpaceTooLarge

pytestmark = pytest.mark.slow


def _space(*, hard=(), corridors=(), cost=None, radius_m=0.0):
    return RoutingSpace(radius_m=radius_m, clearance_m=0.0,
                        cost=cost or RouteCost(corridor_discount_per_ft=0.0),
                        hard=list(hard), soft=[], corridors=list(corridors),
                        bbox=(-1.0, -1.0, 12.0, 12.0), storeys=("main",))


def _route(space, terminals, levels=None):
    graph = build_graph(space, terminals, levels)
    start = min(graph.nodes,
                key=lambda n: math.dist((n.x, n.y), terminals[0][:2])).index
    goal = min(graph.nodes,
               key=lambda n: math.dist((n.x, n.y), terminals[-1][:2])).index
    return graph, shortest_route(graph, space, start, {goal})


def test_around_one_square_obstacle_is_two_bends_not_four() -> None:
    """The property the escape-graph formulation exists for.

    A uniform grid has nodes at the obstacle's corners and a route that hugs them takes
    four turns. Candidate lines are the obstacle's OFFSET edges, so the cheap route is one
    L past a single edge — two bends at most, and one when the terminals allow it."""
    from shapely.geometry import box

    obstacle = HardPrism(tag="CHASE", kind="void", footprint=box(3.0, 3.0, 6.0, 6.0),
                         z0_m=-1.0, z1_m=1.0)
    space = _space(hard=[obstacle])
    terminals = [(0.0, 0.0, 0.0), (9.0, 9.0, 0.0)]
    _graph, route = _route(space, terminals, levels=[0.0])
    assert route is not None
    assert route.bends <= 2, [route.bends, route.polyline()]
    # And it really does go round rather than through.
    for x, y, _z in route.polyline():
        assert not (3.0 < x < 6.0 and 3.0 < y < 6.0)


def test_a_corridor_discount_pulls_the_route_into_the_bay() -> None:
    """A discount on a line the graph never built is worth nothing, so a corridor has to
    seed a candidate line as well as a price. Two runs of the same problem, one with the
    discount and one without: the discounted one rides the bay."""
    bay = Corridor(tag="FS:bay", kind="bay", axis="x", station=4.0,
                   z0_m=-1.0, z1_m=1.0, clear_width_m=1.0, lo_m=-10.0, hi_m=20.0)
    terminals = [(0.0, 0.0, 0.0), (9.0, 8.0, 0.0)]

    plain = _space(corridors=[bay], cost=RouteCost(corridor_discount_per_ft=0.0))
    _g, without = _route(plain, terminals, levels=[0.0])
    cheap = _space(corridors=[bay], cost=RouteCost(corridor_discount_per_ft=8.0))
    _g2, with_bay = _route(cheap, terminals, levels=[0.0])

    assert without is not None and with_bay is not None
    on_bay = [p for p in with_bay.polyline() if abs(p[1] - 4.0) < 1e-6]
    assert on_bay, with_bay.polyline()
    assert with_bay.terms.get("corridor_in", 0.0) < 0.0


def test_the_lattice_guard_raises_rather_than_coarsening() -> None:
    """AGENTS.md 2.3, made a test. A router that drops resolution to finish is answering a
    different question from the one asked, so the size guard is an exception and not a
    fallback — and it names the cap, so raising it is a decision somebody makes on purpose."""
    from shapely.geometry import box

    step = 0.05
    hard = [HardPrism(tag=f"P{i}", kind="void",
                      footprint=box(i * step, i * step, i * step + 0.01,
                                    i * step + 0.01),
                      z0_m=-1.0, z1_m=1.0)
            for i in range(600)]
    space = RoutingSpace(radius_m=0.0, clearance_m=0.0, cost=RouteCost(),
                         hard=hard, soft=[], corridors=[],
                         bbox=(-1.0, -1.0, 40.0, 40.0), storeys=("main",))
    with pytest.raises(RoutingSpaceTooLarge) as caught:
        build_graph(space, [(0.0, 0.0, 0.0), (30.0, 30.0, 0.0)], [0.0])
    assert "MAX_LATTICE_NODES" in str(caught.value) or "MAX_CANDIDATE_LINES" in str(
        caught.value)
    assert MAX_LATTICE_NODES > 0


def test_a_terminal_inside_an_obstacle_is_kept_and_reported() -> None:
    """A branch ties into the very run that blocks its tie point, so refusing to build a
    node there would refuse every tie in the house. The node is kept and the prism named,
    which is the difference between a search that says what it did and one that silently
    relaxed a rule."""
    from shapely.geometry import box

    obstacle = HardPrism(tag="PR-MAIN", kind="run", footprint=box(8.0, 8.0, 10.0, 10.0),
                         z0_m=-1.0, z1_m=1.0)
    space = _space(hard=[obstacle])
    graph = build_graph(space, [(0.0, 0.0, 0.0), (9.0, 9.0, 0.0)], [0.0])
    assert graph.blocked_terminals == ["PR-MAIN"]
    assert any(abs(n.x - 9.0) < 1e-9 and abs(n.y - 9.0) < 1e-9 for n in graph.nodes)


def test_a_vertical_leg_is_cheaper_per_foot_than_a_horizontal_one() -> None:
    """``riser_per_ft`` under 1.0 is what makes a drop the cheap way to change level — it
    is pipe in a wall or a bay rather than pipe across a room. Not free, because it still
    has to land somewhere and be reachable."""
    cost = RouteCost()
    horizontal = cost.segment_cost(10.0)
    vertical = cost.segment_cost(10.0, vertical=True)
    assert 0.0 < vertical < horizontal
    assert vertical == pytest.approx(horizontal * cost.riser_per_ft)


def test_an_unknown_occupancy_is_priced_as_a_living_room_not_as_free() -> None:
    """A new ``Occupancy`` member should cost something until somebody decides what. A
    router that treats an unknown room as a plenum is the failure mode that produces
    confident nonsense."""
    cost = RouteCost()
    assert cost.room_penalty("conservatory") == cost.room_penalty("living")
    assert cost.room_penalty(None) == 0.0
    assert cost.room_penalty("mechanical") == 0.0
