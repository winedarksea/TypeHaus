"""§9's two rules on a hand-built ladder: no S-trap, and the take-off within the limit wins.

Two rows of six nodes a foot apart, the lower a foot down and cheaper, a rung at every
station. The goal is the lower row's far end. With no arm the cheapest route drops at the
trap, which is an S-trap; with the arm open the run may not drop until it has closed at a
take-off, and a take-off past Table 1002.2's limit is not one it can reach.
"""

from __future__ import annotations

from typehaus.quantities import M_PER_IN
from typehaus.routing.cost import RouteCost
from typehaus.routing.graph import Graph, Node
from typehaus.routing.gravity_search import GravityProblem, sloped_route
from typehaus.routing.space import RoutingSpace
from typehaus.routing.trap_vent import arm_reach, arm_seeds

FT = 12 * M_PER_IN


def _ladder() -> tuple[Graph, RoutingSpace]:
    nodes = [Node(index=k + 6 * row, x=k * FT, y=0.0, z=-row * FT)
             for row in range(2) for k in range(6)]
    graph = Graph(nodes=nodes)

    def link(a: int, b: int, axis: str, weight: float) -> None:
        graph.edges.setdefault(a, {}).setdefault(axis, []).append(b)
        graph.edges.setdefault(b, {}).setdefault(axis, []).append(a)
        graph.weights[(a, b)] = graph.weights[(b, a)] = weight

    # The lower row is a bay at a third the price: dropping at the trap is the cheap route.
    for k in range(5):
        link(k, k + 1, "x", 12.0)
        link(k + 6, k + 7, "x", 4.0)
    for k in range(6):
        link(k, k + 6, "z", 6.0)
    space = RoutingSpace(radius_m=0.0, clearance_m=0.0,
                         cost=RouteCost(corridor_discount_per_ft=8.0), hard=[], soft=[],
                         corridors=[], bbox=(0.0, 0.0, 5 * FT, 0.0), storeys=("main",))
    return graph, space


def _problem(graph: Graph | None = None, space: RoutingSpace | None = None,
             takeoffs: dict[int, float] | None = None) -> GravityProblem:
    seeds = None
    if takeoffs is not None:
        reach = arm_reach(graph, space, 0, limit_ft=3.5, weir_m=0.0, grade_in_per_ft=0.25)
        seeds = arm_seeds(reach, takeoffs)
    return GravityProblem(ceiling_m=0.0, grade_in_per_ft=0.25, diameter_m=0.0,
                          required_m={11: -3 * FT}, seeds=seeds)


def _drops_at(graph: Graph, nodes: list[int]) -> int:
    return next(i for i, (a, b) in enumerate(zip(nodes, nodes[1:], strict=False))
                if graph.nodes[b].z < graph.nodes[a].z)


def test_with_no_arm_the_cheapest_route_drops_at_the_trap_and_with_one_it_cannot() -> None:
    graph, space = _ladder()
    free = sloped_route(graph, space, 0, {11}, _problem())
    assert free is not None and _drops_at(graph, free.nodes) == 0  # an S-trap
    # 3.5 ft is Table 1002.2's 1 1/2" arm; with no take-off in reach there is no route.
    assert sloped_route(graph, space, 0, {11}, _problem(graph, space, {})) is None


def test_the_take_off_within_the_limit_wins_over_a_cheaper_one_past_it() -> None:
    graph, space = _ladder()
    # Node 4 is 4 ft out, past the 3.5 ft limit, and its vent is free; node 3 costs 30".
    route = sloped_route(graph, space, 0, {11},
                         _problem(graph, space, {2: 60.0, 3: 30.0, 4: 0.0}))
    assert route is not None and route.takeoff == 3
    assert graph.nodes[route.nodes[_drops_at(graph, route.nodes)]].x >= 3 * FT - 1e-9
