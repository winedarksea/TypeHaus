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
    # Physical breaker position in the enclosure. Real panel numbering: odd slots run down
    # the left column, even slots the right; a 2-pole breaker occupies ``slot`` and
    # ``slot + 2`` (the next space in the SAME column). ``electrical.panel_spaces``
    # reconciles slots against the panel type's ``spaces``.
    slot: int | None = None


register_constructor("Circuit", Circuit)


@register_element
class LoadManagement(Element):
    """A load-management arrangement over a group of circuits (capability, not a pick).

    Models an EMS (NEC 625.42), an interlock, or any controller that guarantees the named
    circuits never draw more than ``max_simultaneous_va`` together — letting
    ``electrical.service_load`` credit the managed group's excess against the service
    calculation. Schedule data like ``Circuit``: no geometry, lives in
    ``Library.load_managements``. The EMS-vs-service-upgrade decision stays open; nothing
    authors an instance until it is made.
    """

    managed_circuits: tuple[str, ...]  # Circuit tags in Library.circuits
    max_simultaneous_va: float  # controller-enforced ceiling for the group together
    strategy: str  # "ems" | "interlock" | ... — free text until a decision is made
    source: str = ""  # where the arrangement came from (product, note, code section)


register_constructor("LoadManagement", LoadManagement)
