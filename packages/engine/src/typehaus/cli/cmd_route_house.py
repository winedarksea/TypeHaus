"""``haus route --house``: the whole-house campaign, driven and printed.

The CLI half of :mod:`typehaus.routing.campaign`. The leaf decides the ORDER and the rip-up
policy and runs no search; this binds a search to it — the same ``_propose`` that serves
``--run`` — and prints what came back.

**It still writes nothing.** A campaign is a hundred proposals instead of one and that makes
the rule more important rather than less: accepting a route is a judgement, and a hundred
judgements taken by a flag is not a hundred judgements taken. ``--out`` writes the JSON
report and the dialect source to a directory for a person to read and paste from; nothing
under ``plan/`` is touched.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()


def run_house_campaign(model: Any, *, directory: Path, trades: list[str] | None,
                       storey: str | None, locked: frozenset[str], margin_ft: float,
                       band: tuple[float, float] | None, avoid: frozenset[str],
                       cost: Any, slope: float | None, alternatives: int,
                       rip_up_budget: int, out_dir: Path | None,
                       as_json: bool, explain: bool) -> int:
    """Lay every target in scope. Returns the process exit code.

    Exit 1 when anything was refused — a campaign that could not serve a terminal is a
    result somebody has to look at, and an exit code is how a script finds out.
    """
    from typehaus.cli.cmd_route import _propose
    from typehaus.routing.campaign import (
        Outcome,
        order_targets,
        run_campaign,
    )
    from typehaus.routing.obstacles import CLEARANCE_M

    targets = order_targets(model, trades=trades, storey=storey, locked=locked)
    unassigned = [t.tag for t in targets if not t.trade]
    targets = [t for t in targets if t.trade]
    if not targets:
        console.print("[yellow]no target in scope — check --storey and --trades[/yellow]")
        return 0

    console.print(f"[bold]{len(targets)} target(s)[/bold] in campaign order")

    def propose(target: Any, occupancy: list) -> Outcome:
        proposals, problems, _notices, refusals = _propose(
            model, [target.tag], mode="run", slope=slope, margin_ft=margin_ft, band=band,
            avoid=avoid, via=[], explain=False, cost=cost, alternatives=alternatives,
            extra_prisms=occupancy)
        if proposals:
            return Outcome(proposal=proposals[0][0])
        # **Back to the TARGET tag.** A blocker names the proposal that is in the way —
        # ``PR-B-KITCH-DRAIN-PROPOSED`` — and the campaign's ledger is keyed on the run it
        # is a proposal FOR. Without this the rip-up never matches anything and a campaign
        # that is blocking itself reports fourteen refusals and no lifts, which is the one
        # outcome that looks like a building problem and is not.
        blockers = tuple(sorted({_target_of(b.tag) for r in refusals for b in r.blockers}))
        reason = (refusals[0].render() if refusals
                  else (problems[0] if problems else "no route, and no reason given"))
        return Outcome(reason=reason, blockers=blockers)

    result = run_campaign(targets, propose, inflate_m=CLEARANCE_M,
                          rip_up_budget=rip_up_budget)
    result.settings.update({
        "storey": storey, "trades": trades, "margin_ft": margin_ft,
        "locked": sorted(locked), "alternatives": alternatives,
    })
    if unassigned:
        # Reported, never inferred. A run whose system names no trade has no place in the
        # order, and putting it somewhere would be the campaign deciding on no evidence.
        result.skipped.extend(
            (tag, "no trade for this run's system — a campaign's order is its whole "
                  "content, so an unassigned run is named rather than placed in it")
            for tag in unassigned)

    _print(result, explain=explain)
    if as_json:
        console.print_json(json.dumps(result.as_dict()))
    if out_dir is not None:
        _write(result, out_dir, directory)
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


def _write(result: Any, out_dir: Path, house_dir: Path) -> None:
    """``report.json`` and ``proposed.py`` — read, then paste what you accept.

    Two files because they are for two readers, the same split
    :meth:`RouteProposal.as_dict` makes: an agent wants the structured report, a person
    wants the constructors. ``proposed.py`` carries the PROPOSED banner for the reason
    ``proposal.render`` gives — a block of dialect source in a file looks exactly like a
    plan, and the one thing a reader must not conclude is that it is one.
    """
    from typehaus.routing.proposal import render

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(result.as_dict(), indent=2) + "\n")
    (out_dir / "proposed.py").write_text(render(result.accepted) + "\n")
    console.print(f"[dim]wrote {out_dir / 'report.json'} and "
                  f"{out_dir / 'proposed.py'} — nothing under {house_dir / 'plan'} "
                  "changed[/dim]")
