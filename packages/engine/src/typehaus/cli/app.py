"""`haus` CLI (Typer) — the entry point module.

The command surface is split across ``cli/_shared.py`` (the app, console, and shared
helpers) and per-topic ``cmd_*`` modules that register onto it. This module keeps the
smaller commands, wires the sub-apps, and re-exports ``app``/``main`` — the packaging entry
point and every existing import path (``from typehaus.cli.app import app``) are unchanged.

The ``cmd_*`` imports below are the whole command list: importing a module is what registers
its commands, so a family that nobody imports is a family that silently vanishes from
``--help``. Their order is the order ``--help`` prints, so it is load-bearing — append, do
not reorder.
"""

from __future__ import annotations

# ``console`` is re-exported here because callers have imported it from this module for a while.
from typehaus.cli._shared import app, console  # noqa: F401
from typehaus.cli.variants import variants_app

app.add_typer(variants_app, name="variants")

# Importing these registers their commands on the shared ``app``. They are deliberately
# imported at module scope (the CLI must know its full command list to render --help) but
# each command body still imports the engine lazily.
from typehaus.cli import cmd_explain, cmd_takeoff  # noqa: E402,F401,I001  (registration order)
from typehaus.cli.cmd_build import build, check, energy, permit_check, version  # noqa: E402,F401
from typehaus.cli.cmd_assets import export, import_asset, import_project  # noqa: E402,F401
from typehaus.cli.cmd_sheets import _write_handoff_bundle, fmt, ls, print_sheets, render  # noqa: E402,F401
from typehaus.cli.cmd_diff import compare, diff  # noqa: E402,F401
from typehaus.cli.cmd_serve import _find_ui_dist, serve  # noqa: E402,F401
from typehaus.cli.cmd_new import new  # noqa: E402,F401


def main() -> None:
    app()


if __name__ == "__main__":
    main()
