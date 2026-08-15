"""`haus serve` — the FastAPI server plus the compiled browser app it delivers.

Split out of :mod:`typehaus.cli.app` at the seam that file already marked ("V6: serve
subcommand (cross-machine app delivery) — keep edits localized"). Honouring that note is the
point of this module: UI discovery and the command that consumes it now live in one file, so
the cross-machine delivery path can be edited without touching any other command.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from typehaus.cli._shared import _resolve_house, app, console


# --- V6: serve subcommand (cross-machine app delivery) — keep edits localized for V8 merge ---
def _find_ui_dist(explicit: Optional[Path]) -> Optional[Path]:
    """Locate a built UI (a directory holding ``index.html``) so one ``haus serve`` command can
    deliver the browser app on another machine (V6). An explicit ``--ui-dir`` is authoritative —
    it is used as-is (returns None if it lacks index.html, so the caller errors) and never falls
    back to discovery. Otherwise the ``TYPEHAUS_UI_DIST`` env var wins, then a walk up from the
    cwd and this package looks for a repo-root ``ui/dist``. Returns None when nothing is found."""
    import os

    def _valid(path: Path) -> Optional[Path]:
        return path.resolve() if (path / "index.html").is_file() else None

    if explicit is not None:
        return _valid(Path(explicit))
    env = os.environ.get("TYPEHAUS_UI_DIST")
    if env:
        return _valid(Path(env))
    for anchor in (Path.cwd(), Path(__file__).resolve()):
        node = anchor
        for _ in range(8):
            found = _valid(node / "ui" / "dist")
            if found is not None:
                return found
            if node.parent == node:
                break
            node = node.parent
    return None


@app.command()
def serve(
    house: Optional[Path] = typer.Argument(None),
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8765),
    ui: Optional[bool] = typer.Option(
        None, "--ui/--no-ui",
        help="Serve the compiled UI at / (default: on when a built ui/dist is found)."),
    ui_dir: Optional[Path] = typer.Option(
        None, "--ui-dir", help="Explicit built-UI directory (overrides auto-discovery)."),
) -> None:
    """Run the FastAPI server: model.json, PATCH /plan, undo/redo, live reload (WP2.1).

    Also serves the compiled browser app at ``/`` when a built ``ui/dist`` is present, so a
    user on another computer runs this one command and opens the house in a browser (V6)."""
    try:
        import uvicorn
    except ImportError as exc:
        console.print("[red]serve needs uvicorn: pip install 'typehaus[server]'[/red]")
        raise typer.Exit(2) from exc
    from typehaus.server.app import create_app

    d = _resolve_house(house)

    ui_dist: Optional[Path] = None
    if ui is not False:  # None (auto) or True → try to find a built UI
        ui_dist = _find_ui_dist(ui_dir)
        if ui_dist is None:
            if ui is True or ui_dir is not None:
                console.print(
                    "[red]--ui requested but no built UI found[/red] — run `npm run build` "
                    "in ui/ (or pass --ui-dir <dir>)")
                raise typer.Exit(2)
            console.print(
                "[yellow]no built UI found — serving API only.[/yellow] "
                "Run `npm run build` in ui/ to serve the app at /.")

    console.print(f"serving {d} on http://{host}:{port}")
    if ui_dist is not None:
        console.print(f"  app UI from {ui_dist} → open http://{host}:{port}/")
    uvicorn.run(create_app(d, ui_dist), host=host, port=port)
