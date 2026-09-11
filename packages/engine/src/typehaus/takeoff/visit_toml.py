"""Serialising ``[visits]`` back to TOML, and the ops that change one.

Split from ``visit_state.py``: the dataclasses and the parser are one job, the writer and
the op vocabulary another, and together they are past 500 lines.

The writer is deterministic — slugs sorted, one field per line, empties dropped — because
the file is under version control and ``git diff`` is the change review. There is no journal
file: every status-changing op stamps ``updated`` and appends one ``log`` line, in the TOML,
where a person editing the file by hand can see it.

The ops live at this layer, not in ``schedule/``, because they write persisted state and
``schedule/`` is a leaf that imports this package. ``schedule/site_ops.py`` is the router
that folds a request's ops through here and through ``inspection_state``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any


def toml_string(text: str) -> str:
    """A TOML basic string with the non-ASCII left alone — see inspection_state.toml_string."""
    return json.dumps(str(text), ensure_ascii=False)


def toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(toml_string(item) for item in value) + "]"
    return toml_string(value)


def _inline(fields: tuple[str, ...], values: Mapping[str, Any]) -> str:
    """``{ a = "x", b = 3 }`` — only the fields that carry something."""
    parts = [f"{name} = {toml_value(values[name])}" for name in fields
             if values.get(name) not in (None, "", (), [], False)]
    return "{ " + ", ".join(parts) + " }"


def visit_lines(state: Any) -> list[str]:
    """The ``[visits]`` half of ``write_tasks``: slugs sorted, one field per line."""
    from typehaus.takeoff.visit_state import (
        BOOKING_FIELDS,
        CHECKPOINT_FIELDS,
        CONSTRAINT_FIELDS,
        FLAG_FIELDS,
        INT_FIELDS,
        LIST_FIELDS,
        MATERIAL_FIELDS,
        SCALAR_FIELDS,
    )

    lines: list[str] = []
    for slug in sorted(state.entries):
        entry = state.entries[slug]
        lines.append(f"[visits.{toml_string(slug)}]")
        for name in SCALAR_FIELDS:
            value = getattr(entry, name)
            if value:
                lines.append(f"{name} = {toml_string(value)}")
        for name in INT_FIELDS:
            if getattr(entry, name) is not None:
                lines.append(f"{name} = {toml_value(getattr(entry, name))}")
        if entry.booked is not None:
            lines.append(f"booked = {_inline(BOOKING_FIELDS, entry.booked.as_dict())}")
        for name in FLAG_FIELDS:
            # `blocks_successors` defaults true and `shared_rows` false, so each is written
            # only when the owner said the non-default thing.
            if getattr(entry, name) is not (name == "blocks_successors"):
                lines.append(f"{name} = {toml_value(getattr(entry, name))}")
        for name in LIST_FIELDS:
            value = getattr(entry, name)
            if value:
                items = ", ".join(toml_string(item) for item in value)
                lines.append(f"{name} = [{items}]")
        for name, fields in (("constraints", CONSTRAINT_FIELDS),
                             ("checkpoints", CHECKPOINT_FIELDS),
                             ("exceptions", ("at", "hold", "note")),
                             ("skipped", ("id", "reason")),
                             ("materials", MATERIAL_FIELDS),
                             ("log", ("at", "from", "to", "ref"))):
            rows = getattr(entry, name)
            if not rows:
                continue
            lines.append(f"{name} = [")
            for row in rows:
                lines.append(f"  {_inline(fields, row.as_dict())},")
            lines.append("]")
        lines.append("")
    return lines


def now_stamp() -> str:
    """The one clock this package reads, and it stamps history — never a schedule."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _logged(entry: Any, before: str, after: str, ref: str, at: str) -> Any:
    from typehaus.takeoff.visit_state import LOG_LIMIT, LogLine

    if before == after:
        return replace(entry, updated=at)
    line = LogLine(at=at, to=after, from_=before, ref=ref)
    return replace(entry, updated=at, log=(entry.log + (line,))[-LOG_LIMIT:])


def entry_rule_errors(slug: str, entry: Any) -> list[str]:
    """The rules a single ``[visits]`` table must satisfy, at load and on every op.

    Entry-local only. "Every handoff item is ticked" and "every inspection this visit
    depends on is resolved" are the other two halves of verification and they need the whole
    board, so ``schedule/rules.py`` owns them — and ``schedule/site_ops.py`` runs both sets
    before any write, which is why a hand edit and a UI write are refused in the same words.
    """
    out: list[str] = []
    if entry.checkpoints and entry.status not in ("todo", "verified"):
        out.append(f"status {entry.status!r} is derived from the checkpoints on a "
                   "checkpointed visit — write the status on the checkpoint instead "
                   "(only 'verified' stays a visit-level fact)")
    if entry.status == "verified":
        open_holds = [c.label for c in entry.constraints
                      if c.cleared is None and c.severity == "blocking"]
        if open_holds:
            out.append(f"cannot be verified while {len(open_holds)} hold(s) are still "
                       f"open: {open_holds[0]!r}")
    ticked = set(entry.checked)
    both = sorted(ticked.intersection(item.id for item in entry.skipped))
    if both:
        out.append(f"handoff item {both[0]!r} is both ticked and skipped")
    for point in entry.checkpoints:
        if point.cure_days is not None and point.cure_days < 0:
            out.append(f"checkpoint {point.id!r}: cure_days {point.cure_days} is negative")
    return out


_OPS = ("set_visit", "set_checkpoint", "tick_handoff", "skip_handoff", "clear_hold",
        "add_hold", "add_exception")


def apply_visit_op(state: Any, op: Mapping[str, Any]) -> Any:
    """Fold one visit op. ``ValueError`` on a malformed one — the server 400s."""
    kind = str(op.get("op") or "")
    if kind not in _OPS:
        raise ValueError(f"unknown visit op {kind!r}; expected one of {list(_OPS)}")
    slug = str(op.get("slug") or "")
    if not slug:
        raise ValueError(f"{kind}: missing slug")
    handler = globals()[f"_{kind}"]
    from typehaus.takeoff.visit_state import VisitEntry, VisitsState

    current = state.entries.get(slug, VisitEntry())
    at = str(op.get("at") or now_stamp())
    updated = handler(slug, current, op, at)
    entries = dict(state.entries)
    entries[slug] = updated
    return VisitsState(entries=entries)


def _set_visit(slug: str, current: Any, op: Mapping[str, Any], at: str) -> Any:
    from typehaus.takeoff.visit_state import (
        FLAG_FIELDS,
        INT_FIELDS,
        LIST_FIELDS,
        SCALAR_FIELDS,
        VISIT_STATUSES,
        _booking,
        _materials,
        constraints_from,
    )

    unknown = set(op) - {"op", "slug", "at", "cleared", "constraints", "checkpoints",
                         "booked", "materials"} \
        - set(SCALAR_FIELDS) - set(FLAG_FIELDS) - set(LIST_FIELDS) - set(INT_FIELDS)
    if unknown:
        raise ValueError(f"set_visit: unknown field(s) {sorted(unknown)}")
    if "status" in op and op["status"] not in VISIT_STATUSES:
        raise ValueError(f"set_visit: status {op['status']!r}; "
                         f"expected one of {list(VISIT_STATUSES)}")
    values: dict[str, Any] = {}
    for name in SCALAR_FIELDS:
        if name in op and name != "updated":
            values[name] = str(op[name]) if op[name] else (
                "" if name in ("label",) else None)
    for name in INT_FIELDS:
        if name in op:
            values[name] = int(op[name]) if op[name] is not None else None
    for name in FLAG_FIELDS:
        if name in op:
            values[name] = bool(op[name])
    if "booked" in op:
        values["booked"] = _booking(op["booked"], "set_visit") if op["booked"] else None
    if "materials" in op:
        values["materials"] = _materials(op["materials"] or [], "set_visit")
    for name in LIST_FIELDS:
        if name in op:
            values[name] = tuple(str(item) for item in (op[name] or ()))
    if "constraints" in op:
        values["constraints"] = constraints_from(op["constraints"], "set_visit")
    if "checkpoints" in op:
        from typehaus.takeoff.visit_state import checkpoints_from

        values["checkpoints"] = checkpoints_from(op["checkpoints"], "set_visit")
    updated = replace(current, **values)
    # `cleared` is a label -> date map rather than a whole constraint list, because the one
    # write a phone makes is a checkbox and resending the list would race the owner's own
    # edit of it in the file.
    if op.get("cleared"):
        marks = {str(k): (str(v) if v else None) for k, v in dict(op["cleared"]).items()}
        updated = replace(updated, constraints=tuple(
            replace(c, cleared=marks.get(c.label, c.cleared)) for c in updated.constraints))
    # Verification is refused against the state *this op arrives at*, and against the state
    # it started from: one request may not both clear the last hold and verify. That is the
    # owner claiming they walked work they were still unblocking as they typed.
    if updated.status == "verified" and current.status != "verified":
        # Refused against the state this op arrives at *and* the state it started from: one
        # request may not both clear the last hold and verify. That is the owner claiming
        # they walked work they were still unblocking as they typed.
        errors = entry_rule_errors(slug, replace(current, status="verified"))
        if errors:
            raise ValueError(f"set_visit {slug!r}: {errors[0]} (before this request)")
    errors = entry_rule_errors(slug, updated)
    if errors:
        raise ValueError(f"set_visit {slug!r}: {errors[0]}")
    return _logged(updated, current.derived_status, updated.derived_status, "", at)


def _set_checkpoint(slug: str, current: Any, op: Mapping[str, Any], at: str) -> Any:
    from typehaus.takeoff.visit_state import CHECKPOINT_STATUSES

    checkpoint_id = str(op.get("checkpoint") or "")
    point = current.checkpoint(checkpoint_id)
    if point is None:
        raise ValueError(f"set_checkpoint {slug!r}: no checkpoint {checkpoint_id!r}; "
                         f"this visit has {[p.id for p in current.checkpoints]}")
    status = str(op.get("status") or point.status)
    if status not in CHECKPOINT_STATUSES:
        raise ValueError(f"set_checkpoint: status {status!r}; "
                         f"expected one of {list(CHECKPOINT_STATUSES)}")
    values: dict[str, Any] = {"status": status}
    for name in ("started", "completed"):
        if name in op:
            values[name] = str(op[name]) if op[name] else None
    replaced = replace(point, **values)
    updated = replace(current, checkpoints=tuple(
        replaced if p.id == checkpoint_id else p for p in current.checkpoints))
    return _logged(updated, current.derived_status, updated.derived_status,
                   checkpoint_id, at)


def _tick_handoff(slug: str, current: Any, op: Mapping[str, Any], at: str) -> Any:
    item = str(op.get("item") or "")
    if not item:
        raise ValueError("tick_handoff: missing item")
    ticked = tuple(dict.fromkeys(current.checked + (item,)))
    return replace(current, checked=ticked,
                   skipped=tuple(s for s in current.skipped if s.id != item), updated=at)


def _skip_handoff(slug: str, current: Any, op: Mapping[str, Any], at: str) -> Any:
    from typehaus.takeoff.visit_state import SkippedItem

    item, reason = str(op.get("item") or ""), str(op.get("reason") or "")
    if not item or not reason:
        raise ValueError("skip_handoff: needs 'item' and a 'reason' — a skip without one "
                         "is a tick nobody can audit")
    return replace(current, checked=tuple(c for c in current.checked if c != item),
                   skipped=tuple(s for s in current.skipped if s.id != item)
                   + (SkippedItem(item, reason),), updated=at)


def _clear_hold(slug: str, current: Any, op: Mapping[str, Any], at: str) -> Any:
    label = str(op.get("label") or "")
    if not any(c.label == label for c in current.constraints):
        raise ValueError(f"clear_hold {slug!r}: no hold labelled {label!r}")
    when = str(op.get("cleared") or at)
    return replace(current, updated=at, constraints=tuple(
        replace(c, cleared=when) if c.label == label else c for c in current.constraints))


def _add_hold(slug: str, current: Any, op: Mapping[str, Any], at: str) -> Any:
    from typehaus.takeoff.visit_state import constraints_from

    fields = {k: v for k, v in op.items() if k not in ("op", "slug", "at")}
    held = constraints_from([fields], "add_hold")
    if any(c.label == held[0].label for c in current.constraints):
        raise ValueError(f"add_hold {slug!r}: a hold labelled {held[0].label!r} is already "
                         "on this visit")
    return replace(current, constraints=current.constraints + held, updated=at)


def _add_exception(slug: str, current: Any, op: Mapping[str, Any], at: str) -> Any:
    from typehaus.takeoff.visit_state import VisitException

    hold = str(op.get("hold") or "")
    if not hold:
        raise ValueError("add_exception: missing 'hold' — an exception names the hold it "
                         "went ahead against")
    item = VisitException(at=at, hold=hold, note=str(op.get("note") or ""))
    return replace(current, exceptions=current.exceptions + (item,), updated=at)


__all__ = ["apply_visit_op", "entry_rule_errors", "now_stamp", "toml_string",
           "toml_value", "visit_lines"]
