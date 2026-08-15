"""HVAC checks — duct/joist-bay coordination (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep import is_parallel_to_floor


# WARN severity + FAIL result, deliberately: the permit integrity gate only blocks on ERROR
# severity, and this finding is advisory, not a hard blocker.
def _advisory_fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return advisory(cid, msg, tags, Result.FAIL)


@check(Tier.STRUCTURAL, "mep.duct_joist_bay")
def duct_joist_bay(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for duct in ctx.model.ducts:
        if duct.routing != "joist_bay":
            continue
        if duct.floor_ref is None or not any(f.tag == duct.floor_ref for f in ctx.model.floors):
            out.append(_unknown(
                "mep.duct_joist_bay", f"duct {duct.tag} floor_ref did not resolve",
                (duct.tag,),
            ))
            continue
        if duct.conflicts or not duct.depth_ok:
            problems = list(duct.conflicts)
            if not duct.depth_ok:
                problems.append(f"depth {duct.depth_m / M_PER_IN:.1f}\" exceeds joist depth")
            out.append(_fail(
                "mep.duct_joist_bay", f"duct {duct.tag}: " + "; ".join(problems), (duct.tag,),
            ))
            continue
        note = f"duct {duct.tag} occupies its joist bay cleanly"
        if duct.crossings:
            points = ", ".join(
                f"({x / M_PER_IN / 12:.1f}', {y / M_PER_IN / 12:.1f}')" for x, y in duct.crossings
            )
            note += (f"; crosses bearing wall(s) at {points} — "
                    "provide fire blocking per R302.11")
        out.append(_pass("mep.duct_joist_bay", note, (duct.tag,)))
    return out


# ERV/HRV distribution coverage (ASHRAE 62.2-shaped, advisory). Sleeping/living/office
# rooms breathe fresh air; wet rooms give stale air back. Registers are matched to rooms
# by their authored `room=` when present, else by point-in-polygon against the resolved
# room's clear face (the floor_finish_over_radiant precedent).
_SUPPLY_OCCUPANCIES = frozenset({"bedroom", "living", "office"})
_STALE_OCCUPANCIES = frozenset({"bathroom", "laundry", "kitchen"})
_STALE_KINDS = frozenset({"return", "exhaust"})
# DuctSystem.TRANSFER is deliberately in neither set. A passive louver moves house air from
# one room to the next; it neither delivers the fresh air this check is counting nor takes
# any stale air out of the house, so crediting it either way would let a room pass on air it
# has already breathed. It still shows up in ``by_room`` — the register is real and a plan
# reader should see it — it just satisfies nothing.


def _registers_by_room(ctx: CheckContext, cid: str) -> tuple[dict, list, list[Finding]]:
    """Map every authored Register to a room tag. Returns (room->kinds, registers, findings)."""
    from shapely.geometry import Point, Polygon

    out: list[Finding] = []
    by_room: dict[str, set] = {}
    registers = []
    rooms = ctx.model.rooms
    for storey in ctx.model.plan.storeys:
        for element in ctx.model.plan.storey_elements(storey.tag):
            if element.element_kind != "Register":
                continue
            registers.append(element)
            room_tag = element.room
            if room_tag is None:
                point = Point(element.position.xy_m)
                room_tag = next(
                    (r.tag for r in rooms
                     if r.storey == storey.tag and len(r.clear_face) >= 3
                     and Polygon(r.clear_face).contains(point)), None)
            if room_tag is None:
                out.append(_unknown(
                    cid, f"register {element.tag} carries no room= and its position lands "
                    "in no room's clear face", (element.tag,),
                ))
                continue
            by_room.setdefault(room_tag, set()).add(element.kind.value)
    return by_room, registers, out


@check(Tier.ADVISORY, "mep.ventilation_distribution")
def ventilation_distribution(ctx: CheckContext) -> list[Finding]:
    cid = "mep.ventilation_distribution"
    rooms = ctx.model.rooms
    if not rooms:
        return [_unknown(cid, "no resolved rooms to distribute ventilation to")]
    by_room, registers, out = _registers_by_room(ctx, cid)

    for room in rooms:
        kinds = by_room.get(room.tag, set())
        if room.occupancy in _SUPPLY_OCCUPANCIES and room.conditioned:
            if "supply" in kinds:
                out.append(_pass(
                    cid, f"{room.tag} ({room.occupancy}) has a fresh-air supply register",
                    (room.tag,),
                ))
            else:
                out.append(_advisory_fail(
                    cid, f"{room.tag} ({room.occupancy}) is conditioned but has no "
                    "fresh-air supply register", (room.tag,),
                ))
        if room.occupancy in _STALE_OCCUPANCIES:
            if kinds & _STALE_KINDS:
                out.append(_pass(
                    cid, f"{room.tag} ({room.occupancy}) has a return/exhaust terminal",
                    (room.tag,),
                ))
            else:
                out.append(_advisory_fail(
                    cid, f"{room.tag} ({room.occupancy}) has no return or exhaust "
                    "terminal", (room.tag,),
                ))

    # Count sanity: at least one terminal per room the whole-house rate has to reach —
    # counts are read off the model, never pinned to an authored constant.
    supply_count = sum(1 for r in registers if r.kind.value == "supply")
    stale_count = sum(1 for r in registers if r.kind.value in _STALE_KINDS)
    need_supply = sum(1 for r in rooms
                      if r.occupancy in _SUPPLY_OCCUPANCIES and r.conditioned)
    need_stale = sum(1 for r in rooms if r.occupancy in _STALE_OCCUPANCIES)
    if supply_count >= need_supply and stale_count >= need_stale:
        out.append(_pass(
            cid, f"{supply_count} supply / {stale_count} return+exhaust terminals cover "
            f"{need_supply} supply-required and {need_stale} stale-required rooms",
        ))
    else:
        out.append(_advisory_fail(
            cid, f"terminal count short of the room count: {supply_count} supply for "
            f"{need_supply} rooms, {stale_count} return/exhaust for {need_stale} rooms",
            (),
        ))
    return out


@check(Tier.ADVISORY, "mep.duct_direction_hint")
def duct_direction_hint(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    floors = {f.tag: f for f in ctx.model.floors}
    for duct in ctx.model.ducts:
        if duct.routing != "joist_bay" or duct.floor_ref not in floors:
            continue
        if not is_parallel_to_floor(list(duct.path), floors[duct.floor_ref]):
            out.append(_advisory_fail(
                "mep.duct_direction_hint",
                f"duct {duct.tag} runs across joists in JOIST_BAY routing — "
                "route across joists in a soffit or chase", (duct.tag,),
            ))
    return out


@check(Tier.ADVISORY, "mep.heating_capacity")
def heating_capacity(ctx: CheckContext) -> list[Finding]:
    """Per-zone block load at design temp vs the zone's outdoor unit at-design capacity.

    A zone is the authored ``Equipment.zone_rooms`` of a rated unit, unioned with the rooms
    of every indoor head that names it through ``outdoor_ref``. Only equipment carrying an
    authored ``heating_capacity*`` rating opens a zone.

    Supplemental resistance heat inside a zone's rooms — sized radiant mats, the electric
    fireplace — is *added to* that zone's capacity rather than ignored: at the design
    temperature it is heat the outdoor unit does not have to make, and pretending otherwise
    reports a shortfall the house does not have. It never opens a zone of its own (nothing is
    sized around a fireplace), and it is keyed by room, so it can never be credited twice. The
    garage unit heater still counts for nothing — it carries no rating and the garage is
    unconditioned.

    Nothing here is a Manual J: it reuses ``estimate_block_load`` with a room filter (whose
    room attribution is approximate — see its docstring), and missing inputs stay UNKNOWN,
    never estimated. A conditioned room that no unit claims is reported as unclaimed rather
    than assigned to the nearest zone.
    """
    from typehaus.takeoff.hvac import heating_zones

    cid = "mep.heating_capacity"
    zones, unclaimed = heating_zones(ctx.model, ctx.preferences)
    out: list[Finding] = []
    if not zones:
        out.append(_unknown(cid, "no Equipment carries a heating_capacity_btuh / "
                                 "heating_capacity_at_design_btuh rating"))
    for zone in zones:
        load = zone.heating_load_btu_per_hour
        served = ", ".join(sorted(zone.rooms)) or "no rooms"
        if not zone.rooms:
            out.append(_unknown(
                cid, f"{zone.equipment_tag}: no zone_rooms authored (and no indoor head "
                     "names it), so there is no zone to size against",
                (zone.equipment_tag,)))
            continue
        capacity = zone.heating_capacity_at_design_btuh
        if capacity is None:
            out.append(_unknown(
                cid, f"{zone.name}: load {load:,.0f} Btu/h at design over {served}, but "
                     f"{zone.type_tag or zone.equipment_tag} has no "
                     "heating_capacity_at_design_btuh", (zone.equipment_tag,)))
            continue
        margin = zone.heating_margin_btuh or 0.0
        supplement = (f" + {zone.supplemental_btuh:,.0f} Btu/h supplemental "
                      f"({', '.join(zone.supplemental_tags)})"
                      if zone.supplemental_tags else "")
        detail = (f"{zone.name}: block load {load:,.0f} Btu/h at design over {served} vs "
                  f"{capacity:,.0f} Btu/h at-design capacity{supplement} "
                  f"(margin {margin:+,.0f} Btu/h)")
        if zone.unknown_inputs:
            out.append(_unknown(
                cid, f"{detail}; block-load inputs missing: "
                     + ", ".join(zone.unknown_inputs), (zone.equipment_tag,)))
        elif margin >= 0:
            out.append(_pass(cid, detail, (zone.equipment_tag,)))
        else:
            out.append(_advisory_fail(cid, detail + " — undersized at design temp",
                                      (zone.equipment_tag,)))
    if unclaimed:
        out.append(_unknown(
            cid, "conditioned room(s) in no equipment zone_rooms: "
                 + ", ".join(sorted(unclaimed)), tuple(sorted(unclaimed))))
    return out


@check(Tier.ADVISORY, "mep.cooling_capacity")
def cooling_capacity(ctx: CheckContext) -> list[Finding]:
    """Per-zone cooling block load vs the unit's authored sensible cooling capacity.

    Advisory and deliberately partial: the block load's cooling side is a UA + window-solar
    sum with no latent split and no internal gains, so it is a screen for "wildly over/under
    size", not a selection. A unit with no ``cooling_capacity_btuh`` stays UNKNOWN — a
    heating rating is not a cooling rating.
    """
    from typehaus.takeoff.hvac import heating_zones

    cid = "mep.cooling_capacity"
    if ctx.model.plan.project.site.design_temp_cooling is None:
        return [_unknown(cid, "Site.design_temp_cooling is not authored")]
    zones, _ = heating_zones(ctx.model, ctx.preferences)
    out: list[Finding] = []
    for zone in zones:
        if not zone.rooms:
            continue
        capacity = zone.cooling_capacity_btuh
        load = zone.cooling_load_btu_per_hour
        if capacity is None:
            out.append(_unknown(
                cid, f"{zone.name}: sensible cooling load {load:,.0f} Btu/h, but "
                     f"{zone.type_tag or zone.equipment_tag} has no "
                     "cooling_capacity_btuh", (zone.equipment_tag,)))
            continue
        margin = zone.cooling_margin_btuh or 0.0
        detail = (f"{zone.name}: sensible cooling load {load:,.0f} Btu/h vs "
                  f"{capacity:,.0f} Btu/h rated (margin {margin:+,.0f} Btu/h; UA + window "
                  "solar only — no latent or internal gains)")
        if zone.unknown_inputs:
            out.append(_unknown(cid, f"{detail}; block-load inputs missing: "
                                     + ", ".join(zone.unknown_inputs),
                                (zone.equipment_tag,)))
        elif margin >= 0:
            out.append(_pass(cid, detail, (zone.equipment_tag,)))
        else:
            out.append(_advisory_fail(cid, detail + " — under the sensible cooling load",
                                      (zone.equipment_tag,)))
    return out
