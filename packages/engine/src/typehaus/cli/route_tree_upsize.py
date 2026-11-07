"""Rip-up rule P8: a laid drain branch re-laid one size up, near its lane, to its own tie.

``houses/catlin/notes/mep_tree_ripup_basis.md`` §4.3: BATH2-TUB cannot tie onto BATH2-SH
because 2 + 2 DFU needs 2" (UPC Table 703.2) and the shower was laid at 1 1/2". The branch
is searched again at the larger outside by the same sloped search, in a world built a
couple of feet round its old lane (so it may shift off a member it now hits, and no
further), from its drain point to the tie it already had. The rest of the tree stands."""

from __future__ import annotations

from typing import Any

#: Nominal DWV sizes, inches: "one size up" walks this ladder.
_DWV_IN = (1.25, 1.5, 2.0, 2.5, 3.0, 4.0)


def next_size(size_m: float) -> float | None:
    """The next nominal DWV size above ``size_m``, or None past the ladder's top."""
    return next((d * 0.0254 for d in _DWV_IN if d * 0.0254 > size_m + 1e-6), None)


def on_lattice(graph: Any, found: Any, laid: list[tuple[float, float, float]],
               tolerance: float) -> Any:
    """``found`` (searched in another lattice) as the nodes of ``graph`` that lie on its
    laid line, in order along it: what reachability and tie owners read."""
    from dataclasses import replace

    from typehaus.cli.cmd_route_tree import _line_nodes

    plan = [p[:2] for p in laid]
    starts = [0.0]
    for (ax, ay), (bx, by) in zip(plan, plan[1:], strict=False):
        starts.append(starts[-1] + abs(bx - ax) + abs(by - ay))

    def along(index: int) -> float:
        node = graph.nodes[index]
        best = (float("inf"), 0.0)
        for k, ((ax, ay), (bx, by)) in enumerate(zip(plan, plan[1:], strict=False)):
            span = abs(bx - ax) + abs(by - ay)
            t = 0.0 if span <= 0 else max(0.0, min(1.0, (abs(node.x - ax) + abs(node.y - ay))
                                                     / span))
            px, py = ax + t * (bx - ax), ay + t * (by - ay)
            best = min(best, (abs(px - node.x) + abs(py - node.y), starts[k] + t * span))
        return best[1]

    return replace(found, nodes=sorted(_line_nodes(graph, plan, tolerance), key=along))


def widen(model: Any, branches: Any, points: list[tuple[float, float, float]],
          size: float, arrival: float, tie_tag: str | None, *, target: str,
          ceiling: float, root_z: float, world: Any, max_labels: int) -> Any:
    """The branch re-laid at ``size`` from its drain point to the tie it had: (route,
    lattice) or None. ``world(size, lane)`` builds (space, graph) round the lane only, so the
    branch may shift within that margin and no further; ``branches`` holds every laid line
    but this one; ``tie_tag`` is the line the tie lies on, pardoned at the tie."""
    from typehaus.cli.route_support import _nearest
    from typehaus.routing.fitting_room import fitting_terms
    from typehaus.routing.gravity import minimum_slope
    from typehaus.routing.gravity_band import band_obstacles, member_constraints, terminal_pardons
    from typehaus.routing.gravity_search import GravityProblem, GravityRefusal, sloped_route
    from typehaus.routing.trades import pipe as pipe_trade

    built = world(size, [(p[0], p[1], root_z) for p in points])
    if built is None:
        return None
    space, graph = built
    start = _nearest(graph, (points[0][0], points[0][1], root_z))
    end = _nearest(graph, (points[-1][0], points[-1][1], root_z))
    if start is None or end is None or start == end:
        return None
    radius = pipe_trade.radius_m(size)
    space.banded = list(space.banded) + branches.prisms(space.radius_m, space.clearance_m)
    pardons = terminal_pardons(space, graph, {end: arrival, start: ceiling}, start,
                               frozenset({target}))
    if tie_tag is not None:
        pardons[end] = pardons.get(end, frozenset()) | {f"{tie_tag}-PROPOSED"}
    nipple, heel = fitting_terms(space.cost, "drain", size, None, radius)
    problem = GravityProblem(ceiling_m=ceiling, grade_in_per_ft=minimum_slope(size),
                             diameter_m=2.0 * radius, required_m={end: arrival},
                             nipple_m=nipple, heel_m=heel, max_labels=max_labels)
    found = sloped_route(graph, space, start, {end}, problem,
                         constraints=member_constraints(model, graph, (arrival, ceiling)),
                         refusal=GravityRefusal(),
                         obstacles=band_obstacles(space, graph, pardons, start), heels={})
    return None if found is None else (found, graph)
