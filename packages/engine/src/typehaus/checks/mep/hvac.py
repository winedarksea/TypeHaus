"""HVAC checks — duct/joist-bay coordination (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

from typehaus.checks._authoring import advisory, not_applicable
from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section, open_web_opening_m
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


@check(Tier.STRUCTURAL, "mep.duct_joist_bay_occupancy")
def duct_joist_bay_occupancy(ctx: CheckContext) -> list[Finding]:
    """Two runs drawn through the same joist bay at the same station and the same height.

    ``mep.duct_joist_bay`` grades each run against the *framing*: does it straddle a joist
    line, does it fit the clear bay, does it fit the joist depth. Every one of those
    questions is asked of one run at a time, so a cavity can hold two runs on the identical
    bay centre at the identical elevation and both of them pass — the bay is wide enough for
    either, and nothing ever asks about the pair. That is the hole
    ``mep.duct_soffit_occupancy`` closed for a dropped box; this is its joist-bay half, and
    it reuses that module's ``segment_band`` sweep and its pairwise loop.

    **What it does NOT reuse is ``HANGER_GAP_M``, and that is the whole difference between
    a bay and a soffit.** A soffit hangs its contents on straps off a ladder, so 2" between
    them buys a flange and a hand. A joist bay carries them: a semi-rigid radial lies on the
    bottom chord or threads a web, nothing is strapped to anything, and two 3" radials
    touching in a 14 1/2" clear bay is what the neck of a radial bundle looks like. The
    question a bay asks is not "is there room for a hanger" but **"does the bay hold both"**,
    so the clear width is the criterion (``clear_bay_width_m``, derived from the resolved
    joist lines) and it is asked only of runs that actually overlap.

    **Only parallel segments are paired.** Between two runs that *cross*, the same
    subtraction returns a number with no meaning — the twelve FS-S-WEST radials produce "-112
    inches of gap" where one passes over another. Whether a run may cross a joist line at all
    is a real and different question, and ``mep.duct_joist_bay`` already asks it (an open-web
    floor answers with its chord opening).

    Three things excuse a parallel pair, and all three are earned from the model: **a joist
    between them** when they are separated across the joists (``joist_line_stations``, the
    same derivation ``duct_bay_occupancy`` grades a straddle against — runs separated *along*
    the joists cannot have one between them, and the excuse is not offered there); **no
    vertical overlap**, since an 11 7/8" open-web floor stacks two 3" radials with room to
    spare; and **a fitting**, ``ducts_are_joined``, which is a tee and not a collision.

    An overlapping pair the bay can still hold is UNKNOWN, not FAIL, and the distinction is
    the model's rather than the building's: this model gives a run one centreline per bay, so
    two lanes sharing a bay are necessarily drawn on top of each other. The FS-S-WEST note in
    ``plan/mep_erv.py`` says exactly that about STUDY and LAUNDRY. What the check *can* say —
    and what nothing said before — is that they are in the same bay at all, and that the bay
    is or is not wide enough for both.
    """
    from typehaus.resolve.mep_queries import clear_bay_width_m, joist_line_stations
    from typehaus.resolve.mep_soffit import ducts_are_joined, segment_band

    cid = "mep.duct_joist_bay_occupancy"
    floors = {floor.tag: floor for floor in ctx.model.floors}
    by_floor: dict[str, list] = {}
    for duct in ctx.model.ducts:
        if duct.routing != "joist_bay" or duct.floor_ref not in floors:
            continue
        by_floor.setdefault(duct.floor_ref, []).append(duct)

    out: list[Finding] = []
    for floor_tag in sorted(by_floor):
        runs = by_floor[floor_tag]
        if len(runs) < 2:
            continue  # one run in a cavity competes with nothing
        floor = floors[floor_tag]
        clear_m = clear_bay_width_m(floor)
        lines = joist_line_stations(floor)
        occupants = _bay_occupants(runs, segment_band)
        overlaps: list[tuple[bool, str]] = []
        for index, first in enumerate(occupants):
            for second in occupants[index + 1:]:
                found = _bay_pair_overlap(ctx, floor, lines, clear_m, first, second,
                                          ducts_are_joined)
                if found is not None:
                    overlaps.append(found)
        too_wide = sorted({text for fits, text in overlaps if not fits})
        drawn_over = sorted({text for fits, text in overlaps if fits})
        if too_wide:
            out.append(_fail(cid, f"floor {floor_tag}: " + "; ".join(too_wide), (floor_tag,)))
        elif drawn_over:
            out.append(_unknown(
                cid, f"floor {floor_tag}: " + "; ".join(drawn_over)
                     + f" — the bay's {clear_m / M_PER_IN:.1f}\" clear width holds them "
                       "both, but this model gives each run one centreline per bay, so it "
                       "cannot place two lanes side by side and cannot confirm they were",
                (floor_tag,)))
        else:
            out.append(_pass(
                cid, f"floor {floor_tag} carries {len(runs)} JOIST_BAY runs and no two "
                     "parallel legs occupy one bay at one station", (floor_tag,)))
    if not out:
        # Earned, not assumed: every JOIST_BAY run in this model was counted, and no floor
        # holds two of them. There is no pair to grade.
        out.append(not_applicable(
            cid, "no floor carries two or more JOIST_BAY duct runs, so no two runs can "
                 "share a bay", ()))
    return out


def _bay_occupants(runs, segment_band) -> list[tuple[str, str, float, tuple[float, float],
                                                     tuple[float, float],
                                                     tuple[float, float]]]:
    """``(tag, travel axis, width, x band, y band, z band)`` for every horizontal bay leg.

    Vertical and oblique legs are dropped rather than squared off: a riser's neighbours are a
    different question, and an oblique leg's bounding box claims bay it never enters.
    """
    occupants = []
    for duct in runs:
        if not duct.z_m or len(duct.z_m) != len(duct.path):
            continue
        for index in range(len(duct.path) - 1):
            a, b = duct.path[index], duct.path[index + 1]
            dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
            if (dx > 1e-9 and dy > 1e-9) or (dx <= 1e-9 and dy <= 1e-9):
                continue  # oblique, or a riser
            band = segment_band(a, b, duct.width_m, duct.depth_m)
            if band is None:
                continue
            mid = (duct.z_m[index] + duct.z_m[index + 1]) / 2.0
            occupants.append((duct.tag, "x" if dy <= 1e-9 else "y", duct.width_m,
                              band[0], band[1],
                              (mid - duct.depth_m / 2.0, mid + duct.depth_m / 2.0)))
    return occupants


def _bay_pair_overlap(ctx, floor, lines, clear_m, first, second, joined
                      ) -> tuple[bool, str] | None:
    """``(the bay holds both, message)`` for two parallel legs sharing one bay, else None."""
    tag, axis, width, x_band, y_band, z_band = first
    other_tag, other_axis, other_width, other_x, other_y, other_z = second
    if tag == other_tag or axis != other_axis:
        return None
    along, across = ((x_band, y_band) if axis == "x" else (y_band, x_band))
    other_along, other_across = ((other_x, other_y) if axis == "x" else (other_y, other_x))
    shared = min(along[1], other_along[1]) - max(along[0], other_along[0])
    if shared <= 1e-9:
        return None
    if (min(z_band[1], other_z[1]) - max(z_band[0], other_z[0])) <= 1e-9:
        return None  # stacked in the bay's depth, not side by side in it
    lap = min(across[1], other_across[1]) - max(across[0], other_across[0])
    if lap <= 1e-9:
        return None  # side by side in the bay, which is what a bay is for
    # A joist can only stand between them when the separation axis IS the across-joist axis.
    # Two legs separated ALONG the joists have no member between them by definition.
    if axis == floor.direction and any(
            min(across[1], other_across[1]) - 1e-9 <= line
            <= max(across[0], other_across[0]) + 1e-9 for line in lines):
        return None
    if joined(ctx.model, tag, other_tag):
        return None
    together = width + other_width
    fits = clear_m is not None and together <= clear_m + 1e-9
    return (fits, f"ducts {tag} and {other_tag} run through one {floor.tag} bay for "
                  f"{shared / M_PER_IN:.1f}\", overlapping by "
                  f"{lap / M_PER_IN:.2f}\" across it; {together / M_PER_IN:.1f}\" of duct "
                  f"in a {(clear_m or 0.0) / M_PER_IN:.1f}\" clear bay")


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
