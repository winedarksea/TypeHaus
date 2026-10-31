"""ADVISORY — the ESS rules the next code adoption brings, graded ahead of it.

The adopted 2018 IRC R327 has no capacity caps and no detection rule
(``checks/code/mn_residential/energy_storage.py``). The 2021 IRC moved the article to R328
and added both, from NFPA 855: R328.5's 20 kWh per unit and 40 kWh aggregate in a utility
closet, basement or storage space (80 kWh in a garage), and R328.7's smoke alarm plus a
listed heat detector where the ESS is. Minnesota's next residential code is built on a
later IRC, so the house is held to them now — as advice, citing the book they come from,
never under a 2018 section number they do not have.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory_fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.advisory.energy_storage import _NO_ESS, _batteries
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import AlarmKind, Occupancy

_MAX_KWH_PER_UNIT = 20.0
#: 2021 R328.5 aggregate ceilings by location. A garage is its own location with its own
#: ceiling, so the documented garage move is a re-room, not a redesign.
_MAX_KWH_INDOOR = 40.0
_MAX_KWH_GARAGE = 80.0
_GARAGE_OCCUPANCIES = frozenset({Occupancy.GARAGE.value})


def _type_of(ctx: CheckContext, element):
    return next((t for t in ctx.plan.library.equipment_types
                 if t.tag == element.type_ref), None)


@check(Tier.ADVISORY, "advisory.ess_capacity")
def ess_capacity(ctx: CheckContext) -> list[Finding]:
    """2021 IRC R328.5 — 20 kWh per unit; 40 kWh aggregate indoors, 80 kWh in a garage."""
    cid, code = "advisory.ess_capacity", "2021 IRC R328.5"
    batteries = _batteries(ctx)
    if not batteries:
        return [_na(cid, _NO_ESS)]
    occupancy = {room.tag: room.occupancy for room in ctx.model.rooms}
    out: list[Finding] = []
    totals = {"indoor": [0.0, []], "garage": [0.0, []]}
    for battery in batteries:
        product = _type_of(ctx, battery)
        kwh = getattr(product, "storage_kwh", None) if product is not None else None
        if kwh is None:
            out.append(_unknown(cid, f"{battery.tag} declares no `storage_kwh`, so neither "
                                     "the per-unit nor the aggregate limit can be graded",
                                (battery.tag,), code=code))
            continue
        if kwh > _MAX_KWH_PER_UNIT + 1e-9:
            out.append(advisory_fail(cid, f"{battery.tag} is rated {kwh:g} kWh; 2021 R328.5 "
                                          f"limits one unit to {_MAX_KWH_PER_UNIT:g} kWh",
                                     (battery.tag,), code=code))
        else:
            out.append(_pass(cid, f"{battery.tag} is {kwh:g} kWh, within the "
                                  f"{_MAX_KWH_PER_UNIT:g} kWh per-unit limit", code=code))
        where = ("garage" if occupancy.get(getattr(battery, "room", None))
                 in _GARAGE_OCCUPANCIES else "indoor")
        totals[where][0] += float(kwh)
        totals[where][1].append(battery.tag)

    for where, limit in (("indoor", _MAX_KWH_INDOOR), ("garage", _MAX_KWH_GARAGE)):
        kwh, tags = totals[where]
        if not tags:
            continue
        tags = tuple(sorted(tags))
        if kwh > limit + 1e-9:
            out.append(advisory_fail(cid, f"{len(tags)} {where} units total {kwh:g} kWh; "
                                          f"2021 R328.5 limits that aggregate to {limit:g} kWh",
                                     tags, code=code))
        else:
            out.append(_pass(cid, f"{kwh:g} kWh {where} aggregate ({', '.join(tags)}), "
                                  f"within the {limit:g} kWh limit", tags, code=code))
    return out


@check(Tier.ADVISORY, "advisory.ess_detection")
def ess_detection(ctx: CheckContext) -> list[Finding]:
    """2021 IRC R328.7 — smoke *and* heat detection in the room the ESS is in.

    In the room, with no proximity allowance: the point is sensing the cabinet, and a head
    on the far side of the enclosure senses the room the enclosure protects instead.
    """
    cid, code = "advisory.ess_detection", "2021 IRC R328.7"
    batteries = _batteries(ctx)
    if not batteries:
        return [_na(cid, _NO_ESS)]
    alarms = [element for element in ctx.plan.all_elements()
              if element.element_kind == "Alarm"]
    out: list[Finding] = []
    for room_tag in sorted({getattr(b, "room", None) for b in batteries} - {None}):
        covering = [a for a in alarms if a.room == room_tag]
        for kind, label in ((AlarmKind.SMOKE, "smoke"), (AlarmKind.HEAT, "heat")):
            found = next((a for a in covering
                          if a.kind is kind
                          or (kind is AlarmKind.SMOKE and a.kind is AlarmKind.COMBO)), None)
            if found is None:
                out.append(advisory_fail(cid, f"ESS room {room_tag} has no {label} alarm in "
                                              "it; 2021 R328.7 wants both smoke and heat "
                                              "detection at the storage system",
                                         (str(room_tag),), code=code))
            else:
                out.append(_pass(cid, f"ESS room {room_tag} is covered by {label} alarm "
                                      f"{found.tag}", (str(room_tag),), code=code))
    return out
