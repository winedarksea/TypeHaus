"""Coating areas the wall walk cannot see: ceilings, opening linings, covered faces.

Paint is resolved, not derived (``resolve/room_paint.py``): every coat a room takes is a
coating layer on a resolved wall, ceiling or lining. Walls bill in ``envelope_layer_takeoff``;
a ceiling's coat bills once here off ``model.ceilings`` (the roof and room-lining loops skip
coatings), and a lining's off ``ResolvedFloor.linings``.
"""

from __future__ import annotations

import math
from collections import defaultdict

from shapely.geometry import Polygon

from typehaus.model.refs import FollowRoof
from typehaus.model.spatial import Roof
from typehaus.resolve.ceiling_over import room_roof_over
from typehaus.resolve.coatings import coating_tags
from typehaus.resolve.model import ResolvedLayer, ResolvedModel, ResolvedWall
from typehaus.resolve.roof_geometry import roof_is_trussed


def covered_paneling_m2(model: ResolvedModel, wall: ResolvedWall,
                        layer: ResolvedLayer) -> float:
    """Paneling (a headboard) that keeps its baseboard, on the face this coating is on.

    The sheet field and its trim include their own enamel, so the wall paint under it is not
    bought; the opposite face keeps its paint.
    """
    (x0, y0), (x1, y1) = wall.axis

    def side(points) -> float:
        return sum((x - x0) * (y1 - y0) - (y - y0) * (x1 - x0) for x, y in points)

    face = side(layer.polygon)
    return sum(band.area_m2 for band in model.panelings
               if band.retains_baseboard and band.wall_tag == wall.tag
               and face * side(band.outline) > 0)


def ceiling_coating_areas(model: ResolvedModel) -> dict[tuple[str, str], float]:
    """``(scope, material) -> m²`` for every resolved ceiling coat and lining coat."""
    coatings = coating_tags(model.plan.library)
    areas: dict[tuple[str, str], float] = defaultdict(float)
    for ceiling in model.ceilings:
        for layer in ceiling.layers:
            if layer.material_ref not in coatings:
                break
            areas[("ceiling", layer.material_ref)] += _ceiling_area_m2(model, ceiling)
    for floor in model.floors:
        for _tag, area, coating in floor.linings:
            if coating is not None:
                areas[("opening lining", coating)] += area
    return areas


def _ceiling_area_m2(model: ResolvedModel, ceiling) -> float:
    """The ceiling's face: its plan outline, sloped where it follows a rafter roof."""
    area = abs(Polygon(ceiling.outline).area)
    room = model.plan.by_tag(ceiling.room_ref)
    if not isinstance(getattr(room, "ceiling", None), FollowRoof):
        return area
    source = room_roof_over(model.plan, ceiling.storey, room)
    roof = next((r for r in model.roofs if source is not None and r.tag == source.tag), None)
    if roof is None or roof_is_trussed(model, roof) or not isinstance(source, Roof):
        return area
    return area * math.sqrt(1.0 + (source.pitch.rise / source.pitch.run) ** 2)
