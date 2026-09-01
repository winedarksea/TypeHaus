"""MEP checks — plumbing, HVAC, electrical (→ Permit-ready plan set Phases 2-3)."""

from __future__ import annotations

from typehaus.checks.mep import (  # noqa: F401 - register
    data,
    deck_equipment,
    drainage,
    duct_connectivity,
    electrical,
    electrical_code,
    electrical_receptacles,
    erv_terminals,
    exhaust,
    hvac,
    lighting,
    plumbing,
    pockets,
    power_sources,
    routing,
    supply_protection,
    water_heater,
)

__all__: list[str] = []
