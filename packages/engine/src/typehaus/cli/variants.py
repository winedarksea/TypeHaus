"""``haus variants`` — declared house variants and the compare surfaces (WP2.14, → 21b).

Three questions, three subcommands:

* ``haus variants list`` — what variants does this house declare, and what do they change?
* ``haus variants compare A B`` — build both and show what choosing B over A does: element
  changes, framing quantities, envelope R-value/thickness, and every check whose result moved.
* ``haus variants assemblies EXT_A EXT_B [EXT_C]`` — the assembly delta compare (#53): two or
  three assemblies side by side with an R / thickness / layers / STC delta row, without
  building anything.

Structured output lands in ``out/variants.json`` and ``out/compare.json`` next to the rest of
the build artifacts, so the UI and an agent read the same numbers the table shows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

variants_app = typer.Typer(name="variants", no_args_is_help=True,
                           help="Declared house variants: list, compare, assembly deltas.")
console = Console()

_UNKNOWN = "UNKNOWN"


def _house(house: Optional[Path]) -> Path:
    return (house or Path.cwd()).resolve()


def _declared(house: Path):
    from typehaus.diff.variants import load_variants

    specs = load_variants(house)
    if not specs:
        console.print(f"[yellow]{house} declares no variants "
                      f"(add a variants.toml — see houses/starter)[/yellow]")
        raise typer.Exit(1)
    return specs


def _number(value: Optional[float], digits: int = 2) -> str:
    return _UNKNOWN if value is None else f"{value:,.{digits}f}"


@variants_app.command("list")
def list_variants(
    house: Optional[Path] = typer.Argument(None, help="House directory (default: cwd)"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """List the variants this house declares and the overrides each one carries."""
    directory = _house(house)
    specs = _declared(directory)
    payload = [spec.as_dict() for spec in specs]
    if as_json:
        console.print_json(json.dumps(payload))
    else:
        table = Table("variant", "overrides", "description")
        for spec in specs:
            overrides = [f"{old} → {new}" for old, new in sorted(spec.assembly_swaps.items())]
            overrides += [item.label() for item in spec.layer_thickness]
            table.add_row(spec.name, "\n".join(overrides) or "—", spec.description)
        console.print(table)
    out = directory / "out"
    out.mkdir(exist_ok=True)
    path = out / "variants.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    console.print(f"wrote {path}")


@variants_app.command("compare")
def compare_variants_command(
    variant_a: str = typer.Argument(..., help="Baseline variant name"),
    variant_b: str = typer.Argument(..., help="Variant to weigh against it"),
    house: Optional[Path] = typer.Option(None, help="House directory (default: cwd)"),
    as_json: bool = typer.Option(False, "--json"),
    checks: bool = typer.Option(True, "--checks/--no-checks",
                                help="Run each variant's checks and diff the results"),
) -> None:
    """Build two declared variants and report every delta between them.

    If the house supplies a ``prices.toml`` (user-authored — see
    :mod:`typehaus.cli.prices` for the format; none is ever shipped), the framing-takeoff
    table gains an estimated Δ $ column, honest about ranges and unpriced sizes.
    """
    from typehaus.cli.prices import load_prices
    from typehaus.diff.compare import compare_variants
    from typehaus.diff.variants import find_variant

    directory = _house(house)
    specs = _declared(directory)
    try:
        prices = load_prices(directory)
        selection_a = find_variant(specs, variant_a).selection(directory)
        selection_b = find_variant(specs, variant_b).selection(directory)
        report = compare_variants(selection_a, selection_b, include_checks=checks)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    if as_json:
        console.print_json(json.dumps(report.as_dict()))
    else:
        _print_compare_tables(report, prices)
    path = report.write(directory / "out" / "compare.json")
    console.print(f"wrote {path}")


def _print_compare_tables(report, prices=None) -> None:
    console.print(f"[bold]A[/bold] {report.label_a}   [bold]B[/bold] {report.label_b}")
    elements = Table("change", "tag", "class", "delta", title="elements")
    for change in report.diff.substantive():
        was = f" (was {change.was_tag})" if change.was_tag else ""
        elements.add_row(change.kind.value, change.tag + was, change.ifc_class, change.delta)
    console.print(elements)

    if report.quantity_deltas:
        columns = ["size", "metric", "A", "B", "Δ"] + (["Δ $ (est)"] if prices else [])
        quantities = Table(*columns, title="framing takeoff")
        total_cost = None
        for item in report.quantity_deltas:
            row = [item.profile, item.metric, f"{item.baseline:,.1f}",
                   f"{item.variant:,.1f}", f"{item.delta:+,.1f}"]
            if prices:
                # $ rides on the ordered lineal feet — the metric a lumber quote is against.
                price = (prices.framing.get(item.profile)
                         if item.metric == "order_length_ft" else None)
                if price is None:
                    row.append("—")
                else:
                    cost = price.times(item.delta)
                    row.append(cost.fmt(signed=True))
                    total_cost = cost if total_cost is None else total_cost.plus(cost)
            quantities.add_row(*row)
        console.print(quantities)
        if prices and total_cost is not None:
            console.print(f"  [bold]framing Δ $ (est):[/bold] {total_cost.fmt(signed=True)}"
                          f"  [dim](from {prices.path.name}; unpriced sizes excluded)[/dim]")
    if report.envelope_deltas:
        envelope = Table("assembly", "metric", "A", "B", "Δ", title="envelope")
        for item in report.envelope_deltas:
            delta = f"{item.delta:+,.2f}" if item.delta is not None else (item.note or _UNKNOWN)
            envelope.add_row(item.assembly, item.metric,
                             _number(item.baseline) if item.baseline is not None else "—",
                             _number(item.variant) if item.variant is not None else "—",
                             delta)
        console.print(envelope)
    if report.check_deltas:
        table = Table("check", "elements", "A", "B", title="checks")
        for item in report.check_deltas:
            table.add_row(item.check_id, item.element_tags or "—",
                          item.baseline or "—", item.variant or "—")
        console.print(table)
    else:
        console.print("[dim]no check result changed[/dim]")


@variants_app.command("assemblies")
def compare_assemblies_command(
    tags: List[str] = typer.Argument(..., help="Two or three assembly tags; the first is the "
                                              "baseline"),
    house: Optional[Path] = typer.Option(None, help="House directory (default: cwd)"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Assembly delta compare (#53): R-value, thickness, layers, framing and STC side by side."""
    from typehaus.diff.assembly_compare import compare_assemblies
    from typehaus.source import load_plan

    directory = _house(house)
    result = load_plan(directory)
    if result.plan is None:
        console.print(f"[red]cannot load the plan in {directory}[/red]")
        raise typer.Exit(1)
    try:
        comparison = compare_assemblies(result.plan.library, list(tags))
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    if as_json:
        console.print_json(json.dumps(comparison.as_dict()))
    else:
        table = Table("assembly", "R", "thickness (in)", "layers", "framing", "STC")
        for item in comparison.metrics:
            framing = "—"
            if item.structure_member:
                spacing = (f' @ {item.framing_spacing_in:g}" o.c.'
                           if item.framing_spacing_in else "")
                framing = f"{item.structure_member}{spacing}"
            table.add_row(item.tag, item.r_value.fmt(), f"{item.thickness_in:.2f}",
                          str(item.layer_count), framing,
                          str(item.stc) if item.stc is not None else "—")
        console.print(table)
        for tag, rows in comparison.deltas.items():
            deltas = Table("metric", comparison.baseline_tag, tag, "Δ",
                           title=f"{tag} vs {comparison.baseline_tag}")
            for row in rows:
                deltas.add_row(f"{row.metric} ({row.unit})", _number(row.baseline),
                               _number(row.candidate),
                               _UNKNOWN if row.delta is None else f"{row.delta:+,.2f}")
            console.print(deltas)
    path = comparison.write(directory / "out" / "assembly_compare.json")
    console.print(f"wrote {path}")
