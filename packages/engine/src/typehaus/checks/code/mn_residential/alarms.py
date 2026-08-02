"""R314 smoke alarms and R315 carbon monoxide alarms.

Split out of ``rules.py``. Between them the two rules here covered sleeping storeys and the
garage; R314.3's actual requirement — an alarm on *each* storey of the dwelling, basements
included — had no rule at all, which is why a basement with zero alarms passed the gate.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import SLEEPING_OCCUPANCIES, AlarmKind, Occupancy
from typehaus.quantities import ft

_SMOKE_KINDS = (AlarmKind.SMOKE, AlarmKind.COMBO)
_CO_KINDS = (AlarmKind.CO, AlarmKind.COMBO)
# Storeys made only of these need no smoke alarm of their own: a detached garage is not a
# storey of the dwelling, and R314.3 counts dwelling storeys.
_NON_DWELLING_OCCUPANCIES = frozenset({Occupancy.GARAGE, Occupancy.UNCONDITIONED})


@check(Tier.CODE, "code.R314_R315_alarms")
def smoke_and_co_alarm_placement(ctx: CheckContext) -> list[Finding]:
    """Require a bedroom alarm and one alarm outside sleeping areas on each sleeping storey."""
    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        elements = ctx.plan.storey_elements(storey.tag)
        bedrooms = [element for element in elements
                    if element.element_kind == "Room" and element.occupancy in SLEEPING_OCCUPANCIES]
        if not bedrooms:
            continue
        alarms = [element for element in elements if element.element_kind == "Alarm"]
        for bedroom in bedrooms:
            alarm = next((item for item in alarms if item.room == bedroom.tag
                          and item.kind in _SMOKE_KINDS), None)
            if alarm is None:
                out.append(_fail("code.R314_R315_alarms",
                                 f"bedroom {bedroom.tag} has no smoke alarm", (bedroom.tag,),
                                 "R314.3"))
            else:
                out.append(_pass("code.R314_R315_alarms",
                                 f"{bedroom.tag} has bedroom smoke alarm {alarm.tag}", "R314.3"))
        non_sleeping_rooms = [element for element in elements if element.element_kind == "Room"
                              and element.tag not in {bedroom.tag for bedroom in bedrooms}]
        shared = next((item for item in alarms
                       if item.kind in _SMOKE_KINDS
                       and item.room in {room.tag for room in non_sleeping_rooms}), None)
        if not non_sleeping_rooms:
            out.append(_unknown("code.R314_R315_alarms",
                                f"no modeled area outside sleeping rooms on storey {storey.tag}",
                                tuple(bedroom.tag for bedroom in bedrooms), "R314.3"))
            continue
        if shared is None:
            out.append(_fail("code.R314_R315_alarms",
                             f"storey {storey.tag} has no smoke alarm outside sleeping areas",
                             tuple(bedroom.tag for bedroom in bedrooms), "R314.3"))
        else:
            out.append(_pass("code.R314_R315_alarms",
                             f"{storey.tag} has outside-sleeping smoke alarm {shared.tag}", "R314.3"))
    return out


@check(Tier.CODE, "code.R314_alarm_every_storey")
def alarm_on_every_storey(ctx: CheckContext) -> list[Finding]:
    """R314.3 — a smoke alarm on each storey of the dwelling, basements included.

    ``code.R314_R315_alarms`` walks *sleeping* storeys only: a storey with no bedroom on it
    was never visited, so a finished basement with zero alarms passed the permit gate. That
    is the single most common alarm write-up an inspector makes, and it is exactly the
    storey the fire starts on.

    R314.4's interconnection and primary-power requirement is measured through the one datum
    the model carries for it: an alarm that names no ``circuit`` is not hardwired, and a
    battery-only alarm cannot be interconnected.
    """
    cid, code = "code.R314_alarm_every_storey", "R314.3"
    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        elements = ctx.plan.storey_elements(storey.tag)
        rooms = [e for e in elements if e.element_kind == "Room"]
        if not rooms:
            out.append(_unknown(cid, f"storey {storey.tag} resolves no rooms, so whether it "
                                "is a storey of the dwelling cannot be decided",
                                (storey.tag,), code))
            continue
        if all(room.occupancy in _NON_DWELLING_OCCUPANCIES for room in rooms):
            out.append(_pass(cid, f"storey {storey.tag} holds no dwelling space "
                             "(garage/unconditioned only) — R314.3 does not reach it", code))
            continue
        alarms = [e for e in elements
                  if e.element_kind == "Alarm" and e.kind in _SMOKE_KINDS]
        if not alarms:
            out.append(_fail(cid, f"storey {storey.tag} has no smoke alarm; R314.3 requires "
                             "one on each storey of the dwelling including basements",
                             (storey.tag,), code))
            continue
        unpowered = [alarm.tag for alarm in alarms if not alarm.circuit]
        if unpowered:
            out.append(_fail(cid, f"storey {storey.tag}: alarm(s) "
                             f"{', '.join(sorted(unpowered))} name no circuit — R314.4 "
                             "requires primary power from the building wiring, and an "
                             "unwired alarm cannot be interconnected",
                             (storey.tag, *sorted(unpowered)), code))
        else:
            out.append(_pass(cid, f"storey {storey.tag} has {len(alarms)} hardwired smoke "
                             f"alarm(s) ({alarms[0].tag})", code))
    return out


@check(Tier.CODE, "code.R315_co_every_sleeping_area")
def co_alarm_outside_sleeping_areas(ctx: CheckContext) -> list[Finding]:
    """R315.3 — a CO alarm outside each separate sleeping area.

    The existing R315 rule is garage-triggered: it asks for CO coverage in rooms *near a
    garage*. R315.3's own requirement is unconditional wherever the dwelling has a
    fuel-burning appliance or an attached garage, and it is located by sleeping area — in
    the immediate vicinity of the bedrooms — not by storey.
    """
    cid, code = "code.R315_co_every_sleeping_area", "R315.3"
    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        elements = ctx.plan.storey_elements(storey.tag)
        bedrooms = [e for e in elements
                    if e.element_kind == "Room" and e.occupancy in SLEEPING_OCCUPANCIES]
        if not bedrooms:
            continue
        alarms = [e for e in elements if e.element_kind == "Alarm" and e.kind in _CO_KINDS]
        bedroom_tags = {room.tag for room in bedrooms}
        outside = [a for a in alarms if a.room not in bedroom_tags]
        if outside:
            out.append(_pass(cid, f"storey {storey.tag} sleeping area is covered by CO "
                             f"alarm {outside[0].tag}", code))
        elif alarms:
            out.append(_fail(cid, f"storey {storey.tag}: CO alarm(s) "
                             f"{', '.join(sorted(a.tag for a in alarms))} are inside "
                             "bedrooms; R315.3 locates one outside each separate sleeping "
                             "area", (storey.tag, *sorted(bedroom_tags)), code))
        else:
            out.append(_fail(cid, f"storey {storey.tag} has bedrooms "
                             f"({', '.join(sorted(bedroom_tags))}) and no CO alarm outside "
                             "the sleeping area", (storey.tag, *sorted(bedroom_tags)), code))
    return out


# How close a habitable room has to be to a garage before R315.2.2's garage-adjacency CO rule
# is in play. A garage sharing a wall is the obvious case; this house's is *freestanding*, 4'
# north, joined door-to-door by an enclosed breezeway — which is the same exposure path a
# common wall gives you, so the rule has to reach it. Beyond this band the garage is genuinely
# detached and the rule reports UNKNOWN rather than passing on a technicality.
_GARAGE_ADJACENCY = ft(12)


@check(Tier.CODE, "code.R315_garage_alarms")
def garage_heat_and_co_alarms(ctx: CheckContext) -> list[Finding]:
    """A garage wants a heat detector, and the dwelling beside it wants CO coverage.

    Neither half was covered. ``code.R314_R315_alarms`` filters on (SMOKE, COMBO) and only
    looks at storeys with bedrooms on them, so the garage storey was invisible to it.

    A garage gets a *heat* detector rather than a smoke alarm: exhaust, dust and a space that
    runs to outdoor temperature would nuisance-trip a smoke head, which is why the code asks
    for CO coverage on the dwelling side instead of a smoke alarm inside the garage.
    """
    from shapely.geometry import Polygon

    cid = "code.R315_garage_alarms"
    out: list[Finding] = []
    alarms = [element for element in ctx.plan.all_elements()
              if element.element_kind == "Alarm"]
    garages = [room for room in ctx.model.rooms if room.occupancy == Occupancy.GARAGE.value]
    if not garages:
        return [_unknown(cid, "no garage modelled", (), "R315.2.2")]

    for garage in garages:
        detector = next((item for item in alarms
                         if item.room == garage.tag and item.kind is AlarmKind.HEAT), None)
        if detector is None:
            out.append(_fail(cid, f"garage {garage.tag} has no heat detector", (garage.tag,),
                             "R315.2.2"))
        else:
            out.append(_pass(cid, f"{garage.tag} has heat detector {detector.tag}",
                             "R315.2.2"))

    # CO coverage on the dwelling side. Adjacency is measured between the resolved room
    # faces, so a breezeway-connected garage counts the same as a shared-wall one.
    garage_tags = {room.tag for room in garages}
    band = [Polygon(room.clear_face).buffer(_GARAGE_ADJACENCY.meters)
            for room in garages if len(room.clear_face) >= 3]
    neighbours = [room for room in ctx.model.rooms
                  if room.tag not in garage_tags and len(room.clear_face) >= 3
                  and any(zone.intersects(Polygon(room.clear_face)) for zone in band)]
    if not neighbours:
        out.append(_unknown(cid, "no habitable room within "
                                 f"{_GARAGE_ADJACENCY.feet:g}' of a garage — detached, so the "
                                 "garage-adjacency CO rule does not apply",
                            tuple(sorted(garage_tags)), "R315.2.2"))
        return out
    covered = [item for item in alarms
               if item.kind in _CO_KINDS
               and item.room in {room.tag for room in neighbours}]
    if not covered:
        out.append(_fail(cid, "no CO alarm in any room adjacent to the garage",
                         tuple(sorted(room.tag for room in neighbours)), "R315.2.2"))
    else:
        out.append(_pass(cid, f"{len(covered)} CO alarm(s) cover the rooms adjacent to the "
                              f"garage ({covered[0].tag})", "R315.2.2"))
    return out
