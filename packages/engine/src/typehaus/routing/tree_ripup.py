"""Rip-up inside one Steiner tree: lift the sibling branch a refused terminal ran into.

The policy is ``houses/catlin/notes/mep_tree_ripup_basis.md`` §1, worked by hand there on
two synthetic worlds (§2a, §2b):

* **P1** only a refusal that names laid branches of *this* tree triggers it; a refusal
  naming authored runs or hard geometry is final (that is ``--lift``'s job).
* **P2** candidates most recently laid first — RSPH laid them by ascending slack, so the
  latest has the most and is cheapest to re-lay.
* **P3** lifting a branch lifts every branch tied onto it, re-laid in original lay order.
* **P4** a trial is kept only if the terminal AND every lifted branch lay; otherwise the
  tree is restored exactly.
* **P5** at most :data:`MAX_LIFTS` trials per refused terminal; re-lays never rip up.
* **P6** a kept ``(terminal, lifted)`` pair is never reversed, so each kept trial adds one
  inversion of the deepest-first order and the loop terminates.

What the tree is built of — the branch ledger, how a refusal names its blockers — is the
caller's, behind :class:`Layer`. This module only sequences trials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.routing.tree import Terminal, Tree

#: Trials per refused terminal, rolled-back ones included (P5). A failing search can walk
#: the whole label budget, so this caps the costly part, not the loop (P6 bounds that).
MAX_LIFTS = 2


class Layer(Protocol):
    """The caller's tree state, as rip-up needs to see it."""

    def blockers(self, tag: str) -> list[str]:
        """Laid branch tags ``tag``'s last refusal names (any order; unknown tags ignored)."""

    def snapshot(self) -> Any:
        """Everything a trial may change, for an exact rollback."""

    def restore(self, state: Any) -> None: ...

    def lift(self, tag: str) -> list[str]:
        """Remove ``tag`` and every branch tied onto it; their tags in lay order."""

    def settle(self) -> None:
        """A trial is over, kept or rolled back. Between ``lift`` and this, every search is
        the trial's, and a layer may spend less on it than on a terminal's own search."""


@dataclass(frozen=True)
class Trial:
    """One rip-up attempt: for whom, which candidate, what it took with it, and how it went."""

    terminal: str
    candidate: str
    lifted: tuple[str, ...]
    kept: bool
    #: Why a rolled-back trial failed: the terminal, or the first lifted branch that would
    #: not re-lay. Empty when kept.
    reason: str = ""

    def sentence(self) -> str:
        cascade = (f" (and {', '.join(t for t in self.lifted if t != self.candidate)} tied "
                   "onto it)" if len(self.lifted) > 1 else "")
        if self.kept:
            return (f"lifted {self.candidate}{cascade} to make room for {self.terminal}: "
                    "both laid, kept")
        return (f"lifted {self.candidate}{cascade} to make room for {self.terminal}: "
                f"{self.reason}, rolled back")


def candidates(blockers: list[str], lay_order: list[str], terminal: str,
               trials: list[Trial]) -> list[str]:
    """P2 and P6: the named laid branches, latest first, never one ``terminal`` once lifted."""
    rank = {tag: index for index, tag in enumerate(lay_order)}
    never = {(t.terminal, lifted) for t in trials if t.kept for lifted in t.lifted}
    named = {tag for tag in blockers if tag in rank and (tag, terminal) not in never}
    return sorted(named, key=lambda tag: -rank[tag])


def rip_up(tree: Tree, terminal: Terminal, by_tag: dict[str, Terminal], layer: Layer,
           search: Any, graph: Any, space: Any, roots: set[int]) -> bool:
    """Try to lay ``terminal`` by lifting the siblings it ran into; True when kept.

    On success ``tree.routes`` holds the terminal and the re-laid branches after every
    branch laid before them, so its insertion order stays the lay order. Every trial,
    kept or not, is appended to ``tree.trials``.
    """
    order = list(tree.routes)
    for candidate in candidates(layer.blockers(terminal.tag), order, terminal.tag,
                                tree.trials)[:MAX_LIFTS]:
        state, routes = layer.snapshot(), dict(tree.routes)
        lifted = layer.lift(candidate)
        for tag in lifted:
            tree.routes.pop(tag, None)
        reach = set(roots).union(*(r.nodes for r in tree.routes.values()))
        reason = ""
        route = search(graph, space, terminal.node, reach)
        if route is None:
            reason = f"{terminal.tag} still refused"
        else:
            tree.routes[terminal.tag] = route
            reach |= set(route.nodes)
            for tag in lifted:  # P3: original order; P5: a re-lay never rips up
                again = search(graph, space, by_tag[tag].node, reach)
                if again is None:
                    reason = f"{tag} would not re-lay"
                    break
                tree.routes[tag] = again
                reach |= set(again.nodes)
        kept = not reason
        tree.trials.append(Trial(terminal.tag, candidate, tuple(lifted), kept, reason))
        if not kept:
            layer.restore(state)  # P4: exact rollback
            tree.routes.clear()
            tree.routes.update(routes)
        layer.settle()
        if kept:
            return True
    return False
