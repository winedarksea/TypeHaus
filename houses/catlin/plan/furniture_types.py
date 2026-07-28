"""House-local furniture catalog for items specific to the Catlin plan."""

from __future__ import annotations

from typehaus import FurnitureType, inch


GARAGE_WORKBENCH = FurnitureType(
    tag="FURN-G-WORKBENCH",
    name="Garage workbench, 60 x 30 x 34 in",
    footprint=(inch(60), inch(30)),
    height=inch(34),
    plan_symbol="desk",
    source="Catlin owner requirement: 60 x 30 x 34 in workbench",
)

FURNITURE_TYPES = (GARAGE_WORKBENCH,)
