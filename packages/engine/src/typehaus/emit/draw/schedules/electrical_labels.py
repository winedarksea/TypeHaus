"""E-605 — the NEC label schedule: a view of ``model.electrical_labels``, nothing summed here.

Quoted wording is the code's own; unquoted is the content the code requires. A label resting
on an open question says so in the note, and an unauthored input prints as NOT AUTHORED.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.paged_tables import PagedTable, wrap_cells
from typehaus.emit.draw.schedules.structural import _write_paged
from typehaus.resolve.model import ResolvedModel


def has_label_schedule(model: ResolvedModel) -> bool:
    return bool(model.electrical_labels)


def label_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    rows = []
    for label in model.electrical_labels:
        notes = []
        if label.also:
            notes.append("also " + ", ".join(label.also))
        if label.missing:
            notes.append("NOT AUTHORED: " + ", ".join(label.missing))
        if label.condition:
            notes.append("if " + label.condition)
        wording = f'"{label.wording}"' if label.literal else label.wording
        rows.append((label.section, wording, label.host_ref or "—", label.location,
                     str(label.quantity), "; ".join(notes) or "—"))
    return tuple(rows)


def label_tables(model: ResolvedModel) -> list[PagedTable]:
    return [PagedTable("ELECTRICAL LABEL SCHEDULE (NEC)",
                       ("NEC", "Wording", "Host", "Location", "Qty", "Note"),
                       wrap_cells(label_rows(model), {1: 46, 3: 40, 5: 30}))]


def write_label_schedule(pdf, model: ResolvedModel, number: str, name: str, *,
                         page: int = 0) -> None:
    _write_paged(pdf, model, number, name, label_tables(model), page)
