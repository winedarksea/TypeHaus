"""Deterministic GitHub-flavoured Markdown — the engine's one prose exit.

The sibling of :mod:`emit.csv_writer`, and held to the same discipline for the same reason.
CSV reaches an estimating package; Markdown reaches a *person* — a mill, a plan reviewer, a
professional engineer being asked to seal a calculation — and the moment two places in the
repo render a table their own way, a reader comparing two of this engine's documents is
comparing two dialects.

Determinism, concretely: one newline convention, one float format, one escaping rule, rows
in the order given, and no blank-line heuristics. Two runs over the same data are the same
bytes, which is what makes ``haus calcs`` regenerable rather than a thing somebody has to
diff by eye.

Escaping is narrow on purpose. Only ``|`` and a newline can break a GFM table cell, so only
those are touched; a citation like ``ACI 318-19 §10.6.1.1`` and an assumption written with
an asterisk both survive verbatim, because mangling an engineer's prose to protect a table
is the wrong trade.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

#: LF, and a single trailing newline on a rendered document. Same reasoning as
#: ``csv_writer.NEWLINE``: a file whose line ending moves with the platform cannot be
#: diffed or committed.
NEWLINE = "\n"


def format_value(value: Any) -> str:
    """One cell or one value, rendered the same way everywhere.

    Floats get 6 significant figures unless they are integral. That is a deliberate step
    away from ``csv_writer``'s fixed 2 decimals: these are engineering quantities, not
    money, and a bearing pressure of 0.0034 ksi must not print as ``0.00``.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            return "—"
        return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.6g}"
    return str(value)


def escape_cell(text: str) -> str:
    """A table cell: pipes escaped, newlines folded to a space.

    A folded newline is not a loss — a cell cannot hold one in GFM at all, so the choice is
    between one line and a broken table.
    """
    return text.replace("|", "\\|").replace("\r\n", " ").replace("\n", " ").strip()


def heading(text: str, level: int = 1) -> str:
    """``## text`` — one blank line after, never before; the caller joins."""
    return f"{'#' * max(1, min(level, 6))} {text}"


def table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    """A GFM table. Every row is padded or truncated to ``headers``.

    Projecting through ``headers`` is the same contract ``csv_writer.render_rows`` keeps:
    the column list is authored once at the call site, and no row can widen the table.
    """
    width = len(headers)
    lines = ["| " + " | ".join(escape_cell(str(h)) for h in headers) + " |",
             "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        cells = [escape_cell(format_value(value)) for value in row][:width]
        cells += [""] * (width - len(cells))
        lines.append("| " + " | ".join(cells) + " |")
    return NEWLINE.join(lines)


def dict_table(headers: Sequence[str], rows: Iterable[Mapping[str, Any]],
               keys: Sequence[str] | None = None) -> str:
    """:func:`table` over dict rows, projected through ``keys`` (default: ``headers``)."""
    names = list(keys if keys is not None else headers)
    return table(headers, [[row.get(name) for name in names] for row in rows])


def kv_block(pairs: Iterable[tuple[str, Any]], *, skip_empty: bool = True) -> str:
    """``**Label:** value`` lines — a header block, not a table.

    A two-column table of five rows reads as data a reader should compare. A calc sheet's
    header block is not that; it is a set of facts about one sheet, and this is how a
    structural calculation letters them.
    """
    lines = []
    for label, value in pairs:
        rendered = format_value(value)
        if skip_empty and not rendered:
            continue
        lines.append(f"**{label}:** {rendered}")
    return "  ".join([]) if not lines else NEWLINE.join(f"{line}  " for line in lines).rstrip()


def callout(text: str, *, marker: str = "**Note**") -> str:
    """A blockquote callout — the form a warning takes in this package.

    Blockquote rather than an admonition directive: GFM has no admonitions, and every
    renderer this package is likely to meet (GitHub, a static-site build, a plain text
    editor) shows a blockquote correctly.
    """
    body = NEWLINE.join(f"> {line}" if line else ">" for line in text.splitlines())
    return f"> {marker}{NEWLINE}>{NEWLINE}{body}" if marker else body


def bullets(items: Iterable[Any], *, indent: int = 0) -> str:
    pad = " " * indent
    return NEWLINE.join(f"{pad}- {format_value(item)}" for item in items)


def document(*blocks: str) -> str:
    """Join blocks with one blank line between, and end with exactly one newline.

    The blank-line discipline lives here rather than at every call site, because "did that
    section end with a newline" is precisely the kind of question that makes two generated
    documents differ by whitespace and nothing else.
    """
    kept = [block.rstrip() for block in blocks if block and block.strip()]
    return (NEWLINE * 2).join(kept) + NEWLINE
