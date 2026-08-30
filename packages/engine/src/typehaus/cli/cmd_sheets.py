"""`haus ls | fmt | render | print` — reading a plan and drawing it.

Split out of :mod:`typehaus.cli.app` by command family: the commands that report on plan
source (``ls``, ``fmt``) and the ones that emit the drawings a human or a jurisdiction reads
(``render``, ``print``). ``print`` is gated on the permit checklist and ``render`` is not,
deliberately — the agent-eyes snapshot loop (#52) has to work on a plan that does not pass
yet, while a permit set that does not pass must not exist.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.table import Table

from typehaus.cli._shared import _detail, _print_findings, _resolve_house, app, console
from typehaus.findings import Result


@app.command()
def ls(
    house: Path | None = typer.Argument(None),
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
def fmt(house: Path | None = typer.Argument(None)) -> None:
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
    house: Path | None = typer.Argument(None),
    view: str = typer.Option(
        "plan", help="plan | site | section | elevation | details | 3d | all (#52 agent eyes)"),
    fmt: str = typer.Option("png", help="png | svg"),
    dpi: int | None = typer.Option(
        None, help="raster resolution; default 110 (screen), 300 for details. An ARCH D "
                   "sheet at plate quality is --dpi 300 → 10800 x 7200 px"),
    paper: str | None = typer.Option(
        None, help="ledger | arch-d — compose onto a real sheet (border, title block, "
                   "graphic scale bar, north arrow) at TRUE architectural scale"),
    scale: str | None = typer.Option(
        None, help="force a scale, e.g. '1/4\" = 1\'-0\"' or 'fit'; implies --paper ledger"),
    underlay: bool = typer.Option(
        True, "--underlay/--no-underlay",
        help="draw the preferences.toml reference underlays behind the linework. On for "
             "the look-at-it loop; --no-underlay for anything anybody else reads"),
) -> None:
    """Emit headless plan/section snapshots for the edit→build→check→look loop (#52).

    Two kinds of output, and ``--paper`` is the switch: without it a frameless snapshot
    fitted to its content (fast, for looking at), with it a real sheet whose printed scale
    is chosen from the standard ladder and true by construction. The PDF from ``haus
    print`` remains the large-format deliverable — it is vector and has no resolution at
    all; a raster only ever approximates it.
    """
    from typehaus.checks import load_preferences
    from typehaus.emit.draw import render_views, resolve_underlays
    from typehaus.emit.draw.sheet_writer import LEDGER, resolve_paper
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    d = _resolve_house(house)
    result = load_plan(d)
    if result.plan is None:
        _print_findings(result.findings)
        raise typer.Exit(1)
    model, _ = resolve(result.plan)
    # A forced scale is meaningless without a sheet to print it on — the frameless path has
    # no viewport to hold the drawing to — so asking for one asks for the default sheet.
    size = LEDGER if (paper is None and scale is not None) else None
    # The plans go out over the reference underlays configured in preferences.toml, so
    # "look at it" can mean look at it *against the survey* rather than at linework alone.
    underlays = resolve_underlays(d, load_preferences(d).underlays) if underlay else ()
    try:
        if paper is not None:
            size = resolve_paper(paper)
        paths = render_views(model, d / "out" / "render", view=view, fmt=fmt,
                             underlays=underlays, dpi=dpi, paper=size, scale=scale)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from None
    for p in paths:
        console.print(f"wrote {p}")


@app.command(name="print")
def print_sheets(
    house: Path | None = typer.Argument(None),
    fmt: str = typer.Option("both", help="dxf | pdf | both"),
    handoff: bool = typer.Option(False, help="also write the architect-handoff bundle"),
    profile: str | None = typer.Option(
        None, help="jurisdiction profile (default: preferences.toml, else the engine default)"),
    details: str = typer.Option(
        "primary", help="primary | all — 'primary' (default) keeps only starred transition "
                        "details (Transition.star) in the composed set; 'all' composes "
                        "every derived detail sheet"),
    paper: str = typer.Option(
        "ledger", help="ledger (11x17) | arch-d (24x36). The paper decides the drawn "
                       "scale: a bigger sheet gives select_scale a bigger viewport, so "
                       "catlin's A-101 goes from 1/16\" = 1'-0\" to 3/16\" = 1'-0\""),
) -> None:
    """Compose the permit-set PDF, plan DXFs, and optional architect handoff (M3).

    The PDF is vector, so ``--paper`` is a statement about the sheet the set is drawn for
    and not about resolution — it plots at whatever the plotter can do. Each paper writes
    its own file (``permit_set.pdf``, ``permit_set_24x36.pdf``) so a set already sent out
    is never silently replaced by one at a different scale.
    """
    from typehaus.checks import evaluate_permit_checklist, load_preferences, run
    from typehaus.checks.run import resolve_profile
    from typehaus.emit.draw import write_permit_set, write_plan_dxfs
    from typehaus.emit.draw.sheet_writer import PAPER_SUFFIX, resolve_paper
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    d = _resolve_house(house)
    try:
        size = resolve_paper(paper)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from None
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
        console.print(
            "[red]permit print blocked: declared checklist has failures or unknowns[/red]")
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
        name = f"permit_set{PAPER_SUFFIX[paper]}.pdf"
        path, _ = write_permit_set(model, out / name, preferences,
                                   profile=jurisdiction, details=details, paper=size)
        console.print(f"wrote {path}")
    if handoff:
        _write_handoff_bundle(d, model, preferences, jurisdiction, size)


def _write_handoff_bundle(house: Path, model, preferences=None, profile=None,
                          paper=None) -> None:
    """Copy only generated/project-owned artifacts into the architect handoff."""
    import shutil

    from typehaus.emit.draw import write_permit_set, write_plan_dxfs
    from typehaus.emit.draw.sheet_writer import LEDGER
    from typehaus.server.model_json import write_model_json

    handoff = house / "out" / "handoff"
    handoff.mkdir(parents=True, exist_ok=True)
    # The bundle carries one set, under one name: whoever opens it wants *the* drawings,
    # not a choice between two papers. It is the paper the command was asked for.
    write_permit_set(model, handoff / "permit_set.pdf", preferences, profile=profile,
                     paper=paper or LEDGER)
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
    _write_handoff_numbers(house, model, handoff)
    console.print(f"wrote {handoff}")


def _write_handoff_numbers(house: Path, model, handoff: Path) -> None:
    """The estimate, as JSON and as CSV, beside the drawings.

    A contractor bundle that carries only drawings makes whoever receives it re-do the
    takeoff — which is the one thing this repo is *certain* about. The CSV is the intake
    artifact (RSMeans Online, Craftsman Cloud and Buildertrend all read CSV/Excel); the
    JSON carries the basis subtotals, the bid ladder and the $/sf the CSV's flat shape
    cannot. Both are skipped silently when the house supplies no ``prices.toml`` — per
    decision #28 dollars are opt-in, and an empty estimate is not worth a file.
    """
    import json

    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.emit.csv_writer import write_csv
    from typehaus.server.space_summary import build_space_summary
    from typehaus.takeoff import bill_of_materials
    from typehaus.takeoff.costs import load_costs
    from typehaus.takeoff.estimate_csv import ESTIMATE_COLUMNS, estimate_rows
    from typehaus.takeoff.product_labels import product_labels

    try:
        prices = load_prices(house)
    except ValueError as exc:
        console.print(f"[yellow]handoff estimate skipped: {exc}[/yellow]")
        return
    if prices is None:
        return
    bom = bill_of_materials(model)
    summary = build_space_summary(model)["overall"]
    estimate = estimate_costs(bom, prices, {"conditioned": summary["conditioned_sf"],
                                            "gross": summary["gross_sf"]},
                              product_labels(model.plan))
    (handoff / "estimate.json").write_text(json.dumps(estimate, indent=2, sort_keys=True))
    write_csv(handoff / "estimate.csv", ESTIMATE_COLUMNS,
              estimate_rows(estimate, load_costs(house)))
