"""R303 light and ventilation, R303.3 local exhaust, N1103.6 whole-house ventilation.

Three rules a plan reviewer asks about on every set and none of which were encoded. The
closest thing that existed was ``advisory.habitable_window``, which reports natural light as
a suggestion — the same requirement, non-gating, and without the openable-area half.
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.checks.code.mn_residential._common import (
    HABITABLE_OCCUPANCIES,
    SF_PER_M2,
    _fail,
    _pass,
    _room_windows,
    _unknown,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import DuctSystem, EquipmentKind, Occupancy

# R303.1: aggregate glazing >= 8% of the floor area, openable >= 4%.
_MIN_GLAZING_FRACTION = 0.08
_MIN_OPENABLE_FRACTION = 0.04
# R303.3 / M1507.3: a bathroom without an operable window needs mechanical exhaust at 50 cfm
# intermittent or 20 cfm continuous.
_MIN_BATH_EXHAUST_INTERMITTENT_CFM = 50.0
_MIN_BATH_EXHAUST_CONTINUOUS_CFM = 20.0
# R303.3's window alternative: 3 sf glazed, half of it openable.
_MIN_BATH_WINDOW_SF = 3.0
_MIN_BATH_OPENABLE_SF = 1.5
# ASHRAE 62.2 / N1103.6: 0.03 cfm per ft2 of floor area plus 7.5 cfm per bedroom + 1.
_VENT_CFM_PER_FT2 = 0.03
_VENT_CFM_PER_OCCUPANT = 7.5

_SF_PER_M2 = SF_PER_M2

# R303.1 binds *habitable* rooms — R202's list, which lives in `_common` because R305.1 and
# R304 take the same subject and three copies of one sentence drift. Bathrooms, halls,
# storage, utility and mechanical space are explicitly outside it, which is why a windowless
# mechanical room is not a violation and a windowless bedroom is.
_HABITABLE = HABITABLE_OCCUPANCIES

# R303.1 Exception 1 — the way a below-grade room or an interior room is legally lit and
# ventilated at all. The glazing is not required where BOTH halves are replaced:
#
#   * artificial light "capable of producing an average illumination of 6 footcandles over
#     the area of the room at a height of 30 inches above the floor", and
#   * a whole-house mechanical ventilation system supplying outdoor air to the room.
#
# Both halves are read off what the plan already states, and neither is assumed. The
# footcandle number is an estimate and says so in the message: lamp lumens are a product
# fact, but what reaches the work plane depends on the room's surfaces, so the two planning
# factors below are applied and named rather than hidden. They are ordinary residential
# values (a light-coloured room with recessed cans); a room that only clears 6 fc by
# rounding is a room to light better, not a number to argue with.
_EXCEPTION_MIN_FOOTCANDLES = 6.0
_COEFFICIENT_OF_UTILIZATION = 0.60
_LIGHT_LOSS_FACTOR = 0.80


def _openable(ctx: CheckContext, opening) -> bool | None:
    """Is this window operable? ``None`` when its type cannot be resolved."""
    window_type = next((t for t in ctx.plan.library.window_types
                        if t.tag == opening.type_ref), None)
    if window_type is None:
        return None
    operation = getattr(window_type, "operation", None)
    if operation is None:
        return None
    return getattr(operation, "value", operation) != "fixed"


def _room_lumens(ctx: CheckContext, room) -> tuple[float | None, list[str]]:
    """Installed lamp lumens in this room, and the fixtures that state none.

    Point luminaires only. A ``LightRun``'s type carries lumens *per foot* and the strip's
    length is authored geometry rather than a fixture count, so a cove is left out of the
    total — it can only add light, which makes the number conservative in the direction that
    matters. Rooms whose light comes only from coves therefore read as unlit here, and that
    is the honest answer for a code minimum measured at the work plane.
    """
    from typehaus.model.enums import DeviceKind

    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    total = 0.0
    unrated: list[str] = []
    found = False
    for element in ctx.plan.all_elements():
        if element.element_kind != "ElectricalDevice":
            continue
        if getattr(element, "kind", None) is not DeviceKind.LIGHT:
            continue
        if getattr(element, "room", None) != room.tag:
            continue
        found = True
        lumens = getattr(types.get(element.type_ref), "lumens", None)
        if lumens is None:
            unrated.append(element.tag)
        else:
            total += float(lumens)
    return (total if found else None), sorted(unrated)


def _has_fresh_air_supply(ctx: CheckContext, room) -> bool:
    """Does a mechanical fresh-air supply terminal land in this room?"""
    return any(element.element_kind == "Register"
               and element.kind is DuctSystem.SUPPLY
               and getattr(element, "room", None) == room.tag
               for element in ctx.plan.all_elements())


def _whole_house_ventilation_rate(ctx: CheckContext) -> tuple[float, float] | None:
    """(provided, required) whole-house cfm, or None when either side is unstated."""
    area_ft2 = sum(r.area_m2 for r in ctx.model.rooms if r.conditioned) * _SF_PER_M2
    if area_ft2 <= 1e-6:
        return None
    bedrooms = sum(1 for r in ctx.model.rooms if r.occupancy == Occupancy.BEDROOM.value)
    required = area_ft2 * _VENT_CFM_PER_FT2 + _VENT_CFM_PER_OCCUPANT * (bedrooms + 1)
    provided = 0.0
    for unit in (e for e in ctx.plan.all_elements()
                 if e.element_kind == "Equipment" and e.kind is EquipmentKind.ERV):
        unit_type = next((t for t in ctx.plan.library.equipment_types
                          if t.tag == unit.type_ref), None)
        cfm = getattr(unit_type, "ventilation_cfm", None) if unit_type else None
        if cfm is None:
            return None
        provided += cfm
    return (provided, required)


def _exception_1(ctx: CheckContext, room, area_sf: float):
    """Adjudicate R303.1 Exception 1 for a room short of glazing.

    Returns ``(verdict, message)`` where verdict is "pass", "fail" or "unknown". Both halves
    have to land: 6 fc of artificial light *and* mechanical outdoor air to this room from a
    whole-house system that meets its own rate. Missing inputs are UNKNOWN — an unlit room
    and a room whose fixtures forgot to state their lumens are not the same finding.
    """
    lumens, unrated = _room_lumens(ctx, room)
    if lumens is None:
        return "fail", "no luminaire is assigned to it, so R303.1 Exception 1 is not available"
    if unrated:
        return "unknown", (f"R303.1 Exception 1 would apply, but {', '.join(unrated)} state "
                           "no lumens on their type, so the 6 fc average cannot be totalled")
    if not _has_fresh_air_supply(ctx, room):
        return "fail", ("it has no mechanical fresh-air supply register, so R303.1 "
                        "Exception 1 is not available")
    rate = _whole_house_ventilation_rate(ctx)
    if rate is None:
        return "unknown", ("R303.1 Exception 1 would apply, but the whole-house ventilation "
                           "rate is not stated, so its outdoor-air half cannot be decided")
    provided, required = rate
    if provided + 1e-6 < required:
        return "fail", (f"the whole-house ventilation system is short ({provided:.0f} cfm vs "
                        f"{required:.0f} cfm), so R303.1 Exception 1 does not carry it")
    delivered = (lumens * _COEFFICIENT_OF_UTILIZATION * _LIGHT_LOSS_FACTOR / area_sf
                 if area_sf > 1e-9 else 0.0)
    numbers = (f"{lumens:.0f} lm at CU {_COEFFICIENT_OF_UTILIZATION:.2f} x LLF "
               f"{_LIGHT_LOSS_FACTOR:.2f} over {area_sf:.0f} sf = {delivered:.1f} fc, "
               f"and {provided:.0f} cfm of whole-house outdoor air reaches it")
    if delivered + 1e-6 < _EXCEPTION_MIN_FOOTCANDLES:
        return "fail", (f"R303.1 Exception 1 does not carry it either: {numbers}, short of "
                        f"the {_EXCEPTION_MIN_FOOTCANDLES:.0f} fc the exception requires")
    return "pass", f"lit and ventilated under R303.1 Exception 1 — {numbers}"


@check(Tier.CODE, "code.R303_1_light_and_ventilation")
def habitable_light_and_ventilation(ctx: CheckContext) -> list[Finding]:
    """R303.1 — habitable rooms need glazing at 8% of floor area and openable at 4%.

    Both halves, because they fail independently: a wall of fixed glass satisfies the light
    requirement and none of the ventilation one, and that is the ordinary way a modern
    elevation gets written up. The openable area is the *window* area of operable units,
    which for a casement is the whole leaf and for a double-hung is half — this counts
    operable units at half throughout, the conservative reading, and says so in the message
    so the number is arguable rather than mysterious.

    A room that misses either half then gets Exception 1 (``_exception_1``), which is what
    makes a below-grade media room or an interior study legal rather than a violation. The
    exception is adjudicated, never assumed: it takes installed lumens and an authored
    fresh-air terminal, and reports UNKNOWN where those inputs are missing.
    """
    cid, code = "code.R303_1_light_and_ventilation", "R303.1"
    out: list[Finding] = []
    for room in ctx.model.rooms:
        if room.occupancy not in {o.value for o in _HABITABLE}:
            continue
        if room.area_m2 <= 1e-9:
            out.append(_unknown(cid, f"{room.tag} resolved no floor area", (room.tag,), code))
            continue
        # Read off the model, not re-derived here. ``resolve.rooms`` totals
        # both areas once and every consumer sees the same numbers — which is what lets the
        # server put a glazing table in front of a reader instead of scraping it back out of
        # these messages. ``None`` means a window type did not resolve, which is the same
        # UNKNOWN this check has always reported and is NOT the same fact as no glazing.
        area_sf = room.area_m2 * _SF_PER_M2
        if room.glazed_area_m2 is None or room.operable_glazed_area_m2 is None:
            out.append(_unknown(cid, f"{room.tag} has a window whose type does not resolve, "
                                "so openable area cannot be totalled", (room.tag,), code))
            continue
        glazed_sf = room.glazed_area_m2 * _SF_PER_M2
        # The halving is R303.1's, not the model's: an operable unit is credited at half its
        # area. ``resolve`` stores the whole area of the operable glass and leaves the code
        # rule here, where it can be cited.
        openable_sf = room.operable_glazed_area_m2 * _SF_PER_M2 / 2.0
        need_glazed = area_sf * _MIN_GLAZING_FRACTION
        need_openable = area_sf * _MIN_OPENABLE_FRACTION
        if glazed_sf + 1e-6 < need_glazed or openable_sf + 1e-6 < need_openable:
            if glazed_sf + 1e-6 < need_glazed:
                short = (f"{room.tag} has {glazed_sf:.1f} sf glazing for a {area_sf:.0f} sf "
                         f"floor; R303.1 requires {need_glazed:.1f} sf (8%)")
            else:
                short = (f"{room.tag} has {openable_sf:.1f} sf openable (operable units "
                         f"counted at half) for a {area_sf:.0f} sf floor; R303.1 requires "
                         f"{need_openable:.1f} sf (4%)")
            verdict, why = _exception_1(ctx, room, area_sf)
            if verdict == "pass":
                out.append(_pass(cid, f"{room.tag} is short of glazing ({glazed_sf:.1f} sf "
                                 f"of {need_glazed:.1f} sf) and is {why}", code))
            elif verdict == "unknown":
                out.append(_unknown(cid, f"{short} — {why}", (room.tag,), code))
            else:
                out.append(_fail(cid, f"{short}, and {why}", (room.tag,), code))
        else:
            out.append(_pass(cid, f"{room.tag}: {glazed_sf:.1f} sf glazing / "
                             f"{openable_sf:.1f} sf openable on {area_sf:.0f} sf floor",
                             code))
    return out


@check(Tier.CODE, "code.R303_3_local_exhaust")
def bathroom_exhaust(ctx: CheckContext) -> list[Finding]:
    """R303.3 / M1507.3 — a bathroom needs an operable window or mechanical exhaust.

    The rate is read off the terminal, never assumed from the presence of a fan: a grille
    that states no ``design_cfm`` is UNKNOWN, not a pass. The *grille's* number is what
    counts, and its run's is only a fallback for a dedicated single-terminal branch — a
    trunk with seven pickups carries seven rooms' air, so reading its total as one
    bathroom's exhaust would overstate that room several times over.

    The kitchen half of R303.3 is scope-passed where no kitchen-occupancy room resolves: an
    open-plan kitchen inside a living room is a modeling choice, not a missing exhaust fan,
    and failing it would be failing the room tagging.
    """
    cid, code = "code.R303_3_local_exhaust", "R303.3"
    baths = [room for room in ctx.model.rooms
             if room.occupancy == Occupancy.BATHROOM.value]
    if not baths:
        return [_unknown(cid, "no bathroom-occupancy rooms resolved", (), code)]
    ducts = {duct.tag: duct for duct in ctx.plan.all_elements()
             if duct.element_kind == "DuctRun"}
    registers = [r for r in ctx.plan.all_elements() if r.element_kind == "Register"]
    out: list[Finding] = []
    for bath in baths:
        windows = _room_windows(ctx, bath, Point, Polygon)
        operable = [w for w in windows if _openable(ctx, w)]
        glazed_sf = sum(w.width_m * w.height_m for w in windows) * _SF_PER_M2
        openable_sf = sum(w.width_m * w.height_m for w in operable) * _SF_PER_M2 / 2.0
        if glazed_sf >= _MIN_BATH_WINDOW_SF and openable_sf >= _MIN_BATH_OPENABLE_SF:
            out.append(_pass(cid, f"{bath.tag} is ventilated by operable window "
                             f"({openable_sf:.1f} sf openable >= 1.5 sf)", code))
            continue
        terminals = [r for r in registers
                     if r.room == bath.tag and r.kind is DuctSystem.EXHAUST]
        if not terminals:
            out.append(_fail(cid, f"{bath.tag} has neither an operable window ("
                             f"{openable_sf:.1f} sf openable) nor an exhaust register; "
                             "R303.3 requires one", (bath.tag,), code))
            continue
        rates = []
        for terminal in terminals:
            rate = terminal.design_cfm
            if rate is None:
                # Fallback, and only where it means anything: a run that terminates in this
                # one grille and nothing else. Its whole airflow does leave through it.
                duct = ducts.get(terminal.duct_ref) if terminal.duct_ref else None
                sole = duct is not None and sum(
                    1 for r in registers if r.duct_ref == duct.tag) == 1
                rate = duct.design_cfm if sole else None
            rates.append(rate)
        if any(rate is None for rate in rates):
            # ``rates`` gets exactly one append per terminal in the loop above.
            unrated = [t.tag for t, rate in zip(terminals, rates, strict=True) if rate is None]
            out.append(_unknown(cid, f"{bath.tag} exhausts through {', '.join(sorted(unrated))} "
                                "but neither the grille nor a run dedicated to it states a "
                                "design_cfm, so the 50/20 cfm rate cannot be evaluated",
                                (bath.tag, *sorted(unrated)), code))
            continue
        total = sum(rates)
        if total + 1e-6 < _MIN_BATH_EXHAUST_CONTINUOUS_CFM:
            out.append(_fail(cid, f"{bath.tag} exhausts {total:.0f} cfm; R303.3 requires "
                             "50 cfm intermittent or 20 cfm continuous",
                             (bath.tag,), code))
        elif total + 1e-6 < _MIN_BATH_EXHAUST_INTERMITTENT_CFM:
            out.append(_pass(cid, f"{bath.tag} exhausts {total:.0f} cfm — meets the 20 cfm "
                             "continuous rate; intermittent operation would need 50 cfm",
                             code))
        else:
            out.append(_pass(cid, f"{bath.tag} exhausts {total:.0f} cfm (>= 50 cfm)", code))
    return out


@check(Tier.CODE, "code.N1103_6_whole_house_ventilation")
def whole_house_ventilation(ctx: CheckContext) -> list[Finding]:
    """N1103.6 / ASHRAE 62.2 — the dwelling needs a whole-house ventilation rate.

    ``0.03 cfm/ft2 of conditioned floor area + 7.5 cfm x (bedrooms + 1)``, against the
    ventilation capacity the ERV/HRV equipment types state. Conditioned area comes from the
    resolved rooms' ``conditioned`` flag, so the garage and the sunken garden are outside
    it, as they must be for every area-derived number in this engine.
    """
    cid, code = "code.N1103_6_whole_house_ventilation", "N1103.6"
    area_ft2 = sum(room.area_m2 for room in ctx.model.rooms if room.conditioned) * _SF_PER_M2
    if area_ft2 <= 1e-6:
        return [_unknown(cid, "no conditioned floor area resolved", (), code)]
    bedrooms = sum(1 for room in ctx.model.rooms
                   if room.occupancy == Occupancy.BEDROOM.value)
    required = area_ft2 * _VENT_CFM_PER_FT2 + _VENT_CFM_PER_OCCUPANT * (bedrooms + 1)

    units = [e for e in ctx.plan.all_elements()
             if e.element_kind == "Equipment" and e.kind is EquipmentKind.ERV]
    if not units:
        return [_unknown(cid, f"no ERV/HRV equipment modeled; {required:.0f} cfm of "
                         "whole-house ventilation is required and nothing states a "
                         "capacity", (), code)]
    provided = 0.0
    unrated = []
    for unit in units:
        unit_type = next((t for t in ctx.plan.library.equipment_types
                          if t.tag == unit.type_ref), None)
        cfm = getattr(unit_type, "ventilation_cfm", None) if unit_type else None
        if cfm is None:
            unrated.append(unit.tag)
        else:
            provided += cfm
    if unrated:
        return [_unknown(cid, f"ventilation unit(s) {', '.join(sorted(unrated))} state no "
                         "ventilation_cfm on their type", tuple(sorted(unrated)), code)]
    detail = (f"{provided:.0f} cfm provided vs {required:.0f} cfm required "
              f"({area_ft2:.0f} sf conditioned, {bedrooms} bedroom(s))")
    if provided + 1e-6 < required:
        return [_fail(cid, f"whole-house ventilation short: {detail}",
                      tuple(sorted(unit.tag for unit in units)), code)]
    return [_pass(cid, f"whole-house ventilation ok: {detail}", code)]
