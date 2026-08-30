"""``haus engineering`` — the engineering register, and the two gates over it.

What this command exists to answer, in one table: which requirements in this house are
outside the prescriptive path, what this engine computed for each, and whether a licensed
professional has sealed it *against the model as it stands right now*.

Two gates, and keeping them apart is the whole point:

* **draft** — this repo's own first-principles calculation checks out. Enough for a
  permit-ready printoff, and what ``haus print`` gates on.
* **sealed** — a PE has stamped it and the stamp still matches. ``--require-seal`` (and
  ``haus print --sealed``) gate here.

The engine never writes ``engineering.toml``. ``--fingerprint`` prints the value for a
person to paste in, which keeps pinning a seal a human act.
"""

from __future__ import annotations

from pathlib import Path

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, app, console


def _load(house: Path | None):  # type: ignore[no-untyped-def]
    """The house's engineering items, its results, and its register.

    The *item list* comes from running the checks and collecting every
    ``Finding.engineering_item``, not from asking the suite to enumerate itself. That is
    deliberate: which requirements in a house are outside the prescriptive path is a
    conclusion the checks reach — 7 feet of unbalanced fill here, 3 feet next door — and a
    second enumeration living in the suite would be the same judgement written twice, free
    to drift. Any kind that registers its own keys is unioned in, for an item nothing asks
    about.
    """
    from typehaus.checks import build_context, run_checks
    from typehaus.source import load_plan

    directory = _resolve_house(house)
    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    ctx, _ = build_context(loaded.plan, directory)
    report = run_checks(ctx)
    named = {x.engineering_item for x in report.findings if x.engineering_item}
    item_ids = sorted(named | set(ctx.engineering))
    return directory, item_ids, ctx.engineering, ctx.engineering_register


def _seal_label(state, signoff) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    from typehaus.engineering import Freshness

    if state is Freshness.FRESH:
        return "sealed", "green"
    if state is Freshness.STALE:
        # Loud on purpose. A stale seal is the only state that reads as done and is not.
        return "STALE", "red"
    if state is Freshness.UNPINNED:
        return f"{signoff.id} (not pinned)" if signoff else "not pinned", "yellow"
    return "unsealed", "yellow"


@app.command()
def engineering(
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    item: str | None = typer.Option(
        None, "--item", help="Print one item's calculation term by term."),
    unsealed: bool = typer.Option(
        False, "--unsealed", help="Only items still waiting on a fresh professional seal."),
    fingerprint_of: str | None = typer.Option(
        None, "--fingerprint",
        help="Print one item's current fingerprint, to paste into engineering.toml."),
    as_json: bool = typer.Option(False, "--json"),
    require_seal: bool = typer.Option(
        False, "--require-seal",
        help="Exit 1 unless every item carries a FRESH seal (the final gate, not the draft "
             "one)."),
) -> None:
    """Engineered requirements: what was computed, what governs, and who sealed it."""
    from rich.table import Table

    from typehaus.engineering import Freshness, Status
    from typehaus.engineering import fingerprint as compute_fingerprint

    _directory, item_ids, results, register = _load(house)

    if fingerprint_of:
        record = results[fingerprint_of]
        if record.status is Status.NO_CALC:
            console.print(
                f"[yellow]{fingerprint_of}: this engine computes nothing for this item, so "
                f"there are no inputs to fingerprint. A seal over it can be recorded, but "
                f"it cannot be pinned — and an unpinned seal never satisfies "
                f"--require-seal.[/yellow]")
            raise typer.Exit(1)
        console.print(compute_fingerprint(record))
        raise typer.Exit(0)

    if item:
        _print_item(results[item], register)
        raise typer.Exit(0)

    records = [results[key] for key in item_ids]
    if unsealed:
        records = [r for r in records
                   if register.freshness(r)[0] is not Freshness.FRESH]

    if as_json:
        import json

        console.print_json(json.dumps({"items": [_row_json(r, register) for r in records]}))
    elif not records:
        console.print("No engineered requirements: every rule in this house is answered by "
                      "a prescriptive table.")
    else:
        table = Table("Item", "Elements", "Governing", "Demand", "Capacity", "Ratio",
                      "Local", "Seal")
        for record in records:
            governing = record.governing
            state, signoff = register.freshness(record)
            label, colour = _seal_label(state, signoff)
            local, local_colour = _LOCAL[record.status]
            table.add_row(
                record.item_id,
                ", ".join(record.element_tags) or record.key,
                governing.name if governing else "—",
                f"{governing.demand:,.4g} {governing.unit}" if governing else "—",
                f"{governing.capacity:,.4g} {governing.unit}" if governing else "—",
                f"{governing.ratio:.2f}" if governing else "—",
                f"[{local_colour}]{local}[/{local_colour}]",
                f"[{colour}]{label}[/{colour}]",
            )
        console.print(table)
        console.print(
            "\n[bold]draft[/bold] = this engine's own calculation checks out (what "
            "`haus print` gates on).  [bold]sealed[/bold] = a licensed PE stamped it and "
            "the stamp still matches the model.", soft_wrap=True)

    over = [r for r in records if r.status is Status.OVER]
    if over:
        console.print(f"[red]{len(over)} item(s) do not check locally: "
                      f"{', '.join(r.item_id for r in over)}[/red]")
        raise typer.Exit(1)
    if require_seal:
        missing = [r for r in records if register.freshness(r)[0] is not Freshness.FRESH]
        if missing:
            console.print(f"[red]{len(missing)} item(s) carry no fresh professional seal: "
                          f"{', '.join(r.item_id for r in missing)}[/red]")
            raise typer.Exit(1)
    raise typer.Exit(0)


#: How each local status letters, and in what colour. NO_CALC is yellow rather than red:
#: nothing is wrong, something is simply outstanding.
_LOCAL = {}


def _init_local() -> None:
    from typehaus.engineering import Status

    _LOCAL.update({
        Status.OK: ("draft", "green"),
        Status.OVER: ("OVER", "red"),
        Status.INCOMPLETE: ("incomplete", "yellow"),
        Status.NO_CALC: ("no local calc", "yellow"),
    })


def _row_json(record, register) -> dict:  # type: ignore[no-untyped-def]
    state, signoff = register.freshness(record)
    governing = record.governing
    return {
        "item": record.item_id,
        "kind": record.kind,
        "elements": list(record.element_tags),
        "status": record.status.value,
        "basis": record.basis,
        "basis_version": record.basis_version,
        "governing": governing.name if governing else None,
        "demand": governing.demand if governing else None,
        "capacity": governing.capacity if governing else None,
        "ratio": record.ratio,
        "missing": list(record.missing),
        "seal": state.value,
        "signoff": signoff.id if signoff else None,
    }


def _print_item(record, register) -> None:  # type: ignore[no-untyped-def]
    """One item, term by term — the form a reviewer can check against a hand calc."""
    from rich.table import Table

    from typehaus.engineering import Status
    from typehaus.engineering import fingerprint as compute_fingerprint

    console.print(f"[bold]{record.item_id}[/bold]  ({record.kind} on {record.key})")
    if record.basis:
        console.print(f"basis: {record.basis}  (basis_version {record.basis_version})")
    if record.summary:
        console.print(record.summary, soft_wrap=True)

    if record.inputs:
        inputs = Table("Input", "Value", "Unit", "Fingerprint quantum", title="Inputs")
        for quantity in record.inputs:
            inputs.add_row(quantity.name, f"{quantity.value:,.6g}", quantity.unit,
                           "exact" if quantity.quantum is None else f"{quantity.quantum:g}")
        console.print(inputs)

    if record.limit_states:
        states = Table("Limit state", "Demand", "Capacity", "Ratio", "Citation",
                       title="Limit states")
        for state in record.limit_states:
            states.add_row(
                state.name, f"{state.demand:,.4g} {state.unit}",
                f"{state.capacity:,.4g} {state.unit}", f"{state.ratio:.3f}", state.citation)
        console.print(states)
        console.print(f"governing: {record.describe()}")

    if record.missing:
        console.print(f"[yellow]missing inputs: {', '.join(record.missing)}[/yellow]")
    for note in record.notes:
        console.print(f"  note: {note}", soft_wrap=True)

    state, signoff = register.freshness(record)
    label, colour = _seal_label(state, signoff)
    console.print(f"seal: [{colour}]{label}[/{colour}]"
                  + (f" — {signoff.scope} ({signoff.credit()})" if signoff else ""))
    if signoff and signoff.document:
        console.print(f"document: {signoff.document}")
    if record.status is not Status.NO_CALC:
        console.print(f"fingerprint: {compute_fingerprint(record)}")


_init_local()
