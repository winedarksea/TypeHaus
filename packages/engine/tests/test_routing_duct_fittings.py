"""Duct take-offs and the port-kit lead: ``mep_duct_routing_basis.md`` §7 and §8.

The stamped elbow's centre-to-face is unpublished, so the take-off tables are asserted with
R INJECTED at the note's three bases (1.5 D stand-in, 1.0 D, the Ward adjustable's A)."""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from typehaus.model.ducts import DuctElbowRow, PortKit
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.mep_fittings import KIND_ELBOW, SERVICE_DUCT
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
    assert elbow(None, 90.0, diameter_m=d).basis == "stand-in"  # no standard is no shop


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


def test_a_far_end_plumb_on_the_lead_is_refused_with_its_shortfall():
    """DU-B-ERV-SUP-TRUNK's shape: the far end on the lead's own axis (where the squared
    offset can round below zero), 10.401" up a 12" lead."""
    from typehaus.cli.route_ports import PortLead, _lead_overshoot
    from typehaus.cli.route_support import Endpoints

    port = (2.25186875, 9.261474999999999, -0.8594725000000003)
    far = (port[0], port[1], port[2] + 10.401 * M_PER_IN)
    tip = (port[0], port[1], port[2] + 12.0 * M_PER_IN)
    ends = Endpoints(origin=tip, root=far, radius_m=0.0762, kind="duct", system="supply",
                     storey="basement", origin_lead=PortLead("EQ.supply", port, tip, "+z"))
    assert 'short by 1.599"' in _lead_overshoot(ends)


def test_the_catalog_snaps_a_duct_elbow_where_the_standard_buys_one():
    """§7.5: one snap, so GYM's 95.3-degree turn is graded as the stamped 90 it is bought as."""
    from typehaus.resolve.duct_standard import ELBOW_SNAP_DEG
    from typehaus.resolve.mep_fittings import fitting_for

    spec = fitting_for(SERVICE_DUCT, KIND_ELBOW, 95.27, 4.0)
    assert spec is not None and spec.angle_deg == 90.0 and spec.snap_deg == ELBOW_SNAP_DEG


def test_a_search_out_of_budget_refuses_and_says_which_budget():
    from typehaus.routing.duct_search import DuctRefusal

    graph, space = _grid([0.0, 20.0, 40.0], [0.0, 3.0, 15.0])
    report = DuctRefusal()
    assert fitted_route(graph, space, 0, {5}, DuctFittingProblem(
        takeoff_m=6.0 * M_PER_IN, max_labels=2), refusal=report) is None
    assert report.stopped == "labels" and "a budget, not a proof" in report.sentence()


def test_a_flat_rectangular_mover_grows_obstacles_by_its_half_depth_in_z():
    """An 18x8 trunk sweeps 9" in plan (its turn's diagonal) but only 4" up: the run it passes
    under is grown by half the DEPTH in elevation, so 5" of air under a return is clear."""
    from typehaus.cli.route_duct_search import z_radius_m

    def _in(value: float) -> float:
        return value * M_PER_IN

    from typehaus.resolve.mep_envelopes import run_envelope

    ends = SimpleNamespace(kind="duct", width_m=_in(18), depth_m=_in(8), radius_m=_in(9.5))
    assert z_radius_m(ends) == pytest.approx(_in(4.5))
    assert z_radius_m(SimpleNamespace(kind="duct", width_m=0.0, depth_m=0.0,
                                      radius_m=_in(3))) is None
    section = (_in(6), _in(5), None)
    path, z = [(0.0, 0.0), (1.0, 0.0)], [0.0, 0.0]
    both = run_envelope("duct", "R", path, z, section, inflate_m=_in(10)).prisms[0]
    flat = run_envelope("duct", "R", path, z, section, inflate_m=_in(10),
                        inflate_z_m=_in(5)).prisms[0]
    assert both.z0_m == pytest.approx(-_in(15)) and flat.z0_m == pytest.approx(-_in(10))
    assert flat.footprint.equals(both.footprint)


def test_a_flat_duct_reads_its_half_height_in_z_in_bars_and_corridor_windows():
    """An 18x8 trunk (r 9") clears a bar 1" over its crown by its 4" half-height, not its 9"
    radius, and the space hands its corridor windows the same reach."""
    from typehaus.routing.floor_bars import Bar, FloorBars

    def _in(value: float) -> float:
        return value * M_PER_IN

    bars = FloorBars([Bar("x", 0.0, -1.0, 1.0, _in(0.75), _in(14), _in(19.5), "2x6", "F bar")])
    args = ("y", 0.0, -_in(30), _in(30), _in(9), None, _in(9))
    assert bars.crossed(*args) and bars.crossed(*args, _in(4)) == []
    space = RoutingSpace(radius_m=_in(9), clearance_m=_in(0.5), cost=RouteCost(), hard=[],
                         soft=[], corridors=[], bbox=(0, 0, 1, 1), storeys=(),
                         z_radius_m=_in(4))
    assert space.z_r == pytest.approx(_in(4))
