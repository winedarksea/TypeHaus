"""Circuits — the panel-schedule vocabulary.

A ``Circuit`` is schedule data, not geometry: it has no position and never appears in a
storey element list. Circuits live in ``Library.circuits``; devices and equipment point
at one via their ``circuit`` tag field. Wire/homerun routing stays a declared non-goal —
only main conduit trunks are modeled (as ``ConduitRun``), and those are independent of
the circuit list.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

from pydantic import model_validator

from typehaus.model.ampacity import ConductorMaterial, is_size
from typehaus.model.base import Element, HausModel
from typehaus.model.enums import BackupTier
from typehaus.model.registry import register_constructor, register_element
from typehaus.model.types import LuminaireType
from typehaus.quantities import Length, inch

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
    # Which GFCI ``gfci`` is; read only where it is True. "A" is the 6 mA personnel class.
    # "C" is a listed Class C SPGFCI (UL 943C, 20 mA), which 2026 NEC 210.8(F) Ex. 3 accepts
    # only for listed HVAC equipment, and only with the equipment's disconnect marked
    # "Warning: Class C SPGFCI Protection Provided for HVAC Unit". No schedule prints that
    # label; the GFCI check's finding states the marking.
    gfci_class: Literal["A", "C"] = "A"
    # Supplies a spa or hot tub: ``code.NEC_680_spa`` grades it (NEC 680.44) even where the
    # tub itself is not modeled. Authored; a circuit an ``EquipmentKind.SPA`` names counts too.
    spa: bool = False
    # The circuit is roughed in only: it ends at its disconnect or outlet and the equipment it
    # is sized for is not installed. Rules that govern only installed equipment read N/A.
    rough_in_only: bool = False
    # The breaker carries a lock-off fixed in place with or without the lock (110.25).
    breaker_lock_off: bool = False
    # AFCI protection at the breaker. NEC 210.12 requires it on the 120V branch circuits
    # serving nearly every habitable room, and unlike GFCI there is no device-level
    # alternative in common use — the breaker is where it lives, so the flag lives here and
    # nowhere else. False means "not stated": the check reports a circuit that needs AFCI
    # and does not declare it, rather than assuming either answer.
    afci: bool = False
    # None means "not on the backup microgrid" — the common case. ALWAYS_ON / SURPLUS is the
    # authored two-tier scheme; nothing infers a tier from the load.
    backup_tier: BackupTier | None = None
    # A power-source interconnection (PV/ESS grid port, a future V2H port), not a load.
    # The service-load summary excludes these: a backfeed breaker is not demand. The
    # 705.12 interconnection check reads exactly this flag to find the source breakers.
    source: bool = False
    # This position holds a plug-on surge protective device: no load, no source.
    spd: bool = False
    # ``spd`` only: the plug-on's catalog ``ElectricalDeviceType`` (never placed), whose
    # ``spd_class``, ``spd_nominal_discharge_ka`` and ``spd_listing`` 215.18(C)/(E) read.
    spd_type_ref: str | None = None
    # Authored average-draw fraction of ``load_va`` over a backup event, 0..1. ESTIMATE
    # ONLY, and only meaningful on backup circuits — it exists so the autonomy calc can
    # say "the fridge is not drawing 700 VA for 24 hours". Never defaulted: a circuit
    # without one is reported as an unknown contributor, never silently as zero.
    duty_cycle: float | None = None
    # The most this circuit can draw DURING A BACKUP EVENT, where something other than its
    # breaker governs it — a smart appliance forced into a low-power mode while the house is
    # on battery. Only meaningful on a backup circuit, and never inferred: absent means the
    # circuit draws its connected load. This is a BACKUP fact and belongs beside
    # ``backup_tier``; it earns nothing in a 120.82 service calculation, which is why it is
    # not a ``LoadManagement`` (an unlisted software governor is not a PCS, 2026 NEC 130.2).
    backup_va: float | None = None
    # PoE data devices (tags) whose switch ports are turned off while the house is on battery.
    # Only meaningful on the backup circuit feeding the PoE switch: ``duty_cycle`` stays the
    # unshed average, and the backup calc subtracts these devices' scheduled ``poe_watts``
    # (grossed up for the switch supply's loss). Authored, never inferred, like the tier.
    backup_shed_poe: tuple[str, ...] = ()
    # Starting draw from a published starting (locked-rotor) current, for the backup surge
    # test. None means the calc assumes 3x ``load_va``; an inverter compressor's start is its
    # running maximum.
    start_va: float | None = None
    load_va: float | None = None
    # The part of the load that runs 3 h or more (210.19(A)(1), 210.20(A)). None: not stated;
    # 0: stated noncontinuous. Never more than the circuit's load.
    continuous_va: float | None = None
    # --- conductors (lane A). Sizes are ``model/ampacity.SIZES`` strings: "12", "1/0",
    # "250" (kcmil). None: not authored, and readers fall back to what the breaker implies.
    conductor_awg: str | None = None
    conductor_material: ConductorMaterial = "cu"  # "al" also covers copper-clad aluminum
    egc_awg: str | None = None  # wire EGC, same material; None: none authored
    # 110.14(C)(1) termination column. None: 60 °C at 100 A or less with 14-1 AWG, else 75 °C.
    # 75 is authored only where both ends are listed and identified for it.
    termination_temp_c: Literal[60, 75] | None = None
    description: str = ""
    # Physical breaker position in the enclosure. Real panel numbering: odd slots run down
    # the left column, even slots the right; a 2-pole breaker occupies ``slot`` and
    # ``slot + 2`` (the next space in the SAME column). ``electrical.panel_spaces``
    # reconciles slots against the panel type's ``spaces``.
    slot: int | None = None

    @model_validator(mode="after")
    def _conductors_are_table_sizes(self) -> Circuit:
        for name in ("conductor_awg", "egc_awg"):
            size = getattr(self, name)
            if size is not None and not is_size(size):
                raise ValueError(f"{self.tag}: {name}={size!r} is not an AWG/kcmil size")
        if self.egc_awg is not None and self.conductor_awg is None:
            raise ValueError(f"{self.tag}: egc_awg needs conductor_awg")
        if (self.continuous_va is not None and self.load_va is not None
                and self.continuous_va > self.load_va + 1e-9):
            raise ValueError(f"{self.tag}: continuous_va exceeds load_va")
        return self


register_constructor("Circuit", Circuit)


# The two bases a load-management credit can rest on, and nothing else. Free text used
# to be allowed here, which let a controller with no listing and no code section behind it
# take a credit off the service calculation just by naming itself an "ems". The old
# ``hvac_interlock`` is gone: 2026 NEC 120.82(C)(3)'s compressor/supplemental interlock is a
# term of the selection, authored as ``Equipment.compressor_lockout_ref``, not a group cap.
LoadManagementStrategy = Literal["noncoincident", "pcs"]


@register_element
class LoadManagement(Element):
    """A load-management arrangement over a group of circuits, and the basis it stands on.

    A controller guarantees the named circuits never draw more than
    ``max_simultaneous_va`` together, so the group's connected excess never reaches the
    service. ``electrical.service_load`` credits that excess only where ``strategy`` names
    a basis the credit actually earns:

    - ``noncoincident`` — 2026 NEC 120.6: the group counts at its single largest load
      (an authored ceiling below that is raised to it). (1) feeder/service loads unlikely to
      run together, an AHJ judgement on a ``source``; or (2) loads listed equipment prevents
      from running together, on a ``listing``.
    - ``pcs`` — a power control system under 2026 NEC Article 130 Part II (120.7(B) sets the
      setpoint at <= 80% of the monitored OCPD; 130.2 requires the listing; 625.42(A)
      points EV supply equipment at the same Part II). Credited only with a ``listing``:
      an unlisted controller running proprietary throttling software earns nothing.
      ``max_simultaneous_va`` is the control setting, and the 120.7(C)(1) load where the PCS
      monitors only controlled loads. One that also monitors noncontrolled loads
      (``monitors_noncontrolled``) counts the group at ``min_operating_amps`` (120.7(C)(2)).

    A noncoincident member's motor counts at 125% (120.11(A)): its equipment type's
    ``largest_motor_va``.

    Schedule data like ``Circuit``: no geometry, lives in ``Library.load_managements``.
    """

    managed_circuits: tuple[str, ...]  # Circuit tags in Library.circuits
    max_simultaneous_va: float  # controller-enforced ceiling for the group together
    strategy: LoadManagementStrategy
    # The standard and mark a ``pcs`` is listed to, e.g. "UL 3141". Empty is "none
    # recorded", which is what a refusal reports — never assumed present.
    listing: str = ""
    source: str = ""  # where the arrangement came from (product, note, code section)
    # ``pcs`` only: the rating of the OCPD the PCS monitors. When set, a setting above 80% of it
    # (120.7(B), at 240 V) refuses the credit. Unset: the setting is not graded.
    monitored_ocpd_amps: float | None = None
    # ``pcs`` only, 120.7(C)(2): the PCS also monitors noncontrolled loads, so the controlled
    # group counts at its minimum operating current (amps at 240 V, zero or more). Unset with
    # ``monitors_noncontrolled``: no credit.
    monitors_noncontrolled: bool = False
    min_operating_amps: float | None = None


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


#: NEC 2026 Table 314.16(A), metal boxes: trade designation -> cubic inches. Code data, not
#: a catalog: a listed nonmetallic box is marked with its own volume instead.
METAL_BOX_VOLUME_IN3: dict[str, float] = {
    "4 x 1-1/4 square": 18.0, "4 x 1-1/2 square": 21.0, "4 x 2-1/8 square": 30.3,
    "4-11/16 x 1-1/4 square": 25.5, "4-11/16 x 1-1/2 square": 29.5,
    "4-11/16 x 2-1/8 square": 42.0,
    "3 x 2 x 2-1/4 device": 10.5, "3 x 2 x 2-1/2 device": 12.5,
    "3 x 2 x 2-3/4 device": 14.0, "3 x 2 x 3-1/2 device": 18.0,
    "4 x 2-1/8 x 1-1/2 device": 10.3, "4 x 2-1/8 x 1-7/8 device": 13.0,
    "4 x 2-1/8 x 2-1/8 device": 14.5,
}

BoxMounting = Literal["surface", "flush", "flush_raceway"]
BoxShape = Literal["rectangular", "round"]


class BoxRow(HausModel):
    """One box and its cover (surface) or device ring (flush), for a mounting × gangs.

    ``box_size`` is (width, height, depth) of the box body; a ``shape="round"`` box is
    (diameter, diameter, depth). A metal box names its Table
    314.16(A) ``designation``; a nonmetallic one authors its marked ``box_volume_in3``.
    ``cover_volume_in3`` is the volume a raised cover or ring adds where it is marked with
    one (314.16(A)); ``cover_rise`` is how far a surface cover stands proud of the box.
    ``use`` names a special-purpose row (``"luminaire"`` for every light, or the
    ``box_use`` a device type asks for, e.g. ``"recessed"``); None is the general row.
    ``block_profile`` derives a flat block of that lumber behind each such box, between the
    bay's studs, for a box that screws to wood wherever it lands (geometry review M3-107).
    ``internal_clamps`` (314.16(B)(2)): None is "not stated" and box fill counts the
    allowance; False is a datasheet showing none. ``support_fittings`` (314.16(B)(3)) counts
    the kinds of fixture stud or hickey inside.
    """

    mounting: BoxMounting
    gangs: int = 1
    use: str | None = None
    box_product_ref: str
    # None where the box takes no ring or cover: a flush nonmetallic box under a wall plate.
    cover_product_ref: str | None = None
    box_size: tuple[Length, Length, Length]
    shape: BoxShape = "rectangular"
    designation: str | None = None
    box_volume_in3: float | None = None
    cover_volume_in3: float = 0.0
    cover_rise: Length = inch(0)
    block_profile: str | None = None
    internal_clamps: bool | None = None
    support_fittings: int = 0

    @property
    def volume_in3(self) -> float | None:
        """Box plus marked cover/ring volume, or None when neither source names one."""
        box = (self.box_volume_in3 if self.box_volume_in3 is not None
               else METAL_BOX_VOLUME_IN3.get(self.designation or ""))
        return None if box is None else box + self.cover_volume_in3


@register_element
class BoxStandard(Element):
    """The house's device boxes, declared once and derived per device (decision #93).

    One per plan (a second is an ``integrity.box_standard`` error). The mounting is derived
    from the host face (``resolve/device_boxes.py``): bare concrete or masonry takes
    ``surface``, a framed cavity ``flush``, and a flush box an authored raceway reaches
    ``flush_raceway``. ``surface_drop`` is the trade size of the derived EMT sleeve that
    brings NM down to a surface box from overhead (NEC 334.15(B)/(C)).
    """

    rows: tuple[BoxRow, ...]
    surface_drop: Length

    def row_for(self, mounting: str, gangs: int, use: str | None = None) -> BoxRow | None:
        """The ``use`` row for this mounting and gangs, else the general one."""
        rows = [row for row in self.rows if row.mounting == mounting and row.gangs == gangs]
        return (next((row for row in rows if use is not None and row.use == use), None)
                or next((row for row in rows if row.use is None), None))

    def product_refs(self) -> tuple[str, ...]:
        refs = [ref for row in self.rows for ref in (row.box_product_ref, row.cover_product_ref)
                if ref]
        return tuple(dict.fromkeys(refs))


register_constructor("BoxStandard", BoxStandard)
register_constructor("BoxRow", BoxRow)
