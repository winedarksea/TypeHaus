"""What would have to change — one movable blocker at a time, and what it would buy.

:mod:`typehaus.routing.diagnostics` says a route failed and names what is standing in the
way. The next question is the useful one and it is not answerable by looking: **would moving
any ONE of those things open a lane, and at what price?** A caller staring at "PR-M-WC-VENT
is in the way" cannot tell whether that vent is the whole problem or the first of six.

So this re-searches with one movable blocker lifted out of the world, bounded and one at a
time, and reports the difference. Two rules make the answer honest:

* **Only ``Mobility.MOVABLE`` blockers are relaxed.** A rough opening and a slab do not move
  because a router would prefer them not to be there. Lifting a fixed prism would produce a
  route through a wall and call it a finding.
* **A counterfactual is never a proposal.** Its geometry is not printed as dialect source
  and it is labelled at every exit. "A route exists if PR-M-WC-VENT were re-routed" is a
  statement about this model with one element deleted, and deleting an element is not a
  design move — the vent still has to go somewhere, and *where* is a search nobody has run.
  It is also not a claim that the element may legally or practically move; that is a
  judgement with a person on the end of it, which is the same line ``Mobility`` draws.

**Bounded on purpose.** One relaxation deep, at most :data:`MAX_RELAXATIONS` of them, each a
full space rebuild and search. Two-at-a-time is a combinatorial search over the house's own
design and would take longer than asking somebody.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.diagnostics import Blocker

#: How many single-blocker relaxations one refusal is worth. Each is a space build and an
#: A* over it; four is a second or two and covers the congestion that actually produces a
#: sealed terminal, where two or three runs share one chase.
MAX_RELAXATIONS = 4


@dataclass(frozen=True)
class Counterfactual:
    """One relaxation and what it bought. ``cost_in`` is None when it bought nothing."""

    blocker: str
    mobility: str
    #: Equivalent inches of the route that becomes possible, or None if still no route.
    cost_in: float | None
    #: Against the unblocked baseline where one exists — the extra price of this detour.
    delta_in: float | None = None
    note: str = ""

    def render(self) -> str:
        if self.cost_in is None:
            return (f"counterfactual: re-routing {self.blocker} alone does NOT open a lane"
                    + (f" — {self.note}" if self.note else ""))
        extra = ("" if self.delta_in is None
                 else f", {self.delta_in:+.0f}\" against the direct line")
        return (f"counterfactual: a route exists if {self.blocker} were re-routed — "
                f"{self.cost_in:.0f}\" equivalent{extra}. This is a diagnosis, not a "
                "proposal: it does not say where that run would go instead, nor that it "
                "may move")

    def payload(self) -> dict:
        return {"blocker": self.blocker, "mobility": self.mobility,
                "cost_in": self.cost_in, "delta_in": self.delta_in, "note": self.note}


def counterfactuals(model: ResolvedModel, blockers: list[Blocker], *,
                    build: Callable[[frozenset[str]], Any],
                    search: Callable[[Any], float | None],
                    baseline_in: float | None = None,
                    limit: int = MAX_RELAXATIONS) -> list[Counterfactual]:
    """Relax each movable blocker in turn and report what a route would then cost.

    ``build(extra_touch)`` rebuilds the space with those tags allowed to be occupied — the
    same ``touch`` channel a re-route already uses for the run it replaces, so a relaxation
    costs no new concept. ``search(space)`` returns the route's equivalent inches or None.

    Both are passed in rather than imported: this module must not decide which search a
    trade uses (a drain's is the gravity one), and taking them as parameters is the same
    shape :func:`~typehaus.routing.alternatives.alternatives` already uses.
    """
    from typehaus.routing.diagnostics import Mobility

    out: list[Counterfactual] = []
    seen: set[str] = set()
    for blocker in blockers:
        if len(out) >= limit:
            break
        if blocker.mobility is not Mobility.MOVABLE or blocker.tag in seen:
            continue
        seen.add(blocker.tag)
        try:
            cost = search(build(frozenset({blocker.tag})))
        except Exception as exc:  # noqa: BLE001 - a relaxation must never fail the refusal
            # A counterfactual is a courtesy on top of a refusal that already stands. A
            # space that cannot be built with one prism lifted is worth saying so about,
            # and is not worth losing the diagnosis it was decorating.
            out.append(Counterfactual(blocker.tag, blocker.mobility.value, None,
                                      note=f"the relaxed search did not complete: {exc}"))
            continue
        delta = (None if cost is None or baseline_in is None else cost - baseline_in)
        out.append(Counterfactual(blocker.tag, blocker.mobility.value, cost, delta))
    return out


def render(items: list[Counterfactual]) -> list[str]:
    """Console lines, with the one sentence that has to accompany all of them."""
    if not items:
        return []
    lines = [item.render() for item in items]
    if any(item.cost_in is not None for item in items):
        lines.append("A counterfactual moves nothing and proposes nothing. The element it "
                     "lifts still has to go somewhere, and that is a search nobody has run.")
    return lines
