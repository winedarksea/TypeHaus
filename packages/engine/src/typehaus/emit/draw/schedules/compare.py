"""The variant-compare study sheet.

Deliberately outside the permit-set index: this compares two design variants and is not a
permit deliverable, so it composes its own figure and carries no title block.
"""

from __future__ import annotations

from pathlib import Path

from typehaus.emit.draw.schedules.tables import _add_table
from typehaus.emit.draw.sheet_writer import section


def write_compare_sheet(report: object, output: Path) -> Path:
    """Render a one-page variant-compare sheet: element changes + quantity deltas.

    ``report`` is a ``typehaus.diff.CompareReport``. Kept off the permit-set index — this is a
    study sheet for comparing two design variants, not a permit deliverable.
    """
    import matplotlib.pyplot as plt

    output.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(11, 14))
    fig.text(0.04, 0.975, "VARIANT COMPARE", fontsize=16, family="monospace")
    fig.text(0.04, 0.952, f"A: {report.label_a}", fontsize=9, family="monospace")
    fig.text(0.04, 0.936, f"B: {report.label_b}", fontsize=9, family="monospace")
    counts = ", ".join(f"{kind} {n}" for kind, n in sorted(report.diff.counts().items())) or "none"
    fig.text(0.04, 0.916, f"element changes: {counts}", fontsize=9, family="monospace")

    section(fig, 0.04, 0.885, "ELEMENT CHANGES (A -> B)")
    change_rows = [(c.kind.value, c.tag + (f" (was {c.was_tag})" if c.was_tag else ""),
                    c.ifc_class, c.delta) for c in report.diff.substantive()]
    _add_table(fig, change_rows or [("—", "no element changes", "", "")],
               ("Change", "Tag", "Class", "Delta"), bbox=(0.04, 0.45, 0.92, 0.40))

    section(fig, 0.04, 0.41, "FRAMING QUANTITY DELTAS (A -> B)")
    qty_rows = [(q.profile, q.metric, f"{q.baseline:,.1f}", f"{q.variant:,.1f}",
                 f"{q.delta:+,.1f}") for q in report.quantity_deltas]
    _add_table(fig, qty_rows or [("—", "no quantity change", "", "", "")],
               ("Size", "Metric", "A", "B", "Δ"), bbox=(0.04, 0.05, 0.7, 0.33))

    fig.savefig(output, dpi=110)
    plt.close(fig)
    return output
