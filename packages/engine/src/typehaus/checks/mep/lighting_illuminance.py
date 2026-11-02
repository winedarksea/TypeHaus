"""``advisory.room_illuminance`` — average lux by the lumen method, against a house target.

A preference, not code: no residential code sets a lux level for a workshop or a garage.
The one code number for artificial light is R303.1 Exception 1's 6 fc, graded in
``code.R303_1_light_and_ventilation``; this reuses its planning factors (CU x LLF) so the
two estimates cannot disagree about a room's surfaces. Never FAIL — a short room is ADVISORY.

Unlike R303.1, ``LightRun`` tape counts (its type's ``lumens`` are per foot), because a
target for a work room is about all the light in it. A fan whose type has no lamp is not a
luminaire here, rather than an unrated one.

A kitchen in an open plan is not graded by default: the lumen method averages over the
whole ROOM, and the great room's average says nothing about the counter. A ``KITCHEN`` room
is graded; a house that wants the great room graded names it in ``[mep.illuminance_lux]``.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.code.mn_residential.ventilation import (
    COEFFICIENT_OF_UTILIZATION,
    LIGHT_LOSS_FACTOR,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.electrical import luminaire_types
from typehaus.model.enums import DeviceKind, LuminaireForm, Occupancy

#: Default average-lux targets by room use (IES residential task ranges, rounded). A house
#: overrides or adds per occupancy or per room tag in ``[mep.illuminance_lux]``.
DEFAULT_TARGET_LUX: dict[Occupancy, float] = {
    Occupancy.UTILITY: 500.0,  # the workshop
    Occupancy.KITCHEN: 300.0,
    Occupancy.OFFICE: 300.0,
    Occupancy.STUDY_CLOSET: 300.0,
    Occupancy.MECHANICAL: 200.0,
    Occupancy.GARAGE: 200.0,
}
_M_PER_FT = 0.3048
_SF_PER_M2 = 10.7639


def target_lux(room, overrides: dict) -> float | None:
    """The room's target: its tag's override, its occupancy's, then the default."""
    for key in (room.tag, room.occupancy):
        if key in overrides:
            return float(overrides[key]) or None
    try:
        return DEFAULT_TARGET_LUX.get(Occupancy(room.occupancy))
    except ValueError:
        return None


def room_lumens(ctx: CheckContext) -> tuple[dict[str, float], dict[str, float],
                                            dict[str, list[str]]]:
    """``(point lm, tape lm, unrated tags)`` per room tag, by each load's authored ``room``."""
    types = luminaire_types(ctx.plan.library)
    point: dict[str, float] = {}
    tape: dict[str, float] = {}
    unrated: dict[str, list[str]] = {}
    for element in ctx.plan.all_elements():
        if element.element_kind != "ElectricalDevice" or element.kind is not DeviceKind.LIGHT:
            continue
        room = getattr(element, "room", None)
        if room is None:
            continue
        product = types.get(element.type_ref or "")
        if (product is not None and product.form is LuminaireForm.CEILING_FAN_LIGHT
                and product.lamp is None and product.lumens is None):
            continue  # a fan with no light kit
        point.setdefault(room, 0.0)
        if product is None or product.lumens is None:
            unrated.setdefault(room, []).append(element.tag)
        else:
            point[room] += float(product.lumens)
    for run in ctx.model.light_runs:
        if run.room is None:
            continue
        product = types.get(run.type_ref)
        tape.setdefault(run.room, 0.0)
        if product is None or product.lumens is None:
            unrated.setdefault(run.room, []).append(run.tag)
        else:
            tape[run.room] += float(product.lumens) * run.length_m / _M_PER_FT
    return point, tape, unrated


@check(Tier.ADVISORY, "advisory.room_illuminance")
def room_illuminance(ctx: CheckContext) -> list[Finding]:
    """Each room with a target averages at least that many lux on the lumen method."""
    cid = "advisory.room_illuminance"
    if not ctx.model.rooms:
        return [_unknown(cid, "no rooms modeled")]
    overrides = ctx.preferences.mep.illuminance_lux
    point, tape, unrated = room_lumens(ctx)
    factor = COEFFICIENT_OF_UTILIZATION * LIGHT_LOSS_FACTOR
    out: list[Finding] = []
    for room in ctx.model.rooms:
        target = target_lux(room, overrides)
        if target is None:
            continue
        if room.area_m2 <= 1e-9:
            out.append(_unknown(cid, f"{room.tag} resolved no floor area", (room.tag,)))
            continue
        lumens = point.get(room.tag, 0.0) + tape.get(room.tag, 0.0)
        lux = lumens * factor / room.area_m2
        numbers = (f"{lumens:,.0f} lm" + (f" ({tape[room.tag]:,.0f} of it tape)"
                                          if tape.get(room.tag) else "")
                   + f" at CU {COEFFICIENT_OF_UTILIZATION:.2f} x LLF {LIGHT_LOSS_FACTOR:.2f}"
                   f" over {room.area_m2 * _SF_PER_M2:.0f} sf = {lux:.0f} lx average")
        missing = sorted(unrated.get(room.tag, ()))
        if lux + 1e-6 >= target:
            out.append(_pass(cid, f"{room.tag} meets its {target:.0f} lx target: {numbers}",
                             (room.tag,)))
        elif missing:
            out.append(_unknown(cid, f"{room.tag} reads {lux:.0f} lx of a {target:.0f} lx "
                                     f"target, but {', '.join(missing)} state no lumens",
                                (room.tag,)))
        else:
            out.append(advisory(cid, f"{room.tag} is short of its {target:.0f} lx target "
                                     f"(house preference, not code): {numbers}",
                                (room.tag,), Result.ADVISORY))
    if not out:
        return [_na(cid, "no room is of a use with an illuminance target")]
    return out
