"""A rain garden's basin geometry: floor ring and ponding volume, read by resolve and checks.

The rim ring is authored; the floor is the rim inset by ``side_slope × ponding depth``.
Ponding volume is the prismoidal formula over rim, mid-depth and floor areas — exact for
a basin whose sides are planes at one slope.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.model.landscape import RainGarden


def _polygon(el: RainGarden) -> Polygon:
    return Polygon([p.xy_m for p in el.outline])


def ponding_depth_m(el: RainGarden) -> float:
    """Floor to the overflow lip (the rim when no lower overflow is authored)."""
    floor = el.rim_elevation.meters - el.ponding_depth.meters
    lip = el.rim_elevation.meters
    if el.overflow_invert is not None:
        lip = min(lip, el.overflow_invert.meters)
    return max(lip - floor, 0.0)


def floor_z_m(el: RainGarden) -> float:
    return el.rim_elevation.meters - el.ponding_depth.meters


def _inset(polygon: Polygon, distance: float) -> Polygon:
    shrunk = polygon.buffer(-distance, join_style="mitre")
    return shrunk if not shrunk.is_empty else Polygon()


def floor_ring(el: RainGarden) -> list[tuple[float, float]]:
    """The basin floor in plan; empty when the slopes meet before reaching the floor."""
    shrunk = _inset(_polygon(el), el.side_slope * el.ponding_depth.meters)
    if shrunk.is_empty or shrunk.geom_type != "Polygon":
        return []
    return [(x, y) for x, y in shrunk.exterior.coords[:-1]]


def ponding_volume_m3(el: RainGarden) -> float:
    """Water held between the floor and the overflow lip, prismoidal."""
    rim = _polygon(el)
    if not rim.is_valid or rim.area <= 0.0:
        return 0.0
    depth = ponding_depth_m(el)
    full = el.ponding_depth.meters
    run = el.side_slope
    # Areas at the floor, at mid-water and at the water surface, all measured as insets of
    # the rim by the slope run at that height below the rim.
    bottom = _inset(rim, run * full).area
    top = _inset(rim, run * (full - depth)).area
    mid = _inset(rim, run * (full - depth / 2.0)).area
    return depth / 6.0 * (top + 4.0 * mid + bottom)
