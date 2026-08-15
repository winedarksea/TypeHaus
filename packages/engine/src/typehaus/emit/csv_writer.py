"""Deterministic RFC 4180 CSV — the engine's one comma-separated exit.

There was no CSV writer anywhere in the engine before this, which is the whole reason
nothing Type:Haus computes could reach an estimating package: RSMeans Online, Craftsman
Cloud, Buildertrend, Trello, Asana and QuickBooks all accept CSV or Excel, and every one of
them was one file format away.

Written by hand rather than via :mod:`csv` for one reason: **determinism**. ``csv.writer``
emits ``\\r\\n`` on some platforms and ``\\n`` on others, quotes at its own discretion, and
formats floats however ``str`` feels — so the same model produces different bytes on
different machines, and a re-export diff stops meaning anything. This module mirrors the
discipline of ``takeoff/costs.py::write_costs``: fixed newline, fixed quoting rule, fixed
float formatting, rows in the order given.

RFC 4180 quoting: a field is quoted iff it contains a comma, a quote, CR or LF; an embedded
quote doubles. Nothing else is escaped, and nothing is ever silently dropped.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

#: LF, not CRLF. RFC 4180 says CRLF, every consumer accepts LF, and a file that changes
#: line ending by platform cannot be diffed or committed.
NEWLINE = "\n"

_NEEDS_QUOTING = (",", '"', "\r", "\n")


def format_field(value: Any) -> str:
    """One cell, rendered deterministically.

    Floats get a fixed 2-decimal form (these are money and quantities, not measurements)
    unless they are integral, and ``None`` becomes the empty string rather than the string
    ``"None"`` — a blank cell is what a spreadsheet means by "not known".
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.0f}" if value.is_integer() else f"{value:.2f}"
    return str(value)


def escape(text: str) -> str:
    if any(char in text for char in _NEEDS_QUOTING):
        return '"' + text.replace('"', '""') + '"'
    return text


def render_rows(columns: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> str:
    """The whole file as one string: header line, then one line per row.

    Every row is projected through ``columns`` — a key a row carries but the column list
    does not is dropped, and a column a row lacks is blank. That projection is the contract:
    the header is authored once, at the call site, and no row can widen the file.
    """
    lines = [",".join(escape(name) for name in columns)]
    for row in rows:
        lines.append(",".join(escape(format_field(row.get(name))) for name in columns))
    return NEWLINE.join(lines) + NEWLINE


def write_csv(path: Path, columns: Sequence[str],
              rows: Iterable[Mapping[str, Any]]) -> Path:
    """Write ``rows`` to ``path`` and return it. Parent directories are created."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_rows(columns, rows), encoding="utf-8", newline="")
    return path
