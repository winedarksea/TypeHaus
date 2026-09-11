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

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from typehaus.takeoff.visit_state import (
    VisitsState,
    load_visits,
    toml_string,
    visit_lines,
)

try:  # tomllib is stdlib on 3.11+; the engine still supports 3.9
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on <3.11 only
    import tomli as tomllib  # type: ignore[no-redef,import-not-found]

TASKS_FILENAME = "tasks.toml"

#: The status vocabulary. The first four are the ones every PM tool this exports to already
#: has — Trello lists, Asana sections, Buildertrend's schedule states — so an import maps
#: rather than translates. ``verified`` is the fifth and is the owner-builder's: ``done`` is
#: the sub's claim that they are finished, ``verified`` is the owner's own walk of the
#: handoff list afterwards, and on a house nobody else is checking those are two facts.
STATUSES = ("todo", "scheduled", "in_progress", "done", "verified")
DEFAULT_STATUS = "todo"

_FIELDS = ("status", "started", "completed", "assignee", "note")
_CALENDAR_FIELDS = ("workdays", "holidays")
CONTRACTOR_FIELDS = ("name", "phone", "email", "trades", "licence", "coi_expires", "w9",
                     "contract", "note")
#: Trades that need a licence named before the first call. Everything else does not, and
#: asking for one would be the tool inventing a requirement.
LICENSED_TRADES = ("electrical", "plumbing")


@dataclass(frozen=True)
class Calendar:
    """Working days and the dates nobody works. Nothing here is derived."""

    #: 0 = Monday. Default is Monday-Friday, which is a convention a house may override.
    workdays: tuple[int, ...] = (0, 1, 2, 3, 4)
    holidays: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {"workdays": list(self.workdays), "holidays": list(self.holidays)}


@dataclass(frozen=True)
class Contractor:
    """One sub, and what is on file for them."""

    key: str
    name: str
    phone: str | None = None
    email: str | None = None
    trades: tuple[str, ...] = ()
    licence: str | None = None
    coi_expires: str | None = None
    w9: str | None = None
    contract: str | None = None
    note: str | None = None

    @property
    def missing_documents(self) -> tuple[str, ...]:
        """Attention items, never blocks. A licence only where the trade requires one."""
        out = [name for name in ("coi_expires", "w9", "contract")
               if not getattr(self, name)]
        if not self.licence and any(t in LICENSED_TRADES for t in self.trades):
            out.append("licence")
        return tuple(out)

    def as_dict(self) -> dict[str, Any]:
        return ({"key": self.key}
                | {name: getattr(self, name) for name in CONTRACTOR_FIELDS}
                | {"trades": list(self.trades),
                   "missing_documents": list(self.missing_documents)})


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
    #: The ``[visits]`` half of the same file. Parsed and written by
    #: ``takeoff/visit_state.py`` — one file, one parser, two modules only because the two
    #: together would be past 500 lines.
    visits: VisitsState = field(default_factory=VisitsState)
    #: ``(id, label)`` in build order, when the house overrides the engine's rows. Empty
    #: means the engine's. A milestone is the only grouping coarse enough to answer "where
    #: am I", and which rows a particular build has is the owner's sentence, not ours.
    milestones: tuple[tuple[str, str], ...] = ()
    #: ``[calendar]``: which weekdays are worked and which dates are not. Authored, because
    #: "legal holidays" is a jurisdiction's answer and a crew's is narrower still.
    calendar: Calendar = field(default_factory=lambda: Calendar())
    #: ``[contractors.<key>]``: who is coming, and which documents are on file for them. A
    #: missing document is an attention item and never a block — great subs without digital
    #: paperwork have to stay bookable.
    contractors: Mapping[str, Contractor] = field(default_factory=dict)

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
    unknown = set(data) - {"entries", "visits", "milestones", "calendar", "contractors"}
    if unknown:
        raise ValueError(f"{path}: unknown top-level key(s) {sorted(unknown)}; expected "
                         "[entries.<slug>], [visits.<slug>], [calendar], "
                         "[contractors.<key>] and milestones = [...]")
    raw_entries = data.get("entries") or {}
    if not isinstance(raw_entries, dict):
        raise ValueError(f"{path}: 'entries' must be a table of work-item slugs")
    return TasksState(entries={str(slug): _entry(str(slug), raw, path)
                               for slug, raw in raw_entries.items()},
                      visits=load_visits(data.get("visits") or {}, path),
                      milestones=_milestones(data.get("milestones"), path),
                      calendar=_calendar(data.get("calendar"), path),
                      contractors=_contractors(data.get("contractors"), path))


def _calendar(raw: Any, path: Path) -> Calendar:
    if not raw:
        return Calendar()
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: [calendar] must be a table")
    unknown = set(raw) - set(_CALENDAR_FIELDS)
    if unknown:
        raise ValueError(f"{path}: [calendar] unknown field(s) {sorted(unknown)}; "
                         f"expected {list(_CALENDAR_FIELDS)}")
    days = raw.get("workdays")
    workdays = tuple(int(d) for d in days) if days else (0, 1, 2, 3, 4)
    if any(d < 0 or d > 6 for d in workdays):
        raise ValueError(f"{path}: [calendar] workdays are 0 (Monday) to 6 (Sunday)")
    return Calendar(workdays=workdays,
                    holidays=tuple(str(d) for d in (raw.get("holidays") or ())))


def _contractors(raw: Any, path: Path) -> dict[str, Contractor]:
    if not raw:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: 'contractors' must be a table of keys")
    out: dict[str, Contractor] = {}
    for key, body in raw.items():
        where = f"{path}: [contractors.{key}]"
        if not isinstance(body, dict):
            raise ValueError(f"{where} must be a table")
        unknown = set(body) - set(CONTRACTOR_FIELDS)
        if unknown:
            raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}; "
                             f"expected {list(CONTRACTOR_FIELDS)}")
        if not body.get("name"):
            raise ValueError(f"{where}: missing 'name'")
        out[str(key)] = Contractor(
            key=str(key), name=str(body["name"]),
            trades=tuple(str(t) for t in (body.get("trades") or ())),
            **{name: (str(body[name]) if body.get(name) else None)
               for name in ("phone", "email", "licence", "coi_expires", "w9", "contract",
                            "note")})
    return out


def _milestones(raw: Any, path: Path) -> tuple[tuple[str, str], ...]:
    """``milestones = [{ id = "...", label = "..." }, ...]`` — an ordered array, not a
    table, because the order *is* the build order and a TOML table does not promise one."""
    if not raw:
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"{path}: 'milestones' must be an array of "
                         "{ id = \"...\", label = \"...\" } tables, in build order")
    out: list[tuple[str, str]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or not item.get("id") or not item.get("label"):
            raise ValueError(f"{path}: milestones #{index + 1} needs an 'id' and a 'label'")
        unknown = set(item) - {"id", "label"}
        if unknown:
            raise ValueError(f"{path}: milestones #{index + 1} has unknown field(s) "
                             f"{sorted(unknown)}")
        out.append((str(item["id"]), str(item["label"])))
    if len({name for name, _ in out}) != len(out):
        raise ValueError(f"{path}: two milestone rows share an id")
    return tuple(out)


def write_tasks(house_dir: Path, state: TasksState) -> Path:
    """Serialize deterministically: slugs sorted, one field per line, empties dropped."""
    lines = ["# tasks.toml — work-package status (written by Type:Haus; safe to edit).",
             "# [entries.\"task/<trade>/<storey>\"]: status / started / completed /",
             "# assignee / note. The slug is the stable work-item id from takeoff/tasks.py;",
             "# `haus tasks` re-derives it every run, so it survives a rebuild.",
             f"# status is one of: {', '.join(STATUSES)}.",
             "# [visits.\"<package slug>/<label>\"]: one sub, one arrival — see",
             "# docs/site-state-format.md.", ""]
    for slug in sorted(state.entries):
        entry = state.entries[slug]
        if entry.is_empty:
            continue
        lines.append(f"[entries.{toml_string(slug)}]")
        for name in _FIELDS:
            value = getattr(entry, name)
            if value is not None:
                lines.append(f"{name} = {toml_string(value)}")
        lines.append("")
    if state.calendar != Calendar():
        lines.append("[calendar]")
        lines.append(f"workdays = [{', '.join(str(d) for d in state.calendar.workdays)}]")
        if state.calendar.holidays:
            items = ", ".join(toml_string(d) for d in state.calendar.holidays)
            lines.append(f"holidays = [{items}]")
        lines.append("")
    for key in sorted(state.contractors):
        who = state.contractors[key]
        lines.append(f"[contractors.{toml_string(key)}]")
        for name in CONTRACTOR_FIELDS:
            value = getattr(who, name)
            if not value:
                continue
            if name == "trades":
                lines.append("trades = ["
                             + ", ".join(toml_string(t) for t in value) + "]")
            else:
                lines.append(f"{name} = {toml_string(value)}")
        lines.append("")
    if state.milestones:
        lines.append("milestones = [")
        for name, label in state.milestones:
            lines.append(f"  {{ id = {toml_string(name)}, "
                         f"label = {toml_string(label)} }},")
        lines.extend(["]", ""])
    lines.extend(visit_lines(state.visits))
    from typehaus.takeoff.atomic import atomic_write_text

    return atomic_write_text(Path(house_dir) / TASKS_FILENAME,
                             "\n".join(lines).rstrip("\n") + "\n")


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
    return replace(state, entries=entries)


def apply_visit_ops(state: TasksState, op: Mapping[str, Any]) -> TasksState:
    """``set_visit``, folded over the ``[visits]`` half of the same state."""
    from typehaus.takeoff.visit_state import apply_visit_op

    return replace(state, visits=apply_visit_op(state.visits, op))
