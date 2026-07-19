"""Site-plan drawing IR derived from the shared project coordinate frame (→ 20).

Real C-101: parcel ring, setback lines + dimensions, utility runs, spot elevations, and
downhill drainage arrows, layered on top of the existing footprint/footing/north-arrow
content (→ Permit-ready plan set Phase 4).
"""

from __future__ import annotations

import math

from typehaus.emit.draw.scene import (
    ArchDimension,
    NamedPoint,
    Polyline,
    Scene,
    SceneBuilder,
    Symbol,
    Text,
)
from typehaus.resolve.model import ResolvedModel

M_TO_IN = 39.37007874015748
_DRAINAGE_RADIUS_FT = 40.0


def build_site_plan(model: ResolvedModel) -> Scene:
    """Show every freestanding footprint together instead of reusing a floor plan for C-101.

    A house can intentionally contain disconnected structures. The site sheet projects
    footprints in their shared north-coordinate frame; it does not infer that the garage,
    garden, or breezeway belong to the main building envelope.
    """
    builder = SceneBuilder(name="site-plan", units="in")
    _emit_roofs_or_wall_footprints(builder, model)
    _emit_foundation_and_post_supports(builder, model)
    site = model.plan.project.site
    _emit_parcel_and_setbacks(builder, model, site)
    _emit_utilities(builder, site)
    _emit_spot_elevations_and_drainage(builder, site)
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


def _emit_parcel_and_setbacks(builder: SceneBuilder, model: ResolvedModel, site) -> None:
    parcel = [p.xy_m for p in site.parcel]
    if len(parcel) < 3:
        return
    builder.add(Polyline(points=tuple(_in(p) for p in parcel), closed=True, layer="C-PROP",
                         lineweight=0.5, linetype="PHANTOM"))
    n = len(parcel)
    footprint_pts = [p for wall in model.walls for p in (wall.axis[0], wall.axis[1])]
    for spec in site.setbacks:
        a, b = parcel[spec.edge % n], parcel[(spec.edge + 1) % n]
        offset_a, offset_b = _offset_edge(a, b, spec.distance.meters)
        builder.add(Polyline(points=(_in(offset_a), _in(offset_b)), layer="C-PROP-SETB",
                             lineweight=0.3, linetype="DASHED"))
        mid = ((offset_a[0] + offset_b[0]) / 2, (offset_a[1] + offset_b[1]) / 2)
        builder.add(Text(anchor=_in(mid), content=f"{spec.label} SETBACK", height=2.5,
                         layer="C-PROP-SETB", align="center"))
        nearest = _nearest_point_to_edge(footprint_pts, a, b)
        if nearest is not None:
            foot = _project_onto_segment(nearest, a, b)
            builder.add(ArchDimension(
                kind="linear", ends=(NamedPoint(xy=_in(foot), name="setback-edge"),
                                     NamedPoint(xy=_in(nearest), name="setback-pt")),
                p0=_in(foot), p1=_in(nearest), offset=0.0,
            ))


def _emit_utilities(builder: SceneBuilder, site) -> None:
    for line in site.utilities:
        path = [p.xy_m for p in line.path]
        if len(path) < 2:
            continue
        layer = f"C-UTIL-{line.kind.value.upper()}"
        builder.add(Polyline(points=tuple(_in(p) for p in path), layer=layer,
                             lineweight=0.3, linetype="DASHED"))
        entry = line.entry.xy_m
        builder.add(Symbol(name="utility-entry", insert=_in(entry), layer=layer))
        builder.add(Text(anchor=_in((entry[0] + 0.5, entry[1] + 0.5)),
                         content=line.kind.value.upper(), height=2.0, layer=layer))


def _emit_spot_elevations_and_drainage(builder: SceneBuilder, site) -> None:
    spots = [(spot.position.xy_m, spot.elevation.meters) for spot in site.spot_elevations]
    for (x, y), elevation_m in spots:
        builder.add(Symbol(name="spot-elev", insert=_in((x, y)), layer="A-SITE-ANNO"))
        elevation_ft = elevation_m * 3.280839895
        sign = "+" if elevation_ft >= 0 else "-"
        builder.add(Text(anchor=_in((x + 0.3, y + 0.3)),
                         content=f"EL. {sign}{abs(elevation_ft):.1f}'", height=2.0,
                         layer="A-SITE-ANNO"))
    radius_m = _DRAINAGE_RADIUS_FT * 0.3048
    for (x, y), elevation_m in spots:
        candidates = [
            ((ox, oy), oe) for (ox, oy), oe in spots
            if oe < elevation_m - 1e-6 and math.hypot(ox - x, oy - y) <= radius_m
        ]
        if not candidates:
            continue
        (dx, dy), _ = min(candidates, key=lambda item: math.hypot(item[0][0] - x, item[0][1] - y))
        builder.add(Polyline(points=(_in((x, y)), _in((dx, dy))), layer="C-TOPO-ARRW",
                             lineweight=0.25))
        builder.add(Symbol(name="span-arrow", insert=_in(((x + dx) / 2, (y + dy) / 2)),
                           rotation=math.degrees(math.atan2(dy - y, dx - x)), scale=12.0,
                           layer="C-TOPO-ARRW"))


def _emit_north_arrow(builder: SceneBuilder, model: ResolvedModel) -> None:
    points = [point for wall in model.walls for point in wall.axis]
    if not points:
        return
    min_x, max_y = min(point[0] for point in points), max(point[1] for point in points)
    origin = (min_x - 2.0, max_y - 1.0)
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


def _offset_edge(a: tuple[float, float], b: tuple[float, float],
                 distance: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """Offset a CCW parcel edge inward by ``distance`` (left-hand normal of CCW = inward)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length  # rotate -90° (CCW ring -> inward normal)
    return ((a[0] + nx * distance, a[1] + ny * distance),
           (b[0] + nx * distance, b[1] + ny * distance))


def _nearest_point_to_edge(points: list[tuple[float, float]], a: tuple[float, float],
                           b: tuple[float, float]) -> tuple[float, float] | None:
    if not points:
        return None
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy or 1.0
    best, best_dist = None, float("inf")
    for p in points:
        t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length2
        foot = (a[0] + t * dx, a[1] + t * dy)
        dist = math.hypot(p[0] - foot[0], p[1] - foot[1])
        if dist < best_dist:
            best_dist, best = dist, p
    return best


def _project_onto_segment(point: tuple[float, float], a: tuple[float, float],
                          b: tuple[float, float]) -> tuple[float, float]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy or 1.0
    t = ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length2
    return (a[0] + t * dx, a[1] + t * dy)


def _in(point: tuple[float, float]) -> tuple[float, float]:
    return point[0] * M_TO_IN, point[1] * M_TO_IN
