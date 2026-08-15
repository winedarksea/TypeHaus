"""`haus ls | fmt | render | print` — reading a plan and drawing it.

Split out of :mod:`typehaus.cli.app` by command family: the commands that report on plan
source (``ls``, ``fmt``) and the ones that emit the drawings a human or a jurisdiction reads
(``render``, ``print``). ``print`` is gated on the permit checklist and ``render`` is not,
deliberately — the agent-eyes snapshot loop (#52) has to work on a plan that does not pass
yet, while a permit set that does not pass must not exist.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from typehaus.cli._shared import _detail, _print_findings, _resolve_house, app, console
from typehaus.findings import Result


@app.command()
def ls(
    house: Optional[Path] = typer.Argument(None),
    summary: bool = typer.Option(False, help="compact whole-plan digest (#52)"),
) -> None:
    """List plan elements (or a compact agent-friendly digest with --summary)."""
    from typehaus.source import load_plan

    d = _resolve_house(house)
    result = load_plan(d)
    if result.plan is None:
        _print_findings(result.findings)
        raise typer.Exit(1)
    plan = result.plan
    if summary:
        from typehaus.cli.digest import print_summary

        print_summary(plan, console)
        return
    table = Table("storey", "kind", "tag", "detail")
    for storey in plan.storeys:
        for el in plan.storey_elements(storey.tag):
            table.add_row(storey.tag, el.element_kind, el.tag, _detail(el))
    console.print(table)


@app.command()
def fmt(house: Optional[Path] = typer.Argument(None)) -> None:
    """Normalize editable plan files and assign missing uids (WP2.2)."""
    from typehaus.source import fmt_house

    d = _resolve_house(house)
    report = fmt_house(d)
    total = sum(report.values())
    for rel, added in report.items():
        if added:
            console.print(f"  {rel}: +{added} uid(s)")
    console.print(f"[green]fmt ok[/green] — assigned {total} missing uid(s)")


@app.command()
def render(
    house: Optional[Path] = typer.Argument(None),
    view: str = typer.Option("plan", help="plan | site | section | elevation | details | 3d (#52 agent eyes)"),
    fmt: str = typer.Option("png", help="png | svg"),
) -> None:
    """Emit headless plan/section snapshots for the edit→build→check→look loop (#52)."""
    from typehaus.checks import load_preferences
    from typehaus.emit.draw import render_views, resolve_underlays
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    d = _resolve_house(house)
    result = load_plan(d)
    if result.plan is None:
        _print_findings(result.findings)
        raise typer.Exit(1)
    model, _ = resolve(result.plan)
    # The plans go out over the reference underlays configured in preferences.toml, so
    # "look at it" can mean look at it *against the survey* rather than at linework alone.
    underlays = resolve_underlays(d, load_preferences(d).underlays)
    paths = render_views(model, d / "out" / "render", view=view, fmt=fmt,
                         underlays=underlays)
    for p in paths:
        console.print(f"wrote {p}")


@app.command(name="print")
def print_sheets(
    house: Optional[Path] = typer.Argument(None),
    fmt: str = typer.Option("both", help="dxf | pdf | both"),
    handoff: bool = typer.Option(False, help="also write the architect-handoff bundle"),
    profile: Optional[str] = typer.Option(
        None, help="jurisdiction profile (default: preferences.toml, else the engine default)"),
    details: str = typer.Option(
        "primary", help="primary | all — 'primary' (default) keeps only starred transition "
                        "details (Transition.star) in the composed set; 'all' composes "
                        "every derived detail sheet"),
) -> None:
    """Compose the permit-set PDF, plan DXFs, and optional architect handoff (M3)."""
    from typehaus.checks import evaluate_permit_checklist, load_preferences, run
    from typehaus.checks.run import resolve_profile
    from typehaus.emit.draw import write_permit_set, write_plan_dxfs
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    d = _resolve_house(house)
    result = load_plan(d)
    if result.plan is None:
        _print_findings(result.findings)
        raise typer.Exit(1)
    preferences = load_preferences(d)
    # One jurisdiction decides both the gate and what the sheets say they were composed
    # against; `--profile` overrides the house's own `[project].jurisdiction`.
    jurisdiction = resolve_profile(preferences, profile)
    checklist = evaluate_permit_checklist(run(result.plan, d, profile=jurisdiction.name),
                                          jurisdiction)
    if not checklist.ok:
        console.print("[red]permit print blocked: declared checklist has failures or unknowns[/red]")
        for item in checklist.items:
            if item.blocking and item.result is not Result.PASS:
                console.print(f"  {item.label}: {item.detail}")
        raise typer.Exit(1)
    model, _ = resolve(result.plan)
    out = d / "out"
    if fmt in ("dxf", "both"):
        for path in write_plan_dxfs(model, out / "sheets"):
            console.print(f"wrote {path}")
    if fmt in ("pdf", "both"):
        path, _ = write_permit_set(model, out / "permit_set.pdf", preferences,
                                   profile=jurisdiction, details=details)
        console.print(f"wrote {path}")
    if handoff:
        _write_handoff_bundle(d, model, preferences, jurisdiction)


def _write_handoff_bundle(house: Path, model, preferences=None, profile=None) -> None:
    """Copy only generated/project-owned artifacts into the architect handoff."""
    import shutil

    from typehaus.emit.draw import write_permit_set, write_plan_dxfs
    from typehaus.server.model_json import write_model_json

    handoff = house / "out" / "handoff"
    handoff.mkdir(parents=True, exist_ok=True)
    write_permit_set(model, handoff / "permit_set.pdf", preferences, profile=profile)
    write_plan_dxfs(model, handoff / "dxfs")
    write_model_json(model, handoff / "model.json")
    for source, destination in ((house / "brief.md", handoff / "brief.md"),
                                (house.parent.parent / "plans" / "01-decisions.md",
                                 handoff / "decision_log.md")):
        if source.exists():
            shutil.copy2(source, destination)
    try:
        from typehaus.emit.ifc import emit_ifc

        emit_ifc(model, handoff / "model_core.ifc", lod="core")
    except RuntimeError as exc:
        console.print(f"[yellow]handoff IFC unavailable: {exc}[/yellow]")
    console.print(f"wrote {handoff}")
