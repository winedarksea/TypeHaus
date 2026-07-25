"""Take-offs derived from the resolved model: framing, sheet goods, solids, and hardware.

Public surface only — the derivations live in focused sibling modules:

- :mod:`typehaus.takeoff.framing` — the lumber cut list, its rollups, sheet goods, the
  construction-return laps, and the resolved structural solids.
- :mod:`typehaus.takeoff.glazing` — glazing panels by the sheet, their extrusions by the
  lineal foot, and the gasketed fixings that hold them.
- :mod:`typehaus.takeoff.hardware` — the critical connection hardware, with its rules in
  :mod:`typehaus.takeoff.hardware_config` and its parts in ``library/hardware.py``.
- :mod:`typehaus.takeoff.bom` — every section at once.
"""

from __future__ import annotations

from typehaus.takeoff.bom import bill_of_materials
from typehaus.takeoff.electrical import (
    backup_component_rows,
    conduit_takeoff,
    panel_schedule,
    service_load_summary,
    solar_takeoff,
)
from typehaus.takeoff.framing import (
    _board_feet_per_ft,
    _order_length_ft,
    construction_returns_takeoff,
    framing_bom_by_size,
    framing_takeoff,
    sheet_goods_takeoff,
    structural_solids_takeoff,
)
from typehaus.takeoff.glazing import (
    glazing_fastener_rows,
    glazing_panel_takeoff,
    glazing_trim_takeoff,
)
from typehaus.takeoff.hardware import hardware_takeoff
from typehaus.takeoff.hardware_config import (
    DEFAULT_HARDWARE_TAKEOFF_CONFIG,
    HardwareTakeoffConfig,
)
from typehaus.takeoff.placeables import floor_heat_takeoff, placeables_takeoff

__all__ = [
    "glazing_panel_takeoff", "glazing_trim_takeoff", "glazing_fastener_rows",
    "backup_component_rows", "conduit_takeoff", "panel_schedule", "service_load_summary",
    "solar_takeoff",
    "bill_of_materials",
    "construction_returns_takeoff",
    "floor_heat_takeoff",
    "framing_bom_by_size",
    "framing_takeoff",
    "hardware_takeoff",
    "placeables_takeoff",
    "sheet_goods_takeoff",
    "structural_solids_takeoff",
    "DEFAULT_HARDWARE_TAKEOFF_CONFIG",
    "HardwareTakeoffConfig",
    # Re-exported for the take-off unit tests, which exercise the ordering/board-foot rules.
    "_board_feet_per_ft",
    "_order_length_ft",
]
