"""§11's supply rules, by hand: a PEX corner bends where its arc clears, an exterior cavity pays.

1/2" PEX is 0.625" OD, so Uponor's 6 x OD gives a 3.75" radius. A corner from +x to +y
bends through a quarter arc whose midpoint stands R(1 - 1/sqrt 2) = 1.098" back along x and
out along y from the corner. A 2 ft edge in an exterior cavity pays 2 x 96 = 192".
"""

from __future__ import annotations

from shapely.geometry import box

from typehaus.quantities import M_PER_IN
from typehaus.routing.cost import RouteCost
from typehaus.routing.graph import Graph, Node, _finish
from typehaus.routing.obstacles import HardPrism, SoftPrism
from typehaus.routing.search import bend_price
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


def test_an_exterior_cavity_pays_per_foot_and_a_vent_is_exempt() -> None:
    wall = SoftPrism(tag="W-EXT", kind="wall", footprint=box(0.0, -0.1, 2 * FT, 0.1),
                     z0_m=-1.0, z1_m=1.0, occupancy="exterior")
    a, b = Node(index=0, x=0.0, y=0.0, z=0.0), Node(index=1, x=2 * FT, y=0.0, z=0.0)
    priced = _finish(_space(soft=[wall]), a, b, "x", [wall])
    assert priced is not None and abs(priced[1]["exterior_wall_in"] - 192.0) < 1e-9
    assert RouteCost().for_run("pipe", "vent").exterior_wall_per_ft == 0.0
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
