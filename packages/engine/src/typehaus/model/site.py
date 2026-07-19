"""Site model: parcel, setbacks, spot elevations, utilities (→ Permit-ready plan set Phase 4).

These are plain value objects nested inside ``Site`` (like ``JoistSpec`` inside
``FloorSystem``) — not independently identified elements, since nothing else references
them by tag.
"""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.model.enums import UtilityKind
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, Point2D


class SetbackSpec(HausModel):
    """A required setback from one parcel edge (``parcel[edge] -> parcel[(edge+1) % n]``)."""

    edge: int
    distance: Length
    label: str = ""  # "FRONT" | "SIDE" | "REAR"


class SpotElevation(HausModel):
    """An authored grade elevation at a point, relative to the main-floor 0 datum."""

    position: Point2D
    elevation: Length


class UtilityLine(HausModel):
    """A utility run from the street/main to a building penetration point."""

    kind: UtilityKind
    path: tuple[Point2D, ...]  # street/main -> entry
    entry: Point2D  # building penetration point
    depth: Length | None = None


for _name, _obj in (
    ("SetbackSpec", SetbackSpec),
    ("SpotElevation", SpotElevation),
    ("UtilityLine", UtilityLine),
):
    register_constructor(_name, _obj)
