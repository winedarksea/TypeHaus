"""``GET/PUT /tasks`` — work-package status beside the cost view.

Deliberately the same 50-line shape as :mod:`typehaus.server.costs_api`: the server owns
HTTP status codes and re-reading files per request, the state machine lives in
:mod:`typehaus.takeoff.task_state`, and the derivation lives in
:mod:`typehaus.takeoff.tasks`. Nothing here knows what a work package *is*.

Also outside the PatchOp/undo journal, for the same reason costs are: closing out a work
package is not a plan edit, and undo must never re-open one.

``tasks.toml`` is re-read per request rather than cached on ``ProjectState`` — a builder
edits it by hand in the same editor session, and a stale cache would show yesterday's
status beside today's plan.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from typehaus.takeoff.task_state import STATUSES, apply_task_op, load_tasks, write_tasks


class TasksRequestError(ValueError):
    """The tasks request was malformed (bad op, unknown status, malformed file)."""


def build_tasks_payload(model: Any, house_dir: Path) -> dict[str, Any]:
    """Work packages for the resolved ``model``, each carrying its persisted status."""
    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.takeoff.bom import bill_of_materials
    from typehaus.takeoff.costs import load_costs
    from typehaus.takeoff.product_labels import product_labels
    from typehaus.takeoff.tasks import build_work_items

    try:
        prices = load_prices(house_dir)
        costs = load_costs(house_dir)
        state = load_tasks(house_dir)
    except ValueError as exc:
        raise TasksRequestError(str(exc)) from exc
    bom = bill_of_materials(model)
    estimate = (estimate_costs(bom, prices, None, product_labels(model.plan))
                if prices is not None else None)
    items = [item.as_dict() | {"status": state.status_of(item.slug),
                               "entry": (state.entries[item.slug].as_dict()
                                         if item.slug in state.entries else None)}
             for item in build_work_items(model, bom, estimate, costs)]
    # Slugs in tasks.toml that no longer derive from the model: the plan dropped the last
    # element of a trade under a storey. Surfaced, never dropped — the same contract
    # ``costs_payload`` keeps for a stale check-off.
    derived = {item["slug"] for item in items}
    stale = sorted(slug for slug in state.entries if slug not in derived)
    return {"tasks": items, "statuses": list(STATUSES), "stale": stale,
            "priced": estimate is not None}


def apply_task_ops(house_dir: Path, ops: Any) -> None:
    """Validate and fold ``ops`` over the persisted state, then write it back.

    All-or-nothing: a bad op anywhere in the list persists nothing, so a client retry
    cannot half-apply a batch.
    """
    if not isinstance(ops, list) or not ops:
        raise TasksRequestError("body must be {\"ops\": [...]} with at least one op")
    try:
        state = load_tasks(house_dir)
        for op in ops:
            if not isinstance(op, dict):
                raise TasksRequestError(f"each op must be an object, got {op!r}")
            state = apply_task_op(state, op)
    except ValueError as exc:
        raise TasksRequestError(str(exc)) from exc
    write_tasks(house_dir, state)
