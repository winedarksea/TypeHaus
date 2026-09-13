"""``build_analytical_model(ctx)`` — the one way an :class:`AnalyticalModel` is made.

Four stages, in this order and each a module of its own: what is in scope
(:mod:`~typehaus.analytical.scope`), where its centrelines are
(:mod:`~typehaus.analytical.members`), what holds it up
(:mod:`~typehaus.analytical.supports`) and what pushes on it
(:mod:`~typehaus.analytical.loads`). The gap register is assembled last, because "no member
carries this item's demand" is a fact about the finished graph and not about any one stage.

Deterministic by construction: every iteration is over a sorted sequence, and a node is
named for what meets there rather than for the order it was reached in. Two builds of one
house are byte-identical, which is what lets ``haus handoff``'s manifest mean anything.
"""

from __future__ import annotations

from typing import Any

from typehaus.analytical import loads as _loads
from typehaus.analytical import members as _members
from typehaus.analytical import scope as _scope
from typehaus.analytical import supports as _supports
from typehaus.analytical.graph import AnalyticalModel


def build_analytical_model(ctx: Any) -> AnalyticalModel:
    """The engineered items and their load path, as nodes, members, supports and loads.

    ``ctx`` is the engineering context every calculation reads — ``plan``, ``model`` and
    the ``engineering`` result map (``cli/engineering_load.load_engineering`` builds one).
    """
    scope = _scope.build_scope(ctx)
    graph = _members.build_members(ctx, scope)
    supports = _supports.derive_supports(ctx, scope, graph)
    load_set = _loads.derive_loads(ctx, scope, graph)

    assumptions = list(graph.assumptions)
    for line in load_set.assumptions:
        if line not in assumptions:
            assumptions.append(line)
    return AnalyticalModel(
        nodes=graph.nodes,
        members=graph.members,
        supports=supports,
        cases=tuple(load_set.cases),
        member_loads=tuple(load_set.member_loads),
        node_loads=tuple(load_set.node_loads),
        combinations=tuple(load_set.combinations),
        scope=scope.item_ids,
        assumptions=tuple(assumptions),
        gaps=_gaps(ctx, scope, graph),
    )


def _gaps(ctx: Any, scope: Any, graph: Any) -> tuple[str, ...]:
    """Every item whose demand no member in this graph carries, in words.

    Earned the same way ``Result.NOT_APPLICABLE`` is: from the finished model, by asking
    whether any member names the item — not from a list of kinds somebody remembered to
    keep up to date.
    """
    graded = {item for member in graph.members for item in member.item_ids}
    return tuple(sorted(_scope.gap_line(item, ctx.engineering[item].kind)
                        for item in scope.item_ids if item not in graded))
