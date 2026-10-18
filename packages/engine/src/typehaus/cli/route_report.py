"""Routing reports and review artifacts. See docs/routing.md for the workflow."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import typer

from typehaus.cli._shared import console
from typehaus.cli.route_support import _storey_datum
from typehaus.routing.proposal import render

_DECISION_FIELDS = (
    "tag", "storey", "kind", "system", "developed_ft", "bends", "cost_in_equivalent",
    "notes", "after_paste",
)


def proposal_rows(model: Any, proposals: list[tuple[Any, str]]) -> list[dict]:
    """Project coordinates stay absolute; printed pipe/duct elevations use their storey."""
    return [dict(proposal.as_dict(storey_datum_m=(
        0.0 if proposal.kind == "conduit" else _storey_datum(model, storey))), storey=storey)
        for proposal, storey in proposals]


def decision_summary(report: dict, out_dir: Path) -> dict:
    """Keep all diagnostics and evaluation changes; leave geometry and source on disk."""
    key = "accepted" if "accepted" in report else "proposals"
    rows = report[key]
    summary = dict(report)
    summary[key] = [
        {**{name: row[name] for name in _DECISION_FIELDS},
         "fitting_gaps": [fitting for fitting in row["fittings"]
                          if fitting["catalog"] is None or fitting["gap"]]}
        for row in rows
    ]
    summary["artifacts"] = {
        "report": str(out_dir / "report.json"),
        "source": str(out_dir / "proposed.py"),
    }
    return summary


def source_artifact(rows: list[dict]) -> str:
    """Group review source by storey/frame and label mutually exclusive alternatives."""
    lines = [render([])]
    alternatives = Counter(row["tag"].split("-PROPOSED")[0] for row in rows)
    groups: dict[tuple[str, bool], list[dict]] = {}
    for row in rows:
        groups.setdefault((row["storey"], row["kind"] == "conduit"), []).append(row)
    for (storey, absolute), group in groups.items():
        frame = "project-frame absolute" if absolute else "storey-relative"
        lines.append(f"# STOREY: {storey}; elevations are {frame}.")
        for row in group:
            target = row["tag"].split("-PROPOSED")[0]
            if alternatives[target] > 1:
                lines.append(f"# ALTERNATIVES for {target}: paste exactly ONE.")
            lines.extend(f"# NOTE: {note}" for note in row["notes"])
            lines.extend(f"# FITTING: {fitting['gap']}" for fitting in row["fittings"]
                         if fitting["gap"])
            lines.append(row["source"])
            lines.extend(f"# AFTER PASTING: {note}" for note in row["after_paste"])
            lines.append("")
    return "\n".join(lines) + "\n"


def validate_output_directory(out_dir: Path | None, house_dir: Path) -> None:
    if out_dir is not None and out_dir.resolve().is_relative_to((house_dir / "plan").resolve()):
        raise typer.BadParameter("--out must be outside the house's plan/ directory")


def write_artifacts(report: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    rows = report["accepted"] if "accepted" in report else report["proposals"]
    (out_dir / "proposed.py").write_text(source_artifact(rows))


def emit_report(report: dict, *, as_json: bool, summary: bool,
                out_dir: Path | None) -> None:
    if out_dir is not None:
        write_artifacts(report, out_dir)
    if as_json:
        output = decision_summary(report, out_dir) if summary else report
        # Rich wraps long strings at terminal width; stdout must remain valid JSON.
        print(json.dumps(output, ensure_ascii=False, indent=None if summary else 2))
    elif out_dir is not None:
        console.print(f"[dim]wrote {out_dir / 'report.json'} and "
                      f"{out_dir / 'proposed.py'}[/dim]")


def report_proposals(model: Any, directory: Path, proposals: list[tuple[Any, str]], *,
                     evaluations: list, problems: list[str], notices: list[str],
                     refusals: list, clock: list[str] | None, cost: Any,
                     explain: bool, as_json: bool, summary: bool,
                     out_dir: Path | None) -> None:
    from typehaus.cli.route_eval import as_dict, render_reports

    report_notices = [*notices, *(f"timing: {line}" for line in clock or ())]
    if explain:
        report_notices.extend(cost.table())
    if as_json or out_dir is not None:
        report = {
            "house": str(directory),
            "storey": proposals[0][1] if proposals else None,
            "proposals": proposal_rows(model, proposals),
            "evaluations": [as_dict(item) for item in evaluations],
            "problems": list(problems), "notices": report_notices,
            "refusals": [item.payload() for item in refusals],
        }
        emit_report(report, as_json=as_json, summary=summary, out_dir=out_dir)
    if as_json:
        return
    for line in report_notices:
        console.print(f"[dim]{line}[/dim]")
    for line in problems:
        console.print(f"[yellow]{line}[/yellow]")
    for line in render_reports(evaluations):
        console.print(line)
    if not proposals:
        if problems or refusals:
            console.print("[red]no proposal — see above. A route that cannot be found is "
                          "reported, never approximated.[/red]")
        return
    groups: dict[tuple[str, bool], list] = {}
    for proposal, storey in proposals:
        groups.setdefault((storey, proposal.kind == "conduit"), []).append(proposal)
    for (storey, absolute), group in groups.items():
        datum = 0.0 if absolute else _storey_datum(model, storey)
        console.print(render(group, storey_datum_m=datum, explain=explain))
        frame = "project-frame absolute" if absolute else f"relative to the `{storey}` storey"
        console.print(f"[dim]elevations are {frame}[/dim]")
    bases = Counter(proposal.tag.split("-PROPOSED")[0] for proposal, _ in proposals)
    if any(count > 1 for count in bases.values()):
        console.print("[yellow]these are ALTERNATIVES to the same problem and they share "
                      "a `serves` — paste exactly ONE[/yellow]")
