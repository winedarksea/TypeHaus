"""The house's markdown notes, indexed — what each one is, and which sheets it reaches.

``houses/<name>/notes/*.md`` is where the design and product reasoning lives: why this
connector, what the ERV was actually certified at, which member the mill has to cut. Until
now the only programmatic reach into that folder was ``haus record``, which renders all of
it into a book. A reader that wants *one* note — the viewer's Notes tab, a contractor on an
iPad — needs a list first.

Pure and DOM-free in the same sense as the rest of ``emit``: it reads the notes directory
and the resolved model, and returns dataclasses. Nothing here writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # a type-only import; the runtime path never needs resolve/
    from typehaus.resolve import ResolvedModel

#: Files in ``notes/`` that are scaffolding rather than notes.
SKIP_NAMES = frozenset({"README.md", "TEMPLATE.md"})

#: The kinds, in reading order. ``brief`` is the house's own brief.md, which is not in
#: ``notes/`` at all but is the first thing anyone opening the folder should read.
KIND_ORDER = ("brief", "detail", "calc", "design", "superseded")


@dataclass(frozen=True)
class NoteEntry:
    """One markdown note as a list row."""

    #: Path relative to the house directory — ``brief.md`` or ``notes/<...>.md``.
    path: str
    title: str
    kind: str
    #: Sheet numbers this note's prose prints on (``Transition.notes`` → A-4xx + G-002).
    on_sheets: tuple[str, ...]
    chars: int

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "title": self.title, "kind": self.kind,
                "on_sheets": list(self.on_sheets), "chars": self.chars}


def sheets_by_note(model: ResolvedModel) -> dict[str, list[str]]:
    """``notes path -> sheet numbers``, from the same derivation G-002's index uses.

    One mapping, computed the one way: a record — or a reader — that disagreed with the
    sheet-note index about which sheet carries a note would be worse than one that said
    nothing. Lives here rather than in ``cli/cmd_record.py`` because two callers now want
    it and a CLI module is not a library.
    """
    from typehaus.emit.draw.callouts import detail_sheet_numbers
    from typehaus.emit.draw.details import derive_detail_slices

    numbers = detail_sheet_numbers(model)
    out: dict[str, list[str]] = {}
    for derived in derive_detail_slices(model):
        rel = getattr(derived.transition, "notes", None) if derived.transition else None
        sheet = numbers.get(derived.key)
        if rel and sheet:
            out.setdefault(rel, []).append(sheet)
    return out


def oracle_notes() -> set[str]:
    """The note *file names* the engineering register names as independent checks.

    ``typehaus.engineering`` is imported for its side effect: every calc module's
    ``oracled_by`` call registers on import, so an unimported register is an empty one
    (the pattern ``tests/test_calc_package.py`` uses).
    """
    import typehaus.engineering  # noqa: F401  — registers the oracles
    from typehaus.engineering.registry import oracles_for, registered_kinds

    return {oracle.note for kind in registered_kinds() for oracle in oracles_for(kind)}


def note_title(text: str, path: str) -> str:
    """The note's own title: frontmatter ``title:``, else its first ``# `` heading, else the
    file stem prettified.

    Frontmatter first because seven catlin notes open ``# Notes`` under a real
    ``title: "Backup Power — the ESS microgrid"`` — the heading is a section label inside a
    template, and reading it would list seven files all called "Notes".
    """
    from typehaus.emit.design_record import _split_frontmatter

    front, body = _split_frontmatter(text)
    for key, value in front:
        if key.strip().lower() == "title":
            declared = value.strip().strip('"').strip("'").strip()
            if declared:
                return declared
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
        if line.strip():
            break
    stem = Path(path).stem.replace("_", " ").replace("-", " ")
    return stem[:1].upper() + stem[1:]


def _declared_kind(text: str) -> str | None:
    """A ``kind:`` frontmatter field, when the note states one itself."""
    from typehaus.emit.design_record import _split_frontmatter

    front, _ = _split_frontmatter(text)
    for key, value in front:
        if key.strip().lower() == "kind":
            declared = value.strip().lower()
            if declared in KIND_ORDER:
                return declared
    return None


def notes_index(house_dir: Path, model: ResolvedModel | None = None) -> list[NoteEntry]:
    """Every note in the house, ``brief.md`` first, then ``notes/**.md`` in path order.

    ``model`` is optional only so a house that does not resolve still lists its notes; the
    "on sheet A-4xx" binding needs it, and without one every note simply reaches no sheet.
    """
    on_sheets = sheets_by_note(model) if model is not None else {}
    oracles = oracle_notes()
    entries: list[NoteEntry] = []

    brief = house_dir / "brief.md"
    if brief.is_file():
        text = brief.read_text(encoding="utf-8")
        entries.append(NoteEntry(path="brief.md", title=note_title(text, "brief.md"),
                                 kind="brief", on_sheets=(), chars=len(text)))

    notes_dir = house_dir / "notes"
    if notes_dir.is_dir():
        for path in sorted(notes_dir.rglob("*.md")):
            if path.name in SKIP_NAMES:
                continue
            rel = f"notes/{path.relative_to(notes_dir).as_posix()}"
            text = path.read_text(encoding="utf-8")
            sheets = tuple(on_sheets.get(rel, ()))
            entries.append(NoteEntry(path=rel, title=note_title(text, rel),
                                     kind=_declared_kind(text) or _kind_of(rel, path.name,
                                                                          sheets, oracles),
                                     on_sheets=sheets, chars=len(text)))
    return entries


def _kind_of(rel: str, name: str, sheets: tuple[str, ...], oracles: set[str]) -> str:
    """What this note *is*, from evidence rather than from a naming convention.

    Order matters. ``superseded/`` is a statement about the note's standing and outranks
    what it contains. A note a sheet prints is a construction note first — that is the copy
    a builder reads on the drawing — even when it also carries arithmetic. An oracle note is
    a calculation. Everything else is design reasoning.
    """
    if rel.startswith("notes/superseded/"):
        return "superseded"
    if sheets:
        return "detail"
    if name in oracles:
        return "calc"
    return "design"


def read_note(house_dir: Path, relative: str) -> str | None:
    """One note's markdown, or ``None`` if it is missing or outside the sandbox.

    Same provenance philosophy as ``POST /detail/notes``: the only readable paths are the
    house's own ``brief.md`` and markdown under its ``notes/`` directory. A client-supplied
    path is resolved and then checked against those two, so ``../pyproject.toml`` and a
    symlink out both come back as ``None`` rather than as a file.
    """
    root = house_dir.resolve()
    target = (root / relative).resolve()
    if target.suffix != ".md" or not target.is_file():
        return None
    if target == root / "brief.md":
        return target.read_text(encoding="utf-8")
    notes_root = root / "notes"
    if notes_root in target.parents:
        return target.read_text(encoding="utf-8")
    return None
