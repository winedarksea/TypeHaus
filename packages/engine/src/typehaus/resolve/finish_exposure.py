"""Room occupancy and axis cells used to decide whether exposed gypsum takes paint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shapely.geometry import Polygon
from shapely.prepared import PreparedGeometry, prep

from typehaus.model.enums import Occupancy
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

if TYPE_CHECKING:
    from typehaus.resolve.model import ResolvedModel

FACE_PROBE_M = 0.0254
MIN_ROOM_Z_OVERLAP_M = 0.3
UsedRoom = tuple[Polygon, PreparedGeometry, float, float]


def used_rooms(model: ResolvedModel) -> list[UsedRoom]:
    """Axis cell, prepared cell, and occupied height band for each conditioned room."""
    storeys = {storey.tag: storey for storey in model.plan.storeys}
    out = []
    for room in model.rooms:
        storey = storeys.get(room.storey)
        if (storey is None or room.occupancy == Occupancy.UNCONDITIONED.value
                or len(axis_ring(room)) < 3):
            continue
        face = axis_polygon(room)
        z0 = storey.elevation.meters
        out.append((face, prep(face), z0, z0 + storey.default_ceiling_height.meters))
    return out
