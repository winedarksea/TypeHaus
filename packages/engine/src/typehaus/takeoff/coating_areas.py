"""Coating areas the wall walk cannot see: ceilings, opening linings, covered faces.

Paint is resolved, not derived (``resolve/room_paint.py``): every coat a room takes is a
coating layer on a resolved wall, ceiling or lining. Walls bill in ``envelope_layer_takeoff``;
a ceiling's coat bills once here off ``model.ceilings`` (the roof and room-lining loops skip
coatings), and a lining's off ``ResolvedFloor.linings``. A host's authored coat under a face
no Room claims bills as authored (``takeoff/ceiling_areas``).
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.resolve.coatings import coating_tags
from typehaus.resolve.model import ResolvedLayer, ResolvedModel, ResolvedWall
from typehaus.resolve.room_paint import paint_standard, unroomed_coat
from typehaus.takeoff.ceiling_areas import ceiling_area_m2, unroomed_ceilings


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
            areas[("ceiling", layer.material_ref)] += ceiling_area_m2(model, ceiling)
    for floor in model.floors:
        for _tag, area, coating in floor.linings:
            if coating is not None:
                areas[("opening lining", coating)] += area
    # A host's own coat under a face no Room claims (a stair hall): no Room decides it, so
    # it stays as authored, as a wall face with no Room does — save a default coat, which
    # takes the ``PaintStandard``'s ceiling system.
    standard = paint_standard(model.plan)[0]
    for piece in unroomed_ceilings(model):
        for layer in piece.layers:
            if layer.material_ref not in coatings:
                break
            areas[("ceiling", unroomed_coat(standard, layer.material_ref, "ceilings"))] += (
                piece.area_m2)
    return areas
