"""Can a room whose only heat is a radiant floor actually carry that room at design?

IRC R303.10, adopted unamended in Minnesota, wants heating capable of 68 F three feet above
the floor at the design temperature. Nothing in the engine asked that of a single room, and
two of Catlin's three radiant zones are the sole heat source in the room they lie in.
Schluter's own literature calls DITRA-HEAT a *secondary* heat source, and whether one of
these zones is nevertheless enough is arithmetic — area, delivered output, room load — which
is exactly the shape of question this engine exists to answer and had not been asked.

**Scope is radiant rooms, and that is the whole check.** A room the ducted system or a head
physically reaches is not this check's subject: its heat is a zone's margin, which
``mep.heating_capacity`` already grades against a zone-scoped block load. Nor is a room with
no heat of its own that is simply open to one — Catlin's basement bathroom takes its heat
through a doorway, and transfer through an opening is not something this model can see. A
room with a radiant floor and nothing else is the one case where every term is in the model.

**Where a supply register or a head IS in the room, this passes without any ΔT arithmetic,
deliberately.** The delivered output of a modulating inverter head is not a model fact: it
depends on the supply temperature it happens to be running at, which depends on the outdoor
temperature, the compressor's modulation and the thermostat's call. The honest statement is
that the room is served, and the sizing question belongs to the zone.

**A shortfall reports UNKNOWN, not FAIL**, and the reason is in ``estimate_block_load``'s own
docstring: a room-scoped load is *approximate by design*. Envelope area is attributed by plan
overlap, air-side terms are apportioned by share of conditioned volume, and there are no
room-level internal gains. All three over-state a small interior room — a bathroom on
continuous extract is credited with a pro-rata slice of ventilation air that in fact leaves
through it, and gets no credit for the lights, the occupant or the hot water. Turning that
into a FAIL would be turning an approximation into a verdict. What the finding does instead
is print both numbers and the shortfall, which is what a reviewer needs to decide whether to
buy an hour of Manual J.

The FAIL is kept for the case that needs no load at all: a room whose sole heat source
delivers *nothing* — every zone in it declaring no wattage and no output, with no
supplemental heat beside it. That is not a thin margin, it is an unheated room.

Habitable rooms cite R303.10. **Bathrooms do not**, and the message says so: R202 defines
habitable space as a space for living, sleeping, eating or cooking and its very next
sentence excludes bathrooms and toilet rooms. Both of Catlin's sole-heat radiant rooms are
bathrooms, so neither is actually a code subject — which is worth saying out loud rather
than quietly citing a section that does not reach them.

Oracled by ``houses/catlin/notes/room_heat_loss_baths.md``, reproduced by
``tests/test_room_heat_source.py``.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, not_applicable, passed, unknown
from typehaus.checks.code.mn_residential._common import HABITABLE_OCCUPANCIES
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import Occupancy

#: R202 excludes these from "habitable space" by name, so R303.10 does not reach them. They
#: still want heat and the arithmetic is still worth doing — it is the citation that changes.
_NOT_HABITABLE = frozenset({Occupancy.BATHROOM})


@check(Tier.ADVISORY, "mep.room_heat_source")
def room_heat_source(ctx: CheckContext) -> list[Finding]:
    """Radiant output against the room's own design load, where the floor is the only heat."""
    from typehaus.energy import estimate_block_load
    from typehaus.takeoff.hvac import room_heat_sources

    cid = "mep.room_heat_source"
    rooms = [row for row in room_heat_sources(ctx.model, ctx.preferences)
             if row.radiant_tags]
    if not rooms:
        # Earned: every conditioned room was walked and not one carries a FloorHeat zone,
        # so no room in this building is heated by a floor at all.
        return [not_applicable(cid, "no conditioned room in this plan carries a radiant "
                                    "floor zone, so no room is heated by one", ())]

    out: list[Finding] = []
    for row in rooms:
        zones = ", ".join(row.radiant_tags)
        if row.reached_by:
            out.append(passed(
                cid, f"{row.room}: {zones} supplements a room the conditioned-air system "
                     f"reaches ({', '.join(row.reached_by)}) — the sizing question is that "
                     "zone's margin, graded by mep.heating_capacity, and the delivered "
                     "output of a modulating head is not a model fact", ()))
            continue

        habitable = (row.occupancy in {item.value for item in HABITABLE_OCCUPANCIES}
                     or row.occupancy in HABITABLE_OCCUPANCIES)
        excluded = (row.occupancy in {item.value for item in _NOT_HABITABLE}
                    or row.occupancy in _NOT_HABITABLE)
        code = "R303.10" if habitable else None
        scope = ("" if habitable else
                 " (R202 excludes a bathroom from habitable space, so R303.10 does not reach "
                 "this room — the arithmetic still stands)" if excluded else
                 " (not a habitable space under R202, so R303.10 does not reach it)")

        if row.radiant_undeclared:
            out.append(unknown(
                cid, f"{row.room}'s only heat is {zones} and "
                     f"{', '.join(row.radiant_undeclared)} states no "
                     "delivered_btuh_per_ft2 — what a heated floor DELIVERS is not derivable "
                     "from what its cable draws, so this cannot be graded" + scope,
                (row.room, *row.radiant_undeclared), code=code,
                fix="author delivered_btuh_per_ft2 from the covering's own output curve at "
                    "the design floor and operative temperatures"))
            continue

        delivered = row.delivered_btuh
        if delivered is None or delivered <= 0.0:
            out.append(advisory(
                cid, f"{row.room}'s only heat is {zones} and it delivers nothing: no zone "
                     "in the room states a wattage or an output, and no supplemental heat "
                     "stands beside it" + scope,
                (row.room, *row.radiant_tags), Result.FAIL, code=code,
                fix="size the mat, or give the room a supply register"))
            continue

        report = estimate_block_load(ctx.model, ctx.preferences,
                                     rooms=frozenset({row.room}))
        if report.unknown_inputs:
            out.append(unknown(
                cid, f"{row.room}'s only heat is {zones} at {delivered:.0f} Btu/h, but its "
                     "design load rests on inputs this model does not carry: "
                     + ", ".join(report.unknown_inputs) + scope,
                (row.room,), code=code))
            continue

        load = report.heating_load_btu_per_hour
        supplement = (f" + {row.supplemental_btuh:.0f} Btu/h from "
                      f"{', '.join(row.supplemental_tags)}" if row.supplemental_tags else "")
        if delivered + 1e-9 >= load:
            out.append(passed(
                cid, f"{row.room}: {zones}{supplement} delivers {delivered:.0f} Btu/h "
                     f"against a {load:.0f} Btu/h design load — covered by "
                     f"{delivered - load:.0f} Btu/h" + scope, (), code=code))
        else:
            out.append(unknown(
                cid, f"{row.room}: {zones}{supplement} delivers {delivered:.0f} Btu/h "
                     f"against a {load:.0f} Btu/h design load — {load - delivered:.0f} Btu/h "
                     f"({(load - delivered) / load * 100:.0f}%) short. UNKNOWN and not a "
                     "FAIL because a room-scoped block load is approximate by design: "
                     "envelope area is attributed by plan overlap, air-side terms by share "
                     "of conditioned volume, and there are no room-level internal gains — "
                     "all three over-state a small interior room" + scope,
                (row.room, *row.radiant_tags), code=code,
                fix="work this room by hand (Manual J) before the permit set, or heat more "
                    "floor area — a cable ladder is capped by the square feet it can cover, "
                    "not by its wattage"))
    return out
