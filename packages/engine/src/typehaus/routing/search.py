"""Weighted A* over ``(node, incoming axis)``, and why the axis is in the state.

The bend penalty is a function of the **turn**, not of the node. A node reached travelling
east and the same node reached travelling north have different futures — one can continue
east for free, the other cannot — so they are different states. A search that keeps only
the node produces staircases: at every node it has already forgotten which way it came,
so a turn costs nothing it can see, and the cheapest path it finds is the one with the
most of them.

The heuristic is Manhattan plan distance plus ``|Δz| × riser_per_ft``, scaled by
:meth:`RouteCost.heuristic_floor` and carrying **no penalty terms at all**. That is what
keeps it admissible: every penalty in :mod:`typehaus.routing.cost` is additive and
non-negative and the one discount is capped, so the cheapest an inch of travel can be is
known, and ``h`` never over-estimates. Adding a room penalty to ``h`` — tempting, since it
would expand fewer nodes — would make A* stop being optimal without saying so.

``houses/catlin/notes/mep_drain_routing_basis.md`` §4 works one search by hand: a 3x3
lattice, one blocked node, ``BEND = 24``, eight pops, and the winning path's cost. The
tie-break stated there — ``(f, node id, axis)`` ascending with ``+x`` before ``+y`` — is
implemented here and is not an implementation detail: without it A* is non-deterministic
and no oracle can pin it.

**A bendable tube searches labels, not states** (``_bent_route``). Its turn is a field bend
only where the straight either side holds the bend's tangent ``R tan(45°) = R`` — the
take-off's own rule (``resolve/mep_fittings._bend``: all of an end leg, half of a leg between
two turns) — so a label carries its SIGNED heading, the straight since the last turn and what
began that leg, Pareto-pruned per ``(node, heading)``. A reversal is refused: a 180 in place
is two coincident legs, and the lattice draws any real U as two 90s with a leg between.
With no radius the ``(node, axis)`` search below is unchanged, so §4 stays pinned.
"""

from __future__ import annotations

import heapq
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, NamedTuple

import numpy as np

from typehaus.routing.graph import Graph
from typehaus.routing.space import RoutingSpace

#: Axis ordering for the tie-break, lowest first. Stated as data so the note and the code
#: cannot drift about which of two equal-cost routes wins.
_AXIS_ORDER = {"x": 0, "y": 1, "z": 2}

#: A step losing less than this is level: the 1/16" grid the repo authors on.
_RISE_TOL_M = 0.0015875

_INDEX = {"x": 0, "y": 1, "z": 2}
_EPS_M = 1e-9


@dataclass
class Route:
    """A found path, its cost, and where the cost went.

    ``terms`` is the whole content of ``--explain``. Every value is in inches of equivalent
    travel, the one unit :mod:`typehaus.routing.cost` states everything in, so the
    breakdown is comparable to the route's own length.
    """

    nodes: list[int]
    points: list[tuple[float, float, float]]
    cost: float
    terms: dict[str, float] = field(default_factory=dict)
    bends: int = 0
    #: How many states were popped. Reported rather than hidden: it is the number that says
    #: whether a heuristic is doing any work, and §4's oracle asserts it exactly.
    expansions: int = 0
    #: Which corridors the winning legs rode, in the order first met. A proposal prints
    #: ``floor_ref=``/``soffit_ref=`` from these, so what the run claims about where it is
    #: concealed is what the search actually priced it at rather than a later guess.
    corridor_tags: tuple[str, ...] = ()
    #: A falling run's chosen start elevation (``gravity_search``): the lowest its legal
    #: band allows. None for every other search, and for a drain the profile may build
    #: from the arrival upward.
    start_m: float | None = None
    #: Where a fixture's trap arm closed with a vent take-off (``gravity_search``), or None.
    takeoff: int | None = None
    #: That take-off's plan point: the arm is laid off the weir to here, then drops.
    takeoff_xy: tuple[float, float] | None = None
    #: The arm ended on a 908.2 wet vent instead (``resolve/mep_wet_tie.WetTie``), or None.
    wet: Any = None
    #: The vent side of a fixture's pair (``cli/route_fixture_vent.VentContext``), or None.
    vent: Any = None
    #: The grade a condensate route was laid at, and why (``gravity.graded_route``), or unset.
    grade_in_per_ft: float | None = None
    grade_note: str = ""

    def polyline(self) -> list[tuple[float, float, float]]:
        """The path with collinear interior vertices removed — what a proposal prints.

        A lattice path visits every candidate line it crosses; a pipe does not have a
        fitting at each of them. Collapsing runs of one axis into a single leg is the
        difference between a proposal a plumber reads and a list of coordinates. A vertex
        where the run turns back along its axis stays: a lav arm out to its wall tee and
        back under the floor is two legs, and its take-off is that vertex.
        """
        if len(self.points) < 3:
            return list(self.points)
        out = [self.points[0]]
        for previous, current, following in zip(self.points, self.points[1:],
                                                self.points[2:], strict=False):
            if (_axis_of(previous, current) != _axis_of(current, following)
                    or _reverses(previous, current, following)):
                out.append(current)
        out.append(self.points[-1])
        return out


def shortest_route(graph: Graph, space: RoutingSpace, start: int,
                   goals: set[int], *, rising: bool = False) -> Route | None:
    """Cheapest route from ``start`` to any node in ``goals``, or None if none exists.

    ``rising`` refuses every step that loses elevation (``trades.pipe.rises``): a vent
    searched in 3-D otherwise dips under a duct and climbs back, and on catlin one
    alternative for ``PR-M-WC-VENT`` fell about ten feet.

    ``goals`` is a **set**, not a node, and that is a domain decision rather than a
    convenience: a drain's root is a vertical, and a vertical is a range of legal arrivals.
    A router that models the root as a point loses exactly the margin the oracle note's §5
    turns on — the suite bath's collector has 0.062" of slack against its stack HEAD and
    lands comfortably on the barrel 3 1/2" below it.
    """
    if start in goals:
        node = graph.nodes[start]
        return Route(nodes=[start], points=[(node.x, node.y, node.z)], cost=0.0)

    if not goals:  # nothing to reach: the heuristic is a min over goals
        return None
    heuristic = _heuristic(graph, space, goals)
    if space.bend_radius_m > 0.0:
        return _bent_route(graph, space, start, goals, heuristic, rising)
    # The heap entry carries ``g`` as its LAST element, after the unique ``counter``, so it
    # takes no part in the ordering and the tie-break stays exactly ``(f, node id, axis)``
    # — which is what §4 of the oracle note pins.
    open_heap: list[tuple[float, int, int, int, str, float]] = []
    counter = 0
    best: dict[tuple[int, str], float] = {}
    came: dict[tuple[int, str], tuple[int, str]] = {}

    for axis in ("x", "y", "z"):
        best[(start, axis)] = 0.0
    heapq.heappush(open_heap,
                   (heuristic(start), start, _AXIS_ORDER["x"], counter, "", 0.0))

    expansions = 0
    while open_heap:
        _f, index, _axis_key, _seq, incoming, popped_g = heapq.heappop(open_heap)
        state = (index, incoming)
        # **Lazy deletion, and it is a correctness fix rather than a speed one.** A state
        # can be pushed twice and relaxed lower in between; taking ``best[state]`` at pop
        # time then pairs one state's g with another's predecessor in ``came``, and the
        # reconstructed path doubles back on itself. Carrying g with the entry and dropping
        # a stale pop is what keeps g and came describing the same path.
        if popped_g > best.get(state, float("inf")) + 1e-12:
            continue
        expansions += 1
        if index in goals:
            return _rebuild(graph, space, came, state, expansions)
        current = popped_g
        for other, axis in graph.neighbours(index):
            step = graph.weights.get((index, other))
            if step is None:
                continue
            if rising and graph.nodes[other].z < graph.nodes[index].z - _RISE_TOL_M:
                continue
            turn = (bend_price(graph, space, came.get(state, (None,))[0], index, other)
                    if incoming and axis != incoming else 0.0)
            candidate = current + step + turn
            key = (other, axis)
            if candidate >= best.get(key, float("inf")) - 1e-12:
                continue
            best[key] = candidate
            came[key] = state
            counter += 1
            heapq.heappush(open_heap,
                           (candidate + heuristic(other), other,
                            _AXIS_ORDER[axis], counter, axis, candidate))
    return None


class _Label(NamedTuple):
    cost: float
    straight: float  # laid since the last turn, capped at the most any rule asks (2R)
    heading: str     # signed ("+x", "-z"); "" at the start
    kind: int        # what began the leg: 0 the run's start, 1 a fitting, 2 a bend


def _bent_route(graph: Graph, space: RoutingSpace, start: int, goals: set[int],
                heuristic: Callable[[int], float], rising: bool) -> Route | None:
    """``shortest_route`` for a bendable tube: every bend's tangent fits its straights."""
    tangent = space.bend_radius_m  # every lattice turn is 90 degrees
    cap = 2.0 * tangent
    # Straight a leg begun by kind 0/1/2 must hold before a bend, a fitting, the goal.
    bend_need, fit_need, goal_need = (tangent, cap, cap), (0.0, 0.0, cap), (0.0, 0.0, tangent)
    fitting, bent = space.cost.bend_in, space.cost.pex_bend_in
    frontier: dict[tuple[int, str], list[tuple[_Label, int]]] = {}
    alive: dict[int, tuple[int, _Label]] = {}
    came: dict[int, int] = {}
    node_of: dict[int, int] = {}
    open_heap: list[tuple[float, int, int, int]] = []
    arcs: dict[tuple[int, int, str], bool] = {}  # whether a turn's arc clears
    counter = 0

    def push(node: int, label: _Label, parent: int | None) -> None:
        nonlocal counter
        kept = frontier.setdefault((node, label.heading), [])
        pruned = False
        for other, lid in kept:
            if _dominates(other, label):
                return
            if _dominates(label, other):
                alive.pop(lid, None)
                pruned = True
        if pruned:
            kept[:] = [entry for entry in kept if entry[1] in alive]
        counter += 1
        kept.append((label, counter))
        alive[counter] = (node, label)
        node_of[counter] = node
        if parent is not None:
            came[counter] = parent
        heapq.heappush(open_heap, (label.cost + heuristic(node), node,
                                   _AXIS_ORDER.get(label.heading[-1:], 0), counter))

    push(start, _Label(0.0, 0.0, "", 0), None)
    expansions = 0
    while open_heap:
        _f, index, _key, lid = heapq.heappop(open_heap)
        entry = alive.get(lid)
        if entry is None:
            continue  # dominated after it was pushed
        label = entry[1]
        expansions += 1
        if index in goals and label.straight >= goal_need[label.kind] - _EPS_M:
            chain = [lid]
            while chain[-1] in came:
                chain.append(came[chain[-1]])
            nodes = [node_of[i] for i in reversed(chain)]
            route = price_route(graph, space, nodes)
            route.expansions = expansions
            return route
        incoming, a = label.heading, graph.nodes[index]
        for other, axis in graph.neighbours(index):
            step = graph.weights.get((index, other))
            if step is None:
                continue
            b = graph.nodes[other]
            if rising and b.z < a.z - _RISE_TOL_M:
                continue
            delta = (b.x - a.x, b.y - a.y, b.z - a.z)[_INDEX[axis]]
            heading = ("+" if delta > 0 else "-") + axis
            leg = min(abs(delta), cap)
            if not incoming or heading == incoming:
                push(other, _Label(label.cost + step, min(label.straight + leg, cap),
                                   heading, label.kind), lid)
                continue
            if incoming[1] == axis:
                continue  # a reversal
            have, cost = label.straight, label.cost + step
            if have >= fit_need[label.kind] - _EPS_M:
                push(other, _Label(cost + fitting, leg, heading, 1), lid)
            if have >= bend_need[label.kind] - _EPS_M and bent < fitting:
                made = _Label(cost + bent, leg, heading, 2)
                if any(_dominates(kept, made) for kept, _lid
                       in frontier.get((other, heading), ())):
                    continue  # the arc test is the search's dearest call: skip it
                turn = (index, other, incoming)
                clears = arcs.get(turn)
                if clears is None:
                    clears = arcs[turn] = bend_price(graph, space, None, index, other,
                                                     heading=incoming) < fitting
                if clears:
                    push(other, made, lid)
    return None


def _dominates(first: _Label, second: _Label) -> bool:
    """No dearer, no less straight, and begun by nothing stricter (start < fitting < bend)."""
    return (first.cost <= second.cost + 1e-12 and first.straight >= second.straight - _EPS_M
            and first.kind <= second.kind)


def _heuristic(graph: Graph, space: RoutingSpace,
               goals: set[int]) -> Callable[[int], float]:
    """Manhattan plan + ``|Δz| × riser_per_ft``, scaled by the cost's own cheapest inch.

    Over a set of goals it is the minimum over them, which is still admissible: the true
    remaining cost is at least the cheapest way to the nearest goal.
    """
    floor = space.cost.heuristic_floor(rack=any(c.kind == "rack" for c in space.corridors))
    riser = space.cost.riser_per_ft
    # Vectorised over the goals and memoised per node: same IEEE operations in the same
    # order as the scalar form, so every f value (and so every tie-break) is bit-identical.
    gx = np.array([graph.nodes[g].x for g in goals])
    gy = np.array([graph.nodes[g].y for g in goals])
    gz = np.array([graph.nodes[g].z for g in goals])
    memo: dict[int, float] = {}

    def estimate(index: int) -> float:
        hit = memo.get(index)
        if hit is None:
            node = graph.nodes[index]
            hit = float((((np.abs(node.x - gx) + np.abs(node.y - gy)) / 0.3048 * 12.0
                          + np.abs(node.z - gz) / 0.3048 * 12.0 * riser) * floor).min())
            memo[index] = hit
        return hit

    return estimate


def _rebuild(graph: Graph, space: RoutingSpace,
             came: dict[tuple[int, str], tuple[int, str]],
             state: tuple[int, str], expansions: int) -> Route:
    chain = [state]
    while state in came:
        state = came[state]
        chain.append(state)
    chain.reverse()
    route = price_route(graph, space, [index for index, _axis in chain])
    return Route(nodes=route.nodes, points=route.points, cost=route.cost,
                 terms=route.terms, bends=route.bends, expansions=expansions,
                 corridor_tags=route.corridor_tags)


def bend_price(graph: Graph, space: RoutingSpace, before: int | None, at: int,
               after: int, *, heading: str = "") -> float:
    """A pressure turn at ``at``: ``pex_bend_in`` where the tube bends, else ``bend_in``.

    A bendable tube (``space.bend_radius_m``) bends where the quarter arc of that radius
    between the two legs clears every hard prism; anything else is a fitting. The way in is
    the signed ``heading`` when given (the label's leg), else ``before`` -> ``at``. Whether
    the straights hold the tangents is the caller's rule, not this one's.
    """
    radius = space.bend_radius_m
    if radius <= 0.0 or (before is None and not heading):
        return space.cost.bend_in
    b, c = graph.nodes[at], graph.nodes[after]
    if heading:
        u = tuple((1.0 if heading[0] == "+" else -1.0) if k == _INDEX[heading[1]] else 0.0
                  for k in range(3))
    else:
        a = graph.nodes[before]
        u = _unit((b.x - a.x, b.y - a.y, b.z - a.z))
    v = _unit((c.x - b.x, c.y - b.y, c.z - b.z))
    # Centre one radius back along the way in and one out along the way out.
    centre = tuple(p - radius * ui + radius * vi
                   for p, ui, vi in zip((b.x, b.y, b.z), u, v, strict=True))
    for k in range(5):
        t = k * math.pi / 8.0
        p = tuple(o - radius * math.cos(t) * vi + radius * math.sin(t) * ui
                  for o, ui, vi in zip(centre, u, v, strict=True))
        if space.blocked(p[:2], p[2]) is not None:
            return space.cost.bend_in
    return space.cost.pex_bend_in


def _unit(d: tuple[float, float, float]) -> tuple[float, float, float]:
    n = math.sqrt(sum(x * x for x in d)) or 1.0
    return (d[0] / n, d[1] / n, d[2] / n)


def turn_price(space: RoutingSpace, before: str, after: str,
               service: str = "drain") -> float | None:
    """A lattice turn from axis ``before`` to ``after`` at its UPC 706 price, or None.

    For a drain a ``z`` leg is falling (the gravity search never rises), so level-to-``z``
    is a quarter bend at ``bend_in`` and every other change a sweep at ``dwv_sweep_in``.
    """
    if not before or before == after:
        return 0.0
    return space.cost.turn_cost(service, _CLASS[before], _CLASS[after])


_CLASS = {"x": "level", "y": "level", "z": "down"}


def price_route(graph: Graph, space: RoutingSpace, nodes: list[int],
                service: str = "") -> Route:
    """Price a node chain against THIS graph's weights — the alternatives' honest ruler.

    Extracted from ``_rebuild`` because a penalty re-search finds a route on a graph whose
    weights have been multiplied, and a route quoted at its penalised price is not
    comparable to the one it is being offered against. :mod:`typehaus.routing.alternatives`
    searches on the penalised graph and prices on the original, so what a reader compares
    is two real costs.

    The axis of each step is re-derived from the geometry rather than carried, which is the
    same function ``polyline`` uses and cannot disagree with the points it is given.
    """
    points = [(graph.nodes[i].x, graph.nodes[i].y, graph.nodes[i].z) for i in nodes]
    axes = [_axis_of(a, b) for a, b in zip(points, points[1:], strict=False)]

    terms: dict[str, float] = {}
    corridors: list[str] = []
    bends = 0
    total = 0.0
    bend_total = 0.0
    bent = space.bend_radius_m > 0.0 and not service
    turns = (_tube_turns(graph, space, nodes, points, axes) if bent else {})
    for step, (a, b) in enumerate(zip(nodes, nodes[1:], strict=False)):
        total += graph.weights.get((a, b), 0.0)
        for key, value in graph.terms.get((a, b), {}).items():
            terms[key] = terms.get(key, 0.0) + value
        tag = graph.corridors.get((a, b))
        if tag is not None and tag not in corridors:
            corridors.append(tag)
        if bent:
            if step in turns:
                price, count = turns[step]
                bends += count
                bend_total += price
        elif step and axes[step] != axes[step - 1]:
            bends += 1
            price = (turn_price(space, axes[step - 1], axes[step], service) if service
                     else bend_price(graph, space, nodes[step - 1], nodes[step],
                                     nodes[step + 1]))
            bend_total += space.cost.bend_in if price is None else price
    total += bend_total
    if bends:
        terms["bend_in"] = bend_total
    return Route(nodes=list(nodes), points=points, cost=total, terms=terms,
                 bends=bends, corridor_tags=tuple(corridors))


def _tube_turns(graph: Graph, space: RoutingSpace, nodes: list[int],
                points: list[tuple[float, float, float]],
                axes: list[str]) -> dict[int, tuple[float, int]]:
    """``step -> (price, bends)`` for a bendable tube, by ``mep_fittings._bend``'s rule.

    A turn bends where its arc clears and ``R`` fits all of an end leg and half of a leg
    between two turns; else it is a fitting. A reversal is two fittings.
    """
    at = [s for s in range(1, len(axes))
          if axes[s] != axes[s - 1] or _reverses(points[s - 1], points[s], points[s + 1])]
    ends = [0, *at, len(points) - 1]
    fitting, radius = space.cost.bend_in, space.bend_radius_m
    out: dict[int, tuple[float, int]] = {}
    for k, s in enumerate(at, start=1):
        if _reverses(points[s - 1], points[s], points[s + 1]):
            out[s] = (2.0 * fitting, 2)
            continue
        legs = []
        for lo, hi in ((ends[k - 1], s), (s, ends[k + 1])):
            shared = lo > 0 and hi < len(points) - 1
            legs.append(math.dist(points[lo], points[hi]) / (2.0 if shared else 1.0))
        price = (bend_price(graph, space, nodes[s - 1], nodes[s], nodes[s + 1])
                 if radius <= min(legs) + _EPS_M else fitting)
        out[s] = (price, 1)
    return out


def _reverses(a: tuple[float, float, float], b: tuple[float, float, float],
              c: tuple[float, float, float]) -> bool:
    return sum((b[i] - a[i]) * (c[i] - b[i]) for i in range(3)) < 0


def _axis_of(a: tuple[float, float, float], b: tuple[float, float, float]) -> str:
    if abs(b[0] - a[0]) > 1e-9:
        return "x"
    if abs(b[1] - a[1]) > 1e-9:
        return "y"
    return "z"
