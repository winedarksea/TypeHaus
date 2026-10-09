"""Supporting floor datum for complete winder platforms."""

from __future__ import annotations

from typehaus.model.floors import FloorSystem, Slab
from typehaus.model.spatial import Stair
from typehaus.resolve.model import ResolvedModel


def winder_supporting_floor(model: ResolvedModel, stair: Stair, finished_base: float) -> float:
    """Seat the first platform on structural subfloor, keeping the oak step datum."""
    from shapely.geometry import Point, Polygon

    origin = Point(stair.start.xy_m) if stair.start else None
    source = model.plan.storey(stair.from_storey)
    candidates = []
    for element in model.plan.storey_elements(stair.from_storey):
        if isinstance(element, FloorSystem):
            if element.outline and origin is not None and not Polygon(
                    [p.xy_m for p in element.outline]).covers(origin):
                continue
            top = element.top_elevation.meters if element.top_elevation else source.elevation.meters
            plywood = element.subfloor.thickness.meters if element.subfloor else 0.0
            candidates.append(top + plywood)
        elif isinstance(element, Slab):
            candidates.append(element.top_elevation.meters if element.top_elevation
                              else source.elevation.meters)
    below = [top for top in candidates if top <= finished_base + 1e-7]
    return max(below) if below else finished_base
