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
from typing import Any, cast

from typehaus.takeoff.costs import apply_costs_op, costs_payload, load_costs, write_costs


class CostsRequestError(ValueError):
    """The costs request was malformed (bad op, unknown section, malformed file)."""


def build_costs_payload(model: Any, house_dir: Path) -> dict:
    """The full costs payload for the resolved ``model``: BOM join, estimate, state.

    The $/sf denominators are computed here exactly as ``cli/cmd_takeoff`` computes them —
    conditioned area is what the energy code grades, gross is what a builder means by
    "$/sf", and both come from the model rather than from a constant. Without them the
    browser had no $/sf at all while the terminal printed it.
    """
    from typehaus.cli.prices import load_prices
    from typehaus.server.space_summary import build_space_summary
    from typehaus.takeoff.bom import bill_of_materials
    from typehaus.takeoff.product_labels import product_labels

    try:
        prices = load_prices(house_dir)
        state = load_costs(house_dir)
    except ValueError as exc:
        raise CostsRequestError(str(exc)) from exc
    # Cast rather than index straight into the payload: `build_space_summary` is typed as a
    # plain JSON dict, so its "overall" block reads as `object` under mypy --strict.
    summary = cast("dict[str, float]", build_space_summary(model)["overall"])
    areas = {"conditioned": summary["conditioned_sf"], "gross": summary["gross_sf"]}
    return costs_payload(bill_of_materials(model), prices, state, areas,
                         product_labels(model.plan))


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
