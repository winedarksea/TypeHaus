"""The pieces every `haus` command shares: the Typer app, the console, and the two helpers
that turn a house argument and a findings list into output.

Commands live in per-topic ``cmd_*`` modules that register onto ``app`` here, rather than in
one 960-line ``app.py``. ``app`` and ``main`` stay importable from :mod:`typehaus.cli.app`
(the packaging entry point), so this split is invisible to installs.

Command bodies keep their imports *inside* the function: `haus --version` must not pay for
importing the resolver, the emitters, or ifcopenshell.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from typehaus._meta import CLI_NAME, PROJECT_NAME, engine_version
from typehaus.findings import Result, Severity

app = typer.Typer(name=CLI_NAME, help=f"{PROJECT_NAME} — infrastructure as code for houses.",
                  no_args_is_help=True, add_completion=False)
console = Console()


def _version_flag(value: bool) -> None:
    if value:
        console.print(f"{PROJECT_NAME} engine {engine_version()}")
        raise typer.Exit(0)


@app.callback()
def _main(
    version: bool = typer.Option(
        False, "--version", callback=_version_flag, is_eager=True,
        help="Print the engine version and exit."),
) -> None:
    """`haus --version` — the packaging smoke every fresh install runs first."""


def _resolve_house(house: Optional[Path]) -> Path:
    return (house or Path.cwd()).resolve()


def _detail(el: object) -> str:
    for attr in ("assembly", "host", "occupancy", "type_ref"):
        v = getattr(el, attr, None)
        if v is not None:
            return f"{attr}={getattr(v, 'value', v)}"
    return ""


def _print_findings(findings: list) -> None:
    for f in findings:
        color = "red" if f.severity is Severity.ERROR else (
            "yellow" if f.result is Result.FAIL else "dim")
        console.print(f"[{color}]{f.render()}[/{color}]")
