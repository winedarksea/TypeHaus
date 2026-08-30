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
from typehaus.engineering import Freshness
from typehaus.findings import Authority, Result, Severity

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


def _check_json_summary(tally, findings: list) -> dict:
    """`haus check --json-summary` payload: counts by category/severity, not every finding.

    ``--json`` dumps every ``Finding`` in full (~230KB on catlin) — the honest machine
    surface a diff or a report generator needs. Most agent callers only ask "did anything
    fail, and where" — this is that answer, an order of magnitude smaller. The top-level
    ``pass``/``fail``/``unknown`` keys are the same ones ``--json`` and the tests already
    assert on, kept identical here on purpose; ``not_applicable`` and ``engineered`` were
    added beside them rather than replacing anything.

    Category is the ``check_id`` namespace before its first dot (``structural.foo`` ->
    ``structural``) — the same grouping every check module already encodes into its ids.
    """
    from collections import Counter

    # Keyed off Result itself: a bucket dict spelled out by hand here is one member-add
    # away from a KeyError on real house output.
    categories: dict[str, dict[str, int]] = {}
    for finding in findings:
        category = finding.check_id.split(".", 1)[0]
        bucket = categories.setdefault(category, {r.value: 0 for r in Result})
        bucket[finding.result.value] += 1
    failing = sorted({x.check_id for x in findings if x.result is Result.FAIL})
    unknown = sorted({x.check_id for x in findings if x.result is Result.UNKNOWN})
    fail_severity = Counter(x.severity.value for x in findings if x.result is Result.FAIL)
    return {
        "pass": tally.passed, "fail": tally.failed, "unknown": tally.unknown,
        "not_applicable": tally.not_applicable, "engineered": tally.engineered,
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
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    lod: str = typer.Option("framed", help="core | framed"),
    with_schedule: bool = typer.Option(
        False, "--with-schedule",
        help="Also emit IfcWorkSchedule/IfcTask + IfcCostSchedule/IfcCostItem for the "
             "derived work packages. Off by default: the permit IFC stays lean."),
    only: str | None = typer.Option(None, help="ifc | json | card"),
    inspect: bool = typer.Option(False, help="parse-only; never imports params/"),
    timing: bool = typer.Option(
        False, "--timing",
        help="Print where the build spent its time, slowest stage first."),
) -> None:
    """Build outputs from a plan (IFC / model.json)."""
    import time

    from typehaus.source import lint_only, load_plan

    # The loader and the resolver already measure their own stages and hand them back
    # (``LoadResult.timings`` / ``ResolvedModel.timings``); nothing ever read them, so the
    # only way to answer "why is the build slow" was a throwaway script. The emit stages
    # below are the missing half — and are, in practice, the answer.
    stages: dict[str, float] = {}

    d = _resolve_house(house)
    if inspect:
        findings = lint_only(d)
        _print_findings(findings)
        raise typer.Exit(1 if any(f.severity is Severity.ERROR for f in findings) else 0)

    t0 = time.perf_counter()
    result = load_plan(d)
    load_total = (time.perf_counter() - t0) * 1000.0
    _print_findings(result.findings)
    if not result.ok or result.plan is None:
        console.print("[red]build failed[/red]")
        raise typer.Exit(1)
    stages.update({f"load.{name}": ms for name, ms in result.timings.items()})
    # Whatever the loader does not attribute to a named stage (module import machinery,
    # the manifest walk) still belongs to the load — otherwise the table silently loses it.
    stages["load.other"] = load_total - sum(result.timings.values())

    from typehaus.resolve import resolve

    t0 = time.perf_counter()
    model, rfindings = resolve(result.plan)
    stages["resolve"] = (time.perf_counter() - t0) * 1000.0
    _print_findings(rfindings)
    out = d / "out"
    out.mkdir(exist_ok=True)

    # The vocabulary manifest (member/solid colours, solid trades, layer visibility groups,
    # typography constants — emit/vocabulary_manifest.py) is derived from engine source alone,
    # never from this house's model, so it is written unconditionally rather than gated by
    # `only`: it is the regenerable half of the ui/src/generated/vocabulary.json the viewer
    # imports directly, and there is no house-specific reason to skip it.
    from typehaus.emit.vocabulary_manifest import write_vocabulary_manifest

    vocab_path = out / "vocabulary.json"
    t0 = time.perf_counter()
    write_vocabulary_manifest(vocab_path)
    stages["write_vocabulary_manifest"] = (time.perf_counter() - t0) * 1000.0
    console.print(f"wrote {vocab_path}")

    if only in (None, "json"):
        from typehaus.checks import load_preferences
        from typehaus.server.model_json import load_variant_catalog, write_model_json

        t0 = time.perf_counter()
        p = write_model_json(model, out / "model.json", content_hash=result.content_hash,
                             preferences=load_preferences(d), variants=load_variant_catalog(d))
        stages["write_model_json"] = (time.perf_counter() - t0) * 1000.0
        console.print(f"wrote {p}")
    if only in (None, "ifc"):
        try:
            from typehaus.emit.ifc import emit_ifc

            t0 = time.perf_counter()
            p = emit_ifc(model, out / "model.ifc", lod=lod,
                          sequence=with_schedule, house_dir=d)
            stages["emit_ifc"] = (time.perf_counter() - t0) * 1000.0
            extra = " + schedule" if with_schedule else ""
            console.print(f"wrote {p} (lod={lod}{extra})")
        except RuntimeError as exc:
            console.print(f"[yellow]skipped IFC: {exc}[/yellow]")
    if timing:
        # Resolve's own sub-stages are reported as one line: it is ~0.3 s of the build, and
        # unfolding it here would bury the stages that are not.
        table = Table(title="build timing", box=None)
        table.add_column("stage")
        table.add_column("ms", justify="right")
        for name, ms in sorted(stages.items(), key=lambda kv: -kv[1]):
            table.add_row(name, f"{ms:.1f}")
        table.add_row("[bold]total[/bold]", f"[bold]{sum(stages.values()):.1f}[/bold]")
        console.print(table)
    console.print("[green]build ok[/green]")


@app.command()
def check(
    house: Path | None = typer.Argument(None),
    profile: str = typer.Option("mn-2024"),
    tier: TierName | None = typer.Option(None, help="Restrict to one checks tier."),
    as_json: bool = typer.Option(False, "--json"),
    json_summary: bool = typer.Option(
        False, "--json-summary",
        help="Compact JSON: result counts by category, not every finding's "
             "full model_dump() (#52). --json stays the complete machine surface."),
    only: str = typer.Option(_ONLY_DEFAULT, "--only",
                             help=f"Results to print: `{_ONLY_ALL}`, or a comma-separated "
                                  "subset of pass,fail,unknown,not_applicable."),
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
    tally = report.counts()
    if as_json:
        import json

        # --json is the machine surface and stays complete regardless of --only.
        console.print_json(json.dumps({
            "pass": tally.passed, "fail": tally.failed, "unknown": tally.unknown,
            "not_applicable": tally.not_applicable, "engineered": tally.engineered,
            "findings": [x.model_dump(mode="json") for x in report.findings],
        }))
    elif json_summary:
        import json

        console.print_json(json.dumps(_check_json_summary(tally, report.findings)))
    else:
        shown = report.findings if keep is None else [
            x for x in report.findings if x.result in keep]
        _print_findings(shown, plain=plain_out)
        hidden = len(report.findings) - len(shown)
        suffix = f"; {hidden} hidden by --only {only} (--only all shows them)" if hidden else ""
        # #32's wording survives with two clauses inserted, and each prints only when
        # non-zero — a house with neither regresses no pinned line.
        na = f", {tally.not_applicable} not applicable" if tally.not_applicable else ""
        eng = (f"; {tally.engineered} of the results rest on engineered design "
               f"(see haus engineering)" if tally.engineered else "")
        console.print(
            f"\n[bold]{tally.passed} pass, {tally.failed} fail, "
            f"{tally.unknown} not evaluable{na}[/bold] of "
            f"{tally.total} encoded rules{eng}; this profile covers a declared subset of the "
            f"code{suffix}.",
            soft_wrap=True,
        )

    load_errors = any(x.severity is Severity.ERROR for x in result.findings)
    if exit_on is ExitOn.none:
        raise typer.Exit(0)
    gated = bool(report.errors) or load_errors
    if exit_on is ExitOn.fail:
        gated = gated or tally.failed > 0
    raise typer.Exit(1 if gated else 0)


@app.command(name="permit-check")
def permit_check(
    house: Path | None = typer.Argument(None),
    profile: str = typer.Option("mn-2024"),
    as_json: bool = typer.Option(False, "--json"),
    sealed: bool = typer.Option(
        False, "--sealed",
        help="Gate on the FINAL state instead of the draft one: every engineered item must "
             "also carry a professional seal that still matches the model."),
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
            "sealed": checklist.sealed,
            # Built field by field rather than from __dict__: the item now carries two
            # objects (a Freshness and a Signoff) that json.dumps cannot encode, and a
            # dataclass whose new field silently breaks the machine surface is worse than
            # a few lines of spelling it out.
            "items": [{
                "label": item.label,
                "result": item.result.value,
                "detail": item.detail,
                "check_ids": list(item.check_ids),
                "blocking": item.blocking,
                "authority": item.authority.value,
                "engineering_items": list(item.engineering_items),
                "seal": item.seal.value if item.seal else None,
                "signoff": item.signoff.id if item.signoff else None,
            } for item in checklist.items],
        }))
    else:
        colors = {Result.PASS: "green", Result.FAIL: "red", Result.UNKNOWN: "yellow",
                  Result.NOT_APPLICABLE: "dim"}

        seal_colors = {Freshness.FRESH: "green", Freshness.STALE: "red",
                       Freshness.UNPINNED: "yellow", Freshness.UNSEALED: "yellow"}

        def _render(rows, title: str, *, seals: bool = False) -> None:
            columns = ["Result", "Requirement", "Detail"] + (["Seal"] if seals else [])
            table = Table(*columns, title=title)
            for item in rows:
                color = colors[item.result]
                cells = [f"[{color}]{item.result.value.upper()}[/{color}]",
                         item.label, item.detail]
                if seals:
                    tone = seal_colors.get(item.seal, "dim")
                    label = item.seal.value if item.seal else "—"
                    cells.append(f"[{tone}]{label}[/{tone}]")
                table.add_row(*cells)
            console.print(table)

        gating = [item for item in checklist.items if item.blocking]
        _render(gating, "Permit gate", seals=any(item.seal for item in gating))
        # The third section. An engineered requirement is not "under review" — it is done
        # or it is not, by a person this engine cannot stand in for — and mixing it into
        # the staging lane loses exactly the distinction this section exists to draw.
        if checklist.engineered:
            _render(checklist.engineered,
                    "Engineered — requires a professional seal", seals=True)
        # Encoded, running, and deliberately not yet gating — see PermitItemSpec.blocking.
        # Printed separately rather than hidden: a rule this house cannot answer yet is a
        # real coverage statement, and burying it would repeat the drift the profile
        # mechanism exists to stop.
        review = [item for item in checklist.under_review
                  if item.authority is not Authority.ENGINEERED]
        if review:
            _render(review, "Under review — encoded, not gating")
        console.print(
            "Declared MN subset only; local amendments, engineering, MEP, and energy "
            "review remain external."
        )
    if sealed and not checklist.sealed:
        console.print(
            f"[red]--sealed: {len(checklist.unsealed)} engineered item(s) carry no fresh "
            f"professional seal: "
            f"{', '.join(item.label for item in checklist.unsealed)}[/red]")
        raise typer.Exit(1)
    raise typer.Exit(0 if checklist.ok else 1)


@app.command()
def energy(
    house: Path | None = typer.Argument(None),
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
        console.print("[yellow]Not included / unknown: "
                      + ", ".join(report.unknown_inputs) + "[/yellow]")
