"""The pieces every `haus` command shares: the Typer app, the console, and the two helpers
that turn a house argument and a findings list into output.

Commands live in per-topic ``cmd_*`` modules that register onto ``app`` here, rather than in
one 960-line ``app.py``. ``app`` and ``main`` stay importable from :mod:`typehaus.cli.app`
(the packaging entry point), so this split is invisible to installs.

Command bodies keep their imports *inside* the function: `haus --version` must not pay for
importing the resolver, the emitters, or ifcopenshell.
"""

from __future__ import annotations

import os
import sys
from enum import StrEnum
from pathlib import Path

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


class TierName(StrEnum):
    """Typer-facing mirror of :class:`typehaus.checks.registry.Tier`.

    Duplicated rather than imported because importing the registry drags in the whole
    checks package (~180 ms), which every `haus --version` would then pay for. Parity is
    pinned by ``tests/test_cli_check_output.py``.
    """

    integrity = "integrity"
    code = "code"
    advisory = "advisory"
    structural = "structural"
    building_science = "building_science"


class ExitOn(StrEnum):
    """What makes `haus check` exit non-zero.

    ``fail`` is the default: an ERROR-only gate can't see catlin's four advisory FAILs — the
    command would exit 0 while reporting failures, so no script could use it as a gate.
    """

    error = "error"
    fail = "fail"
    none = "none"


def _resolve_house(house: Path | None) -> Path:
    return (house or Path.cwd()).resolve()


def _detail(el: object) -> str:
    for attr in ("assembly", "host", "occupancy", "type_ref"):
        v = getattr(el, attr, None)
        if v is not None:
            return f"{attr}={getattr(v, 'value', v)}"
    return ""


def _plain_by_default() -> bool:
    """True when findings should print as bare lines: NO_COLOR, or stdout is not a tty.

    rich sizes a non-tty console at 80 columns and hard-wraps mid-sentence, which turns
    `haus check | grep` into a lie — half of every long finding lands on a continuation
    line that matches nothing. Piped output is machine-facing, so it gets one physical
    line per finding and no markup.
    """
    return bool(os.environ.get("NO_COLOR")) or not sys.stdout.isatty()


def _print_findings(findings: list, plain: bool | None = None) -> None:
    if plain is None:
        plain = _plain_by_default()
    if plain:
        for f in findings:
            print(f.render())
        return
    for f in findings:
        color = "red" if f.severity is Severity.ERROR else (
            "yellow" if f.result is Result.FAIL else "dim")
        console.print(f"[{color}]{f.render()}[/{color}]", soft_wrap=True)
