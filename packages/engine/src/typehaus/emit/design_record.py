"""The design record — why the building is what it is, published as its own document.

CSI splits construction documents two ways: **drawings carry quantity, location and
dimension; specifications carry quality, performance and procedure.** A third kind of
content lives in this house's ``notes/*.md`` files and belongs to neither::

    Roof framing: 11-7/8" TJI 230 at 24" o.c.        → sheet note   (quantity)
    Bucks before foam; fillet, never butt square.    → specification (procedure)
    The spacing is NOT FINAL: the TJ-4000 table ...  → design record (why)

That third kind is the most valuable writing in the repository and the least suited to a
construction sheet. It is the argument — what was considered, what it replaced, what it
cost, what is still open. A builder standing at a wall cannot use it; the next person to
change the wall cannot work without it.

So it gets a document of its own, and **the markdown files do not move**. Agents and
people keep reading them in place; this emitter assembles them into something a human can
hand over, with a banner saying what it is not.

Pure — ``{relative path: markdown}`` out, no file I/O, the ``takeoff/calc_package.py``
discipline. The CLI does the only writing, and the output is byte-deterministic so the
record is regenerated rather than maintained and a diff between two runs is a real change.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Printed at the top of every page. A design record is not a contract document and must
#: not be mistaken for one — a note in it may describe a scheme that was rejected, a cost
#: that was not taken, or an option still open.
BANNER = (
    "> **This is a design record, not a contract document.** It is the reasoning behind "
    "the drawings — including options that were rejected and questions that are still "
    "open. Nothing here is a construction instruction. Build from the drawings and the "
    "specifications."
)


@dataclass(frozen=True)
class NoteSource:
    """One ``notes/*.md`` file, as read by the caller."""

    relative: str          #: e.g. ``notes/roof_wall_eave_detail.md``
    text: str
    on_sheets: tuple[str, ...] = ()   #: sheet numbers whose details this note reaches


@dataclass(frozen=True)
class RecordInputs:
    house: str
    generated: str
    engine_version: str
    content_hash: str
    notes: tuple[NoteSource, ...]


def design_record(inputs: RecordInputs) -> dict[str, str]:
    """``{relative path: markdown}`` for the whole record, sorted."""
    files = {"index.md": _index(inputs)}
    for note in inputs.notes:
        files[f"{_stem(note.relative)}.md"] = _page(inputs, note)
    return dict(sorted(files.items()))


def _stem(relative: str) -> str:
    return relative.rsplit("/", 1)[-1].removesuffix(".md")


def _title(relative: str) -> str:
    return _stem(relative).replace("_", " ").title()


def _index(inputs: RecordInputs) -> str:
    """Cover and contents, split by whether a note reaches a drawing.

    The split is the useful one: a note bound by a ``Transition.notes=`` is *drawing
    content* whose sheet notes are on the set and whose argument is here, while everything
    else renders nowhere and is only here. A reader wanting to know why a detail says what
    it says looks in the first list.
    """
    # Sorted, not in input order: the record is regenerated rather than maintained, so a
    # diff between two runs must be a real change in a note and never a change in the order
    # the caller happened to read the directory in.
    ordered = sorted(inputs.notes, key=lambda n: n.relative)
    drawing = [n for n in ordered if n.on_sheets]
    other = [n for n in ordered if not n.on_sheets]
    lines = [
        f"# {inputs.house} — design record",
        "",
        BANNER,
        "",
        f"Generated {inputs.generated} · engine {inputs.engine_version} · "
        f"model `{inputs.content_hash[:12]}`",
        "",
        f"{len(inputs.notes)} note(s). Regenerated, never edited — the source is "
        "`notes/*.md` in the house, which is where to make a change.",
        "",
    ]
    if drawing:
        lines += ["## Behind a drawing", "",
                  "Each of these is bound to a detail by a `Transition.notes=`. Its sheet "
                  "notes print on the sheets named; the argument below them is here.", ""]
        lines += [f"- [{_title(n.relative)}]({_stem(n.relative)}.md) — "
                  f"{_sheet_span(n.on_sheets)}" for n in drawing]
        lines.append("")
    if other:
        lines += ["## Not on any drawing", "",
                  "Reasoning, calculation oracles and decisions that reach no sheet.", ""]
        lines += [f"- [{_title(n.relative)}]({_stem(n.relative)}.md)" for n in other]
        lines.append("")
    return "\n".join(lines)


def _sheet_span(sheets: tuple[str, ...]) -> str:
    """``A-509`` / ``A-522, A-523`` / ``A-510..A-578 (7 sheets)``.

    Same rule G-002's index uses: a note bound to a whole assembly pattern reaches a dozen
    sheets, and printing all twelve numbers is a wall of text where a range says it.
    """
    ordered = sorted(set(sheets))
    if len(ordered) > 3:
        return f"{ordered[0]}..{ordered[-1]} ({len(ordered)} sheets)"
    return ", ".join(ordered)


def _page(inputs: RecordInputs, note: NoteSource) -> str:
    """One note: a header block from its frontmatter, then the body verbatim.

    **Verbatim** is the whole point. This emitter reformats nothing — no wrapping, no
    sanitizing, no heading demotion. The sheet-note path in ``emit/draw/note_text.py`` does
    all of that because a construction sheet is a hostile medium; a design record is read
    the same way the file is, so anything done to it here can only lose something.
    """
    front, body = _split_frontmatter(note.text)
    lines = [f"# {_title(note.relative)}", "", BANNER, "",
             f"Source: `{note.relative}`"]
    if note.on_sheets:
        lines.append(f"Sheet notes from this file print on {_sheet_span(note.on_sheets)}.")
    lines.append("")
    if front:
        lines += ["| Field | Value |", "|---|---|"]
        lines += [f"| {key} | {value} |" for key, value in front]
        lines.append("")
    lines += ["---", "", body.strip(), ""]
    return "\n".join(lines)


def _split_frontmatter(text: str) -> tuple[list[tuple[str, str]], str]:
    """``([(key, value)], body)``. A flat read, deliberately not a YAML parse.

    The frontmatter here is a handful of scalars and short lists, and the record only ever
    displays them. Taking a YAML dependency to render a table would buy nothing and would
    make an emitter fail on a file a human can still read.
    """
    raw = text.splitlines()
    if not raw or raw[0].strip() != "---":
        return ([], text)
    end = next((i for i in range(1, len(raw)) if raw[i].strip() == "---"), None)
    if end is None:
        return ([], text)
    fields: list[tuple[str, str]] = []
    key = ""
    for line in raw[1:end]:
        if not line.strip():
            continue
        if line.startswith((" ", "\t", "-")):
            # A continuation or a list item — fold it onto the field it belongs to rather
            # than inventing a key for it.
            if fields:
                joined = f"{fields[-1][1]} {line.strip().lstrip('- ')}".strip()
                fields[-1] = (fields[-1][0], joined)
            continue
        key, _, value = line.partition(":")
        fields.append((key.strip(), value.strip().strip('"')))
    return (fields, "\n".join(raw[end + 1:]))
