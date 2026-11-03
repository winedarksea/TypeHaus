"""A falling run's obstacles as forbidden START intervals, not as one plane it is tested in.

A drain searches in plan at its tie's elevation while its real invert stands
``slope x remaining`` above it, so a duct over the bay at the drain's true height was never
seen and a prism at the tie's height blocked a run that would pass over it. Here each hard
prism that spans only part of the run's possible band ``[tie, ceiling]`` leaves the plan
obstacle set and becomes, per lattice edge, the interval of start elevations that would put
the centreline inside it. ``gravity_search`` subtracts that interval from a label's band of
legal starts; a forbidden interval in the middle splits one label into an "under" and an
"over" label, and the Pareto frontier keeps both.

Prisms are already inflated by radius + clearance, so the test is on the centreline. A
prism covering the whole band stays a plan obstacle: no start passes it.
``houses/catlin/notes/mep_drain_routing_basis.md`` §8a is the hand-worked oracle.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.routing.graph import Graph
    from typehaus.routing.space import RoutingSpace

#: ``(t0, t1, z0, z1, tag)``: over fractions ``[t0, t1]`` of an edge, centreline may not
#: be inside ``[z0, z1]``. A riser reports ``(0, 1, ...)`` for every prism at its point.
Obstacle = tuple[float, float, float, float, str]
Obstacles = Callable[[int, int], "list[Obstacle]"]

#: A run riding exactly on an inflated prism's boundary is at its clearance, not inside it.
_ERODE_M = 0.0015875


def prepare_falling(space: RoutingSpace, band: tuple[float, float]) -> None:
    """Add the walls' illegal stud and plate zones, then split the set by ``band``."""
    if space.members is not None:
        space.hard.extend(space.members.wall_prisms())
    split_banded(space, band)


def split_banded(space: RoutingSpace, band: tuple[float, float]) -> None:
    """Move every hard prism spanning only part of ``band`` into ``space.banded``.

    Prisms wholly outside the band cannot touch the centreline and are dropped from the
    plan set; prisms covering it stay plan-hard. Indexes are reset.
    """
    low, high = band
    keep, banded = [], []
    for prism in space.hard:
        if prism.applies is None and prism.z0_m <= low and prism.z1_m >= high:
            keep.append(prism)
        elif prism.z1_m >= low and prism.z0_m <= high:
            banded.append(prism)
    space.hard = keep
    space.banded = banded
    space.plan_band = band
    space._hard_index = None
    space._exact = None
    space._blocked_memo.clear()


def band_obstacles(space: RoutingSpace, graph: Graph,
                   pardon: dict[int, frozenset[str]] | None = None) -> Obstacles:
    """Per-edge banded obstacles, cached per undirected edge and reversed on the way back.

    ``pardon`` names, per terminal node, the prisms the terminal stands in at its own
    height — the step off it may pass through those, as ``graph.build_graph`` pardons a
    plan-hard terminal.
    """
    from shapely import STRtree, prepared
    from shapely.geometry import LineString, Point

    prisms = list(space.banded)
    tree = STRtree([p.footprint for p in prisms]) if prisms else None
    eroded: dict[int, object] = {}
    excused = pardon or {}
    cache: dict[tuple[int, int], list[Obstacle]] = {}

    def shape(index: int):
        if index not in eroded:
            eroded[index] = prepared.prep(prisms[index].footprint.buffer(-_ERODE_M))
        return eroded[index]

    def obstacles(a: int, b: int) -> list[Obstacle]:
        key = (a, b) if a < b else (b, a)
        found = cache.get(key)
        if found is None:
            found = []
            if tree is not None:
                first, second = graph.nodes[key[0]], graph.nodes[key[1]]
                skip = excused.get(key[0], frozenset()) | excused.get(key[1], frozenset())
                riser = abs(first.x - second.x) + abs(first.y - second.y) < _ERODE_M
                axis = ("z" if riser else
                        "x" if abs(first.x - second.x) > abs(first.y - second.y) else "y")
                line = (Point(first.plan) if riser
                        else LineString([first.plan, second.plan]))
                for index in tree.query(line):
                    prism = prisms[int(index)]
                    if prism.applies is not None and axis not in prism.applies:
                        continue
                    if prism.tag in skip or not shape(int(index)).intersects(line):
                        continue
                    if riser:
                        found.append((0.0, 1.0, prism.z0_m, prism.z1_m, prism.tag))
                        continue
                    for t0, t1 in _fractions(line, prism.footprint.buffer(-_ERODE_M)):
                        found.append((t0, t1, prism.z0_m, prism.z1_m, prism.tag))
            cache[key] = found
        if a < b:
            return found
        return [(1.0 - t1, 1.0 - t0, z0, z1, tag) for t0, t1, z0, z1, tag in found]

    return obstacles


def terminal_pardons(space: RoutingSpace, graph: Graph,
                     at: dict[int, float]) -> dict[int, frozenset[str]]:
    """Per terminal node, the banded prisms it stands in at the given height."""
    from shapely.geometry import Point

    out: dict[int, frozenset[str]] = {}
    for index, z in at.items():
        node = graph.nodes[index]
        probe = Point(node.plan)
        tags = frozenset(p.tag for p in space.banded
                         if p.z0_m <= z <= p.z1_m and p.footprint.covers(probe))
        if tags:
            out[index] = tags
    return out


def _fractions(line, footprint) -> list[tuple[float, float]]:
    """``(t0, t1)`` along ``line`` for each piece of it inside ``footprint``."""
    from shapely.geometry import Point

    inside = line.intersection(footprint)
    if inside.is_empty:
        return []
    pieces = getattr(inside, "geoms", [inside])
    out = []
    for piece in pieces:
        if piece.length <= 0:
            continue
        ends = [line.project(Point(c)) / line.length
                for c in (piece.coords[0], piece.coords[-1])]
        out.append((min(ends), max(ends)))
    return out


def subtract(band: tuple[float, float], forbidden: tuple[float, float],
             tol: float) -> list[tuple[float, float]]:
    """``band`` less ``forbidden``: zero, one or two intervals ("under", "over")."""
    low, high = band
    f0, f1 = forbidden
    if f1 < low - tol or f0 > high + tol:
        return [band]
    out = []
    if f0 > low + tol:
        out.append((low, f0))
    if f1 < high - tol:
        out.append((f1, high))
    return out
