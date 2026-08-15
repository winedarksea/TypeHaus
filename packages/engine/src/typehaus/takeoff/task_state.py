"""Work-item status (``tasks.toml``) — where a package is, beside what it costs.

Mirrors ``takeoff/costs.py``'s idiom exactly (loader raises on a malformed file, writer is
deterministic and sorted, no dependency on the server) because the two files are read and
written by the same hands, and a second serialization style in the same directory is a
second thing to learn for no reason.

Status lives here and **not** on ``CostEntry``. Paid and done are different facts about
different objects: a package is done when the work is done, and a BOM row is paid when the
invoice clears — a delivered-and-paid-for pallet of studs sitting in the driveway is neither
of the other one. Conflating them was the specific mistake to avoid.

Like ``costs.toml``, this is deliberately outside the PatchOp/undo journal: closing out a
work package is not a plan edit, and un-closing one by pressing undo would be a lie about
the site.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

try:  # tomllib is stdlib on 3.11+; the engine still supports 3.9
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on <3.11 only
    import tomli as tomllib  # type: ignore[no-redef,import-not-found]

TASKS_FILENAME = "tasks.toml"

#: The status vocabulary. Four values, chosen because they are the ones every PM tool this
#: exports to already has — Trello lists, Asana sections, Buildertrend's schedule states —
#: so an import maps rather than translates.
STATUSES = ("todo", "scheduled", "in_progress", "done")
DEFAULT_STATUS = "todo"

_FIELDS = ("status", "started", "completed", "assignee", "note")


@dataclass(frozen=True)
class TaskEntry:
    """The owner's state for one work package, keyed by its stable slug."""

    status: str = DEFAULT_STATUS
    started: str | None = None     # "YYYY-MM-DD" prose, not validated as a date
    completed: str | None = None
    assignee: str | None = None    # the sub or crew, however the builder names them
    note: str | None = None

    @property
    def is_empty(self) -> bool:
        return (self.status == DEFAULT_STATUS and not self.started and not self.completed
                and not self.assignee and not self.note)

    def as_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in _FIELDS}


@dataclass(frozen=True)
class TasksState:
    entries: Mapping[str, TaskEntry] = field(default_factory=dict)

    def status_of(self, slug: str) -> str:
        entry = self.entries.get(slug)
        return entry.status if entry is not None else DEFAULT_STATUS


def _entry(slug: str, raw: Any, path: Path) -> TaskEntry:
    where = f"{path}: [entries.{slug!r}]"
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be a table")
    unknown = set(raw) - set(_FIELDS)
    if unknown:
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}; "
                         f"expected {list(_FIELDS)}")
    status = str(raw.get("status", DEFAULT_STATUS))
    if status not in STATUSES:
        raise ValueError(f"{where}: status {status!r}; expected one of {list(STATUSES)}")
    return TaskEntry(
        status=status,
        started=str(raw["started"]) if raw.get("started") else None,
        completed=str(raw["completed"]) if raw.get("completed") else None,
        assignee=str(raw["assignee"]) if raw.get("assignee") else None,
        note=str(raw["note"]) if raw.get("note") else None,
    )


def load_tasks(house_dir: Path) -> TasksState:
    """Read ``tasks.toml`` if the house carries one; an absent file is an empty state.

    A *malformed* file raises ``ValueError`` naming the offending key — a mistyped status
    must never silently become an ignored one.
    """
    path = Path(house_dir) / TASKS_FILENAME
    if not path.exists():
        return TasksState()
    data = tomllib.loads(path.read_text())
    unknown = set(data) - {"entries"}
    if unknown:
        raise ValueError(f"{path}: unknown top-level key(s) {sorted(unknown)}; "
                         "expected [entries.<slug>] tables")
    raw_entries = data.get("entries") or {}
    if not isinstance(raw_entries, dict):
        raise ValueError(f"{path}: 'entries' must be a table of work-item slugs")
    return TasksState(entries={str(slug): _entry(str(slug), raw, path)
                               for slug, raw in raw_entries.items()})


def write_tasks(house_dir: Path, state: TasksState) -> Path:
    """Serialize deterministically: slugs sorted, one field per line, empties dropped."""
    lines = ["# tasks.toml — work-package status (written by Type:Haus; safe to edit).",
             "# [entries.\"task/<trade>/<storey>\"]: status / started / completed /",
             "# assignee / note. The slug is the stable work-item id from takeoff/tasks.py;",
             "# `haus tasks` re-derives it every run, so it survives a rebuild.",
             f"# status is one of: {', '.join(STATUSES)}.", ""]
    for slug in sorted(state.entries):
        entry = state.entries[slug]
        if entry.is_empty:
            continue
        lines.append(f"[entries.{json.dumps(slug)}]")
        for name in _FIELDS:
            value = getattr(entry, name)
            if value is not None:
                lines.append(f"{name} = {json.dumps(str(value))}")
        lines.append("")
    path = Path(house_dir) / TASKS_FILENAME
    path.write_text("\n".join(lines).rstrip("\n") + "\n")
    return path


def apply_task_op(state: TasksState, op: Mapping[str, Any]) -> TasksState:
    """One state transition. Raises ``ValueError`` on a malformed op — the server maps that
    to a 400 rather than persisting garbage."""
    if op.get("op") != "set_task":
        raise ValueError(f"unknown task op {op.get('op')!r} (expected set_task)")
    slug = op.get("slug")
    if not slug:
        raise ValueError("set_task: missing slug")
    fields = {name: op[name] for name in _FIELDS if name in op}
    if "status" in fields and fields["status"] not in STATUSES:
        raise ValueError(f"set_task: status {fields['status']!r}; "
                         f"expected one of {list(STATUSES)}")
    current = state.entries.get(str(slug), TaskEntry())
    updated = replace(current, **fields)
    entries = dict(state.entries)
    if updated.is_empty:
        entries.pop(str(slug), None)
    else:
        entries[str(slug)] = updated
    return TasksState(entries=entries)
