"""MEP checks — plumbing, HVAC, electrical (→ Permit-ready plan set Phases 2-3)."""

from __future__ import annotations

from typehaus.checks.mep import (  # noqa: F401 - register
    data,
    deck_equipment,
    drain_geometry,
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
    port_service,
    power_sources,
    routing,
    routing_ceiling,
    routing_openings,
    supply_protection,
    water_heater,
)

__all__: list[str] = []
