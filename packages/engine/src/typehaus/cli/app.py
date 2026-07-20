"""`haus` CLI (Typer) — build | check | ls | explain | fmt (WP1.9, → 02 §CLI)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from typehaus._meta import CLI_NAME, PROJECT_NAME, engine_version
from typehaus.findings import Result, Severity

app = typer.Typer(name=CLI_NAME, help=f"{PROJECT_NAME} — infrastructure as code for houses.",
                  no_args_is_help=True, add_completion=False)
console = Console()


def _resolve_house(house: Optional[Path]) -> Path:
    return (house or Path.cwd()).resolve()


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
        from typehaus.server.model_json import write_model_json

        p = write_model_json(model, out / "model.json", preferences=load_preferences(d))
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
    raise typer.Exit(1 if report.errors else 0)


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
        table = Table("Result", "Requirement", "Detail")
        for item in checklist.items:
            color = {Result.PASS: "green", Result.FAIL: "red", Result.UNKNOWN: "yellow"}[item.result]
            table.add_row(f"[{color}]{item.result.value.upper()}[/{color}]", item.label, item.detail)
        console.print(table)
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


@app.command()
def takeoff(
    house: Optional[Path] = typer.Argument(None),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Report resolved framing counts and radiant-wire lengths (M3)."""
    from collections import Counter
    import json

    from typehaus.resolve import resolve
    from typehaus.source import load_plan
    from typehaus.takeoff import sheet_goods_takeoff

    d = _resolve_house(house)
    loaded = load_plan(d)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    model, findings = resolve(loaded.plan)
    if any(finding.severity is Severity.ERROR for finding in findings):
        _print_findings(findings)
        raise typer.Exit(1)
    framing = Counter(f"{member.category}:{member.profile}" for member in model.all_members())
    radiant = [{"tag": zone.tag, "storey": zone.storey, "system": zone.system,
                "wire_length_ft": round(zone.wire_length_m / 0.3048, 1)}
               for zone in model.floor_heat]
    payload = {"framing": dict(sorted(framing.items())), "floor_heat": radiant,
               "sheet_goods": sheet_goods_takeoff(model)}
    if as_json:
        console.print_json(json.dumps(payload))
        return
    console.print("[bold]Framing members[/bold]")
    for item, count in payload["framing"].items():
        console.print(f"  {item}: {count}")
    if radiant:
        console.print("[bold]Radiant floor heat[/bold]")
        for zone in radiant:
            console.print(f"  {zone['tag']} ({zone['system']}): {zone['wire_length_ft']:.1f} LF")
    if payload["sheet_goods"]:
        console.print("[bold]Sheet goods (4x8 panels)[/bold]")
        for item in payload["sheet_goods"]:
            console.print(f"  {item['scope']}: {item['sheets_4x8']} sheets of "
                          f"{item['thickness_in']}\" {item['material']} "
                          f"({item['net_area_sqft']} sf net)")


@app.command(name="import")
def import_asset(
    kind: str = typer.Argument(..., help="currently: furniture"),
    source: Path = typer.Argument(..., help=".glb | .gltf | .dae mesh to import"),
    house: Optional[Path] = typer.Argument(None, help="House directory (default: cwd)"),
    tag: Optional[str] = typer.Option(None, help="Type tag suffix (for example lounge-chair)"),
    name: Optional[str] = typer.Option(None, help="Display name"),
    room: Optional[str] = typer.Option(None, help="Room tag; requires --at-m"),
    at_m: Optional[str] = typer.Option(None, help="Placement as 'x,y' meters; requires --room"),
    storage: bool = typer.Option(False, help="Count this type toward the storage ratio"),
) -> None:
    """Import a house-local asset; ``haus import furniture`` is the M3 mesh path."""
    if kind != "furniture":
        raise typer.BadParameter("only 'furniture' is supported")
    position = _parse_xy_meters(at_m) if at_m is not None else None
    from typehaus.cli.furniture_import import import_furniture_mesh

    result = import_furniture_mesh(source, _resolve_house(house), tag=tag, name=name,
                                   room=room, position_m=position, storage=storage)
    console.print(f"imported {result['type']['tag']} → {result['mesh']}")
    if result["instance"] is not None:
        console.print(f"placed {result['instance']['tag']} in {result['instance']['room']}")


def _parse_xy_meters(value: str) -> tuple[float, float]:
    try:
        x, y = (float(item.strip()) for item in value.split(","))
    except ValueError as exc:
        raise typer.BadParameter("--at-m must be 'x,y' in meters") from exc
    return x, y


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
def explain(
    target: str = typer.Argument(..., help="element tag | assembly tag | 'transitions'"),
    house: Optional[Path] = typer.Argument(None),
    card: bool = typer.Option(False, help="render the assembly section card"),
    detail: bool = typer.Option(False, help="render the transition detail(s) for a TR-* tag"),
    out: Optional[Path] = typer.Option(None, help="write card SVG to this path"),
    transitions: bool = typer.Option(False, help="enumerate derived boundary conditions"),
    bearing: bool = typer.Option(False, help="show authored bearing walls and resolved stack edges"),
) -> None:
    """Explain an element, render an assembly card, or list transitions."""
    from typehaus.source import load_plan

    d = _resolve_house(house)
    result = load_plan(d)
    if result.plan is None:
        _print_findings(result.findings)
        raise typer.Exit(1)
    plan = result.plan

    if target == "transitions" or transitions:
        from typehaus.resolve import resolve

        model, _ = resolve(plan)
        table = Table("kind", "key", "elements")
        for cond in model.conditions:
            table.add_row(cond.kind.value, cond.key, ", ".join(cond.element_tags))
        console.print(table)
        return

    if bearing:
        from typehaus.resolve import resolve

        model, findings = resolve(plan)
        _print_findings(findings)
        table = Table("storey", "bearing wall", "assembly", "supports / stack relation")
        authored = {element.tag: element for element in plan.all_elements()
                    if element.element_kind in ("Wall", "FoundationWall")}
        for wall in sorted(model.walls, key=lambda item: (item.storey, item.tag)):
            source = authored.get(wall.tag)
            role = getattr(getattr(source, "structural_role", None), "value", "unknown")
            lower = [edge.lower_wall for edge in model.stack_edges if edge.upper_wall == wall.tag]
            upper = [edge.upper_wall for edge in model.stack_edges if edge.lower_wall == wall.tag]
            if role != "bearing" and not lower and not upper:
                continue
            relation = ", ".join([*(f"on {tag}" for tag in lower),
                                  *(f"to {tag}" for tag in upper)]) or "bearing role"
            table.add_row(wall.storey, wall.tag, wall.assembly, relation)
        console.print(table)
        return

    if detail:
        from typehaus.emit.draw.details import build_detail, derive_detail_slices
        from typehaus.emit.draw.pdf_writer import write_raster
        from typehaus.resolve import resolve

        model, _ = resolve(plan)
        details = [d for d in derive_detail_slices(model)
                   if d.transition is not None and d.transition.tag == target]
        if not details:
            console.print(f"[red]no derived detail bound to transition {target!r}[/red]")
            raise typer.Exit(1)
        dest_dir = out or (d / "out" / "render")
        dest_dir.mkdir(parents=True, exist_ok=True)
        for derived in details:
            scene, findings = build_detail(model, derived)
            _print_findings(findings)
            slug = derived.view.tag.replace("/", "_")
            path = write_raster(scene, dest_dir / f"detail_{slug}.png",
                                title=f"detail · {derived.key}")
            console.print(f"wrote {path}")
        return

    asm = plan.library.resolve_assembly(target)
    if asm is not None:
        from typehaus.analysis import assembly_r_value
        from typehaus.checks import load_preferences
        from typehaus.checks.building_science.condensation import analyze_assembly
        from typehaus.emit.draw import render_card_svg

        rv = assembly_r_value(asm, plan.library)
        console.print(f"[bold]{asm.tag}[/bold]  R-value: {rv.fmt()}"
                      + (f"  STC {asm.stc}" if asm.stc else ""))
        for layer in list(asm.default_lining) + list(asm.layers):
            console.print(f"  {layer.function.value:9} {layer.name:12} {layer.thickness.fmt()}")
            if layer.cavity is not None:
                fill = layer.cavity
                thk = fill.thickness if fill.thickness is not None else layer.thickness
                console.print(f"  {'  ↳ cavity':9} {fill.material_ref:12} {thk.fmt()}"
                              f"  (ff {fill.framing_factor:.0%}, in bays — adds no depth)")
        if card or out:
            heating = plan.project.site.design_temp_heating
            condensation = analyze_assembly(
                asm, plan.library,
                heating_design_temp_f=heating.fahrenheit if heating else None,
                preferences=load_preferences(d),
            )
            svg = render_card_svg(asm, plan.library, condensation)
            dest = out or (d / "out" / f"card_{asm.tag}.svg")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(svg)
            console.print(f"wrote {dest}")
        return

    el = plan.by_tag(target)
    if el is None:
        console.print(f"[red]no element, assembly, or 'transitions' named {target!r}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]{el.tag}[/bold] ({el.element_kind}) uid={el.uid}")
    loc = result.provenance.location(el.tag)
    if loc:
        console.print(f"  source: {loc}")
    console.print(f"  {_detail(el)}")


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
    view: str = typer.Option("plan", help="plan | section | details | 3d (#52 agent eyes)"),
    fmt: str = typer.Option("png", help="png | svg"),
) -> None:
    """Emit headless plan/section snapshots for the edit→build→check→look loop (#52)."""
    from typehaus.emit.draw import render_views
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    d = _resolve_house(house)
    result = load_plan(d)
    if result.plan is None:
        _print_findings(result.findings)
        raise typer.Exit(1)
    model, _ = resolve(result.plan)
    paths = render_views(model, d / "out" / "render", view=view, fmt=fmt)
    for p in paths:
        console.print(f"wrote {p}")


@app.command(name="print")
def print_sheets(
    house: Optional[Path] = typer.Argument(None),
    fmt: str = typer.Option("both", help="dxf | pdf | both"),
    handoff: bool = typer.Option(False, help="also write the architect-handoff bundle"),
) -> None:
    """Compose the permit-set PDF, plan DXFs, and optional architect handoff (M3)."""
    from typehaus.checks import evaluate_permit_checklist, load_preferences, run
    from typehaus.emit.draw import write_permit_set, write_plan_dxfs
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    d = _resolve_house(house)
    result = load_plan(d)
    if result.plan is None:
        _print_findings(result.findings)
        raise typer.Exit(1)
    checklist = evaluate_permit_checklist(run(result.plan, d), "mn-2024")
    if not checklist.ok:
        console.print("[red]permit print blocked: declared checklist has failures or unknowns[/red]")
        for item in checklist.items:
            if item.result is not Result.PASS:
                console.print(f"  {item.label}: {item.detail}")
        raise typer.Exit(1)
    model, _ = resolve(result.plan)
    preferences = load_preferences(d)
    out = d / "out"
    if fmt in ("dxf", "both"):
        for path in write_plan_dxfs(model, out / "sheets"):
            console.print(f"wrote {path}")
    if fmt in ("pdf", "both"):
        path, _ = write_permit_set(model, out / "permit_set.pdf", preferences)
        console.print(f"wrote {path}")
    if handoff:
        _write_handoff_bundle(d, model, preferences)


def _write_handoff_bundle(house: Path, model, preferences=None) -> None:
    """Copy only generated/project-owned artifacts into the architect handoff."""
    import shutil

    from typehaus.emit.draw import write_permit_set, write_plan_dxfs
    from typehaus.server.model_json import write_model_json

    handoff = house / "out" / "handoff"
    handoff.mkdir(parents=True, exist_ok=True)
    write_permit_set(model, handoff / "permit_set.pdf", preferences)
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


@app.command()
def serve(
    house: Optional[Path] = typer.Argument(None),
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8765),
) -> None:
    """Run the FastAPI server: model.json, PATCH /plan, undo/redo, live reload (WP2.1)."""
    try:
        import uvicorn
    except ImportError as exc:
        console.print("[red]serve needs uvicorn: pip install 'typehaus[server]'[/red]")
        raise typer.Exit(2) from exc
    from typehaus.server.app import create_app

    d = _resolve_house(house)
    console.print(f"serving {d} on http://{host}:{port}")
    uvicorn.run(create_app(d), host=host, port=port)


@app.command()
def new(
    directory: Path = typer.Argument(..., help="new house directory to scaffold"),
    name: str = typer.Option("My House", help="project display name"),
    template: str = typer.Option("catlin", help="catlin (the real house, #22) | minimal"),
) -> None:
    """Scaffold a new house: brief.md, preferences.toml, plan/ skeleton (WP2.12, #22)."""
    from typehaus.cli.scaffold import scaffold_house

    created = scaffold_house(directory, name, template=template)
    for p in created:
        console.print(f"created {p}")
    console.print(f"[green]new house ready[/green] — try: haus serve {directory}")


def _detail(el: object) -> str:
    for attr in ("assembly", "host", "occupancy", "type_ref"):
        v = getattr(el, attr, None)
        if v is not None:
            return f"{attr}={getattr(v, 'value', v)}"
    return ""


def _print_findings(findings: list) -> None:
    for f in findings:
        color = "red" if f.severity is Severity.ERROR else (
            "yellow" if f.result is Result.FAIL else "dim")
        console.print(f"[{color}]{f.render()}[/{color}]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
