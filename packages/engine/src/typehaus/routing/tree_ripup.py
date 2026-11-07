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
* **P8** a tie refused only for SIZE may upsize the carrying branch one size on its own
  lane (its dependents re-laid), keep or roll back as P4. Tried before P1's lifts, within
  P5's two: it keeps the lay order and is what a plumber does (a tub and a shower on one
  2" branch), where P1 hands the lane to the later fixture.

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

    def capped(self, tag: str) -> bool:
        """``tag``'s refusal came from a probe stopped short of the full budget, so it is no
        answer: when no trial is kept the caller searches it again, in full."""

    def undersized(self, tag: str) -> list[str]:
        """Laid branches whose ties ``tag`` found too small for it, in the order to try."""

    def upsize(self, tag: str) -> tuple[Any, list[str]] | None:
        """P8: lift ``tag`` and its dependents and re-lay ``tag`` one size up on its own
        lane. (its new route, the dependents in lay order), or None when it cannot."""


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
    upsized: bool = False  #: P8: the candidate was re-laid one size up, not moved

    def sentence(self) -> str:
        others = ", ".join(t for t in self.lifted if t != self.candidate)
        cascade = ("" if not others else f" (re-laying {others} after it)" if self.upsized
                   else f" (and {others} tied onto it)")
        did = (f"upsized {self.candidate} one size{cascade} so {self.terminal} could tie "
               "onto it" if self.upsized else
               f"lifted {self.candidate}{cascade} to make room for {self.terminal}")
        return f"{did}: " + ("all laid, kept" if self.kept else f"{self.reason}, rolled back")


def candidates(blockers: list[str], lay_order: list[str], terminal: str,
               trials: list[Trial]) -> list[str]:
    """P2 and P6: the named laid branches, latest first, never one ``terminal`` once lifted."""
    rank = {tag: index for index, tag in enumerate(lay_order)}
    never = {(t.terminal, lifted) for t in trials if t.kept for lifted in t.lifted}
    named = {tag for tag in blockers if tag in rank and (tag, terminal) not in never}
    return sorted(named, key=lambda tag: -rank[tag])


def rip_up(tree: Tree, terminal: Terminal, by_tag: dict[str, Terminal], layer: Layer,
           search: Any, graph: Any, space: Any, roots: set[int]) -> bool:
    """Try to lay ``terminal`` by upsizing (P8) or lifting (P1) the siblings it ran into.

    True when a trial is kept. ``tree.routes`` then stays in lay order: the branches laid
    before, the re-laid ones, the terminal. Every trial is appended to ``tree.trials``."""
    upsizes = [t for t in layer.undersized(terminal.tag) if t in tree.routes]
    lifts = candidates(layer.blockers(terminal.tag), list(tree.routes), terminal.tag,
                       tree.trials)
    plan = [(t, True) for t in upsizes] + [(t, False) for t in lifts]
    for candidate, upsized in plan[:MAX_LIFTS]:
        state, routes = layer.snapshot(), dict(tree.routes)
        if upsized:
            got = layer.upsize(candidate)
            lifted, relay = [candidate], []
            if got is not None:
                route, relay = got
                for tag in relay:
                    tree.routes.pop(tag, None)
                tree.routes.pop(candidate, None)
                tree.routes[candidate] = route
                lifted += relay
        else:
            lifted = layer.lift(candidate)
            got, relay = True, lifted
            for tag in lifted:
                tree.routes.pop(tag, None)
        reason = (f"{candidate} does not clear its lane one size up" if got is None else
                  _lay(tree, terminal, relay, by_tag, search, graph, space, roots))
        kept = not reason
        tree.trials.append(Trial(terminal.tag, candidate, tuple(lifted), kept, reason,
                                 upsized))
        if not kept:
            layer.restore(state)  # P4: exact rollback
            tree.routes.clear()
            tree.routes.update(routes)
        layer.settle()
        if kept:
            return True
    return False


def _lay(tree: Tree, terminal: Terminal, relay: list[str], by_tag: dict[str, Terminal],
         search: Any, graph: Any, space: Any, roots: set[int]) -> str:
    """Search the terminal, then re-lay ``relay`` in order (P3; P5: never ripping up).
    The reason it failed, or "" when everything laid."""
    reach = set(roots).union(*(r.nodes for r in tree.routes.values()))
    route = search(graph, space, terminal.node, reach)
    if route is None:
        return f"{terminal.tag} still refused"
    tree.routes[terminal.tag] = route
    reach |= set(route.nodes)
    for tag in relay:
        again = search(graph, space, by_tag[tag].node, reach)
        if again is None:
            return f"{tag} would not re-lay"
        tree.routes[tag] = again
        reach |= set(again.nodes)
    return ""
