"""`haus takeoff` — the resolved bill of materials, optionally costed.

Registered onto the shared app in :mod:`typehaus.cli._shared`; see that module for why
command bodies keep their imports inside the function.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from typehaus.cli._shared import _print_findings, _resolve_house, app, console
from typehaus.findings import Severity


@app.command()
def takeoff(
    house: Optional[Path] = typer.Argument(None),
    as_json: bool = typer.Option(False, "--json"),
    summary: bool = typer.Option(False, "--summary",
                                 help="compact per-section counts + $ rollup (#52), instead "
                                      "of the full per-row dump"),
    csv: Optional[Path] = typer.Option(
        None, "--csv", help="Also write the priced estimate as a CSV at this path "
                            "(the RSMeans / Craftsman / Buildertrend intake artifact)."),
) -> None:
    """Report the resolved bill of materials: framing, solids, sheet goods, glazing,
    hardware, placeables, and radiant floor heat.

    If the house supplies a ``prices.toml`` (user-authored — Type:Haus ships none; see
    :mod:`typehaus.cli.prices` for the format), the report adds a $ / $-range cost
    estimate that is explicit about which rows it could not price.
    """
    from collections import Counter
    import json

    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.takeoff.product_labels import product_labels
    from typehaus.resolve import resolve
    from typehaus.source import load_plan
    from typehaus.takeoff import bill_of_materials

    d = _resolve_house(house)
    loaded = load_plan(d)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    try:
        prices = load_prices(d)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc
    model, findings = resolve(loaded.plan)
    if any(finding.severity is Severity.ERROR for finding in findings):
        _print_findings(findings)
        raise typer.Exit(1)
    framing = Counter(f"{member.category}:{member.profile}" for member in model.all_members())
    bom = bill_of_materials(model)
    framing_bom = bom["framing"]
    framing_by_size = bom["framing_by_size"]
    radiant = bom["floor_heat"]
    payload = {"framing": dict(sorted(framing.items())),
               "framing_bom": framing_bom, "framing_by_size": framing_by_size,
               "structural_solids": bom["structural_solids"],
               "floor_heat": radiant, "sheet_goods": bom["sheet_goods"],
               "construction_returns": bom["construction_returns"],
               "sill_gaskets": bom["sill_gaskets"],
               "glazing_panels": bom["glazing_panels"],
               "glazing_trim": bom["glazing_trim"],
               "hardware": bom["hardware"],
               "placeables": bom["placeables"],
               "electrical_devices": bom["electrical_devices"],
               "panel_schedule": bom["panel_schedule"],
               "service_load": bom["service_load"],
               "conduit": bom["conduit"],
               "solar": bom["solar"],
               "backup_power": bom["backup_power"],
               "luminaire_schedule": bom["luminaire_schedule"],
               # lighting_controls was the one section bill_of_materials produced and this
               # payload dropped — the switch legs simply never reached `haus takeoff`.
               "lighting_controls": bom["lighting_controls"],
               "light_runs": bom["light_runs"],
               "light_run_materials": bom["light_run_materials"],
               "lighting_load": bom["lighting_load"],
               # Same argument as lighting_controls above: a section the CLI drops is
               # invisible to the estimate and to variant compare.
               "data_devices": bom["data_devices"],
               "data_raceways": bom["data_raceways"],
               "poe_budget": bom["poe_budget"],
               # Forwarded here rather than left in bill_of_materials only: a section the
               # CLI drops is invisible to the estimate and to `haus variants compare`.
               "floor_finishes": bom["floor_finishes"],
               "envelope_layers": bom["envelope_layers"],
               "wall_structure": bom["wall_structure"],
               "wood_surfaces": bom["wood_surfaces"],
               "openings": bom["openings"],
               "stair_finish": bom["stair_finish"],
               "footing_bedding": bom["footing_bedding"],
               "pipe_runs": bom["pipe_runs"],
               "pipe_fittings": bom["pipe_fittings"],
               "plumbing_specialties": bom["plumbing_specialties"],
               "install_parts": bom["install_parts"],
               "pipe_insulation": bom["pipe_insulation"],
               "ducts": bom["ducts"],
               "sleeves": bom["sleeves"],
               "conductors": bom["conductors"],
               "railings": bom["railings"],
               "bug_screens": bom["bug_screens"],
               "drainage": bom["drainage"],
               "edge_trim": bom["edge_trim"]}
    if prices is not None:
        # $/sf needs a denominator, and the only honest ones are the space summary's:
        # conditioned area is what the energy code grades, gross is what a builder means
        # by "$/sf". Both come from the model, neither from a constant.
        from typehaus.server.space_summary import build_space_summary

        space_summary = build_space_summary(model)["overall"]
        areas = {"conditioned": space_summary["conditioned_sf"], "gross": space_summary["gross_sf"]}
        payload["cost_estimate"] = estimate_costs(bom, prices, areas,
                                                  product_labels(loaded.plan))
        payload["space_summary"] = space_summary
    if csv is not None:
        if prices is None:
            console.print("[red]--csv needs prices: this house has no prices.toml[/red]")
            raise typer.Exit(2)
        from typehaus.emit.csv_writer import write_csv
        from typehaus.takeoff.costs import load_costs
        from typehaus.takeoff.estimate_csv import ESTIMATE_COLUMNS, estimate_rows

        rows = estimate_rows(payload["cost_estimate"], load_costs(d))
        written = write_csv(csv, ESTIMATE_COLUMNS, rows)
        console.print(f"wrote {written} ({len(rows)} rows)", soft_wrap=True)
    if as_json:
        console.print_json(json.dumps(payload))
        return
    if summary:
        _print_takeoff_summary(payload, console)
        return
    console.print("[bold]Framing bill of materials[/bold]  (size · type: pieces / lineal ft)")
    for row in framing_bom:
        buckets = ", ".join(f"{b['count']}×{b['length_ft']}'" for b in row["stock"])
        bf = f" · {row['board_feet']} bf" if row["board_feet"] else ""
        console.print(f"  {row['profile']:>18} {row['category']:<18} "
                      f"{row['pieces']:>4} pc / {row['cut_length_ft']:>7.1f} LF cut "
                      f"[{buckets}]{bf}")
    console.print("[bold]Framing rollup by size[/bold]")
    for row in framing_by_size:
        bf = f" · {row['board_feet']} bf" if row["board_feet"] else ""
        console.print(f"  {row['profile']:>18}: {row['pieces']:>4} pc / "
                      f"{row['order_length_ft']:>5} LF ordered{bf}")
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
    if payload["structural_solids"]:
        console.print("[bold]Structural solids (concrete + standalone structure)[/bold]")
        for item in payload["structural_solids"]:
            assembly = f" · {item['assembly']}" if item["assembly"] else ""
            console.print(f"  {item['category']}{assembly}: {item['count']} × / "
                          f"{item['volume_cubic_yards']} cy")
    if payload["construction_returns"]:
        console.print("[bold]Construction returns (#45 pre-framing laps)[/bold]")
        for item in payload["construction_returns"]:
            console.print(f"  {item['category']} ({item['material']}): "
                          f"{item['count']} × / {item['length_ft']} LF")
    if payload["sill_gaskets"]:
        console.print("[bold]Sill seal (under the bearing plates)[/bold]")
        for item in payload["sill_gaskets"]:
            console.print(f"  {item['product']} ({item['thickness_in']}\" compressed): "
                          f"{item['count']} × / {item['length_ft']} LF")
    if payload["glazing_panels"]:
        console.print("[bold]Glazing panels (4x8 sheets)[/bold]")
        for item in payload["glazing_panels"]:
            console.print(f"  {item['assembly']}: {item['sheets_4x8']} sheets / "
                          f"{item['panels']} panel(s) ({item['net_area_sqft']} sf net)")
    if payload["glazing_trim"]:
        console.print("[bold]Glazing trim (aluminium extrusion)[/bold]")
        for item in payload["glazing_trim"]:
            weep = " · weep holes" if item["weep_holes"] else ""
            console.print(f"  {item['profile']}-channel ({item['material']}): "
                          f"{item['count']} × / {item['length_ft']} LF{weep}")
    if payload["hardware"]:
        console.print("[bold]Hardware[/bold]  (count · part: basis)")
        for item in payload["hardware"]:
            size = f" {item['size']}" if item["size"] else ""
            console.print(f"  {item['count']:>5} {item['unit']:<5} "
                          f"{item['part_number']}{size} — {item['description']}")
            console.print(f"        [dim]{item['basis']}[/dim]")
    if payload["placeables"]:
        console.print("[bold]Fixtures, appliances & furniture[/bold]  (count · type: domain · storey)")
        for item in payload["placeables"]:
            console.print(f"  {item['count']:>5} ea    {item['type']} — "
                          f"{item['domain']} · {item['storey']}")
    if payload["electrical_devices"]:
        console.print("[bold]Electrical devices[/bold]  (count · kind: type)")
        for item in payload["electrical_devices"]:
            label = item["name"] or item["type"]
            nema = f" NEMA {item['nema']}" if item["nema"] and item["nema"] not in label else ""
            console.print(f"  {item['count']:>5} ea    {item['kind']}: {label}{nema}")
    if payload["wood_surfaces"]:
        console.print("[bold]Wood surfaces by species[/bold]  (species · material · kind)")
        for item in payload["wood_surfaces"]:
            if item.get("net_area_sqft") is not None:
                qty = (f"{item['net_area_sqft']} sf net / "
                       f"{item['order_area_sqft']} sf order")
            else:
                qty = (f"{item['count']} pc / {item['order_length_ft']} LF ordered")
            bf = f" · {item['board_feet']} bf" if item.get("board_feet") else ""
            console.print(f"  {str(item['species'] or '?'):>9} · {item['material']:<14} "
                          f"{item['kind']:<20} {qty}{bf}")
    if payload["panel_schedule"]:
        load = payload["service_load"]
        console.print(f"[bold]Panel schedule[/bold]  ({len(payload['panel_schedule'])} circuits; "
                      f"demand {load['demand_amps']}A of {load['service_amps']}A service, "
                      f"{load['panel_rating_amps']}A panel"
                      + ("" if load["within_service"] else " — [red]OVER[/red]") + ")")
        for row in payload["panel_schedule"]:
            flags = "".join((" GFCI" if row["gfci"] else "",
                             f" {row['backup_tier'].upper()}" if row["backup_tier"]
                             else "",
                             " SOURCE" if row["source"] else ""))
            console.print(f"  {row['circuit']:<16} {row['breaker_amps']:>3}A/{row['poles']}p "
                          f"{row['connected_va']:>7,.0f} VA{flags} — {row['description']}")
    if payload["conduit"]:
        console.print("[bold]Conduit (EMT trunks)[/bold]")
        for item in payload["conduit"]:
            console.print(f"  {item['trade_size_in']}\": {item['runs']} run(s) / "
                          f"{item['length_ft']} LF — {', '.join(item['tags'])}")
    if payload["solar"]["panels"]:
        solar = payload["solar"]
        kw = solar["total_watts"] / 1000.0
        console.print(f"[bold]Solar[/bold]  {solar['panels']} × "
                      f"{solar['by_product'][0]['product']} = {kw:.2f} kW installed")
    if payload["backup_power"]["components"]:
        console.print("[bold]Backup microgrid[/bold]")
        for item in payload["backup_power"]["components"]:
            console.print(f"  {item['count']:>5} ea    {item['component']}")
            console.print(f"        [dim]{item['basis']}[/dim]")
    runtime = payload["backup_power"]["runtime"]
    if runtime.get("modeled"):
        autonomy, cycle = runtime["autonomy"], runtime["cycle_48h"]
        hours = autonomy["hours_always_on_only"]
        console.print(f"[bold]Backup runtime[/bold] (estimate)  "
                      f"{autonomy['usable_kwh']:g} kWh usable · always-on tier "
                      + (f"{hours:.1f} h" if hours is not None else "not computable")
                      + f" · 48h net {cycle['net_kwh_all_tiers']:+g} kWh")
        console.print(f"        [dim]{runtime['verdict']}[/dim]")
    if payload["luminaire_schedule"]:
        console.print("[bold]Luminaire schedule[/bold]  (mark · qty: description)")
        for row in payload["luminaire_schedule"]:
            qty = (f"{row['count']:>5} ea" if row["count"]
                   else f"{row['length_ft'] or 0:>5.0f} LF")
            photometry = " · ".join(part for part in (
                f"{row['watts']:.0f} W" if row["watts"] else
                (f"{row['watts_per_ft']:.1f} W/ft" if row["watts_per_ft"] else ""),
                f"{row['lumens']:,.0f} lm" if row["lumens"] else "",
                f"{row['cct_k']}K" if row["cct_k"] else "",
                f"CRI {row['cri']}" if row["cri"] else "",
                row["rating"],
            ) if part)
            console.print(f"  {row['mark']:>3}  {qty}    {row['description']}")
            console.print(f"        [dim]{photometry} · {', '.join(row['rooms'])}[/dim]")
        runs = payload["light_runs"]
        if runs["runs"]:
            console.print(f"[bold]LED runs[/bold]  {runs['total_length_ft']} LF total")
            for supply in runs["supplies"]:
                verdict = ("[red]UNDERSIZED[/red]" if supply["adequate"] is False
                           else ("?" if supply["adequate"] is None else "ok"))
                console.print(f"  {supply['psu']}: {supply['length_ft']} LF / "
                              f"{supply['connected_watts']:.0f} W connected, needs "
                              f"{supply['required_watts']:.0f} W at 125% — rated "
                              f"{supply['rated_watts']} W {verdict}")
        load = payload["lighting_load"]
        console.print(f"[bold]Connected lighting load[/bold]  "
                      f"{load['total_connected_va']:,.0f} VA against the "
                      f"{load['allowance_va']:,.0f} VA NEC 220.82 allowance for "
                      f"{load['conditioned_area_ft2']:,.0f} ft2")
    if prices is not None:
        estimate = payload["cost_estimate"]
        console.print(f"[bold]Cost estimate[/bold]  (from {prices.path.name}; "
                      "user-supplied prices, no defaults shipped)")
        for name, section in estimate["sections"].items():
            aside = "" if section.get("in_total", True) else "  [dim](beside the total)[/dim]"
            console.print(f"  {name}: {section['subtotal_fmt']}{aside}")
            for row in section["rows"]:
                console.print(f"    {row['quantity']:>9,.1f} {row['unit']:<6} "
                              f"{row['key']}: {row['cost_fmt']}")
        console.print(f"  [bold]construction total: {estimate['total_fmt']}[/bold]")
        _print_basis(estimate)
        _print_bid_ladder(estimate)
        _print_per_sf(estimate)
        if estimate.get("excluded_sections"):
            console.print(f"  {'+'.join(estimate['excluded_sections'])}: "
                          f"{estimate['excluded_total_fmt']}")
            console.print(f"  [bold]with furnishings: "
                          f"{estimate['grand_total_fmt']}[/bold]")
        if estimate["unpriced"]:
            missing = ", ".join(f"{row['section']}:{row['key']}"
                                for row in estimate["unpriced"])
            console.print(f"  [yellow]not priced (add to prices.toml): {missing}[/yellow]")


# Sections whose full-detail rows this rollup never speaks for — the giant nested payloads
# (`cost_estimate`, `space_summary`) get their own compact treatment below rather than a
# meaningless "N keys" line.
_SUMMARY_SKIP = {"cost_estimate", "space_summary"}


def _print_takeoff_summary(payload: dict, console: Console) -> None:
    """`haus takeoff --summary` — a compact, context-window-sized BOM rollup for agents (#52).

    Same argument as ``cli/digest.py``'s ``print_summary`` (``haus ls --summary``): the full
    per-row dump is ~1,363 lines / ~860KB on catlin, and most agent workflows only need "how
    many, and how much" per section, not every row. Sourced straight from the same payload
    the full/--json modes print, so it can never disagree with them about a count or a total.
    """
    console.print("[bold]Bill of materials summary[/bold]  (rows/keys per section)")
    total_rows = 0
    section_count = 0
    for name, value in payload.items():
        if name in _SUMMARY_SKIP:
            continue
        if isinstance(value, list):
            count, unit = len(value), "rows"
        elif isinstance(value, dict):
            count, unit = len(value), "keys"
        else:
            continue
        total_rows += count
        section_count += 1
        console.print(f"  {name:<22} {count:>5} {unit}")
    console.print(f"  [dim]{section_count} sections, {total_rows} rows/keys total[/dim]")
    estimate = payload.get("cost_estimate")
    if estimate is None:
        return
    console.print("[bold]Cost sections[/bold]  (from prices.toml; rows priced · subtotal)")
    for name, section in estimate["sections"].items():
        aside = "" if section.get("in_total", True) else "  [dim](beside the total)[/dim]"
        console.print(f"  {name:<22} {len(section['rows']):>5} rows  "
                      f"{section['subtotal_fmt']}{aside}")
    console.print(f"  [bold]construction total: {estimate['total_fmt']}[/bold]")
    if estimate.get("excluded_sections"):
        console.print(f"  [bold]with furnishings: {estimate['grand_total_fmt']}[/bold]")
    if estimate["unpriced"]:
        console.print(f"  [yellow]{len(estimate['unpriced'])} unpriced row group(s) "
                      "(add to prices.toml)[/yellow]")


def _print_basis(estimate: dict) -> None:
    """material / labour / merged, and whether the file actually declared its basis.

    A total that does not say what it includes is the difference between a homeowner's
    shopping list and a contractor's bid, and until ``[basis]`` existed the only statement
    of it was a prose comment at the top of prices.toml.
    """
    net = estimate["bid"]["net"]
    if not estimate.get("basis_declared"):
        console.print(r"  [yellow]no \[basis] table in prices.toml — every section is "
                      "assumed material-only[/yellow]")
    console.print(f"  [dim]basis: material {net['fmt']['material']} · "
                  f"labour {net['fmt']['labour']} · "
                  f"merged (installed, split unknown) {net['fmt']['merged']}[/dim]")


def _print_bid_ladder(estimate: dict) -> None:
    """The five stages, each on its own line — never folded into a section subtotal."""
    stages = [row for row in estimate["bid"]["stages"]
              if row["low"] or row["high"] or row["label"] in ("subtotal_net", "total")]
    if len(stages) <= 2:
        return  # nothing but net and total: the house declares no adjustments
    console.print("  [bold]bid ladder[/bold]")
    for row in stages:
        rate = f"  [dim]({row['rate'] * 100:.3g}%)[/dim]" if row.get("rate") else ""
        console.print(f"    {row['label']:<18} {row['fmt']}{rate}")
    untaxed = estimate["bid"]["untaxed_merged"]
    if untaxed["high"]:
        console.print(f"    [dim]sales tax could not reach ${untaxed['low']:,.0f}–"
                      f"${untaxed['high']:,.0f} of merged material+labour[/dim]")
    # Said out loud for the same reason: a tax stage that skips a third of the material base
    # is one nobody can check unless it names what it skipped and why.
    paid = estimate["bid"].get("material_tax_already_paid") or {}
    if paid.get("high"):
        console.print(f"    [dim]sales tax skipped ${paid['low']:,.0f}–${paid['high']:,.0f} of "
                      f"material already priced tax-inclusive[/dim]")


def _print_per_sf(estimate: dict) -> None:
    per_sf = estimate.get("per_sf")
    if not per_sf:
        return
    areas = estimate["areas"]
    for name, value in sorted(per_sf["total"].items()):
        console.print(f"  ${value['low']:,.0f}–${value['high']:,.0f} / {name} sf "
                      f"[dim]({areas[name]:,.0f} sf)[/dim]")
