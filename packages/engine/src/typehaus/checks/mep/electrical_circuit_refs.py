"""Circuit schedule integrity: references resolve and breakers fit their panels."""

from __future__ import annotations

from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.electrical import _warn_fail
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding


@check(Tier.ADVISORY, "electrical.circuit_refs")
def circuit_refs(ctx: CheckContext) -> list[Finding]:
    """Every ``circuit`` reference resolves, every panel_ref is a panel, poles match ports."""
    cid = "electrical.circuit_refs"
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    if not circuits:
        return [_unknown(cid, "no circuits authored")]

    # Alarms are consumers too: R314.4 puts them on a branch circuit, so a detector naming a
    # circuit that does not exist is the same defect as a receptacle doing it.
    consumers = [element for element in ctx.plan.all_elements()
                 if element.element_kind in ("ElectricalDevice", "Equipment", "Register",
                                             "Alarm")]
    panels = {element.tag for element in consumers
              if element.element_kind == "ElectricalDevice" and element.kind.value == "panel"}
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}

    out: list[Finding] = []
    for circuit in circuits.values():
        if circuit.panel_ref not in panels:
            out.append(_warn_fail(cid, f"circuit {circuit.tag} names missing panel "
                                       f"{circuit.panel_ref}", (circuit.tag,)))
    _required = {1: "power_120", 2: "power_240"}
    for element in consumers:
        ref = element.circuit
        if not ref:
            continue
        circuit = circuits.get(ref)
        if circuit is None:
            out.append(_warn_fail(cid, f"{element.tag} references unknown circuit {ref}",
                                  (element.tag,)))
            continue
        # A 2-pole circuit's device must offer a POWER_240 port (and 1-pole a POWER_120);
        # multi-port types (e.g. a two-gang 5-20R/6-20R) satisfy either.
        product_type = types.get(getattr(element, "type_ref", None))
        required = _required.get(circuit.poles)
        if (element.element_kind == "ElectricalDevice" and product_type is not None
                and product_type.ports and required is not None
                and required not in {port.service.value for port in product_type.ports}):
            out.append(_warn_fail(
                cid, f"{element.tag} on {circuit.poles}-pole circuit {ref} has no "
                     f"{required} port", (element.tag, ref),
            ))
    if not out:
        out.append(_pass(cid, f"{len(circuits)} circuits reconcile with their devices"))
    return out


@check(Tier.ADVISORY, "electrical.panel_spaces")
def panel_spaces(ctx: CheckContext) -> list[Finding]:
    """Breaker spaces required per panel vs. the enclosure, plus slot-map integrity.

    Spaces required = Σ poles over the panel's circuits. Where circuits author ``slot``
    positions, the physical map is checked too: a 2-pole breaker occupies ``slot`` and
    ``slot + 2`` (same column — odd left, even right), no two breakers may share a
    position, and no position may sit past the enclosure's ``spaces``.
    """
    cid = "electrical.panel_spaces"
    circuits = list(ctx.plan.library.circuits)
    if not circuits:
        return [_unknown(cid, "no circuits authored")]

    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    panels = {element.tag: element for element in ctx.plan.all_elements()
              if element.element_kind == "ElectricalDevice" and element.kind.value == "panel"}

    by_panel: dict[str, list] = {}
    for circuit in circuits:
        by_panel.setdefault(circuit.panel_ref, []).append(circuit)

    out: list[Finding] = []
    for panel_ref, group in sorted(by_panel.items()):
        required = sum(circuit.poles for circuit in group)
        panel = panels.get(panel_ref)
        product_type = types.get(getattr(panel, "type_ref", None)) if panel else None
        spaces = getattr(product_type, "spaces", None)
        if spaces is None:
            out.append(_unknown(
                cid, f"panel {panel_ref} needs {required} spaces but its type declares "
                     f"no ``spaces``", (panel_ref,)))
        elif required > spaces:
            out.append(_warn_fail(
                cid, f"panel {panel_ref} needs {required} breaker spaces but the "
                     f"enclosure has {spaces} — swap to a larger panel or shed circuits",
                (panel_ref,)))
        else:
            out.append(_pass(
                cid, f"panel {panel_ref}: {required} spaces required fits the "
                     f"{spaces}-space enclosure", (panel_ref,)))
        # Slot-map integrity — only over circuits that author a slot.
        occupied: dict[int, str] = {}
        for circuit in group:
            if circuit.slot is None:
                continue
            positions = (circuit.slot,) if circuit.poles == 1 else (circuit.slot,
                                                                    circuit.slot + 2)
            for position in positions:
                if position in occupied:
                    out.append(_warn_fail(
                        cid, f"panel {panel_ref}: slot {position} assigned to both "
                             f"{occupied[position]} and {circuit.tag}",
                        (occupied[position], circuit.tag)))
                else:
                    occupied[position] = circuit.tag
            if spaces is not None and positions[-1] > spaces:
                out.append(_warn_fail(
                    cid, f"panel {panel_ref}: {circuit.tag} occupies slot "
                         f"{positions[-1]}, past the {spaces}-space enclosure",
                    (circuit.tag,)))
    return out
