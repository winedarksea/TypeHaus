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
"""

from __future__ import annotations

import heapq
from collections.abc import Callable
from dataclasses import dataclass, field

from typehaus.routing.graph import Graph
from typehaus.routing.space import RoutingSpace

#: Axis ordering for the tie-break, lowest first. Stated as data so the note and the code
#: cannot drift about which of two equal-cost routes wins.
_AXIS_ORDER = {"x": 0, "y": 1, "z": 2}


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

    def polyline(self) -> list[tuple[float, float, float]]:
        """The path with collinear interior vertices removed — what a proposal prints.

        A lattice path visits every candidate line it crosses; a pipe does not have a
        fitting at each of them. Collapsing runs of one axis into a single leg is the
        difference between a proposal a plumber reads and a list of coordinates.
        """
        if len(self.points) < 3:
            return list(self.points)
        out = [self.points[0]]
        for previous, current, following in zip(self.points, self.points[1:],
                                                self.points[2:], strict=False):
            if _axis_of(previous, current) != _axis_of(current, following):
                out.append(current)
        out.append(self.points[-1])
        return out


def shortest_route(graph: Graph, space: RoutingSpace, start: int,
                   goals: set[int]) -> Route | None:
    """Cheapest route from ``start`` to any node in ``goals``, or None if none exists.

    ``goals`` is a **set**, not a node, and that is a domain decision rather than a
    convenience: a drain's root is a vertical, and a vertical is a range of legal arrivals.
    A router that models the root as a point loses exactly the margin the oracle note's §5
    turns on — the suite bath's collector has 0.062" of slack against its stack HEAD and
    lands comfortably on the barrel 3 1/2" below it.
    """
    if start in goals:
        node = graph.nodes[start]
        return Route(nodes=[start], points=[(node.x, node.y, node.z)], cost=0.0)

    heuristic = _heuristic(graph, space, goals)
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
            turn = (space.cost.bend_in
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


def _heuristic(graph: Graph, space: RoutingSpace,
               goals: set[int]) -> Callable[[int], float]:
    """Manhattan plan + ``|Δz| × riser_per_ft``, scaled by the cost's own cheapest inch.

    Over a set of goals it is the minimum over them, which is still admissible: the true
    remaining cost is at least the cheapest way to the nearest goal.
    """
    floor = space.cost.heuristic_floor()
    riser = space.cost.riser_per_ft
    targets = [(graph.nodes[g].x, graph.nodes[g].y, graph.nodes[g].z) for g in goals]

    def estimate(index: int) -> float:
        node = graph.nodes[index]
        return min(((abs(node.x - gx) + abs(node.y - gy)) / 0.3048 * 12.0
                    + abs(node.z - gz) / 0.3048 * 12.0 * riser) * floor
                   for gx, gy, gz in targets)

    return estimate


def _rebuild(graph: Graph, space: RoutingSpace,
             came: dict[tuple[int, str], tuple[int, str]],
             state: tuple[int, str], expansions: int) -> Route:
    chain = [state]
    while state in came:
        state = came[state]
        chain.append(state)
    chain.reverse()
    indices = [index for index, _axis in chain]
    points = [(graph.nodes[i].x, graph.nodes[i].y, graph.nodes[i].z) for i in indices]

    terms: dict[str, float] = {}
    bends = 0
    total = 0.0
    for (a, axis_a), (b, axis_b) in zip(chain, chain[1:], strict=False):
        total += graph.weights.get((a, b), 0.0)
        for key, value in graph.terms.get((a, b), {}).items():
            terms[key] = terms.get(key, 0.0) + value
        if axis_a and axis_b != axis_a:
            bends += 1
            total += space.cost.bend_in
    if bends:
        terms["bend_in"] = bends * space.cost.bend_in
    return Route(nodes=indices, points=points, cost=total, terms=terms,
                 bends=bends, expansions=expansions)


def _axis_of(a: tuple[float, float, float], b: tuple[float, float, float]) -> str:
    if abs(b[0] - a[0]) > 1e-9:
        return "x"
    if abs(b[1] - a[1]) > 1e-9:
        return "y"
    return "z"
