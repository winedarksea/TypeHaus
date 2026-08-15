"""Circuits — the panel-schedule vocabulary (plans/electrical_notes.md).

A ``Circuit`` is schedule data, not geometry: it has no position and never appears in a
storey element list. Circuits live in ``Library.circuits``; devices and equipment point
at one via their ``circuit`` tag field. Wire/homerun routing stays a declared non-goal —
only main conduit trunks are modeled (as ``ConduitRun``), and those are independent of
the circuit list.
"""

from __future__ import annotations

from typehaus.model.base import Element
from typehaus.model.enums import BackupTier
from typehaus.model.registry import register_constructor, register_element


@register_element
class Circuit(Element):
    """One branch circuit / breaker position in a panel.

    ``poles`` carries the voltage (1 → 120V, 2 → 240V); ``backup_tier`` places a circuit
    on the backup microgrid, and says which of the two tiers it belongs to — see
    :class:`BackupTier`. ``load_va`` is an authored override — when unset the panel
    schedule sums ``ElectricalDeviceType.load_va`` over the referencing devices.
    """

    panel_ref: str  # PANEL-kind ElectricalDevice tag, e.g. "ED-B-PANEL"
    breaker_amps: int
    poles: int = 1
    nema: str | None = None  # receptacle configuration where one defines the circuit
    gfci: bool = False  # GFCI protection at the breaker (not the outlet)
    # AFCI protection at the breaker. E3902.16 requires it on the 120V branch circuits
    # serving nearly every habitable room, and unlike GFCI there is no device-level
    # alternative in common use — the breaker is where it lives, so the flag lives here and
    # nowhere else. False means "not stated": the check reports a circuit that needs AFCI
    # and does not declare it, rather than assuming either answer.
    afci: bool = False
    # None means "not on the backup microgrid" — the common case. ALWAYS_ON / SHED is the
    # authored two-tier scheme; nothing infers a tier from the load.
    backup_tier: BackupTier | None = None
    # A power-source interconnection (PV/ESS grid port, a future V2H port), not a load.
    # The service-load summary excludes these: a backfeed breaker is not demand. The
    # 705.12 interconnection check reads exactly this flag to find the source breakers.
    source: bool = False
    # Authored average-draw fraction of ``load_va`` over a backup event, 0..1. ESTIMATE
    # ONLY, and only meaningful on backup circuits — it exists so the autonomy calc can
    # say "the fridge is not drawing 700 VA for 24 hours". Never defaulted: a circuit
    # without one is reported as an unknown contributor, never silently as zero.
    duty_cycle: float | None = None
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


def luminaire_types(library: object) -> dict[str, object]:
    """The ``LuminaireType`` subset of ``Library.electrical_device_types``.

    A luminaire is the electrical-device type that carries a ``LuminaireForm``; there is
    no separate collection, so every consumer has to filter for it. Takes the library
    rather than the plan so the check tier (which holds a ``CheckContext``) and the draw
    and take-off tiers (which hold a model) can share one answer.
    """
    return {product.tag: product
            for product in library.electrical_device_types  # type: ignore[attr-defined]
            if getattr(product, "form", None) is not None}
