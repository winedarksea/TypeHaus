"""``haus site validate`` and ``haus site migrate`` — the agent interface to site state.

There is no ``apply``, no ``changes``, no change journal. The agent editing ``tasks.toml``
and ``inspections.toml`` is Claude Code editing the TOML directly, ``git diff`` is the change
review, and this command is what says whether the edit describes a buildable sequence. The
same rules run at load and behind every ``PUT``, so a hand edit and a UI write are refused
in the same words.

``migrate`` is the one command here that writes, it writes in place, it prints every change
it made, and it refuses to invent: an ambiguous case is listed for review rather than
resolved. Historical ``done`` never becomes ``verified`` — that is the owner's own walk and
no migration can have done it for them.
"""

from __future__ import annotations

from pathlib import Path

import typer

from typehaus.cli._shared import _resolve_house, app, console

site_app = typer.Typer(help="Validate and migrate the site-state files.", no_args_is_help=True)
app.add_typer(site_app, name="site")


@site_app.command("validate")
def validate_site(house: Path | None = typer.Argument(None)) -> None:
    """Load both site-state files, derive the board, and report every rule it breaks."""
    from typehaus.cli.cmd_schedule import _board
    from typehaus.schedule.rules import validate

    directory = _resolve_house(house)
    model, board, _items = _board(directory)
    errors, warnings = validate(board, model)

    for warning in warnings:
        console.print(f"[yellow]warning[/yellow]  {warning}", soft_wrap=True)
    for error in errors:
        console.print(f"[red]error[/red]    {error}", soft_wrap=True)
    ready = sum(1 for r in board.readiness.values() if r.state == "ready")
    console.print(f"\n{len(board.visits)} visit(s), {ready} ready; "
                  f"{len(errors)} error(s), {len(warnings)} warning(s).")
    if errors:
        raise typer.Exit(1)


@site_app.command("migrate")
def migrate_site(
    house: Path | None = typer.Argument(None),
    write: bool = typer.Option(False, "--write",
                               help="Rewrite the files. Without it nothing is written."),
) -> None:
    """Fold the old spellings into the current ones, in place, and say what moved.

    ``[entries].status`` onto the implicit visit it describes; an inspection's single
    ``result``/``history`` slot into ``attempts``. Ids, dates, ticks and notes are preserved,
    and a package already split into visits with mixed status is *listed*, never resolved.
    """
    from typehaus.schedule.migrate import migrate

    directory = _resolve_house(house)
    changes, review = migrate(directory, write=write)
    for line in changes:
        console.print(f"[green]moved[/green]    {line}", soft_wrap=True)
    for line in review:
        console.print(f"[yellow]review[/yellow]   {line}", soft_wrap=True)
    if not changes and not review:
        console.print("Nothing to migrate.")
        return
    if not write:
        console.print("\n[dim]nothing written — re-run with --write[/dim]")
