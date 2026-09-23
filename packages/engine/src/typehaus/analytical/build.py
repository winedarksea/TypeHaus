"""``build_analytical_model(ctx)`` — the one way an :class:`AnalyticalModel` is made.

Five stages, in this order and each a module of its own: what is in scope
(:mod:`~typehaus.analytical.scope`), where its centrelines are
(:mod:`~typehaus.analytical.members`), what holds it up
(:mod:`~typehaus.analytical.supports`), what pushes on it
(:mod:`~typehaus.analytical.loads`) and which of the walls are surfaces rather than curves
(:mod:`~typehaus.analytical.shells`). The gap register is assembled last, because "nothing
in this graph carries this item's demand" is a fact about the finished graph and not about
any one stage.

Deterministic by construction: every iteration is over a sorted sequence, and a node is
named for what meets there rather than for the order it was reached in. Two builds of one
house are byte-identical, which is what lets ``haus handoff``'s manifest mean anything.
"""

from __future__ import annotations

from typing import Any

from typehaus.analytical import loads as _loads
from typehaus.analytical import members as _members
from typehaus.analytical import scope as _scope
from typehaus.analytical import shells as _shells
from typehaus.analytical import supports as _supports
from typehaus.analytical import ties as _ties
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
    shell_set = _shells.derive_shells(ctx, scope)

    assumptions = list(graph.assumptions)
    for line in (*load_set.assumptions, *shell_set.assumptions):
        if line not in assumptions:
            assumptions.append(line)
    return AnalyticalModel(
        nodes=graph.nodes + tuple(shell_set.nodes),
        members=graph.members,
        supports=supports,
        cases=tuple(load_set.cases),
        member_loads=tuple(load_set.member_loads),
        node_loads=tuple(load_set.node_loads),
        combinations=tuple(load_set.combinations),
        plates=tuple(shell_set.plates),
        support_springs=tuple(shell_set.springs) + _ties.springs(ctx, scope, graph.tie_node),
        plate_pressures=tuple(shell_set.pressures),
        scope=scope.item_ids,
        assumptions=tuple(assumptions),
        gaps=(_gaps(ctx, scope, graph, shell_set) + tuple(load_set.gaps)
              + tuple(shell_set.gaps) + _ties.unplaced(ctx, scope, graph.tie_node)),
    )


def _gaps(ctx: Any, scope: Any, graph: Any, shell_set: Any = None) -> tuple[str, ...]:
    """Every item whose demand no member in this graph carries, in words.

    Earned the same way ``Result.NOT_APPLICABLE`` is: from the finished model, by asking
    whether any member names the item — not from a list of kinds somebody remembered to
    keep up to date.
    """
    graded = {item for member in graph.members for item in member.item_ids}
    graded |= set(getattr(shell_set, "spoken_for", set()))
    ledgers = tuple(
        f"{tag}: a ledger on {beam.ledger_on}, continuously supported, so it is not a "
        f"member here; its deck's load goes to the wall through the anchors"
        for tag in scope.terminals
        if (beam := ctx.plan.by_tag(tag)) is not None and getattr(beam, "ledger_on", None))
    return tuple(sorted(_scope.gap_line(item, ctx.engineering[item].kind)
                        for item in scope.item_ids if item not in graded)) + ledgers
