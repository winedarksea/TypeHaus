"""R303 light and ventilation, R303.3 local exhaust, MN 1322 R403.5 whole-house ventilation.

Three rules a plan reviewer asks about on every set and none of which were encoded. The
closest thing that existed was ``advisory.habitable_window``, which reports natural light as
a suggestion — the same requirement, non-gating, and without the openable-area half.
"""

from __future__ import annotations

from dataclasses import dataclass

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
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedModel

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
# MN Rules 1322 R403.5 — Minnesota's own whole-house rate, which is NOT ASHRAE 62.2's and
# is not the IRC's N1103.6 either. Total ventilation rate:
#
#     TVR = 0.02 cfm/ft2 x conditioned floor area + 15 cfm x (bedrooms + 1)
#
# and the *continuous* portion must be at least half of that, and never below 40 cfm. The
# two are separate requirements: a system may run the balance intermittently, but it may not
# run the whole rate intermittently.
_VENT_CFM_PER_FT2 = 0.02
_VENT_CFM_PER_OCCUPANT = 15.0
_CONTINUOUS_FRACTION_OF_TOTAL = 0.5
_MIN_CONTINUOUS_CFM = 40.0
_WHOLE_HOUSE_REF = "MN 1322 R403.5"

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


def _r303_floor_area(room) -> tuple[float, str | None]:
    """``(the sf R303.1 divides by, a phrase naming the reduction)`` for one room.

    ** R304.3 REACHES R303.1, AND THAT IS A READING — SAY SO WHEREVER IT BITES. ** R303.1
    asks for glazing at 8% "of the floor area of such rooms" and Exception 1 for 6 fc "over
    the area of the room", and neither sentence cross-references R304.3. What R304.3 says,
    under the heading *Height effect on room area*, is that floor raking below 5'-0" "shall
    not be considered as contributing to the minimum required habitable area for that room".
    Taken together this check reads one floor area per room and applies it to both halves:
    floor that does not count as habitable area is not floor area a habitability rule
    divides by, and the daylight test and its artificial-light substitute cannot sensibly
    disagree about how big the room is.

    ** IT IS ARGUABLE AND A PLAN REVIEWER MAY ARGUE IT. ** The literal scope of R304.3 is
    R304.1's 70 sf and nothing else, and on that reading catlin's RM-A-STUDIO owes 8% of
    356 sf rather than of 146 sf — the difference between a room lit under Exception 1 and a
    room that passes on daylight. So every message this reduction touches prints BOTH areas
    and the section, rather than quietly reporting the smaller one.

    ``ResolvedRoom.head_limited_area_m2`` is the model's one source for that area
    (``resolve/roof_geometry.py``), measured to the roof UNDERSIDE. Two limits worth
    knowing, both in the conservative direction here:

    * It subtracts only what a **roof** rakes down. R304.3's other half — a furred ceiling
      under 7'-0" — is not applied, so a soffited room keeps its full area.
    * ``code.R305_ceiling_height`` measures the same rake to the rafter TOP and so reports a
      LARGER qualifying area (catlin's studio: 190 sf against this 146 sf). The two are not
      reconciled and the R305 branch says so in its own docstring; this is the honest plane.

    ``None`` for the phrase means nothing was taken off and the caller's messages must stay
    byte-identical to what they were before this reduction existed.
    """
    gross_sf = room.area_m2 * _SF_PER_M2
    qualifying_m2 = getattr(room, "head_limited_area_m2", None)
    if qualifying_m2 is None:
        return gross_sf, None
    qualifying_sf = qualifying_m2 * _SF_PER_M2
    if gross_sf - qualifying_sf <= 1e-6:
        return gross_sf, None
    return qualifying_sf, (f"R304.3: {gross_sf:.0f} sf of deck less "
                           f"{gross_sf - qualifying_sf:.0f} sf raking below 5'-0\"")


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
        # ONE floor area for both halves of R303.1, and it is R304.3's, not the deck's —
        # see ``_r303_floor_area`` for the reading and for why ``basis`` is printed rather
        # than the smaller number being reported on its own.
        area_sf, basis = _r303_floor_area(room)
        if area_sf <= 1e-9:
            out.append(_unknown(cid, f"{room.tag} has no floor at or above 5'-0\" of head "
                                "(R304.3), so R303.1 has no floor area to divide by — "
                                "code.R305_ceiling_height is the finding that grades it",
                                (room.tag,), code))
            continue
        floor_phrase = f"{area_sf:.0f} sf" + (f" floor ({basis})" if basis else " floor")
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
                short = (f"{room.tag} has {glazed_sf:.1f} sf glazing for a {floor_phrase}; "
                         f"R303.1 requires {need_glazed:.1f} sf (8%)")
            else:
                short = (f"{room.tag} has {openable_sf:.1f} sf openable (operable units "
                         f"counted at half) for a {floor_phrase}; R303.1 requires "
                         f"{need_openable:.1f} sf (4%)")
            verdict, why = _exception_1(ctx, room, area_sf)
            if verdict == "pass":
                # ``short``, not a glazing sentence of its own: a room can reach here on the
                # *openable* half alone (RM-S-PLANT is 36.7 sf glazed against 12.7 required
                # and has not one operable sash), and saying it was "short of glazing" then
                # printed a false number.
                out.append(_pass(cid, f"{short}, and it is {why}", code))
            elif verdict == "unknown":
                out.append(_unknown(cid, f"{short} — {why}", (room.tag,), code))
            else:
                out.append(_fail(cid, f"{short}, and {why}", (room.tag,), code))
        else:
            out.append(_pass(cid, f"{room.tag}: {glazed_sf:.1f} sf glazing / "
                             f"{openable_sf:.1f} sf openable on {floor_phrase}",
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


@dataclass(frozen=True)
class WholeHouseVentilation:
    """MN 1322 R403.5's two rates and what the plan actually provides.

    One function, two consumers: this is what the check grades and what G-005's ventilation
    worksheet prints, so the sheet cannot state a required rate the finding disagrees with.

    ``provided_cfm`` is ``None`` when the plan states no rate at all — either no ERV/HRV is
    modelled, or one is and its type carries no ``ventilation_cfm``. ``reason`` says which,
    because "nothing installed" and "installed, unrated" are different gaps and only the
    second is a datasheet away from an answer.
    """

    conditioned_area_ft2: float
    bedrooms: int
    total_rate_cfm: float  # TVR
    continuous_rate_cfm: float  # CVR — at least half of TVR, never under 40 cfm
    provided_cfm: float | None
    unit_tags: tuple[str, ...]
    unrated_tags: tuple[str, ...]
    reason: str | None = None


def whole_house_summary(model: ResolvedModel,
                        plan: PlanModel) -> WholeHouseVentilation | None:
    """Derive R403.5's TVR and CVR and the rate the modelled equipment provides.

    ``None`` when no conditioned floor area resolves — with no area there is no requirement
    to state, which is a different answer from a requirement nothing meets. Conditioned area
    comes from the resolved rooms' ``conditioned`` flag, so the garage and the sunken garden
    are outside it, as they must be for every area-derived number in this engine.
    """
    area_ft2 = sum(room.area_m2 for room in model.rooms if room.conditioned) * _SF_PER_M2
    if area_ft2 <= 1e-6:
        return None
    bedrooms = sum(1 for room in model.rooms if room.occupancy == Occupancy.BEDROOM.value)
    total = area_ft2 * _VENT_CFM_PER_FT2 + _VENT_CFM_PER_OCCUPANT * (bedrooms + 1)
    continuous = max(total * _CONTINUOUS_FRACTION_OF_TOTAL, _MIN_CONTINUOUS_CFM)

    units = [e for e in plan.all_elements()
             if e.element_kind == "Equipment" and e.kind is EquipmentKind.ERV]
    unit_tags = tuple(sorted(unit.tag for unit in units))
    if not units:
        return WholeHouseVentilation(
            conditioned_area_ft2=area_ft2, bedrooms=bedrooms, total_rate_cfm=total,
            continuous_rate_cfm=continuous, provided_cfm=None, unit_tags=(),
            unrated_tags=(), reason="no ERV/HRV equipment modeled")
    provided = 0.0
    unrated: list[str] = []
    for unit in units:
        unit_type = next((t for t in plan.library.equipment_types
                          if t.tag == unit.type_ref), None)
        cfm = getattr(unit_type, "ventilation_cfm", None) if unit_type else None
        if cfm is None:
            unrated.append(unit.tag)
        else:
            provided += cfm
    if unrated:
        return WholeHouseVentilation(
            conditioned_area_ft2=area_ft2, bedrooms=bedrooms, total_rate_cfm=total,
            continuous_rate_cfm=continuous, provided_cfm=None, unit_tags=unit_tags,
            unrated_tags=tuple(sorted(unrated)),
            reason=(f"ventilation unit(s) {', '.join(sorted(unrated))} state no "
                    "ventilation_cfm on their type"))
    return WholeHouseVentilation(
        conditioned_area_ft2=area_ft2, bedrooms=bedrooms, total_rate_cfm=total,
        continuous_rate_cfm=continuous, provided_cfm=provided, unit_tags=unit_tags,
        unrated_tags=())


@check(Tier.CODE, "code.N1103_6_whole_house_ventilation")
def whole_house_ventilation(ctx: CheckContext) -> list[Finding]:
    """MN Rules 1322 R403.5 — the dwelling needs a whole-house ventilation rate.

    ``0.02 cfm/ft2 of conditioned floor area + 15 cfm x (bedrooms + 1)``, with at least half
    of it (and never less than 40 cfm) delivered continuously, against the rate the ERV/HRV
    equipment types state. ``EquipmentType.ventilation_cfm`` IS a continuous balanced flow,
    so a unit that meets the total rate meets the continuous one by construction; the
    continuous figure is carried and printed because the certificate posted at the panel
    has a line for it. The check id keeps its N1103.6 spelling — it is an identifier
    houses suppress by name — but the citation is Minnesota's own rule, which is what
    actually governs here and is not the same arithmetic as ASHRAE 62.2's.
    """
    cid, code = "code.N1103_6_whole_house_ventilation", _WHOLE_HOUSE_REF
    summary = whole_house_summary(ctx.model, ctx.plan)
    if summary is None:
        return [_unknown(cid, "no conditioned floor area resolved", (), code)]
    rates = (f"{summary.total_rate_cfm:.0f} cfm total / "
             f"{summary.continuous_rate_cfm:.0f} cfm continuous")
    if summary.provided_cfm is None:
        return [_unknown(cid, f"{summary.reason}; R403.5 requires {rates} "
                         f"({summary.conditioned_area_ft2:.0f} sf conditioned, "
                         f"{summary.bedrooms} bedroom(s))",
                         summary.unrated_tags, code)]
    detail = (f"{summary.provided_cfm:.0f} cfm provided vs {rates} required "
              f"({summary.conditioned_area_ft2:.0f} sf conditioned, "
              f"{summary.bedrooms} bedroom(s))")
    if summary.provided_cfm + 1e-6 < summary.total_rate_cfm:
        return [_fail(cid, f"whole-house ventilation short: {detail}",
                      summary.unit_tags, code)]
    return [_pass(cid, f"whole-house ventilation ok: {detail}", code)]
