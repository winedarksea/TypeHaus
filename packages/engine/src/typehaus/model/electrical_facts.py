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
