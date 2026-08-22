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
from typehaus.cli._shared import (
    ExitOn,
    TierName,
    _print_findings,
    _resolve_house,
    app,
    console,
)
from typehaus.findings import Result, Severity

# `--only` accepts these result names, or `all`. Default is failures + unevaluable rules:
# on catlin that is 1451 lines of output down to ~30, and the 716 passing checks it drops
# were never the reason anyone ran the command.
_ONLY_ALL = "all"
_ONLY_DEFAULT = "fail,unknown"


def _parse_only(only: str) -> frozenset[Result] | None:
    """None means "no filter"; otherwise the set of results to print."""
    wanted = [piece.strip().lower() for piece in only.split(",") if piece.strip()]
    if _ONLY_ALL in wanted:
        return None
    try:
        return frozenset(Result(name) for name in wanted)
    except ValueError:
        valid = ", ".join(r.value for r in Result)
        console.print(f"[red]--only: expected `{_ONLY_ALL}` or a comma-separated subset "
                      f"of {{{valid}}}, got {only!r}[/red]")
        raise typer.Exit(2) from None


def _check_json_summary(p: int, f: int, u: int, findings: list) -> dict:
    """`haus check --json-summary` payload: counts by category/severity, not every finding.

    ``--json`` dumps every ``Finding`` in full (~230KB on catlin) — the honest machine
    surface a diff or a report generator needs. Most agent callers only ask "did anything
    fail, and where" — this is that answer, an order of magnitude smaller. The top-level
    ``pass``/``fail``/``unknown`` keys are the same ones ``--json`` and the tests already
    assert on, kept identical here on purpose.

    Category is the ``check_id`` namespace before its first dot (``structural.foo`` ->
    ``structural``) — the same grouping every check module already encodes into its ids.
    """
    from collections import Counter

    categories: dict[str, dict[str, int]] = {}
    for finding in findings:
        category = finding.check_id.split(".", 1)[0]
        bucket = categories.setdefault(category, {"pass": 0, "fail": 0, "unknown": 0})
        bucket[finding.result.value] += 1
    failing = sorted({x.check_id for x in findings if x.result is Result.FAIL})
    unknown = sorted({x.check_id for x in findings if x.result is Result.UNKNOWN})
    fail_severity = Counter(x.severity.value for x in findings if x.result is Result.FAIL)
    return {
        "pass": p, "fail": f, "unknown": u,
        "categories": dict(sorted(categories.items())),
        "fail_severity": dict(sorted(fail_severity.items())),
        "failing_check_ids": failing,
        "unknown_check_ids": unknown,
    }


@app.command()
def version() -> None:
    """Print the engine version."""
    console.print(f"{PROJECT_NAME} engine {engine_version()}")


@app.command()
def build(
    house: Optional[Path] = typer.Argument(None, help="House directory (default: cwd)"),
    lod: str = typer.Option("framed", help="core | framed"),
    with_schedule: bool = typer.Option(
        False, "--with-schedule",
        help="Also emit IfcWorkSchedule/IfcTask + IfcCostSchedule/IfcCostItem for the "
             "derived work packages. Off by default: the permit IFC stays lean."),
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

            p = emit_ifc(model, out / "model.ifc", lod=lod,
                          sequence=with_schedule, house_dir=d)
            extra = " + schedule" if with_schedule else ""
            console.print(f"wrote {p} (lod={lod}{extra})")
        except RuntimeError as exc:
            console.print(f"[yellow]skipped IFC: {exc}[/yellow]")
    console.print("[green]build ok[/green]")


@app.command()
def check(
    house: Optional[Path] = typer.Argument(None),
    profile: str = typer.Option("mn-2024"),
    tier: Optional[TierName] = typer.Option(None, help="Restrict to one checks tier."),
    as_json: bool = typer.Option(False, "--json"),
    json_summary: bool = typer.Option(
        False, "--json-summary",
        help="Compact JSON: pass/fail/unknown counts by category, not every finding's "
             "full model_dump() (#52). --json stays the complete machine surface."),
    only: str = typer.Option(_ONLY_DEFAULT, "--only",
                             help=f"Results to print: `{_ONLY_ALL}`, or a comma-separated "
                                  "subset of pass,fail,unknown."),
    exit_on: ExitOn = typer.Option(ExitOn.fail, "--exit-on",
                                   help="What makes the command exit 1."),
    plain: bool = typer.Option(False, "--plain",
                               help="One unwrapped, uncoloured line per finding "
                                    "(implied by NO_COLOR or a piped stdout)."),
) -> None:
    """Run the checks registry (same registry pytest runs)."""
    from typehaus.checks import Tier, run
    from typehaus.source import load_plan

    plain_out = True if plain else None
    keep = _parse_only(only)
    d = _resolve_house(house)
    result = load_plan(d)
    if result.plan is None:
        _print_findings(result.findings, plain=plain_out)
        raise typer.Exit(1)
    # Loader findings appended *after* a successful import (e.g. a movable element authored
    # in a non-editable file) are still real errors — print them, don't only print on
    # import failure. They are never filtered: a load error the user asked not to see is
    # still the reason everything downstream is wrong.
    if result.findings:
        _print_findings(result.findings, plain=plain_out)
    tier_enum = Tier(tier.value) if tier else None
    report = run(result.plan, d, profile=profile, tier=tier_enum)
    p, f, u = report.counts()
    if as_json:
        import json

        # --json is the machine surface and stays complete regardless of --only.
        console.print_json(json.dumps({
            "pass": p, "fail": f, "unknown": u,
            "findings": [x.model_dump(mode="json") for x in report.findings],
        }))
    elif json_summary:
        import json

        console.print_json(json.dumps(_check_json_summary(p, f, u, report.findings)))
    else:
        shown = report.findings if keep is None else [
            x for x in report.findings if x.result in keep]
        _print_findings(shown, plain=plain_out)
        hidden = len(report.findings) - len(shown)
        suffix = f"; {hidden} hidden by --only {only} (--only all shows them)" if hidden else ""
        console.print(
            f"\n[bold]{p} pass, {f} fail, {u} not evaluable[/bold] of "
            f"{p + f + u} encoded rules; this profile covers a declared subset of the "
            f"code{suffix}.",
            soft_wrap=True,
        )

    load_errors = any(x.severity is Severity.ERROR for x in result.findings)
    if exit_on is ExitOn.none:
        raise typer.Exit(0)
    gated = bool(report.errors) or load_errors
    if exit_on is ExitOn.fail:
        gated = gated or f > 0
    raise typer.Exit(1 if gated else 0)


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
