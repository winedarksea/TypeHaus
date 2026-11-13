"""R303 light and ventilation, R303.3 local exhaust (R403.5 is in `whole_house_ventilation`).

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
from typehaus.checks.code.mn_residential.whole_house_ventilation import whole_house_summary
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import DuctSystem, Occupancy

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
_SF_PER_M2 = SF_PER_M2

# R303.1 binds *habitable* rooms — R202's list, which lives in `_common` because R305.1 and
# R304 take the same subject and three copies of one sentence drift. Bathrooms, halls,
# storage, utility and mechanical space are explicitly outside it, which is why a windowless
# mechanical room is not a violation and a windowless bedroom is.
_HABITABLE = HABITABLE_OCCUPANCIES

# R303.1's exceptions, 2018 IRC as Minnesota adopts it (Minn. R. 1309.0303 amends R303.4 only):
#
#   1. "The glazed areas need not be openable where the opening is not required by Section
#      R310 and a whole-house mechanical ventilation system is installed in accordance with
#      Section M1505."
#   2. "The glazed areas need not be installed in rooms where Exception 1 is satisfied and
#      artificial light is provided that is capable of producing an average illumination of
#      6 footcandles (65 lux) over the area of the room at a height of 30 inches (762 mm)
#      above the floor level."
#
# So a room short only of OPENABLE area needs Exception 1 alone: no R310 opening, and an
# installed whole-house system whose rate passes. Neither exception asks for a supply
# terminal in the room. A room short of GLAZING needs Exception 2: Exception 1 plus the light.
# The footcandles are an estimate (CU x LLF, named in the message), not a photometric run.
_EXCEPTION_MIN_FOOTCANDLES = 6.0
COEFFICIENT_OF_UTILIZATION = 0.60
LIGHT_LOSS_FACTOR = 0.80


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


def _r310_requires_opening(ctx: CheckContext, room) -> bool | None:
    """Does R310 require this room's opening? ``None`` when the room's escape window is the
    R310 opening and the rest of its glazing therefore is not.

    R310.1 binds every sleeping room (the basement-storey half is satisfied per storey, not
    per room, and ``code.R310_1_storey_egress`` grades it). A sleeping room with a compliant
    escape window has its R310 opening; R303.1's openable area is then the rest's business.
    """
    from typehaus.checks.code.mn_residential.egress import egress_window_rooms
    from typehaus.model.enums import SLEEPING_OCCUPANCIES

    if room.occupancy not in {o.value for o in SLEEPING_OCCUPANCIES}:
        return False
    # Operable only: ``egress_window_rooms`` sizes the frame and does not ask if it opens.
    escapes = [tag for tag, owner in egress_window_rooms(ctx).items() if owner == room.tag]
    openings = {o.tag: o for o in ctx.model.openings}
    return None if any(_openable(ctx, openings[tag]) for tag in escapes if tag in openings) \
        else True


def _exception_1(ctx: CheckContext, room):
    """R303.1 Exception 1: ``(verdict, why)`` with verdict "pass", "fail" or "unknown"."""
    r310 = _r310_requires_opening(ctx, room)
    if r310:
        return "fail", ("R310 requires its escape opening and it has no compliant one, so "
                        "R303.1 Exception 1 is not available")
    summary = whole_house_summary(ctx.model, ctx.plan, ctx)
    if summary is None or not summary.unit_tags:
        return "fail", ("no whole-house mechanical ventilation system is installed, so "
                        "R303.1 Exception 1 is not available")
    verdict = summary.verdict()
    if verdict in ("unstated", "unknown"):
        return "unknown", ("R303.1 Exception 1 would apply, but the whole-house ventilation "
                           "rate is not stated or not yet settled")
    provided, required = summary.graded_cfm, summary.total_rate_cfm
    if verdict == "fail":
        return "fail", (f"the whole-house ventilation system is short ({provided:.0f} cfm vs "
                        f"{required:.0f} cfm), so R303.1 Exception 1 does not carry it")
    escape = ("its R310 escape window is provided" if r310 is None
              else "no R310 opening is required")
    return "pass", (f"R303.1 Exception 1 applies: {escape} and the "
                    f"whole-house system is installed ({provided:.0f} cfm vs "
                    f"{required:.0f} cfm, M1505)")


def _exception_2(ctx: CheckContext, room, area_sf: float):
    """R303.1 Exception 2 — Exception 1 plus 6 fc of artificial light.

    Missing inputs are UNKNOWN: an unlit room and a room whose fixtures forgot to state
    their lumens are not the same finding.
    """
    lumens, unrated = _room_lumens(ctx, room)
    if lumens is None:
        return "fail", "no luminaire is assigned to it, so R303.1 Exception 2 is not available"
    verdict, why = _exception_1(ctx, room)
    if verdict != "pass":
        return verdict, why
    delivered = (lumens * COEFFICIENT_OF_UTILIZATION * LIGHT_LOSS_FACTOR / area_sf
                 if area_sf > 1e-9 else 0.0)
    numbers = (f"{lumens:.0f} lm at CU {COEFFICIENT_OF_UTILIZATION:.2f} x LLF "
               f"{LIGHT_LOSS_FACTOR:.2f} over {area_sf:.0f} sf = {delivered:.1f} fc")
    # An unrated fixture only adds light, so the rated total is a lower bound: it can
    # carry the exception on its own, but cannot sink it.
    if unrated:
        numbers += f" (counting only rated fixtures; {', '.join(unrated)} state no lumens)"
        if delivered + 1e-6 < _EXCEPTION_MIN_FOOTCANDLES:
            return "unknown", (f"R303.1 Exception 2 would apply, but {', '.join(unrated)} "
                               "state no lumens on their type, and the rated fixtures alone "
                               f"give {delivered:.1f} fc, short of the "
                               f"{_EXCEPTION_MIN_FOOTCANDLES:.0f} fc average")
    if delivered + 1e-6 < _EXCEPTION_MIN_FOOTCANDLES:
        return "fail", (f"R303.1 Exception 2 does not carry it: {numbers}, short of "
                        f"the {_EXCEPTION_MIN_FOOTCANDLES:.0f} fc the exception requires")
    return "pass", f"lit under R303.1 Exception 2 ({numbers}), and {why}"


@check(Tier.CODE, "code.R303_1_light_and_ventilation")
def habitable_light_and_ventilation(ctx: CheckContext) -> list[Finding]:
    """R303.1 — habitable rooms need glazing at 8% of floor area and openable at 4%.

    Both halves, because they fail independently: a wall of fixed glass satisfies the light
    requirement and none of the ventilation one, and that is the ordinary way a modern
    elevation gets written up. The openable area is the *window* area of operable units,
    which for a casement is the whole leaf and for a double-hung is half — this counts
    operable units at half throughout, the conservative reading, and says so in the message
    so the number is arguable rather than mysterious.

    A room short of openable area gets Exception 1; one short of glazing, Exception 2
    (Exception 1 plus 6 fc), which is what makes a windowless media room legal. Both are
    adjudicated, never assumed, and report UNKNOWN where their inputs are missing.
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
            # Short of glazing needs Exception 2; short only of openable area, Exception 1
            # (RM-S-PLANT: 36.7 sf glazed against 12.7 required, not one operable sash).
            verdict, why = (_exception_2(ctx, room, area_sf) if glazed_sf + 1e-6 < need_glazed
                            else _exception_1(ctx, room))
            if verdict == "pass":
                out.append(_pass(cid, f"{short}; {why}", code))
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
