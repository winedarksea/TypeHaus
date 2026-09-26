"""Circuits — the panel-schedule vocabulary (plans/electrical_notes.md).

A ``Circuit`` is schedule data, not geometry: it has no position and never appears in a
storey element list. Circuits live in ``Library.circuits``; devices and equipment point
at one via their ``circuit`` tag field. Wire/homerun routing stays a declared non-goal —
only main conduit trunks are modeled (as ``ConduitRun``), and those are independent of
the circuit list.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

from typehaus.model.base import Element
from typehaus.model.enums import BackupTier
from typehaus.model.registry import register_constructor, register_element
from typehaus.model.types import LuminaireType

if TYPE_CHECKING:
    from typehaus.model.plan import Library


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
    # The most this circuit can draw DURING A BACKUP EVENT, where something other than its
    # breaker governs it — a smart appliance forced into a low-power mode while the house is
    # on battery. Only meaningful on a backup circuit, and never inferred: absent means the
    # circuit draws its connected load. This is a BACKUP fact and belongs beside
    # ``backup_tier``; it earns nothing in a 220.82 service calculation, which is why it is
    # not a ``LoadManagement`` (an unlisted software governor is not a PCS, 2026 NEC 130.2).
    backup_va: float | None = None
    load_va: float | None = None
    description: str = ""
    # Physical breaker position in the enclosure. Real panel numbering: odd slots run down
    # the left column, even slots the right; a 2-pole breaker occupies ``slot`` and
    # ``slot + 2`` (the next space in the SAME column). ``electrical.panel_spaces``
    # reconciles slots against the panel type's ``spaces``.
    slot: int | None = None


register_constructor("Circuit", Circuit)


# The three bases a load-management credit can rest on, and nothing else. Free text used
# to be allowed here, which let a controller with no listing and no code section behind it
# take a credit off the service calculation just by naming itself an "ems".
LoadManagementStrategy = Literal["hvac_interlock", "noncoincident", "pcs"]


@register_element
class LoadManagement(Element):
    """A load-management arrangement over a group of circuits, and the basis it stands on.

    A controller guarantees the named circuits never draw more than
    ``max_simultaneous_va`` together, so the group's connected excess never reaches the
    service. ``electrical.service_load`` credits that excess only where ``strategy`` names
    a basis the credit actually earns:

    - ``hvac_interlock`` — 2026 NEC 220.82(C)(2)/(4) itself credits a controller that
      prevents a compressor and its supplemental heat from running at once. Needs no
      listed device. Credited only over heat-pump circuits: (C) governs space-conditioning
      loads and reaches nothing else.
    - ``noncoincident`` — 2026 NEC 220.60: loads that cannot be energized together are
      counted once, at the largest. Needs a ``source`` saying what makes them exclusive,
      and is an AHJ judgement, not an arithmetic fact.
    - ``pcs`` — a power control system under 2026 NEC Article 130 Part II (120.7 sets the
      setpoint at <= 80% of the monitored OCPD; 130.2 requires the listing; 625.42(A)
      points EV supply equipment at the same Part II). Credited only with a ``listing``:
      an unlisted controller running proprietary throttling software earns nothing.

    Schedule data like ``Circuit``: no geometry, lives in ``Library.load_managements``.
    """

    managed_circuits: tuple[str, ...]  # Circuit tags in Library.circuits
    max_simultaneous_va: float  # controller-enforced ceiling for the group together
    strategy: LoadManagementStrategy
    # The standard and mark a ``pcs`` is listed to, e.g. "UL 3141". Empty is "none
    # recorded", which is what a refusal reports — never assumed present.
    listing: str = ""
    source: str = ""  # where the arrangement came from (product, note, code section)


register_constructor("LoadManagement", LoadManagement)


def luminaire_types(library: Library) -> dict[str, LuminaireType]:
    """The ``LuminaireType`` subset of ``Library.electrical_device_types``.

    A luminaire is the electrical-device type that carries a ``LuminaireForm``; there is
    no separate collection, so every consumer has to filter for it. Takes the library
    rather than the plan so the check tier (which holds a ``CheckContext``) and the draw
    and take-off tiers (which hold a model) can share one answer.
    """
    return {product.tag: cast(LuminaireType, product)
            for product in library.electrical_device_types
            if getattr(product, "form", None) is not None}
