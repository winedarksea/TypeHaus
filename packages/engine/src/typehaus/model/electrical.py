"""Circuits — the panel-schedule vocabulary (plans/electrical_notes.md).

A ``Circuit`` is schedule data, not geometry: it has no position and never appears in a
storey element list. Circuits live in ``Library.circuits``; devices and equipment point
at one via their ``circuit`` tag field. Wire/homerun routing stays a declared non-goal —
only main conduit trunks are modeled (as ``ConduitRun``), and those are independent of
the circuit list.
"""

from __future__ import annotations

from typehaus.model.base import Element
from typehaus.model.registry import register_constructor, register_element


@register_element
class Circuit(Element):
    """One branch circuit / breaker position in a panel.

    ``poles`` carries the voltage (1 → 120V, 2 → 240V); ``backup`` marks circuits on the
    smart-relay backup subsystem (Shelly Pro 4PM behind the DIN enclosure), which the
    backup-component takeoff counts. ``load_va`` is an authored override — when unset the
    panel schedule sums ``ElectricalDeviceType.load_va`` over the referencing devices.
    """

    panel_ref: str  # PANEL-kind ElectricalDevice tag, e.g. "ED-B-PANEL"
    breaker_amps: int
    poles: int = 1
    nema: str | None = None  # receptacle configuration where one defines the circuit
    gfci: bool = False  # GFCI protection at the breaker (not the outlet)
    backup: bool = False
    load_va: float | None = None
    description: str = ""


register_constructor("Circuit", Circuit)
