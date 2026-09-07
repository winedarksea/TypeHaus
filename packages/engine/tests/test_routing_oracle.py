"""`houses/catlin/notes/mep_drain_routing_basis.md`, reproduced numerically.

CLAUDE.md's rule is that a calc which only agrees with itself is not verified. These tests
are the other half of that: every number here is read off the note, and the note's numbers
were hand-worked before this code existed.

§1 the four terminals and the gaps that said nobody had drawn the branches;
§2 the head budget the gravity profile has to reproduce, term by term;
§3 the bay, hand-derived from the authored `JoistSpec`;
§4 one escape graph — a 3x3 lattice, one removed node, and the eight-row A* expansion;
§5 the RSPH ordering, and the fact that route length is not a proxy for head slack.
"""

from __future__ import annotations

import math

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.routing.cost import RouteCost
from typehaus.routing.graph import Graph, Node
from typehaus.routing.search import shortest_route
from typehaus.routing.space import RoutingSpace


def _in(metres: float) -> float:
    return metres / M_PER_IN


# --- §1 the terminals ------------------------------------------------------------------

#: The note's own table, in inches. The gaps below are computed from these and nothing else.
_TERMINALS = {
    "FX-S-SUITEBATH-WC": (134.81, 250.625),
    "FX-S-SUITEBATH-LAV": (165.5, 268.0),
    "FX-S-SUITEBATH-TUBSH": (197.615, 261.125),
}
_ROOT = (156.0, 202.8)


def test_the_derived_drain_points_are_what_the_note_says(catlin_model_ro) -> None:
    """§1's table, against the engine's own derivation.

    If this fails the note is stale, not the code — every downstream number in §1 and §5
    is computed from these three points.
    """
    from typehaus.resolve.mep import _expected_drain_point

    for tag, expected in _TERMINALS.items():
        point = _expected_drain_point(catlin_model_ro, tag)
        assert point is not None, tag
        assert (_in(point[0]), _in(point[1])) == pytest.approx(expected, abs=0.01), tag


def test_the_gaps_reproduce_what_fixture_drain_reach_measured() -> None:
    """§1's arithmetic: straight-line plan distance from each drain point to the stack head.

    52.31" / 65.89" / 71.65", which `mep.fixture_drain_reach` reported as 52.3 / 65.9 /
    71.6 before the branches were authored. This is the check's 12" threshold being
    derived rather than asserted."""
    gaps = {tag: math.dist(point, _ROOT) for tag, point in _TERMINALS.items()}
    assert gaps["FX-S-SUITEBATH-WC"] == pytest.approx(52.31, abs=0.01)
    assert gaps["FX-S-SUITEBATH-LAV"] == pytest.approx(65.89, abs=0.01)
    assert gaps["FX-S-SUITEBATH-TUBSH"] == pytest.approx(71.65, abs=0.01)


# --- §2 the head budget ----------------------------------------------------------------

def test_the_collector_profile_is_the_note_s_arithmetic(catlin_model_ro) -> None:
    """§2's table: two legs, their lengths, their falls and their slopes.

    An invert is `start - slope x developed plan length` and nothing else, which is what
    `GravityProfile.invert_at` has to reproduce. Read off the authored run so the note and
    the house cannot drift apart."""
    run = next(r for r in catlin_model_ro.pipe_runs
               if r.tag == "PR-M-S-SUITE-WC-DRAIN")
    z = [_in(v) for v in run.z_m]
    path = [(_in(p[0]), _in(p[1])) for p in run.path]

    assert z[0] == pytest.approx(120.75, abs=0.001)   # the finished floor
    assert z[1] == pytest.approx(116.5, abs=0.001)    # the drop bottom, under the chord
    assert z[-1] == pytest.approx(112.0, abs=0.001)   # on the stack barrel

    south = math.dist(path[1], path[2])
    east = math.dist(path[2], path[3])
    assert south == pytest.approx(47.825, abs=0.001)
    assert east == pytest.approx(21.19, abs=0.001)
    assert (z[1] - z[2]) / (south / 12.0) == pytest.approx(0.784, abs=0.001)
    assert (z[2] - z[3]) / (east / 12.0) == pytest.approx(0.779, abs=0.001)

    developed_ft = (south + east) / 12.0
    assert developed_ft == pytest.approx(5.7513, abs=0.001)
    assert 0.25 * developed_ft == pytest.approx(1.4378, abs=0.001)


def test_the_two_arms_arrive_above_the_collector_they_tie_into(catlin_model_ro) -> None:
    """§2's closing paragraph. The collector's invert is interpolated at each tie station
    and each arm arrives above it — a side entry into the upper half of the 3", inside
    `_TIE_IN_INVERT_TOL_M` so `drain_tie_ins` still links the load."""
    runs = {r.tag: r for r in catlin_model_ro.pipe_runs}
    collector = runs["PR-M-S-SUITE-WC-DRAIN"]
    start, total_fall, developed = 116.5, 4.5, 69.015

    for tag, station, expected in (("PR-M-S-SUITE-LAV-DRAIN", 246.0, 116.198),
                                   ("PR-M-S-SUITE-TUB-DRAIN", 228.0, 115.025)):
        travelled = 250.625 - station
        invert = start - total_fall * (travelled / developed)
        assert invert == pytest.approx(expected, abs=0.001)
        arrival = _in(runs[tag].z_m[-1])
        assert arrival > invert
        assert arrival - invert < 1.0, tag
    del collector


# --- §3 the bay ------------------------------------------------------------------------

def test_the_bay_and_its_crossing_window_are_hand_derivable(catlin_model_ro) -> None:
    """§3, from the authored `JoistSpec`: lines at y = 16n, bay centres at 8 + 16n, a
    12.5" clear bay between 3.5" chords, and an 8 7/8" chord-to-chord crossing window
    from 109.625" to 118.5"."""
    from typehaus.resolve.mep_queries import clear_bay_width_m, joist_line_stations
    from typehaus.routing.corridors import crossing_window, floor_corridors

    floor = next(f for f in catlin_model_ro.floors if f.tag == "FS-S-WEST")
    assert floor.direction == "x"
    lines = {round(_in(v), 3) for v in joist_line_stations(floor)}
    assert {0.0, 16.0, 32.0, 48.0} <= lines
    assert _in(clear_bay_width_m(floor)) == pytest.approx(12.5, abs=0.001)

    low, high = crossing_window(catlin_model_ro, floor)
    assert _in(low) == pytest.approx(109.625, abs=0.001)
    assert _in(high) == pytest.approx(118.5, abs=0.001)
    assert _in(high - low) == pytest.approx(8.875, abs=0.001)

    bays = [c for c in floor_corridors(catlin_model_ro)
            if c.tag.startswith("FS-S-WEST")]
    assert bays and all(c.axis == "x" for c in bays)
    assert {round(_in(c.station), 3) for c in bays} >= {8.0, 24.0, 40.0}


def test_a_three_inch_pipe_fits_the_crossing_window_only_in_a_band(
        catlin_model_ro) -> None:
    """The number the collector's drop bottom is set by. A 3" pipe crossing the trusses
    has a centreline range of [111.125, 117.0]; 116.5 leaves 1/2" of crown margin and
    117.0 puts the crown exactly on the chord, which the router must treat as infeasible
    rather than tight."""
    from typehaus.routing.corridors import crossing_window

    floor = next(f for f in catlin_model_ro.floors if f.tag == "FS-S-WEST")
    low, high = crossing_window(catlin_model_ro, floor)
    radius = 1.5 * M_PER_IN
    assert _in(low + radius) == pytest.approx(111.125, abs=0.001)
    assert _in(high - radius) == pytest.approx(117.0, abs=0.001)


# --- §4 the escape graph ---------------------------------------------------------------

def _lattice() -> tuple[Graph, RoutingSpace]:
    """§4's world, built by hand: 3x3 at 24", the centre node absent, every edge 24" long.

    The graph is constructed rather than derived from `build_graph` on purpose — §4 is a
    statement about the SEARCH, and handing it the lattice is what makes the expansion
    table checkable without a house in the way.
    """
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
            if not (math.isclose(dx + dy, step, rel_tol=1e-9)):
                continue
            axis = "x" if dx > dy else "y"
            graph.edges.setdefault(a.index, {}).setdefault(axis, []).append(b.index)
            graph.edges.setdefault(b.index, {}).setdefault(axis, []).append(a.index)
            graph.weights[(a.index, b.index)] = 24.0
            graph.weights[(b.index, a.index)] = 24.0
            graph.terms[(a.index, b.index)] = {"travel_in": 24.0}
            graph.terms[(b.index, a.index)] = {"travel_in": 24.0}
    return graph, space


def test_the_escape_graph_expansion_matches_the_note() -> None:
    """§4's table, line for line: eight pops, cost 120, one bend, A -> D -> G -> H -> I.

    Both tie-breaks are exercised. Steps 5-6 turn on the node id (F's 4 before H's 6);
    step 8 turns on the axis (`+x` before `+y` for two states of the same node at the same
    f). Without either, A* is non-deterministic and the note could not pin it."""
    graph, space = _lattice()
    route = shortest_route(graph, space, start=0, goals={7})
    assert route is not None
    assert route.cost == pytest.approx(120.0, abs=1e-9)
    assert route.bends == 1
    assert route.expansions == 8
    assert route.nodes == [0, 3, 5, 6, 7]


def test_going_round_the_obstacle_costs_two_bends_not_four() -> None:
    """The reason candidate lines come from OFFSET obstacle edges rather than a uniform
    grid: there are no nodes to hug, so the cheap route is the L and not the staircase.
    Four bends would cost 96 more than one, and the found route takes one."""
    graph, space = _lattice()
    route = shortest_route(graph, space, start=0, goals={7})
    assert route is not None
    assert route.cost < 96.0 + 4 * space.cost.bend_in


def test_the_heuristic_never_over_estimates() -> None:
    """Admissibility, asserted rather than argued. Every penalty is additive and
    non-negative and the one discount is capped, so Manhattan x `heuristic_floor()` is a
    lower bound on the true remaining cost from every node the search touches."""
    graph, space = _lattice()
    route = shortest_route(graph, space, start=0, goals={7})
    assert route is not None
    goal = graph.nodes[7]
    remaining = route.cost
    for index, previous in zip(route.nodes, [None, *route.nodes], strict=False):
        node = graph.nodes[index]
        manhattan = (abs(node.x - goal.x) + abs(node.y - goal.y)) / 0.3048 * 12.0
        assert manhattan * space.cost.heuristic_floor() <= remaining + 1e-9
        if previous is not None:
            remaining -= graph.weights[(previous, index)]


def test_a_discount_makes_the_heuristic_floor_drop() -> None:
    """The trap the cap exists for. With a corridor discount configured, an inch of travel
    can cost less than an inch, so a heuristic scaled at 1.0 would over-estimate and A*
    would quietly stop being optimal."""
    assert RouteCost(corridor_discount_per_ft=0.0).heuristic_floor() == 1.0
    assert RouteCost(corridor_discount_per_ft=8.0).heuristic_floor() == pytest.approx(1 / 3)
    assert RouteCost(corridor_discount_per_ft=99.0).heuristic_floor() == 0.0


# --- §5 deepest first ------------------------------------------------------------------

#: §5's table: the rectilinear route each terminal would take, its start ceiling from §3's
#: chord window, and the arrival the root demands.
_SLACK_INPUTS = {
    "FX-S-SUITEBATH-WC": (3.0, 117.00),
    "FX-S-SUITEBATH-TUBSH": (1.5, 117.75),
    "FX-S-SUITEBATH-LAV": (1.5, 117.75),
}
_ROOT_Z = 115.5


def _slack(tag: str) -> tuple[float, float]:
    x, y = _TERMINALS[tag]
    rectilinear_ft = (abs(_ROOT[0] - x) + abs(_ROOT[1] - y)) / 12.0
    _diameter, ceiling = _SLACK_INPUTS[tag]
    return rectilinear_ft, ceiling - 0.25 * rectilinear_ft - _ROOT_Z


def test_the_slack_table_is_the_note_s() -> None:
    """§5's three rows, recomputed. Routes are rectilinear because that is what the router
    produces and what §4's lattice can express — not the straight lines of §1."""
    assert _slack("FX-S-SUITEBATH-WC") == pytest.approx((5.7513, 0.0622), abs=0.001)
    assert _slack("FX-S-SUITEBATH-TUBSH") == pytest.approx((8.3283, 0.1679), abs=0.001)
    assert _slack("FX-S-SUITEBATH-LAV") == pytest.approx((6.2250, 0.6937), abs=0.001)


def test_length_and_slack_order_the_terminals_differently() -> None:
    """The whole content of "deepest first": **length is not a proxy for slack.**

    The tub has the longest route and the second-tightest budget; the lavatory has a
    shorter route and four times the head. So the two orderings agree about the water
    closet — by luck, and by six inches of pipe — and disagree about everything after it.
    RSPH gives the second terminal the direct lane and makes the third bend round it, so
    which of the tub and the lavatory goes second decides whether the tighter of the two
    fits."""
    by_length = sorted(_TERMINALS, key=lambda tag: _slack(tag)[0])
    by_slack = sorted(_TERMINALS, key=lambda tag: _slack(tag)[1])
    assert by_length == ["FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-LAV",
                         "FX-S-SUITEBATH-TUBSH"]
    assert by_slack == ["FX-S-SUITEBATH-WC", "FX-S-SUITEBATH-TUBSH",
                        "FX-S-SUITEBATH-LAV"]
    assert by_length[0] == by_slack[0], "they agree about the closet, and only by luck"
    assert by_length[1:] == by_slack[1:][::-1]
