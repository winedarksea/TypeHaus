"""IRC R327 — stationary storage battery systems (energy storage systems).

The profile's base is the 2018 IRC, where this article is **R327**; the 2021 edition
renumbered it to R328 and expanded it. The citations here follow the declared edition, not
the newer numbering — a permit reader checking a section number against the adopted book is
the whole point of carrying a code_ref.

Three requirements are encoded, and they are the three that an ESS actually turns on:

- **R327.2 Equipment listings** — the unit is listed and labeled to UL 9540.
- **R327.5 Energy ratings** — 20 kWh per unit, 40 kWh aggregate in a dwelling space.
- **R327.7 Fire detection** — smoke *and* heat coverage in the room the ESS is in.

Not encoded, and not claimed: R327.3 installation per the manufacturer's instructions and
R327.6 protection from impact. Both are field/judgement requirements with nothing in the
model to grade — an instruction manual is not geometry, and "subject to vehicle damage" is
a site condition, not a room property.

Every check no-ops (returns nothing) when no ESS is placed, the same guard
``checks/mep/supply_protection.py`` uses: a house with no battery is not a house failing the
battery rules.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import AlarmKind, EquipmentKind, Occupancy
from typehaus.quantities import ft

# R327.5. Per-unit and aggregate ceilings for storage inside a dwelling. The aggregate is
# what the two-battery future runs into, which is why it is computed over the placements
# rather than read off a single type.
_MAX_KWH_PER_UNIT = 20.0
_MAX_KWH_AGGREGATE = 40.0

# R327.7 asks for detection in the room the ESS is in. Where the ESS room is too small to
# host its own alarms — a 3'x4' closet often is — an alarm just outside the door is the
# real-world install, so coverage is measured as "in the room, or within this reach of it".
_DETECTION_REACH = ft(6)

# Occupancies that are dwelling space for R327.5's aggregate ceiling. A garage is
# deliberately absent: the article treats an attached garage as a permitted location
# separate from the dwelling's interior rooms, and relocating the ESS to the garage is the
# documented future move (notes/backup_power.md) — this exemption is the seam that makes it
# a re-room rather than a code redesign.
_GARAGE_OCCUPANCIES = frozenset({Occupancy.GARAGE.value})


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
        return []
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


@check(Tier.CODE, "code.R327_ess_capacity")
def ess_capacity(ctx: CheckContext) -> list[Finding]:
    """R327.5 — 20 kWh per unit, 40 kWh aggregate in the dwelling.

    The aggregate is summed over the units in *dwelling* rooms only. A garage placement is a
    separate permitted location under R327.4 and does not load the interior aggregate; that
    exemption is what lets the future garage relocation be a change of room rather than a
    change of design.
    """
    cid, code = "code.R327_ess_capacity", "R327.5"
    batteries = _batteries(ctx)
    if not batteries:
        return []
    occupancy = {room.tag: room.occupancy for room in ctx.model.rooms}
    out: list[Finding] = []
    indoor_kwh = 0.0
    indoor_tags: list[str] = []
    for battery in batteries:
        product = _type_of(ctx, battery)
        kwh = getattr(product, "storage_kwh", None) if product is not None else None
        if kwh is None:
            out.append(_unknown(cid, f"{battery.tag} declares no `storage_kwh`, so neither "
                                     "the per-unit nor the aggregate limit can be graded",
                                (battery.tag,), code))
            continue
        if kwh > _MAX_KWH_PER_UNIT + 1e-9:
            out.append(_fail(cid, f"{battery.tag} is rated {kwh:g} kWh; R327.5 limits one "
                                  f"unit to {_MAX_KWH_PER_UNIT:g} kWh",
                             (battery.tag,), code))
        else:
            out.append(_pass(cid, f"{battery.tag} is {kwh:g} kWh, within the "
                                  f"{_MAX_KWH_PER_UNIT:g} kWh per-unit limit", code))
        room = getattr(battery, "room", None)
        if room is not None and occupancy.get(room) in _GARAGE_OCCUPANCIES:
            continue  # R327.4 permitted garage location — not part of the interior aggregate
        indoor_kwh += float(kwh)
        indoor_tags.append(battery.tag)

    if indoor_tags:
        if indoor_kwh > _MAX_KWH_AGGREGATE + 1e-9:
            out.append(_fail(cid, f"{len(indoor_tags)} units inside the dwelling total "
                                  f"{indoor_kwh:g} kWh; R327.5 limits the aggregate to "
                                  f"{_MAX_KWH_AGGREGATE:g} kWh",
                             tuple(sorted(indoor_tags)), code))
        else:
            out.append(_pass(cid, f"{indoor_kwh:g} kWh aggregate inside the dwelling "
                                  f"({', '.join(sorted(indoor_tags))}), within the "
                                  f"{_MAX_KWH_AGGREGATE:g} kWh limit", code))
    return out


@check(Tier.CODE, "code.R327_ess_detection")
def ess_detection(ctx: CheckContext) -> list[Finding]:
    """R327.7 — smoke and heat detection covering the room the ESS is in.

    Both, not either: R327.7 sends you to R314 for smoke coverage and adds a listed heat
    detector for the locations a smoke alarm cannot serve. A battery closet is exactly such
    a location — the failure mode that matters starts as heat — so this check wants one of
    each covering the ESS room.

    Coverage is measured with the same shapely proximity pattern
    ``alarms.py::garage_heat_and_co_alarms`` uses for the garage's CO neighbours: an alarm
    in the ESS room counts, and so does one in a room whose face comes within
    ``_DETECTION_REACH`` — because a 3'x4' closet is often too small to host two heads, and
    a head on the ceiling right outside its door is the install that gets built.
    """
    from shapely.geometry import Polygon

    cid, code = "code.R327_ess_detection", "R327.7"
    batteries = _batteries(ctx)
    if not batteries:
        return []
    alarms = [element for element in ctx.plan.all_elements()
              if element.element_kind == "Alarm"]
    rooms = {room.tag: room for room in ctx.model.rooms}

    out: list[Finding] = []
    for room_tag in sorted({getattr(b, "room", None) for b in batteries} - {None}):
        room = rooms.get(room_tag)
        if room is None or len(room.clear_face) < 3:
            out.append(_unknown(cid, f"ESS room {room_tag} has no resolved face, so alarm "
                                     "coverage cannot be measured", (str(room_tag),), code))
            continue
        band = Polygon(room.clear_face).buffer(_DETECTION_REACH.meters)
        nearby = {tag for tag, other in rooms.items()
                  if len(other.clear_face) >= 3
                  and band.intersects(Polygon(other.clear_face))}
        covering = [a for a in alarms if a.room in nearby]
        for kind, label in ((AlarmKind.SMOKE, "smoke"), (AlarmKind.HEAT, "heat")):
            found = next((a for a in covering
                          if a.kind is kind
                          or (kind is AlarmKind.SMOKE and a.kind is AlarmKind.COMBO)), None)
            if found is None:
                out.append(_fail(cid, f"ESS room {room_tag} has no {label} alarm in it or "
                                      f"within {_DETECTION_REACH.feet:g}'; R327.7 requires "
                                      "both smoke and heat detection at the storage system",
                                 (str(room_tag),), code))
            else:
                where = ("in the room" if found.room == room_tag
                         else f"in {found.room}, within {_DETECTION_REACH.feet:g}'")
                out.append(_pass(cid, f"ESS room {room_tag} is covered by {label} alarm "
                                      f"{found.tag} ({where})", code))
    return out
