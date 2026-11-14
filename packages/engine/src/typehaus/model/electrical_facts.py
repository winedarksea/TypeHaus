"""Electrical product facts, as mixins on the type families that carry them.

Kept out of ``types.py`` (1,200+ lines) so each NEC lane owns one block here instead of
editing that file. A field belongs to the *type* when the datasheet states it; a value the
house decides (a circuit's continuous load) stays on the instance.
"""

from __future__ import annotations

from typehaus.model.base import HausModel


class EquipmentElectricalFacts(HausModel):
    """Nameplate facts of a piece of equipment (``EquipmentType``)."""

    # --- lane I: HVAC (Art. 440) and space heat (Art. 424) ---


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
