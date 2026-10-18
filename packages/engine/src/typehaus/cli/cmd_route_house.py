"""Bind the campaign policy to trade searches and print/save review reports.

Campaign occupancy and rip-up live in routing.campaign. Evaluation grades the complete
accepted network. See docs/routing.md for reports and acceptance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()


def run_house_campaign(model: Any, *, directory: Path, trades: list[str] | None,
                       storey: str | None, locked: frozenset[str], margin_ft: float,
                       band: tuple[float, float] | None, avoid: frozenset[str],
                       cost: Any, slope: float | None, alternatives: int,
                       rip_up_budget: int, out_dir: Path | None,
                       as_json: bool, explain: bool, evaluate: bool = False,
                       orders: int = 1, summary: bool = False) -> int:
    """Lay every target in scope. Returns the process exit code.

    Exit 1 when anything was refused — a campaign that could not serve a terminal is a
    result somebody has to look at, and an exit code is how a script finds out.
    """
    from typehaus.cli.cmd_route import _propose
    from typehaus.cli.route_eval import _storey_for, as_dict, evaluate_network, render_reports
    from typehaus.cli.route_report import emit_report, proposal_rows
    from typehaus.routing.campaign import (
        ORDER_STRATEGIES,
        Outcome,
        order_targets,
        rank,
        reorder,
        run_campaign,
    )
    from typehaus.routing.obstacles import CLEARANCE_M

    targets = order_targets(model, trades=trades, storey=storey, locked=locked)
    unassigned = [t.tag for t in targets if not t.trade]
    targets = [t for t in targets if t.trade]
    if not targets and not as_json:
        console.print("[yellow]no target in scope — check --storey and --trades[/yellow]")

    if not as_json and targets:
        console.print(f"[bold]{len(targets)} target(s)[/bold] in campaign order")

    diagnostics: dict[str, tuple[list[str], list[str], list]] = {}

    def propose(target: Any, occupancy: list) -> Outcome:
        proposals, problems, notices, refusals = _propose(
            model, [target.tag], mode="run", slope=slope, margin_ft=margin_ft, band=band,
            avoid=avoid, via=[], explain=explain or as_json or out_dir is not None,
            cost=cost, alternatives=alternatives,
            extra_prisms=occupancy)
        diagnostics[target.tag] = (problems, notices, refusals)
        if proposals:
            return Outcome(proposal=proposals[0][0])
        # The occupancy uses proposal tags; the rip-up ledger uses their authored targets.
        blockers = tuple(sorted({_target_of(b.tag) for r in refusals for b in r.blockers}))
        reason = (refusals[0].render() if refusals
                  else (problems[0] if problems else "no route, and no reason given"))
        return Outcome(reason=reason, blockers=blockers)

    strategies = [name for name, _why in ORDER_STRATEGIES][:max(1, orders)]
    results = []
    diagnostics_by_strategy = {}
    for name in strategies:
        diagnostics = {}
        results.append(run_campaign(reorder(targets, name), propose, inflate_m=CLEARANCE_M,
                                    rip_up_budget=rip_up_budget, strategy=name))
        diagnostics_by_strategy[name] = diagnostics
    ranked = rank(results)
    result = ranked[0]
    if len(ranked) > 1 and not as_json:
        console.print("[bold]orders tried, best first[/bold] — fewest refusals outranks "
                      "cheapest, always: those are not two points on one scale")
        for candidate in ranked:
            console.print(f"  {candidate.settings['order_strategy']:>14}: "
                          f"{len(candidate.accepted)} laid, {len(candidate.refused)} "
                          f"refused, {sum(p.cost for p in candidate.accepted):.0f}\" "
                          "equivalent")
    result.settings.update({
        "storey": storey, "trades": trades, "margin_ft": margin_ft,
        "locked": sorted(locked), "alternatives": alternatives,
    })
    if unassigned:
        result.skipped.extend(
            (tag, "no trade for this run's system — a campaign's order is its whole "
                  "content, so an unassigned run is named rather than placed in it")
            for tag in unassigned)

    evaluations = []
    if evaluate or as_json:
        evaluation = evaluate_network(directory, model, result.accepted)
        evaluations.append(evaluation)
        result.settings["evaluated"] = True
        if not as_json:
            for line in render_reports(evaluations):
                console.print(line)

    if not as_json:
        _print(result, explain=explain)
    if as_json or out_dir is not None:
        report = result.as_dict()
        report["house"] = str(directory)
        report["accepted"] = proposal_rows(
            model, [(proposal, _storey_for(model, proposal)) for proposal in result.accepted])
        report["evaluations"] = [as_dict(item) for item in evaluations]
        diagnostics = diagnostics_by_strategy[result.settings["order_strategy"]]
        report["problems"] = [line for problems, _, _ in diagnostics.values()
                              for line in problems]
        report["notices"] = [line for _, notices, _ in diagnostics.values()
                             for line in notices]
        report["refusals"] = [item.payload() for _, _, refusals in diagnostics.values()
                              for item in refusals]
        report["orders_tried"] = [
            {"strategy": item.settings["order_strategy"], "accepted": len(item.accepted),
             "refused": len(item.refused), "cost_in_equivalent": sum(p.cost for p in item.accepted)}
            for item in ranked]
        emit_report(report, as_json=as_json, summary=summary, out_dir=out_dir)
    return 1 if result.refused else 0


#: How a proposal's tag is built from its target's (→ ``cli/route_eval``, which splits it
#: the same way). ``-PROPOSED`` for a single answer, ``-PROPOSED-A`` and up for alternatives.
_PROPOSED = "-PROPOSED"


def _target_of(tag: str) -> str:
    """The run a blocker's tag is about, whether or not it is one of ours."""
    return tag.split(_PROPOSED)[0]


def _print(result: Any, *, explain: bool) -> None:
    from typehaus.routing.campaign import TRADE_ORDER

    if explain:
        console.print("[dim]order, and why each trade sits where it does:[/dim]")
        for index, (trade, why) in enumerate(TRADE_ORDER, start=1):
            console.print(f"[dim]  {index}. {trade}: {why}[/dim]")
    for proposal in result.accepted:
        console.print(f"[green]laid[/green] {proposal.tag}: "
                      f"{proposal.developed_ft():.2f} ft, {proposal.bends} bend(s)")
        for line in proposal.fitting_lines():
            console.print(f"  [yellow]{line}[/yellow]")
    for lifted, for_whom in result.lifts:
        console.print(f"[cyan]lifted[/cyan] {lifted} to make room for {for_whom}, and "
                      "re-queued it")
    for tag, reason in result.refused:
        console.print(f"[red]refused[/red] {tag}: {reason}")
    for tag, reason in result.skipped:
        console.print(f"[yellow]skipped[/yellow] {tag}: {reason}")
    console.print(f"[bold]{result.termination}[/bold]")
