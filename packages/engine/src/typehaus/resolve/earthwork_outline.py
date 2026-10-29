"""The dug structures' outer outline, shared by the drain column and the over-dig.

The interior of a dig is derived the way ``site_earth`` derives the earth sheet's voids: a
below-grade floor is the bottom of a hole. The outline is those floors plus the bodies of
the bedded walls standing around them, closed across small gaps (an isolation joint between
a court wall and the house) and with holes filled. Its exterior is the soil side — the outer
face of the foundation's XPS and coating.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import JOIN_STYLE, MultiPolygon, Polygon

from typehaus.resolve.model import ResolvedFootingBedding, ResolvedModel, ResolvedWall
from typehaus.resolve.overlay import union_all
from typehaus.resolve.site_earth import heated_floor_footprint, open_excavation_floors

#: How near a bed a floor must lie, and a wall body a floor, to be part of the same dig.
_BED_REACH_M = 0.3
_WALL_REACH_M = 0.05
#: Closes joints up to twice this wide between walls that read as one enclosure.
_CLOSING_M = 0.15
_MITRE = JOIN_STYLE.mitre


def polygon_of(ring) -> Polygon | None:
    if len(ring) < 3:
        return None
    polygon = Polygon(ring)
    return polygon if polygon.is_valid and polygon.area > 0.0 else None


def host_wall(model: ResolvedModel, bed: ResolvedFootingBedding) -> ResolvedWall | None:
    """The wall a bed serves: its host if a wall, else the wall its footing is under."""
    wall = model.wall(bed.host)
    if wall is not None:
        return wall
    under = getattr(model.plan.by_tag(bed.host), "under", None)
    return model.wall(under) if under else None


def wall_body(wall: ResolvedWall) -> Any | None:
    parts = [p for layer in wall.layers if (p := polygon_of(layer.polygon)) is not None]
    return union_all(parts) if parts else None


def dug_outline(model: ResolvedModel) -> Any | None:
    """Filled plan outline of every below-grade enclosure a bed stands around, or None."""
    beds = [p for b in model.footing_beddings if (p := polygon_of(b.outline)) is not None]
    if not beds:
        return None
    bed_zone = union_all(beds).buffer(_BED_REACH_M)
    floors = [polygon for _tag, polygon, _top in open_excavation_floors(model)]
    heated = heated_floor_footprint(model)
    if heated is not None and not heated.is_empty:
        floors.append(heated)
    floors = [f for f in floors if f.intersects(bed_zone)]
    if not floors:
        return None
    floor_union = union_all(floors)
    bodies = []
    for bed in model.footing_beddings:
        wall = host_wall(model, bed)
        body = wall_body(wall) if wall is not None else None
        if body is not None and body.distance(floor_union) <= _WALL_REACH_M:
            bodies.append(body)
    merged = union_all([floor_union, *bodies])
    closed = merged.buffer(_CLOSING_M, join_style=_MITRE).buffer(-_CLOSING_M, join_style=_MITRE)
    parts = closed.geoms if isinstance(closed, MultiPolygon) else [closed]
    filled = [Polygon(part.exterior) for part in parts if not part.is_empty]
    return union_all(filled) if filled else None
