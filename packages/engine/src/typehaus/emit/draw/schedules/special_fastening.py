"""S-001's SPECIAL FASTENING block (decision #147).

Code-standard schedules fold into one line; every other authored spec gets one short line:
host, fastener, finish, spacing, source. Empty when the house authors none.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.fastening_specs import fastening_specs


def _short(source: str) -> str:
    """The citation's first clause, as a drawing note carries it."""
    for stop in (";", ":", " ("):
        source = source.split(stop)[0]
    return source if len(source) <= 60 else source[:57].rstrip() + "..."


def special_fastening_block(model: ResolvedModel) -> list[str]:
    specs = fastening_specs(model)
    rows = sorted({spec.code_row for spec in specs if spec.code_row})
    lines = [f"SHEATHING AND SUBFLOOR NAILING PER {' / '.join(rows).upper()} UNLESS LISTED"
             ] if rows else []
    for spec in specs:
        if spec.code_row:
            continue
        finish = f" {spec.finish.upper()}" if spec.finish else ""
        source = f" ({_short(spec.source)})" if spec.source else ""
        lines.append(f"{spec.use.upper()}: {spec.part}{finish} @ {spec.spacing}{source}")
    return lines
