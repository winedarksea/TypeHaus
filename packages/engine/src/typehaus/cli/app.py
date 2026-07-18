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
        from typehaus.server.model_json import write_model_json

        p = write_model_json(model, out / "model.json")
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
    tier: Optional[str] = typer.Option(None, help="integrity|code|advisory|structural"),
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
    out: Optional[Path] = typer.Option(None, help="write card SVG to this path"),
    transitions: bool = typer.Option(False, help="enumerate derived boundary conditions"),
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

    asm = plan.library.resolve_assembly(target)
    if asm is not None:
        from typehaus.analysis import assembly_r_value
        from typehaus.emit.draw import render_card_svg

        rv = assembly_r_value(asm, plan.library)
        console.print(f"[bold]{asm.tag}[/bold]  R-value: {rv.fmt()}"
                      + (f"  STC {asm.stc}" if asm.stc else ""))
        for layer in list(asm.default_lining) + list(asm.layers):
            console.print(f"  {layer.function.value:9} {layer.name:12} {layer.thickness.fmt()}")
        if card or out:
            svg = render_card_svg(asm, plan.library)
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
    """Normalize editable plan files and assign missing uids (basic M1 stub)."""
    from typehaus.source import editable_files, missing_uid_findings

    d = _resolve_house(house)
    total = 0
    for f in editable_files(d):
        rel = f.relative_to(d).as_posix()
        missing = missing_uid_findings(rel, f.read_text())
        total += len(missing)
    console.print(f"{total} element(s) missing uid (full fmt writeback lands in M2 WP2.2)")


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
