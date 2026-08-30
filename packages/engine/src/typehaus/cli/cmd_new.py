"""`haus new` — scaffold a house directory.

Split out of :mod:`typehaus.cli.app` by command family. It stays its own module rather than
joining the bundle commands because registration order is what ``haus --help`` prints, and
``new`` is authored last; :mod:`typehaus.cli.scaffold` holds the template writing this only
wraps.
"""

from __future__ import annotations

from pathlib import Path

import typer

from typehaus.cli._shared import app, console


@app.command()
def new(
    directory: Path = typer.Argument(..., help="new house directory to scaffold"),
    name: str = typer.Option("My House", help="project display name"),
    template: str = typer.Option(
        "starter", help="starter (small, buildable) | catlin (the real house, #22)"),
) -> None:
    """Scaffold a new house: brief.md, preferences.toml, plan/ skeleton (WP2.12, #22)."""
    from typehaus.cli.scaffold import scaffold_house

    created = scaffold_house(directory, name, template=template)
    for p in created:
        console.print(f"created {p}")
    console.print(f"[green]new house ready[/green] — try: haus serve {directory}")
