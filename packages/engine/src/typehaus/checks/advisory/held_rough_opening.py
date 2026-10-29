"""``advisory.held_rough_opening`` — a door still framed to its pre-sizing RO.

Decision 6 of plans/door-sizing.md: where the derived RO would cause a conflict, that one
opening keeps its current framing (``Door.held_rough_opening``) until the change is
confirmed. ADVISORY, so it is listed and never blocks the permit gate (decision 12).
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, advisory, not_applicable

_CID = "advisory.held_rough_opening"
_IN = 0.0254


def _size(width_m: float, height_m: float) -> str:
    return f'{width_m / _IN:.2f}" x {height_m / _IN:.2f}"'


@check(Tier.ADVISORY, _CID)
def held_rough_opening(ctx: CheckContext) -> list[Finding]:
    """Every held opening, and the RO its nominal leaf needs."""
    doors = [o for o in ctx.model.openings if o.sizing is not None]
    held = sorted((o for o in doors if o.sizing.held), key=lambda o: o.tag)
    if not doors:
        return [not_applicable(_CID, "this plan types no door")]
    if not held:
        return [not_applicable(_CID, "no door holds its framing; every RO is published "
                                     "or derived")]
    out = []
    for opening in held:
        s = opening.sizing
        pocket = s.pocket_run_m > 1e-9
        # A pocket holds its passage; the cassette width follows the leaf.
        held_w = s.passage_w_m if pocket else s.rough_w_m
        need_w = s.nominal_w_m if pocket else s.required_w_m
        out.append(advisory(
            _CID,
            f"ADVISORY — {opening.tag} holds a {_size(held_w, s.rough_h_m)} RO; its "
            f"{_size(s.nominal_w_m, s.nominal_h_m)} nominal leaf needs "
            f"{_size(need_w, s.required_h_m)} ({s.required_basis})",
            (opening.tag,), Result.ADVISORY,
            fix="drop held_rough_opening once the derived RO is confirmed"))
    return out
