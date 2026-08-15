"""`haus tasks` and `haus costs import` — the contractor PM surface.

Two commands that close the loop the rest of the takeoff opens. ``tasks`` groups the priced
BOM into ordered work packages and exports them in the column set Trello, Asana, Jira,
Monday and Buildertrend all ingest unmodified. ``costs import`` reads an edited estimate CSV
back through the *existing* ``apply_costs_ops``, so actual-vs-estimated round-trips through a
spreadsheet with no new server surface at all.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, app, console
from typehaus.findings import Severity

#: The work-item column set, chosen so the common PM tools import it unmodified: ``id`` and
#: ``title`` are the two every one of them requires, ``status`` maps to a Trello list or an
#: Asana section, and ``depends_on`` is what Buildertrend and MS Project read as a
#: predecessor list. Same writer as the estimate CSV.
TASK_COLUMNS = ("id", "slug", "title", "description", "status", "trade", "storey",
                "cost_code", "estimate_low", "estimate_high", "actual_cost", "depends_on",
                "element_tags")


def _load_priced_model(
    directory: Path,
) -> tuple[Any, dict[str, Any], dict[str, Any] | None, Any]:
    """(model, bom, estimate|None, costs state) — the spine both commands share."""
    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.resolve import resolve
    from typehaus.source import load_plan
    from typehaus.takeoff import bill_of_materials
    from typehaus.takeoff.costs import load_costs

    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    model, findings = resolve(loaded.plan)
    if any(finding.severity is Severity.ERROR for finding in findings):
        _print_findings(findings)
        raise typer.Exit(1)
    bom = bill_of_materials(model)
    try:
        prices = load_prices(directory)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc
    estimate = estimate_costs(bom, prices) if prices is not None else None
    return model, bom, estimate, load_costs(directory)


@app.command()
def tasks(
    house: Path | None = typer.Argument(None),
    csv: Path | None = typer.Option(None, "--csv", help="Write the work items here."),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Derive construction work packages at (trade x storey) from the priced takeoff.

    Ids are stable GlobalIds derived from the project uuid and the package slug, so
    re-exporting after a rebuild updates the same task rather than creating a second one.
    Durations, crew sizes and dates are deliberately absent: the model cannot know them.
    """
    import json

    from typehaus.takeoff.task_state import load_tasks
    from typehaus.takeoff.tasks import build_work_items

    d = _resolve_house(house)
    model, bom, estimate, costs = _load_priced_model(d)
    try:
        state = load_tasks(d)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc
    items = [item.as_dict() | {"status": state.status_of(item.slug)}
             for item in build_work_items(model, bom, estimate, costs)]
    if csv is not None:
        from typehaus.emit.csv_writer import write_csv

        rows = [{**item,
                 "estimate_low": item["estimate"]["low"],
                 "estimate_high": item["estimate"]["high"],
                 "depends_on": ", ".join(item["depends_on"]),
                 "element_tags": ", ".join(item["element_tags"])}
                for item in items]
        written = write_csv(csv, TASK_COLUMNS, rows)
        console.print(f"wrote {written} ({len(rows)} work items)", soft_wrap=True)
    if as_json:
        console.print_json(json.dumps({"tasks": items}))
        return
    if estimate is None:
        console.print("[yellow]no prices.toml — work packages carry no cost roll-up"
                      "[/yellow]", soft_wrap=True)
    console.print("[bold]Work packages[/bold]  (trade x storey, in construction order)")
    for item in items:
        depends = f"  [dim]after {len(item['depends_on'])}[/dim]" if item["depends_on"] else ""
        actual = (f"  actual ${item['actual_cost']:,.0f}"
                  if item["actual_cost"] is not None else "")
        console.print(f"  {item['status']:<12} {item['slug']:<32} "
                      f"{item['estimate_fmt']:>26}{actual}{depends}", soft_wrap=True)


costs_app = typer.Typer(name="costs", help="Cost tracking: import actuals from a spreadsheet.",
                        no_args_is_help=True, add_completion=False)
app.add_typer(costs_app, name="costs")


@costs_app.command("import")
def costs_import(
    csv_path: Path = typer.Argument(..., help="An estimate CSV with actual_cost/paid edited."),
    house: Path | None = typer.Option(None, "--house", help="House directory (default: cwd)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report changes without writing."),
) -> None:
    """Read ``actual_cost`` and ``paid`` back out of an edited estimate CSV.

    The file `haus takeoff --csv` writes, edited in a spreadsheet and handed back. Rows are
    matched on ``(section, key)`` — the same join the estimate prices and ``costs.toml``
    files under — and routed through the existing ``apply_costs_op``, so this adds no new
    state and no new server surface.

    A row whose ``(section, key)`` no longer matches the estimate is **reported, never
    silently applied**: it means the plan moved on under the spreadsheet, which is exactly
    the fact an owner has to see.
    """
    import csv as csv_module

    from typehaus.takeoff.costs import apply_costs_op, load_costs, write_costs

    d = _resolve_house(house)
    if not csv_path.exists():
        console.print(f"[red]no such file: {csv_path}[/red]", soft_wrap=True)
        raise typer.Exit(2)
    _model, _bom, estimate, _costs = _load_priced_model(d)
    known = {(section, row["key"])
             for section, body in (estimate or {}).get("sections", {}).items()
             for row in body.get("rows", [])}

    with csv_path.open(newline="") as handle:
        rows = list(csv_module.DictReader(handle))
    missing = {"section", "key", "actual_cost", "paid"} - set(rows[0] if rows else {})
    if missing:
        console.print(f"[red]{csv_path}: missing column(s) {sorted(missing)} — this is not "
                      f"an estimate CSV[/red]", soft_wrap=True)
        raise typer.Exit(2)

    state = load_costs(d)
    applied, stale, skipped = 0, [], 0
    for row in rows:
        slot = (row["section"], row["key"])
        actual, paid = _parse_actual(row.get("actual_cost")), _parse_bool(row.get("paid"))
        if actual is None and not paid:
            skipped += 1
            continue
        if slot not in known:
            stale.append(slot)
            continue
        # Merged onto the existing entry, not written over it: product, paid_date and note
        # are fields the CSV has no column for, and an import that silently erased the
        # product somebody recorded would be worse than one that refused to run.
        current = state.entries.get(slot[0], {}).get(slot[1])
        entry = current.as_dict() if current is not None else {}
        entry = {name: value for name, value in entry.items() if value is not None}
        entry["paid"] = paid
        if actual is not None:
            entry["actual_cost"] = actual
        state = apply_costs_op(state, {"op": "set_entry", "section": slot[0],
                                       "key": slot[1], "entry": entry})
        applied += 1

    for section, key in stale:
        console.print(f"[yellow]stale: {section}:{key} matches no current takeoff row — "
                      f"not applied[/yellow]", soft_wrap=True)
    if dry_run:
        console.print(f"[dim]dry run: {applied} row(s) would be written, {skipped} blank, "
                      f"{len(stale)} stale[/dim]", soft_wrap=True)
        return
    if applied:
        console.print(f"wrote {write_costs(d, state)} ({applied} row(s))", soft_wrap=True)
    else:
        console.print("nothing to import: no row carried an actual_cost or a paid flag")


def _parse_actual(raw: str | None) -> float | None:
    """Money as a spreadsheet writes it: blank, ``1234.56``, ``$1,234.56``."""
    if raw is None:
        return None
    text = raw.strip().replace("$", "").replace(",", "")
    if not text:
        return None
    try:
        value = float(text)
    except ValueError as exc:
        raise typer.BadParameter(f"actual_cost {raw!r} is not a number") from exc
    if value < 0:
        raise typer.BadParameter(f"actual_cost {raw!r} is negative")
    return value


def _parse_bool(raw: str | None) -> bool:
    return str(raw or "").strip().lower() in {"true", "yes", "y", "1", "x", "paid"}
