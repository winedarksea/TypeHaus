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

    from typehaus.schedule.timing import visit_dates
    from typehaus.takeoff.task_state import load_tasks

    dates = visit_dates(board, load_tasks(directory))
    if board.errors:
        console.print("[red]the sequence graph does not hold — the board below is the "
                      "last valid state:[/red]")
        for error in board.errors:
            console.print(f"  [red]{error}[/red]", soft_wrap=True, markup=False)

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
            for exception in visit.exceptions:
                # Exceptions first, always: "we went ahead anyway" outranks every other
                # line on this visit.
                _line("!", "red", f"EXCEPTION {exception['at']}: went ahead against "
                                  f"{exception['hold']}")
            _dates(dates.get(slug))
            for point in visit.checkpoints:
                tick = {"done": "x", "in_progress": ">"}.get(str(point["status"]), " ")
                cure = (f"  (+{point['cure_days']}d cure)" if point.get("cure_days")
                        else "")
                after = (f"  after {', '.join(point['after'])}" if point.get("after")
                         else "")
                _line(tick, "cyan",
                      f"{point['label'] or point['id']}{after}{cure}")
            for constraint in readiness.blockers:
                _line("x", "red", constraint.label + _hold_detail(constraint))
            for constraint in readiness.attention:
                _line("?", "yellow", constraint.label + _hold_detail(constraint))
            if visit.needs_rewalk:
                _line("~", "yellow", "the handoff set changed under existing ticks — "
                                     "needs re-walk")
            if readiness.state in ("done", "in_progress"):
                skipped = {x["id"]: x["reason"] for x in visit.skipped}
                for item in handoff_items(model, visit):
                    tick = ("x" if item.id in visit.checked
                            else ("-" if item.id in skipped else " "))
                    why = (f"  [dim]skipped: {skipped[item.id]}[/dim]"
                           if item.id in skipped else "")
                    console.print(f"      [{tick}] {item.label}{why}", soft_wrap=True)
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

    state = load_inspections(directory)
    authorities = state.authorities
    console.print(f"[bold]Inspections[/bold]  [dim]{board.profile_name}[/dim]")
    permit = state.permit
    if not permit.is_empty:
        parts = [f"{name} {getattr(permit, name)}" for name in
                 ("number", "issued", "expires", "code_edition", "nec_edition")
                 if getattr(permit, name)]
        console.print(f"[dim]permit: {'; '.join(parts)}[/dim]", soft_wrap=True)
    # What the authority has NOT told you yet. Minn. R. 1300.0210 subp. 4 obliges them to
    # state these at issuance, so an empty field is an open item and not a default.
    unknown = sorted(
        f"{key}: {', '.join(n for n in ('window', 'lead_days') if getattr(one, n) is None)}"
        for key, one in authorities.items()
        if one.phone and (one.window is None or one.lead_days is None))
    if unknown:
        console.print("[yellow]not published — ask at permit issuance "
                      "(MN Rules 1300.0210 subp. 4):[/yellow]", soft_wrap=True)
        for line in unknown:
            console.print(f"  {line}", soft_wrap=True, markup=False)
    for record in board.inspections:
        mark = _INSPECTION_MARK.get(record.state, record.state)
        authority = authorities.get(record.authority)
        who = f"  [dim]{authority.label}[/dim]" if authority else f"  [dim]{record.authority}[/dim]"
        console.print(f"\n {record.sequence + 1:>2}. {mark:<22} {record.id}{who}")
        console.print(f"     {record.label}", soft_wrap=True)
        if record.applicability is not None and record.applicability.applies is not True:
            console.print(f"     [dim]{record.applicability.evidence}[/dim]",
                          soft_wrap=True)
        if record.scope:
            console.print(f"     [dim]covers {', '.join(record.scope)}[/dim]",
                          soft_wrap=True, markup=False)
        for attempt in record.attempts:
            colour = "green" if attempt["result"] == "pass" else "red"
            console.print(f"     [{colour}]{attempt['date']} {attempt['result']}"
                          f"[/{colour}]", end="")
            detail = "; ".join(
                list(attempt["corrections"])
                + ([f"released {', '.join(attempt['approved'])}"]
                   if attempt["approved"] else []))
            console.print(f"  {detail}" if detail else "", soft_wrap=True, markup=False)
        for prerequisite in record.unmet:
            console.print("     [red]x[/red] ", end="")
            console.print(prerequisite.label, soft_wrap=True, markup=False,
                          highlight=False)


def _line(mark: str, colour: str, text: str) -> None:
    """One indented line under a visit. ``markup=False`` on the text: a hold that says
    ``[permit].code_edition`` is not a rich style tag, and rich would eat it."""
    console.print(f"      [{colour}]{mark}[/{colour}] ", end="")
    console.print(text, soft_wrap=True, markup=False, highlight=False)


def _hold_detail(constraint: Any) -> str:
    """The three fields that turn a hold into a task, plus a locate's derived dates."""
    parts = [f"on {constraint.owner}" if constraint.owner else "",
             f"next: {constraint.next_action}" if constraint.next_action else "",
             f"chase {constraint.follow_up}" if constraint.follow_up else "",
             constraint.derived]
    shown = [p for p in parts if p]
    return f"  ({'; '.join(shown)})" if shown else ""


def _dates(record: Any) -> None:
    """Suggested / planned / booked, and the threat to a booking. Never a default."""
    if record is None:
        return
    parts: list[str] = []
    if record.suggested_start:
        parts.append(f"suggested {record.suggested_start}..{record.suggested_finish}")
    elif record.why:
        parts.append(record.why)
    if record.planned:
        parts.append(f"planned {record.planned}")
    if record.booked:
        parts.append(f"booked {record.booked}")
    if record.threatened_by_days:
        parts.append(f"THREATENED by {record.threatened_by_days}d")
    for item in record.materials:
        if item.get("why"):
            parts.append(f"{item['id']}: {item['why']}")
        elif item.get("order_by") and not item.get("on_site"):
            parts.append(f"{item['id']}: order by {item['order_by']}")
    if parts:
        _line("·", "dim", "; ".join(parts))


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
