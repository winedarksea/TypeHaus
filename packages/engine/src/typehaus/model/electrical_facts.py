"""Electrical product facts, as mixins on the type families that carry them.

Kept out of ``types.py`` (1,200+ lines) so each NEC lane owns one block here instead of
editing that file. A field belongs to the *type* when the datasheet states it; a value the
house decides (a circuit's continuous load) stays on the instance.
"""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class EquipmentElectricalFacts(HausModel):
    """Nameplate facts of a piece of equipment (``EquipmentType``)."""

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


class DeviceElectricalFacts(HausModel):
    """Listing and rating facts of a wiring device or panel (``ElectricalDeviceType``)."""

    # --- lane E: devices, panels, working space (Arts. 404/406/408, 110.26) ---

    # --- lane J: box depth (314.24(B)) ---
    # How far the device reaches behind its mounting strap, off the datasheet. Over 1-7/8 in.
    # (or 1 in. on 12/10 AWG) the box needs it plus 1/4 in. Unset: not stated, not graded.
    rear_projection: Length | None = None

    # --- lane I (shared with E): disconnect facts read by 440.11 / 440.12(A)(1) ---
    disconnect_rating_a: int | None = None
    lockable: bool | None = None  # locks, or needs a tool to open (440.11)
