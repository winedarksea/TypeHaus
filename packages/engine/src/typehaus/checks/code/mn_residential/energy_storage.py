"""IRC R327 — stationary storage battery systems, as the adopted 2018 book has it.

The profile's base is the 2018 IRC (MN Rules ch. 1309, no R327 amendment found), and its
R327 (code change RB171-16 as modified) is six short sub-sections: R327.1 scope, **R327.2
listing** (UL 9540; under 1 kWh exempt), **R327.3 installation** (manufacturer's
instructions, and *not within the habitable space of a dwelling unit*), R327.4 electrical
(NFPA 70; inverter UL 1741 or part of the UL 9540 listing), R327.5 ventilation (only for
batteries that gas off hydrogen — not LFP), R327.6 vehicle impact.

The 20/40 kWh caps and the smoke-alarm rule are the 2021 IRC's R328.5 and R328.7 (from NFPA
855). They are not in the adopted book, so they live in
``checks/advisory/energy_storage_anticipated.py`` as the code the next adoption brings. The
2021 R328.4 location list is graded nowhere.

Every check reports NOT_APPLICABLE when no ESS is placed: a permit item with no matched
findings resolves to UNKNOWN, so returning nothing would make "there is no battery here" and
"nobody looked" the same answer.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import (
    HABITABLE_OCCUPANCIES,
    _fail,
    _na,
    _pass,
    _unknown,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import EquipmentKind

#: What every R327 check says when the house places no storage unit. One string so the
#: lines cannot drift into different accounts of the same fact.
_NO_ESS = ("no energy storage system is placed in this house, so R327 has no stationary "
           "storage battery to govern")


def _batteries(ctx: CheckContext) -> list:
    return [element for element in ctx.plan.all_elements()
            if element.element_kind == "Equipment"
            and getattr(element, "kind", None) is EquipmentKind.BATTERY]


def _type_of(ctx: CheckContext, element):
    return next((t for t in ctx.plan.library.equipment_types
                 if t.tag == element.type_ref), None)


@check(Tier.CODE, "code.R327_ess_listing")
def ess_listing(ctx: CheckContext) -> list[Finding]:
    """R327.2 — every storage unit is listed and labeled to UL 9540.

    ``ul_9540_listed`` is declared on the equipment type and never inferred. False therefore
    means "this model does not state that the unit is listed", which is exactly what a plan
    reviewer needs to see — a listing you cannot point at is not a listing.
    """
    cid, code = "code.R327_ess_listing", "R327.2"
    batteries = _batteries(ctx)
    if not batteries:
        return [_na(cid, _NO_ESS, (), code)]
    out: list[Finding] = []
    for battery in batteries:
        product = _type_of(ctx, battery)
        if product is None:
            out.append(_unknown(cid, f"{battery.tag} names no equipment type, so its "
                                     "listing cannot be read", (battery.tag,), code))
        elif getattr(product, "ul_9540_listed", False):
            out.append(_pass(cid, f"{battery.tag} ({product.tag}) is declared listed and "
                                  "labeled to UL 9540", code))
        else:
            out.append(_fail(cid, f"{battery.tag} ({product.tag}) does not declare "
                                  "`ul_9540_listed=True`; R327.2 requires the unit be "
                                  "listed and labeled to UL 9540",
                             (battery.tag,), code))
    return out


@check(Tier.CODE, "code.R327_ess_location")
def ess_location(ctx: CheckContext) -> list[Finding]:
    """R327.3 — not within the habitable space of a dwelling unit.

    Read off the room's occupancy against R202's habitable set. A battery that names no
    room, or a room the model did not resolve, is UNKNOWN, never a pass.
    """
    cid, code = "code.R327_ess_location", "R327.3"
    batteries = _batteries(ctx)
    if not batteries:
        return [_na(cid, _NO_ESS, (), code)]
    habitable = {item.value for item in HABITABLE_OCCUPANCIES}
    occupancy = {room.tag: room.occupancy for room in ctx.model.rooms}
    out: list[Finding] = []
    for battery in sorted(batteries, key=lambda e: e.tag):
        room = getattr(battery, "room", None)
        if room not in occupancy:
            out.append(_unknown(cid, f"{battery.tag} names no resolved room, so R327.3's "
                                     "habitable-space exclusion cannot be read",
                                (battery.tag,), code))
        elif occupancy[room] in habitable:
            out.append(_fail(cid, f"{battery.tag} is in {room} ({occupancy[room]}); R327.3 "
                                  "keeps an ESS out of the habitable space of a dwelling",
                             (battery.tag, room), code))
        else:
            out.append(_pass(cid, f"{battery.tag} is in {room} ({occupancy[room]}), not "
                                  "habitable space", code))
    return out
