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
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.graph import Graph
    from typehaus.routing.space import RoutingSpace

#: ``(t0, t1, z0, z1, tag)``: over fractions ``[t0, t1]`` of an edge, centreline may not
#: be inside ``[z0, z1]``. A riser reports ``(0, 1, ...)`` for every prism at its point.
Obstacle = tuple[float, float, float, float, str]
Obstacles = Callable[[int, int], "list[Obstacle]"]

#: A run riding exactly on an inflated prism's boundary is at its clearance, not inside it.
_ERODE_M = 0.0015875


def prepare_falling(space: RoutingSpace, band: tuple[float, float],
                    model: ResolvedModel | None = None) -> None:
    """Add the walls' stud and plate zones, the rails and (with ``model``) the outside."""
    if space.members is not None:
        space.hard.extend(space.members.wall_prisms())
    space.hard.extend(rail_prisms(space))
    if model is not None:
        space.hard.extend(outside_prisms(model, space))
        space.hard.extend(exterior_prisms(model, space))
    split_banded(space, band)


def exterior_prisms(model: ResolvedModel, space: RoutingSpace) -> list:
    """An exterior insulated wall's stud cavity, at its own height, is no lane for a drain.

    Its soft price is read at the lattice's plane, which a falling run never shares: the
    main tree ran FX-M-BATH2-SH 92" along x = 4" at -7.6..-9.6", inside W-M-W3's cavity
    (-13.44" up, it drops to the foundation) against a -16" plane (§13).
    """
    from shapely.geometry import Polygon

    from typehaus.routing.obstacles import HardPrism, exterior_cavities

    grow = space.radius_m + space.clearance_m
    return [HardPrism(tag=tag, kind="exterior", footprint=Polygon(ring).buffer(grow),
                      z0_m=z0 - grow, z1_m=z1 + grow)
            for tag, ring, z0, z1 in exterior_cavities(model)]


def outside_prisms(model: ResolvedModel, space: RoutingSpace) -> list:
    """Within a floor's depth, past every deck there at that height is outside the house.

    A falling run searches a plan, and past the rim nothing stops it: the main tree laid a
    laundry drain at x = -1.44", outside W-B-W1 (§13). Each storey's decks are taken as
    their convex hull, so the bearing-line gaps between deck fields stay inside; a hull can
    only admit more, never refuse a lane a deck holds.
    """
    from shapely.geometry import MultiPoint, box

    from typehaus.resolve.overlay import difference, union_all
    from typehaus.routing.obstacles import HardPrism

    grow = space.radius_m + space.clearance_m
    minx, miny, maxx, maxy = space.bbox
    world = box(minx - 1.0, miny - 1.0, maxx + 1.0, maxy + 1.0)
    storeys: dict[str, tuple[list, float, float]] = {}
    for floor in model.floors:
        placed = [m.z0_m for m in floor.members if m.z0_m is not None]
        if len(floor.deck_outline) < 3 or not placed:
            continue
        points, z0, z1 = storeys.get(floor.storey, ([], float("inf"), float("-inf")))
        storeys[floor.storey] = (points + list(floor.deck_outline), min(z0, *placed),
                                 max(z1, floor.deck_z1_m))
    out = []
    for storey, (_points, z0, z1) in sorted(storeys.items()):
        inside = union_all(MultiPoint(p).convex_hull for p, a0, a1 in storeys.values()
                           if a0 <= z1 and a1 >= z0)
        outside = difference(world, inside).buffer(grow)
        if not outside.is_empty:
            out.append(HardPrism(tag=f"outside {storey}", kind="outside", footprint=outside,
                                 z0_m=z0 - grow, z1_m=z1 + grow))
    return out


def rail_prisms(space: RoutingSpace) -> list:
    """Floor rails at their real height: a falling run may cross a member, never ride it.

    ``RoutingSpace._rail_blocked`` reads the nominal plane, which a drain never shares
    with the rim it would ride; banded, each rail forbids the starts that put it inside.
    """
    from shapely.geometry import box

    from typehaus.routing.obstacles import HardPrism

    grow = space.radius_m + space.clearance_m
    out = []
    for axis, station, lo, hi, half, z0, z1, tag in space.rails:
        w = half + grow
        footprint = (box(lo, station - w, hi, station + w) if axis == "x"
                     else box(station - w, lo, station + w, hi))
        # Its own tag: a pardon names one member, never the whole floor's.
        out.append(HardPrism(tag=f"{tag} {axis}={station / 0.0254:.3f}in", kind="rail",
                             footprint=footprint, z0_m=z0 - grow, z1_m=z1 + grow,
                             applies=frozenset({axis})))
    return out


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
                   pardon: dict[int, frozenset[str]] | None = None,
                   start: int | None = None) -> Obstacles:
    """Per-edge banded obstacles, cached per undirected edge and reversed on the way back.

    ``pardon`` names, per terminal node, the prisms the terminal stands in at its own
    height — the step off it may pass through those, as ``graph.build_graph`` pardons a
    plan-hard terminal. Across such a prism (never along it), a step heading for a tie, or
    away from ``start``, is excused all the way through (§13).
    """
    from shapely import STRtree
    from shapely.geometry import LineString, Point

    prisms = list(space.banded)
    tree = STRtree([p.footprint for p in prisms]) if prisms else None
    eroded: dict[int, object] = {}
    excused = pardon or {}
    cache: dict[tuple[int, int], tuple[list[Obstacle], list, bool]] = {}
    # §13: the step INTO a tie crosses its own run, a wye's last inches. Pardoned nodes by
    # lattice line, so a crossing edge can find the tie it is heading for.
    ties_on: dict[tuple[bool, int], list[tuple[float, frozenset[str]]]] = {}
    for n, tags in excused.items():
        if n == start:
            continue  # the start is left, never approached
        node = graph.nodes[n]
        ties_on.setdefault((True, round(node.y / _ERODE_M)), []).append((node.x, tags))
        ties_on.setdefault((False, round(node.x / _ERODE_M)), []).append((node.y, tags))
    origin = graph.nodes[start] if start is not None else None
    leaving = excused.get(start, frozenset()) if start is not None else frozenset()
    # Every edge on one lattice line meets a prism in the same spans: clip the line once.
    spans: dict[tuple[int, bool, int], list[tuple[float, float]]] = {}

    def shape(index: int):
        if index not in eroded:
            eroded[index] = prisms[index].footprint.buffer(-_ERODE_M)
        return eroded[index]

    def line_spans(index: int, along_x: bool, across: float) -> list[tuple[float, float]]:
        key = (index, along_x, round(across / _ERODE_M))
        if key not in spans:
            x0, y0, x1, y1 = prisms[index].footprint.bounds
            ends = ([(x0 - 1.0, across), (x1 + 1.0, across)] if along_x
                    else [(across, y0 - 1.0), (across, y1 + 1.0)])
            spans[key] = _spans(LineString(ends).intersection(shape(index)), along_x)
        return spans[key]

    def obstacles(a: int, b: int) -> list[Obstacle]:
        key = (a, b) if a < b else (b, a)
        cached = cache.get(key)
        if cached is None:
            found: list[Obstacle] = []
            approach: list[tuple[int, tuple[float, ...]]] = []
            along_x = False
            if tree is not None:
                first, second = graph.nodes[key[0]], graph.nodes[key[1]]
                riser = abs(first.x - second.x) + abs(first.y - second.y) < _ERODE_M
                ex0, ex1 = excused.get(key[0], frozenset()), excused.get(key[1], frozenset())
                # A pardon excuses the step OFF a terminal; a level edge between two pardoned
                # nodes rides inside the very thing they stand in, so it excuses nothing.
                skip = (ex0 | ex1) if riser else (ex0 ^ ex1)
                along_x = abs(first.x - second.x) > abs(first.y - second.y)
                axis = "z" if riser else "x" if along_x else "y"
                line = (Point(first.plan) if riser
                        else LineString([first.plan, second.plan]))
                lo_end, hi_end, across = ((first.x, second.x, first.y) if along_x
                                          else (first.y, second.y, first.x))
                for index in tree.query(line):
                    prism = prisms[int(index)]
                    if prism.applies is not None and axis not in prism.applies:
                        continue
                    if prism.tag in skip:
                        continue
                    if riser:
                        if shape(int(index)).intersects(line):
                            found.append((0.0, 1.0, prism.z0_m, prism.z1_m, prism.tag))
                        continue
                    run = hi_end - lo_end
                    x0, y0, x1, y1 = prism.footprint.bounds
                    width = min(x1 - x0, y1 - y0) + _ERODE_M
                    for s0, s1 in line_spans(int(index), along_x, across):
                        start = max(min(lo_end, hi_end), s0)
                        end = min(max(lo_end, hi_end), s1)
                        if end > start:
                            t0, t1 = sorted(((start - lo_end) / run, (end - lo_end) / run))
                            found.append((t0, t1, prism.z0_m, prism.z1_m, prism.tag))
                            if s1 - s0 > width:
                                continue  # riding along a prism is never an approach
                            at = tuple(c for c, tags in ties_on.get(
                                (along_x, round(across / _ERODE_M)), ())
                                if prism.kind == "run" and prism.tag in tags
                                and s0 <= c <= s1)
                            away: tuple[float, ...] = ()
                            if prism.tag in leaving and origin is not None:
                                c, off = ((origin.x, origin.y) if along_x
                                          else (origin.y, origin.x))
                                if abs(off - across) < _ERODE_M and s0 <= c <= s1:
                                    away = (c,)
                            if at or away:
                                approach.append((len(found) - 1, at, away))
            cached = cache[key] = (found, approach, along_x)
        found, approach, along_x = cached
        if approach:  # into a tie, or out of the start; never the other way
            ca, cb = ((graph.nodes[a].x, graph.nodes[b].x) if along_x
                      else (graph.nodes[a].y, graph.nodes[b].y))
            drop = {i for i, at, away in approach
                    if any(abs(cb - c) < abs(ca - c) for c in at)
                    or any(abs(cb - c) > abs(ca - c) for c in away)}
            found = [e for i, e in enumerate(found) if i not in drop]
        if a < b:
            return found
        return [(1.0 - t1, 1.0 - t0, z0, z1, tag) for t0, t1, z0, z1, tag in found]

    return obstacles


def terminal_pardons(space: RoutingSpace, graph: Graph, at: dict[int, float],
                     start: int | None = None, tie_runs: frozenset[str] | None = None
                     ) -> dict[int, frozenset[str]]:
    """Per terminal node, the banded prisms it stands in at the given height.

    The ``start`` (a fixture in its wall) is pardoned whatever it stands in; a TIE only
    the run it lies on (``tie_runs``, when the caller knows it). A tie inside a rim, a wall
    or a neighbour's pipe is a line laid close to it, not a licence for every edge off it
    to pass through (§13).
    """
    from shapely.geometry import Point

    out: dict[int, frozenset[str]] = {}
    for index, z in at.items():
        node = graph.nodes[index]
        probe = Point(node.plan)
        tags = frozenset(p.tag for p in space.banded
                         if (start is None or index == start
                             or (p.kind == "run" and (tie_runs is None or p.tag in tie_runs)))
                         and p.z0_m <= z <= p.z1_m and p.footprint.covers(probe))
        if tags:
            out[index] = tags
    return out


def _spans(inside, along_x: bool) -> list[tuple[float, float]]:
    """The ``(lo, hi)`` ordinate ranges along the line of each piece of ``inside``."""
    k = 0 if along_x else 1
    out = []
    for piece in getattr(inside, "geoms", [inside]):
        if piece.is_empty or piece.length <= 0:
            continue
        ends = sorted((piece.coords[0][k], piece.coords[-1][k]))
        out.append((ends[0], ends[1]))
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
