"""§7 of `houses/catlin/notes/mep_drain_routing_basis.md`, reproduced numerically.

The note enumerates §4's lattice by hand and finds exactly two simple paths, edge-disjoint
and equally priced. Everything here is read off that enumeration.
"""

from __future__ import annotations

import math

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.routing.alternatives import alternative_routes, corridor_tolerance_m
from typehaus.routing.cost import RouteCost
from typehaus.routing.graph import Graph, Node
from typehaus.routing.search import shortest_route
from typehaus.routing.space import RoutingSpace


def _lattice() -> tuple[Graph, RoutingSpace]:
    """§4's world, built by hand: 3x3 at 24", the centre node absent, every edge 24" long."""
    step = 24.0 * M_PER_IN
    coords = [(i * step, j * step) for j in range(3) for i in range(3)]
    coords.pop(4)  # the blocked centre node, E, is removed and its id never used
    nodes = [Node(index=k, x=x, y=y, z=0.0) for k, (x, y) in enumerate(coords)]

    cost = RouteCost(bend_in=24.0, corridor_discount_per_ft=0.0)
    space = RoutingSpace(radius_m=0.0, clearance_m=0.0, cost=cost, hard=[], soft=[],
                         corridors=[], bbox=(0.0, 0.0, 2 * step, 2 * step),
                         storeys=("main",))
    graph = Graph(nodes=nodes)
    for a in nodes:
        for b in nodes:
            if b.index <= a.index:
                continue
            dx, dy = abs(b.x - a.x), abs(b.y - a.y)
            if not math.isclose(dx + dy, step, rel_tol=1e-9):
                continue
            axis = "x" if dx > dy else "y"
            graph.edges.setdefault(a.index, {}).setdefault(axis, []).append(b.index)
            graph.edges.setdefault(b.index, {}).setdefault(axis, []).append(a.index)
            graph.weights[(a.index, b.index)] = 24.0
            graph.weights[(b.index, a.index)] = 24.0
            graph.terms[(a.index, b.index)] = {"travel_in": 24.0}
            graph.terms[(b.index, a.index)] = {"travel_in": 24.0}
    return graph, space


def test_k_of_three_yields_exactly_the_two_paths_that_exist() -> None:
    """§7's enumeration: A-D-G-H-I and A-B-C-F-I, both at 120, and no third."""
    graph, space = _lattice()
    routes = alternative_routes(shortest_route, graph, space, 0, {7}, 3)
    assert [r.nodes for r in routes] == [[0, 3, 5, 6, 7], [0, 1, 2, 4, 7]]
    assert [r.cost for r in routes] == pytest.approx([120.0, 120.0])
    assert [r.bends for r in routes] == [1, 1]


def test_route_a_is_byte_identical_to_the_plain_search() -> None:
    """§4 is untouched by this module existing, and that is not an accident.

    A feature that quietly changed the default answer would invalidate every pinned number
    in the note — so the first alternative IS the plain search, node for node and inch for
    inch, and `k = 1` never enters the penalty loop at all.
    """
    graph, space = _lattice()
    plain = shortest_route(graph, space, 0, {7})
    assert plain is not None
    only = alternative_routes(shortest_route, graph, space, 0, {7}, 1)
    assert [r.nodes for r in only] == [plain.nodes]
    first = alternative_routes(shortest_route, graph, space, 0, {7}, 3)[0]
    assert first.nodes == plain.nodes
    assert first.cost == pytest.approx(plain.cost)


def test_the_second_route_is_priced_on_the_original_graph_not_the_penalised_one() -> None:
    """120, not the 120-at-a-tripled-weight it would have carried out of the copy.

    §7 works the arithmetic: route A's own penalised cost is 4 x 72 + 24 = 312. A router
    that quoted alternatives at their search-time weight would offer a reader two numbers
    measured with two different rulers.
    """
    graph, space = _lattice()
    routes = alternative_routes(shortest_route, graph, space, 0, {7}, 3)
    assert len(routes) == 2
    assert routes[1].cost == pytest.approx(120.0)
    assert routes[1].terms["travel_in"] == pytest.approx(96.0)
    assert routes[1].terms["bend_in"] == pytest.approx(24.0)


def test_a_third_alternative_is_refused_rather_than_padded() -> None:
    """Asking for five gets two, because two is how many there are.

    The rejected candidate on round 2 is route A again at a shared fraction of 1.0. A list
    padded to five with the same lane wearing a jog would be a worse answer than the truth.
    """
    graph, space = _lattice()
    assert len(alternative_routes(shortest_route, graph, space, 0, {7}, 5)) == 2


def test_the_penalty_band_is_a_lane_and_not_a_line() -> None:
    """§7: radius and clearance are zero here, so the band is the 12" floor.

    Without the floor a hair-thin run would penalise only literally-collinear edges and
    find "another route" one candidate line away from the one just offered.
    """
    _graph, space = _lattice()
    assert corridor_tolerance_m(space) == pytest.approx(0.3048)


def test_a_factor_below_one_is_refused_rather_than_discounting_a_taken_lane() -> None:
    """At 0.5 the tripled lane would be halved and round 1 would return route A at 60 —
    the same route offered as an alternative to itself."""
    graph, space = _lattice()
    with pytest.raises(ValueError, match="CHEAPER"):
        alternative_routes(shortest_route, graph, space, 0, {7}, 3, factor=0.5)


def test_an_unreachable_goal_returns_nothing_rather_than_raising() -> None:
    """A walled-off terminal is a statement about the model; it is not this module's to
    soften, and it must not become a traceback on the way out."""
    graph, space = _lattice()
    graph.nodes.append(Node(index=8, x=99.0, y=99.0, z=0.0))  # no edges at all
    assert alternative_routes(shortest_route, graph, space, 0, {8}, 3) == []
