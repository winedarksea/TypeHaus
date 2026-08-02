"""`haus` CLI (Typer) — the entry point module.

The command surface is split across ``cli/_shared.py`` (the app, console, and shared
helpers) and per-topic ``cmd_*`` modules that register onto it. This module keeps the
smaller commands, wires the sub-apps, and re-exports ``app``/``main`` — the packaging entry
point and every existing import path (``from typehaus.cli.app import app``) are unchanged.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from typehaus._meta import PROJECT_NAME, engine_version
from typehaus.cli._shared import _detail, _print_findings, _resolve_house, app, console
from typehaus.cli.variants import variants_app
from typehaus.findings import Result, Severity

app.add_typer(variants_app, name="variants")

# Importing these registers their commands on the shared ``app``. They are deliberately
# imported at module scope (the CLI must know its full command list to render --help) but
# each command body still imports the engine lazily.
from typehaus.cli import cmd_explain, cmd_takeoff  # noqa: E402,F401  (registration side effect)


@app.command()
def version() -> None:
    """Print the engine version."""
    console.print(f"{PROJECT_NAME} engine {engine_version()}")


@app.command()
def build(
    house: Optional[Path] = typer.Argument(None, help="House directory (default: cwd)"),
    lod: str = typer.Option("framed", help="core | framed"),
    only: Optional[str] = typer.Option(None, help="ifc | json | card"),
    inspect: bool = typer.Option(False, help="parse-only; never imports params/"),
) -> None:
    """Build outputs from a plan (IFC / model.json)."""
    from typehaus.source import lint_only, load_plan

    d = _resolve_house(house)
    if inspect:
        findings = lint_only(d)
        _print_findings(findings)
        raise typer.Exit(1 if any(f.severity is Severity.ERROR for f in findings) else 0)

    result = load_plan(d)
    _print_findings(result.findings)
    if not result.ok or result.plan is None:
        console.print("[red]build failed[/red]")
        raise typer.Exit(1)

    from typehaus.resolve import resolve

    model, rfindings = resolve(result.plan)
    _print_findings(rfindings)
    out = d / "out"
    out.mkdir(exist_ok=True)

    if only in (None, "json"):
        from typehaus.checks import load_preferences
        from typehaus.server.model_json import load_variant_catalog, write_model_json

        p = write_model_json(model, out / "model.json", preferences=load_preferences(d),
                             variants=load_variant_catalog(d))
        console.print(f"wrote {p}")
    if only in (None, "ifc"):
        try:
            from typehaus.emit.ifc import emit_ifc

            p = emit_ifc(model, out / "model.ifc", lod=lod)
            console.print(f"wrote {p} (lod={lod})")
        except RuntimeError as exc:
            console.print(f"[yellow]skipped IFC: {exc}[/yellow]")
    console.print("[green]build ok[/green]")


@app.command()
def check(
    house: Optional[Path] = typer.Argument(None),
    profile: str = typer.Option("mn-2024"),
    tier: Optional[str] = typer.Option(None, help="integrity|code|advisory|structural|building_science"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Run the checks registry (same registry pytest runs)."""
    from typehaus.checks import Tier, run
    from typehaus.source import load_plan

    d = _resolve_house(house)
    result = load_plan(d)
    if result.plan is None:
        _print_findings(result.findings)
        raise typer.Exit(1)
    # Loader findings appended *after* a successful import (e.g. a movable element authored
    # in a non-editable file) are still real errors — print them, don't only print on
    # import failure.
    if result.findings:
        _print_findings(result.findings)
    tier_enum = Tier(tier) if tier else None
    report = run(result.plan, d, profile=profile, tier=tier_enum)
    p, f, u = report.counts()
    if as_json:
        import json

        console.print_json(json.dumps({
            "pass": p, "fail": f, "unknown": u,
            "findings": [x.model_dump(mode="json") for x in report.findings],
        }))
    else:
        _print_findings(report.findings)
        console.print(
            f"\n[bold]{p} pass, {f} fail, {u} not evaluable[/bold] of "
            f"{p + f + u} encoded rules; this profile covers a declared subset of the code."
        )
    from typehaus.findings import Severity

    load_errors = any(x.severity is Severity.ERROR for x in result.findings)
    raise typer.Exit(1 if (report.errors or load_errors) else 0)


@app.command(name="permit-check")
def permit_check(
    house: Optional[Path] = typer.Argument(None),
    profile: str = typer.Option("mn-2024"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Gate the declared M3 permit subset; unknowns and failures stop printing."""
    import json

    from typehaus.checks import evaluate_permit_checklist, run
    from typehaus.source import load_plan

    d = _resolve_house(house)
    loaded = load_plan(d)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    report = run(loaded.plan, d, profile=profile)
    checklist = evaluate_permit_checklist(report, profile)
    if as_json:
        console.print_json(json.dumps({
            "profile": checklist.profile_name,
            "ok": checklist.ok,
            "items": [item.__dict__ | {"result": item.result.value}
                      for item in checklist.items],
        }))
    else:
        colors = {Result.PASS: "green", Result.FAIL: "red", Result.UNKNOWN: "yellow"}

        def _render(rows, title: str) -> None:
            table = Table("Result", "Requirement", "Detail", title=title)
            for item in rows:
                color = colors[item.result]
                table.add_row(f"[{color}]{item.result.value.upper()}[/{color}]",
                              item.label, item.detail)
            console.print(table)

        gating = [item for item in checklist.items if item.blocking]
        _render(gating, "Permit gate")
        # Encoded, running, and deliberately not yet gating — see PermitItemSpec.blocking.
        # Printed separately rather than hidden: a rule this house cannot answer yet is a
        # real coverage statement, and burying it would repeat the drift the profile
        # mechanism exists to stop.
        if checklist.under_review:
            _render(checklist.under_review, "Under review — encoded, not gating")
        console.print(
            "Declared MN subset only; local amendments, engineering, MEP, and energy review remain external."
        )
    raise typer.Exit(0 if checklist.ok else 1)


@app.command()
def energy(
    house: Optional[Path] = typer.Argument(None),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Estimate a transparent design-day block heating/cooling load (Manual J lite)."""
    from typehaus.checks import build_context
    from typehaus.energy import estimate_block_load
    from typehaus.source import load_plan

    d = _resolve_house(house)
    result = load_plan(d)
    if result.plan is None:
        _print_findings(result.findings)
        raise typer.Exit(1)
    ctx, _ = build_context(result.plan, d)
    report = estimate_block_load(ctx.model, ctx.preferences)
    if as_json:
        import json

        console.print_json(json.dumps(report.as_dict()))
        return
    console.print(f"[bold]Heating:[/bold] {report.heating_load_btu_per_hour:,.0f} BTU/h")
    console.print(f"[bold]Cooling:[/bold] {report.cooling_load_btu_per_hour:,.0f} BTU/h "
                  f"({report.cooling_tons:.2f} tons)")
    for component in report.components:
        console.print(f"  {component.kind:8} {component.area_ft2:,.0f} sf  "
                      f"UA {component.ua_btu_per_hour_f:,.1f}")
    if report.unknown_inputs:
        console.print("[yellow]Not included / unknown: " + ", ".join(report.unknown_inputs) + "[/yellow]")



@app.command(name="import")
def import_asset(
    kind: str = typer.Argument(..., help="furniture | plumbing | appliance | mechanical | register | electrical"),
    source: Path = typer.Argument(..., help=".glb | .gltf | .dae | .svg | .ifc asset to import"),
    house: Optional[Path] = typer.Argument(None, help="House directory (default: cwd)"),
    tag: Optional[str] = typer.Option(None, help="Type tag suffix (for example lounge-chair)"),
    name: Optional[str] = typer.Option(None, help="Display name"),
    analyze: bool = typer.Option(False, help="Analyze only; do not mutate the project"),
    confirm: bool = typer.Option(False, help="Commit a confirmed project-local catalog type"),
    units: str = typer.Option("m", help="Confirmed source units: m | mm | ft"),
    up_axis: str = typer.Option("y", help="Confirmed up axis: y | z"),
    origin: str = typer.Option("floor_center", help="Confirmed origin: floor_center"),
    ifc_occurrence: Optional[str] = typer.Option(None, help="Analyzed IFC occurrence ID or GlobalId to extract"),
) -> None:
    """Analyze, then explicitly commit a house-local placeable visual asset."""
    from typehaus.source.placeable_import import (ImportConfirmation, analyze_placeable_asset,
                                                  commit_placeable_asset)
    house_dir = _resolve_house(house)
    asset_analysis = analyze_placeable_asset(source)
    if analyze:
        console.print({"format": asset_analysis.format, "content_hash": asset_analysis.content_hash,
                       "total_bytes": asset_analysis.total_bytes,
                       "dependencies": [str(path) for path in asset_analysis.dependencies],
                       "ifc_candidates": [{"id": item.occurrence_id, "global_id": item.global_id,
                                           "class": item.ifc_class, "name": item.name,
                                           "type_global_id": item.type_global_id, "bounds_m": item.bounds_m,
                                           "footprint_m": item.footprint_m,
                                           "orientation_degrees": item.orientation_degrees,
                                           "materials": item.materials, "properties": item.properties,
                                           "ports": item.ports}
                                          for item in asset_analysis.ifc_candidates]})
        return
    if not confirm:
        raise typer.BadParameter("review analysis first, then rerun with --confirm and normalization decisions")
    if tag is None or name is None:
        raise typer.BadParameter("--tag and --name are required for confirmed catalog imports")
    record = commit_placeable_asset(asset_analysis, house_dir, domain=kind, tag=tag, name=name,
                                    confirmation=ImportConfirmation(units=units, up_axis=up_axis, origin=origin),
                                    ifc_occurrence=ifc_occurrence)
    console.print(f"imported {record['tag']} into assets/placeables.json")


@app.command()
def export(
    house: Optional[Path] = typer.Argument(None, help="House directory (default: cwd)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Archive path (default: <house>.haus.zip)"),
) -> None:
    """Bundle a house + its external reference assets into a portable .zip for another machine."""
    from typehaus.source.bundle import export_house

    d = _resolve_house(house)
    try:
        result = export_house(d, output)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"wrote {result.archive} ({result.file_count} source file(s))")
    for original, bundled in result.relinked_underlays:
        console.print(f"  bundled underlay {original} -> {bundled}")
    for missing in result.missing_underlays:
        console.print(f"[yellow]  underlay source missing, not bundled: {missing}[/yellow]")
    console.print("[green]export ok[/green]")


@app.command(name="import-project")
def import_project(
    archive: Path = typer.Argument(..., help="house .zip produced by `haus export`"),
    dest: Path = typer.Argument(..., help="destination directory for the imported house"),
    force: bool = typer.Option(False, help="overwrite a non-empty destination"),
) -> None:
    """Unpack a portable house bundle and verify its relinked asset references."""
    from typehaus.source.bundle import import_house

    try:
        result = import_house(archive, dest, force=force)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"imported {result.name} into {result.house_dir}")
    for missing in result.missing_underlays:
        console.print(f"[yellow]  missing underlay: {missing}[/yellow]")
    for missing in result.missing_assets:
        console.print(f"[yellow]  missing asset: {missing}[/yellow]")
    if result.ok:
        console.print(f"[green]import ok[/green] — try: haus build {result.house_dir}")
    else:
        console.print("[red]import completed with missing references[/red]")
        raise typer.Exit(1)


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
    view: str = typer.Option("plan", help="plan | site | section | details | 3d (#52 agent eyes)"),
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


@app.command()
def diff(
    external: Path = typer.Argument(..., help="architect-modified IFC to compare"),
    house: Optional[Path] = typer.Argument(None),
) -> None:
    """Semantic diff of an external IFC against the deterministic baseline (WP2.10)."""
    from typehaus.diff import build_report
    from typehaus.diff.ifc_adapter import baseline_elems, external_elems
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    d = _resolve_house(house)
    result = load_plan(d)
    if result.plan is None:
        _print_findings(result.findings)
        raise typer.Exit(1)
    model, _ = resolve(result.plan)
    try:
        ext = external_elems(external)
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc
    report = build_report(baseline_elems(model), ext)
    table = Table("change", "tag", "class", "delta")
    for c in report.substantive():
        was = f" (was {c.was_tag})" if c.was_tag else ""
        table.add_row(c.kind.value, c.tag + was, c.ifc_class, c.delta)
    console.print(table)
    p = report.write(d / "out" / "diff.json")
    console.print(f"wrote {p} — {report.counts()}")


# --- V6: serve subcommand (cross-machine app delivery) — keep edits localized for V8 merge ---
def _find_ui_dist(explicit: Optional[Path]) -> Optional[Path]:
    """Locate a built UI (a directory holding ``index.html``) so one ``haus serve`` command can
    deliver the browser app on another machine (V6). An explicit ``--ui-dir`` is authoritative —
    it is used as-is (returns None if it lacks index.html, so the caller errors) and never falls
    back to discovery. Otherwise the ``TYPEHAUS_UI_DIST`` env var wins, then a walk up from the
    cwd and this package looks for a repo-root ``ui/dist``. Returns None when nothing is found."""
    import os

    def _valid(path: Path) -> Optional[Path]:
        return path.resolve() if (path / "index.html").is_file() else None

    if explicit is not None:
        return _valid(Path(explicit))
    env = os.environ.get("TYPEHAUS_UI_DIST")
    if env:
        return _valid(Path(env))
    for anchor in (Path.cwd(), Path(__file__).resolve()):
        node = anchor
        for _ in range(8):
            found = _valid(node / "ui" / "dist")
            if found is not None:
                return found
            if node.parent == node:
                break
            node = node.parent
    return None


@app.command()
def compare(
    variant_a: Path = typer.Argument(..., help="House A directory (baseline variant)"),
    variant_b: Optional[Path] = typer.Argument(
        None, help="House B directory; omit to compare variant A against itself with --swap"),
    swap: list[str] = typer.Option(
        [], "--swap", "-s",
        help="Assembly swap OLD=NEW applied to variant B's walls (repeatable)"),
    label_a: Optional[str] = typer.Option(None, help="Display label for variant A"),
    label_b: Optional[str] = typer.Option(None, help="Display label for variant B"),
    as_json: bool = typer.Option(False, "--json"),
    sheet: bool = typer.Option(False, help="also render a compare sheet PNG"),
) -> None:
    """Compare two variants of the same design: semantic element diff + quantity deltas.

    Two ways to pick the pair (vibe-code-friendly):
      haus compare houseA houseB                  — two named plan variants
      haus compare house --swap OLD=NEW            — same plan, one assembly selection swapped
    """
    from typehaus.diff.compare import VariantSelection, compare_variants

    swaps: dict[str, str] = {}
    for item in swap:
        if "=" not in item:
            raise typer.BadParameter(f"--swap expects OLD=NEW, got {item!r}")
        old, new = item.split("=", 1)
        swaps[old.strip()] = new.strip()
    if variant_b is None and not swaps:
        raise typer.BadParameter("provide a second house directory or at least one --swap")

    base_dir = _resolve_house(variant_a)
    selection_a = VariantSelection(house=base_dir, label=label_a)
    selection_b = VariantSelection(
        house=_resolve_house(variant_b) if variant_b is not None else base_dir,
        swaps=swaps, label=label_b)
    try:
        report = compare_variants(selection_a, selection_b)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    if as_json:
        import json

        console.print_json(json.dumps(report.as_dict()))
    else:
        console.print(f"[bold]A[/bold] {report.label_a}   [bold]B[/bold] {report.label_b}")
        table = Table("change", "tag", "class", "delta")
        for c in report.diff.substantive():
            was = f" (was {c.was_tag})" if c.was_tag else ""
            table.add_row(c.kind.value, c.tag + was, c.ifc_class, c.delta)
        console.print(table)
        if report.quantity_deltas:
            qty = Table("size", "metric", "A", "B", "Δ")
            for q in report.quantity_deltas:
                qty.add_row(q.profile, q.metric, f"{q.baseline:,.1f}",
                            f"{q.variant:,.1f}", f"{q.delta:+,.1f}")
            console.print(qty)
        else:
            console.print("[dim]no framing quantity change[/dim]")
        console.print(f"element changes: {report.diff.counts()}")

    out = base_dir / "out"
    p = report.write(out / "compare.json")
    console.print(f"wrote {p}")
    if sheet:
        from typehaus.emit.draw.sheets import write_compare_sheet

        sheet_path = write_compare_sheet(report, out / "render" / "compare.png")
        console.print(f"wrote {sheet_path}")


@app.command()
def serve(
    house: Optional[Path] = typer.Argument(None),
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8765),
    ui: Optional[bool] = typer.Option(
        None, "--ui/--no-ui",
        help="Serve the compiled UI at / (default: on when a built ui/dist is found)."),
    ui_dir: Optional[Path] = typer.Option(
        None, "--ui-dir", help="Explicit built-UI directory (overrides auto-discovery)."),
) -> None:
    """Run the FastAPI server: model.json, PATCH /plan, undo/redo, live reload (WP2.1).

    Also serves the compiled browser app at ``/`` when a built ``ui/dist`` is present, so a
    user on another computer runs this one command and opens the house in a browser (V6)."""
    try:
        import uvicorn
    except ImportError as exc:
        console.print("[red]serve needs uvicorn: pip install 'typehaus[server]'[/red]")
        raise typer.Exit(2) from exc
    from typehaus.server.app import create_app

    d = _resolve_house(house)

    ui_dist: Optional[Path] = None
    if ui is not False:  # None (auto) or True → try to find a built UI
        ui_dist = _find_ui_dist(ui_dir)
        if ui_dist is None:
            if ui is True or ui_dir is not None:
                console.print(
                    "[red]--ui requested but no built UI found[/red] — run `npm run build` "
                    "in ui/ (or pass --ui-dir <dir>)")
                raise typer.Exit(2)
            console.print(
                "[yellow]no built UI found — serving API only.[/yellow] "
                "Run `npm run build` in ui/ to serve the app at /.")

    console.print(f"serving {d} on http://{host}:{port}")
    if ui_dist is not None:
        console.print(f"  app UI from {ui_dist} → open http://{host}:{port}/")
    uvicorn.run(create_app(d, ui_dist), host=host, port=port)


@app.command()
def new(
    directory: Path = typer.Argument(..., help="new house directory to scaffold"),
    name: str = typer.Option("My House", help="project display name"),
    template: str = typer.Option("starter", help="starter (small, buildable) | catlin (the real house, #22)"),
) -> None:
    """Scaffold a new house: brief.md, preferences.toml, plan/ skeleton (WP2.12, #22)."""
    from typehaus.cli.scaffold import scaffold_house

    created = scaffold_house(directory, name, template=template)
    for p in created:
        console.print(f"created {p}")
    console.print(f"[green]new house ready[/green] — try: haus serve {directory}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
