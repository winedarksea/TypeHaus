"""Markdown → drawing text. Ordered sanitization passes, pure (text in, text out).

A design-rationale note is written for a reader with a scrollbar, a monospace font and a
link to click. A construction sheet has none of those. Every pass below exists because a
specific artefact of the first medium printed verbatim onto a sheet in the second:

``[the eave detail](notes/roof_wall_eave_detail.md)``
    printed the brackets, the parentheses and a house-relative path onto A-402.
```` `test_the_catlin_eave_is_a_two_page_detail` ````
    a pytest id, with backticks, on a permit drawing.
``**BOTH HALVES ARE NOW BUILT**``
    four asterisks a builder reads as a footnote marker.
``—`` / ``≥``
    outside the DXF writer's code page; they land as ``?`` or nothing at all.
A source hard wrap
    ``• Interior sauna liner (walls + ceiling): 2" foil-faced polyiso`` then a new bullet
    reading ``(taped seams).`` — the note file wrapped at 100 columns and the loader turned
    each physical line into a logical one.

**No auto-uppercasing.** It was tried and it destroys the units a structural note is made
of: ``ksi``, ``MC``, ``R-30C``, ``psf/ft``.
"""

from __future__ import annotations

import re

#: ``[text](target)`` → ``text``. The target is a repo path or a URL either way; neither is
#: something a builder standing at the wall can follow.
_LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")

#: A code span. Every one is matched by this and then *classified* by
#: :func:`_is_repo_reference`. Deciding with one pattern per outcome was tried and is
#: subtly wrong: a "drop" pattern anchored on ``/`` matched from the backtick that CLOSES
#: one span to the backtick that OPENS the next, swallowing the prose between them —
#: ``CATLIN_BASEMENT_12` and `CATLIN_BASEMENT_8` therefore carry ... (`coating-acrylic``
#: came out of the basement detail as ``CATLIN_BASEMENT_12 and CATLIN_BASEMENT_8coating``.
_CODE_ANY = re.compile(r"`([^`]*)`")

#: A code span that is a *repository* reference — a path, a pytest id, a module — and so
#: means nothing to a builder at the wall. Dropped whole. A bare
#: ``test_garage_overhead_door_opens_from_the_slab_at_grade`` has neither an extension nor
#: a ``::``, and it printed on the garage detail anyway.
_REPO_REF = re.compile(
    r"^(?:[^\s]*(?:\.(?:md|py|toml|json|ts|tsx)\b|::)[^\s]*|test_[A-Za-z0-9_]*)$")

#: Bold/italic runs. Longest first, so ``**x**`` does not leave a stray pair behind.
_EMPH = re.compile(r"\*{1,3}(?=\S)(.+?)(?<=\S)\*{1,3}")

#: A markdown table row, a blockquote, or a fence line. None of the three survives being
#: re-flowed into a 43-column note band, and a fenced block is code by definition.
_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_RULE = re.compile(r"^\s*\|?[\s:-]*-{2,}[\s:|-]*$")
_BLOCKQUOTE = re.compile(r"^\s*>")
_FENCE = re.compile(r"^\s*(```|~~~)")

#: Bullet openers, both spellings.
_BULLET = re.compile(r"^\s*[-*+]\s+")

#: An ordered-list opener: ``1. ``/``2) ``.
_ORDERED = re.compile(r"^\s*\d+[.)]\s+")

#: Non-ASCII the DXF writer cannot set, and what to set instead. ``•`` is deliberately
#: absent: both writers indent continuation lines off it, so it is load-bearing.
_FOLD = {
    "—": "--", "–": "-", "−": "-",
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "≥": ">=", "≤": "<=", "≠": "!=", "≈": "~",
    "×": "x", "°": " deg", "→": "->", " ": " ",
    "…": "...", "½": "1/2", "¼": "1/4", "¾": "3/4",
    "±": "+/-", "′": "'", "″": '"', "®": "", "™": "",
}

#: Words CSI bans from a construction note. Reported, never silently rewritten — the fix is
#: a decision about the requirement, not a synonym.
BANNED_WORDS = (
    "adequate", "as required", "as directed", "best", "workmanlike",
    "etc.", "and/or", "should", "to the satisfaction of", "any and all",
)

_LEADING_PREP = re.compile(r"\s*\b(?:see|per|from|in|at)\s+(?=[,;.)]|$)", re.IGNORECASE)


def fold_ascii(text: str) -> str:
    """Replace the typographic characters the DXF code page cannot set."""
    for src, dst in _FOLD.items():
        text = text.replace(src, dst)
    return "".join(ch for ch in text if ch == "•" or ord(ch) < 128)


def _uncode(match: re.Match[str]) -> str:
    """One code span: dropped if it is a repository reference, unticked otherwise.

    An identifier a reader can still act on — an assembly tag, a material ref, a field
    name — keeps its text, because a builder holding the drawing and the schedule can look
    ``CATLIN_BASEMENT_8`` up. ``plan/storeys/basement.py`` they cannot.
    """
    body = match.group(1)
    return "" if _REPO_REF.match(body.strip()) else body


def strip_markdown(text: str) -> str:
    """Links, code spans and emphasis out; the sentence's words left standing."""
    text = _LINK.sub(r"\1", text)
    text = _CODE_ANY.sub(_uncode, text)
    text = _EMPH.sub(r"\1", text)
    return text


def collapse_space(text: str) -> str:
    """One space between words; no space before punctuation an empty span left orphaned."""
    text = _LEADING_PREP.sub("", text)
    text = re.sub(r"\s+", " ", text)
    # A parenthetical whose whole content was a dropped path leaves "( -- )" or "(,)".
    text = re.sub(r"\s*\(\s*(?:--|[-,;:])?\s*\)", "", text)
    text = re.sub(r"\s*--\s*([,.;)])", r"\1", text)
    text = re.sub(r"\.\s*\.(?=\s|$)", ".", text)
    text = re.sub(r"\s+([,;.:)])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"(?:,\s*){2,}", ", ", text)
    text = re.sub(r"\s*--\s*--\s*", " -- ", text)
    # A dropped opener ("See `notes/x.md`. The cavity...") leaves the sentence starting
    # on its predecessor's full stop. Only the *leading* period goes — a trailing one
    # ends a real sentence.
    return text.lstrip(" \t,;.").rstrip(" \t,;")


def clean(text: str) -> str:
    """The full pass, in order. Markdown first: folding ``—`` before it would not matter,
    but stripping a link *after* folding would leave a folded path behind."""
    return collapse_space(fold_ascii(strip_markdown(text)))


def is_droppable(line: str) -> bool:
    """A physical line that carries no sentence: a table row, quote, fence or rule."""
    stripped = line.strip()
    if not stripped:
        return False
    return bool(
        _TABLE_ROW.match(line) or _TABLE_RULE.match(line)
        or _BLOCKQUOTE.match(line) or _FENCE.match(line)
    )


def logical_bullets(lines: list[str]) -> list[str]:
    """Rejoin source hard wraps into one string per authored bullet.

    A bullet opener starts a new logical line; every following non-blank, non-opener line is
    a continuation of it and is joined with a single space. A blank line inside a bullet
    ends it — that is how the markdown reads, and how a nested paragraph under a bullet
    stays its own note rather than a 3,040-character run-on.
    """
    out: list[str] = []
    fenced = False
    for raw in lines:
        if _FENCE.match(raw):
            fenced = not fenced
            continue
        if fenced or is_droppable(raw):
            continue
        stripped = raw.strip()
        if not stripped:
            out.append("")
            continue
        if stripped.startswith("#"):
            out.append("")
            continue
        opener = _BULLET.match(stripped) or _ORDERED.match(stripped)
        if opener:
            out.append(stripped[opener.end():].strip())
        elif out and out[-1]:
            out[-1] = f"{out[-1]} {stripped}"
        else:
            out.append(stripped)
    return [b for b in out if b]


def banned_terms(text: str) -> list[str]:
    """Which of :data:`BANNED_WORDS` this note uses, in catalogue order."""
    low = text.lower()
    return [w for w in BANNED_WORDS if w in low]
