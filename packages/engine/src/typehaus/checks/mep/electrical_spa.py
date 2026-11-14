"""2026 NEC Article 680 as it reaches a spa or hot tub: Parts I and II through 680.42/.43/.45
and Part IV (680.40-680.44), graded from the model. ``docs/nec-2026-paraphrase-680.md``.

Circuit rules (a circuit flagged ``Circuit.spa`` or named by an ``EquipmentKind.SPA``): 680.44(A)
with 680.5(B)/(C) GFCI class, and 680.41(A) (N/A in a one-family dwelling). Distance rules need
the tub's footprint (``electrical_spa_geometry``): 680.13 maintenance disconnect, 680.22 and
680.43 receptacles, switches, outlets, luminaires, 680.41(B). Without a footprint each is one
UNKNOWN naming what to author. Not graded for want of data: 680.7 and 680.14 (no conductor or
wiring-method data), 680.26 bonding, 680.44(B)/(C), 680.42(A). Pools and Part V fountains: the
model has no such element, so absence is not evidence and nothing is emitted.
"""

from __future__ import annotations

from typehaus.checks._authoring import by_result
from typehaus.checks.mep.electrical_spa_geometry import spa_geometry
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import DeviceKind, EquipmentKind
from typehaus.model.nec import NEC, cite
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

_CID = "code.NEC_680_spa"
# 680.5(B): Class A GFCI on <=150 V to ground circuits of <=60 A single-phase. A 1- or 2-pole
# circuit off this house's 120/240 V single-phase service is 120 V to ground.
_CLASS_A_MAX_AMPS = 60


def _is_indoors(ctx: CheckContext, obj) -> bool:
    from shapely.geometry import Polygon

    centre = Polygon(obj.footprint).centroid
    return any(room.storey == obj.storey and axis_polygon(room).contains(centre)
               for room in ctx.model.rooms if len(axis_ring(room)) >= 3)


def _circuit_findings(circuit) -> list[Finding]:
    code = cite(NEC.SPA_GFCI, NEC.GFCI_150V)
    if circuit.poles > 2:
        gfci = by_result(_CID, Result.UNKNOWN, f"{circuit.tag} (spa) is {circuit.poles}-pole: "
                         "its voltage to ground is not stated, so 680.5(B) vs (C) is open",
                         (circuit.tag,), code)
    elif circuit.breaker_amps > _CLASS_A_MAX_AMPS:
        gfci = by_result(_CID, Result.UNKNOWN, f"{circuit.tag} (spa) is "
                         f"{circuit.breaker_amps} A: 680.5(B) covers single-phase circuits of "
                         "60 A or less and (C) those above 150 V to ground",
                         (circuit.tag,), code)
    elif not circuit.gfci:
        gfci = by_result(_CID, Result.FAIL, f"{circuit.tag} supplies a spa with no GFCI",
                         (circuit.tag,), code, "Class A GFCI breaker, or a listed unit marked "
                         "with integral GFCI (680.44(B), which the model cannot state)")
    elif circuit.gfci_class != "A":
        gfci = by_result(_CID, Result.FAIL, f"{circuit.tag} (spa, {circuit.breaker_amps} A, "
                         "120 V to ground) has a Class C SPGFCI; 680.5(B) wants Class A",
                         (circuit.tag,), code, "Class A GFCI breaker")
    else:
        gfci = by_result(_CID, Result.PASS, f"{circuit.tag} (spa, {circuit.breaker_amps} A, "
                         f"{circuit.poles}-pole, 120 V to ground) is on a Class A GFCI breaker",
                         (circuit.tag,), code)
    wiring = by_result(
        _CID, Result.UNKNOWN,
        f"{circuit.tag} 680.7 (insulated copper EGC of at least 12 AWG, sized per 250.122, in a "
        "wet or corrosive place; cords the same, wet-rated terminals) and 680.14 (no aluminum "
        "wiring method) are ungraded: the model carries no conductor, EGC or terminal data",
        (circuit.tag,), cite(NEC.POOL_GROUNDING, NEC.POOL_CORROSIVE))
    return [gfci, wiring]


@check(Tier.CODE, _CID)
def spa_and_hot_tub(ctx: CheckContext) -> list[Finding]:
    """680.44 / 680.5 GFCI on a spa circuit; 680.41(A); the tub's distances where it is modeled."""
    spas = [e for e in ctx.plan.all_elements()
            if e.element_kind == "Equipment" and e.kind is EquipmentKind.SPA]
    named = {s.circuit for s in spas if s.circuit}
    circuits = {c.tag: c for c in ctx.plan.library.circuits if c.spa or c.tag in named}
    if not spas and not circuits:
        return []  # the model has no pool or fountain element, so silence is not N/A
    out: list[Finding] = []
    for circuit in sorted(circuits.values(), key=lambda c: c.tag):
        out += _circuit_findings(circuit)
    one_dwelling = sum(b.kind == "dwelling" for b in ctx.plan.project.buildings) == 1
    out.append(by_result(
        _CID, Result.NOT_APPLICABLE if one_dwelling else Result.UNKNOWN,
        "680.41(A) emergency switch reaches other than one-family dwellings; this plan has one "
        "dwelling building" if one_dwelling else
        "680.41(A) emergency switch: the plan does not state a one-family dwelling",
        (), cite(NEC.SPA_EMERGENCY_SWITCH)))
    types = {t.tag: t for t in ctx.plan.library.equipment_types}
    placed = {o.tag: o for o in ctx.model.canvas_objects}
    if not spas:
        disconnects = sorted(e.tag for e in ctx.plan.all_elements()
                             if e.element_kind == "ElectricalDevice"
                             and e.kind is DeviceKind.DISCONNECT and e.circuit in circuits)
        out += _unmodeled(sorted(circuits), disconnects)
    for spa in spas:
        obj = placed.get(spa.tag)
        if obj is None or len(obj.footprint or ()) < 3:
            out.append(by_result(_CID, Result.UNKNOWN, f"{spa.tag} has no resolved footprint",
                                 (spa.tag,), cite(NEC.SPA_MAINT_DISCONNECT)))
            continue
        out += spa_geometry(ctx, spa, obj, circuits, types, _is_indoors(ctx, obj))
    return out


def _unmodeled(circuits: list[str], disconnects: list[str]) -> list[Finding]:
    """One UNKNOWN per rule family while no tub footprint exists to measure from."""
    what = ", ".join(circuits)
    fix = "model the tub as an Equipment of kind SPA with its footprint and type"
    return [
        by_result(_CID, Result.UNKNOWN,
                  f"{what} supplies a spa that is not modeled, so the 680.13 maintenance "
                  f"disconnect ({', '.join(disconnects) or 'none on the circuit'}: at least 5 ft "
                  "horizontally from the water's edge, or a barrier giving a 5 ft reach, readily "
                  "accessible and within sight) cannot be measured", tuple(circuits) + tuple(
                      disconnects), cite(NEC.SPA_MAINT_DISCONNECT), fix),
        by_result(_CID, Result.UNKNOWN,
                  f"{what}: with no tub footprint, receptacle (680.22(A), 6-20 ft; indoors "
                  "680.43(A)), switch, outlet and luminaire distances, 680.41(B)/680.22(F) "
                  "equipment separation and indoor vs outdoor are ungraded", tuple(circuits),
                  cite(NEC.POOL_RECEPTACLES, NEC.SPA_EQUIPMENT_DISTANCE), fix),
        by_result(_CID, Result.UNKNOWN,
                  f"{what}: 680.26 equipotential bonding is ungraded. Author the tub type and "
                  "listing, rim height, perimeter paving, and any fixed metal within 5 ft "
                  "horizontally or 12 ft above the water; the 680.42(B) waiver of perimeter "
                  "bonding needs a listed self-contained aboveground tub on or above grade",
                  tuple(circuits), cite(NEC.POOL_EQUIPOTENTIAL, NEC.SPA_BONDING_WAIVER)),
    ]
