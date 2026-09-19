"""Markdown -> Platypus flowables. The one place this repo parses its own calc markdown.

Kept apart from :mod:`typehaus.takeoff.calc_pdf` because the two answer different questions:
this one is "what is on the page", that one is "where does the page go and what is stamped
around it". Splitting them is also what makes the parser testable without building a PDF.

** THE PARSER THIS REPLACES DID NOT PARSE. ** It was a line-oriented ``textwrap`` pass that
printed a table's pipes literally, truncated every line at ``COLUMNS + 24`` characters
(305 lines of catlin's package sat at that cap, the longest source row 860 characters, and
the overflow was dropped silently), and had no notion of a paragraph. The restriction was
not matplotlib's text engine so much as the absence of any layout model at all.

The dialect is deliberately narrow — exactly what ``takeoff/markdown.py`` emits: ATX
headings, paragraphs, ``-`` bullets, pipe tables with a separator row, fenced code, ``---``
rules, and ``**bold**`` / ``` `code` ``` inline. Anything else passes through as text
rather than being guessed at.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_RULE = re.compile(r"^\s*([-*_])\1{2,}\s*$")
_BULLET = re.compile(r"^(\s*)[-*•]\s+(.*)$")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_CODE = re.compile(r"`([^`]+)`")
#: ``_like this_`` — ``takeoff/markdown.py``'s italic, used for the "nothing is missing"
#: line on every complete sheet. Underscore-delimited only, and bounded by non-word
#: characters, because a bare ``*`` is a bullet and ``snake_case_names`` are everywhere in
#: a calc sheet: matching those would italicise half of every element tag.
_ITALIC = re.compile(r"(?<![A-Za-z0-9_])_([^_\n]+)_(?![A-Za-z0-9_])")


@dataclass(frozen=True)
class Heading:
    """One heading, and the anchor a bookmark and an internal link both point at."""

    level: int
    text: str
    anchor: str


@dataclass(frozen=True)
class Paragraph_:
    text: str


@dataclass(frozen=True)
class Bullets:
    items: tuple[str, ...]


@dataclass(frozen=True)
class Table_:
    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class Code:
    lines: tuple[str, ...]


@dataclass(frozen=True)
class Rule:
    pass


Block = Heading | Paragraph_ | Bullets | Table_ | Code | Rule


def anchor_for(name: str, index: int) -> str:
    """A stable, unique anchor id. Deterministic, because the PDF has to be."""
    safe = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    return f"{safe}_{index}"


def parse(markdown: str, *, source: str = "") -> list[Block]:
    """Markdown to blocks. Pure, and it never drops input."""
    blocks: list[Block] = []
    lines = markdown.splitlines()
    i = 0
    para: list[str] = []
    bullets: list[str] = []
    counter = 0

    def flush() -> None:
        nonlocal para, bullets
        if para:
            blocks.append(Paragraph_(" ".join(para).strip()))
            para = []
        if bullets:
            blocks.append(Bullets(tuple(bullets)))
            bullets = []

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        if stripped.startswith("```"):
            flush()
            i += 1
            body: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i].rstrip())
                i += 1
            blocks.append(Code(tuple(body)))
            i += 1
            continue

        head = _HEADING.match(stripped)
        if head:
            flush()
            counter += 1
            text = head.group(2).strip()
            blocks.append(Heading(len(head.group(1)), text,
                                  anchor_for(source or text, counter)))
            i += 1
            continue

        if _RULE.match(raw):
            flush()
            blocks.append(Rule())
            i += 1
            continue

        # A pipe table: a header row, a separator row, then body rows. The separator is
        # what distinguishes a table from a line that merely contains a pipe.
        if stripped.startswith("|") and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
            flush()
            header = _cells(stripped)
            i += 2
            rows: list[tuple[str, ...]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_cells(lines[i].strip()))
                i += 1
            blocks.append(Table_(header, tuple(rows)))
            continue

        bullet = _BULLET.match(raw)
        if bullet:
            if para:
                blocks.append(Paragraph_(" ".join(para).strip()))
                para = []
            bullets.append(bullet.group(2).strip())
            i += 1
            continue

        if not stripped:
            flush()
            i += 1
            continue

        # A continuation line of the bullet above it, not a new paragraph.
        if bullets and raw.startswith(("  ", "\t")):
            bullets[-1] = f"{bullets[-1]} {stripped}"
            i += 1
            continue

        if bullets:
            flush()
        para.append(stripped)
        i += 1

    flush()
    return blocks


def _cells(row: str) -> tuple[str, ...]:
    return tuple(cell.strip() for cell in row.strip().strip("|").split("|"))


def inline(text: str) -> str:
    """Markdown inline emphasis to Platypus' mini-HTML, XML-escaped first.

    Escaping first and marking up second is the order that matters: a calc sheet is full of
    ``<=`` and ``&`` and a bare ``<`` would otherwise take Platypus' parser down or, worse,
    silently eat the rest of the line.
    """
    out = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    out = _BOLD.sub(r"<b>\1</b>", out)
    out = _ITALIC.sub(r"<i>\1</i>", out)
    out = _CODE.sub(r'<font face="Courier" size="8.2">\1</font>', out)
    return out
