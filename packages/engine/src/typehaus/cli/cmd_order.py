"""`haus order` — one retailer's shopping list: every bought item, in packs.

A view of the placeables BOM (``takeoff/order_list.py``); it adds nothing to the estimate.
The unit price is shown only where the house's own ``prices.toml`` carries one (#28).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, app, console
from typehaus.findings import Severity


def _unit_price(prices: Any, keys: list[str]) -> str:
    from typehaus.cli.prices import rate_for

    for key in keys:
        _, price = rate_for(prices, "placeables", key)
        if price is not None:
            material = getattr(price, "material", None) or price
            low, high = material.low, material.high
            return f"${low:,.2f}" if abs(high - low) < 1e-9 else f"${low:,.0f}-{high:,.0f}"
    return ""


def _markdown(listing: dict[str, list[dict[str, Any]]], brand: str | None) -> str:
    from typehaus.emit.md_writer import document, heading, table
    from typehaus.takeoff.order_list import ORDER_COLUMNS

    items, unresolved = listing["items"], listing["unresolved"]
    brands = sorted({item["brand"] for item in items})
    blocks = [heading(f"{brand or 'Parts'} order list"),
              "Units are what the model counts; packs round each up to the retail pack. "
              "Linear stock (rail, toe kick) is whole sticks per touching run. A view of "
              "the takeoff, not an addition to it."]
    for name in brands:
        blocks += [heading(name, 2), table(
            [column.replace("_", " ") for column in ORDER_COLUMNS],
            [[item.get(column) if item.get(column) not in ("", None) else None
              for column in ORDER_COLUMNS] for item in items if item["brand"] == name])]
    blocks += [heading("Unresolved", 2),
               table(["item", "reason", "used by"],
                     [[row["item"], row["reason"], row["used_by"]] for row in unresolved])
               if unresolved else "Nothing: every item names an article number."]
    return document(*blocks)


@app.command()
def order(
    house: Path | None = typer.Argument(None),
    brand: str | None = typer.Option(None, "--brand",
                                     help="One brand, e.g. IKEA. Default: every brand with parts."),
    md: Path | None = typer.Option(None, "--md", help="Write the list as Markdown."),
    csv: Path | None = typer.Option(None, "--csv", help="Write the list as CSV."),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Report a retailer order list: article, packs, and the cabinets that use each item."""
    import json

    from typehaus.cli.price_file import load_prices
    from typehaus.resolve import resolve
    from typehaus.source import load_plan
    from typehaus.takeoff.order_list import ORDER_COLUMNS, order_list

    directory = _resolve_house(house)
    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    model, findings = resolve(loaded.plan)
    if any(finding.severity is Severity.ERROR for finding in findings):
        _print_findings(findings)
        raise typer.Exit(1)
    listing = order_list(model, brand)
    prices = load_prices(directory)
    for item in listing["items"]:
        keys = item.pop("price_keys")
        item["unit_price"] = _unit_price(prices, keys) if prices is not None else ""

    if csv is not None:
        from typehaus.emit.csv_writer import write_csv

        written = write_csv(csv, ORDER_COLUMNS, listing["items"])
        console.print(f"wrote {written} ({len(listing['items'])} items)", soft_wrap=True)
    if md is not None:
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(_markdown(listing, brand), encoding="utf-8")
        console.print(f"wrote {md} ({len(listing['items'])} items)", soft_wrap=True)
    if as_json:
        console.print_json(json.dumps(listing))
        return
    for item in listing["items"]:
        length = f" ({item['length_ft']} ft)" if item.get("length_ft") else ""
        console.print(f"  {item['brand']:<11} {item['article'] or '?':<12} "
                      f"{item['packs']:>3} pk / {item['units']:>3} u{length}  "
                      f"{item['name']}  [dim]{item['unit_price']}[/dim]", soft_wrap=True)
    if listing["unresolved"]:
        console.print("[bold yellow]Unresolved[/bold yellow]")
        for row in listing["unresolved"]:
            console.print(f"  {row['item']}: {row['reason']}  [dim]{row['used_by']}[/dim]",
                          soft_wrap=True)
