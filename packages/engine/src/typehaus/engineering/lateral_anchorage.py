"""The cast-in anchor under a shear panel's hold-down, graded in the pier it stands in.

Split from ``lateral_system`` to keep that module under 500 lines.
"""

from __future__ import annotations

from typehaus.engineering.item import LimitState, Quantity
from typehaus.engineering.registry import EngineeringContext
from typehaus.engineering.retaining_basis import PRESUMPTIVE_FC_PSI


def anchorage(ctx: EngineeringContext, wall: object, tension_lb: float, shear_lb: float,
               states: list[LimitState], notes: list[str], inputs: list[Quantity]) -> None:
    """The cast-in anchor under each end of a panel, graded in the pier it stands in.

    ** THE PANEL'S END POST NAMES ITS OWN PIER BY STANDING ON IT. ** A post framed into the
    panel (``Post.within_wall``) bears on the cast pier at its own plan position, and that
    pier's diameter and f'c are what the anchor lives in. Nothing is assumed: a post with no
    pier under it raises no row, because there is then no concrete to design.
    """
    from typehaus.engineering.column_head_joint import _net_uplift
    from typehaus.engineering.holdown_anchor import round_pier_anchor
    from typehaus.engineering.holdown_anchor import states as anchor_states
    from typehaus.engineering.pier_basis import _round_size, cast_piers

    posts = [e for e in ctx.plan.all_elements()
             if getattr(e, "within_wall", None) == getattr(wall, "tag", None)]
    if not posts:
        return
    piers = [p for p in cast_piers(ctx)
             for post in posts
             if _same_station(ctx.plan.by_tag(p.tag), post)]
    # ** THE WORST PIER IS GRADED, ONCE. ** The bases are identical parts carrying the two
    # ends of one couple, so a row per base would be the same row twice; the smallest pier
    # at the lowest f'c is the one that answers for the pair.
    candidates = [(pier, _round_size(getattr(ctx.plan.by_tag(pier.tag), "size", "") or ""))
                  for pier in piers]
    ranked = sorted(((pier, size) for pier, size in candidates if size is not None),
                    key=lambda row: (row[1][0], row[0].specified_fc_psi or 0.0))
    if ranked:
        pier, size = ranked[0]
        inputs.append(Quantity(f"panel_anchor_fc_{wall.tag}",
                               pier.specified_fc_psi or PRESUMPTIVE_FC_PSI, "psi", 1.0))
        uplift = _net_uplift(ctx, pier, notes=[]) or 0.0
        anchor = round_pier_anchor(pier.tag, size[0], pier.specified_fc_psi or PRESUMPTIVE_FC_PSI)
        states.extend(anchor_states(
            anchor, tension_lb + uplift, shear_lb / max(len(piers), 1),
            f"the panel's overturning couple {tension_lb:,.0f} lb plus the column's net "
            f"roof uplift {uplift:,.0f} lb (0.6D + 0.6W), no dead load credited against "
            f"either",
            f"the panel's base shear {shear_lb:,.0f} lb shared by its {len(piers)} bases — "
            f"put ALL of it on one and the shear row doubles and the interaction still "
            f"clears"))
        notes.append(
            f"THE HOLD-DOWN'S ANCHOR IS GRADED IN ITS PIER, NOT AS A PART: one cast-in "
            f"5/8in x 10in bolt per base in a round pier, ACI 318-19 Ch. 17, cracked, "
            f"condition B, with h_ef derived from the bolt's own length and the edge distance "
            f"the pier's radius gives it on every side. The two bases are identical, so one "
            f"is graded ({pier.tag}). What is NOT credited: supplementary reinforcement "
            f"(the cage is not developed as anchor reinforcement), uncracked concrete, and "
            f"any bearing or friction under the base plate.")


def _same_station(pier_element: object, post: object) -> bool:
    """Same plan position to a tenth of an inch — a post standing on a pier, not near one."""
    a = getattr(pier_element, "position", None)
    b = getattr(post, "position", None)
    if a is None or b is None:
        return False
    return all(abs(x - y) < 0.0025 for x, y in zip(a.xy_m, b.xy_m, strict=False))
