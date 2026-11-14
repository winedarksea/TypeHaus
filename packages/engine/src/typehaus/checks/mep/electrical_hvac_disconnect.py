"""``electrical.hvac_disconnect`` — 2026 NEC 440.14: a disconnect in sight of the A/C equipment.

Each outdoor heat-pump unit and ducted air handler on its own circuit needs a disconnecting
means within sight of it and readily accessible (it may be in the equipment). The disconnect is
the ``DeviceKind.DISCONNECT`` device on the unit's circuit. Within sight is read as a straight
plan line to the unit's footprint with no wall across it (the ``electrical_spa_geometry``
approach); the printed distance limit is Article 100's and is not read, so the gap is reported,
not graded. Not graded: readily accessible, 110.26(A) working space, panels that obscure the
nameplate. Indoor heads carry no circuit (the outdoor unit feeds them) and are skipped. A unit
with no disconnect device on its circuit is UNKNOWN: the equipment may carry one.
"""

from __future__ import annotations

from typehaus.checks._authoring import passed, unknown
from typehaus.checks.mep.electrical_spa_geometry import _separated, _walls
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import DeviceKind
from typehaus.model.nec import NEC, cite

_CID = "electrical.hvac_disconnect"
_FT = 0.3048
_KINDS = frozenset({"heat_pump", "ducted_air_handler"})


@check(Tier.ADVISORY, _CID)
def hvac_disconnect(ctx: CheckContext) -> list[Finding]:
    """Each circuit-fed heat pump or air handler has a disconnect in plan sight of it."""
    from shapely.geometry import Point, Polygon

    from typehaus.checks._authoring import not_applicable

    code = cite(NEC.HVAC_DISCONNECT)
    units = [e for e in ctx.plan.all_elements()
             if e.element_kind == "Equipment" and getattr(e, "circuit", None)
             and getattr(getattr(e, "kind", None), "value", None) in _KINDS]
    if not units:
        return [not_applicable(_CID, "no circuit-fed heat pump or air handler is authored",
                               code=code)]
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    disconnects = [e for e in ctx.plan.all_elements()
                   if e.element_kind == "ElectricalDevice" and e.kind is DeviceKind.DISCONNECT]
    out: list[Finding] = []
    for unit in sorted(units, key=lambda e: e.tag):
        obj = objects.get(unit.tag)
        mine = [d for d in disconnects if d.circuit == unit.circuit]
        if not mine or obj is None:
            out.append(unknown(
                _CID, f"{unit.tag} (circuit {unit.circuit}) has no disconnect device on its "
                      "circuit; 440.14 lets the equipment carry one, which the model cannot say",
                (unit.tag,), code=code, fix="author a DISCONNECT device on the circuit, or state "
                                            "that the unit has an integral one"))
            continue
        body = Polygon(obj.footprint)
        for disc in mine:
            other = objects.get(disc.tag)
            if other is None or other.storey != obj.storey:
                out.append(unknown(_CID, f"{disc.tag} is not on {unit.tag}'s level, so "
                                         "sight cannot be read in plan", (unit.tag, disc.tag),
                                   code=code))
                continue
            gap = body.distance(Point(other.position))
            if _separated(body, Point(other.position), _walls(ctx, obj.storey)):
                out.append(unknown(
                    _CID, f"{disc.tag} is {gap / _FT:.1f} ft from {unit.tag} with a wall "
                          "between, so within sight is not shown", (unit.tag, disc.tag),
                    code=code))
            else:
                out.append(passed(
                    _CID, f"{disc.tag} is {gap / _FT:.1f} ft from {unit.tag} in plan with no "
                          "wall between (distance limit and accessibility not graded)",
                    (unit.tag, disc.tag), code=code))
    return out
