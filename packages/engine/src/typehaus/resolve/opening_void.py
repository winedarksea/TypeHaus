"""An opening's void through its host wall: every body layer, or a BLIND one's cut layers only.

The IFC ``IfcOpeningElement`` and the IFC diff adapter both read the void here, so a blind
rough opening (``RoughOpening.depth``) voids exactly the layers the elevation cuts
(:func:`~typehaus.resolve.geometry_walls.cuts_layer`) and leaves its back whole.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import Polygon

from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_walls import cuts_layer
from typehaus.resolve.model import ResolvedLayer, ResolvedWall
from typehaus.resolve.overlay import intersection, union_all


def void_layers(wall: ResolvedWall, opening: Any) -> tuple[ResolvedLayer, ...]:
    """The body layers ``opening`` voids: all of them for a through hole."""
    return tuple(layer for layer in wall.body_layers()
                 if len(layer.polygon) >= 3 and cuts_layer(wall, layer.name, opening))


def void_band(wall: ResolvedWall, opening: Any) -> tuple[float, float] | None:
    """The void's (lo, hi) offset along the wall's left normal, from the axis start."""
    origin, _tangent, (nx, ny), _length = wall_frame(wall)
    offsets = [(p[0] - origin[0]) * nx + (p[1] - origin[1]) * ny
               for layer in void_layers(wall, opening) for p in layer.polygon]
    return (min(offsets), max(offsets)) if offsets else None


def void_span(wall: ResolvedWall, opening: Any) -> tuple[float, float]:
    """The void's (centre offset along the left normal, depth): its voided band.

    Not the axis: a face-aligned wall stands wholly to one side of it.
    """
    band = void_band(wall, opening)
    if band is None:
        return 0.0, wall.thickness_m or 0.15
    return (band[0] + band[1]) / 2, band[1] - band[0]


def void_profile(wall: ResolvedWall, opening: Any) -> list[tuple[float, float]]:
    """The voided layers' real footprint, clipped to the opening's jamb station strip.

    ``[]`` when nothing is left to clip.
    """
    (sx, sy), (tx, ty), (nx, ny), _length = wall_frame(wall)
    start = opening.center_along_m - opening.width_m / 2
    end = opening.center_along_m + opening.width_m / 2
    transverse_extent = max(wall.thickness_m * 4.0, 1.0)

    def point(along: float, across: float) -> tuple[float, float]:
        return (sx + tx * along + nx * across, sy + ty * along + ny * across)

    station_strip = Polygon([
        point(start, -transverse_extent), point(end, -transverse_extent),
        point(end, transverse_extent), point(start, transverse_extent),
    ])
    # On the overlay grid: a lapped sheathing band is snapped to it, so a bare union
    # leaves a 1-ulp seam against its neighbour and max() below keeps only one half.
    # Bodies, not depth: depth keeps a slot's first region only, so a later one drops out.
    host_footprint = union_all(Polygon(layer.polygon) for layer in void_layers(wall, opening))
    clipped = intersection(host_footprint, station_strip)
    polygons = [clipped] if isinstance(clipped, Polygon) else [
        item for item in getattr(clipped, "geoms", ()) if isinstance(item, Polygon)
    ]
    polygons = [item for item in polygons if not item.is_empty]
    if not polygons:
        return []  # the caller falls back to its own segment rectangle
    polygon = max(polygons, key=lambda item: item.area)
    return [(float(x), float(y)) for x, y in list(polygon.exterior.coords)[:-1]]
