"""The complete bill of materials: one payload, every section, nothing dropped.

Sections are deliberately parallel rather than merged — a framer orders lumber by size and
type, a concrete sub orders by the yard, and hardware is ordered by part number — but they
are produced together so a caller cannot render half a BOM.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.framing import (
    construction_returns_takeoff,
    framing_bom_by_size,
    framing_takeoff,
    sheet_goods_takeoff,
    structural_solids_takeoff,
)
from typehaus.takeoff.electrical import (
    backup_component_rows,
    conduit_takeoff,
    electrical_device_takeoff,
    panel_schedule,
    service_load_summary,
    solar_takeoff,
)
from typehaus.takeoff.glazing import glazing_panel_takeoff, glazing_trim_takeoff
from typehaus.takeoff.hardware import hardware_takeoff
from typehaus.takeoff.lighting import (connected_lighting_va, light_run_takeoff,
                                       lighting_controls, luminaire_schedule)
from typehaus.takeoff.hardware_config import (
    DEFAULT_HARDWARE_TAKEOFF_CONFIG,
    HardwareTakeoffConfig,
)
from typehaus.takeoff.placeables import floor_heat_takeoff, placeables_takeoff


def bill_of_materials(
    model: ResolvedModel,
    hardware_config: HardwareTakeoffConfig = DEFAULT_HARDWARE_TAKEOFF_CONFIG,
) -> dict:
    """Every BOM section for ``model``.

    ``framing`` is the cut list (one row per size *and* member type, reconciling 1:1 with
    ``model.all_members()``); ``framing_by_size`` rolls it up; ``structural_solids`` covers
    the concrete and standalone structure the member list cannot represent;
    ``construction_returns``, ``sheet_goods`` and ``hardware`` complete the order.
    ``glazing`` covers what none of those could: sheet goods bought as panels rather than as
    sheathing, and the aluminium extrusions that cap them, bought by the lineal foot.
    The ``luminaire_*``/``light_runs``/``lighting_load`` sections are the lighting order:
    fixtures by schedule mark, tape by the lineal foot, and one supply per cove area.
    ``placeables`` counts the free-placed and wall-attached products (casework, appliances,
    fixtures — the UI BOM's placeablesSection twin) and ``floor_heat`` bills each radiant
    zone's element length, so no billable record lives only in a CLI patch or the browser.
    """
    return {
        "framing": framing_takeoff(model),
        "framing_by_size": framing_bom_by_size(model),
        "structural_solids": structural_solids_takeoff(model),
        "construction_returns": construction_returns_takeoff(model),
        "sheet_goods": sheet_goods_takeoff(model),
        "glazing_panels": glazing_panel_takeoff(model),
        "glazing_trim": glazing_trim_takeoff(model),
        "hardware": hardware_takeoff(model, hardware_config),
        "placeables": placeables_takeoff(model),
        "floor_heat": floor_heat_takeoff(model),
        # The electrical program (→ takeoff/electrical.py): devices by type, the panel
        # schedule + NEC 220.82-style service load, raceway LF, the PV array's installed
        # wattage, and the backup subsystem's derived DIN component list.
        "electrical_devices": electrical_device_takeoff(model),
        "panel_schedule": panel_schedule(model),
        "service_load": service_load_summary(model),
        "conduit": conduit_takeoff(model),
        "solar": solar_takeoff(model),
        "backup_components": backup_component_rows(model),
        # The lighting program (→ takeoff/lighting.py): the E-602 schedule by mark, the
        # switch legs, the LED runs with their supplies sized against them, and the real
        # connected load beside the 3 VA/ft2 allowance the service calculation uses.
        "luminaire_schedule": luminaire_schedule(model),
        "lighting_controls": lighting_controls(model),
        "light_runs": light_run_takeoff(model),
        "lighting_load": connected_lighting_va(model),
    }
