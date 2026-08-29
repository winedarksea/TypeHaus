"""`haus millwork` — the hardwood milling schedule, for handing to a sawyer.

Its own command rather than a section of ``haus takeoff --csv`` because that writer flattens
``payload["cost_estimate"]["sections"]`` (``takeoff/estimate_csv.py``), so only *priced* rows
survive into the file — today exactly one ``wood_surfaces`` row reaches it. A milling
schedule is not a priced view: dollars are opt-in and the mill is quoting, not being quoted
(plans/01-decisions.md #28). Parallel to ``haus tasks``, which exports for the same reason.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, app, console
from typehaus.findings import Severity

#: The mill's column set: what to cut, how many, to what finished size, from what stock,
#: with what profile — and whether it can come off one board.
MILLWORK_COLUMNS = ("use", "species", "material", "pieces", "finished_size",
                    "coverage_sqft", "nominal_stock", "milling_profile",
                    "rough_board_feet", "rough_surface_sqft", "laminations", "glue_up",
                    "glue_up_reason", "element_tags")


def _as_tags(value: object) -> list[str]:
    """A row's ``tags`` narrowed for the CSV — BOM rows are ``dict[str, object]``."""
    return [str(tag) for tag in value] if isinstance(value, (list, tuple)) else []


def _finished_size(row: dict[str, object]) -> str:
    """``T x W x L`` in inches for a cut piece; empty for a coverage row."""
    if row.get("pieces") is None:
        return ""
    return (f"{row['finished_thickness_in']}\" x {row['finished_width_in']}\" x "
            f"{row['finished_length_in']}\"")


@app.command()
def millwork(
    house: Optional[Path] = typer.Argument(None),
    csv: Optional[Path] = typer.Option(None, "--csv", help="Write the schedule here."),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Report the hardwood milling schedule: cut list, rough stock, and glue-up flags.

    Every quantity is a *view* of one already billed elsewhere — the rows carry their
    ``also_in_*`` mirror flags — so nothing here adds to the estimate. What it adds is the
    rough stock a mill has to saw to land the finished piece.
    """
    import json

    from typehaus.resolve import resolve
    from typehaus.source import load_plan
    from typehaus.takeoff.hardwood import hardwood_takeoff

    directory = _resolve_house(house)
    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    model, findings = resolve(loaded.plan)
    if any(finding.severity is Severity.ERROR for finding in findings):
        _print_findings(findings)
        raise typer.Exit(1)
    rows = hardwood_takeoff(model)

    if csv is not None:
        from typehaus.emit.csv_writer import write_csv

        flat = [{**{column: "" for column in MILLWORK_COLUMNS},
                 **{key: value for key, value in row.items()
                    if key in MILLWORK_COLUMNS},
                 "finished_size": _finished_size(row),
                 "element_tags": ", ".join(_as_tags(row.get("tags")))}
                for row in rows]
        written = write_csv(csv, MILLWORK_COLUMNS, flat)
        console.print(f"wrote {written} ({len(flat)} schedule rows)", soft_wrap=True)
    if as_json:
        console.print_json(json.dumps({"hardwood": rows}))
        return

    if not rows:
        console.print("[yellow]no hardwood scheduled — this house declares no "
                      "MillworkStandard and no species wood surfaces[/yellow]",
                      soft_wrap=True)
        return

    console.print("[bold]Milling schedule[/bold]  (by use, then stock, then profile)")
    totals: dict[str, float] = {}
    for row in rows:
        size = _finished_size(row) or f"{row.get('coverage_sqft', 0)} SF coverage"
        pieces = f"{row['pieces']:>4} x " if row.get("pieces") is not None else "       "
        stock = str(row.get("nominal_stock") or "?")
        profile = str(row.get("milling_profile") or "-")
        rough_bf = row.get("rough_board_feet")
        bf = f"{rough_bf:>8.1f} bf" if isinstance(rough_bf, (int, float)) else "       ? bf"
        flag = "  [yellow]GLUE-UP[/yellow]" if row.get("glue_up") else ""
        console.print(f"  {str(row['use']):<19} {pieces}{size:<34} "
                      f"{stock:>4} {profile:<8}{bf}{flag}", soft_wrap=True)
        if row.get("glue_up") and row.get("glue_up_reason"):
            console.print(f"      [dim]{row['glue_up_reason']}[/dim]", soft_wrap=True)
        if isinstance(rough_bf, (int, float)):
            totals[str(row.get("species") or "unknown")] = (
                totals.get(str(row.get("species") or "unknown"), 0.0) + float(rough_bf))
    console.print("[bold]Rough board feet by species[/bold]")
    for species in sorted(totals):
        console.print(f"  {species:<12} {totals[species]:>9.1f} bf", soft_wrap=True)
    console.print("[dim]A view: every quantity is billed in another section (see the "
                  "also_in_* flags in --json). Rough figures include a "
                  "straight-line/joint width loss and a defect-and-trim length "
                  "allowance.[/dim]", soft_wrap=True)
