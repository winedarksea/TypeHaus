"""R311.6 hallway width.

This rule is why the coverage test exists in the direction it does. The profile's
``coverage_statement`` has claimed "R311.6 hallway width" since it was written, and nothing
implemented it: the meta-test catches a *checklist item* naming a check that does not exist,
and a *registered check* on no checklist item, but not a prose claim with neither. The claim
was true of the sentence and false of the engine for as long as both existed.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import _fail, _min_clear_width, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import Occupancy
from typehaus.quantities import ft

_MIN_HALLWAY_WIDTH = ft(3)  # R311.6: 36" clear


@check(Tier.CODE, "code.R311_6_hallway_width")
def hallway_width(ctx: CheckContext) -> list[Finding]:
    """R311.6 — hallways serving as an exit route are at least 36" wide.

    Measured as the narrowest clear width the room polygon admits (the largest disc that
    still fits everywhere along it), not the authored dimension: a hallway that pinches at
    one chase or one out-of-plane closet return is exactly the case a nominal width hides,
    and ``clear_face`` is already the *interior finish face*, so the number this reads is the
    one an inspector's tape measures.
    """
    cid, code = "code.R311_6_hallway_width", "R311.6"
    halls = [room for room in ctx.model.rooms
             if room.occupancy == Occupancy.HALLWAY.value]
    if not halls:
        return [_unknown(cid, "no hallway-occupancy rooms resolved, so the 36\" corridor "
                         "requirement has nothing to measure", (), code)]
    out: list[Finding] = []
    for hall in halls:
        width = _min_clear_width(hall.clear_face)
        if width is None:
            out.append(_unknown(cid, f"{hall.tag} resolved no usable clear-face polygon",
                                (hall.tag,), code))
        elif width + 1e-9 < _MIN_HALLWAY_WIDTH.meters:
            out.append(_fail(cid, f"{hall.tag} pinches to {width / .0254:.1f}\" clear; "
                             "R311.6 requires 36\"", (hall.tag,), code))
        else:
            out.append(_pass(cid, f"{hall.tag} is {width / .0254:.1f}\" clear at its "
                             "narrowest (>= 36\")", code))
    return out
