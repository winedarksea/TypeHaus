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


def test_a_wet_vent_goal_is_seeded_at_the_arm_cost_alone_and_wins() -> None:
    """§14: a join on a dry-vented bathroom-group drain needs no vent search, so its seed
    carries no ``h_vent`` and beats a take-off whose vent costs 30"."""
    graph, space = _ladder()
    reach = arm_reach(graph, space, 0, limit_ft=3.5, weir_m=0.0, grade_in_per_ft=0.25)
    problem = GravityProblem(ceiling_m=0.0, grade_in_per_ft=0.25, diameter_m=0.0,
                             required_m={11: -3 * FT, 2: -0.5 * M_PER_IN},
                             seeds=arm_seeds(reach, {3: 30.0}, frozenset({2})))
    route = sloped_route(graph, space, 0, {11, 2}, problem)
    assert route is not None and route.takeoff == 2 and route.nodes[-1] == 2


def _branch(wc_first: bool):
    """A 908.2 branch by hand: collector C, the lav's drain L (dry-vented) joining it at
    y=0, the tub's arm joining upstream at y=1.5', the WC upstream of L or downstream."""
    from types import SimpleNamespace

    from typehaus.resolve.mep_trap_arm import WetVentData

    inch = M_PER_IN

    def on_c(y_ft: float) -> tuple[float, float, float]:  # C falls 1.5" over 6' southward
        return (3 * FT, y_ft * FT, (-0.25 - 1.5 * (2 - y_ft) / 6) * inch)

    wc_y = 0.5 if wc_first else -2.0
    drains = {"C": [on_c(2), on_c(-4)],
              "L": [(0.0, 0.0, 0.0), on_c(0)],
              "W": [(5 * FT, wc_y * FT, on_c(wc_y)[2] + 0.25 * inch), on_c(wc_y)],
              "T": [(1.5 * FT, 3 * FT, 0.0), (1.5 * FT, 2 * FT, -0.25 * inch)]}
    radii = {"C": 1.5 * inch, "L": 0.75 * inch, "W": 1.5 * inch, "T": 0.75 * inch}
    vent = (0.5 * FT, 0.0, on_c(0)[2] * 0.5 / 3)  # on L, a sixth of the way down
    fx = {"FX-LAV": ("L", 1.0, "lavatory", "s"), "FX-WC": ("W", 3.0, "toilet", "s"),
          "FX-TUB": ("T", 2.0, "tub", "s")}
    data = WetVentData(drains, radii, fx, {"FX-LAV": [vent]}, [vent])
    model = SimpleNamespace(pipe_runs=[SimpleNamespace(
        tag="V-LAV", system="vent", serves=("FX-LAV",), path=[vent[:2], vent[:2]],
        z_m=[vent[2], vent[2] + FT])])
    arm = [(4.5 * FT, 1.5 * FT, 0.0), on_c(1.5)]  # 18" to C, then 18" down it to L
    return model, data, arm


def test_a_wet_tie_grades_wc_last_with_its_upsize_and_refuses_wc_first() -> None:
    from typehaus.resolve.mep_wet_tie import grade_hypothetical_tie

    model, data, arm = _branch(wc_first=False)
    tie, _notes = grade_hypothetical_tie(model, data, "FX-TUB", arm, 0.75 * M_PER_IN, 42.0)
    # 1 + 2 + 3 = 6 DFU on the wet length: 908.2.2 wants 3", and L is 1 1/2".
    assert tie is not None and tie.parent == "C" and "908.2 horizontal" in tie.what
    assert tie.upsize == (("L", 3.0),) and tie.name_on_vent == ("V-LAV",)
    model, data, arm = _branch(wc_first=True)
    tie, notes = grade_hypothetical_tie(model, data, "FX-TUB", arm, 0.75 * M_PER_IN, 42.0)
    assert tie is None and any("908.2.4" in n for n in notes)


def test_the_arm_holds_the_weir_grade_and_drops_at_the_take_off_not_at_the_trap() -> None:
    from typehaus.cli.route_fall import _fall
    from typehaus.routing.gravity import HeadBudget

    inch = M_PER_IN
    plan = [(0.0, 0.0, 0.0), (2 * FT, 0.0, 0.0), (4 * FT, 0.0, 0.0)]
    budget = HeadBudget(ceiling_m=0.0, required_m=-6 * inch, developed_ft=4.0,
                        diameter_m=1.5 * inch)
    out = _fall(plan, (0.0, 0.0, 0.0), budget, 0.25, "T", [], takeoff_xy=(2 * FT, 0.0))
    assert out is not None
    assert [round(p[2] / inch, 4) for p in out[0]] == [0.0, -0.5, -5.5, -6.0]
    # Over an obstacle the rest starts high and drops again into the tie: two drops.
    over = _fall(plan, (0.0, 0.0, 0.0), budget, 0.25, "T", [], start_m=-1 * inch,
                 takeoff_xy=(2 * FT, 0.0))
    assert [round(p[2] / inch, 4) for p in over[0]] == [0.0, -0.5, -1.5, -2.0, -6.0]
