"""`haus diff | compare` — the two "what changed?" commands.

Split out of :mod:`typehaus.cli.app` by command family. ``diff`` answers it across the
boundary (an architect's modified IFC against the deterministic baseline, WP2.10);
``compare`` answers it inside the design (two plan variants, or one plan with an assembly
swapped). Both render the same element-change table, which is why they sit together.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from typehaus.cli._shared import _print_findings, _resolve_house, app, console


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
