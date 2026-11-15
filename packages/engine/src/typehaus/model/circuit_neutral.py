"""Whether a branch circuit carries a neutral: one leaf for box fill, raceway fill and the BOM.

``Circuit.neutral`` wins when authored. A 1-pole circuit always has one. A 2-pole circuit has
one when any device on it has a 120 V half (a 14- receptacle, or both power ports), none when
every device on it is a straight-240 receptacle (a 6- configuration), and otherwise keeps
the conservative count (a neutral), since an equipment type's ports do not prove a two-wire
supply: author ``neutral=False`` from the submittal instead.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def device_has_neutral(product_type: Any | None) -> bool:
    """A device type that lands a neutral: a 14- configuration or a 120 V and a 240 V port."""
    nema = getattr(product_type, "nema", None) or ""
    services = {getattr(port.service, "value", None)
                for port in getattr(product_type, "ports", ())}
    return nema.startswith("14-") or {"power_120", "power_240"} <= services


def _straight_240(product_type: Any | None) -> bool:
    return (getattr(product_type, "nema", None) or "").startswith("6-")


def circuit_has_neutral(circuit: Any, device_types: Iterable[Any | None]) -> bool:
    """``device_types``: the types of the ElectricalDevices on ``circuit`` (None: untyped)."""
    if circuit.neutral is not None:
        return circuit.neutral
    if circuit.poles == 1:
        return True
    types = list(device_types)
    if any(device_has_neutral(t) for t in types):
        return True
    return not (types and all(_straight_240(t) for t in types))


def neutral_by_circuit(plan: Any) -> dict[str, bool]:
    """Circuit tag -> whether it carries a neutral, over a whole plan."""
    types = {t.tag: t for t in plan.library.electrical_device_types}
    on: dict[str, list] = {}
    for element in plan.all_elements():
        if element.element_kind == "ElectricalDevice" and getattr(element, "circuit", None):
            on.setdefault(element.circuit, []).append(types.get(element.type_ref or ""))
    return {c.tag: circuit_has_neutral(c, on.get(c.tag, ())) for c in plan.library.circuits}


def conductors_per_circuit(circuit: Any, has_neutral: bool) -> int:
    """Insulated current-carrying conductors: the hots, plus a neutral where one runs."""
    return max(circuit.poles, 1) + (1 if has_neutral else 0)
