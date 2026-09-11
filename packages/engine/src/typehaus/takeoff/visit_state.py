"""``[visits]`` in ``tasks.toml`` — the schedulable unit, authored by the owner.

A work package at (trade x storey) is the right grain for money and the wrong grain for a
phone call: catlin's concrete is roughly six mobilisations across two subs with inspections
between them, and the plumbing sleeves go in before the pour while the trade order puts
plumbing after framing. A **visit** is one sub, one arrival.

It lives here rather than in ``schedule/`` because it is persisted site state in the same
file ``task_state.py`` owns, and one file should have one parser. The writer and the ops
live next door in ``visit_toml.py`` because the two together would be past 500 lines.

Authored, never derived. The engine proposes splits (``schedule/propose.py``) and derives
readiness (``schedule/readiness.py``); which sub comes when is the owner's judgement, and a
visit the engine invented would be a booking nobody made.

Three slug shapes, and the third is new. ``task/<trade>/<storey>`` is a whole package;
``task/<trade>/<storey>/<label>`` is one arrival inside it; ``site/<label>`` is a
**standalone** visit that draws from no package at all — a locate, a side-permit, a survey,
a delivery. Those are real arrivals with real holds and the board was blind to them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: Mirrors ``task_state.STATUSES`` and adds the owner's own walk. ``done`` is the sub's
#: claim that they are finished; ``verified`` is the owner having checked the handoff list
#: afterwards. On an owner-built house nobody else is checking, so both are needed.
VISIT_STATUSES = ("todo", "scheduled", "in_progress", "done", "verified")
DEFAULT_STATUS = "todo"

#: A checkpoint is a pause *inside* one arrival, so it has no ``verified``: the owner's walk
#: is of the visit, once.
CHECKPOINT_STATUSES = ("todo", "in_progress", "done")

#: The prefix of a standalone visit — one that names no work package.
SITE_PREFIX = "site/"

SCALAR_FIELDS = ("label", "status", "scheduled", "assignee", "contact", "note",
                 "trade", "storey", "milestone", "contractor", "planned", "updated")
INT_FIELDS = ("duration_days",)
FLAG_FIELDS = ("blocks_successors", "shared_rows")
LIST_FIELDS = ("rows", "element_tags", "depends_on", "checked")
TABLE_FIELDS = ("constraints", "checkpoints", "exceptions", "skipped", "log", "materials")
#: One table, not a list: a visit is booked once.
BOOKING_FIELDS = ("date", "window", "confirmed_by", "confirmed_at", "note")
MATERIAL_FIELDS = ("id", "label", "lead_days", "order_by", "ordered", "expected",
                   "received", "source", "note")
VISIT_FIELDS = (*SCALAR_FIELDS, *INT_FIELDS, *FLAG_FIELDS, *LIST_FIELDS,
                *TABLE_FIELDS, "booked")


@dataclass(frozen=True)
class VisitConstraint:
    """A hold the owner put on a visit, and the date they took it off.

    Labels only — no lead times, no durations. "Windows delivered and checked against the
    RO schedule" is a fact somebody establishes by looking in the garage; how many weeks
    the supplier quoted is not in this model and never will be.

    ``owner``, ``next_action`` and ``follow_up`` are the three fields that turn a hold from
    a complaint into a task: who is on the hook, what unsticks it, and when to chase.
    ``severity = "attention"`` is a hold that never blocks — a missing certificate of
    insurance is worth showing and a terrible reason to refuse a sub who shows up.
    """

    label: str
    cleared: str | None = None
    severity: str = "blocking"
    owner: str | None = None
    next_action: str | None = None
    follow_up: str | None = None
    #: ``"locate"`` for a Gopher State One Call ticket, else empty.
    kind: str = ""
    ticket: str | None = None
    start: str | None = None
    refresh_agreement: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in CONSTRAINT_FIELDS}


CONSTRAINT_FIELDS = ("label", "cleared", "severity", "owner", "next_action", "follow_up",
                     "kind", "ticket", "start", "refresh_agreement")
_CONSTRAINT_FLAGS = ("refresh_agreement",)
CONSTRAINT_SEVERITIES = ("blocking", "attention")


@dataclass(frozen=True)
class Checkpoint:
    """An ordered pause inside one arrival, where work must actually stop.

    Footings are one visit and three stops: set the forms, pour, strip. The inspection sits
    between the first and the second, and before checkpoints the only way to say so was to
    invent two visits for one sub's one mobilisation.
    """

    id: str
    label: str = ""
    status: str = DEFAULT_STATUS
    #: Refs — ``insp/<id>`` or a visit slug — this checkpoint waits on, beyond the visit's.
    after: tuple[str, ...] = ()
    #: Calendar days the work has to sit before the next checkpoint. Authored, never
    #: defaulted: nothing here knows the mix or the weather.
    cure_days: int | None = None
    started: str | None = None
    completed: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {name: (list(getattr(self, name)) if name == "after"
                       else getattr(self, name))
                for name in CHECKPOINT_FIELDS}


CHECKPOINT_FIELDS = ("id", "label", "status", "after", "cure_days", "started", "completed")


@dataclass(frozen=True)
class VisitException:
    """The sub called it done while a blocking hold was open. Recorded, never resolved."""

    at: str
    hold: str
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"at": self.at, "hold": self.hold, "note": self.note}


@dataclass(frozen=True)
class SkippedItem:
    """A handoff item the owner deliberately passed on, and why. A tick needs no reason."""

    id: str
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "reason": self.reason}


@dataclass(frozen=True)
class LogLine:
    """One status change, stamped. Bounded and TOML-native — there is no journal file."""

    at: str
    to: str
    from_: str = ""
    ref: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"at": self.at, "from": self.from_, "to": self.to, "ref": self.ref}


#: How many ``log`` lines an entry keeps. A visit that churns is interesting for a week,
#: not forever, and the file is one a person edits by hand.
LOG_LIMIT = 20


@dataclass(frozen=True)
class Booking:
    """A date somebody confirmed with the sub. The engine never moves one.

    ``planned`` is intent and ``booked`` is a commitment, and the difference is the whole
    reason there are two fields: a predecessor that slips past a booking makes the booking
    *threatened*, with the slack in days, and leaves the date exactly where the owner and
    the sub agreed it would be.
    """

    date: str
    window: str | None = None
    confirmed_by: str | None = None
    confirmed_at: str | None = None
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in BOOKING_FIELDS}


@dataclass(frozen=True)
class Material:
    """Something that has to be on site before this visit, and what is known about when.

    ``lead_days`` is **authored when quoted** and defaulted never: the board says "lead time
    unknown" and asks for it, because a fabricated lead time is the number a schedule gets
    built on. ``expected`` is a promise and ``received`` is a fact — a delivery date never
    counts as a delivery.
    """

    id: str
    label: str = ""
    lead_days: int | None = None
    order_by: str | None = None
    ordered: str | None = None
    expected: str | None = None
    received: str | None = None
    source: str | None = None
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in MATERIAL_FIELDS}


@dataclass(frozen=True)
class VisitEntry:
    """One authored visit. The slug that keys it is the package slug plus an owner label."""

    label: str = ""
    status: str = DEFAULT_STATUS
    scheduled: str | None = None
    assignee: str | None = None
    contact: str | None = None
    note: str | None = None
    #: Standalone visits only: they draw from no work package, so they carry their own.
    trade: str | None = None
    storey: str | None = None
    #: Overrides the milestone the trade would put this visit in.
    milestone: str | None = None
    #: Key into ``[contractors]``. A visit names who is coming; the documents hang off them.
    contractor: str | None = None
    #: The owner's intent, not yet confirmed with the sub.
    planned: str | None = None
    updated: str | None = None
    #: Working days on site. Authored, never derived — nothing here knows a crew size.
    duration_days: int | None = None
    booked: Booking | None = None
    #: False takes this visit out of *package-level* predecessor expansion: flatwork,
    #: final grading and the punch list are authored last on purpose and must not make the
    #: next trade wait. It still has its own predecessors and its own readiness.
    blocks_successors: bool = True
    #: True where two visits deliberately cover the same BOM rows. Without it a shared row
    #: is a double-count in the estimate and validate says so.
    shared_rows: bool = False
    #: ``"section:key"`` BOM rows — a subset of the package's. Empty means all of them.
    rows: tuple[str, ...] = ()
    #: Globs over the package's element tags (``"FT-B-*"``). Empty means all of them.
    element_tags: tuple[str, ...] = ()
    #: Visit slugs, ``visit#checkpoint``, and/or ``insp/<id>``. Cross-trade order is
    #: expressible here, which is the whole reason a visit is not just a package.
    depends_on: tuple[str, ...] = ()
    constraints: tuple[VisitConstraint, ...] = ()
    #: Handoff item ids the owner ticked on the walk.
    checked: tuple[str, ...] = ()
    checkpoints: tuple[Checkpoint, ...] = ()
    exceptions: tuple[VisitException, ...] = ()
    skipped: tuple[SkippedItem, ...] = ()
    log: tuple[LogLine, ...] = ()
    materials: tuple[Material, ...] = ()

    @property
    def derived_status(self) -> str:
        """The visit's status. Derived from the checkpoints where it has any.

        ``verified`` stays a visit-level fact even on a checkpointed visit: the owner walks
        the arrival once, not once per pause.
        """
        if not self.checkpoints:
            return self.status
        if self.status == "verified":
            return "verified"
        states = [point.status for point in self.checkpoints]
        if all(state == "done" for state in states):
            return "done"
        if any(state != DEFAULT_STATUS for state in states):
            return "in_progress"
        return self.status if self.status in ("todo", "scheduled") else DEFAULT_STATUS

    def checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        for point in self.checkpoints:
            if point.id == checkpoint_id:
                return point
        return None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {name: getattr(self, name) for name in SCALAR_FIELDS}
        out.update({name: getattr(self, name) for name in (*INT_FIELDS, *FLAG_FIELDS)})
        out["booked"] = self.booked.as_dict() if self.booked else None
        out.update({name: list(getattr(self, name)) for name in LIST_FIELDS})
        out.update({name: [item.as_dict() for item in getattr(self, name)]
                    for name in TABLE_FIELDS})
        out["derived_status"] = self.derived_status
        return out


def package_of(slug: str) -> str:
    """``task/concrete/building/footings`` -> ``task/concrete/building``.

    A slug with exactly three segments *is* a package slug and maps to itself, which is how
    an implicit visit and an authored one that happens to cover the whole package end up on
    the same package without a special case. A standalone ``site/<label>`` maps to itself
    and no work item ever claims it.
    """
    parts = str(slug).split("/")
    return "/".join(parts[:3]) if len(parts) > 3 else str(slug)


def is_standalone(slug: str) -> bool:
    return str(slug).startswith(SITE_PREFIX)


@dataclass(frozen=True)
class VisitsState:
    entries: Mapping[str, VisitEntry] = field(default_factory=dict)

    def for_package(self, package: str) -> dict[str, VisitEntry]:
        return {slug: entry for slug, entry in self.entries.items()
                if not is_standalone(slug) and package_of(slug) == package}

    @property
    def standalone(self) -> dict[str, VisitEntry]:
        return {slug: entry for slug, entry in self.entries.items() if is_standalone(slug)}


def _strings(raw: Any, where: str, name: str) -> tuple[str, ...]:
    if isinstance(raw, str) or not isinstance(raw, (list, tuple)):
        raise ValueError(f"{where}: {name!r} must be an array of strings")
    return tuple(str(item) for item in raw)


def _tables(raw: Any, where: str, name: str) -> list[dict[str, Any]]:
    if not isinstance(raw, (list, tuple)):
        raise ValueError(f"{where}: {name!r} must be an array of tables")
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError(f"{where}: every {name} entry must be a table")
    return [dict(item) for item in raw]


def constraints_from(raw: Any, where: str) -> tuple[VisitConstraint, ...]:
    out: list[VisitConstraint] = []
    for item in _tables(raw, where, "constraints"):
        if not item.get("label"):
            raise ValueError(f"{where}: every constraint needs a 'label'")
        unknown = set(item) - set(CONSTRAINT_FIELDS)
        if unknown:
            raise ValueError(f"{where}: constraint has unknown field(s) {sorted(unknown)}")
        severity = str(item.get("severity") or "blocking")
        if severity not in CONSTRAINT_SEVERITIES:
            raise ValueError(f"{where}: constraint severity {severity!r}; expected one of "
                             f"{list(CONSTRAINT_SEVERITIES)}")
        values: dict[str, Any] = {"severity": severity}
        for name in CONSTRAINT_FIELDS:
            if name in ("severity", *_CONSTRAINT_FLAGS):
                continue
            values[name] = str(item[name]) if item.get(name) else (
                "" if name in ("label", "kind") else None)
        values["refresh_agreement"] = bool(item.get("refresh_agreement", False))
        out.append(VisitConstraint(**values))
    return tuple(out)


def checkpoints_from(raw: Any, where: str) -> tuple[Checkpoint, ...]:
    out: list[Checkpoint] = []
    seen: set[str] = set()
    for item in _tables(raw, where, "checkpoints"):
        if not item.get("id"):
            raise ValueError(f"{where}: every checkpoint needs an 'id'")
        unknown = set(item) - set(CHECKPOINT_FIELDS)
        if unknown:
            raise ValueError(f"{where}: checkpoint {item['id']!r} has unknown field(s) "
                             f"{sorted(unknown)}")
        status = str(item.get("status") or DEFAULT_STATUS)
        if status not in CHECKPOINT_STATUSES:
            raise ValueError(f"{where}: checkpoint {item['id']!r} status {status!r}; "
                             f"expected one of {list(CHECKPOINT_STATUSES)}")
        checkpoint_id = str(item["id"])
        if checkpoint_id in seen:
            raise ValueError(f"{where}: two checkpoints share the id {checkpoint_id!r}")
        seen.add(checkpoint_id)
        cure = item.get("cure_days")
        out.append(Checkpoint(
            id=checkpoint_id, label=str(item.get("label") or ""), status=status,
            after=_strings(item["after"], where, "after") if item.get("after") else (),
            cure_days=int(cure) if cure is not None else None,
            started=str(item["started"]) if item.get("started") else None,
            completed=str(item["completed"]) if item.get("completed") else None))
    return tuple(out)


def _exceptions(raw: Any, where: str) -> tuple[VisitException, ...]:
    out: list[VisitException] = []
    for item in _tables(raw, where, "exceptions"):
        unknown = set(item) - {"at", "hold", "note"}
        if unknown or not item.get("at") or not item.get("hold"):
            raise ValueError(f"{where}: an exception is "
                             "{ at = \"...\", hold = \"...\", note = \"...\" }")
        out.append(VisitException(str(item["at"]), str(item["hold"]),
                                  str(item.get("note") or "")))
    return tuple(out)


def _skipped(raw: Any, where: str) -> tuple[SkippedItem, ...]:
    out: list[SkippedItem] = []
    for item in _tables(raw, where, "skipped"):
        unknown = set(item) - {"id", "reason"}
        if unknown or not item.get("id") or not item.get("reason"):
            raise ValueError(f"{where}: a skipped handoff item is "
                             "{ id = \"...\", reason = \"...\" } — a skip needs its reason")
        out.append(SkippedItem(str(item["id"]), str(item["reason"])))
    return tuple(out)


def _materials(raw: Any, where: str) -> tuple[Material, ...]:
    out: list[Material] = []
    for item in _tables(raw, where, "materials"):
        unknown = set(item) - set(MATERIAL_FIELDS)
        if unknown or not item.get("id"):
            raise ValueError(f"{where}: a material needs an 'id'; unknown field(s) "
                             f"{sorted(unknown)}")
        lead = item.get("lead_days")
        out.append(Material(
            id=str(item["id"]), label=str(item.get("label") or ""),
            lead_days=int(lead) if lead is not None else None,
            **{name: (str(item[name]) if item.get(name) else None)
               for name in ("order_by", "ordered", "expected", "received", "source",
                            "note")}))
    return tuple(out)


def _booking(raw: Any, where: str) -> Booking:
    if not isinstance(raw, dict) or not raw.get("date"):
        raise ValueError(f"{where}: 'booked' is "
                         "{ date = \"...\", window = \"...\", confirmed_by = \"...\" } "
                         "— a booking without a date is a plan, and that is 'planned'")
    unknown = set(raw) - set(BOOKING_FIELDS)
    if unknown:
        raise ValueError(f"{where}: booked has unknown field(s) {sorted(unknown)}")
    return Booking(**{name: (str(raw[name]) if raw.get(name) else None)
                      for name in BOOKING_FIELDS})


def _log(raw: Any, where: str) -> tuple[LogLine, ...]:
    out: list[LogLine] = []
    for item in _tables(raw, where, "log"):
        unknown = set(item) - {"at", "from", "to", "ref"}
        if unknown or not item.get("at") or not item.get("to"):
            raise ValueError(f"{where}: a log line is "
                             "{ at = \"...\", from = \"...\", to = \"...\" }")
        out.append(LogLine(at=str(item["at"]), to=str(item["to"]),
                           from_=str(item.get("from") or ""),
                           ref=str(item.get("ref") or "")))
    return tuple(out[-LOG_LIMIT:])


def parse_visit(slug: str, raw: Any, where: str) -> VisitEntry:
    """One ``[visits."<slug>"]`` table. Raises ``ValueError`` naming the offending key."""
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be a table")
    unknown = set(raw) - set(VISIT_FIELDS)
    if unknown:
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}; "
                         f"expected {list(VISIT_FIELDS)}")
    status = str(raw.get("status", DEFAULT_STATUS))
    if status not in VISIT_STATUSES:
        raise ValueError(f"{where}: status {status!r}; "
                         f"expected one of {list(VISIT_STATUSES)}")
    if is_standalone(slug):
        if len(str(slug).split("/")) != 2 or not str(slug).split("/")[1]:
            raise ValueError(f"{where}: a standalone visit is \"site/<label>\"; "
                             f"{slug!r} is not")
        if not raw.get("trade"):
            raise ValueError(f"{where}: a standalone visit draws from no work package, so "
                             "it must author its own 'trade'")
    elif len(str(slug).split("/")) < 4:
        raise ValueError(f"{where}: a visit slug is a package slug plus an owner label "
                         f"(\"task/<trade>/<storey>/<label>\") or a standalone "
                         f"\"site/<label>\"; {slug!r} names a package")
    entry = VisitEntry(
        label=str(raw.get("label") or ""),
        status=status,
        scheduled=str(raw["scheduled"]) if raw.get("scheduled") else None,
        assignee=str(raw["assignee"]) if raw.get("assignee") else None,
        contact=str(raw["contact"]) if raw.get("contact") else None,
        note=str(raw["note"]) if raw.get("note") else None,
        trade=str(raw["trade"]) if raw.get("trade") else None,
        contractor=str(raw["contractor"]) if raw.get("contractor") else None,
        planned=str(raw["planned"]) if raw.get("planned") else None,
        duration_days=(int(raw["duration_days"])
                       if raw.get("duration_days") is not None else None),
        booked=_booking(raw["booked"], where) if raw.get("booked") else None,
        materials=_materials(raw["materials"], where) if raw.get("materials") else (),
        storey=str(raw["storey"]) if raw.get("storey") else None,
        milestone=str(raw["milestone"]) if raw.get("milestone") else None,
        updated=str(raw["updated"]) if raw.get("updated") else None,
        blocks_successors=bool(raw.get("blocks_successors", True)),
        shared_rows=bool(raw.get("shared_rows", False)),
        rows=_strings(raw["rows"], where, "rows") if raw.get("rows") else (),
        element_tags=(_strings(raw["element_tags"], where, "element_tags")
                      if raw.get("element_tags") else ()),
        depends_on=(_strings(raw["depends_on"], where, "depends_on")
                    if raw.get("depends_on") else ()),
        constraints=(constraints_from(raw["constraints"], where)
                     if raw.get("constraints") else ()),
        checked=_strings(raw["checked"], where, "checked") if raw.get("checked") else (),
        checkpoints=(checkpoints_from(raw["checkpoints"], where)
                     if raw.get("checkpoints") else ()),
        exceptions=_exceptions(raw["exceptions"], where) if raw.get("exceptions") else (),
        skipped=_skipped(raw["skipped"], where) if raw.get("skipped") else (),
        log=_log(raw["log"], where) if raw.get("log") else (),
    )
    errors = entry_rule_errors(slug, entry)
    if errors:
        raise ValueError(f"{where}: {errors[0]}")
    return entry


def load_visits(raw_visits: Any, path: Path) -> VisitsState:
    """Build the visit half of a parsed ``tasks.toml``."""
    import json

    if not isinstance(raw_visits, dict):
        raise ValueError(f"{path}: 'visits' must be a table of visit slugs")
    return VisitsState(entries={
        str(slug): parse_visit(str(slug), raw, f"{path}: [visits.{json.dumps(str(slug))}]")
        for slug, raw in raw_visits.items()})


# Re-exported so ``task_state`` and every existing caller keep one import site.
from typehaus.takeoff.visit_toml import (  # noqa: E402
    apply_visit_op,
    entry_rule_errors,
    toml_string,
    visit_lines,
)

__all__ = [
    "CHECKPOINT_FIELDS", "CHECKPOINT_STATUSES", "CONSTRAINT_FIELDS", "CONSTRAINT_SEVERITIES",
    "DEFAULT_STATUS", "LOG_LIMIT", "SITE_PREFIX", "VISIT_STATUSES", "Checkpoint", "LogLine",
    "BOOKING_FIELDS", "Booking", "INT_FIELDS", "MATERIAL_FIELDS", "Material",
    "SkippedItem", "VisitConstraint", "VisitEntry", "VisitException", "VisitsState",
    "apply_visit_op", "checkpoints_from", "constraints_from", "entry_rule_errors",
    "is_standalone", "load_visits",
    "package_of", "parse_visit", "toml_string", "visit_lines",
]
