"""``haus route --group``: one fixture group laid as ordered steps (908.2 wet vent).

STUB: E2 fills this. docs/routing.md."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.cli.route_options import RouteOptions, not_built

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel


def route_group(model: ResolvedModel, group: str, opts: RouteOptions) -> int:
    """Lay ``group`` (a fixture-group tag or a room) and report; return the exit code.

    Owns its own reporting (``route_report.report_proposals`` with ``opts``): each laid
    step is re-resolved before the next, so no single proposal list exists up front.
    Raise ``typer.Exit(2)`` for a ``group`` that names nothing; ``opts.out_dir`` is already
    validated outside the house's plan/."""
    not_built("--group")
