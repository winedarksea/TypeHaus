"""``haus bids`` — one unpriced request-for-quote per trade, from the same BOM the estimate
prices (decision #71).

Its own command rather than a flag on ``haus takeoff --csv`` for the reason ``haus millwork``
is: that writer flattens the *priced* estimate, and a bid package is the other way round —
the sub is quoting, not being quoted. Dollars are opt-in (``--priced``) and refused without
a ``prices.toml``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, app, console
from typehaus.findings import Severity

#: The CSV column set. Unpriced by default; ``--priced`` appends the four price columns.
BID_COLUMNS = ("trade", "group", "section", "key", "description", "quantity", "unit",
               "storeys", "element_tags")
PRICE_COLUMNS = ("unit_price_low", "unit_price_high", "total_low", "total_high")


def _load(directory: Path, priced: bool) -> tuple[Any, Any, dict[str, Any], Any]:
    """``(loaded, model, packages, labels)`` — exits 1 on a load/resolve error, 2 when
    ``--priced`` is asked of a house with no prices."""
    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.emit.draw.sheets import build_sheet_index
    from typehaus.resolve import resolve
    from typehaus.server.space_summary import estimate_areas
    from typehaus.source import load_plan
    from typehaus.takeoff.bid_package import build_bid_packages
    from typehaus.takeoff.bom import bill_of_materials
    from typehaus.takeoff.labels import LabelIndex
    from typehaus.takeoff.product_labels import product_labels

    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    model, findings = resolve(loaded.plan)
    if any(finding.severity is Severity.ERROR for finding in findings):
        _print_findings(findings)
        raise typer.Exit(1)
    prices = load_prices(directory)
    if priced and prices is None:
        console.print("[red]--priced needs prices: this house has no prices.toml[/red]")
        raise typer.Exit(2)
    labels = LabelIndex.from_plan(loaded.plan)
    bom = bill_of_materials(model)
    estimate = (estimate_costs(bom, prices, estimate_areas(model), product_labels(loaded.plan),
                               labels) if prices is not None else None)
    sheets = tuple(spec.number for spec in build_sheet_index(model, house_dir=directory))
    packages = build_bid_packages(model, bom, estimate=estimate, priced=priced, labels=labels,
                                  sheet_numbers=sheets)
    return loaded, model, packages, labels


def _flat_rows(package: Any, priced: bool) -> list[dict[str, Any]]:
    rows = []
    for group in package.groups:
        for line in group.lines:
            row = {"trade": package.trade, "group": group.heading, "section": line.section,
                   "key": line.key, "description": line.description,
                   "quantity": line.quantity, "unit": line.unit,
                   "storeys": ", ".join(line.storeys),
                   "element_tags": ", ".join(line.element_tags)}
            if priced:
                row.update({"unit_price_low": line.unit_price[0] if line.unit_price else "",
                            "unit_price_high": line.unit_price[1] if line.unit_price else "",
                            "total_low": line.total[0] if line.total else "",
                            "total_high": line.total[1] if line.total else ""})
            rows.append(row)
    return rows


def _markdown(package: Any, loaded: Any, priced: bool) -> str:
    """The package as one Markdown document, byte-deterministic: no date, sorted throughout."""
    from typehaus import engine_version
    from typehaus.emit.md_writer import bullets, callout, document, heading, kv_block, table

    blocks = [
        heading(f"{package.recipe.title} — {loaded.plan.project.name}"),
        kv_block([("House", loaded.plan.project.name), ("Trade", package.label),
                  ("Engine", engine_version()), ("Model hash", loaded.content_hash),
                  ("Lines", len(package.lines))]),
        package.recipe.intro,
        callout("Quantities are net of waste unless a line says otherwise; this is a request "
                "for quote, not a purchase order. Price the scope as you would install it and "
                "note where your count differs."),
    ]
    price_cols = ["unit low", "unit high", "total low", "total high"] if priced else []
    for group in package.groups:
        blocks.append(heading(group.heading, 2))
        blocks.append(table(
            ["item", "quantity", "unit", "detail", "storeys", *price_cols],
            [[line.description, line.quantity, line.unit, line.detail, ", ".join(line.storeys),
              *((line.unit_price[0], line.unit_price[1], line.total[0], line.total[1])
                if priced and line.unit_price and line.total else
                (("", "", "", "") if priced else ()))]
             for line in group.lines]))
    if package.recipe.tags_appendix and package.lines:
        blocks.append(heading("Appendix A — elements, per line", 2))
        blocks.append(table(["item", "elements"],
                            [[line.description, ", ".join(line.element_tags) or "—"]
                             for line in package.lines]))
    if package.sheets:
        blocks.append(heading("Appendix B — drawings", 2))
        blocks.append(bullets(package.sheets))
    if package.allowances:
        blocks.append(heading("Appendix C — owner allowances in this trade", 2))
        blocks.append(table(["allowance", "quantity", "unit"],
                            [[line.description, line.quantity, line.unit]
                             for line in package.allowances]))
    return document(*blocks)


def _readme(packages: dict[str, Any], loaded: Any) -> str:
    from typehaus.emit.md_writer import document, heading, table

    return document(
        heading(f"Bid packages — {loaded.plan.project.name}"),
        "One request for quote per trade, unpriced, from the model's bill of materials.",
        table(["trade", "package", "lines", "storeys", "files"],
              [[p.label, p.recipe.title, len(p.lines), ", ".join(p.storeys),
                f"{trade}.md, {trade}.csv"] for trade, p in packages.items()]))


@app.command()
def bids(
    house: Path | None = typer.Argument(None),
    trade: str | None = typer.Option(None, "--trade", help="One trade's package."),
    md: Path | None = typer.Option(None, "--md", help="Write the package as Markdown."),
    csv: Path | None = typer.Option(None, "--csv", help="Write the package as CSV."),
    as_json: bool = typer.Option(False, "--json"),
    all_trades: bool = typer.Option(False, "--all", help="Every trade, one file pair each."),
    out: Path = typer.Option(Path("out/bids"), "--out", help="Directory for --all."),
    priced: bool = typer.Option(False, "--priced",
                                help="Carry the estimate's prices. Needs prices.toml."),
) -> None:
    """Report the per-trade bid packages: what each sub is asked to quote, unpriced."""
    import json

    from typehaus.emit.csv_writer import write_csv
    from typehaus.emit.trades import TRADES

    directory = _resolve_house(house)
    loaded, _model, packages, _labels = _load(directory, priced)
    columns = (*BID_COLUMNS, *(PRICE_COLUMNS if priced else ()))

    if all_trades:
        from typehaus.takeoff.handoff import write_manifest

        out.mkdir(parents=True, exist_ok=True)
        files: list[str] = []
        for name, package in packages.items():
            (out / f"{name}.md").write_text(_markdown(package, loaded, priced), encoding="utf-8")
            write_csv(out / f"{name}.csv", columns, _flat_rows(package, priced))
            files += [f"{name}.md", f"{name}.csv"]
        (out / "README.md").write_text(_readme(packages, loaded), encoding="utf-8")
        files.append("README.md")
        write_manifest(out, files)
        console.print(f"wrote {len(packages)} package(s) to {out}", soft_wrap=True)
        return

    if trade is not None:
        if trade not in TRADES:
            console.print(f"[red]unknown trade {trade!r}; one of {sorted(TRADES)}[/red]")
            raise typer.Exit(2)
        package = packages.get(trade)
        if package is None:
            console.print(f"[yellow]no BOM row files under {trade!r} in this house[/yellow]")
            raise typer.Exit(0)
        if md is not None:
            md.parent.mkdir(parents=True, exist_ok=True)
            md.write_text(_markdown(package, loaded, priced), encoding="utf-8")
            console.print(f"wrote {md} ({len(package.lines)} lines)", soft_wrap=True)
        if csv is not None:
            write_csv(csv, columns, _flat_rows(package, priced))
            console.print(f"wrote {csv} ({len(package.lines)} lines)", soft_wrap=True)
        if as_json:
            console.print_json(json.dumps(package.as_dict()))
        if md is None and csv is None and not as_json:
            console.print(_markdown(package, loaded, priced), soft_wrap=True, markup=False)
        return

    if as_json:
        console.print_json(json.dumps({name: p.as_dict() for name, p in packages.items()}))
        return
    from rich.table import Table

    summary = Table(title="Bid packages", show_lines=False)
    for column in ("trade", "package", "lines", "sections", "storeys"):
        summary.add_column(column)
    for name, package in packages.items():
        summary.add_row(name, package.recipe.title, str(len(package.lines)),
                        str(len(package.groups)), ", ".join(package.storeys))
    console.print(summary)
    console.print("[dim]haus bids <house> --trade framing --md out/bids/framing.md; "
                  "--all writes every package[/dim]")
