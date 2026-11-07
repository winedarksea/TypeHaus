"""How each scorecard target mode is proposed (``cli/route_scorecard.py``; docs/routing.md).

One function per mode family, each returning a :class:`Found`. An entry point that is not
built yet (``route_options.not_built`` exits 2) records as a refusal row, so the card still
completes and the row starts measuring the day the stub is filled."""

from __future__ import annotations

import contextlib
import io
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


@dataclass
class Found:
    proposals: list[RouteProposal]
    expected: int  #: terminals the target should have served
    lifts: int = 0  #: lifts a campaign/rip-up row reports
    notes: list[str] = field(default_factory=list)  #: why a row came back empty


def propose_target(directory: Path, model: ResolvedModel, target: ScoreTarget,
                   cost: RouteCost) -> Found:
    """Search ``target`` the way ``haus route`` would; a stub's exit 2 is a refusal row."""
    try:
        return _MODES[target.mode](directory, model, target, cost)
    except typer.Exit as stop:
        return Found([], max(1, _expected(model, target)), notes=[f"exit {stop.exit_code}"])


def _opts(directory: Path, model: ResolvedModel, target: ScoreTarget, cost: RouteCost
          ) -> RouteOptions:
    from typehaus.cli.route_support import storey_band

    band = storey_band(model, target.level) if target.level else None
    return RouteOptions(
        directory=directory, cost=cost, out_dir=None, as_json=False, summary=False,
        explain=False, details=False, evaluate=False, margin_ft=_MARGIN_FT,
        level=target.level, band=band, avoid=frozenset(), via=(), slope=_SLOPE_UNSET,
        alternatives=1, timing=None)


def _expected(model: ResolvedModel, target: ScoreTarget) -> int:
    """Terminals expected: a tree/group one per fixture served, a campaign one per target."""
    if target.mode in ("tree", "lift", "trunk"):
        return _tree_terminals(model, target)
    if target.mode == "group":
        return _group_terminals(model, target.tag)
    return 1


def _tree_terminals(model: ResolvedModel, target: ScoreTarget) -> int:
    from typehaus.cli.route_support import _storey_of
    from typehaus.model.spatial import Fixture

    main = next((r for r in model.pipe_runs if r.tag == target.tag), None)
    if main is None:
        return 1
    fixtures = [t for t in main.serves if isinstance(model.plan.by_tag(t), Fixture)]
    if target.level is not None:
        fixtures = [t for t in fixtures if _storey_of(model, t) == target.level]
    return max(1, len(fixtures))


def _pairs(made: list[tuple[Any, str]], expected: int, notes: list[str], lifts: int = 0
           ) -> Found:
    return Found([p for p, _s in made], expected, lifts, notes)


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
    return _pairs(made, _tree_terminals(model, target), problems)


def _lift(directory, model, target, cost) -> Found:
    from typehaus.cli.route_tree_lift import propose_tree_lifted

    made, problems, _n, _r = propose_tree_lifted(
        model, target.tag, target.lift, _opts(directory, model, target, cost))
    # The lifts asked for; E1's entry point reports no count of its own.
    return _pairs(made, _tree_terminals(model, target), problems, lifts=len(target.lift))


def _trunk(directory, model, target, cost) -> Found:
    from typehaus.cli.cmd_route_supply_tree import propose_supply_tree

    made, problems, _n, _r = propose_supply_tree(
        model, target.tag, "trunk", _opts(directory, model, target, cost))
    return _pairs(made, _tree_terminals(model, target), problems)


def _single(directory, model, target, cost) -> Found:
    """``--run`` / ``--fixture``: one target, one proposal expected."""
    from typehaus.cli.cmd_route import _propose

    made, problems, _n, _r = _propose(
        model, [target.tag], mode=target.mode, slope=None, margin_ft=_MARGIN_FT, band=None,
        avoid=frozenset(), via=[], explain=False, cost=cost)
    return _pairs(made, 1, problems)


def _group(directory, model, target, cost) -> Found:
    """``route_group`` owns its reporting and returns an exit code, so the proposals are
    taken off the ``report_proposals`` call it makes, with its console output discarded.
    Expected: one per fixture in the room."""
    import typehaus.cli.cmd_route_group as module
    import typehaus.cli.route_report as report

    opts = _opts(directory, model, target, cost)
    if hasattr(module, "group_proposals"):  # preferred seam: the 4-tuple, no capture
        made, problems, _n, _r = module.group_proposals(model, target.tag, opts)
        return _pairs(made, _group_terminals(model, target.tag), problems)
    caught: list[tuple[list, list[str]]] = []

    def capture(_model, _directory, proposals, *, problems, **_kw):
        caught.append((list(proposals), list(problems)))

    holders = [h for h in (module, report) if hasattr(h, "report_proposals")]
    saved = [h.report_proposals for h in holders]
    for holder in holders:
        holder.report_proposals = capture
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            module.route_group(model, target.tag, opts)
    finally:
        for holder, original in zip(holders, saved, strict=True):
            holder.report_proposals = original
    made, problems = (caught[-1] if caught else ([], []))
    return _pairs(made, _group_terminals(model, target.tag), problems)


def _group_terminals(model: ResolvedModel, room: str) -> int:
    """Drained fixtures filed in ``room`` (a filler has no drain point)."""
    from typehaus.model.spatial import Fixture
    from typehaus.resolve.mep import _expected_drain_point  # type: ignore[attr-defined]

    return max(1, sum(1 for e in model.plan.all_elements()
                      if isinstance(e, Fixture) and e.room == room
                      and _expected_drain_point(model, e.tag) is not None))


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
    return Found(list(run.result.accepted), len(run.targets), len(run.result.lifts), notes)


_MODES = {
    "tree": _tree, "lift": _lift, "trunk": _trunk, "fixture": _single, "run": _single,
    "group": _group, "manifold": _campaign, "house": _campaign,
}
