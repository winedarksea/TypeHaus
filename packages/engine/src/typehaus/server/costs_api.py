"""``GET/PUT /costs`` — the cost-tracking state behind the BOM view.

Thin, like :mod:`typehaus.server.macros_api`: the server owns HTTP status codes and
re-reading files per request; the state machine itself lives in
:mod:`typehaus.takeoff.costs`. Deliberately OUTSIDE the PatchOp/undo journal — paying a
bill is not a plan edit, and undo must never un-pay one.

Both files are re-read on every request rather than cached on ``ProjectState``: the owner
edits ``prices.toml``/``costs.toml`` by hand in the same editor session, and a stale cache
here would show yesterday's check-offs beside today's plan.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from typehaus.takeoff.costs import apply_costs_op, costs_payload, load_costs, write_costs


class CostsRequestError(ValueError):
    """The costs request was malformed (bad op, unknown section, malformed file)."""


def build_costs_payload(model: Any, house_dir: Path) -> dict:
    """The full costs payload for the resolved ``model``: BOM join, estimate, state."""
    from typehaus.cli.prices import load_prices
    from typehaus.takeoff.bom import bill_of_materials

    try:
        prices = load_prices(house_dir)
        state = load_costs(house_dir)
    except ValueError as exc:
        raise CostsRequestError(str(exc)) from exc
    return costs_payload(bill_of_materials(model), prices, state)


def apply_costs_ops(house_dir: Path, ops: Any) -> None:
    """Validate and fold ``ops`` over the persisted state, then write it back.

    All-or-nothing: a bad op anywhere in the list persists nothing, so a client retry
    cannot half-apply a batch.
    """
    if not isinstance(ops, list) or not ops:
        raise CostsRequestError("body must be {\"ops\": [...]} with at least one op")
    try:
        state = load_costs(house_dir)
        for op in ops:
            if not isinstance(op, dict):
                raise CostsRequestError(f"each op must be an object, got {op!r}")
            state = apply_costs_op(state, op)
    except ValueError as exc:
        raise CostsRequestError(str(exc)) from exc
    write_costs(house_dir, state)
