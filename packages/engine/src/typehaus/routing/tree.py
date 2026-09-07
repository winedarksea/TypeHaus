"""The branch→main topology: a directed Steiner tree by repeated shortest path.

RSPH is the standard heuristic — route one terminal to the root, then route each remaining
terminal to the **tree**, with nodes already on it costing zero — and it is the right one
here: wyes form where a plumber would put them, because a terminal joining an existing
branch is exactly what a wye is.

**One domain change, and it is the whole of this module's opinion: order terminals by
required invert, deepest first, not cheapest first.** Gravity makes the fixture with the
least head budget the one whose route is nearly unique; a lavatory's is nearly free. RSPH
gives the second terminal routed the direct lane and makes the third bend round it, so the
order decides which of them fits.

``houses/catlin/notes/mep_drain_routing_basis.md`` §5 works it on the suite bath's three
fixtures, and finds the honest version of the argument: length is **not** a proxy for slack
— the tub has the longest route and the second-tightest budget, the lavatory a shorter
route and four times the head.

A terminal with no feasible route lands in ``unserved`` **with its shortfall in inches**.
It is never dropped, and never silently rounded into feasibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from typehaus.routing.graph import Graph
from typehaus.routing.gravity import HeadBudget
from typehaus.routing.search import Route, shortest_route
from typehaus.routing.space import RoutingSpace


@dataclass(frozen=True)
class Terminal:
    """One thing that has to reach the root, and what its geometry allows.

    ``budget`` is None for a trade with no gravity predicate — supply pipe, duct, raceway —
    and those are ordered by route cost, which is what RSPH does everywhere else.
    """

    tag: str
    node: int
    budget: HeadBudget | None = None


@dataclass
class Tree:
    """What RSPH built: a route per served terminal, and the shortfall per unserved one."""

    root: int
    routes: dict[str, Route] = field(default_factory=dict)
    #: ``tag -> shortfall in inches``. A terminal here has a route in plan and not enough
    #: head to fall down it; the number is what a person needs to fix it.
    unserved: dict[str, float] = field(default_factory=dict)
    #: The order terminals were routed in, and why — printed by ``--explain``, because the
    #: order is the one thing about this algorithm somebody will want to argue with.
    order: list[tuple[str, float]] = field(default_factory=list)

    @property
    def nodes(self) -> set[int]:
        return {index for route in self.routes.values() for index in route.nodes}

    @property
    def cost(self) -> float:
        return sum(route.cost for route in self.routes.values())


def order_terminals(terminals: list[Terminal]) -> list[Terminal]:
    """Deepest first: least slack, then tag.

    A terminal with no budget sorts last and among themselves by tag, which is stable and
    is all "cheapest first" can honestly mean when nothing falls. The tag tie-break is not
    cosmetic — two runs of the same problem must return the same tree, or a proposal cannot
    be diffed against the one before it.
    """
    return sorted(
        terminals,
        key=lambda t: (t.budget is None,
                       t.budget.slack_in if t.budget is not None else 0.0,
                       t.tag))


def build_tree(graph: Graph, space: RoutingSpace, root: int,
               terminals: list[Terminal], *, root_nodes: set[int] | None = None) -> Tree:
    """Route every terminal to the root, deepest first, joining the tree as it grows.

    ``root_nodes`` is the set of arrivals the root accepts — for a stack, every node on its
    barrel rather than the head alone. Defaulting to ``{root}`` is the degenerate case and
    is what a supply trunk wants; a drain almost never does. See
    :func:`~typehaus.routing.search.shortest_route` on why goals are a set.
    """
    tree = Tree(root=root)
    reachable = set(root_nodes or {root})

    for terminal in order_terminals(terminals):
        slack = terminal.budget.slack_in if terminal.budget is not None else float("inf")
        tree.order.append((terminal.tag, slack))
        if terminal.budget is not None and not terminal.budget.feasible:
            tree.unserved[terminal.tag] = terminal.budget.shortfall_in()
            continue
        route = shortest_route(graph, space, terminal.node, reachable)
        if route is None:
            # No route in PLAN, which is a different failure from no head and is reported
            # as such: a shortfall of infinity is not a number, so it is stated as one.
            tree.unserved[terminal.tag] = float("inf")
            continue
        tree.routes[terminal.tag] = route
        reachable |= set(route.nodes)
    return tree


def explain(tree: Tree) -> list[str]:
    """The order, the cost and the failures, as lines — ``--explain``'s tree section.

    The ordering is printed with each terminal's slack beside it because that is the
    argument: a reader who disagrees with the tree should be able to see the number the
    order was made on without re-deriving it.
    """
    lines = [f"routed {len(tree.routes)} terminal(s), "
             f"{len(tree.unserved)} unserved, total {tree.cost:.0f}\" equivalent"]
    lines.append("  order (deepest first — least head slack routes first):")
    for tag, slack in tree.order:
        margin = "no gravity" if slack == float("inf") else f'{slack:+.3f}" slack'
        lines.append(f"    {tag:28s} {margin}")
    for tag, shortfall in sorted(tree.unserved.items()):
        if shortfall == float("inf"):
            lines.append(f"  UNSERVED {tag}: no route in plan — every lane to the tree is "
                         "blocked, not merely too shallow")
        else:
            lines.append(f'  UNSERVED {tag}: short {shortfall:.2f}" of head at the '
                         "minimum grade")
    return lines
