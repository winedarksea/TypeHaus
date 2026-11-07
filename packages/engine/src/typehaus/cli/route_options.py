"""The parsed ``haus route`` options a mode hands to its module, and the "not built" exit.

``cmd_route`` parses and validates; a mode module reads this and owns all behaviour.
Frozen so a mode cannot change what the next one sees. docs/routing.md."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

import typer

from typehaus.cli._shared import console

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.routing.cost import RouteCost


@dataclass(frozen=True)
class RouteOptions:
    """Everything ``route`` parsed that is not the mode's own target."""

    directory: Path  #: the house (plan/, prices, preferences)
    cost: RouteCost  #: [mep.routing] weights already converted
    out_dir: Path | None  #: --out; None writes nothing
    as_json: bool
    summary: bool  #: compact decision JSON (needs as_json + out_dir)
    explain: bool
    details: bool  #: collect per-proposal details (--explain, --json or --out)
    evaluate: bool  #: --evaluate OR --json
    margin_ft: float
    level: str | None  #: --level name
    band: tuple[float, float] | None  #: that storey's z band
    avoid: frozenset[str]
    via: tuple[tuple[float, float], ...]  #: --via points in metres
    slope: float | None  #: in/ft; None = code minimum
    alternatives: int
    timing: list[str] | None  #: --timing sink (append lines); None when off


def not_built(feature: str) -> NoReturn:
    """A stub's whole body: say so and exit 2, like any refused invocation."""
    console.print(f"[red]{feature}: not built yet[/red]")
    raise typer.Exit(2)
