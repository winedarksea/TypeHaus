"""One write path for every change to the site state, whoever is making it.

The CLI, ``PUT /tasks``, ``PUT /inspections`` and — later — an AI built into the UI all fold
their changes through :func:`apply_ops`. That is the whole point of an op vocabulary rather
than a file: an agent that edits TOML directly has to be trusted to reproduce every rule,
and an agent that calls ops only has to name what it wants.

Three things happen here that cannot happen in either file's own writer.

**The board-level rules run.** ``verified`` needs every handoff item ticked or skipped and
every inspection this visit depends on resolved, and neither of those is knowable from one
``[visits]`` table. ``takeoff/visit_toml.py`` enforces the entry-local half; this runs both,
so a hand edit and a UI write are refused in the same words.

**Both files move together or neither does.** A batch that renames a handoff item and ticks
it must not half-apply.

**A stale write is refused, not merged.** ``if_revision`` is the content hash the client got
from its ``GET``; a mismatch returns the fresh state rather than overwriting an edit the
owner made in their editor thirty seconds ago.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from typehaus.schedule.inspection_state import (
    INSPECTIONS_FILENAME,
    apply_inspection_op,
    load_inspections,
    write_inspections,
)
from typehaus.takeoff.atomic import revision
from typehaus.takeoff.task_state import TASKS_FILENAME, load_tasks, write_tasks
from typehaus.takeoff.visit_toml import apply_visit_op

#: Ops that change ``tasks.toml``'s ``[visits]``.
VISIT_OPS = ("set_visit", "set_checkpoint", "tick_handoff", "skip_handoff", "clear_hold",
             "add_hold", "add_exception")
#: Ops that change ``tasks.toml``'s ``[entries]`` — the package-level status ladder.
TASK_OPS = ("set_task",)
#: Ops that change ``inspections.toml``.
INSPECTION_OPS = ("set_inspection", "add_attempt", "set_instance", "set_authority",
                  "set_permit", "set_extra_inspection", "remove_extra_inspection")

OPS = (*VISIT_OPS, *TASK_OPS, *INSPECTION_OPS)


class SiteOpError(ValueError):
    """The request was malformed, or the result would break a rule. The server 400s."""


class StaleRevision(SiteOpError):
    """The client's ``if_revision`` is not the one on disk. The server 409s."""


def site_revision(house_dir: Path) -> str:
    """The version both files are at, together. Echoed by every GET."""
    directory = Path(house_dir)
    return revision(directory / TASKS_FILENAME, directory / INSPECTIONS_FILENAME)


def apply_ops(house_dir: Path, ops: Any, *, if_revision: str | None = None,
              validate_with: Any = None) -> str:
    """Fold ``ops`` over both files and write what changed. Returns the new revision.

    All-or-nothing: a bad op anywhere in the list persists nothing, so a client retry
    cannot half-apply a batch. ``validate_with`` is a callable that takes the two fresh
    states and returns a list of errors — the caller supplies it because the board-level
    rules need a resolved model and this module must not build one.
    """
    directory = Path(house_dir)
    if not isinstance(ops, list) or not ops:
        raise SiteOpError('body must be {"ops": [...]} with at least one op')
    current = site_revision(directory)
    if if_revision is not None and str(if_revision) != current:
        raise StaleRevision(
            f"site state has moved on: you sent if_revision {if_revision!r} and the files "
            f"are at {current!r}. Re-read and re-apply — nothing was written.")

    try:
        tasks = load_tasks(directory)
        inspections = load_inspections(directory)
    except ValueError as exc:
        raise SiteOpError(str(exc)) from exc

    # The state the REQUEST started from, kept so a verify can be graded against it. Two
    # ops in one request may not both clear the last hold and verify: that is the owner
    # claiming they walked work they were still unblocking as they typed, and grading the
    # verify against the state the earlier op in the same batch produced would allow it.
    opening = tasks.visits

    touched_tasks = touched_inspections = False
    for op in ops:
        if not isinstance(op, Mapping):
            raise SiteOpError(f"each op must be an object, got {op!r}")
        kind = str(op.get("op") or "")
        try:
            if kind in VISIT_OPS:
                if kind == "set_visit" and op.get("status") == "verified":
                    _refuse_a_same_request_verify(opening, str(op.get("slug") or ""))
                tasks = _with_visits(tasks, apply_visit_op(tasks.visits, op))
                touched_tasks = True
            elif kind in TASK_OPS:
                from typehaus.takeoff.task_state import apply_task_op

                tasks = apply_task_op(tasks, op)
                touched_tasks = True
            elif kind in INSPECTION_OPS:
                inspections = apply_inspection_op(inspections, op)
                touched_inspections = True
            else:
                raise SiteOpError(f"unknown op {kind!r}; expected one of {list(OPS)}")
        except ValueError as exc:
            raise SiteOpError(str(exc)) from exc

    if validate_with is not None:
        errors = list(validate_with(tasks, inspections) or ())
        if errors:
            raise SiteOpError("; ".join(errors[:3]))

    if touched_tasks:
        write_tasks(directory, tasks)
    if touched_inspections:
        write_inspections(directory, inspections)
    return site_revision(directory)


def _refuse_a_same_request_verify(opening: Any, slug: str) -> None:
    from dataclasses import replace

    from typehaus.takeoff.visit_state import VisitEntry
    from typehaus.takeoff.visit_toml import entry_rule_errors

    entry = opening.entries.get(slug)
    if entry is None:
        entry = VisitEntry()
    errors = entry_rule_errors(slug, replace(entry, status="verified"))
    if errors:
        raise SiteOpError(f"set_visit {slug!r}: {errors[0]} (before this request)")


def _with_visits(tasks: Any, visits: Any) -> Any:
    from dataclasses import replace

    return replace(tasks, visits=visits)
