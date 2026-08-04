"""`haus takeoff` — the resolved bill of materials, optionally costed.

Registered onto the shared app in :mod:`typehaus.cli._shared`; see that module for why
command bodies keep their imports inside the function.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, app, console
from typehaus.findings import Severity


@app.command()
def takeoff(
    house: Optional[Path] = typer.Argument(None),
    as_json: bool = typer.Option(False, "--json"),
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
               "lighting_load": bom["lighting_load"],
               # Low-voltage (2026-08-02). Same argument as lighting_controls above: a
               # section the CLI drops is invisible to the estimate and to variant compare.
               "data_devices": bom["data_devices"],
               "data_raceways": bom["data_raceways"],
               "poe_budget": bom["poe_budget"],
               # The 2026-07-25 sweep's sections. Forwarded here rather than left in
               # bill_of_materials only: a section the CLI drops is invisible to the
               # estimate and to `haus variants compare`.
               "floor_finishes": bom["floor_finishes"],
               "envelope_layers": bom["envelope_layers"],
               "wall_structure": bom["wall_structure"],
               "wood_surfaces": bom["wood_surfaces"],
               "openings": bom["openings"],
               "stair_finish": bom["stair_finish"],
               "footing_bedding": bom["footing_bedding"],
               "pipe_runs": bom["pipe_runs"],
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
        payload["cost_estimate"] = estimate_costs(bom, prices)
    if as_json:
        console.print_json(json.dumps(payload))
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
            console.print(f"  {name}: {section['subtotal_fmt']}")
            for row in section["rows"]:
                console.print(f"    {row['quantity']:>9,.1f} {row['unit']:<6} "
                              f"{row['key']}: {row['cost_fmt']}")
        console.print(f"  [bold]total: {estimate['total_fmt']}[/bold]")
        if estimate["unpriced"]:
            missing = ", ".join(f"{row['section']}:{row['key']}"
                                for row in estimate["unpriced"])
            console.print(f"  [yellow]not priced (add to prices.toml): {missing}[/yellow]")
