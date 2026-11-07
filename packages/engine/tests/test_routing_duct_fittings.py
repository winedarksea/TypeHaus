"""Duct take-offs and the port-kit lead: ``mep_duct_routing_basis.md`` §7 and §8.

The stamped elbow's centre-to-face is unpublished, so the take-off tables are asserted with
R INJECTED at the note's three bases (1.5 D stand-in, 1.0 D, the Ward adjustable's A)."""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from typehaus.model.ducts import DuctElbowRow, PortKit
from typehaus.quantities import M_PER_IN, inch
from typehaus.routing.cost import RouteCost
from typehaus.routing.duct_fittings import (
    elbow,
    floor_takeoff_m,
    kit_lead,
    lead_shortfall_m,
    min_straight_m,
    takeoff_m,
)
from typehaus.routing.duct_search import DuctFittingProblem, fitted_route
from typehaus.routing.graph import Graph, Node
from typehaus.routing.space import RoutingSpace


def _to(radius_in: float, angle: float) -> float:
    return takeoff_m(radius_in * M_PER_IN, angle) / M_PER_IN


@pytest.mark.parametrize(("radius_in", "angles", "want"), [
    (6.0, (90, 45), (6.000, 2.485)),                       # 4" stamped, 1.5 D
    (4.0, (90, 45), (4.000, 1.657)),                       # 4" stamped, 1.0 D
    (4.75, (90, 60, 45, 30), (4.750, 2.742, 1.968, 1.273)),  # 4" adjustable A
    (9.0, (90, 45), (9.000, 3.728)),                       # 6" stamped, 1.5 D
    (7.0, (90, 60, 45, 30), (7.000, 4.041, 2.899, 1.876)),   # 8" adjustable A
])
def test_take_off_per_turn_is_the_note_s_7_1(radius_in, angles, want):
    assert [round(_to(radius_in, a), 3) for a in angles] == list(want)


def test_minimum_straights_are_the_note_s_7_2():
    """4" 90+90: 12.0 / 8.0 / 9.5; 4" 45+45: 4.971 / 3.314 / 3.935; 8" 90+90 at 1.5 D: 24."""
    for radius, ninety, forty_five in ((6.0, 12.000, 4.971), (4.0, 8.000, 3.314),
                                       (4.75, 9.500, 3.935)):
        assert min_straight_m(*(takeoff_m(radius * M_PER_IN, 90),) * 2) / M_PER_IN \
            == pytest.approx(ninety, abs=5e-4)
        assert min_straight_m(*(takeoff_m(radius * M_PER_IN, 45),) * 2) / M_PER_IN \
            == pytest.approx(forty_five, abs=5e-4)
    assert 2 * _to(12.0, 90) == pytest.approx(24.0)
    assert 2 * floor_takeoff_m(4 * M_PER_IN, 90) / M_PER_IN == pytest.approx(4.000)


_ROWS = (DuctElbowRow(diameter=inch(4), product_ref="S4", kind="stamped"),
         DuctElbowRow(diameter=inch(4), product_ref="A4", angles=(90.0,),
                      center_to_face=inch(4.75)))
_STANDARD = SimpleNamespace(elbows=_ROWS)


def test_the_elbow_bought_decides_the_radius():
    """A stamped 90 (unpublished: the 1.5 D stand-in); the 26-degree jog of §7.3 an
    adjustable set down (A = 4.75); §7.5's 95.27-degree turn a stamped 90 within the 10."""
    d = 4 * M_PER_IN
    ninety = elbow(_STANDARD, 90.0, diameter_m=d)
    assert (ninety.basis, round(ninety.takeoff_m(90) / M_PER_IN, 3)) == ("stand-in", 6.0)
    jog = math.degrees(math.atan(4.875 / 10.0))
    adjustable = elbow(_STANDARD, jog, diameter_m=d)
    assert adjustable.basis == "bought"
    assert adjustable.takeoff_m(jog) / M_PER_IN == pytest.approx(1.096, abs=5e-4)
    gym = elbow(_STANDARD, 95.27, diameter_m=d)
    need = (gym.takeoff_m(95.27) + ninety.takeoff_m(90.0)) / M_PER_IN
    assert need == pytest.approx(12.579, abs=5e-4) and need > 6.125
    assert elbow(_STANDARD, 90.0).fabricated  # rectangular: no throat radius is read


def test_the_supply_port_lead_is_the_note_s_8():
    """12" flex; to the first rigid vertex 21.0" (6" 1.5 D) or 18.0" (A = 6); the outdoor
    kit's GV0772 length is reported unread; DU-B-ERV-SUP-TRUNK is 1.599" short."""
    supply = kit_lead(PortKit(type_ref="T", flex_product_ref="FLEX", flex_length=inch(12)),
                      needs_transition=False)
    assert supply.inches == pytest.approx(12.000) and not supply.unread
    assert supply.inches + _to(9.0, 90) == pytest.approx(21.000)
    assert supply.inches + _to(6.0, 90) == pytest.approx(18.000)
    outdoor = kit_lead(PortKit(type_ref="T", transition_product_ref="GV0772",
                               flex_product_ref="FLEX", flex_length=inch(12)),
                       needs_transition=True)
    assert outdoor.inches == pytest.approx(12.000) and "GV0772" in outdoor.unread[0]
    trunk = [tuple(c * M_PER_IN for c in p) for p in ((88.656, 364.625, -33.838),
                                                       (88.656, 364.625, -23.437))]
    assert lead_shortfall_m(trunk, supply.length_m) / M_PER_IN == pytest.approx(1.599,
                                                                               abs=5e-4)


def _grid(xs, ys, *, section: bool = False) -> tuple[Graph, RoutingSpace]:
    """A hand-built lattice (inches), every edge priced at its length: plan (x, y), or a
    section (x, z) with ``section``."""
    coords = [(x, y) for y in ys for x in xs]
    nodes = [Node(index=k, x=x * M_PER_IN, y=0.0 if section else y * M_PER_IN,
                  z=y * M_PER_IN if section else 0.0) for k, (x, y) in enumerate(coords)]
    graph = Graph(nodes=nodes)
    for a in nodes:
        for b in nodes:
            ia, ib = coords[a.index], coords[b.index]
            same_x, same_y = ia[0] == ib[0], ia[1] == ib[1]
            if a.index == b.index or not (same_x or same_y):
                continue
            line = xs if same_y else ys
            k0, k1 = sorted((line.index(ia[0 if same_y else 1]),
                             line.index(ib[0 if same_y else 1])))
            if k1 - k0 != 1:
                continue
            across = "z" if section else "y"
            graph.edges.setdefault(a.index, {}).setdefault("x" if same_y else across,
                                                           []).append(b.index)
            length = abs(ia[0] - ib[0]) + abs(ia[1] - ib[1])
            graph.weights[(a.index, b.index)] = length
            graph.terms[(a.index, b.index)] = {"travel_in": length}
    space = RoutingSpace(radius_m=0.0, clearance_m=0.0,
                         cost=RouteCost(bend_in=24.0, corridor_discount_per_ft=0.0),
                         hard=[], soft=[], corridors=[], bbox=(0.0, 0.0, 1.0, 1.0),
                         storeys=("main",))
    return graph, space


def _plan(route) -> list[tuple[float, float]]:
    """(x, y) — or (x, z) for a section — in inches."""
    return [(round(x / M_PER_IN, 3), round((y + z) / M_PER_IN, 3)) for x, y, z in
            route.polyline()]


def test_two_turns_closer_than_their_take_offs_are_refused():
    """(0,0) -> (40,3): every one-bend lane ends in a 3" straight, short of a 6" take-off,
    so the fitted route detours by y = 15 (two turns, legs 15 / 40 / 12). At a 1" take-off
    the 3" jog is legal again and the one-bend L wins."""
    graph, space = _grid([0.0, 20.0, 40.0], [0.0, 3.0, 15.0])
    start, goal = 0, 5
    tight = fitted_route(graph, space, start, {goal},
                         DuctFittingProblem(takeoff_m=6.0 * M_PER_IN))
    assert _plan(tight) == [(0.0, 0.0), (0.0, 15.0), (40.0, 15.0), (40.0, 3.0)]
    loose = fitted_route(graph, space, start, {goal},
                         DuctFittingProblem(takeoff_m=1.0 * M_PER_IN))
    assert loose.bends == 1


def test_a_port_lead_fixes_the_heading_and_a_reversal_is_never_a_way_round():
    """Leaving +x with no slack, the first turn needs 6" of rigid straight first; the route
    may not run past the goal and double back to buy straight."""
    graph, space = _grid([0.0, 20.0, 40.0], [0.0, 3.0, 15.0])
    route = fitted_route(graph, space, 0, {5},
                         DuctFittingProblem(takeoff_m=6.0 * M_PER_IN, start_axis="+x"))
    plan = _plan(route)
    assert plan[1][1] == 0.0 and route.bends == 3  # leaves along x, round by y = 15
    assert len(set(plan)) == len(plan)


def test_a_jog_too_short_for_two_90s_is_laid_as_an_offset():
    """FS-S-WEST's 4 7/8" tier change (§7.4), in section: two 4" 90s need 12", so it is a
    45 pair — the far corner slides on h = 4.875 and the jog is laid oblique, 6.894" long
    against the pair's 2 x 2.485 = 4.971"."""
    graph, space = _grid([0.0, 30.0, 60.0], [0.0, 4.875], section=True)
    problem = DuctFittingProblem(takeoff_m=6.0 * M_PER_IN, offset_jog_max_m=18 * M_PER_IN,
                                 offsets=((45.0, _to(6.0, 45) * M_PER_IN),
                                          (30.0, _to(4.75, 30) * M_PER_IN)))
    route = fitted_route(graph, space, 0, {5}, problem)
    assert _plan(route) == [(0.0, 0.0), (30.0, 0.0), (34.875, 4.875), (60.0, 4.875)]
    assert route.bends == 2 and route.offsets == 1
    assert fitted_route(graph, space, 0, {5},
                        DuctFittingProblem(takeoff_m=6.0 * M_PER_IN)) is None
