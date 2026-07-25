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
from typehaus.takeoff.glazing import glazing_panel_takeoff, glazing_trim_takeoff
from typehaus.takeoff.hardware import hardware_takeoff
from typehaus.takeoff.hardware_config import (
    DEFAULT_HARDWARE_TAKEOFF_CONFIG,
    HardwareTakeoffConfig,
)


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
    }
