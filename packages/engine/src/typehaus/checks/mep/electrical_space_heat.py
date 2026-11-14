"""``electrical.space_heat_circuit`` — 2026 NEC 424.4(B), 424.5 and the floor-heat GFCI rules.

Fixed electric space heating here is a ``FloorHeat`` zone (its circuit is its thermostat's) or an
``EquipmentKind.SPACE_HEATER`` on a circuit. Graded per circuit: 424.5, a continuous load, so the
breaker is at least 125% of the authored ``load_va`` (volts from the poles); 424.4(B), a circuit
for two or more heater outlets is 30 A or less; and for a heating-cable zone, GFCI (424.44(E)
bathrooms and kitchens, 424.45(E) any cable under a floor covering, 424.99(C)(5) panels), read
from ``Circuit.gfci``. Not graded: disconnects (424.19-424.21), the panel label (424.47) and
the placement rules, none of which the model holds. A sauna heater is not in Article 424.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
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
