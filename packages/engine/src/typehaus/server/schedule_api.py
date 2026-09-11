"""``GET/PUT /schedule`` and ``GET/PUT /inspections`` — the site surface's data.

Same 60-line shape as :mod:`typehaus.server.tasks_api`: the server owns HTTP status codes
and re-reads the two TOML files per request, the state machines live in
``takeoff/visit_state.py`` and ``schedule/inspection_state.py``, and the derivation lives in
``schedule/readiness.py``. Nothing here knows what a visit is.

Both payloads echo ``checks_pending``. A board built during the brief window after a
rebuild and before the check job lands would show every finding-derived blocker as absent,
which is the one wrong answer this surface must not give quietly — so the flag rides along
and the UI says so.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from typehaus.schedule.inspection_state import (
    apply_inspection_op,
    load_inspections,
    write_inspections,
)


class ScheduleRequestError(ValueError):
    """The request was malformed (bad op, unknown status, malformed file)."""


def _board(model: Any, house_dir: Path, findings: list[Any]) -> Any:
    from typehaus.checks.run import load_preferences, resolve_profile
    from typehaus.cli.prices import estimate_costs, load_prices
    from typehaus.schedule.readiness import make_ready
    from typehaus.server.space_summary import estimate_areas
    from typehaus.takeoff.bom import bill_of_materials
    from typehaus.takeoff.costs import load_costs
    from typehaus.takeoff.product_labels import product_labels
    from typehaus.takeoff.task_state import load_tasks
    from typehaus.takeoff.tasks import build_work_items

    try:
        preferences = load_preferences(house_dir)
        prices = load_prices(house_dir)
        costs = load_costs(house_dir)
        tasks = load_tasks(house_dir)
        inspections = load_inspections(house_dir)
    except ValueError as exc:
        raise ScheduleRequestError(str(exc)) from exc
    profile = resolve_profile(preferences)
    bom = bill_of_materials(model)
    estimate = (estimate_costs(bom, prices, estimate_areas(model),
                               product_labels(model.plan))
                if prices is not None else None)
    items = build_work_items(model, bom, estimate, costs)
    board = make_ready(model, items, tasks, inspections, profile, list(findings), costs)
    return board, items, inspections


def build_schedule_payload(model: Any, house_dir: Path, findings: list[Any],
                           checks_pending: bool = False) -> dict[str, Any]:
    """The build board: milestones, visits, readiness, handoff lists and proposals."""
    from typehaus.schedule.handoff import handoff_items
    from typehaus.schedule.propose import propose_all

    board, items, _state = _board(model, house_dir, findings)
    specs = tuple(type("_Spec", (), {"id": record.id, "gates": record.gates})()
                  for record in board.inspections)
    authored = {visit.package for visit in board.visits if not visit.implicit}
    visits = []
    for visit in board.visits:
        readiness = board.readiness[visit.slug]
        visits.append(visit.as_dict() | {
            "readiness": readiness.state,
            "constraints": [c.as_dict() for c in readiness.constraints],
            "handoff": [item.as_dict() | {"checked": item.id in visit.checked}
                        for item in handoff_items(model, visit)]})
    # Only for packages nobody has split yet: a proposal beside an accepted split is noise,
    # and re-proposing over authored work is how a tool starts arguing with its user.
    proposals = {slug: found
                 for slug, found in propose_all(items, specs).items()
                 if slug not in authored}
    return {"profile": board.profile_name, "checks_pending": bool(checks_pending),
            "milestones": [m.as_dict() for m in board.milestones],
            "visits": visits, "proposals": proposals, "stale": list(board.stale)}


def build_inspections_payload(model: Any, house_dir: Path, findings: list[Any],
                              checks_pending: bool = False) -> dict[str, Any]:
    """Every inspection, its state, and everything between it and a phone call."""
    board, _items, state = _board(model, house_dir, findings)
    return {"profile": board.profile_name, "checks_pending": bool(checks_pending),
            "authorities": {key: value.as_dict()
                            for key, value in state.authorities.items()},
            "inspections": [record.as_dict() for record in board.inspections]}


def apply_inspection_ops(house_dir: Path, ops: Any) -> None:
    """Validate and fold ``ops`` over ``inspections.toml``, then write it back.

    All-or-nothing: a bad op anywhere in the list persists nothing, so a client retry
    cannot half-apply a batch.
    """
    if not isinstance(ops, list) or not ops:
        raise ScheduleRequestError('body must be {"ops": [...]} with at least one op')
    try:
        state = load_inspections(house_dir)
        for op in ops:
            if not isinstance(op, dict):
                raise ScheduleRequestError(f"each op must be an object, got {op!r}")
            state = apply_inspection_op(state, op)
    except ValueError as exc:
        raise ScheduleRequestError(str(exc)) from exc
    write_inspections(house_dir, state)
