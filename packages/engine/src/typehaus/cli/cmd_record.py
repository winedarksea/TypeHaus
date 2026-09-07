"""``haus record`` — the design record, as a folder of Markdown.

Its own command rather than a flag on ``haus print``, for the reason ``haus calcs`` is its
own command: this is a *deliverable with a different audience*. The permit set goes to a
reviewer and a builder; the calculation package goes to a licensed professional; the design
record goes to whoever changes the building next, which over the life of a house is the
largest of the three audiences and the only one currently served by reading the repository.

The markdown files stay where they are. This assembles them; it does not move them.
"""

from __future__ import annotations

from pathlib import Path

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, app, console


@app.command()
def record(
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    out: Path | None = typer.Option(
        None, "--out",
        help="Where to write the record (default: <house>/out/design-record)."),
) -> None:
    """Emit the design record: an index plus one page per note.

    Byte-deterministic — two runs over an unchanged model produce identical files — so the
    record is regenerated rather than maintained, and a diff between two runs is a real
    change in a note.
    """
    from datetime import date

    from typehaus._meta import engine_version
    from typehaus.emit.design_record import NoteSource, RecordInputs, design_record
    from typehaus.emit.notes_index import sheets_by_note
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    directory = _resolve_house(house)
    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)

    notes_dir = directory / "notes"
    if not notes_dir.is_dir():
        console.print(f"[yellow]{directory.name} has no notes/ directory[/yellow]")
        raise typer.Exit(0)

    model, _ = resolve(loaded.plan)
    on_sheets = sheets_by_note(model)
    # ``superseded/`` is deliberately included: a superseded note opens with a banner
    # naming what replaced it, and the rule it established usually outlives the design that
    # prompted it. That is exactly what a design record is for.
    sources = tuple(
        NoteSource(relative=f"notes/{path.relative_to(notes_dir).as_posix()}",
                   text=path.read_text(encoding="utf-8"),
                   on_sheets=tuple(on_sheets.get(
                       f"notes/{path.relative_to(notes_dir).as_posix()}", ())))
        for path in sorted(notes_dir.rglob("*.md"))
        if path.name not in ("README.md", "TEMPLATE.md")
    )
    files = design_record(RecordInputs(
        house=loaded.plan.project.name or directory.name,
        generated=date.today().isoformat(),
        engine_version=engine_version(),
        content_hash=loaded.content_hash,
        notes=sources,
    ))

    root = out if out is not None else directory / "out" / "design-record"
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")
    bound = sum(1 for s in sources if s.on_sheets)
    console.print(f"wrote {root} ({len(files)} files, {bound} of {len(sources)} notes "
                  f"reach a drawing)", soft_wrap=True)
