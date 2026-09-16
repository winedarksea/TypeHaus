"""Does a run crossing a blocked bearing line fit the 2x6 box framed around it.

``resolve/floor_blocking.py`` blocks every bay where a wall above stands on a floor's
bearing line, and frames a 2x6 box instead where a pipe, duct or raceway crosses. A run
whose crown is above the box's top rail, or that runs into the face closing the bay, cannot
pass without cutting the load path the blocking exists for.

``Tier.STRUCTURAL``, no ``PermitItemSpec`` — the footing ``mep.run_member_crossing`` has.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding

_CID = "mep.run_through_blocking"


@check(Tier.STRUCTURAL, _CID)
def run_through_blocking(ctx: CheckContext) -> list[Finding]:
    """One FAIL per run that cannot clear its box; one PASS per floor whose boxes all fit."""
    out: list[Finding] = []
    blocked = 0
    for floor in ctx.model.floors:
        boxes = sorted({m.child_key.removesuffix("-rail-top") for m in floor.members
                        if m.category == "blocking" and m.child_key.endswith("-rail-top")})
        if not boxes and not any(m.child_key.startswith("bearing-block")
                                 for m in floor.members):
            continue
        blocked += 1
        for conflict in floor.blocking_conflicts:
            out.append(_fail(
                _CID,
                f"{conflict.run_tag} crosses {floor.tag}'s bearing-line blocking at "
                f"{conflict.member_key}: {conflict.reason}",
                (conflict.run_tag, floor.tag),
                fix=("move the run to a bay where it clears a 2x6 box, lower or raise it "
                     "within the joist depth, or cross the line where no wall stands above")))
        if not floor.blocking_conflicts:
            out.append(_pass(
                _CID,
                f"{floor.tag}: {len(boxes)} run pass-through(s) in its bearing-line blocking, "
                "each framed as a 2x6 box the runs clear", (floor.tag,)))
    if blocked == 0:
        return [_na(_CID, "no floor carries bearing-line blocking: no wall above stands on "
                          "an interior or shared bearing line")]
    return out
