"""ADVISORY — the owner's garage heat alarm, a house standard rather than a code line.

Minnesota's residential code (Minn. R. 1309, the 2018 IRC as amended, read on UpCodes
2026-11-14) asks for no heat alarm anywhere: R314 is smoke alarms, R315 carbon monoxide, and
neither names a garage heat detector. Washington's amendment to R314 adds one in a new
attached garage; this house keeps one in its detached garage by choice (owner, 2026-11-14),
so it is graded here without a code citation, like the ESS closet's heat alarm.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory_fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import AlarmKind, Occupancy

_CID = "advisory.garage_heat_alarm"


@check(Tier.ADVISORY, _CID)
def garage_heat_alarm(ctx: CheckContext) -> list[Finding]:
    """Each garage carries a heat alarm (owner standard)."""
    garages = [room for room in ctx.model.rooms if room.occupancy == Occupancy.GARAGE.value]
    if not garages:
        return [_na(_CID, "no room is a garage")]
    heat = {element.room: element.tag for element in ctx.plan.all_elements()
            if element.element_kind == "Alarm" and element.kind is AlarmKind.HEAT}
    out: list[Finding] = []
    for garage in garages:
        if garage.tag in heat:
            out.append(_pass(_CID, f"{garage.tag} has heat detector {heat[garage.tag]} (owner "
                                   "standard; no MN code line asks for one)", (garage.tag,)))
        else:
            out.append(advisory_fail(_CID, f"garage {garage.tag} has no heat detector; the "
                                           "owner's standard keeps one (beyond Minn. R. 1309 "
                                           "R314/R315)", (garage.tag,)))
    return out
