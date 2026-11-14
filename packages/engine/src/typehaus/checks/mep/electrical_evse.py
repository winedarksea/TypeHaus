"""``electrical.evse_circuit`` — 2026 NEC 625.40, 625.41, 625.43(C) and 625.54 for an EV circuit.

An EV circuit is the one ``service_load`` already files under "ev" (its description says EV
charging); there is no EVSE device kind. Its load is the authored ``load_va``, taken as the
charger's continuous output (625.41: EVSE is a continuous load, so the breaker is 125% of it).
625.40 wants the circuit individual: nothing else may be on it. 625.54 reaches only a receptacle
installed for EV charging; a circuit with none (hardwired) earns N/A. 625.43(C): a permanently
connected EVSE has a readily accessible disconnect, and a plaque on it where that is remote.
No plaque is modelled, so a hardwired unit's breaker, the only disconnect, is reported, not
graded; a cord-and-plug unit's plug is its disconnect (60 A or less). 625.50: an appliance
whose type states ``connector_holster_height`` stores its connector at least 18 in. above an
indoor floor (a room holds it) or 24 in. above outdoor grade.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.nec import NEC, cite

_CID = "electrical.evse_circuit"
_RECEPTACLES = frozenset({"receptacle", "gfci", "receptacle_240"})
_HOLSTER_MIN_INDOORS_IN = 18.0  # 625.50
_HOLSTER_MIN_OUTDOORS_IN = 24.0


@check(Tier.ADVISORY, _CID)
def evse_circuit(ctx: CheckContext) -> list[Finding]:
    """Each EV circuit: individual (625.40), 125% of the charger (625.41), 625.43(C), 625.54."""
    from typehaus.takeoff.service_load import _bucket

    consumers: dict[str, list] = {}
    for element in ctx.plan.all_elements():
        circuit = getattr(element, "circuit", None)
        if circuit:
            consumers.setdefault(circuit, []).append(element)
    ev = [c for c in ctx.plan.library.circuits
          if not c.source and _bucket(ctx.model, c, consumers.get(c.tag, [])) == "ev"]
    if not ev:
        return [not_applicable(_CID, "no EV circuit is authored",
                               code=cite(NEC.EVSE_CIRCUIT))]
    out: list[Finding] = []
    for circuit in ev:
        on = consumers.get(circuit.tag, [])
        tags = (circuit.tag, *(e.tag for e in on))
        if len(on) != 1:
            out.append(failed(_CID, f"{circuit.tag} serves {len(on)} devices; an EVSE outlet "
                                    "takes an individual circuit", tags,
                              code=cite(NEC.EVSE_CIRCUIT),
                              fix="give the EVSE its own breaker"))
        else:
            out.append(passed(_CID, f"{circuit.tag} serves only {on[0].tag}", tags,
                              code=cite(NEC.EVSE_CIRCUIT)))
        if circuit.load_va is None:
            out.append(unknown(_CID, f"{circuit.tag} states no load_va, so 125% is unknown",
                               tags, code=cite(NEC.EVSE_CONTINUOUS)))
        else:
            amps = circuit.load_va / (240.0 if circuit.poles == 2 else 120.0)
            need = 1.25 * amps
            verb = passed if circuit.breaker_amps + 1e-9 >= need else failed
            out.append(verb(_CID, f"{circuit.tag}: {amps:.1f} A charger x 125% = {need:.1f} A "
                                  f"against a {circuit.breaker_amps} A breaker", tags,
                            code=cite(NEC.EVSE_CONTINUOUS)))
        if any(e.kind.value in _RECEPTACLES for e in on if hasattr(e, "kind")):
            ok = circuit.gfci or all(getattr(e, "gfci_ref", None) for e in on)
            out.append((passed if ok else failed)(
                _CID, f"{circuit.tag}'s EV receptacle {'is' if ok else 'is not'} GFCI-protected",
                tags, code=cite(NEC.EVSE_RECEPTACLE_GFCI)))
        else:
            out.append(not_applicable(_CID, f"{circuit.tag} feeds no receptacle (hardwired)",
                                      tags, code=cite(NEC.EVSE_RECEPTACLE_GFCI)))
            out.append(advisory(
                _CID, f"{circuit.tag}: its breaker in {circuit.panel_ref} is the only "
                      "disconnect modelled; if it is remote from the EVSE, a plaque on the "
                      "unit must say where", tags, Result.ADVISORY,
                code=cite(NEC.EVSE_DISCONNECT)))
    out.extend(_coupling_height(ctx))
    return out


def _coupling_height(ctx: CheckContext) -> list[Finding]:
    """625.50 for each placed EVSE whose type states where its connector is stored."""
    types = {t.tag: t for t in ctx.plan.library.appliance_types}
    out: list[Finding] = []
    for unit in sorted((e for e in ctx.plan.all_elements() if e.element_kind == "Appliance"),
                       key=lambda e: e.tag):
        height = getattr(types.get(unit.type_ref or ""), "connector_holster_height", None)
        if height is None:
            continue
        inches = height.inches
        indoors = bool(getattr(unit, "room", None))
        need = _HOLSTER_MIN_INDOORS_IN if indoors else _HOLSTER_MIN_OUTDOORS_IN
        where = f"above the floor of {unit.room}" if indoors else "above grade"
        verb = passed if inches + 1e-6 >= need else failed
        out.append(verb(_CID, f"{unit.tag}: connector stored {inches:g} in. {where}, against "
                              f"{need:g} in.", (unit.tag,), code=cite(NEC.EVSE_COUPLING_HEIGHT)))
    return out
