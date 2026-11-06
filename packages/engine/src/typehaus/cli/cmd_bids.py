"""``haus bids`` — one unpriced request-for-quote per crew, from the same BOM the estimate
prices (decision #71). A crew is the trades one sub bids together (decision #115).

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
from typehaus.cli.bid_render import crew_markdown, package_markdown, readme, summary_markdown
from typehaus.findings import Severity

#: The CSV column set. Unpriced by default; ``--priced`` appends the four price columns.
BID_COLUMNS = ("trade", "group", "section", "key", "description", "quantity", "unit",
               "application", "storeys", "element_tags")
PRICE_COLUMNS = ("unit_price_low", "unit_price_high", "total_low", "total_high")


def _load(directory: Path, priced: bool) -> tuple[Any, Any, dict[str, Any], dict[str, Any],
                                                   Any]:
    """``(loaded, model, packages, crews, bom)`` — exits 1 on a load/resolve error, 2 when
    ``--priced`` is asked of a house with no prices."""
    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.emit.draw.sheets import build_sheet_index
    from typehaus.resolve import resolve
    from typehaus.server.space_summary import estimate_areas
    from typehaus.source import load_plan
    from typehaus.takeoff.bid_package import build_bid_packages
    from typehaus.takeoff.bom import bill_of_materials
    from typehaus.takeoff.crews import crews_for
    from typehaus.takeoff.labels import LabelIndex
    from typehaus.takeoff.product_labels import product_labels
    from typehaus.takeoff.task_state import load_tasks

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
    return loaded, model, packages, crews_for(packages, load_tasks(directory).crews), bom


def _summaries(directory: Path, model: Any, bom: Any, packages: dict[str, Any],
               trades: tuple[str, ...] | None = None) -> dict[str, Any]:
    """The per-trade summaries. Safety glazing and egress are the R308.4 / R310 checks'
    own derivation, handed in so ``takeoff`` never imports ``checks``."""
    from typehaus.checks.code.mn_residential.egress import egress_window_rooms
    from typehaus.checks.code.mn_residential.glazing import safety_glazing_clauses
    from typehaus.checks.run import build_context_from_model
    from typehaus.takeoff.bid_summaries import SummaryInputs, build_summaries

    ctx = build_context_from_model(model, [], directory)
    return build_summaries(SummaryInputs(model, bom, safety_glazing_clauses(ctx),
                                         egress_window_rooms(ctx), packages), trades)


def _write_summary(summary: Any, loaded: Any, md: Path, csv_stem: Path) -> list[Path]:
    """``md`` and one ``<stem>-<table>.csv`` per table: each table has its own columns."""
    from typehaus.emit.csv_writer import write_csv

    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(summary_markdown(summary, loaded), encoding="utf-8")
    paths = [md]
    for item in summary.tables:
        paths.append(write_csv(csv_stem.with_name(f"{csv_stem.name}-{item.slug}.csv"),
                               item.columns, item.as_dicts()))
    return paths


def _flat_rows(package: Any, priced: bool) -> list[dict[str, Any]]:
    rows = []
    for group in package.groups:
        for line in group.lines:
            row = {"trade": package.trade, "group": group.heading, "section": line.section,
                   "key": line.key, "description": line.description,
                   "quantity": line.quantity, "unit": line.unit,
                   "application": line.application,
                   "storeys": ", ".join(line.storeys),
                   "element_tags": ", ".join(line.element_tags)}
            if priced:
                row.update({"unit_price_low": line.unit_price[0] if line.unit_price else "",
                            "unit_price_high": line.unit_price[1] if line.unit_price else "",
                            "total_low": line.total[0] if line.total else "",
                            "total_high": line.total[1] if line.total else ""})
            rows.append(row)
    return rows


@app.command()
def bids(
    house: Path | None = typer.Argument(None),
    trade: str | None = typer.Option(None, "--trade", help="One trade's package."),
    crew: str | None = typer.Option(None, "--crew",
                                    help="One crew's package: its trades as one document."),
    md: Path | None = typer.Option(None, "--md", help="Write the package as Markdown."),
    csv: Path | None = typer.Option(None, "--csv", help="Write the package as CSV."),
    as_json: bool = typer.Option(False, "--json"),
    all_trades: bool = typer.Option(False, "--all", help="Every crew, one file pair each."),
    out: Path = typer.Option(Path("out/bids"), "--out", help="Directory for --all."),
    priced: bool = typer.Option(False, "--priced",
                                help="Carry the estimate's prices. Needs prices.toml."),
    summary: bool = typer.Option(False, "--summary",
                                 help="With --trade: the trade's summary schedule instead."),
) -> None:
    """Report the bid packages: what each crew is asked to quote, unpriced."""
    import json

    from typehaus.emit.csv_writer import write_csv
    from typehaus.emit.trades import TRADES

    directory = _resolve_house(house)
    loaded, model, packages, crews, bom = _load(directory, priced)
    columns = (*BID_COLUMNS, *(PRICE_COLUMNS if priced else ()))

    if all_trades:
        from typehaus.takeoff.handoff import write_manifest

        out.mkdir(parents=True, exist_ok=True)
        files: list[str] = []
        summaries = _summaries(directory, model, bom, packages)
        for name, item in crews.items():
            (out / f"{name}.md").write_text(crew_markdown(item, packages, loaded, priced),
                                            encoding="utf-8")
            write_csv(out / f"{name}.csv", columns,
                      [row for t in item.trades for row in _flat_rows(packages[t], priced)])
            files += [f"{name}.md", f"{name}.csv"]
        for name, item in summaries.items():
            files += [path.name for path in _write_summary(
                item, loaded, out / f"{name}-summary.md", out / name)]
        (out / "README.md").write_text(readme(crews, packages, loaded, summaries),
                                       encoding="utf-8")
        files.append("README.md")
        write_manifest(out, files)
        console.print(f"wrote {len(crews)} crew package(s) to {out}", soft_wrap=True)
        return

    if crew is not None:
        found_crew = crews.get(crew)
        if found_crew is None:
            console.print(f"[red]no crew {crew!r} bids in this house; one of "
                          f"{sorted(crews)}[/red]")
            raise typer.Exit(2)
        text = crew_markdown(found_crew, packages, loaded, priced)
        if md is not None:
            md.parent.mkdir(parents=True, exist_ok=True)
            md.write_text(text, encoding="utf-8")
            console.print(f"wrote {md}", soft_wrap=True)
        if csv is not None:
            write_csv(csv, columns, [row for t in found_crew.trades
                                     for row in _flat_rows(packages[t], priced)])
            console.print(f"wrote {csv}", soft_wrap=True)
        if md is None and csv is None:
            console.print(text, soft_wrap=True, markup=False)
        return

    if trade is not None:
        if trade not in TRADES:
            console.print(f"[red]unknown trade {trade!r}; one of {sorted(TRADES)}[/red]")
            raise typer.Exit(2)
        if summary:
            found = _summaries(directory, model, bom, packages, (trade,)).get(trade)
            if found is None:
                console.print(f"[yellow]{trade!r} has no summary; its package is the "
                              "schedule[/yellow]")
                raise typer.Exit(0)
            if md is None and csv is None:
                console.print(summary_markdown(found, loaded), soft_wrap=True, markup=False)
            else:
                paths = _write_summary(found, loaded, md or Path(f"out/bids/{trade}-summary.md"),
                                       (csv or Path(f"out/bids/{trade}.csv")).with_suffix(""))
                console.print(f"wrote {', '.join(str(p) for p in paths)}", soft_wrap=True)
            return
        package = packages.get(trade)
        if package is None:
            console.print(f"[yellow]no BOM row files under {trade!r} in this house[/yellow]")
            raise typer.Exit(0)
        if md is not None:
            md.parent.mkdir(parents=True, exist_ok=True)
            md.write_text(package_markdown(package, loaded, priced), encoding="utf-8")
            console.print(f"wrote {md} ({len(package.lines)} lines)", soft_wrap=True)
        if csv is not None:
            write_csv(csv, columns, _flat_rows(package, priced))
            console.print(f"wrote {csv} ({len(package.lines)} lines)", soft_wrap=True)
        if as_json:
            console.print_json(json.dumps(package.as_dict()))
        if md is None and csv is None and not as_json:
            console.print(package_markdown(package, loaded, priced), soft_wrap=True,
                          markup=False)
        return

    if as_json:
        console.print_json(json.dumps({name: p.as_dict() for name, p in packages.items()}))
        return
    from rich.table import Table

    summary = Table(title="Bid packages", show_lines=False)
    for column in ("crew", "by", "trade", "package", "lines", "storeys"):
        summary.add_column(column)
    for key, item in crews.items():
        for index, name in enumerate(item.trades):
            package = packages[name]
            summary.add_row(key if index == 0 else "",
                            ("owner" if item.self_performed else "sub") if index == 0 else "",
                            name, package.recipe.title, str(len(package.lines)),
                            ", ".join(package.storeys))
    console.print(summary)
    console.print("[dim]haus bids <house> --crew <key> --md out/bids/<key>.md; --trade for "
                  "one trade; --all writes every crew[/dim]")
