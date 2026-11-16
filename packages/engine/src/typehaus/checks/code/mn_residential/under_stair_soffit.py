"""R302.7's underside half: how much of a space under a stair its gypsum underside covers.

The evidence is the stair's own ``undersides`` (``resolve/stair_undersides.py``): a flight
or landing board of gypsum at least 1/2" thick, read in plan against the room's face.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.findings import Finding
from typehaus.quantities import inch
from typehaus.resolve.overlay import intersection, union_all

R302_7_MIN_GYPSUM_M = inch(0.5).meters
# The share of the space's plan its stair's gypsum underside must cover.
UNDERSIDE_COVER = 0.9


def grade_enclosed(ctx, cid: str, code: str, stair, room, finishes: set[str],
                   outline: Polygon) -> Finding:
    """One enclosed space under a stair: its walls' gypsum, then the underside's."""
    tags = (room.tag, stair.tag)
    if not finishes:
        return _fail(cid, f"{room.tag} is enclosed usable space under {stair.tag}, reached by "
                          "a door, and its bounding walls carry no gypsum finish; R302.7 "
                          "requires 1/2\" gypsum board on the enclosed side", tags, code)
    walls = ", ".join(sorted(finishes))
    cover = gypsum_underside_cover(ctx, stair, room, outline)
    if cover >= UNDERSIDE_COVER - 1e-9:
        return _pass(cid, f"{room.tag} under {stair.tag} is lined with {walls} and {cover:.0%} "
                          "of the stair's underside is 1/2\" gypsum", code)
    return _unknown(cid, f"{room.tag} under {stair.tag}: walls lined with {walls}, but only "
                         f"{cover:.0%} of the stair's underside is modelled as 1/2\" gypsum "
                         "(Stair.underside_material)", tags, code)


def gypsum_underside_cover(ctx, stair, room, outline: Polygon) -> float:
    """Fraction of (stair outline ∩ room face) under a qualifying gypsum underside board."""
    target = intersection(outline, Polygon(room.clear_face))
    if target.is_empty or target.area <= 1e-9:
        return 0.0
    boards = [Polygon(board.outline) for board in stair.undersides
              if board.role in ("flight", "landing")
              and board.thickness_m >= R302_7_MIN_GYPSUM_M - 1e-9
              and getattr(ctx.plan.library.material(board.material_ref), "gypsum_type", None)]
    if not boards:
        return 0.0
    return intersection(target, union_all(boards)).area / target.area
