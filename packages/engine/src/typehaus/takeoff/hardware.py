"""The hardware section of the bill of materials.

One entry point that runs every hardware derivation against the resolved model and returns
BOM rows in a single shape. Nothing here knows a house: the counts come from the resolved
framing, assemblies, construction returns, junctions, and modeled connectors, and the rules
that turn geometry into quantities live in
:class:`~typehaus.takeoff.hardware_config.HardwareTakeoffConfig`.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.anchors import anchorage_rows
from typehaus.takeoff.doors import door_hardware_rows
from typehaus.takeoff.fasteners import (
    exposed_fastener_cladding_screw_rows,
    exterior_insulation_screw_rows,
)
from typehaus.takeoff.glazing import glazing_fastener_rows
from typehaus.takeoff.hangers import joist_hanger_rows, ridge_tie_strap_rows
from typehaus.takeoff.hardware_config import (
    DEFAULT_HARDWARE_TAKEOFF_CONFIG,
    HardwareTakeoffConfig,
)
from typehaus.takeoff.uplift import uplift_rows


def hardware_takeoff(model: ResolvedModel,
                     config: HardwareTakeoffConfig = DEFAULT_HARDWARE_TAKEOFF_CONFIG) -> list:
    """Every critical hardware line item, derived from the resolved model.

    Rows share one schema (see
    :func:`~typehaus.takeoff.hardware_catalog.hardware_row`): what the part is, how many,
    the purchase unit, and the ``basis`` rule that produced the count.
    """
    return [
        *exterior_insulation_screw_rows(model, config.exterior_insulation_fasteners),
        *exposed_fastener_cladding_screw_rows(model, config.exposed_fastener_cladding),
        *joist_hanger_rows(model, config.hanger_detection),
        *ridge_tie_strap_rows(model, config.hanger_detection),
        *uplift_rows(model, config.uplift),
        *anchorage_rows(model, config),
        *glazing_fastener_rows(model),
        *door_hardware_rows(model),
    ]
