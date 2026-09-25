"""Starter panel schedule — every branch circuit in ED-PANEL.

NOT ``# haus: editable``: circuits are schedule data, not geometry — nothing here can be
dragged in the editor. Devices, equipment and alarms reference these tags via their
``circuit=`` field in the editable files, and ``electrical.circuit_refs`` reconciles the
two directions.

Conventions (the same ones ``houses/catlin/plan/circuits.py`` uses, at template scale):

- ``poles=1`` is a 120V circuit; ``poles=2`` would be 240V. This house has no 240V load.
- ``afci=True`` is arc-fault protection at the breaker. ``code.E3902_16_afci`` requires it
  on the 120V 15/20A circuits that reach a habitable room, which here is all of them.
- ``slot`` is the physical breaker position — odd numbers run down the left column, even
  down the right. Four one-pole breakers use 4 of ED-T-PANEL's 20 spaces.

NEC 220.12 asks for 3 VA/sf of general lighting and receptacle load, which over this
house's 886 sf of habitable floor is 2,658 VA — two 15/20A circuits' worth, which is
exactly the two authored below. Splitting receptacles per storey is what a real house
would do; one circuit is the honest minimum and the panel has the spaces for the split.
"""

from __future__ import annotations

from library.electrical import panel_type

from typehaus import Circuit

_PANEL = "ED-PANEL"

# The panel: the library's 100A row under this house's own tag. Here, not in the editable
# plan/electrical.py, because that dialect has no ``model_copy``.
PANEL_TYPES = (
    # `service_amps` is what the 220.82 demand estimate is compared against, and `spaces`
    # is what `electrical.panel_spaces` reconciles the circuit slots against. A 20-space
    # 100A load centre is the smallest enclosure this house could be built on, and it
    # leaves spare positions for the radon fan's future circuit and for the kitchen and
    # bathroom this template does not yet have.
    panel_type("ED-T-PANEL-100A", tag="ED-T-PANEL"),
)

CIRCUITS = (
    Circuit(tag="CKT-LIGHTS", slot=1, panel_ref=_PANEL, breaker_amps=15, poles=1,
            afci=True, description="Lighting, both storeys"),
    Circuit(tag="CKT-RECEPT", slot=3, panel_ref=_PANEL, breaker_amps=20, poles=1,
            afci=True, nema="5-20R",
            description="General-purpose receptacles, both storeys"),
    # R314.4 wants the alarms' primary power from the building wiring, which is what
    # naming a circuit says. Unswitched, and shared with nothing that could be turned off
    # at a wall plate.
    Circuit(tag="CKT-ALARMS", slot=5, panel_ref=_PANEL, breaker_amps=15, poles=1,
            afci=True, description="Smoke/CO alarms (R314.4 building wiring)"),
    # The branch MN 1303.2402 subpart 6's junction box will land on when a fan is fitted.
    # `afci=True` because `code.E3902_16_afci` reads ED-RADON-FAN-JB as belonging to
    # RM-Main — the box hangs on that room's exterior wall, and the check places an element
    # by the nearest face it touches. That reading is also the safe one: the homerun runs
    # through habitable space to reach the siding, and AFCI protects the wiring, not only
    # the outlet at the end of it.
    Circuit(tag="CKT-RADON", slot=7, panel_ref=_PANEL, breaker_amps=15, poles=1,
            afci=True, description="Future radon fan (MN 1303.2402 subp. 6)"),
)
