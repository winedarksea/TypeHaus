"""Collapse near-identical record text into one template plus the numbers that vary.

Twelve cast columns each print "LOAD COMBINATIONS: 1.4D -> Pu 2,163 lb, …" with their own
numbers, and ``04-assumptions.md`` was 22 pages of those. A reviewer disagrees with the
SENTENCE once; the numbers are per member. So text that is identical once its numeric
tokens and element tags are masked becomes one row, the tokens that differ become ``[1]``,
``[2]`` …, and a values table says what each member put there. Nothing is dropped:
:func:`expand` reproduces every original string, and a test holds it to that.

Deterministic by construction: groups and members are sorted, and nothing iterates a set.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from typehaus.emit.md_writer import table

#: A varying token: a number (``5,000``, ``2.77e+07``, ``22.4.2.1``) not glued to a word, or
#: an element tag (``PT-SG-BF1``). Clause numbers match too, and stay literal because they
#: do not vary across members.
_TOKEN = re.compile(
    r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)*(?:e[-+]?\d+)?(?![\w])"
    r"|\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")

_SLOT = "\x00"


@dataclass(frozen=True)
class Collapsed:
    """One template row. ``values`` is empty when every member said exactly the same thing."""

    template: str
    members: tuple[str, ...]
    #: ``(member, the varying tokens in slot order)``, one row per original string.
    values: tuple[tuple[str, tuple[str, ...]], ...] = ()


def _split(text: str) -> tuple[str, tuple[str, ...]]:
    return _TOKEN.sub(_SLOT, text), tuple(_TOKEN.findall(text))


def collapse(entries: Iterable[tuple[str, str]]) -> list[Collapsed]:
    """``(member, text)`` pairs to template rows, sorted by template.

    Only text reaching two or more members collapses; a string one member alone says is
    printed verbatim, because a template with one row of values is harder to read than
    the sentence it came from.
    """
    unique = sorted(set(entries))
    groups: dict[str, list[tuple[str, str, tuple[str, ...]]]] = {}
    for member, text in unique:
        skeleton, tokens = _split(text)
        groups.setdefault(skeleton, []).append((member, text, tokens))

    rows: list[Collapsed] = []
    for skeleton in sorted(groups):
        group = groups[skeleton]
        members = tuple(sorted({member for member, _, _ in group}))
        texts = sorted({text for _, text, _ in group})
        if len(texts) == 1:
            rows.append(Collapsed(texts[0], members))
            continue
        if len(members) == 1:
            rows.extend(Collapsed(text, members) for text in texts)
            continue
        width = len(group[0][2])
        varying = [i for i in range(width) if len({tokens[i] for _, _, tokens in group}) > 1]
        literal = group[0][2]
        pieces = skeleton.split(_SLOT)
        out = [pieces[0]]
        for i in range(width):
            out.append(f"[{varying.index(i) + 1}]" if i in varying else literal[i])
            out.append(pieces[i + 1])
        values = tuple((member, tuple(tokens[i] for i in varying))
                       for member, _, tokens in sorted(group, key=lambda g: (g[0], g[2])))
        rows.append(Collapsed("".join(out), members, values))
    return sorted(rows, key=lambda row: (row.template, row.members))


def expand(row: Collapsed) -> list[str]:
    """Every original string a row stands for — the proof that collapsing dropped nothing."""
    if not row.values:
        return [row.template]
    out = []
    for _member, tokens in row.values:
        text = row.template
        for slot, token in enumerate(tokens, start=1):
            text = text.replace(f"[{slot}]", token)
        out.append(text)
    return out


def values_line(tokens: Sequence[str]) -> str:
    """``[1] 2,163 · [2] 0 · …`` — a values cell that wraps, whatever the slot count."""
    return " · ".join(f"[{slot}] {token}" for slot, token in enumerate(tokens, start=1))


def reaching(members: Sequence[str], *, limit: int = 3) -> str:
    """The first few members, then a count — the register column a row reaches."""
    shown = ", ".join(f"`{member}`" for member in members[:limit])
    return shown + (f", … ({len(members)} items)" if len(members) > limit else "")


def collapsed_tables(rows: Sequence[Collapsed], *, label: str, prefix: str = "") -> str:
    """The template rows as one table, then one values table per row that has any."""
    blocks = [table(["#", label, "Items", "Reaching"],
                    [[f"{prefix}{n}", row.template, len(row.members), reaching(row.members)]
                     for n, row in enumerate(rows, start=1)])]
    for n, row in enumerate(rows, start=1):
        if row.values:
            blocks.append(f"**{prefix}{n}** — the numbers in [ ], by member:\n\n" + table(
                ["Member", "Values"],
                [[f"`{member}`", values_line(tokens)] for member, tokens in row.values]))
    return "\n\n".join(blocks)
