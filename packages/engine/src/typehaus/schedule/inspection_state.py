"""``inspections.toml`` — what the AHJ actually said, beside what the code requires.

Same idiom as ``takeoff/costs.py`` and ``takeoff/task_state.py``: the loader raises on a
malformed file naming the offending key, the writer is deterministic and sorted, and
neither depends on the server. Outside the PatchOp/undo journal, like the other two — a
passed inspection is not a plan edit, and undo must never un-pass one.

**The engine reads this file and never writes it during a build.** Only an explicit
``PUT /inspections`` writes, exactly as ``engineering.toml`` is read and never written.

Two things that look alike and are not. ``waived`` is the AHJ saying this inspection is not
required *here* — a fact about the jurisdiction's discretion. ``not_applicable`` is this
building not having the condition the inspection covers — a fact about the model, earned
from positive evidence in :mod:`typehaus.schedule.applicability`. Neither is derivable from
the other and conflating them would let a shrug close a gate.
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

INSPECTIONS_FILENAME = "inspections.toml"

#: What an AHJ writes on the card. ``partial`` is real and common — half the house passed
#: and the inspector wants a second look at one corner — and folding it into ``fail`` would
#: lose the distinction the owner schedules against.
RESULTS = ("pass", "fail", "partial")

_ENTRY_FIELDS = ("requested", "scheduled", "inspector", "result", "result_date",
                 "reinspect", "history", "checked", "requires", "waived", "note")
_LIST_FIELDS = ("history", "checked", "requires")
_AUTHORITY_FIELDS = ("label", "phone", "window", "lead_days")
_EXTRA_FIELDS = ("id", "label", "authority", "after", "gates", "check_ids", "on_site",
                 "code_refs", "milestone", "applies_when")


@dataclass(frozen=True)
class Authority:
    """Who to call. House-owned: the engine ships no phone numbers."""

    label: str
    phone: str | None = None
    #: When they take calls, as the AHJ words it: ``"7:30-9:00 M-F"``.
    window: str | None = None
    #: Business days' notice they ask for. A number the *jurisdiction* states, not one the
    #: engine derives — nothing here computes a date from it.
    lead_days: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"label": self.label, "phone": self.phone, "window": self.window,
                "lead_days": self.lead_days}


@dataclass(frozen=True)
class InspectionEntry:
    """The owner's record of one inspection, keyed by the spec id."""

    requested: str | None = None
    scheduled: str | None = None
    inspector: str | None = None
    result: str | None = None
    result_date: str | None = None
    reinspect: str | None = None
    history: tuple[str, ...] = ()
    checked: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    waived: str | None = None
    note: str | None = None

    @property
    def is_empty(self) -> bool:
        return not any(getattr(self, name) for name in _ENTRY_FIELDS)

    def as_dict(self) -> dict[str, Any]:
        return {name: (list(getattr(self, name)) if name in _LIST_FIELDS
                       else getattr(self, name))
                for name in _ENTRY_FIELDS}


@dataclass(frozen=True)
class ExtraInspection:
    """An inspection this house needs that the profile does not list.

    catlin's girt-screw hold is one: ``authority = "owner"``, because a hold the owner
    placed on themselves is not an AHJ visit and giving it a phone number would be a lie.
    """

    id: str
    label: str
    authority: str = "building"
    after: tuple[str, ...] = ()
    gates: tuple[str, ...] = ()
    check_ids: tuple[str, ...] = ()
    on_site: tuple[str, ...] = ()
    code_refs: tuple[str, ...] = ()
    milestone: str = ""
    applies_when: str | None = None

    def as_spec(self) -> Any:
        from typehaus.checks.jurisdiction import InspectionSpec

        return InspectionSpec(id=self.id, label=self.label, authority=self.authority,
                              after=self.after, gates=self.gates,
                              check_ids=self.check_ids, on_site=self.on_site,
                              code_refs=self.code_refs, milestone=self.milestone,
                              applies_when=self.applies_when)


@dataclass(frozen=True)
class InspectionsState:
    authorities: Mapping[str, Authority] = field(default_factory=dict)
    entries: Mapping[str, InspectionEntry] = field(default_factory=dict)
    extra: tuple[ExtraInspection, ...] = ()

    def entry(self, inspection_id: str) -> InspectionEntry | None:
        return self.entries.get(inspection_id)


def _strings(raw: Any, where: str, name: str) -> tuple[str, ...]:
    if isinstance(raw, str) or not isinstance(raw, (list, tuple)):
        raise ValueError(f"{where}: {name!r} must be an array of strings")
    return tuple(str(item) for item in raw)


def _entry(inspection_id: str, raw: Any, path: Path) -> InspectionEntry:
    where = f"{path}: [entries.{inspection_id}]"
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be a table")
    unknown = set(raw) - set(_ENTRY_FIELDS)
    if unknown:
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}; "
                         f"expected {list(_ENTRY_FIELDS)}")
    result = raw.get("result")
    if result is not None and str(result) not in RESULTS:
        raise ValueError(f"{where}: result {result!r}; expected one of {list(RESULTS)}")
    values: dict[str, Any] = {}
    for name in _ENTRY_FIELDS:
        if name in _LIST_FIELDS:
            values[name] = _strings(raw[name], where, name) if raw.get(name) else ()
        else:
            values[name] = str(raw[name]) if raw.get(name) else None
    return InspectionEntry(**values)


def _authority(key: str, raw: Any, path: Path) -> Authority:
    where = f"{path}: [authorities.{key}]"
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be a table")
    unknown = set(raw) - set(_AUTHORITY_FIELDS)
    if unknown:
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}; "
                         f"expected {list(_AUTHORITY_FIELDS)}")
    if "label" not in raw:
        raise ValueError(f"{where}: missing 'label'")
    lead = raw.get("lead_days")
    return Authority(label=str(raw["label"]),
                     phone=str(raw["phone"]) if raw.get("phone") else None,
                     window=str(raw["window"]) if raw.get("window") else None,
                     lead_days=int(lead) if lead is not None else None)


def _extra(raw: Any, path: Path, index: int) -> ExtraInspection:
    where = f"{path}: [[extra]] #{index + 1}"
    if not isinstance(raw, dict):
        raise ValueError(f"{where} must be a table")
    unknown = set(raw) - set(_EXTRA_FIELDS)
    if unknown:
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}; "
                         f"expected {list(_EXTRA_FIELDS)}")
    for required in ("id", "label"):
        if not raw.get(required):
            raise ValueError(f"{where}: missing {required!r}")
    return ExtraInspection(
        id=str(raw["id"]), label=str(raw["label"]),
        authority=str(raw.get("authority", "building")),
        after=_strings(raw["after"], where, "after") if raw.get("after") else (),
        gates=_strings(raw["gates"], where, "gates") if raw.get("gates") else (),
        check_ids=(_strings(raw["check_ids"], where, "check_ids")
                   if raw.get("check_ids") else ()),
        on_site=_strings(raw["on_site"], where, "on_site") if raw.get("on_site") else (),
        code_refs=(_strings(raw["code_refs"], where, "code_refs")
                   if raw.get("code_refs") else ()),
        milestone=str(raw.get("milestone") or ""),
        applies_when=str(raw["applies_when"]) if raw.get("applies_when") else None,
    )


def load_inspections(house_dir: Path) -> InspectionsState:
    """Read ``inspections.toml`` if the house carries one; an absent file is empty state."""
    path = Path(house_dir) / INSPECTIONS_FILENAME
    if not path.exists():
        return InspectionsState()
    data = tomllib.loads(path.read_text())
    unknown = set(data) - {"authorities", "entries", "extra"}
    if unknown:
        raise ValueError(f"{path}: unknown top-level key(s) {sorted(unknown)}; expected "
                         "[authorities.<id>], [entries.<id>], [[extra]]")
    raw_extra = data.get("extra") or []
    if not isinstance(raw_extra, list):
        raise ValueError(f"{path}: 'extra' must be an array of tables ([[extra]])")
    return InspectionsState(
        authorities={str(key): _authority(str(key), raw, path)
                     for key, raw in (data.get("authorities") or {}).items()},
        entries={str(key): _entry(str(key), raw, path)
                 for key, raw in (data.get("entries") or {}).items()},
        extra=tuple(_extra(raw, path, i) for i, raw in enumerate(raw_extra)),
    )


def toml_string(text: str) -> str:
    """A TOML basic string, with the non-ASCII left ALONE.

    ``json.dumps`` escapes an em dash to ``\u2014``, which is legal TOML and unreadable in a
    file whose whole point is that a person edits it by hand — "Saint Paul DSI \u2014
    Inspections" is not a label anybody wants to correct a phone number next to.
    """
    return json.dumps(str(text), ensure_ascii=False)


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(toml_string(item) for item in value) + "]"
    return toml_string(value)


def write_inspections(house_dir: Path, state: InspectionsState) -> Path:
    """Serialize deterministically: ids sorted, one field per line, empties dropped."""
    lines = ["# inspections.toml — what the AHJ said, beside what the code requires.",
             "# Written by Type:Haus and safe to edit by hand. See",
             "# docs/site-state-format.md. Dates are prose: nothing here is computed.", ""]
    for key in sorted(state.authorities):
        authority = state.authorities[key]
        lines.append(f"[authorities.{key}]")
        for name in _AUTHORITY_FIELDS:
            value = getattr(authority, name)
            if value is not None:
                lines.append(f"{name} = {_toml_value(value)}")
        lines.append("")
    for key in sorted(state.entries):
        entry = state.entries[key]
        if entry.is_empty:
            continue
        lines.append(f"[entries.{key}]")
        for name in _ENTRY_FIELDS:
            value = getattr(entry, name)
            if value:
                lines.append(f"{name} = {_toml_value(value)}")
        lines.append("")
    for item in sorted(state.extra, key=lambda x: x.id):
        lines.append("[[extra]]")
        for name in _EXTRA_FIELDS:
            value = getattr(item, name)
            if value:
                lines.append(f"{name} = {_toml_value(value)}")
        lines.append("")
    path = Path(house_dir) / INSPECTIONS_FILENAME
    path.write_text("\n".join(lines).rstrip("\n") + "\n")
    return path


def apply_inspection_op(state: InspectionsState, op: Mapping[str, Any]) -> InspectionsState:
    """One state transition. ``ValueError`` on a malformed op; the server maps that to 400."""
    kind = op.get("op")
    if kind == "set_inspection":
        return _set_inspection(state, op)
    if kind == "set_extra_inspection":
        return _set_extra(state, op)
    if kind == "remove_extra_inspection":
        inspection_id = str(op.get("id") or "")
        if not inspection_id:
            raise ValueError("remove_extra_inspection: missing id")
        return replace(state, extra=tuple(x for x in state.extra if x.id != inspection_id))
    raise ValueError(f"unknown inspection op {kind!r}; expected set_inspection, "
                     "set_extra_inspection or remove_extra_inspection")


def _set_inspection(state: InspectionsState, op: Mapping[str, Any]) -> InspectionsState:
    inspection_id = str(op.get("id") or "")
    if not inspection_id:
        raise ValueError("set_inspection: missing id")
    unknown = set(op) - {"op", "id"} - set(_ENTRY_FIELDS)
    if unknown:
        raise ValueError(f"set_inspection: unknown field(s) {sorted(unknown)}")
    if op.get("result") is not None and str(op["result"]) not in RESULTS:
        raise ValueError(f"set_inspection: result {op['result']!r}; "
                         f"expected one of {list(RESULTS)}")
    values: dict[str, Any] = {}
    for name in _ENTRY_FIELDS:
        if name not in op:
            continue
        raw = op[name]
        if name in _LIST_FIELDS:
            values[name] = tuple(str(item) for item in (raw or ()))
        else:
            values[name] = str(raw) if raw else None
    updated = replace(state.entries.get(inspection_id, InspectionEntry()), **values)
    entries = dict(state.entries)
    if updated.is_empty:
        entries.pop(inspection_id, None)
    else:
        entries[inspection_id] = updated
    return replace(state, entries=entries)


def _set_extra(state: InspectionsState, op: Mapping[str, Any]) -> InspectionsState:
    unknown = set(op) - {"op"} - set(_EXTRA_FIELDS)
    if unknown:
        raise ValueError(f"set_extra_inspection: unknown field(s) {sorted(unknown)}")
    for required in ("id", "label"):
        if not op.get(required):
            raise ValueError(f"set_extra_inspection: missing {required!r}")
    item = ExtraInspection(
        id=str(op["id"]), label=str(op["label"]),
        authority=str(op.get("authority", "building")),
        after=tuple(str(x) for x in (op.get("after") or ())),
        gates=tuple(str(x) for x in (op.get("gates") or ())),
        check_ids=tuple(str(x) for x in (op.get("check_ids") or ())),
        on_site=tuple(str(x) for x in (op.get("on_site") or ())),
        code_refs=tuple(str(x) for x in (op.get("code_refs") or ())),
        milestone=str(op.get("milestone") or ""),
        applies_when=(str(op["applies_when"]) if op.get("applies_when") else None),
    )
    return replace(state, extra=tuple(x for x in state.extra if x.id != item.id) + (item,))
