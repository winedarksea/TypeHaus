"""Whole-house coordination: many targets, one occupancy, a stated order, bounded rip-up.

Phase 6 of the routing roadmap, and the reason every phase before it was built. One run at
a time is a question about a run; a house is a question about the *order* they are laid in
and about what each one leaves for the next. Two runs that each route perfectly against the
authored model can still be drawn through each other, because neither search ever saw the
other's answer.

**One occupancy ledger.** Every accepted proposal becomes hard prisms — its own envelope,
the same :func:`~typehaus.resolve.mep_envelopes.run_envelope` reading the checks and the
single-run router already share — and every later target searches against them. That is
what makes a campaign a coordination rather than a batch.

**The order is declared, not discovered** (:data:`TRADE_ORDER`), and it is an initial
heuristic that says so. Gravity drains first and deepest first, because a drain is the only
service with no freedom in z and the least of it goes first; then their vents, which must
reach the same stacks; then bulky rigid duct largest first, because a 10" trunk fits in
fewer places than a 4" branch; then supply and conduit, which bend, are small, and can be
threaded around what is already there. A different order is a different answer and the
result records which one it used.

**Rip-up is bounded and never silent.** When a target is refused by a blocker that is itself
a proposal this campaign accepted — never a locked run, never a fact about the building —
the most recently accepted such blocker is lifted, the refused target is re-searched, and
the lifted one is queued to route again at the end. The budget is a count, the result names
every lift, and a target that cannot be served after the budget is spent is REFUSED with its
reason rather than approximated.

**This module runs no search of its own.** ``propose`` is a parameter, exactly as it is in
:func:`~typehaus.routing.alternatives.alternatives`, for the same two reasons: the search a
campaign should run depends on the trade (a drain's is the gravity label search, a duct's is
the 3-D one), and ``routing`` is a leaf that may not reach for the CLI that binds them.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.obstacles import HardPrism
    from typehaus.routing.proposal import RouteProposal

#: The trades a campaign lays, in the order it lays them, with the reason each sits where it
#: does. The index is the primary sort key; each trade's own tie-break follows in
#: :func:`order_targets`.
TRADE_ORDER: tuple[tuple[str, str], ...] = (
    ("drain", "no freedom in z at all — an invert is a function of developed length, so a "
              "drain that is laid second is laid into whatever is left"),
    ("vent", "must reach the same stacks the drains just fixed, and is otherwise free"),
    ("duct", "bulky and rigid: a 10 inch trunk fits in fewer places than anything after it"),
    ("supply", "small and bendable, and its pressure loss is insensitive to a detour"),
    ("conduit", "smallest, bendable, and the one trade a person will happily re-pull"),
)

_TRADE_INDEX = {trade: index for index, (trade, _why) in enumerate(TRADE_ORDER)}

#: How many times a campaign may lift an accepted proposal to make room for a refused one.
#: A count rather than a time, so the same campaign takes the same decisions on any machine.
DEFAULT_RIP_UP_BUDGET = 4


@dataclass(frozen=True)
class CampaignTarget:
    """One run a campaign has to lay, and what decides when it is laid."""

    tag: str
    #: A key of :data:`TRADE_ORDER`.
    trade: str
    #: ``pipe`` | ``duct`` | ``conduit`` — which endpoint derivation and search applies.
    kind: str
    storey: str
    #: Nominal size in metres — the within-trade tie-break, biggest first for duct.
    size_m: float
    #: The run's deepest invert where it has one, for the drains' deepest-first order.
    depth_m: float | None = None
    #: True when the caller locked this run: it is an obstacle, never a target.
    locked: bool = False


@dataclass(frozen=True)
class Outcome:
    """What ``propose`` hands back: a route, or a refusal that names what refused it."""

    proposal: RouteProposal | None = None
    reason: str | None = None
    #: Tags in the way, from the search's own diagnostics. A campaign can only rip up what
    #: it is told about, so a refusal with no blockers is a refusal it cannot act on — which
    #: is the honest outcome when the obstruction is the building itself.
    blockers: tuple[str, ...] = ()


@dataclass
class CampaignResult:
    """Contracts 2 and 3 for a whole campaign: what was laid, what was not, and why."""

    order: list[str] = field(default_factory=list)
    accepted: list[RouteProposal] = field(default_factory=list)
    refused: list[tuple[str, str]] = field(default_factory=list)
    #: ``(lifted, for the sake of)`` — every rip-up, so the log is readable as a narrative.
    lifts: list[tuple[str, str]] = field(default_factory=list)
    #: Targets the caller named that this campaign never reached, and why.
    skipped: list[tuple[str, str]] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)
    termination: str = "complete"

    def as_dict(self, *, storey_datum_m: float = 0.0) -> dict:
        return {
            "order": list(self.order),
            "settings": dict(self.settings),
            "termination": self.termination,
            "accepted": [p.as_dict(storey_datum_m=storey_datum_m) for p in self.accepted],
            "refused": [{"tag": tag, "reason": reason} for tag, reason in self.refused],
            "lifts": [{"lifted": a, "for": b} for a, b in self.lifts],
            "skipped": [{"tag": tag, "reason": reason} for tag, reason in self.skipped],
        }


def order_targets(model: ResolvedModel, *, trades: Sequence[str] | None = None,
                  storey: str | None = None,
                  locked: frozenset[str] = frozenset()) -> list[CampaignTarget]:
    """Every run in scope, in the order :data:`TRADE_ORDER` states, ties broken per trade.

    A locked run is not a target: it is left exactly where it is and reaches the search as
    part of the authored model, which is what "locked" has to mean for the word to be worth
    anything.

    **Missing service assignments are reported, not inferred.** A run whose system this
    module has no trade for comes back as a target with ``trade=""`` so the caller can name
    it; guessing which trade an unrecognised system belongs to would put it somewhere in the
    order on no evidence at all, and the order is the whole content of a campaign.
    """
    from typehaus.resolve.mep_fittings import SERVICE_BY_SYSTEM

    wanted = None if trades is None else set(trades)
    out: list[CampaignTarget] = []

    for run in model.pipe_runs:
        service = SERVICE_BY_SYSTEM.get(run.system, "")
        trade = {"drain": "drain", "vent": "vent", "supply": "supply"}.get(service, "")
        depth = min(run.z_m) if run.z_m else None
        out.append(CampaignTarget(tag=run.tag, trade=trade, kind="pipe", storey=run.storey,
                                  size_m=run.diameter_m, depth_m=depth,
                                  locked=run.tag in locked))
    for duct in model.ducts:
        size = (duct.diameter_m if duct.diameter_m is not None
                else max(duct.width_m, duct.depth_m))
        out.append(CampaignTarget(tag=duct.tag, trade="duct", kind="duct",
                                  storey=duct.storey, size_m=size,
                                  locked=duct.tag in locked))
    for conduit in getattr(model, "conduits", ()):
        out.append(CampaignTarget(tag=conduit.tag, trade="conduit", kind="conduit",
                                  storey=conduit.storey,
                                  size_m=getattr(conduit, "diameter_m", 0.0) or 0.0,
                                  locked=conduit.tag in locked))

    scoped = [t for t in out
              if not t.locked
              and (storey is None or t.storey == storey)
              and (wanted is None or t.trade in wanted)]
    return sorted(scoped, key=_sort_key)


def _sort_key(target: CampaignTarget) -> tuple:
    """Primary by trade, then each trade's own reason, then the tag so it is total.

    A drain goes **deepest first** — least head slack, which is the same rule
    ``tree.order_terminals`` applies inside one tree and for the same reason: route length is
    not a proxy for slack. A duct goes **largest first**. Everything else goes by tag, which
    is not a claim that size does not matter to it but a refusal to invent a rule for it.
    """
    index = _TRADE_INDEX.get(target.trade, len(TRADE_ORDER))
    if target.trade == "drain":
        return (index, target.depth_m if target.depth_m is not None else 0.0, target.tag)
    if target.trade == "duct":
        return (index, -target.size_m, target.tag)
    return (index, target.tag)


def proposal_prisms(proposal: RouteProposal, *, inflate_m: float) -> list[HardPrism]:
    """An accepted proposal as hard prisms — one per segment, over its own z range.

    The same reading a run already in the model gets
    (:func:`~typehaus.resolve.mep_envelopes.run_envelope`), so a proposal blocks the next
    target by exactly the solid it will occupy once pasted. Deriving a second, looser shape
    here is how a campaign comes back internally consistent and externally wrong.
    """
    from typehaus.resolve.mep_envelopes import run_envelope
    from typehaus.routing.obstacles import HardPrism

    rectangular = proposal.width_m > 0.0 or proposal.depth_m > 0.0
    if rectangular:
        section = (proposal.width_m / 2.0, proposal.depth_m / 2.0, None)
    else:
        half = proposal.diameter_m / 2.0
        section = (half, half, None)
    envelope = run_envelope(proposal.kind, proposal.tag,
                            [(x, y) for x, y, _z in proposal.points],
                            [z for _x, _y, z in proposal.points],
                            section, inflate_m=inflate_m)
    return [HardPrism(tag=envelope.tag, kind="run", footprint=prism.footprint,
                      z0_m=prism.z0_m, z1_m=prism.z1_m)
            for prism in envelope.prisms]


#: The orderings a campaign may try, named. The first IS :data:`TRADE_ORDER`'s own — a
#: campaign asked for one alternative gets exactly what it gets today — and the rest vary
#: the **conflict order**, which is the axis the roadmap names and the only one that can be
#: varied without also varying what a route costs.
ORDER_STRATEGIES: tuple[tuple[str, str], ...] = (
    ("declared", "the trade order, each trade's own tie-break: drains deepest first, ducts "
                 "largest first"),
    ("biggest_first", "size descending ACROSS trades, trade order broken only to let a big "
                      "run claim its lane before a small one that could have gone round"),
    ("reversed_ties", "the trade order, but each trade's tie-break reversed — a shallow "
                      "drain and a small duct go first, which is the opposite bet and "
                      "sometimes the right one when the deep runs are the flexible ones"),
)


def reorder(targets: Sequence[CampaignTarget], strategy: str) -> list[CampaignTarget]:
    """The same targets under one of :data:`ORDER_STRATEGIES`.

    A different order is a different answer, and none of these is claimed to be better than
    another — which is why the caller runs them and *ranks the results* rather than this
    module picking one. The ranking is on the outcome (fewest refusals, then cost), because
    that is the only evidence there is.
    """
    if strategy == "declared":
        return sorted(targets, key=_sort_key)
    if strategy == "biggest_first":
        return sorted(targets, key=lambda t: (-t.size_m, _TRADE_INDEX.get(
            t.trade, len(TRADE_ORDER)), t.tag))
    if strategy == "reversed_ties":
        return sorted(targets, key=lambda t: (
            _TRADE_INDEX.get(t.trade, len(TRADE_ORDER)),
            -(t.depth_m if t.depth_m is not None else 0.0) if t.trade == "drain"
            else t.size_m if t.trade == "duct" else 0.0,
            t.tag))
    raise ValueError(f"unknown order strategy {strategy!r}; the strategies are "
                     f"{', '.join(name for name, _why in ORDER_STRATEGIES)}")


def rank(results: Sequence[CampaignResult]) -> list[CampaignResult]:
    """Complete-and-validated first, then by the cost of what was laid.

    **Fewest refusals outranks cheapest, always.** A campaign that serves every terminal at a
    higher price is not a worse answer than one that leaves two fixtures unconnected for
    less; those are not two points on one scale. Cost breaks the tie between two results that
    serve the same number, and the underlying quantities stay on each proposal so a reader
    can see what the ranking was made of.
    """
    return sorted(results, key=lambda r: (len(r.refused), len(r.skipped),
                                          sum(p.cost for p in r.accepted),
                                          r.settings.get("order_strategy", "")))


def run_campaign(targets: Sequence[CampaignTarget],
                 propose: Callable[[CampaignTarget, list], Outcome],
                 *, inflate_m: float,
                 rip_up_budget: int = DEFAULT_RIP_UP_BUDGET,
                 strategy: str = "declared") -> CampaignResult:
    """Lay every target in order against one growing occupancy, ripping up within budget.

    ``propose`` is handed the target and the prisms every accepted proposal so far
    contributes; what it does with them is the trade's business. It returns an
    :class:`Outcome`, and a refusal that names blockers is what a rip-up acts on.

    ``targets`` is laid in the order it arrives in; ``strategy`` is recorded in the settings
    so a ranked set of results says which ordering produced each. Use :func:`reorder` to
    build the sequence.
    """
    result = CampaignResult(order=[t.tag for t in targets], settings={
        "trade_order": [trade for trade, _why in TRADE_ORDER],
        "rip_up_budget": rip_up_budget,
        "inflate_m": inflate_m,
        "order_strategy": strategy,
    })
    accepted: dict[str, RouteProposal] = {}
    prisms: dict[str, list] = {}
    # Insertion order IS the rip-up order: the most recently laid blocker is the one whose
    # lane the refused target most likely wants, and lifting an early trunk to make room for
    # a late branch inverts the priority the order was chosen for.
    laid: list[str] = []
    queue = list(targets)
    requeued: set[str] = set()
    budget = rip_up_budget

    def occupancy() -> list:
        return [prism for tag in laid for prism in prisms[tag]]

    while queue:
        target = queue.pop(0)
        outcome = propose(target, occupancy())
        if outcome.proposal is not None:
            accepted[target.tag] = outcome.proposal
            prisms[target.tag] = proposal_prisms(outcome.proposal, inflate_m=inflate_m)
            laid.append(target.tag)
            continue

        liftable = [tag for tag in laid if tag in outcome.blockers]
        if not liftable or budget <= 0:
            # Either nothing in the way is this campaign's to move — the obstruction is the
            # building, which is a finding and not a scheduling problem — or the budget is
            # spent. Both are refusals with a reason, which is the deliverable.
            result.refused.append((target.tag, outcome.reason or "no route, no reason given"))
            continue

        lifted = liftable[-1]
        budget -= 1
        laid.remove(lifted)
        del prisms[lifted]
        accepted.pop(lifted)
        result.lifts.append((lifted, target.tag))
        # Retry the refused target now, against the world without the lifted run; the lifted
        # one goes to the back, because it has just been shown to be the one with slack.
        queue.insert(0, target)
        lifted_target = next((t for t in targets if t.tag == lifted), None)
        if lifted_target is not None and lifted not in requeued:
            requeued.add(lifted)
            queue.append(lifted_target)
        else:
            result.skipped.append((
                lifted, f"lifted for {target.tag} and not re-routed: it has already been "
                        "lifted once in this campaign, and lifting the same run twice is a "
                        "loop rather than a search"))

    result.accepted = [accepted[tag] for tag in laid]
    if result.refused:
        result.termination = (f"{len(accepted)} of {len(targets)} targets laid; "
                              f"{len(result.refused)} refused")
    elif budget < rip_up_budget:
        result.termination = (f"all {len(targets)} targets laid, after "
                              f"{rip_up_budget - budget} rip-up(s)")
    else:
        result.termination = f"all {len(targets)} targets laid with no rip-up"
    return result
