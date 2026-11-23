"""A cast pier that is part of its FOOTING, not a column — decision 16 (2026-11-22).

A pinned, laterally propped pier standing on its own ``Pad`` and standing out of grade no more
than a pedestal (exposed height / diameter <= 3, ACI 318-19 §2.3 and §14.3.3.1) is the deck
footing of IRC R507.3 ("concrete footings ... as shown in Figure R507.3"), its depth set by
R403.1.4 and its pad by Table R507.3.1. Below grade it is a soil-embedded pier; above grade a
pedestal. It carries no base moment of its own (``_Pier.lateral_system`` is False: its deck is
tied or braced, or the post above it is pinned).

Such a pier leaves ``deck_post``'s register. What it still needs is graded prescriptively:
the pad by ``structural.deck_footing_size``; a pier under a PINNED roof post, which stands free
at its head, by IBC 1807.3.2.1 in ``structural.column_base`` (``checks/structural/deck_piers``).

Oracle: ``houses/catlin/notes/north_entry_piers.md`` §6c.
"""

from __future__ import annotations

from typing import Any

#: ACI 318-19 §2.3 / §14.3.3.1: a pedestal's height is at most 3x its least lateral dimension.
PEDESTAL_RATIO = 3.0


def grade_ft(ctx: Any) -> float | None:
    grade = getattr(getattr(ctx.plan.project, "site", None), "grade", None)
    return None if grade is None else float(grade.inches) / 12.0


def exposed_ft(ctx: Any, tag: str) -> float | None:
    """Pier top above ``Site.grade``, ft (0 if the top is buried); ``None`` if unresolved."""
    solid = ctx.model.by_tag(tag)
    grade = grade_ft(ctx)
    if solid is None or grade is None:
        return None
    return max(solid.z1_m / 0.3048 - grade, 0.0)


def is_footing_pier(ctx: Any, pier: Any) -> bool:
    """Pinned, on its own pad, and a pedestal above grade."""
    if pier.lateral_system or pier.base_kind != "pad" or pier.diameter_in <= 0.0:
        return False
    out = exposed_ft(ctx, pier.tag)
    return out is not None and out * 12.0 / pier.diameter_in <= PEDESTAL_RATIO + 1e-6


def footing_piers(ctx: Any) -> dict[str, float]:
    """``tag -> exposed height ft`` of every footing pier in the plan."""
    from typehaus.engineering.pier_basis import cast_piers

    return {p.tag: exposed_ft(ctx, p.tag) or 0.0 for p in cast_piers(ctx)
            if is_footing_pier(ctx, p)}
