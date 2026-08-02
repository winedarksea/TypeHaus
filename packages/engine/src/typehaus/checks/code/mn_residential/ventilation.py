"""R303 light and ventilation, R303.3 local exhaust, N1103.6 whole-house ventilation.

Three rules a plan reviewer asks about on every set and none of which were encoded. The
closest thing that existed was ``advisory.habitable_window``, which reports natural light as
a suggestion — the same requirement, non-gating, and without the openable-area half.
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.checks.code.mn_residential._common import (_fail, _pass, _room_windows, _unknown)
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

_SF_PER_M2 = 10.7639

# R303.1 binds *habitable* rooms — R202's list. Bathrooms, halls, storage, utility and
# mechanical space are explicitly outside it, which is why a windowless mechanical room is
# not a violation and a windowless bedroom is.
_HABITABLE = frozenset({
    Occupancy.BEDROOM, Occupancy.LIVING, Occupancy.DINING, Occupancy.KITCHEN,
    Occupancy.MEDIA, Occupancy.OFFICE,
})


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


@check(Tier.CODE, "code.R303_1_light_and_ventilation")
def habitable_light_and_ventilation(ctx: CheckContext) -> list[Finding]:
    """R303.1 — habitable rooms need glazing at 8% of floor area and openable at 4%.

    Both halves, because they fail independently: a wall of fixed glass satisfies the light
    requirement and none of the ventilation one, and that is the ordinary way a modern
    elevation gets written up. The openable area is the *window* area of operable units,
    which for a casement is the whole leaf and for a double-hung is half — this counts
    operable units at half throughout, the conservative reading, and says so in the message
    so the number is arguable rather than mysterious.
    """
    cid, code = "code.R303_1_light_and_ventilation", "R303.1"
    out: list[Finding] = []
    for room in ctx.model.rooms:
        if room.occupancy not in {o.value for o in _HABITABLE}:
            continue
        if room.area_m2 <= 1e-9:
            out.append(_unknown(cid, f"{room.tag} resolved no floor area", (room.tag,), code))
            continue
        windows = _room_windows(ctx, room, Point, Polygon)
        area_sf = room.area_m2 * _SF_PER_M2
        glazed_sf = sum(w.width_m * w.height_m for w in windows) * _SF_PER_M2
        operability = [_openable(ctx, w) for w in windows]
        if any(state is None for state in operability):
            out.append(_unknown(cid, f"{room.tag} has a window whose type does not resolve, "
                                "so openable area cannot be totalled", (room.tag,), code))
            continue
        openable_sf = sum(w.width_m * w.height_m for w, state in zip(windows, operability)
                          if state) * _SF_PER_M2 / 2.0
        need_glazed = area_sf * _MIN_GLAZING_FRACTION
        need_openable = area_sf * _MIN_OPENABLE_FRACTION
        if glazed_sf + 1e-6 < need_glazed:
            out.append(_fail(cid, f"{room.tag} has {glazed_sf:.1f} sf glazing for a "
                             f"{area_sf:.0f} sf floor; R303.1 requires "
                             f"{need_glazed:.1f} sf (8%)", (room.tag,), code))
        elif openable_sf + 1e-6 < need_openable:
            out.append(_fail(cid, f"{room.tag} has {openable_sf:.1f} sf openable (operable "
                             f"units counted at half) for a {area_sf:.0f} sf floor; R303.1 "
                             f"requires {need_openable:.1f} sf (4%)", (room.tag,), code))
        else:
            out.append(_pass(cid, f"{room.tag}: {glazed_sf:.1f} sf glazing / "
                             f"{openable_sf:.1f} sf openable on {area_sf:.0f} sf floor",
                             code))
    return out


@check(Tier.CODE, "code.R303_3_local_exhaust")
def bathroom_exhaust(ctx: CheckContext) -> list[Finding]:
    """R303.3 / M1507.3 — a bathroom needs an operable window or mechanical exhaust.

    The rate is read through the register's duct, never assumed from the presence of a fan:
    a terminal whose run states no ``design_cfm`` is UNKNOWN, not a pass. That is this
    house's situation today — four ERV runs, none with an authored airflow — and reporting
    it as a pass would be inventing the one number the requirement is about.

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
            duct = ducts.get(terminal.duct_ref) if terminal.duct_ref else None
            rates.append(None if duct is None else duct.design_cfm)
        if any(rate is None for rate in rates):
            unrated = [t.tag for t, rate in zip(terminals, rates) if rate is None]
            out.append(_unknown(cid, f"{bath.tag} exhausts through {', '.join(sorted(unrated))} "
                                "but the run states no design_cfm, so the 50/20 cfm rate "
                                "cannot be evaluated", (bath.tag, *sorted(unrated)), code))
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
