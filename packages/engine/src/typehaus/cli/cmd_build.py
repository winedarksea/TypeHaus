"""`haus version | build | check | permit-check | energy` — the loop that turns plan source
into outputs and grades it.

Split out of :mod:`typehaus.cli.app` by command family. These five share the same spine:
load the plan, print its findings, exit non-zero when it did not hold up — which is why the
same `_print_findings`/`typer.Exit(1)` shape repeats here rather than being scattered.

Registration is a side effect of importing this module; :mod:`typehaus.cli.app` imports it in
the original order so ``haus --help`` lists commands exactly as it always has. Command bodies
keep their imports inside the function: `haus --version` must not pay for the resolver.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from typehaus._meta import PROJECT_NAME, engine_version
from typehaus.cli._shared import _print_findings, _resolve_house, app, console
from typehaus.findings import Result, Severity


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

        p = write_model_json(model, out / "model.json", content_hash=result.content_hash,
                             preferences=load_preferences(d), variants=load_variant_catalog(d))
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
