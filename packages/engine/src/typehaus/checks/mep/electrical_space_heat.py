"""``electrical.space_heat_circuit`` — 2026 NEC 424.4(B), 424.5 and the floor-heat GFCI rules.

Fixed electric space heating here is a ``FloorHeat`` zone (its circuit is its thermostat's) or an
``EquipmentKind.SPACE_HEATER`` on a circuit. Graded per circuit: 424.5, a continuous load, so the
breaker is at least 125% of the authored ``load_va`` (volts from the poles); 424.4(B), a circuit
for two or more heater outlets is 30 A or less; and for a heating-cable zone, GFCI (424.44(E)
bathrooms and kitchens, 424.45(E) any cable under a floor covering, 424.99(C)(5) panels), read
from ``Circuit.gfci``. 424.19: a ``DeviceKind.DISCONNECT`` on the circuit in plan sight of every
heater (no wall between, the 440.14 reading), or a breaker stated lockable open
(``Circuit.breaker_lock_off``, 110.25), or a heater whose type is ``cord_and_plug`` (its factory
plug, 422.33(A), owner 2026-11-14); else UNKNOWN. A thermostat is never credited as the
disconnect: 424.20(A) needs a marked off position that directly opens every ungrounded conductor
and cannot re-energize by itself, which no field states. Not graded: the motor-over-1/8-hp
split, the panel label (424.47) and the placement rules. A sauna heater is not in Article 424.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.mep.electrical_spa_geometry import _separated, _walls
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import DeviceKind
from typehaus.model.nec import NEC, cite

_CID = "electrical.space_heat_circuit"


@check(Tier.ADVISORY, _CID)
def space_heat_circuit(ctx: CheckContext) -> list[Finding]:
    """Each fixed electric space-heating circuit: 125% (424.5), 30 A (424.4(B)), GFCI."""
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    devices = {e.tag: e for e in ctx.plan.all_elements() if e.element_kind == "ElectricalDevice"}
    heaters: dict[str, list[str]] = {}   # circuit -> heater tags
    cables: dict[str, list[str]] = {}    # circuit -> heating-cable zone tags
    for e in ctx.plan.all_elements():
        if e.element_kind == "Equipment" and getattr(e.kind, "value", "") == "space_heater" \
                and e.circuit:
            heaters.setdefault(e.circuit, []).append(e.tag)
        elif e.element_kind == "FloorHeat" and getattr(e.system, "value", "") == "electric":
            stat = devices.get(e.thermostat_ref or "")
            if stat is None or not stat.circuit:
                cables.setdefault("", []).append(e.tag)
            else:
                heaters.setdefault(stat.circuit, []).append(e.tag)
                cables.setdefault(stat.circuit, []).append(e.tag)
    if not heaters and not cables:
        return [not_applicable(_CID, "no fixed electric space heating is authored",
                               code=cite(NEC.SPACE_HEAT_CONTINUOUS))]
    out: list[Finding] = []
    for tag in cables.get("", []):
        out.append(unknown(_CID, f"{tag} names no thermostat on a circuit, so its circuit and "
                                 "GFCI protection are unknown", (tag,),
                           code=cite(NEC.SPACE_HEAT_GFCI)))
    for name, on in sorted(heaters.items()):
        circuit = circuits.get(name)
        if circuit is None:
            continue
        tags = (name, *on)
        if circuit.load_va is None:
            out.append(unknown(_CID, f"{name} states no load_va, so 125% is unknown", tags,
                               code=cite(NEC.SPACE_HEAT_CONTINUOUS)))
        else:
            amps = circuit.load_va / (240.0 if circuit.poles == 2 else 120.0)
            verb = passed if circuit.breaker_amps + 1e-9 >= 1.25 * amps else failed
            out.append(verb(_CID, f"{name}: {amps:.1f} A x 125% = {1.25 * amps:.1f} A against a "
                                  f"{circuit.breaker_amps} A breaker ({', '.join(on)})", tags,
                            code=cite(NEC.SPACE_HEAT_CONTINUOUS)))
        out.append(_disconnect(ctx, circuit, on, name in cables))
        if len(on) >= 2:
            verb = passed if circuit.breaker_amps <= 30 else failed
            out.append(verb(_CID, f"{name} serves {len(on)} heater outlets on a "
                                  f"{circuit.breaker_amps} A breaker (30 A at most)", tags,
                            code=cite(NEC.SPACE_HEAT_OUTLETS)))
        if name in cables:
            zones = tuple(cables[name])
            if circuit.gfci:
                out.append(passed(_CID, f"{name}: heating cable {', '.join(zones)} is "
                                        "GFCI-protected", (name, *zones),
                                  code=cite(NEC.SPACE_HEAT_GFCI)))
            else:
                out.append(unknown(_CID, f"{name} does not state GFCI protection for heating "
                                         f"cable {', '.join(zones)}", (name, *zones),
                                   code=cite(NEC.SPACE_HEAT_GFCI),
                                   fix="set gfci=True on the circuit if the breaker or "
                                       "thermostat is a GFCI"))
    return out


def _disconnect(ctx: CheckContext, circuit, heaters: list[str], stat: bool) -> Finding:
    """424.19: a disconnect in sight of every heater, or the breaker locks open."""
    from shapely.geometry import Point, Polygon

    code = cite(NEC.SPACE_HEAT_DISCONNECT)
    tags = (circuit.tag, *heaters)
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    discs = [objects[e.tag] for e in ctx.plan.all_elements()
             if e.element_kind == "ElectricalDevice" and e.kind is DeviceKind.DISCONNECT
             and e.circuit == circuit.tag and e.tag in objects]

    def in_sight(heater: str) -> str | None:
        obj = objects.get(heater)
        if obj is None or len(obj.footprint or ()) < 3:
            return None
        body = Polygon(obj.footprint)
        return next((d.tag for d in discs if d.storey == obj.storey and not _separated(
            body, Point(d.position), _walls(ctx, obj.storey))), None)

    types = {t.tag: t for t in ctx.plan.library.equipment_types}
    kinds = {e.tag: types.get(e.type_ref) for e in ctx.plan.all_elements()
             if e.element_kind == "Equipment" and e.tag in heaters}

    def plugged(heater: str) -> bool:
        return getattr(kinds.get(heater), "utilization_connection", None) == "cord_and_plug"

    seen = [in_sight(h) for h in heaters] if discs else []
    if seen and all(seen):
        return passed(_CID, f"{circuit.tag}: {', '.join(sorted(set(seen)))} is in plan sight "
                            f"of {', '.join(heaters)} (no wall between)", tags, code=code)
    if all(plugged(h) for h in heaters):
        return passed(_CID, f"{circuit.tag}: {', '.join(heaters)} is cord-and-plug connected, so "
                            "its factory plug is the disconnect (422.33(A))", tags,
                      code=cite(NEC.SPACE_HEAT_DISCONNECT, NEC.CORD_PLUG_DISCONNECT))
    if circuit.breaker_lock_off:
        return passed(_CID, f"{circuit.tag}: the breaker locks open (110.25), the 424.19(B)(1) "
                            f"disconnect for {', '.join(heaters)} out of sight", tags, code=code)
    note = "; its thermostat is not credited (424.20(A))" if stat else ""
    return unknown(_CID, f"{circuit.tag}: no disconnect in sight of {', '.join(heaters)} and the "
                         f"breaker is not stated lockable open{note}", tags,
                   code=cite(NEC.SPACE_HEAT_DISCONNECT, NEC.SPACE_HEAT_THERMOSTAT),
                   fix="a breaker lock-off fixed in place (breaker_lock_off=True), a "
                       "disconnect within sight, or for a cord-connected heater "
                       "utilization_connection='cord_and_plug' (422.33(A))")
