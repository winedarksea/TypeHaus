"""Parse a ``notes/*.md`` file into the three kinds of content a standard set separates.

The governing rule is CSI's: **drawings carry quantity, location and dimension;
specifications carry quality, performance and procedure**; and the reasoning behind a
decision belongs to neither — it is a design record. One catlin note file mixes all three::

    Roof framing: 11-7/8" TJI 230 @ 24" o.c.          → sheet note   (quantity)
    Bucks before foam; fillet, never butt square.     → specification (procedure)
    The spacing is NOT FINAL: the TJ-4000 table ...   → design record (why)

Authoring format — a body section, not frontmatter
--------------------------------------------------
``## Sheet notes`` is a heading in the body, above the existing ``# Notes``::

    ## Sheet notes
    ### General
    - Structural ridge beam; not a rafter-tie roof. Do not omit the LSSR hangers.
    ### Keyed
    - [K1 @ W-M-N-EXT#layer:sheathing:out] 5" closed-cell foam to deck underside.
    ### Spec 07 21 00
    - Install window bucks before spraying foam. Fillet against block sides.

    # Notes
    ...rationale, unchanged, below this line...

Frontmatter was the obvious alternative and is the wrong one. ``server/app.py``'s
``append_detail_note`` is a plain-text append gated on provenance; putting sheet notes in
YAML means parsing and re-emitting the whole block on every UI note. The frontmatter is
already load-bearing for ``applied_to``/``source``. And a 200-character imperative sentence
in a YAML scalar invites folded blocks, indentation bugs and quoting of the ``"`` marks that
every dimension in this house is written with.

Anything under ``## Sheet notes`` that is not under a recognised ``###`` subheading is a
**parse problem**, surfaced as a check finding. It is never silently swallowed.

This module is pure: text in, records out, no file I/O — the ``takeoff/calc_package.py``
discipline. The caller reads the file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from typehaus.emit.draw.note_text import banned_terms, clean, logical_bullets

#: The notes band a detail card actually prints into is 51 rows of 43 columns
#: (``detail_card.bands`` at ``NOTES_W_IN = 3.4`` through ``typography.wrap_columns_for``).
#: Every budget below is derived from that measurement, not chosen.
NOTE_COLUMNS = 43
MAX_SHEET_LINES = 48        #: wrapped rows, leaving the header and air
MAX_BULLET_CHARS = 200      #: ~4.6 wrapped rows; CSI's <=25 words lands well inside it
MAX_GENERAL = 10
MAX_KEYED = 16

_SECTION = re.compile(r"^\s*##\s+Sheet\s+notes\s*$", re.IGNORECASE)
_SUBHEAD = re.compile(r"^\s*###\s+(.+?)\s*$")
_ANY_H2 = re.compile(r"^\s*#{1,2}\s+")
#: ``[K1 @ W-M-N-EXT#layer:sheathing:out]`` — key, anchor uid, anchor face. Backticks are
#: tolerated around it because an author who writes markdown will reach for them.
_KEY = re.compile(
    r"^`?\[\s*(?P<key>[A-Za-z0-9]+)\s*(?:@\s*(?P<uid>[^\]#\s]+)"
    r"(?:#(?P<face>[^\]\s]+))?)?\s*\]`?\s*(?P<text>.*)$"
)
_SPEC_HEAD = re.compile(r"^spec\b\s*(?P<section>[0-9 ]{2,})?$", re.IGNORECASE)


@dataclass(frozen=True)
class SheetNote:
    """One note as it will print. ``key`` empty means a general note (no bubble)."""

    text: str
    key: str = ""
    anchor_uid: str = ""
    anchor_face: str = ""
    spec_section: str = ""

    @property
    def anchored(self) -> bool:
        return bool(self.key and self.anchor_uid)


@dataclass(frozen=True)
class SheetNoteSet:
    """What one notes file contributes to the set.

    ``legacy`` is populated only for a file with no ``## Sheet notes`` section — the whole
    body, sanitized and rejoined, exactly as the old loader would have printed it minus the
    markdown. ``problems`` are authoring errors for ``integrity.sheet_note_legibility``;
    they are strings, not ``Finding``s, because this package must not import ``checks``.
    """

    general: tuple[SheetNote, ...] = ()
    keyed: tuple[SheetNote, ...] = ()
    spec: tuple[SheetNote, ...] = ()
    legacy: tuple[str, ...] = ()
    problems: tuple[str, ...] = ()

    @property
    def authored(self) -> bool:
        """True when the file carries a ``## Sheet notes`` section at all."""
        return not self.legacy and bool(self.general or self.keyed or self.spec
                                        or self.problems)

    def sheet_lines(self) -> list[str]:
        """The ``Scene.notes`` payload: a header, the general notes, then the keyed ones.

        Specifications are deliberately absent — they belong on A-002/S-002, and printing
        them here is the duplication *say it once* exists to stop.
        """
        if self.legacy:
            return list(self.legacy)
        out: list[str] = ["NOTES:"]
        out.extend(f"• {n.text}" for n in self.general)
        if self.keyed:
            out.append("")
            out.append("KEYED NOTES:")
            out.extend(f"{n.key}  {n.text}" for n in self.keyed)
        return out if len(out) > 1 else []


def _split_frontmatter(raw: list[str]) -> list[str]:
    if raw and raw[0].strip() == "---":
        i = 1
        while i < len(raw) and raw[i].strip() != "---":
            i += 1
        return raw[min(i + 1, len(raw)):]
    return raw


def _subsection_kind(head: str) -> tuple[str, str]:
    """``("general"|"keyed"|"spec"|"", spec_section)`` for a ``###`` heading."""
    low = head.strip().lower()
    if low == "general":
        return ("general", "")
    if low == "keyed":
        return ("keyed", "")
    match = _SPEC_HEAD.match(low)
    if match:
        return ("spec", " ".join((match.group("section") or "").split()))
    return ("", "")


def parse_sheet_notes(text: str, *, source: str = "") -> SheetNoteSet:
    """Parse one note file's contents. Falls back to :func:`legacy_notes` when the file
    carries no ``## Sheet notes`` section — an *unmigrated* file, which the legibility check
    reports as UNKNOWN rather than passing."""
    body = _split_frontmatter(text.splitlines())
    start = next((i for i, line in enumerate(body) if _SECTION.match(line)), None)
    if start is None:
        return SheetNoteSet(legacy=tuple(legacy_notes(text)))

    end = len(body)
    for i in range(start + 1, len(body)):
        if _ANY_H2.match(body[i]) and not _SUBHEAD.match(body[i]):
            end = i
            break

    general: list[SheetNote] = []
    keyed: list[SheetNote] = []
    spec: list[SheetNote] = []
    problems: list[str] = []
    where = f"{source}: " if source else ""

    kind, section = "", ""
    pending: list[str] = []

    def flush() -> None:
        if not pending:
            return
        for bullet in logical_bullets(pending):
            _add(bullet, kind, section, general, keyed, spec, problems, where)
        pending.clear()

    for line in body[start + 1:end]:
        head = _SUBHEAD.match(line)
        if head:
            flush()
            kind, section = _subsection_kind(head.group(1))
            if not kind:
                problems.append(
                    f"{where}unknown '### {head.group(1).strip()}' under '## Sheet notes' "
                    f"(expected General, Keyed, or Spec <section>)")
            continue
        if not kind:
            if line.strip():
                problems.append(
                    f"{where}content under '## Sheet notes' before any "
                    f"'###' subheading: {line.strip()[:60]!r}")
            continue
        pending.append(line)
    flush()

    problems.extend(_budget_problems(general, keyed, where))
    return SheetNoteSet(tuple(general), tuple(keyed), tuple(spec), (), tuple(problems))


def _add(bullet: str, kind: str, section: str, general: list[SheetNote],
         keyed: list[SheetNote], spec: list[SheetNote], problems: list[str],
         where: str) -> None:
    match = _KEY.match(bullet)
    key = uid = face = ""
    if match:
        key = match.group("key")
        uid = match.group("uid") or ""
        face = match.group("face") or ""
        bullet = match.group("text")
    body = clean(bullet)
    if not body:
        return
    if kind == "keyed" and not key:
        problems.append(f"{where}keyed note has no [K#] prefix: {body[:60]!r}")
    if kind != "keyed" and key:
        problems.append(f"{where}[{key}] key on a non-keyed note: {body[:60]!r}")
        key = uid = face = ""
    if len(body) > MAX_BULLET_CHARS:
        problems.append(
            f"{where}note is {len(body)} chars (max {MAX_BULLET_CHARS}): {body[:60]!r}")
    banned = banned_terms(body)
    if banned:
        problems.append(f"{where}banned term(s) {', '.join(banned)} in: {body[:60]!r}")
    note = SheetNote(text=body, key=key, anchor_uid=uid, anchor_face=face,
                     spec_section=section)
    {"general": general, "keyed": keyed, "spec": spec}[kind].append(note)


def _budget_problems(general: list[SheetNote], keyed: list[SheetNote],
                     where: str) -> list[str]:
    out: list[str] = []
    if len(general) > MAX_GENERAL:
        out.append(f"{where}{len(general)} general notes (max {MAX_GENERAL})")
    if len(keyed) > MAX_KEYED:
        out.append(f"{where}{len(keyed)} keyed notes (max {MAX_KEYED})")
    seen: set[str] = set()
    for note in keyed:
        if note.key in seen:
            out.append(f"{where}duplicate keyed-note key {note.key}")
        seen.add(note.key)
    return out


def legacy_notes(text: str) -> list[str]:
    """The unmigrated path: the whole body as bullets, sanitized and hard-wraps rejoined.

    Same shape the old ``details._load_markdown_notes`` returned — a ``NOTES:`` header then
    one string per bullet — but with markdown, paths, test ids and typographic characters
    gone, and with a sentence the source wrapped at column 100 put back together.
    """
    body = _split_frontmatter(text.splitlines())
    out = ["NOTES:"]
    for bullet in logical_bullets(body):
        cleaned = clean(bullet)
        if cleaned:
            out.append(f"• {cleaned}")
    return out if len(out) > 1 else []


def wrapped_line_count(lines: list[str], columns: int = NOTE_COLUMNS) -> int:
    """Rows these logical lines occupy once wrapped into a ``columns``-wide band."""
    total = 0
    for line in lines:
        if not line:
            total += 1
            continue
        total += max(1, -(-len(line) // columns))
    return total
