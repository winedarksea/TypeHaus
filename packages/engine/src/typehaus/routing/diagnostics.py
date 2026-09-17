"""Why a search found nothing — named, not merely reported.

"No route in plan; every lane is blocked" is true and useless. A caller iterating on a
proposal needs the tag of the thing in the way and where it stands, which is the difference
between "move something" and "give up". Nothing here searches or decides; it reads the space
the search was given and says what is in it, which is why it oracles nothing.

This is the seed of the roadmap's Phase 4 two-way street. It answers the two questions that
are cheap today: **what stands on the lanes out of this node**, and **how much of the world
could the search reach at all**.
"""

from __future__ import annotations

from typehaus.routing.graph import Graph
from typehaus.routing.space import RoutingSpace


def enclosure(space: RoutingSpace, graph: Graph, node: int,
              reach_m: float = 0.3048) -> list[str]:
    """Tags of the hard prisms standing on the lanes out of ``node``, nearest first.

    A lattice node with no edges is one whose neighbours were all dropped, and the reason
    each was dropped is a prism this can name — probed a foot out along both plan axes and
    both directions, which is a hand's width and covers the fitting-scale congestion that
    produces this case (an ERV manifold's ports sit four inches apart).
    """
    origin = graph.nodes[node]
    found: list[str] = []
    for dx, dy in ((reach_m, 0.0), (-reach_m, 0.0), (0.0, reach_m), (0.0, -reach_m)):
        for step in (0.25, 0.5, 1.0):
            tag = space.blocked((origin.x + dx * step, origin.y + dy * step), origin.z)
            if tag is not None and tag not in found:
                found.append(tag)
    return found


def reachable(graph: Graph, start: int) -> set[int]:
    """Every node the search could get to from ``start`` at any price.

    Reported as a count rather than a set by the caller: "three of thirty-three thousand
    nodes" says "walled in at the terminal", and "thirty thousand" says "the goal is the
    problem". Those are different defects and the same message was covering both.
    """
    seen = {start}
    stack = [start]
    while stack:
        for other, _axis in graph.neighbours(stack.pop()):
            if other not in seen:
                seen.add(other)
                stack.append(other)
    return seen


def refusal(space: RoutingSpace, graph: Graph, start: int, goals: set[int]) -> str:
    """One sentence saying which end the search died at, and what is standing there."""
    seen = reachable(graph, start)
    end, node = (("origin", start) if len(seen) < max(8, len(graph.nodes) // 100)
                 else ("root", min(goals)) if goals else ("origin", start))
    tags = enclosure(space, graph, node)
    where = f"{tags[0]}" if tags else "nothing this probe can name"
    return (f"no route: {len(seen):,} of {len(graph.nodes):,} lattice nodes are reachable "
            f"from the origin, and the lanes off the {end} are inside {where}"
            + (f" (also {', '.join(tags[1:])})" if len(tags) > 1 else "")
            + ". That is a statement about the model, not about the search")
