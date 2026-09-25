"""The printers behind `haus takeoff`'s text report (split from :mod:`cmd_takeoff`)."""

from __future__ import annotations

from rich.console import Console

from typehaus.cli._shared import console


def _unpriced_note(estimate: dict) -> str:
    """The headline's own caveat: a total that silently omits unpriced rows reads as a saving."""
    n = len(estimate.get("unpriced") or [])
    return f"  [yellow]— excludes {n} unpriced row group(s)[/yellow]" if n else ""


def _print_driver_overlaps(estimate: dict, console: Console) -> None:
    """Driven allowances measured off BOM rows another section also priced.

    Not an error and deliberately not silent. [allowances]'s one rule is that an allowance
    must be scope no other section prices; this is the only automatic check of that rule.
    It cannot decide:
    measuring a roof vent mat off the standing seam's square footage is right, and billing
    the standing seam twice is wrong, and the two are the same shape. It names them so a
    reader can look at the one line where it matters.
    """
    overlaps = estimate.get("driver_overlaps") or []
    if not overlaps:
        return
    console.print(f"  [yellow]{len(overlaps)} driven allowance(s) measured off rows another "
                  f"section prices — confirm each is a MEASUREMENT, not a second "
                  f"bill:[/yellow]")
    for finding in overlaps:
        parts = []
        for name, keys in finding["sections"].items():
            # Truncated on purpose: the reader needs to know WHICH SECTION, not to read 14
            # window types. The full list is in the --json payload's `driver_overlaps`.
            shown = ", ".join(keys[:3])
            more = f" +{len(keys) - 3}" if len(keys) > 3 else ""
            parts.append(f"{name} ({shown}{more})")
        console.print(f"    [yellow]{finding['item']} <- {'; '.join(parts)}[/yellow]")


# Sections whose full-detail rows this rollup never speaks for — the giant nested payloads
# (`cost_estimate`, `space_summary`) get their own compact treatment below rather than a
# meaningless "N keys" line.
_SUMMARY_SKIP = {"cost_estimate", "space_summary"}


def _print_run_schedule(rows: list, console: Console) -> None:
    """The routing schedule, worst detour first.

    Printed as one line per run rather than grouped, because the reader is looking for the
    single run to go and look at. ``ratio`` is developed / straight-line-3D; a blank one is
    a run whose endpoints are too close together to grade (see ``runs.MIN_STRAIGHT_FT``),
    not a run that scored zero.
    """
    total = sum(float(row["developed_ft"]) for row in rows)
    console.print(f"[bold]Run schedule[/bold]  ({len(rows)} runs / {total:,.0f} LF developed; "
                  "developed · plan · rise · straight · ratio · elbows)")
    console.print(f"  [dim]{'tag':<24}{'kind':<8}{'dev':>7}{'plan':>7}{'rise':>7}"
                  f"{'strt':>7}{'ratio':>7}{'elb':>5}  cost[/dim]", soft_wrap=True)
    for row in rows:
        ratio = f"{row['ratio']:.2f}" if row["ratio"] is not None else "—"
        low, high = row.get("cost_low"), row.get("cost_high")
        if low is None:
            key = row.get("price_key", "?")
            cost = f"[dim]unpriced ({key})[/dim]" if "price_key" in row else ""
        elif abs(high - low) < 0.005:
            cost = f"${low:,.0f}"
        else:
            cost = f"${low:,.0f} – ${high:,.0f}"
        console.print(f"  {row['tag']:<24}{row['kind']:<8}"
                      f"{row['developed_ft']:>7.1f}{row['plan_ft']:>7.1f}"
                      f"{row['rise_ft']:>7.1f}{row['straight_ft']:>7.1f}"
                      f"{ratio:>7}{row['elbows']:>5}  {cost}", soft_wrap=True)


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
    console.print(f"  [bold]construction total: {estimate['total_fmt']}[/bold]"
                  f"{_unpriced_note(estimate)}")
    if estimate.get("excluded_sections"):
        console.print(f"  [bold]with furnishings: {estimate['grand_total_fmt']}[/bold]")
    if estimate["unpriced"]:
        console.print(f"  [yellow]{len(estimate['unpriced'])} unpriced row group(s) "
                      "(add to prices.toml)[/yellow]")
    # The mirror: a price with no quantity. Dim rather than yellow — an unpriced row makes
    # the total WRONG, a dead row only makes it silent about coverage the reader thinks
    # they have. Declared-[retired] rows are already subtracted, so what prints is the
    # class worth looking at.
    unused = estimate.get("unused_price_rows") or []
    if unused:
        console.print(f"  [dim]{len(unused)} price row(s) no BOM row visits — a renamed "
                      r"key, a deleted element, or a deliberate revert (declare it in "
                      r"\[retired])[/dim]")


def _print_basis(estimate: dict) -> None:
    """material / labour / merged, and whether the file actually declared its basis.

    A total that does not say what it includes is the difference between a homeowner's
    shopping list and a contractor's bid.
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
