"""The over-dig (``Excavation``): cut, backfill and cap, sliced level by level.

At elevation z the hole is the union of
  * the dug outline (``earthwork_outline``) above the hosted footings' tops, and every floor
    solid inside it (slab, base course, field band) and every sump or trench below them,
    from its own underside — the interiors;
  * every hosted bed's footprint from its stone floor;
  * the perimeter dig: each bed's column and bed, buffered out by ``working_space`` plus
    ``h_per_v`` x (z - floor), less the outline so the slope never eats inward.
Each bed's dig stops at its own strip grade; the interiors at the site grade.

Fill at z is the hole less everything standing in it (the outline, beds, columns, footings,
pads, slabs, walls, planting fill). Its top ``cap_thickness`` under each bed's grade is cap.
The level prisms drawn ARE the prisms measured, so drawing and billing cannot disagree.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import JOIN_STYLE, Polygon

from typehaus.findings import Finding
from typehaus.model.excavation import Excavation
from typehaus.resolve.earthwork_outline import dug_outline, polygon_of, wall_body
from typehaus.resolve.excavation_slices import Hole, slice_hole
from typehaus.resolve.excavation_slices import levels as _levels
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.model_earthwork import ResolvedExcavation
from typehaus.resolve.overlay import intersection, union_all
from typehaus.resolve.site_earth import (
    grade_strip,
    open_excavation_floors,
    site_grade_elevation_m,
    strip_grade_elevation_m,
)
from typehaus.resolve.solid_categories import SOLID_CATEGORIES
from typehaus.resolve.wall_column import CATEGORY as COLUMN
from typehaus.resolve.wall_column import footing_top, soil_face

_MITRE = JOIN_STYLE.mitre
_FLOORISH = frozenset({"sub_slab"})
_POCKETS = frozenset({"sump", "french_drain"})
#: What stands in the hole and displaces fill. Thin runs (pipe, tile, conduit) do not count.
_OBSTACLES = frozenset({"sub_slab", "beam", "column", "pad", "footing", COLUMN,
                        "planting_fill", "planting_soil", "drywell", "sump", "thermal_break",
                        "rain_garden_media", "rain_garden_stone", "french_drain"})
_INSIDE = 0.9


def _floorish(category: str) -> bool:
    row = SOLID_CATEGORIES.get(category)
    return category in _FLOORISH or (row is not None and row.slab_family == "slab")


def _obstacle(category: str) -> bool:
    row = SOLID_CATEGORIES.get(category)
    return category in _OBSTACLES or (row is not None and (row.is_pour or bool(row.slab_family)))


def _filled(solid: ResolvedSolid) -> Polygon | None:
    """A solid's plan with its voids filled: a planting pocket in a walk base is not backfill."""
    return polygon_of(solid.outline)


def resolve_excavations(model: ResolvedModel) -> list[Finding]:
    authored = [(storey.tag, el) for storey in model.plan.storeys
                for el in model.plan.storey_elements(storey.tag) if isinstance(el, Excavation)]
    if not authored:
        return []
    outline = dug_outline(model)
    if outline is None:
        return []
    for storey, element in authored:
        _resolve(model, element, storey, outline)
    return []


def _resolve(model: ResolvedModel, exc: Excavation, storey: str, outline: Any) -> None:
    beds = {b.tag: b for b in model.footing_beddings}
    hosted = [beds[t] for t in exc.hosts if t in beds]
    if not hosted:
        return
    grade = site_grade_elevation_m(model)
    ws, slope = exc.working_space.meters, exc.side_slope.h_per_v
    cap_t = exc.cap_thickness.meters
    floors = open_excavation_floors(model)
    columns: dict[str, list[Polygon]] = {}
    for solid in model.solids:
        if solid.category == COLUMN and (p := _filled(solid)) is not None:
            columns.setdefault(solid.uid.rsplit("-DC-", 1)[0], []).append(p)
    digs = []  # (core, floor, top, sloped): an interior bed is only its own trench
    for bed in sorted(hosted, key=lambda b: b.uid):
        own = polygon_of(bed.outline)
        if own is None:
            continue
        face = soil_face(model, bed, outline)
        top = (strip_grade_elevation_m(model, grade_strip(face[2], face[3]), floors)[0]
               if face is not None else grade)
        digs.append((union_all([own, *columns.get(bed.uid, [])]), bed.stone_z0_m, top,
                     face is not None))
    z_struct = max(footing_top(model, b) for b in hosted)
    floor = min(d[1] for d in digs)
    roof = max([d[2] for d in digs] + [grade])
    extent = union_all([outline, *(core.buffer(ws + slope * (roof - f), join_style=_MITRE)
                                   for core, f, _top, _sloped in digs)])
    x0, y0, x1, y1 = extent.bounds

    def near(z0: float, z1: float, ring) -> bool:
        return (z1 > floor and z0 < roof and len(ring) >= 3
                and min(p[0] for p in ring) < x1 and max(p[0] for p in ring) > x0
                and min(p[1] for p in ring) < y1 and max(p[1] for p in ring) > y0)

    interiors, obstacles = [], []
    for solid in model.solids:
        floorish = solid.z1_m <= grade + 0.02 and (
            _floorish(solid.category) or solid.category in _POCKETS)
        if not (floorish or _obstacle(solid.category)) or not near(
                solid.z0_m, solid.z1_m, solid.outline):
            continue
        net = _filled(solid)
        if net is None:
            continue
        if floorish and intersection(net, outline).area >= _INSIDE * net.area:
            interiors.append((net, solid.z0_m))
        if _obstacle(solid.category):
            obstacles.append((net, solid.z0_m, solid.z1_m))
    for bed in model.footing_beddings:
        if near(bed.stone_z0_m, bed.z1_m, bed.outline) and (p := polygon_of(bed.outline)):
            obstacles.append((p, bed.stone_z0_m, bed.z1_m))
    for wall in model.walls:
        ring = [p for layer in wall.layers for p in layer.polygon]
        if near(wall.z0_m, wall.z1_m, ring) and (body := wall_body(wall)) is not None:
            obstacles.append((body, wall.z0_m, wall.z1_m))
    floor = min([floor] + [z for _p, z in interiors])
    grouped: dict[tuple[float, float], list[Any]] = {}
    for polygon, a, b in obstacles:  # one union per shared z range, not per slice
        if polygon.intersects(extent):
            grouped.setdefault((a, b), []).append(polygon)
    obstacles = [(union_all(ps), a, b) for (a, b), ps in grouped.items()]
    levels = _levels(floor, roof, exc.draw_step.meters,
                     [z for d in digs for z in (d[1], d[2], d[2] - cap_t)]
                     + [z for _p, z in interiors] + [z_struct]
                     + [z for _p, a, b in obstacles if floor < a < roof or floor < b < roof
                        for z in (a, b)])
    hole = Hole(outline, digs, interiors, obstacles, grade, z_struct, ws, slope, cap_t)
    cut, fill, cap, prisms = slice_hole(hole, levels)
    solids = [ResolvedSolid(
        uid=f"{exc.uid}-BF-{n:03d}", tag=f"{exc.tag}-BF-{n + 1}", storey=storey,
        category=category, outline=list(part.exterior.coords)[:-1], z0_m=za, z1_m=zb,
        voids=tuple(list(r.coords)[:-1] for r in part.interiors))
        for n, (category, part, za, zb) in enumerate(prisms)]
    model.solids.extend(solids)
    tags = {b.tag for b in hosted}
    model.excavations.append(ResolvedExcavation(
        uid=exc.uid, tag=exc.tag, hosts=tuple(sorted(tags)), floor_m=floor, top_m=roof,
        cut_bank_m3=cut, fill_m3=fill, cap_m3=cap,
        column_m3=sum(c.volume_m3 for c in model.wall_columns if c.bed_tag in tags),
        swell=exc.swell.fraction, shrink=exc.shrink.fraction, cap_material=exc.cap_material,
        lift_m=exc.lift.meters))

