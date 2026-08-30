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
                    "coverage_sqft", "nominal_stock", "milling_profile", "layup",
                    "boards_per_piece", "board_width_in", "rough_width_in",
                    "rough_board_feet", "rough_surface_sqft", "stock_note", "element_tags")


def _as_tags(value: object) -> list[str]:
    """A row's ``tags`` narrowed for export — BOM rows are ``dict[str, object]``."""
    return [str(tag) for tag in value] if isinstance(value, (list, tuple)) else []


def _finished_size(row: dict[str, object]) -> str:
    """``T x W x L`` in inches for a cut piece; empty for a coverage row."""
    if row.get("pieces") is None:
        return ""
    return (f"{row['finished_thickness_in']}\" x {row['finished_width_in']}\" x "
            f"{row['finished_length_in']}\"")


def _flat_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """One dict per row carrying exactly ``MILLWORK_COLUMNS``, blanks filled in.

    Shared by both writers so a CSV and a Markdown file of the same schedule can never
    disagree about a column or an empty cell.
    """
    return [{**{column: "" for column in MILLWORK_COLUMNS},
             **{key: value for key, value in row.items() if key in MILLWORK_COLUMNS},
             "finished_size": _finished_size(row),
             "element_tags": ", ".join(_as_tags(row.get("tags")))}
            for row in rows]


def _markdown(rows: list[dict[str, object]]) -> str:
    """The schedule as a GitHub-flavoured Markdown table plus its species totals.

    The format a mill or a family member can actually read in an email. CSV is for a
    spreadsheet and turns every one of these numbers into a bare float; this keeps the
    inch marks, the species column and the stock notes that say what to do.
    """
    flat = _flat_rows(rows)
    header = [column.replace("_", " ") for column in MILLWORK_COLUMNS]
    lines = ["# Hardwood milling schedule", "",
             "Sorted by use, then stock, then profile. Every quantity here is also billed "
             "in another section of the takeoff — this is a *view* for the mill, not an "
             "addition to the estimate.", "",
             "| " + " | ".join(header) + " |",
             "|" + "|".join("---" for _ in header) + "|"]
    for row in flat:
        cells = [str(row[column]) if row[column] not in (None, "") else ""
                 for column in MILLWORK_COLUMNS]
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in cells) + " |")
    totals: dict[str, float] = {}
    for row in rows:
        rough = row.get("rough_board_feet")
        if isinstance(rough, (int, float)):
            species = str(row.get("species") or "unknown")
            totals[species] = totals.get(species, 0.0) + float(rough)
    lines += ["", "## Rough board feet by species", "",
              "| species | rough bf |", "|---|---|"]
    lines += [f"| {species} | {totals[species]:.1f} |" for species in sorted(totals)]
    lines += ["", f"**Total {sum(totals.values()):.1f} rough board feet.** Rough figures "
                  "include a straight-line/joint width loss and a defect-and-trim length "
                  "allowance.", ""]
    return "\n".join(lines)


@app.command()
def millwork(
    house: Optional[Path] = typer.Argument(None),
    csv: Optional[Path] = typer.Option(None, "--csv", help="Write the schedule as CSV."),
    md: Optional[Path] = typer.Option(
        None, "--md", help="Write the schedule as a Markdown table (emailable)."),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Report the hardwood milling schedule: cut list, rough stock, and how each is laid up.

    Every quantity is a *view* of one already billed elsewhere — the rows carry their
    ``also_in_*`` mirror flags — so nothing here adds to the estimate. What it adds is the
    rough stock a mill has to saw to land the finished piece, and the ``layup`` that says
    whether that piece is one board, a glued panel, a field of boards or a sawn timber.
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

        flat = _flat_rows(rows)
        written = write_csv(csv, MILLWORK_COLUMNS, flat)
        console.print(f"wrote {written} ({len(flat)} schedule rows)", soft_wrap=True)
    if md is not None:
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(_markdown(rows), encoding="utf-8")
        console.print(f"wrote {md} ({len(rows)} schedule rows)", soft_wrap=True)
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
        species = str(row.get("species") or "?")
        stock = str(row.get("nominal_stock") or "?")
        profile = str(row.get("milling_profile") or "-")
        layup = str(row.get("layup") or "")
        boards = row.get("boards_per_piece")
        if isinstance(boards, int) and boards > 1:
            layup = f"{layup} x{boards}"
        rough_bf = row.get("rough_board_feet")
        bf = f"{rough_bf:>8.1f} bf" if isinstance(rough_bf, (int, float)) else "       ? bf"
        console.print(f"  {str(row['use']):<19} {pieces}{size:<32} "
                      f"[cyan]{species:<9}[/cyan]{stock:>6} {profile:<9}"
                      f"{layup:<19}{bf}", soft_wrap=True)
        if row.get("stock_note"):
            console.print(f"      [dim]{row['stock_note']}[/dim]", soft_wrap=True)
        if isinstance(rough_bf, (int, float)):
            totals[species] = totals.get(species, 0.0) + float(rough_bf)
    console.print("[bold]Rough board feet by species[/bold]")
    for species in sorted(totals):
        console.print(f"  {species:<12} {totals[species]:>9.1f} bf", soft_wrap=True)
    console.print("[dim]A view: every quantity is billed in another section (see the "
                  "also_in_* flags in --json). Rough figures include a "
                  "straight-line/joint width loss and a defect-and-trim length "
                  "allowance. --csv and --md export the same rows.[/dim]", soft_wrap=True)
