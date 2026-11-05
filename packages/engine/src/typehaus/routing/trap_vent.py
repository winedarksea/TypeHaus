"""A fixture's trap arm and its vent, searched together, the way a plumber lays them.

UPC 1002.2: the arm runs from the trap at grade to a vent within Table 1002.2's developed
length, and it may not drop on the way — a fall of more than a pipe diameter before the vent
is an S-trap. UPC 905.2/905.3: the vent leaves above the drain's centreline and rises
vertically to 6" over the flood rim before any horizontal leg. So the search is three
pieces, each small:

1. :func:`arm_reach` — every node the arm reaches on its own level, held at grade from the
   trap and never dropping, within the limit. Its invert is known exactly (the trap weir
   less slope x developed), so each banded obstacle is tested at its real height.
2. :func:`vent_cost_to_go` — ONE backward search from the vent network over a rising
   lattice, horizontal only above the 905.3 line, so every candidate take-off has
   ``h_vent``.
3. ``gravity_search.sloped_route`` from ALL take-offs at once, each seeded with its arm and
   vent cost and the arm's invert as its ceiling, so one search picks the cheapest
   drain-plus-vent total.

``houses/catlin/notes/mep_drain_routing_basis.md`` §9 works FX-S-SUITEBATH-LAV by hand.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from typehaus.quantities import M_PER_IN
from typehaus.routing.graph import Graph
from typehaus.routing.gravity_band import Constraints, Obstacles
from typehaus.routing.search import turn_price
from typehaus.routing.space import RoutingSpace

_TOL_M = 0.0015875
#: An arm under a wall tees up through its plate from a floor's depth and a soffit under it.
_PLATE_REACH_M = 30 * M_PER_IN


@dataclass(frozen=True)
class ArmReach:
    """The cheapest way the arm reaches one node: cost, developed length, the node chain."""

    node: int
    cost: float
    developed_ft: float
    nodes: tuple[int, ...]


def arm_reach(graph: Graph, space: RoutingSpace, start: int, *, limit_ft: float,
              weir_m: float, grade_in_per_ft: float,
              obstacles: Obstacles | None = None,
              stopped: dict[str, int] | None = None,
              constraints: Constraints | None = None,
              radius_m: float = 0.0) -> dict[int, ArmReach]:
    """Every node the arm reaches level-by-level from ``start`` within ``limit_ft``.

    Horizontal edges only (a drop before the vent is an S-trap), each turn at its UPC 706
    price, and a banded prism forbids an edge where the arm's known invert —
    ``weir - slope x developed`` — passes inside it, as does a member window (a joist
    crossing, ``gravity_band.member_constraints``) the arm's outside does not fit at that
    station. ``stopped`` counts what held the arm, so a refusal can name it.
    """
    best: dict[tuple[int, str], float] = {(start, ""): 0.0}
    found: dict[int, ArmReach] = {start: ArmReach(start, 0.0, 0.0, (start,))}
    heap: list[tuple[float, int, str, float, tuple[int, ...]]] = [(0.0, start, "", 0.0,
                                                                   (start,))]
    while heap:
        cost, index, incoming, developed, chain = heapq.heappop(heap)
        if cost > best.get((index, incoming), float("inf")) + 1e-12:
            continue
        node = graph.nodes[index]
        for other, axis in graph.neighbours(index):
            if axis == "z":
                continue
            step = graph.weights.get((index, other))
            if step is None:
                continue
            target = graph.nodes[other]
            plan_ft = (abs(target.x - node.x) + abs(target.y - node.y)) / 0.3048
            reach = developed + plan_ft
            if reach > limit_ft + 1e-9:
                continue
            hit = None if obstacles is None else _blocked(
                obstacles(index, other), weir_m, grade_in_per_ft, developed, plan_ft)
            if hit is None and constraints is not None and not _fits(
                    constraints(index, other), weir_m, grade_in_per_ft, developed, plan_ft,
                    radius_m):
                hit = "a joist member window"
            if hit is not None:
                if stopped is not None:
                    stopped[hit] = stopped.get(hit, 0) + 1
                continue
            turn = turn_price(space, incoming, axis)
            if turn is None:
                continue
            candidate = cost + step + turn
            if candidate >= best.get((other, axis), float("inf")) - 1e-12:
                continue
            best[(other, axis)] = candidate
            path = (*chain, other)
            if other not in found or candidate < found[other].cost:
                found[other] = ArmReach(other, candidate, reach, path)
            heapq.heappush(heap, (candidate, other, axis, reach, path))
    return found


def _blocked(hits, weir_m: float, grade: float, developed_ft: float,
             plan_ft: float) -> str | None:
    for t0, t1, z0, z1, tag in hits:
        high = weir_m - (developed_ft + t0 * plan_ft) * grade * M_PER_IN
        low = weir_m - (developed_ft + t1 * plan_ft) * grade * M_PER_IN
        if high >= z0 - _TOL_M and low <= z1 + _TOL_M:
            return tag
    return None


def _fits(windows, weir_m: float, grade: float, developed_ft: float, plan_ft: float,
          radius_m: float) -> bool:
    """The arm's outside inside every member window it crosses, at that station's invert."""
    for fraction, low, high in windows:
        z = weir_m - (developed_ft + fraction * plan_ft) * grade * M_PER_IN
        if z - radius_m < low - _TOL_M or z + radius_m > high + _TOL_M:
            return False
    return True


def vent_cost_to_go(graph: Graph, goals: set[int], *, level_floor_m: float
                    ) -> dict[int, float]:
    """``h_vent`` for every node that can rise to ``goals``: one backward Dijkstra.

    A forward vent step may hold or gain elevation, never lose it, and may run level only
    at or above ``level_floor_m`` (UPC 905.3, 6" over the flood rim). Bends are not in ``h``;
    the chosen take-off's vent is re-searched forward and priced in full.
    """
    dist = dict.fromkeys(goals, 0.0)
    heap = [(0.0, g) for g in sorted(goals)]
    heapq.heapify(heap)
    while heap:
        cost, index = heapq.heappop(heap)
        if cost > dist.get(index, float("inf")) + 1e-12:
            continue
        here = graph.nodes[index]
        for other, axis in graph.neighbours(index):
            # Forward the vent steps other -> index: index must not be lower than other.
            there = graph.nodes[other]
            if here.z < there.z - _TOL_M:
                continue
            if axis != "z" and there.z < level_floor_m - _TOL_M:
                continue
            step = graph.weights.get((other, index))
            if step is None:
                continue
            candidate = cost + step
            if candidate < dist.get(other, float("inf")) - 1e-12:
                dist[other] = candidate
                heapq.heappush(heap, (candidate, other))
    return dist


def vent_size_m(drain_m: float) -> float:
    """UPC 904: a vent at least half its drain and never under 1 1/4", on a DWV size."""
    sizes = (1.25, 1.5, 2.0, 3.0, 4.0)
    want = max(1.25, drain_m / M_PER_IN / 2.0)
    return next(s for s in sizes if s >= want - 1e-9) * M_PER_IN


def takeoff_candidates(graph: Graph, space: RoutingSpace, reach: dict[int, ArmReach], *,
                       vent_od_m: float, rise_to_m: float, limit: int = 12) -> list[int]:
    """Arm-reachable nodes under or in a wall cavity that holds the vent's OD, cheapest first.

    UPC 905.2: the vent leaves the arm and rises; on this lattice that is a node on a wall
    corridor's station whose clear width takes the vent, and whose cavity carries it to the
    905.3 line ``rise_to_m`` — a wall that tops out under the fixture leaves the riser in the
    room. An arm in the floor depth may tee up through the plate, within ``_PLATE_REACH_M``.
    ``limit`` bounds the vent lattice.
    """
    out = [(arm.cost, index) for index, arm in reach.items()
           if takeoff_wall(space, graph.nodes[index], vent_od_m=vent_od_m,
                           rise_to_m=rise_to_m) is not None]
    return [index for _cost, index in sorted(out)[:limit]]


def takeoff_wall(space: RoutingSpace, node, *, vent_od_m: float, rise_to_m: float):
    """The wall corridor whose station ``node`` stands on and whose cavity holds the vent."""
    for corridor in space.corridors:
        if (corridor.kind != "wall" or corridor.clear_width_m + _TOL_M < vent_od_m
                or corridor.z1_m + _TOL_M < rise_to_m):
            continue
        across, along = (node.y, node.x) if corridor.axis == "x" else (node.x, node.y)
        if (abs(across - corridor.station) <= _TOL_M
                and corridor.lo_m - _TOL_M <= along <= corridor.hi_m + _TOL_M
                and corridor.z0_m - _PLATE_REACH_M <= node.z <= corridor.z1_m + _TOL_M):
            return corridor
    return None


def arm_invert_m(arm: ArmReach, weir_m: float, grade_in_per_ft: float) -> float:
    """The arm's centreline where it reaches ``arm.node``: the weir less its graded fall."""
    return weir_m - arm.developed_ft * grade_in_per_ft * M_PER_IN


def vent_path(graph: Graph, dist: dict[int, float], start: int, *,
              level_floor_m: float) -> list[int] | None:
    """The vent read back off :func:`vent_cost_to_go`: each step the one ``dist`` was set by.

    Following the distances forward keeps every rule the backward search applied (never
    falling, level only over the 905.3 line). Ties keep the axis already travelling.
    """
    if start not in dist:
        return None
    path, here, axis = [start], start, ""
    while dist[here] > 1e-9:
        best = None
        for other, step_axis in graph.neighbours(here):
            step = graph.weights.get((here, other))
            if step is None or other not in dist:
                continue
            a, b = graph.nodes[here], graph.nodes[other]
            if b.z < a.z - _TOL_M or (step_axis != "z" and a.z < level_floor_m - _TOL_M):
                continue  # the same two rules the backward search applied
            if abs(dist[other] + step - dist[here]) > 1e-6:
                continue
            key = (step_axis != axis, other)
            if best is None or key < best[0]:
                best = (key, other, step_axis)
        if best is None:
            return None
        _key, here, axis = best
        path.append(here)
    return path


def arm_seeds(reach: dict[int, ArmReach], takeoffs: dict[int, float],
              vented: frozenset[int] = frozenset(), *, keep: int = 2
              ) -> dict[int, tuple[float, float, tuple[int, ...]]]:
    """``GravityProblem.seeds``: the ``keep`` cheapest take-offs at arm + ``h_vent``, and each
    goal the arm itself reaches on a vented stack at the arm's cost alone.

    ``keep`` bounds the search, not the answer's legality: seeds with different (cost,
    developed) never dominate each other, so each one multiplies the drain's label front.
    """
    ranked = sorted((reach[n].cost + h, n) for n, h in takeoffs.items() if n in reach)
    out = {n: (total, reach[n].developed_ft, reach[n].nodes) for total, n in ranked[:keep]}
    out.update({g: (reach[g].cost, reach[g].developed_ft, reach[g].nodes)
                for g in vented if g in reach})
    return out
