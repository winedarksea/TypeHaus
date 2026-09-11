"""``haus schedule`` and ``haus inspections`` — the site surface without a phone.

Text mode is not a fallback anybody should apologise for: it is the version that works in a
basement with no signal, and it is what the UI is checked against. Everything either
command prints is derived by :mod:`typehaus.schedule.readiness`, so there is exactly one
answer to "is this ready" in this program.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, app, console

#: How a readiness state prints. Colour carries the same information as the word, for the
#: terminal that has no colour.
_VISIT_MARK = {"ready": "[green]ready[/green]", "blocked": "[red]blocked[/red]",
               "in_progress": "[yellow]on site[/yellow]", "done": "[cyan]done[/cyan]",
               "verified": "[green]verified[/green]"}
_INSPECTION_MARK = {
    "passed": "[green]passed[/green]", "failed": "[red]failed[/red]",
    "scheduled": "[cyan]scheduled[/cyan]", "requested": "[cyan]requested[/cyan]",
    "ready": "[green]ready[/green]", "not_ready": "[yellow]not ready[/yellow]",
    "not_applicable": "[dim]n/a[/dim]", "waived": "[dim]waived[/dim]"}


def _board(directory: Path) -> tuple[Any, Any, Any]:
    """``(model, board, work items)`` — the spine both commands share."""
    from typehaus.checks.registry import run_checks
    from typehaus.checks.run import build_context
    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.findings import Severity
    from typehaus.schedule.inspection_state import load_inspections
    from typehaus.schedule.readiness import make_ready
    from typehaus.server.space_summary import estimate_areas
    from typehaus.source import load_plan
    from typehaus.takeoff import bill_of_materials
    from typehaus.takeoff.costs import load_costs
    from typehaus.takeoff.product_labels import product_labels
    from typehaus.takeoff.task_state import load_tasks
    from typehaus.takeoff.tasks import build_work_items

    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    ctx, resolve_findings = build_context(loaded.plan, directory)
    if any(finding.severity is Severity.ERROR for finding in resolve_findings):
        _print_findings(resolve_findings)
        raise typer.Exit(1)
    model = ctx.model
    report = run_checks(ctx)
    bom = bill_of_materials(model)
    try:
        prices = load_prices(directory)
        costs = load_costs(directory)
        tasks = load_tasks(directory)
        inspections = load_inspections(directory)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc
    estimate = (estimate_costs(bom, prices, estimate_areas(model),
                               product_labels(loaded.plan))
                if prices is not None else None)
    items = build_work_items(model, bom, estimate, costs)
    board = make_ready(model, items, tasks, inspections, ctx.profile,
                       list(report.findings), costs)
    return model, board, items


@app.command()
def schedule(
    house: Path | None = typer.Argument(None),
    milestone: str | None = typer.Option(None, "--milestone",
                                         help="Show only this milestone."),
    propose: str | None = typer.Option(None, "--propose",
                                       help="Propose a visit split for this package slug."),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """The build board: visits, what is ready, and exactly what is in the way.

    Readiness is derived; dates are authored. Nothing here computes a duration, a lead
    time or a calendar date — see ``docs/site-state-format.md``.
    """
    from typehaus.schedule.handoff import handoff_items
    from typehaus.schedule.propose import propose_all

    directory = _resolve_house(house)
    model, board, items = _board(directory)

    if propose is not None:
        matched = [item for item in items if item.slug == propose]
        if not matched:
            console.print(f"[red]no work package {propose!r}; try one of:[/red]")
            for item in items:
                console.print(f"  {item.slug}", soft_wrap=True)
            raise typer.Exit(2)
        specs = board.inspections
        proposals = propose_all(matched, tuple(
            type("S", (), {"id": r.id, "gates": r.gates})() for r in specs))
        if not proposals:
            console.print(f"{propose}: one row family — nothing to split.", soft_wrap=True)
            return
        console.print(f"[bold]Proposed visits for {propose}[/bold]  "
                      "[dim](nothing is written — paste what you accept)[/dim]")
        for proposal in proposals[propose]:
            console.print("")
            # markup=False: the very first line is ``[visits."..."]``, which rich would
            # read as a style tag and silently eat.
            console.print(proposal["toml"], soft_wrap=True, highlight=False,
                          markup=False)
        return

    if as_json:
        console.print_json(json.dumps(_schedule_payload(model, board, directory)))
        return

    for record in board.milestones:
        if milestone is not None and record.id != milestone:
            continue
        console.print(f"\n[bold]{record.label}[/bold]  [dim]{record.state}[/dim]")
        for slug in record.visits:
            visit = board.visit(slug)
            readiness = board.readiness[slug]
            mark = _VISIT_MARK.get(readiness.state, readiness.state)
            when = f"  [dim]{visit.scheduled}[/dim]" if visit.scheduled else ""
            who = f"  {visit.assignee}" if visit.assignee else ""
            console.print(f"  {mark:<22} {slug}{who}{when}", soft_wrap=True)
            for constraint in readiness.blockers:
                console.print(f"      [red]x[/red] {constraint.label}", soft_wrap=True)
            for constraint in readiness.attention:
                console.print(f"      [yellow]?[/yellow] {constraint.label}",
                              soft_wrap=True)
            if readiness.state in ("done", "in_progress"):
                for item in handoff_items(model, visit):
                    tick = "x" if item.id in visit.checked else " "
                    console.print(f"      [{tick}] {item.label}", soft_wrap=True)
        for inspection_id in record.inspections:
            inspection = board.inspection(inspection_id)
            if inspection is None:
                continue
            mark = _INSPECTION_MARK.get(inspection.state, inspection.state)
            console.print(f"  {mark:<22} insp/{inspection.id}  [dim]{inspection.label}"
                          f"[/dim]", soft_wrap=True)
    if board.stale:
        console.print("\n[yellow]authored but no longer derived from the model:[/yellow]")
        for slug in board.stale:
            console.print(f"  {slug}", soft_wrap=True)


@app.command()
def inspections(
    house: Path | None = typer.Argument(None),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Every inspection this jurisdiction requires, and what stands before each one."""
    directory = _resolve_house(house)
    _model, board, _items = _board(directory)
    if as_json:
        console.print_json(json.dumps(_inspections_payload(directory, board)))
        return

    from typehaus.schedule.inspection_state import load_inspections

    authorities = load_inspections(directory).authorities
    console.print(f"[bold]Inspections[/bold]  [dim]{board.profile_name}[/dim]")
    for record in board.inspections:
        mark = _INSPECTION_MARK.get(record.state, record.state)
        authority = authorities.get(record.authority)
        who = f"  [dim]{authority.label}[/dim]" if authority else f"  [dim]{record.authority}[/dim]"
        console.print(f"\n {record.sequence + 1:>2}. {mark:<22} {record.id}{who}")
        console.print(f"     {record.label}", soft_wrap=True)
        if record.applicability is not None and record.applicability.applies is not True:
            console.print(f"     [dim]{record.applicability.evidence}[/dim]",
                          soft_wrap=True)
        for prerequisite in record.unmet:
            console.print(f"     [red]x[/red] {prerequisite.label}", soft_wrap=True)


def _schedule_payload(model: Any, board: Any, directory: Path | None = None
                      ) -> dict[str, Any]:
    from typehaus.schedule.handoff import handoff_items
    from typehaus.schedule.timing import visit_dates
    from typehaus.takeoff.task_state import load_tasks

    tasks = load_tasks(directory) if directory is not None else None
    dates = visit_dates(board, tasks) if tasks is not None else {}
    visits = []
    for visit in board.visits:
        readiness = board.readiness[visit.slug]
        visits.append(visit.as_dict() | {
            "readiness": readiness.state,
            "constraints": [c.as_dict() for c in readiness.constraints],
            "handoff": [item.as_dict() | {"checked": item.id in visit.checked}
                        for item in handoff_items(model, visit)],
            "dates": (dates[visit.slug].as_dict() if visit.slug in dates else {})})
    return {"profile": board.profile_name, "checks_pending": False,
            "milestones": [m.as_dict() for m in board.milestones],
            "visits": visits, "proposals": {}, "stale": list(board.stale),
            "errors": list(board.errors)}


def _inspections_payload(directory: Path, board: Any) -> dict[str, Any]:
    from typehaus.schedule.inspection_state import load_inspections

    state = load_inspections(directory)
    return {"profile": board.profile_name, "checks_pending": False,
            "authorities": {key: value.as_dict()
                            for key, value in state.authorities.items()},
            "inspections": [record.as_dict() for record in board.inspections]}
