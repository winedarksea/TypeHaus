"""Site-plan drawing IR derived from the shared project coordinate frame."""

from __future__ import annotations

from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Text
from typehaus.resolve.model import ResolvedModel

M_TO_IN = 39.37007874015748


def build_site_plan(model: ResolvedModel) -> Scene:
    """Show every freestanding footprint together instead of reusing a floor plan for C-101.

    A house can intentionally contain disconnected structures. The site sheet projects
    footprints in their shared north-coordinate frame; it does not infer that the garage,
    garden, or breezeway belong to the main building envelope.
    """
    builder = SceneBuilder(name="site-plan", units="in")
    _emit_roofs_or_wall_footprints(builder, model)
    _emit_foundation_and_post_supports(builder, model)
    _emit_north_arrow(builder, model)
    return builder.build()


def _emit_roofs_or_wall_footprints(builder: SceneBuilder, model: ResolvedModel) -> None:
    roofs_by_storey = {roof.storey for roof in model.roofs}
    for roof in model.roofs:
        builder.add(Polyline(points=tuple(_in(point) for point in roof.footprint), closed=True,
                             layer="A-SITE-ROOF", lineweight=0.6, uid=roof.uid, tag=roof.tag))
        _label(builder, roof.tag, roof.footprint)

    # A freestanding concrete garden can have no roof. The lowest wall loop provides its
    # honest footprint, while roofed storeys avoid redundant wall outlines.
    for wall in model.walls:
        if wall.storey in roofs_by_storey or wall.storey not in {"basement", "main", "garage"}:
            continue
        builder.add(Polyline(points=(_in(wall.axis[0]), _in(wall.axis[1])), layer="A-SITE-WALL",
                             lineweight=0.45, uid=wall.uid, tag=wall.tag))


def _emit_foundation_and_post_supports(builder: SceneBuilder, model: ResolvedModel) -> None:
    for solid in model.solids:
        if solid.category not in {"footing", "pad"}:
            continue
        builder.add(Polyline(points=tuple(_in(point) for point in solid.outline), closed=True,
                             layer="A-SITE-FOUND", lineweight=0.3, uid=solid.uid, tag=solid.tag))


def _emit_north_arrow(builder: SceneBuilder, model: ResolvedModel) -> None:
    points = [point for wall in model.walls for point in wall.axis]
    if not points:
        return
    min_x, max_y = min(point[0] for point in points), max(point[1] for point in points)
    origin = (min_x - 2.0, max_y - 1.0)
    import math

    radians = model.plan.project.site.true_north.radians
    tip = (origin[0] + math.sin(radians) * 3.0, origin[1] + math.cos(radians) * 3.0)
    builder.add(Polyline(points=(_in(origin), _in(tip)), layer="A-SITE-ANNO", lineweight=0.7))
    builder.add(Text(anchor=_in((tip[0], tip[1] + 0.4)), content="N", height=4.0,
                     layer="A-SITE-ANNO", align="center"))


def _label(builder: SceneBuilder, tag: str, footprint: list[tuple[float, float]]) -> None:
    if not footprint:
        return
    x = sum(point[0] for point in footprint) / len(footprint)
    y = sum(point[1] for point in footprint) / len(footprint)
    builder.add(Text(anchor=_in((x, y)), content=tag, height=3.5, layer="A-SITE-ANNO",
                     align="center"))


def _in(point: tuple[float, float]) -> tuple[float, float]:
    return point[0] * M_TO_IN, point[1] * M_TO_IN
