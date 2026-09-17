"""More than one answer, each priced at what it really costs.

**Penalty re-search, not Yen's**, and the reason is the lattice. Yen's k-shortest paths
deviates from the incumbent one edge at a time, so on an escape graph its next answers are
the same route shifted onto the neighbouring candidate line — twins, not alternatives. What
a person comparing routes wants is a different *lane*: down the other wall, round the far
side of the stair, through the soffit instead of the bay. Multiplying the price of the lanes
already taken and searching again is what produces those.

**Route A is the unpenalised answer and is byte-identical to a plain search.** The oracle
note's §4 is untouched by this module existing: with ``k = 1`` nothing here runs, and with
``k > 1`` the first result is the same search. That is deliberate — a feature that quietly
changed the default answer would invalidate every pinned number in the note.

**Every route is re-priced on the ORIGINAL graph.** A route found at a tripled weight and
quoted at that weight is not comparable to the one it is offered against; the search runs on
the penalised copy and ``search.price_route`` prices the winner on the real one, so what a
reader compares is two true costs.

**Nodes are never removed, only made dear.** A forced tie-in — the one node a branch must
reach — stays reachable at any penalty, so an alternative is always a real route and never
"no route found" manufactured by this module's own pruning.

``houses/catlin/notes/mep_drain_routing_basis.md`` §7 is the hand-worked oracle: on §4's
lattice there are exactly two simple paths, they are edge-disjoint, they cost the same, and
``k = 3`` therefore yields exactly two.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING

from typehaus.routing.graph import Graph
from typehaus.routing.space import RoutingSpace

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.routing.search import Route

#: What a taken lane's edges are multiplied by each round. Three is enough to push the
#: search off a lane it has already been given and small enough that a genuinely forced
#: corridor — a chase with one way through — is still taken rather than replaced by a
#: detour twice as long. **It must be >= 1**: a factor below one would make an accepted
#: lane cheaper and the "alternative" would be the same route again.
DEFAULT_FACTOR = 3.0

#: How much of a candidate may lie on lanes already accepted before it stops being an
#: alternative and becomes the same route with a jog in it. Half, measured by length.
DEFAULT_MAX_SHARED = 0.5

#: The band round an accepted leg whose parallel edges are penalised. Two envelope widths,
#: or a foot, whichever is larger — the second term is what stops a hair-thin raceway from
#: penalising only literally-collinear edges and finding its own line one lattice step over.
def corridor_tolerance_m(space: RoutingSpace) -> float:
    return max(2.0 * (space.radius_m + space.clearance_m), 0.3048)


Search = Callable[[Graph, RoutingSpace, int, set[int]], "Route | None"]


def alternative_routes(search: Search, graph: Graph, space: RoutingSpace, start: int,
                       goals: set[int], k: int, *, factor: float = DEFAULT_FACTOR,
                       max_shared: float = DEFAULT_MAX_SHARED) -> list[Route]:
    """Up to ``k`` distinct routes, cheapest first, each priced on the original graph.

    ``search`` is a parameter rather than an import so a gravity-aware search slots in
    without this module learning what a drain is — see ``routing/gravity_search.py``.

    Returns fewer than ``k`` rather than padding: a lane that is the only lane is a fact
    about the building, and a second "alternative" that is 96% the first route is a worse
    answer than saying there is only one.
    """
    from typehaus.routing.search import price_route

    if factor < 1.0:
        raise ValueError("an alternatives factor below 1 makes a taken lane CHEAPER, so "
                         "the next search returns the same route at a discount")
    first = search(graph, space, start, goals)
    if first is None or k <= 1:
        return [] if first is None else [first]

    accepted = [first]
    penalties: dict[tuple[int, int], float] = {}
    tolerance = corridor_tolerance_m(space)
    rounds = 0
    while len(accepted) < k and rounds < 3 * k:
        rounds += 1
        _penalise(graph, penalties, accepted[-1], tolerance, factor)
        weighted = replace(graph, weights={**graph.weights, **penalties})
        found = search(weighted, space, start, goals)
        if found is None:
            break
        priced = price_route(graph, space, found.nodes)
        if any(_shared_fraction(graph, priced, other) >= max_shared
               for other in accepted):
            continue
        accepted.append(priced)
    return accepted


def _penalise(graph: Graph, penalties: dict[tuple[int, int], float], route: Route,
              tolerance: float, factor: float) -> None:
    """Multiply every edge parallel to and beside one of this route's legs.

    A *leg*, not an edge: the point is to price the whole lane the route rode, including
    the parallel candidate lines a hair away from it that carry a run the trade would call
    the same lane. The band is a plan-and-elevation one — an edge directly under the
    accepted route on another storey is not the same lane and is not penalised.
    """
    points = [(graph.nodes[i].x, graph.nodes[i].y, graph.nodes[i].z) for i in route.nodes]
    legs = [(a, b) for a, b in zip(points, points[1:], strict=False)]
    for (a, b) in graph.weights:
        if a > b:
            continue  # each undirected edge once; both directions are written below
        na, nb = graph.nodes[a], graph.nodes[b]
        mid = ((na.x + nb.x) / 2.0, (na.y + nb.y) / 2.0, (na.z + nb.z) / 2.0)
        axis = _axis((na.x, na.y, na.z), (nb.x, nb.y, nb.z))
        if not any(_beside(mid, axis, leg, tolerance) for leg in legs):
            continue
        base = penalties.get((a, b), graph.weights[(a, b)])
        penalties[(a, b)] = base * factor
        penalties[(b, a)] = base * factor


def _beside(mid: tuple[float, float, float], axis: str,
            leg: tuple[tuple[float, float, float], tuple[float, float, float]],
            tolerance: float) -> bool:
    """Is this edge's midpoint inside the band round a leg running the same way?"""
    a, b = leg
    if _axis(a, b) != axis:
        return False
    index = {"x": 0, "y": 1, "z": 2}[axis]
    if not (min(a[index], b[index]) - tolerance <= mid[index]
            <= max(a[index], b[index]) + tolerance):
        return False
    return all(abs(mid[other] - a[other]) <= tolerance
               for other in range(3) if other != index)


def _shared_fraction(graph: Graph, candidate: Route, other: Route) -> float:
    """How much of ``candidate``, by length, lies on ``other``'s own edges.

    By length rather than by edge count, because a lattice is denser where the geometry is
    busy: counting edges would call two routes "half shared" for agreeing about six inches
    in a congested corner and disagreeing about forty feet everywhere else.
    """
    taken = {frozenset(pair) for pair in zip(other.nodes, other.nodes[1:], strict=False)}
    total = shared = 0.0
    for a, b in zip(candidate.nodes, candidate.nodes[1:], strict=False):
        na, nb = graph.nodes[a], graph.nodes[b]
        length = abs(nb.x - na.x) + abs(nb.y - na.y) + abs(nb.z - na.z)
        total += length
        if frozenset((a, b)) in taken:
            shared += length
    return shared / total if total > 0 else 1.0


def _axis(a: tuple[float, float, float], b: tuple[float, float, float]) -> str:
    if abs(b[0] - a[0]) > 1e-9:
        return "x"
    if abs(b[1] - a[1]) > 1e-9:
        return "y"
    return "z"
