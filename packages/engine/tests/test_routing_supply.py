"""§11's supply rules, by hand: a PEX corner bends where its arc clears, an exterior cavity pays.

1/2" PEX is 0.625" OD, so Uponor's 6 x OD gives a 3.75" radius. A corner from +x to +y
bends through a quarter arc whose midpoint stands R(1 - 1/sqrt 2) = 1.098" back along x and
out along y from the corner. A 2 ft edge on an exterior bay's cold side pays 2 x 96 + 480 = 672"
(the per-edge cavity price), on its warm side 2 x 24 = 48". The bay: films R 1.42 in /
R 0.23 out, R 3.7/in fill over 5.5", R 10 continuous outboard, 70 F in, -15 F out. The pipe
face is 42 F where R_in = 28 x 32.0 / 85 = 10.54, i.e. 2.47" into the fill: a lane at 1" is
warm, at 4" cold; with no continuous insulation, or no reading, the whole bay is cold.
"""

from __future__ import annotations

from shapely.geometry import box

from typehaus.quantities import M_PER_IN
from typehaus.routing.cost import RouteCost
from typehaus.routing.graph import Graph, Node, _finish
from typehaus.routing.obstacles import HardPrism, SoftPrism
from typehaus.routing.search import bend_price, price_route, shortest_route
from typehaus.routing.space import RoutingSpace
from typehaus.routing.trades.pipe import bend_radius_m

FT = 12 * M_PER_IN


def _space(hard: list | None = None, soft: list | None = None) -> RoutingSpace:
    return RoutingSpace(radius_m=0.0, clearance_m=0.0, cost=RouteCost(), hard=hard or [],
                        soft=soft or [], corridors=[], bbox=(0.0, 0.0, 2 * FT, 2 * FT),
                        storeys=("main",))


def test_a_pex_corner_bends_where_its_arc_clears_and_is_fitted_where_it_does_not() -> None:
    radius = bend_radius_m(0.5 * M_PER_IN, "water_cold", "pex")
    assert abs(radius / M_PER_IN - 3.75) < 1e-9
    assert bend_radius_m(0.5 * M_PER_IN, "water_cold", "copper") == 0.0
    graph = Graph(nodes=[Node(index=0, x=0.0, y=FT, z=0.0), Node(index=1, x=FT, y=FT, z=0.0),
                         Node(index=2, x=FT, y=2 * FT, z=0.0)])
    clear = _space()
    clear.bend_radius_m = radius
    assert bend_price(graph, clear, 0, 1, 2) == clear.cost.pex_bend_in
    # A 1/4" post on the arc's midpoint, 1.098" back and out from the corner.
    mid_x, mid_y = FT - 1.098 * M_PER_IN, FT + 1.098 * M_PER_IN
    post = HardPrism(tag="POST", kind="member", z0_m=-1.0, z1_m=1.0,
                     footprint=box(mid_x - 0.125 * M_PER_IN, mid_y - 0.125 * M_PER_IN,
                                   mid_x + 0.125 * M_PER_IN, mid_y + 0.125 * M_PER_IN))
    blocked = _space(hard=[post])
    blocked.bend_radius_m = radius
    assert bend_price(graph, blocked, 0, 1, 2) == blocked.cost.bend_in


def _line_graph(points: list[tuple[float, float]], links: list[tuple[int, int]]) -> Graph:
    """Nodes at plan points in inches, each link one edge priced at its length."""
    graph = Graph(nodes=[Node(index=i, x=x * M_PER_IN, y=y * M_PER_IN, z=0.0)
                         for i, (x, y) in enumerate(points)])
    for a, b in links:
        axis = "x" if points[a][1] == points[b][1] else "y"
        length = abs(points[a][0] - points[b][0]) + abs(points[a][1] - points[b][1])
        for u, v in ((a, b), (b, a)):
            graph.edges.setdefault(u, {}).setdefault(axis, []).append(v)
            graph.weights[(u, v)] = length
    return graph


def test_pex_bends_hold_their_tangents_and_a_back_step_is_never_a_bend() -> None:
    """R = 3.75": two bends 1" apart need 7.5" between them, so the jog is two fittings;
    a 1/2" back-step along x is refused, not priced as a 4" bend."""
    space = _space()
    space.bend_radius_m = 3.75 * M_PER_IN
    jog = _line_graph([(0, 0), (24, 0), (24, 1), (48, 1)], [(0, 1), (1, 2), (2, 3)])
    route = shortest_route(jog, space, 0, {3})
    assert route is not None and route.bends == 2
    assert route.cost == 49.0 + 2 * space.cost.bend_in
    assert price_route(jog, space, route.nodes).cost == route.cost
    # A(0,0) B(24,0) C(23.5,0) G(23.5,24) D(24,24): C hangs off B, so A-B-C-G back-steps.
    back = _line_graph([(0, 0), (24, 0), (23.5, 0), (23.5, 24), (24, 24)],
                       [(0, 1), (1, 2), (2, 3), (1, 4), (4, 3)])
    route = shortest_route(back, space, 0, {3})
    assert route is not None and route.nodes == [0, 1, 4, 3]
    assert route.cost == 48.5 + space.cost.pex_bend_in + space.cost.bend_in
    assert price_route(back, space, [0, 1, 2, 3]).cost == 48.5 + 3 * space.cost.bend_in


def test_an_exterior_bay_pays_by_the_side_it_runs_on_and_a_vent_is_exempt() -> None:
    from typehaus.routing.freeze_bay import FreezeBay

    rows = ((-1.0, 1.0, 0, 3.7 / M_PER_IN, False), (-1.0, 1.0, 1, 10.0, True))
    bay = FreezeBay((0.0, 1.0), 0.0, 5.5 * M_PER_IN, rows, -15.0)
    bare = FreezeBay((0.0, 1.0), 0.0, 5.5 * M_PER_IN, rows[:1], -15.0)
    priced = {}
    for name, depth_in, reading in (("warm", 1.0, bay), ("cold", 4.0, bay),
                                    ("bare", 1.0, bare), ("unread", 1.0, None)):
        wall = SoftPrism(tag="W-EXT", kind="wall", footprint=box(0.0, 0.0, 2 * FT, 0.14),
                         z0_m=-1.0, z1_m=1.0, occupancy="exterior", bay=reading)
        y = depth_in * M_PER_IN
        a, b = Node(index=0, x=0.0, y=y, z=0.0), Node(index=1, x=2 * FT, y=y, z=0.0)
        priced[name] = _finish(_space(soft=[wall]), a, b, "x", [wall])[1]
    assert abs(priced["warm"]["exterior_warm_in"] - 48.0) < 1e-9
    for name in ("cold", "bare", "unread"):
        assert abs(priced[name]["exterior_cold_in"] - 672.0) < 1e-9, name
    assert RouteCost().for_run("pipe", "vent").exterior_bay_per_ft("warm") == 0.0
    assert RouteCost().for_run("duct", "supply").exterior_wall_per_ft == 0.0
    assert RouteCost().for_run("pipe", "water_cold").exterior_wall_per_ft == 96.0


def test_a_laid_supply_leg_offers_a_rack_lane_either_side_and_a_drain_offers_none() -> None:
    from types import SimpleNamespace

    from typehaus.routing.rack import rack_lanes

    def laid(system: str) -> SimpleNamespace:
        return SimpleNamespace(tag=f"PR-{system}", kind="pipe", system=system,
                               diameter_m=0.5 * M_PER_IN, echo={"material": "pex"},
                               points=[(0.0, 0.0, 0.0), (2 * FT, 0.0, 0.0)])

    # 1/2" PEX is 0.625" OD: 0.3125 + 1" spacing + 0.3125 puts each lane 1.625" off.
    lanes = rack_lanes([laid("water_hot"), laid("drain")], system="water_cold",
                       radius_m=0.3125 * M_PER_IN, spacing_m=1.0 * M_PER_IN)
    assert sorted(round(lane.station / M_PER_IN, 4) for lane in lanes) == [-1.625, 1.625]
    space = _space()
    space.corridors.extend(lanes)
    space.radius_m = 0.3125 * M_PER_IN
    a = Node(index=0, x=0.0, y=1.625 * M_PER_IN, z=0.0)
    b = Node(index=1, x=2 * FT, y=1.625 * M_PER_IN, z=0.0)
    priced = _finish(space, a, b, "x", [])
    # 24" of travel less 2 ft x 4"/ft of rack discount.
    assert priced is not None and abs(priced[0] - 16.0) < 1e-9
    assert abs(priced[1]["rack_in"] + 8.0) < 1e-9


def test_a_room_charges_the_length_inside_it_and_rooms_sum() -> None:
    def room(x1: float, occupancy: str) -> SoftPrism:
        return SoftPrism(tag="R", kind="room", footprint=box(0.0, -0.1, x1, 0.1),
                         z0_m=-1.0, z1_m=1.0, occupancy=occupancy)

    a, b = Node(index=0, x=0.0, y=0.0, z=0.0), Node(index=1, x=2 * FT, y=0.0, z=0.0)
    cost = RouteCost()
    half, whole = room(FT, "living"), room(2 * FT, "bedroom")
    # 24" of travel; the straddled room bills 1 ft of it, an enclosing second room 2 ft more.
    for rooms, billed in (([half], cost.room_penalty("living")),
                          ([half, whole], cost.room_penalty("living")
                           + 2 * cost.room_penalty("bedroom"))):
        priced = _finish(_space(soft=rooms), a, b, "x", rooms)
        assert priced is not None and abs(priced[1]["room_in"] - billed) < 1e-9
        assert abs(priced[0] - (24.0 + billed)) < 1e-9
