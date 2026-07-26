"""Stair finish: treads, risers and landing decking as a millwork order.

The stringers, joists and rims already bill as lumber through ``framing_takeoff`` — they are
``FramedMember``s with a profile like every other stick. The *finish* does not, and it is a
different order from a different supplier: a tread is a milled hardwood board with a bullnose
and a riser is a finished board, both counted by the piece and priced by the run, not bought
as 2x stock by the lineal foot.

Counting is off the resolved members rather than off ``riser_count``, so a stair with winders
bills the winders it actually generated. A riser is billed per tread — the vertical face
below it — because the model has no riser member: it is the gap between two treads, and a
closed-riser stair still buys a board for every one of them.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895
_M2_TO_FT2 = 10.7639104

# The walking surfaces a stair buys as finish goods, and what each is ordered as.
_TREAD_CATEGORIES = ("tread", "winder")
_LANDING_CATEGORY = "landing"


def stair_finish_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per stair: treads and risers by the piece, landing decking by the square foot.

    Tread width is the member's own run length, so a winder's tapered board bills at its wide
    end — which is the blank a millwork shop cuts it from, not the average of its two ends.
    """
    rows: list[dict[str, object]] = []
    for stair in sorted(model.stairs, key=lambda item: item.tag):
        treads = [m for m in stair.members if m.category in _TREAD_CATEGORIES]
        landings = [m for m in stair.members if m.category == _LANDING_CATEGORY]
        if not treads and not landings:
            continue
        tread_lf = sum(m.length_m for m in treads)
        widest = max((m.length_m for m in treads), default=0.0)
        landing_area = sum(
            m.length_m * cross_section(m.profile).width_m for m in landings)
        rows.append({
            "stair": stair.tag,
            "treads": len(treads),
            "tread_run_in": round(stair.tread_depth_m / 0.0254, 2),
            "tread_lf": round(tread_lf * _M_TO_FT, 1),
            "widest_tread_ft": round(widest * _M_TO_FT, 2),
            # One riser board per tread: the face below it. The model has no riser member —
            # a riser is the gap between two treads — but a closed-riser stair buys one.
            "risers": len(treads),
            "riser_height_in": round(stair.riser_height_m / 0.0254, 2),
            "riser_lf": round(tread_lf * _M_TO_FT, 1),
            "landing_decks": len(landings),
            "landing_area_sqft": round(landing_area * _M2_TO_FT2, 1),
        })
    return rows
