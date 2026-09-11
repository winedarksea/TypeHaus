"""``[visits]`` in ``tasks.toml`` — the schedulable unit, authored by the owner.

A work package at (trade x storey) is the right grain for money and the wrong grain for a
phone call: catlin's concrete is roughly six mobilisations across two subs with inspections
between them, and the plumbing sleeves go in before the pour while the trade order puts
plumbing after framing. A **visit** is one sub, one arrival.

It lives here rather than in ``schedule/`` because it is persisted site state in the same
file ``task_state.py`` owns, and one file should have one parser. It lives in its own
module rather than in ``task_state.py`` because the two together would be past 500 lines.

Authored, never derived. The engine proposes splits (``schedule/propose.py``) and derives
readiness (``schedule/readiness.py``); which sub comes when is the owner's judgement, and a
visit the engine invented would be a booking nobody made.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

#: Mirrors ``task_state.STATUSES`` and adds the owner's own walk. ``done`` is the sub's
#: claim that they are finished; ``verified`` is the owner having checked the handoff list
#: afterwards. On an owner-built house nobody else is checking, so both are needed.
VISIT_STATUSES = ("todo", "scheduled", "in_progress", "done", "verified")
DEFAULT_STATUS = "todo"

_SCALARS = ("label", "status", "scheduled", "assignee", "contact", "note")
_LISTS = ("rows", "element_tags", "depends_on", "checked")
_FIELDS = (*_SCALARS, *_LISTS, "constraints")


@dataclass(frozen=True)
class VisitConstraint:
    """A hold the owner put on a visit, and the date they took it off.

    Labels only — no lead times, no durations. "Windows delivered and checked against the
    RO schedule" is a fact somebody establishes by looking in the garage; how many weeks
    the supplier quoted is not in this model and never will be.
    """

    label: str
    cleared: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"label": self.label, "cleared": self.cleared}


@dataclass(frozen=True)
class VisitEntry:
    """One authored visit. The slug that keys it is the package slug plus an owner label."""

    label: str = ""
    status: str = DEFAULT_STATUS
    scheduled: str | None = None
    assignee: str | None = None
    contact: str | None = None
    note: str | None = None
    #: ``"section:key"`` BOM rows — a subset of the package's. Empty means all of them.
    rows: tuple[str, ...] = ()
    #: Globs over the package's element tags (``"FT-B-*"``). Empty means all of them.
    element_tags: tuple[str, ...] = ()
    #: Visit slugs and/or ``insp/<id>``. Cross-trade order is expressible here, which is
    #: the whole reason a visit is not just a package.
    depends_on: tuple[str, ...] = ()
    constraints: tuple[VisitConstraint, ...] = ()
    #: Handoff item ids the owner ticked on the walk.
    checked: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {name: getattr(self, name) for name in _SCALARS}
        out.update({name: list(getattr(self, name)) for name in _LISTS})
        out["constraints"] = [c.as_dict() for c in self.constraints]
        return out


def toml_string(text: str) -> str:
    """A TOML basic string with the non-ASCII left alone — see inspection_state._quote."""
    return json.dumps(str(text), ensure_ascii=False)


def package_of(slug: str) -> str:
    """``task/concrete/building/footings`` -> ``task/concrete/building``.

    A slug with exactly three segments *is* a package slug and maps to itself, which is how
    an implicit visit and an authored one that happens to cover the whole package end up on
    the same package without a special case.
    """
    parts = str(slug).split("/")
    return "/".join(parts[:3]) if len(parts) > 3 else str(slug)


@dataclass(frozen=True)
class VisitsState:
    entries: Mapping[str, VisitEntry] = field(default_factory=dict)

    def for_package(self, package: str) -> dict[str, VisitEntry]:
        return {slug: entry for slug, entry in self.entries.items()
                if package_of(slug) == package}


def _strings(raw: Any, where: str, name: str) -> tuple[str, ...]:
    if isinstance(raw, str) or not isinstance(raw, (list, tuple)):
        raise ValueError(f"{where}: {name!r} must be an array of strings")
    return tuple(str(item) for item in raw)


def _constraints(raw: Any, where: str) -> tuple[VisitConstraint, ...]:
    if not isinstance(raw, (list, tuple)):
        raise ValueError(f"{where}: 'constraints' must be an array of "
                         "{ label = \"...\", cleared = \"...\" } tables")
    out: list[VisitConstraint] = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("label"):
            raise ValueError(f"{where}: every constraint needs a 'label'")
        unknown = set(item) - {"label", "cleared"}
        if unknown:
            raise ValueError(f"{where}: constraint has unknown field(s) {sorted(unknown)}")
        out.append(VisitConstraint(str(item["label"]),
                                   str(item["cleared"]) if item.get("cleared") else None))
    return tuple(out)


def parse_visit(slug: str, raw: Any, where: str) -> VisitEntry:
    """One ``[visits."<slug>"]`` table. Raises ``ValueError`` naming the offending key."""
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be a table")
    unknown = set(raw) - set(_FIELDS)
    if unknown:
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}; "
                         f"expected {list(_FIELDS)}")
    status = str(raw.get("status", DEFAULT_STATUS))
    if status not in VISIT_STATUSES:
        raise ValueError(f"{where}: status {status!r}; "
                         f"expected one of {list(VISIT_STATUSES)}")
    if len(str(slug).split("/")) < 4:
        raise ValueError(f"{where}: a visit slug is a package slug plus an owner label "
                         f"(\"task/<trade>/<storey>/<label>\"); {slug!r} names a package")
    return VisitEntry(
        label=str(raw.get("label") or ""),
        status=status,
        scheduled=str(raw["scheduled"]) if raw.get("scheduled") else None,
        assignee=str(raw["assignee"]) if raw.get("assignee") else None,
        contact=str(raw["contact"]) if raw.get("contact") else None,
        note=str(raw["note"]) if raw.get("note") else None,
        rows=_strings(raw["rows"], where, "rows") if raw.get("rows") else (),
        element_tags=(_strings(raw["element_tags"], where, "element_tags")
                      if raw.get("element_tags") else ()),
        depends_on=(_strings(raw["depends_on"], where, "depends_on")
                    if raw.get("depends_on") else ()),
        constraints=_constraints(raw["constraints"], where) if raw.get("constraints") else (),
        checked=_strings(raw["checked"], where, "checked") if raw.get("checked") else (),
    )


def load_visits(raw_visits: Any, path: Path) -> VisitsState:
    """Build the visit half of a parsed ``tasks.toml``."""
    if not isinstance(raw_visits, dict):
        raise ValueError(f"{path}: 'visits' must be a table of visit slugs")
    return VisitsState(entries={
        str(slug): parse_visit(str(slug), raw, f"{path}: [visits.{json.dumps(str(slug))}]")
        for slug, raw in raw_visits.items()})


def visit_lines(state: VisitsState) -> list[str]:
    """The ``[visits]`` half of ``write_tasks``: slugs sorted, one field per line."""
    lines: list[str] = []
    for slug in sorted(state.entries):
        entry = state.entries[slug]
        lines.append(f"[visits.{toml_string(slug)}]")
        for name in _SCALARS:
            value = getattr(entry, name)
            if value:
                lines.append(f"{name} = {toml_string(value)}")
        for name in _LISTS:
            value = getattr(entry, name)
            if value:
                items = ", ".join(toml_string(item) for item in value)
                lines.append(f"{name} = [{items}]")
        if entry.constraints:
            lines.append("constraints = [")
            for constraint in entry.constraints:
                cleared = (f", cleared = {toml_string(constraint.cleared)}"
                           if constraint.cleared else "")
                lines.append(f"  {{ label = {toml_string(constraint.label)}{cleared} }},")
            lines.append("]")
        lines.append("")
    return lines


def apply_visit_op(state: VisitsState, op: Mapping[str, Any]) -> VisitsState:
    """Fold one ``set_visit`` op. ``ValueError`` on a malformed one — the server 400s."""
    if op.get("op") != "set_visit":
        raise ValueError(f"unknown visit op {op.get('op')!r} (expected set_visit)")
    slug = str(op.get("slug") or "")
    if not slug:
        raise ValueError("set_visit: missing slug")
    unknown = set(op) - {"op", "slug", "cleared"} - set(_FIELDS)
    if unknown:
        raise ValueError(f"set_visit: unknown field(s) {sorted(unknown)}")
    if "status" in op and op["status"] not in VISIT_STATUSES:
        raise ValueError(f"set_visit: status {op['status']!r}; "
                         f"expected one of {list(VISIT_STATUSES)}")
    current = state.entries.get(slug, VisitEntry())
    values: dict[str, Any] = {}
    for name in _SCALARS:
        if name in op:
            values[name] = (str(op[name]) if op[name] else
                            ("" if name in ("label",) else None))
    if "status" in op:
        values["status"] = str(op["status"])
    for name in _LISTS:
        if name in op:
            values[name] = tuple(str(item) for item in (op[name] or ()))
    if "constraints" in op:
        values["constraints"] = _constraints(op["constraints"], "set_visit")
    updated = replace(current, **values)
    # `cleared` is a label -> date map rather than a whole constraint list, because the one
    # write a phone makes is a checkbox and resending the list would race the owner's own
    # edit of it in the file.
    if op.get("cleared"):
        marks = {str(k): (str(v) if v else None) for k, v in dict(op["cleared"]).items()}
        updated = replace(updated, constraints=tuple(
            replace(c, cleared=marks.get(c.label, c.cleared)) for c in updated.constraints))
    # The one rule this writer enforces, and it is the owner-builder's whole point:
    # ``verified`` is the owner saying they walked it, and a hold they put on themselves
    # that is still open means they did not. ``done`` (the sub's claim) is unaffected.
    if updated.status == "verified":
        open_holds = [c.label for c in updated.constraints if c.cleared is None]
        if open_holds:
            raise ValueError(
                f"set_visit {slug!r}: cannot mark verified while {len(open_holds)} "
                f"constraint(s) are still open: {open_holds[0]!r}")
    entries = dict(state.entries)
    entries[slug] = updated
    return VisitsState(entries=entries)
