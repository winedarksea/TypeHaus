"""``electrical.hvac_service_receptacle`` — 2026 NEC 210.63(A), the servicing receptacle.

Heating and air-conditioning equipment (outdoor heat pumps, ducted air handlers, indoor heads)
has a 125 V, 15/20 A receptacle at an accessible location within 25 ft, on the same level, and
not on the load side of the equipment's branch-circuit disconnect. Read here as a counting
receptacle (``_counts_as_a_125v_receptacle``, unswitched) that is:

* on the unit's storey, and on its side of the envelope: an outdoor unit (inside no room) takes
  an outdoor receptacle, an indoor one a receptacle indoors with no wall across the straight
  line between them (``_separated``);
* within 25 ft in plan of the unit's footprint (a lower bound on the real distance, so a near
  miss reads in the unit's favour);
* on another circuit. A receptacle on the unit's own circuit may sit ahead of its disconnect
  (422.12 Ex. 2 lets the 210.63(A) receptacle share that circuit) or behind it; the model has
  no wiring order, so such a unit with no other receptacle is UNKNOWN, never PASS.

"Accessible" is not graded. Left out: refrigeration equipment (a household unit is plugged in),
the ERV and the water heater (neither is 210.63(A) equipment), and 210.63(B), which is for
buildings other than dwellings. 210.63's exception for evaporative coolers does not apply.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.mep.electrical import _counts_as_a_125v_receptacle
from typehaus.checks.mep.electrical_spa_geometry import _separated, _walls
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.nec import NEC, cite
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

_CID = "electrical.hvac_service_receptacle"
HVAC_RECEPTACLE_REACH_M = 25 * 0.3048
_KINDS = frozenset({"heat_pump", "ducted_air_handler", "indoor_head"})


@check(Tier.ADVISORY, _CID)
def hvac_service_receptacle(ctx: CheckContext) -> list[Finding]:
    """Each heat pump, air handler and indoor head has a servicing receptacle within 25 ft."""
    from shapely.geometry import Point, Polygon

    code = cite(NEC.HVAC_RECEPTACLE)
    units = [e for e in ctx.plan.all_elements() if e.element_kind == "Equipment"
             and getattr(getattr(e, "kind", None), "value", None) in _KINDS]
    if not units:
        return [not_applicable(_CID, "no heating or air-conditioning equipment is authored",
                               code=code)]
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    rooms: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(axis_ring(room)) >= 3:
            rooms.setdefault(room.storey, []).append(axis_polygon(room))

    def indoors(storey: str, point) -> bool:
        return any(poly.contains(point) for poly in rooms.get(storey, ()))

    receptacles = [e for e in ctx.plan.all_elements() if e.element_kind == "ElectricalDevice"
                   and e.tag in objects and not getattr(e, "controlled_by", ())
                   and _counts_as_a_125v_receptacle(ctx, e)]
    out: list[Finding] = []
    for unit in sorted(units, key=lambda e: e.tag):
        uobj = objects.get(unit.tag)
        if uobj is None:
            out.append(unknown(_CID, f"{unit.tag} has no resolved footprint", (unit.tag,),
                               code=code))
            continue
        body = Polygon(uobj.footprint)
        inside = indoors(uobj.storey, body.representative_point())
        walls = _walls(ctx, uobj.storey)
        ok, same_circuit = [], []
        for rc in receptacles:
            robj = objects[rc.tag]
            point = Point(robj.position)
            gap = body.distance(point)
            if (robj.storey != uobj.storey or gap > HVAC_RECEPTACLE_REACH_M
                    or indoors(robj.storey, point) != inside
                    or (inside and _separated(body, point, walls))):
                continue
            (same_circuit if unit.circuit and rc.circuit == unit.circuit else ok).append(
                (gap, rc.tag))
        where = "indoors" if inside else "outdoors"
        if ok:
            gap, tag = min(ok)
            out.append(passed(_CID, f"{unit.tag}: {tag} is {gap / 0.3048:.1f} ft away {where} "
                                    "on the same level and another circuit (accessibility not "
                                    "graded)", (unit.tag, tag), code=code))
        elif same_circuit:
            gap, tag = min(same_circuit)
            out.append(unknown(
                _CID, f"{unit.tag}: the only receptacle in reach, {tag}, is on the unit's own "
                      f"circuit {unit.circuit}; whether it sits ahead of the disconnect is not "
                      "modelled", (unit.tag, tag), code=code,
                fix="put the servicing receptacle on another circuit, or say it is line side"))
        else:
            out.append(failed(
                _CID, f"{unit.tag} has no 125 V 15/20 A receptacle {where} within 25 ft on its "
                      "level (a wall between, another level, or the wrong side of the "
                      "envelope does not count)", (unit.tag,), code=code,
                fix="add a GFCI receptacle beside the unit"))
    return out
