"""How each scorecard target mode is proposed (``cli/route_scorecard.py``; docs/routing.md).

One function per mode family, each returning a :class:`Found`. An entry point that is not
built yet (``route_options.not_built`` exits 2) records as a refusal row, so the card still
completes and the row starts measuring the day the stub is filled."""

from __future__ import annotations

import contextlib
import signal
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer

from typehaus.cli.route_options import RouteOptions

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.cli.route_scorecard_targets import ScoreTarget
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.cost import RouteCost
    from typehaus.routing.proposal import RouteProposal

_SLOPE_UNSET = None
_MARGIN_FT = 8.0
#: Wall-clock bound on one row's search. A search that runs past it is a refusal row, so no
#: target can hang the card (a duct search once ran 16 CPU minutes).
ROW_BUDGET_S = 300


class RowTimeout(Exception):
    """A row's search ran past ``ROW_BUDGET_S``."""


@contextlib.contextmanager
def _row_budget(seconds: int):
    """SIGALRM bound (main thread, POSIX); a no-op elsewhere."""
    def fire(_sig, _frame):
        raise RowTimeout

    try:
        previous = signal.signal(signal.SIGALRM, fire)
    except (ValueError, AttributeError):  # not the main thread / no SIGALRM
        yield
        return
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


@dataclass
class Found:
    proposals: list[RouteProposal]
    #: Terminals no proposal covers, counted from what each entry point returned (a drain
    #: proposal's ``serves``), never as terminals minus proposals: a group or lifted tree
    #: returns more proposals than terminals (vent, arm, re-laid supply runs).
    refused: int
    #: Lifts: a campaign row's own rip-up lifts as the campaign reports them; a ``lift`` row's
    #: are the runs the entry point lifted (its ``outcome``).
    lifts: int = 0
    notes: list[str] = field(default_factory=list)  #: why a row came back empty
    relaid: int = 0  #: ``lift`` rows: lifted authored runs re-laid as proposals
    relay_refused: int = 0  #: ``lift`` rows: lifted runs the entry point could not re-lay
    #: When set, ``developed_ft`` counts only the proposal with this tag (``trunk:CW``
    #: compares the trunk alone with its authored length, not trunk plus branches).
    ft_tag: str | None = None


def propose_target(directory: Path, model: ResolvedModel, target: ScoreTarget,
                   cost: RouteCost) -> Found:
    """Search ``target`` the way ``haus route`` would; a stub's exit 2 is a refusal row."""
    try:
        with _row_budget(ROW_BUDGET_S):
            return _MODES[target.mode](directory, model, target, cost)
    except typer.Exit as stop:
        return Found([], len(_terminals(model, target)), notes=[f"exit {stop.exit_code}"])
    except RowTimeout:
        return Found([], len(_terminals(model, target)),
                     notes=[f"timed out after {ROW_BUDGET_S} s"])


def _opts(directory: Path, model: ResolvedModel, target: ScoreTarget, cost: RouteCost
          ) -> RouteOptions:
    from typehaus.cli.route_support import storey_band

    band = storey_band(model, target.level) if target.level else None
    return RouteOptions(
        directory=directory, cost=cost, out_dir=None, as_json=False, summary=False,
        explain=False, details=False, evaluate=False, margin_ft=_MARGIN_FT,
        level=target.level, band=band, avoid=frozenset(), via=(), slope=_SLOPE_UNSET,
        alternatives=1, timing=None)


def _terminals(model: ResolvedModel, target: ScoreTarget) -> set[str]:
    """Tags a target must serve: a drain tree's or group's drained fixtures, a supply tree's
    ends (E4's network, trunk included), otherwise the target itself."""
    if target.mode == "group":
        return _group_terminals(model, target.tag)
    if target.mode in ("tree", "lift", "trunk"):
        return _tree_terminals(model, target)
    return {target.tag}


def _tree_terminals(model: ResolvedModel, target: ScoreTarget) -> set[str]:
    from typehaus.cli.cmd_route_supply_tree import _network, is_supply_main

    if is_supply_main(model, target.tag):
        net = _network(model, target.tag, [])
        return set(net.ends) if net is not None and net.ends else {target.tag}
    from typehaus.cli.route_support import _storey_of
    from typehaus.model.spatial import Fixture

    main = next((r for r in model.pipe_runs if r.tag == target.tag), None)
    if main is None:
        return {target.tag}
    fixtures = {t for t in main.serves if isinstance(model.plan.by_tag(t), Fixture)}
    if target.level is not None:
        fixtures = {t for t in fixtures if _storey_of(model, t) == target.level}
    return fixtures or {target.tag}


def _base(tag: str) -> str:
    return tag.removesuffix("-PROPOSED")


def _covered(model: ResolvedModel, target: ScoreTarget, proposals: list[Any]) -> int:
    """Terminals of ``target`` that no proposal reaches: a drain proposal serving the
    fixture, or (supply trees) a proposal for the end's own run or one that ``replaces`` it
    (a trunk takes over its farthest end and any end that stands on another new run)."""
    terminals = _terminals(model, target)
    if target.mode in ("fixture", "run"):
        return 0 if proposals else 1
    laid: set[str] = set()
    for proposal in proposals:
        if target.mode == "trunk" or _is_supply(model, target):
            laid.add(_base(proposal.tag))
            laid.update(getattr(proposal, "replaces", ()))
        elif proposal.system == "drain" and _base(proposal.tag) not in target.lift:
            laid.update(proposal.serves)
    return len(terminals - laid)


def _is_supply(model: ResolvedModel, target: ScoreTarget) -> bool:
    from typehaus.cli.cmd_route_supply_tree import is_supply_main

    return target.mode in ("tree", "trunk") and is_supply_main(model, target.tag)


def _pairs(model: ResolvedModel, target: ScoreTarget, made: list[tuple[Any, str]],
           notes: list[str], lifts: int = 0) -> Found:
    proposals = [p for p, _s in made]
    return Found(proposals, _covered(model, target, proposals), lifts, notes)


def _tree(directory, model, target, cost) -> Found:
    from typehaus.cli.cmd_route_supply_tree import is_supply_main, propose_supply_tree
    from typehaus.cli.cmd_route_tree import _propose_tree

    if is_supply_main(model, target.tag):
        made, problems, _n, _r = propose_supply_tree(
            model, target.tag, None, _opts(directory, model, target, cost))
    else:
        made, problems, _n, _r = _propose_tree(
            model, target.tag, slope=None, margin_ft=_MARGIN_FT, level=target.level,
            avoid=frozenset(), via=[], explain=False, cost=cost)
    return _pairs(model, target, made, problems)


def _lift(directory, model, target, cost) -> Found:
    from typehaus.cli.route_tree_lift import propose_tree_lifted

    outcome: dict[str, Any] = {}
    made, problems, _n, _r = propose_tree_lifted(
        model, target.tag, target.lift, _opts(directory, model, target, cost), outcome)
    found = _pairs(model, target, made, problems, lifts=len(outcome.get("lifted", ())))
    found.relaid = len(outcome.get("relaid", ()))
    found.relay_refused = len(outcome.get("refused", ())) + (
        len(target.lift) - len(outcome.get("lifted", ())))
    return found


def _trunk(directory, model, target, cost) -> Found:
    from typehaus.cli.cmd_route_supply_tree import propose_supply_tree

    made, problems, _n, _r = propose_supply_tree(
        model, target.tag, "trunk", _opts(directory, model, target, cost))
    found = _pairs(model, target, made, problems)
    found.ft_tag = f"{target.tag}-PROPOSED"
    return found


def _single(directory, model, target, cost) -> Found:
    """``--run`` / ``--fixture``: one target, one proposal expected."""
    from typehaus.cli.cmd_route import _propose

    made, problems, _n, _r = _propose(
        model, [target.tag], mode=target.mode, slope=None, margin_ft=_MARGIN_FT, band=None,
        avoid=frozenset(), via=[], explain=False, cost=cost)
    return _pairs(model, target, made, problems)


def _group(directory, model, target, cost) -> Found:
    from typehaus.cli.cmd_route_group import group_proposals

    made, problems, _n, _r = group_proposals(model, target.tag,
                                             _opts(directory, model, target, cost))
    return _pairs(model, target, made, problems)


def _group_terminals(model: ResolvedModel, room: str) -> set[str]:
    """Drained fixtures filed in ``room`` (a filler has no drain point)."""
    from typehaus.model.spatial import Fixture
    from typehaus.resolve.mep import _expected_drain_point  # type: ignore[attr-defined]

    return {e.tag for e in model.plan.all_elements()
            if isinstance(e, Fixture) and e.room == room
            and _expected_drain_point(model, e.tag) is not None} or {room}


def _campaign(directory, model, target, cost) -> Found:
    from typehaus.cli.cmd_route_house import campaign_result, manifold_branches

    only = None
    if target.mode == "manifold":
        only = manifold_branches(model, target.tag)
        if not only:
            return Found([], 1, notes=[f"{target.tag}: no supply run starts on an outlet"])
    run = campaign_result(
        model, trades=["supply"] if only is not None else list(target.trades) or None,
        storey=target.storey, locked=frozenset(), margin_ft=_MARGIN_FT, band=None,
        avoid=frozenset(), cost=cost, slope=None, alternatives=1, rip_up_budget=4,
        only=only)
    notes = [f"{tag}: {reason}" for tag, reason in run.result.refused]
    return Found(list(run.result.accepted), len(run.result.refused),
                 len(run.result.lifts), notes)


_MODES = {
    "tree": _tree, "lift": _lift, "trunk": _trunk, "fixture": _single, "run": _single,
    "group": _group, "manifold": _campaign, "house": _campaign,
}
