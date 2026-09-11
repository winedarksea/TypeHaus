"""Writing ``inspections.toml``, the ops that change it, and the migration into attempts.

Split from ``inspection_state.py`` so each file stays under 500 lines and each has one job:
that one is the vocabulary and the loader, this one is everything that produces a new file.

Deterministic on purpose — ids sorted, one field per line, empties dropped — because the
file is under version control and ``git diff`` is the change review for both the owner and
the agent.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any


def toml_string(text: str) -> str:
    """A TOML basic string, with the non-ASCII left ALONE.

    ``json.dumps`` escapes an em dash to ``\\u2014``, which is legal TOML and unreadable in a
    file whose whole point is that a person edits it by hand — "Saint Paul DSI —
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


def _key(name: str) -> str:
    """A bare TOML key where it is one, quoted where it is not (an instance's slash)."""
    import re

    return name if re.fullmatch(r"[A-Za-z0-9_-]+", name) else toml_string(name)


def _inline(fields: tuple[str, ...], values: Mapping[str, Any]) -> str:
    parts = [f"{name} = {_toml_value(values[name])}" for name in fields
             if values.get(name) not in (None, "", (), [], False)]
    return "{ " + ", ".join(parts) + " }"


def write_inspections(house_dir: Path, state: Any) -> Path:
    """Serialize deterministically: ids sorted, one field per line, empties dropped."""
    from typehaus.schedule.inspection_state import (
        _EXTRA_FIELDS,
        ATTEMPT_FIELDS,
        AUTHORITY_FIELDS,
        INSPECTIONS_FILENAME,
        PERMIT_FIELDS,
        WAIVER_FIELDS,
    )

    lines = ["# inspections.toml — what the AHJ said, beside what the code requires.",
             "# Written by Type:Haus and safe to edit by hand. See",
             "# docs/site-state-format.md. Dates are prose: nothing here is computed.", ""]
    if not state.permit.is_empty:
        lines.append("[permit]")
        for name in PERMIT_FIELDS:
            value = getattr(state.permit, name)
            if value:
                lines.append(f"{name} = {_toml_value(value)}")
        lines.append("")
    for key in sorted(state.authorities):
        authority = state.authorities[key]
        lines.append(f"[authorities.{key}]")
        for name in AUTHORITY_FIELDS:
            value = getattr(authority, name)
            if value is not None:
                lines.append(f"{name} = {_toml_value(value)}")
        lines.append("")
    for key in sorted(state.entries):
        entry = state.entries[key]
        if entry.is_empty:
            continue
        lines.append(f"[entries.{_key(key)}]")
        for name in ("requested", "scheduled", "inspector", "note"):
            if getattr(entry, name):
                lines.append(f"{name} = {_toml_value(getattr(entry, name))}")
        for name in ("scope", "checked", "requires"):
            if getattr(entry, name):
                lines.append(f"{name} = {_toml_value(getattr(entry, name))}")
        if entry.waived is not None:
            lines.append(f"waived = {_inline(WAIVER_FIELDS, entry.waived.as_dict())}")
        if entry.attempts:
            lines.append("attempts = [")
            for attempt in entry.attempts:
                lines.append(f"  {_inline(ATTEMPT_FIELDS, attempt.as_dict())},")
            lines.append("]")
        lines.append("")
    for item in sorted(state.extra, key=lambda x: x.id):
        lines.append("[[extra]]")
        for name in _EXTRA_FIELDS:
            value = getattr(item, name)
            if value:
                lines.append(f"{name} = {_toml_value(value)}")
        lines.append("")
    from typehaus.takeoff.atomic import atomic_write_text

    return atomic_write_text(Path(house_dir) / INSPECTIONS_FILENAME,
                             "\n".join(lines).rstrip("\n") + "\n")


_OPS = ("set_inspection", "add_attempt", "set_instance", "set_authority", "set_permit",
        "set_extra_inspection", "remove_extra_inspection")


def apply_inspection_op(state: Any, op: Mapping[str, Any]) -> Any:
    """One state transition. ``ValueError`` on a malformed op; the server maps that to 400."""
    kind = str(op.get("op") or "")
    if kind not in _OPS:
        raise ValueError(f"unknown inspection op {kind!r}; expected one of {list(_OPS)}")
    return globals()[f"_{kind}"](state, op)


def _set_inspection(state: Any, op: Mapping[str, Any]) -> Any:
    """Booking, on-site ticks, the note and the waiver. **Never** a result.

    A result only ever arrives as an attempt, because the failure this replaces was a single
    slot that a second call overwrote.
    """
    from typehaus.schedule.inspection_state import ENTRY_FIELDS, InspectionEntry, _waiver

    key = str(op.get("id") or "")
    if not key:
        raise ValueError("set_inspection: missing id")
    settable = set(ENTRY_FIELDS) - {"attempts"}
    unknown = set(op) - {"op", "id"} - settable
    if unknown:
        raise ValueError(f"set_inspection: unknown field(s) {sorted(unknown)}; a result is "
                         "recorded with add_attempt, never by overwriting one")
    values: dict[str, Any] = {}
    for name in ("requested", "scheduled", "inspector", "note"):
        if name in op:
            values[name] = str(op[name]) if op[name] else None
    for name in ("scope", "checked", "requires"):
        if name in op:
            values[name] = tuple(str(item) for item in (op[name] or ()))
    if "waived" in op:
        values["waived"] = (_waiver(op["waived"], "set_inspection")
                            if op["waived"] else None)
    updated = replace(state.entries.get(key, InspectionEntry()), **values)
    return _stored(state, key, updated)


def _add_attempt(state: Any, op: Mapping[str, Any]) -> Any:
    """Append one visit by the inspector. Nothing overwrites; the list only grows."""
    from typehaus.schedule.inspection_state import InspectionEntry, _attempts

    key = str(op.get("id") or "")
    if not key:
        raise ValueError("add_attempt: missing id")
    fields = {k: v for k, v in op.items() if k not in ("op", "id")}
    attempt = _attempts([fields], "add_attempt")[0]
    current = state.entries.get(key, InspectionEntry())
    updated = replace(current, attempts=current.attempts + (attempt,))
    # `reinspect` is not a field: the next booking after a fail is the next `scheduled`,
    # and keeping one date in two places is how the two disagree.
    if attempt.result == "fail":
        updated = replace(updated, scheduled=None)
    return _stored(state, key, updated)


def _set_instance(state: Any, op: Mapping[str, Any]) -> Any:
    """Create or re-scope a second instance of one spec: ``footing`` -> ``footing/court``."""
    from typehaus.schedule.inspection_state import InspectionEntry, spec_of

    key = str(op.get("id") or "")
    if "/" not in key:
        raise ValueError("set_instance: an instance id is \"<spec>/<name>\"; the bare "
                         "spec id is the default instance and always exists")
    if not spec_of(key):
        raise ValueError(f"set_instance: {key!r} names no spec before the slash")
    current = state.entries.get(key, InspectionEntry())
    scope = tuple(str(item) for item in (op.get("scope") or current.scope))
    if not scope:
        raise ValueError(f"set_instance {key!r}: a second instance needs a 'scope' — "
                         "element-tag globs and/or visit slugs it covers")
    return _stored(state, key, replace(current, scope=scope))


def _set_authority(state: Any, op: Mapping[str, Any]) -> Any:
    from typehaus.schedule.inspection_state import AUTHORITY_FIELDS, METHODS, Authority

    key = str(op.get("key") or "")
    if not key:
        raise ValueError("set_authority: missing key")
    unknown = set(op) - {"op", "key"} - set(AUTHORITY_FIELDS)
    if unknown:
        raise ValueError(f"set_authority: unknown field(s) {sorted(unknown)}")
    if op.get("method") and str(op["method"]) not in METHODS:
        raise ValueError(f"set_authority: method {op['method']!r}; "
                         f"expected one of {list(METHODS)}")
    current = state.authorities.get(key)
    values = {name: getattr(current, name) if current else None
              for name in AUTHORITY_FIELDS}
    values["label"] = values["label"] or key
    for name in AUTHORITY_FIELDS:
        if name in op:
            values[name] = (int(op[name]) if name == "lead_days" and op[name] is not None
                            else (str(op[name]) if op[name] else None))
    if not values["label"]:
        raise ValueError("set_authority: an authority needs a 'label'")
    authorities = dict(state.authorities)
    authorities[key] = Authority(**values)
    return replace(state, authorities=authorities)


def _set_permit(state: Any, op: Mapping[str, Any]) -> Any:
    from typehaus.schedule.inspection_state import PERMIT_FIELDS, Permit

    unknown = set(op) - {"op"} - set(PERMIT_FIELDS)
    if unknown:
        raise ValueError(f"set_permit: unknown field(s) {sorted(unknown)}")
    values = {name: getattr(state.permit, name) for name in PERMIT_FIELDS}
    for name in PERMIT_FIELDS:
        if name in op:
            values[name] = str(op[name]) if op[name] else None
    return replace(state, permit=Permit(**values))


def _set_extra_inspection(state: Any, op: Mapping[str, Any]) -> Any:
    from typehaus.schedule.inspection_state import _EXTRA_FIELDS, ExtraInspection

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
        applies_when=(str(op["applies_when"]) if op.get("applies_when") else None))
    return replace(state, extra=tuple(x for x in state.extra if x.id != item.id) + (item,))


def _remove_extra_inspection(state: Any, op: Mapping[str, Any]) -> Any:
    inspection_id = str(op.get("id") or "")
    if not inspection_id:
        raise ValueError("remove_extra_inspection: missing id")
    return replace(state, extra=tuple(x for x in state.extra if x.id != inspection_id))


def _stored(state: Any, key: str, entry: Any) -> Any:
    entries = dict(state.entries)
    if entry.is_empty:
        entries.pop(key, None)
    else:
        entries[key] = entry
    return replace(state, entries=entries)


def migrate_entries(path: Path) -> tuple[Any, list[str]]:
    """Read a file in the pre-attempts spelling and return ``(state, what moved)``.

    The real loader refuses the old fields by design — a mistyped key must never become an
    ignored one — so the migration reads the file itself rather than asking the loader for a
    permissive mode.

    ``result`` + ``result_date`` + ``inspector`` become one attempt. Each ``history`` line
    becomes an attempt of its own where it parses as ``"<date> <result>[ note]"``, and a
    note-only attempt otherwise, because the vocabulary was write-only and nothing appended
    to it in a fixed shape. ``reinspect`` becomes the next ``scheduled``. A string ``waived``
    becomes a table whose ``by`` is the string, so the claim keeps its author. ``partial``
    is preserved as ``partial`` — it used to collapse to ``failed``.
    """
    from typehaus.schedule.inspection_state import (
        Attempt,
        InspectionEntry,
        InspectionsState,
        Waiver,
        _authority,
        _extra,
        _flatten_entries,
        _permit,
    )

    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover
        import tomli as tomllib  # type: ignore[no-redef,import-not-found]

    path = Path(path)
    if not path.exists():
        return InspectionsState(), []
    data = tomllib.loads(path.read_text())
    raw_entries = _flatten_entries(data.get("entries") or {})
    entries: dict[str, Any] = {}
    changes: list[str] = []
    for key, body in sorted(raw_entries.items()):
        entry, moved = _migrate_entry(key, dict(body), Attempt, InspectionEntry, Waiver)
        entries[key] = entry
        changes.extend(moved)
    state = InspectionsState(
        authorities={str(k): _authority(str(k), v, path)
                     for k, v in (data.get("authorities") or {}).items()},
        entries=entries,
        extra=tuple(_extra(v, path, i)
                    for i, v in enumerate(data.get("extra") or [])),
        permit=_permit(data.get("permit"), path))
    return state, changes


_LEGACY = ("result", "result_date", "reinspect", "history")


def _migrate_entry(key: str, body: dict[str, Any], Attempt: Any, InspectionEntry: Any,
                   Waiver: Any) -> tuple[Any, list[str]]:
    changes: list[str] = []
    attempts: list[Any] = []
    for line in body.pop("history", ()) or ():
        attempts.append(_history_attempt(str(line), Attempt))
        changes.append(f"[entries.{key}] history line {str(line)!r} -> attempts")
    result = body.pop("result", None)
    result_date = body.pop("result_date", None)
    if result:
        attempts.append(Attempt(
            date=str(result_date or ""), result=str(result),
            inspector=str(body["inspector"]) if body.get("inspector") else None,
            approved=("*",) if str(result) == "partial" else (),
            note=("scope unrecorded: the old spelling had no approved list"
                  if str(result) == "partial" else None)))
        changes.append(f"[entries.{key}] result {str(result)!r} -> one attempt")
    reinspect = body.pop("reinspect", None)
    if reinspect:
        body["scheduled"] = str(reinspect)
        changes.append(f"[entries.{key}] reinspect -> scheduled")
    waived = body.get("waived")
    if isinstance(waived, str) and waived:
        body["waived"] = Waiver(by=waived, note="migrated from a bare string")
        changes.append(f"[entries.{key}] waived string -> a table naming who granted it")
    elif isinstance(waived, dict):
        body["waived"] = Waiver(**{k: str(v) for k, v in waived.items()})
    values = {name: body.get(name) for name in
              ("requested", "scheduled", "inspector", "note", "waived")}
    lists = {name: tuple(str(x) for x in (body.get(name) or ()))
             for name in ("scope", "checked", "requires")}
    return InspectionEntry(attempts=tuple(attempts), **values, **lists), changes


def _history_attempt(line: str, Attempt: Any) -> Any:
    """``"2027-05-05 fail bolts off layout"`` where it parses; a dated note otherwise."""
    from typehaus.schedule.inspection_state import RESULTS

    parts = line.split(None, 2)
    if len(parts) >= 2 and parts[1] in RESULTS:
        return Attempt(date=parts[0], result=parts[1],
                       approved=("*",) if parts[1] == "partial" else (),
                       note=parts[2] if len(parts) > 2 else None)
    return Attempt(date=parts[0] if parts else "", result="fail",
                   note=f"migrated history line, result not stated: {line}")
