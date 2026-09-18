"""HVAC checks — duct/joist-bay coordination (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.checks._authoring import advisory
from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section, open_web_opening_m
from typehaus.resolve.mep import is_parallel_to_floor

if TYPE_CHECKING:
    pass


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


@check(Tier.STRUCTURAL, "mep.duct_soffit_occupancy")
def duct_soffit_occupancy(ctx: CheckContext) -> list[Finding]:
    """Everything inside a modeled ``Soffit`` fits its **derived** clear section.

    The other half of ``mep.duct_joist_bay``. ``JOIST_BAY`` routing has had a validator
    since MEP Phase 3; ``SOFFIT``/``CHASE`` had none — they were the flag that turned the
    joist check *off*. So every clearance claim about a duct box in this house lived in a
    plan comment as hand arithmetic: "the plan's 2'-8" box loses 4 1/4" total to
    framing/lining, leaving only 27 3/4" clear", "the air handler's 21"x43" case fills the
    box y 6'-0"..9'-7", leaving ~5" either side of it". Right, both of them, and neither
    re-runnable when the ``FramingSpec`` changes.

    The clear section is never authored — it comes off the soffit's own drop, its framing
    member and the gypsum lining, from the same arithmetic ``framing/soffit.py`` builds the
    ladders with (→ ``soffit_clear_section``). An authored ``clear_width`` would be a second
    source of truth for a number the framing already states, and would drift the first time
    a 2x2 became a 2x3.

    A soffit with no ``FramingSpec`` reports UNKNOWN rather than being graded against its
    finished dimension: an unframed box has no clear width, and crediting 4 1/4" of gypsum
    and lumber as if it were air is exactly the mistake the check exists to catch.
    """
    from typehaus.resolve.mep_soffit import soffit_occupancy

    cid = "mep.duct_soffit_occupancy"
    out: list[Finding] = []
    claimed = {duct.soffit_ref for duct in ctx.model.ducts if duct.soffit_ref}
    claimed |= {ref for ref in (getattr(el, "soffit_ref", None)
                                for el in ctx.plan.all_elements()) if ref}
    known = {soffit.tag for soffit in ctx.model.soffits}
    for missing in sorted(claimed - known):
        out.append(_fail(cid, f"soffit_ref={missing!r} names no modeled Soffit", (missing,)))
    for soffit in ctx.model.soffits:
        if soffit.tag not in claimed:
            continue  # a soffit nobody is hiding anything in has nothing to grade
        conflicts, section = soffit_occupancy(ctx.model, soffit)
        if section is None:
            out.append(_unknown(
                cid, f"soffit {soffit.tag} states no FramingSpec (or is not an "
                     "axis-aligned rectangle), so it has no derivable clear section",
                (soffit.tag,)))
            continue
        if conflicts:
            out.append(_fail(cid, f"soffit {soffit.tag}: " + "; ".join(conflicts),
                             (soffit.tag,)))
            continue
        out.append(_pass(
            cid, f"soffit {soffit.tag} holds everything claiming it: "
                 f"{section.width_m / M_PER_IN:.2f}\" clear x "
                 f"{section.drop_m / M_PER_IN:.2f}\" drop", (soffit.tag,)))
    if not out:
        out.append(_unknown(cid, "no duct or machine names a modeled Soffit", ()))
    return out


@check(Tier.ADVISORY, "mep.duct_direction_hint")
def duct_direction_hint(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    floors = {f.tag: f for f in ctx.model.floors}
    for duct in ctx.model.ducts:
        if duct.routing != "joist_bay" or duct.floor_ref not in floors:
            continue
        floor = floors[duct.floor_ref]
        if not is_parallel_to_floor(list(duct.path), floor):
            opening_m = (open_web_opening_m(cross_section(floor.members[0].profile))
                        if floor.members else None)
            if opening_m is not None and duct.depth_m <= opening_m + 1e-9:
                # A truss-floor run through the open webs needs no soffit hint.
                continue
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
    of every indoor head that names it through ``outdoor_ref``. Only equipment carrying a
    published ``heating_ratings`` table (or a resistance rating) opens a zone, and the
    at-design capacity is READ from that table at ``Site.design_temp_heating`` rather than
    authored — see ``takeoff/hvac.capacity_at`` and decision #76.

    **There is deliberately NO upper bound here.** A cold-climate heat pump sized for −15 °F
    is *supposed* to be enormous at 47 °F, and Manual S caps heat-pump selection through the
    COOLING sizing factor, not a heating one. An upper bound on heating capacity would be a
    rule this engine invented, and it would fail correctly-sized equipment. Heating over-size
    is measured — correctly, and across the published rows rather than at one point — by
    ``mep.heat_pump_turndown``. The defensible ``<= 1.40`` applies to COMBUSTION equipment
    (a type carrying ``afue``), and catlin has none.

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
        out.append(_unknown(cid, "no Equipment carries a heating_ratings table or a "
                                 "resistance_heating_btuh rating"))
    for zone in zones:
        load = zone.heating_load_btu_per_hour
        served = ", ".join(sorted(zone.rooms)) or "no rooms"
        if not zone.rooms:
            out.append(_unknown(
                cid, f"{zone.equipment_tag}: no zone_rooms authored (and no indoor head "
                     "names it), so there is no zone to size against",
                (zone.equipment_tag,)))
            continue
        # A compressor lockout WARMER than the site design temperature is a FAIL before
        # any margin arithmetic: the unit is off at the hour the load is being sized for,
        # so whatever capacity it publishes is capacity the house does not have.
        lockout = zone.min_operating_temp_f
        if (lockout is not None and zone.design_temp_f is not None
                and lockout > zone.design_temp_f):
            out.append(_advisory_fail(
                cid, f"{zone.name}: {zone.type_tag or zone.equipment_tag} locks out below "
                     f"{lockout:g} °F and the site designs at {zone.design_temp_f:g} °F — "
                     f"the unit is OFF at the design hour, so the zone's {load:,.0f} Btu/h "
                     "load over " + served + " is carried by whatever else there is",
                (zone.equipment_tag,)))
            continue
        capacity = zone.heating_capacity_at_design_btuh
        if capacity is None:
            reason = ("has no heating_ratings table" if not zone.heating_ratings
                      else f"publishes no row spanning {zone.design_temp_f:g} °F, and "
                           "capacity_at refuses to extrapolate past either end of a table")
            out.append(_unknown(
                cid, f"{zone.name}: load {load:,.0f} Btu/h at design over {served}, but "
                     f"{zone.type_tag or zone.equipment_tag} {reason}",
                (zone.equipment_tag,)))
            continue
        margin = zone.heating_margin_btuh or 0.0
        supplement = (f" + {zone.supplemental_btuh:,.0f} Btu/h supplemental "
                      f"({', '.join(zone.supplemental_tags)})"
                      if zone.supplemental_tags else "")
        basis = f", {zone.capacity_basis}" if zone.capacity_basis else ""
        detail = (f"{zone.name}: block load {load:,.0f} Btu/h at design over {served} vs "
                  f"{capacity:,.0f} Btu/h at-design capacity{basis}{supplement} "
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

    **Two-sided now.** It was ``elif margin >= 0: PASS`` with no upper bound anywhere, which
    is half a check: catlin's System 3 was at 276% of its zone's cooling load and passed.
    Manual S caps cooling selection at 1.30 of the design load for a modulating unit and
    1.15 for a single-stage one, and which one binds is DERIVED from the unit's own ratings
    table (→ ``_cooling_sizing_ceiling``). Over-size is not a comfort preference: an
    over-sized compressor short-cycles, never reaches the steady-state coil condition its
    latent rating was measured at, and leaves a house cold and damp.

    Advisory and deliberately partial. The block load's cooling side carries hourly glass at
    one coincident peak hour, the AED excursion and Manual J internal gains, but no roof
    sol-air term where no absorptance is stated and only occupant latent — so the LOAD is an
    upper bound and the over-size RATIO is therefore a LOWER bound. Every message says so.
    A unit with no ``cooling_capacity_btuh`` stays UNKNOWN — a heating rating is not a
    cooling rating.
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
        # The caveats come off the block load itself rather than being restated here, so a
        # term the method stops carrying (or starts) cannot drift out of step with the
        # sentence a reviewer reads. They are NOT ``unknown_inputs``: an omitted term is a
        # stated limitation of the method, and taking the verdict to UNKNOWN over one would
        # make every house unsizeable.
        caveats = ("; ".join(zone.cooling_caveats) if zone.cooling_caveats
                   else "no stated omissions")
        ratio = capacity / load if load > 0 else None
        ceiling = _cooling_sizing_ceiling(zone)
        detail = (f"{zone.name}: sensible cooling load {load:,.0f} Btu/h vs "
                  f"{capacity:,.0f} Btu/h rated (margin {margin:+,.0f} Btu/h"
                  + (f", ratio {ratio:.2f} against a Manual S ceiling of {ceiling:.2f}"
                     if ratio is not None else "")
                  + f") + {zone.latent_btu_per_hour:,.0f} Btu/h latent. "
                  f"The LOAD is an upper bound, so the RATIO is a LOWER one: {caveats}")
        if zone.unknown_inputs:
            out.append(_unknown(cid, f"{detail}; block-load inputs missing: "
                                     + ", ".join(zone.unknown_inputs),
                                (zone.equipment_tag,)))
        elif margin < 0:
            out.append(_advisory_fail(cid, detail + " — under the sensible cooling load",
                                      (zone.equipment_tag,)))
        elif ratio is not None and ratio > ceiling:
            out.append(_advisory_fail(
                cid, detail + f" — OVER-SIZED: Manual S caps cooling selection at "
                              f"{ceiling:.2f} of the load, and an over-sized compressor "
                              "short-cycles, never reaches its steady-state latent removal, "
                              "and leaves the house cold and damp",
                (zone.equipment_tag,)))
        else:
            out.append(_pass(cid, detail, (zone.equipment_tag,)))
    return out


# Manual S §2 cooling sizing factors. A MODULATING unit may be selected to 1.30 of the
# design cooling load because it can run down to the load at part load; a single-stage one
# is capped at 1.15, because at 1.30 it is on for half the hour and off for the other half
# and never reaches the steady-state coil condition its latent rating was measured at.
_MODULATING_COOLING_CEILING = 1.30
_SINGLE_STAGE_COOLING_CEILING = 1.15


def _cooling_sizing_ceiling(zone) -> float:
    """Which Manual S ceiling binds this unit — DERIVED from its own ratings table.

    A row whose minimum and maximum differ is a unit that modulates; a table where every row
    has ``minimum == maximum`` is single-stage, and that is a positive statement the type
    made about itself rather than an absence. No new authored flag: a flag would be a second
    place for the same fact to be wrong, and the table already says it.

    A unit with no table at all takes the modulating ceiling, which is the permissive
    reading — this check is about catching gross over-size, and inventing the stricter cap
    for a machine nobody has characterised would fail it on the engine's ignorance.
    """
    rows = getattr(zone, "heating_ratings", ())
    if not rows:
        return _MODULATING_COOLING_CEILING
    modulates = any(row.minimum_btuh is not None and row.maximum_btuh is not None
                    and row.minimum_btuh < row.maximum_btuh for row in rows)
    return _MODULATING_COOLING_CEILING if modulates else _SINGLE_STAGE_COOLING_CEILING
