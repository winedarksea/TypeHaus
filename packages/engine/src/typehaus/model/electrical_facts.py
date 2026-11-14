"""Electrical product facts, as mixins on the type families that carry them.

Kept out of ``types.py`` (1,200+ lines) so each NEC lane owns one block here instead of
editing that file. A field belongs to the *type* when the datasheet states it; a value the
house decides (a circuit's continuous load) stays on the instance.
"""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class EquipmentElectricalFacts(HausModel):
    """Nameplate facts of a piece of equipment (``EquipmentType``)."""

    # --- lane A: conductors and circuit loads (210.23(B)) ---
    # How the product connects as shipped: "cord_and_plug" (factory cord to a receptacle, not
    # fastened in place) or "fastened" (fastened in place). None: not stated.
    utilization_connection: Literal["cord_and_plug", "fastened"] | None = None

    # --- lane I: HVAC (Art. 440) and space heat (Art. 424) ---
    # 440.4(B) nameplate of multimotor/combination equipment, from the published submittal.
    # A field-installed accessory (a heat kit) whose row marks the whole unit carries the
    # combination's values; the circuit is graded against the largest MCA on it.
    min_circuit_ampacity_a: float | None = None  # MCA
    max_overcurrent_a: int | None = None  # MOCP: maximum fuse or breaker

    # --- lane J: load calculation (Art. 120) ---
    # VA of the largest motor over 1/8 hp (nameplate FLA x volts), not a hermetic compressor
    # (Art. 440). A noncoincident group takes it at 125% (120.11(A)). Unset: no motor stated.
    largest_motor_va: float | None = None

    # --- lane F: sources (Arts. 480, 702, 705, 706) ---
    # An inverter's grid-port maximum OCPD rides on ``max_overcurrent_a`` above.
    # PCS functions the maker publishes for its UL 1741 PCS listing, e.g. "export_limiting",
    # "import_limiting", "ess_operating_modes", "overload_control" (702.4(A)(3) reads the last).
    # None: no PCS function stated.
    pcs_functions: tuple[str, ...] | None = None
    # BATTERY kinds: nominal voltage, V dc (480.7(A)'s 60 V, 480.7(F)/706.15(D) label).
    battery_nominal_voltage_v: float | None = None
    # INVERTER kinds: what opening the RSD initiation loop stops, per the maker's manual:
    # "pv_array" (690.12), "ac_output" (export to premises wiring), "ess" (battery disconnect).
    rsd_shutdown_scope: tuple[Literal["pv_array", "ac_output", "ess"], ...] | None = None


class DeviceElectricalFacts(HausModel):
    """Listing and rating facts of a wiring device or panel (``ElectricalDeviceType``)."""

    # --- lane E: devices, panels, working space (Arts. 404/406/408, 110.26) ---
    # SPD kinds: UL 1449 nominal discharge current In, kA (230.67(E), 215.18(E): 10 or more).
    # Not ``surge_ka``, the maker's surge-capacity headline. Unset: the sheet does not publish it.
    spd_nominal_discharge_ka: float | None = None
    # SPD kinds: the listing as the sheet states it, e.g. "UL 1449 4th ed., Type 2".
    spd_listing: str | None = None
    # Receptacle kinds: listed weather-resistant (406.9(A)(1)(c) damp, (B)(1)(d) wet).
    weather_resistant: bool | None = None
    # Receptacle kinds: under a listed extra-duty in-use hood, weatherproof with a plug in
    # (406.9(B)(1)(a)-(b), wet locations). None: unstated.
    in_use_cover: bool | None = None
    # Receptacle kinds: factory-marked with the 406.11(D) "controlled" symbol and word.
    controlled_marking: bool | None = None
    # Disconnect kinds: ampere rating, and whether it locks open (110.25; 440.11/440.12(A)(1)).
    disconnect_rating_a: int | None = None
    lockable: bool | None = None
    # Panel kinds: short-circuit current rating from the label, A (408.6). The field-marked
    # value (408.6(2)) rests on the installed OCPDs, so this is the most the panel can carry.
    sccr_a: int | None = None
    # Service-equipment kinds (a meter-main): the utility's available fault current at its line
    # terminals, A (408.6(1)). House-authored from the utility's letter; unset until it is known.
    available_fault_current_a: int | None = None

    # --- lane J: box depth (314.24(B)) ---
    # How far the device reaches behind its mounting strap, off the datasheet. Over 1-7/8 in.
    # (or 1 in. on 12/10 AWG) the box needs it plus 1/4 in. Unset: not stated, not graded.
    rear_projection: Length | None = None

    # --- lane H: grounding (Art. 250) ---
    # IBT kinds: terminals for bonding conductors, off the sheet (250.94(A): at least three).
    bonding_terminals: int | None = None

    # --- lane F: panel feed position (705.12(B)(2)/(4)) ---
    # Panel kinds: where the primary feed (main or main lugs) enters the bus, read off the
    # product's sheet. "center": a center-fed panelboard. None: not stated.
    main_feed_end: Literal["top", "bottom", "center"] | None = None


class EvseElectricalFacts(HausModel):
    """EV supply equipment facts (``ApplianceType``) — lane F, 625.50."""

    # Where the connector is stored, above the floor (indoors) or grade (outdoors). A holster
    # sold loose (Grizzl-E EasyEvPlug) is placed by the house, so the house's type states it.
    connector_holster_height: Length | None = None
