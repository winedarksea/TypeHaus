"""One load path for the three commands that answer engineering questions.

``haus engineering``, ``haus calcs`` and ``haus handoff`` all need the same five things: the
resolved context, the checks' report, the item list, the permit checklist and the register.
Each derived them for itself, and the ITEM LIST in particular is a judgement — the checks'
own ``engineering_item`` conclusions, unioned with the kinds that enumerate their own keys —
so three copies of it were three chances for the register, the calc package and the PE
bundle to disagree about what this house owes an engineer.

The item list is deliberately NOT the suite enumerating itself. Which requirements in a
house are outside the prescriptive path is a conclusion the checks reach — 7 feet of
unbalanced fill here, 3 feet next door — and a second enumeration living in the suite would
be the same judgement written twice, free to drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, console


@dataclass(frozen=True)
class EngineeringLoad:
    """Everything the three commands read, loaded once."""

    directory: Path
    loaded: Any
    """The ``LoadedPlan`` — ``content_hash`` rides on it, and every seal is pinned against it."""
    ctx: Any
    report: Any
    item_ids: tuple[str, ...]
    checklist: Any

    @property
    def results(self):  # type: ignore[no-untyped-def]
        return self.ctx.engineering

    @property
    def register(self):  # type: ignore[no-untyped-def]
        return self.ctx.engineering_register

    def records(self) -> list:
        return [self.results[item] for item in self.item_ids]


def load_engineering(house: Path | None, profile: str | None = None) -> EngineeringLoad:
    """Load, resolve, run the checks and derive the item list. Exits 1 on a load failure."""
    from typehaus.checks import build_context, evaluate_permit_checklist, run_checks
    from typehaus.source import load_plan

    directory = _resolve_house(house)
    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    ctx, _ = build_context(loaded.plan, directory, profile)
    report = run_checks(ctx)
    named = {f.engineering_item for f in report.findings if f.engineering_item}
    item_ids = tuple(sorted(named | set(ctx.engineering)))
    checklist = evaluate_permit_checklist(report, ctx.profile)
    return EngineeringLoad(directory=directory, loaded=loaded, ctx=ctx, report=report,
                           item_ids=item_ids, checklist=checklist)


def require_item(load: EngineeringLoad, item: str) -> None:
    """Refuse an item this house does not have, with the command that lists them."""
    if item in load.item_ids:
        return
    if item in load.results:
        return
    console.print(f"[red]{item}: no such engineering item in this house[/red]")
    console.print("[dim]run `haus engineering` for the list[/dim]")
    raise typer.Exit(1)
