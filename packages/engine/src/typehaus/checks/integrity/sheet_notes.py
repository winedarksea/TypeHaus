"""A construction note has to be legible on the sheet it prints on.

INTEGRITY tier, and the same family as ``integrity.reveal_concentric``: the model says
something it cannot mean. A ``Transition.notes`` file whose bullets run to 3,040 characters
is not a long note — it is a note that will not print, and the model asserting it will is
the defect. So is a repository path on a permit drawing, or a pytest id, or four asterisks
a builder reads as a footnote marker. Each of those was measured on catlin's own sheets
before ``emit/draw/sheet_notes.py`` existed: 296 note lines and 22,626 characters on one
detail, markdown syntax and house-relative paths printed verbatim.

**Subject.** Every distinct markdown file a ``Transition.notes=`` names. A note file that
no transition binds reaches no drawing (five of catlin's do not) and is out of this rule's
subject rather than a gap in it.

**Grade.** The budgets in ``emit/draw/sheet_notes.py``, which are measured off the band the
writer actually prints into — ask ``pdf_writer.note_pages`` how many rows it puts on one
page and the answer is 36 of 43 columns. A bullet over ``MAX_BULLET_CHARS``, a wrapped
total over ``MAX_SHEET_LINES``, a surviving path or test id or backtick or table row, a
parse error, a duplicate key: all FAIL, severity ERROR, so ``checks/permit.py`` gates on
them.

**UNKNOWN, deliberately, for a file with no ``## Sheet notes`` section.** The legacy path
is in use and the whole body is being sanitized onto the sheet. That is *better* than what
it replaced and it is not a pass: the rule cannot tell whether what survived is a
construction note or an argument about one, and a rule that cannot evaluate is UNKNOWN
(→ decision #32).

**NOT_APPLICABLE when no transition binds a notes file at all** — the starter house. Earned
from positive evidence of absence, per ``Result``'s contract, and never returned as ``[]``.
"""

from __future__ import annotations

import re
from pathlib import Path

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.emit.draw.sheet_notes import (
    MAX_SHEET_LINES,
    parse_sheet_notes,
    wrapped_line_count,
)
from typehaus.findings import Finding, failed, not_applicable, passed, unknown

_CHECK_ID = "integrity.sheet_note_legibility"

#: Artefacts of the authoring medium that must never reach a sheet, and what to call each
#: one in the finding. Every pattern here was measured on a real catlin sheet.
_ARTEFACTS = (
    (re.compile(r"`"), "a backtick"),
    (re.compile(r"\*\*"), "bold markdown"),
    (re.compile(r"\]\("), "a markdown link"),
    (re.compile(r"\S+\.(?:md|py|toml|json)\b"), "a repository path"),
    (re.compile(r"::"), "a pytest id"),
    (re.compile(r"^\s*\|.*\|\s*$"), "a table row"),
    (re.compile(r"[^\x00-\x7f•]"), "a character the DXF writer cannot set"),
)


def _bound_note_files(ctx: CheckContext) -> dict[str, Path]:
    """``relative path -> absolute path`` for every notes file a transition binds.

    Read off ``Transition.notes`` rather than off the directory: ``applied_to`` frontmatter
    is not the test and never was — several catlin notes carry it and render nowhere, which
    is what ``notes/README.md`` used to get wrong.
    """
    root = ctx.model.plan.source_root
    if not root:
        return {}
    out: dict[str, Path] = {}
    for transition in ctx.model.plan.library.transitions:
        rel = getattr(transition, "notes", None)
        if not rel or rel in out:
            continue
        path = Path(root) / rel
        if path.exists():
            out[rel] = path
    return out


@check(Tier.INTEGRITY, _CHECK_ID)
def sheet_note_legibility(ctx: CheckContext) -> list[Finding]:
    files = _bound_note_files(ctx)
    if not files:
        return [not_applicable(
            _CHECK_ID,
            "no transition in this building names a notes file, so no note reaches a "
            "sheet and there is nothing to grade")]

    findings: list[Finding] = []
    for rel, path in sorted(files.items()):
        tag = Path(rel).stem
        notes = parse_sheet_notes(path.read_text(encoding="utf-8"), source=Path(rel).name)

        if not notes.authored:
            findings.append(unknown(
                _CHECK_ID,
                f"{rel} carries no '## Sheet notes' section, so its whole body is being "
                f"sanitized onto the sheet. What prints is legible; whether it is a "
                f"construction note or an argument about one, this rule cannot tell",
                (tag,), fix="split it per emit/draw/sheet_notes.py"))
            continue

        problems = list(notes.problems)
        lines = notes.sheet_lines()
        rows = wrapped_line_count(lines)
        if rows > MAX_SHEET_LINES:
            problems.append(
                f"{rows} wrapped rows against a {MAX_SHEET_LINES}-row page — the notes "
                f"take a second page")
        problems.extend(_artefacts_in(lines))

        if problems:
            findings.append(failed(
                _CHECK_ID, f"{rel}: " + "; ".join(problems[:4])
                + (f" (+{len(problems) - 4} more)" if len(problems) > 4 else ""),
                (tag,), fix="see emit/draw/sheet_notes.py for the budgets"))
        else:
            findings.append(passed(
                _CHECK_ID,
                f"{rel}: {len(notes.general)} general + {len(notes.keyed)} keyed notes, "
                f"{rows} of {MAX_SHEET_LINES} rows, no markdown or repository reference",
                (tag,)))
    return findings


def _artefacts_in(lines: list[str]) -> list[str]:
    """One problem per artefact KIND, not per occurrence.

    A file that never migrated has a backtick on every line, and forty identical findings
    say nothing forty times. The first offending line is quoted so the author can find it.
    """
    found: list[str] = []
    for pattern, name in _ARTEFACTS:
        hit = next((line for line in lines if pattern.search(line)), None)
        if hit is not None:
            found.append(f"{name} reaches the sheet: {hit[:60]!r}")
    return found
