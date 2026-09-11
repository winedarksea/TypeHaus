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

from typehaus.schedule.inspection_state import load_inspections
from typehaus.schedule.site_ops import (
    SiteOpError,
    StaleRevision,
    apply_ops,
    site_revision,
)


class ScheduleRequestError(ValueError):
    """The request was malformed (bad op, unknown status, malformed file)."""


class ScheduleConflict(ValueError):
    """The client's ``if_revision`` is stale. The server 409s with the fresh payload."""


def _board(model: Any, house_dir: Path, findings: list[Any],
           tasks_state: Any = None, inspections_state: Any = None) -> Any:
    """The board, optionally against *candidate* site state rather than what is on disk.

    The two states are parameters so ``_validator`` can ask "what would this op batch make
    the board look like" without writing anything first — and so it asks with the same
    prices and costs the real payload uses, since a package with no priced rows is a package
    the dependency rules would then call dangling.
    """

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
        tasks = load_tasks(house_dir) if tasks_state is None else tasks_state
        inspections = (load_inspections(house_dir) if inspections_state is None
                       else inspections_state)
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
    from typehaus.schedule.timing import visit_dates
    from typehaus.takeoff.task_state import load_tasks

    board, items, _state = _board(model, house_dir, findings)
    dates = visit_dates(board, load_tasks(house_dir))
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
                        for item in handoff_items(model, visit)],
            "dates": dates[visit.slug].as_dict()})
    # Only for packages nobody has split yet: a proposal beside an accepted split is noise,
    # and re-proposing over authored work is how a tool starts arguing with its user.
    proposals = {slug: found
                 for slug, found in propose_all(items, specs).items()
                 if slug not in authored}
    return {"profile": board.profile_name, "checks_pending": bool(checks_pending),
            "revision": site_revision(house_dir),
            "milestones": [m.as_dict() for m in board.milestones],
            "visits": visits, "proposals": proposals, "stale": list(board.stale),
            "contractors": {key: value.as_dict() for key, value
                            in load_tasks(house_dir).contractors.items()},
            "errors": list(board.errors),
            "dropped_gates": [{"trade": trade, "inspection": ref}
                              for trade, ref in board.dropped_gates]}


def build_inspections_payload(model: Any, house_dir: Path, findings: list[Any],
                              checks_pending: bool = False) -> dict[str, Any]:
    """Every inspection, its state, and everything between it and a phone call."""
    from typehaus.schedule.timing import inspection_dates
    from typehaus.takeoff.task_state import load_tasks

    board, _items, state = _board(model, house_dir, findings)
    dates = inspection_dates(board.inspections, state.authorities, load_tasks(house_dir))
    return {"profile": board.profile_name, "checks_pending": bool(checks_pending),
            "revision": site_revision(house_dir),
            "authorities": {key: value.as_dict()
                            for key, value in state.authorities.items()},
            "permit": state.permit.as_dict(),
            "errors": list(board.errors),
            "inspections": [record.as_dict() | {"dates": dates.get(record.id, {})}
                            for record in board.inspections]}


def apply_site_ops(house_dir: Path, body: Any, model: Any = None) -> str:
    """Validate and fold a request's ops through the one write path. Returns the revision.

    The endpoint that calls this does not care which file each op lands in — that is
    ``schedule/site_ops.py``'s job, and it is also the module an in-UI agent will call.
    """
    if not isinstance(body, dict):
        raise ScheduleRequestError('body must be {"ops": [...]}')
    try:
        return apply_ops(house_dir, body.get("ops"),
                         if_revision=body.get("if_revision"),
                         validate_with=_validator(house_dir, model))
    except StaleRevision as exc:
        raise ScheduleConflict(str(exc)) from exc
    except SiteOpError as exc:
        raise ScheduleRequestError(str(exc)) from exc


def apply_inspection_ops(house_dir: Path, ops: Any) -> None:
    """Back-compatible shim: the old ``{"ops": [...]}`` body for ``PUT /inspections``."""
    apply_site_ops(house_dir, {"ops": ops})


def _validator(house_dir: Path, model: Any) -> Any:
    """The board-level rules, run against the state an op batch would write.

    ``None`` where there is no resolved model: the entry-local rules still ran, and
    refusing every write because the plan does not resolve would lock the owner out of the
    board exactly when they most need to record what happened on site.
    """
    if model is None:
        return None

    def validate(tasks: Any, inspections: Any) -> list[str]:
        from typehaus.schedule.rules import validate as rules_validate

        board, _items, _state = _board(model, house_dir, [], tasks, inspections)
        errors, _warnings = rules_validate(board, model)
        return errors

    return validate
