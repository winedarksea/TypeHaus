"""Planting and trellises → plants and display solids.

Beds expand into plants here — a grid clipped to its outline, or one plant per planting
pocket in a walk slab — with accents applied by the bed's lattice rule. Every solid is
``derived=True``: drawn by glTF, model.json and the viewer, never measured by the concrete
take-off, sections, IFC or bids. A plant's solid is its bounding and pick record; what draws
is its procedural model (``resolve/plant_models.py``), instanced by the same uid. The
counts live in ``model.plants`` and bill (unpriced) from ``takeoff/planting.py``.
"""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon

from typehaus.findings import Finding
from typehaus.model.enums import FloorOpeningPurpose
from typehaus.model.floors import FloorOpening, Slab
from typehaus.model.landscape import (
    AccentRule,
    GridLayout,
    Plant,
    PlantingBed,
    RainGarden,
    Trellis,
)
from typehaus.resolve.geometry import circle_outline, rect_between
from typehaus.resolve.model import ResolvedModel, ResolvedPlant, ResolvedSolid
from typehaus.resolve.plant_models import (
    build_espalier,
    build_prototype,
    pick_variant,
    prototype_ref,
    role_materials,
)
from typehaus.resolve.rain_garden import surface_z_m

PLANT_CATEGORY = "plant"
TRELLIS_CATEGORY = "trellis"

_PLANT_FACETS = 8
_ESPALIER_THICKNESS_M = 6.0 * 0.0254
_WIRE_SECTION_M = 0.25 * 0.0254
_EPS = 1e-6


def site_grade_m(model: ResolvedModel) -> float:
    grade = model.plan.project.site.grade
    return grade.meters if grade is not None else 0.0


def grid_cells(outline, grid: GridLayout) -> list[tuple[int, int, float, float]]:
    """``(i, j, x, y)`` for every kept grid cell, row-major. Metres, plan frame."""
    polygon = Polygon([p.xy_m if hasattr(p, "xy_m") else p for p in outline])
    if not polygon.is_valid or polygon.area <= 0.0:
        return []
    spacing = grid.spacing.meters
    inset = grid.edge_inset.meters if grid.edge_inset is not None else spacing / 2.0
    minx, miny, maxx, maxy = polygon.bounds
    columns = int(math.floor((maxx - minx - 2 * inset) / spacing + _EPS)) + 1
    rows = int(math.floor((maxy - miny - 2 * inset) / spacing + _EPS)) + 1
    cells = []
    for j in range(max(rows, 0)):
        shift = spacing / 2.0 if grid.stagger and j % 2 else 0.0
        for i in range(max(columns, 0)):
            x = minx + inset + i * spacing + shift
            y = miny + inset + j * spacing
            point = Point(x, y)
            if polygon.contains(point) and polygon.exterior.distance(point) >= inset - _EPS:
                cells.append((i, j, x, y))
    return cells


def accent_type(rule: AccentRule | None, i: int, j: int) -> str | None:
    """The accent type for cell (i, j), or ``None`` for a field plant."""
    if rule is None or not rule.type_refs or rule.every <= 0:
        return None
    value = rule.a * i + rule.b * j
    if value % rule.every != rule.offset % rule.every:
        return None
    return rule.type_refs[(i + j) % len(rule.type_refs)]


def field_ref(bed: PlantingBed, i: int, j: int) -> str:
    """The field type for cell (i, j): the grid's mix on the lattice, else the bed's own."""
    refs = bed.grid.type_refs if bed.grid is not None else ()
    return refs[(i + j) % len(refs)] if refs else bed.type_ref


def pocket_centres(model: ResolvedModel, slab_refs) -> list[tuple[str, float, float, float]]:
    """``(opening tag, x, y, slab top z)`` for every PLANTING opening in the named slabs."""
    plan = model.plan
    tops = {s.tag: s.z1_m for s in model.solids if s.category == "slab"}
    out = []
    for slab_tag in slab_refs:
        slab = plan.by_tag(slab_tag)
        if not isinstance(slab, Slab) or slab_tag not in tops:
            continue
        for tag in slab.openings:
            opening = plan.by_tag(tag)
            if not isinstance(opening, FloorOpening):
                continue
            if opening.purpose is not FloorOpeningPurpose.PLANTING:
                continue
            ring = Polygon([p.xy_m for p in opening.outline])
            out.append((opening.tag, ring.centroid.x, ring.centroid.y, tops[slab_tag]))
    return out


def resolve_landscape(model: ResolvedModel) -> list[Finding]:
    """Append plant and trellis solids, fill ``model.plants`` and ``model.plant_models``."""
    plan = model.plan
    types = {t.tag: t for t in plan.library.plant_types}
    grade = site_grade_m(model)
    trellises: dict[str, Trellis] = {}
    basins = [el for el in plan.all_elements() if isinstance(el, RainGarden)]
    for storey in plan.storeys:
        for element in plan.storey_elements(storey.tag):
            if isinstance(element, Trellis):
                trellises[element.tag] = element
                _resolve_trellis(model, element, storey.tag, grade)
    for storey in plan.storeys:
        for element in plan.storey_elements(storey.tag):
            if isinstance(element, Plant):
                _resolve_specimen(model, element, storey.tag, types, trellises, grade)
            elif isinstance(element, PlantingBed):
                _resolve_bed(model, element, storey.tag, types, grade, basins)
    return []


def _add_plant(model: ResolvedModel, *, uid: str, tag: str, storey: str, ptype, x: float,
               y: float, ground: float, source: str, accent: bool = False) -> None:
    height = ptype.mature_height.meters
    spread = ptype.mature_spread.meters
    model.solids.append(ResolvedSolid(
        uid=uid, tag=tag, storey=storey, category=PLANT_CATEGORY,
        outline=circle_outline((x, y), spread / 2.0, _PLANT_FACETS),
        z0_m=ground, z1_m=ground + height, material=ptype.foliage_material, derived=True))
    variant, rotation, spread_k, height_k = pick_variant(uid)
    ref = prototype_ref(ptype.tag, variant)
    if ref not in model.plant_models:
        model.plant_models[ref] = build_prototype(ptype, variant)
    model.plants.append(ResolvedPlant(
        tag=tag, type_ref=ptype.tag, position=(x, y), ground_z_m=ground, height_m=height,
        spread_m=spread, source_ref=source, accent=accent, uid=uid, storey=storey,
        model_ref=ref, rotation_rad=rotation,
        scale=(spread * spread_k, spread * spread_k, height * height_k),
        material_by_role=tuple(role_materials(ptype).items())))


def _resolve_specimen(model, el: Plant, storey: str, types, trellises, grade: float) -> None:
    ptype = types.get(el.type_ref)
    if ptype is None:
        return  # integrity.plant_type_ref reports it
    ground = el.ground_elevation.meters if el.ground_elevation is not None else grade
    x, y = el.position.xy_m
    trellis = trellises.get(el.trellis_ref or "")
    if el.training != "espalier" or trellis is None:
        _add_plant(model, uid=f"{el.uid}-00", tag=el.tag, storey=storey, ptype=ptype,
                   x=x, y=y, ground=ground, source=el.tag)
        return
    # Espalier: a thin panel in the trellis plane, as wide as the spread, no taller than
    # the frame that trains it; its model is its own, built off the trellis wires.
    start, end = _nearest_segment(trellis, (x, y))
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    spread = ptype.mature_spread.meters
    half = spread / 2.0
    p0, p1 = (x - ux * half, y - uy * half), (x + ux * half, y + uy * half)
    height = min(ptype.mature_height.meters, trellis.post_height.meters)
    t = _ESPALIER_THICKNESS_M / 2.0
    uid = f"{el.uid}-00"
    model.solids.append(ResolvedSolid(
        uid=uid, tag=el.tag, storey=storey, category=PLANT_CATEGORY,
        outline=rect_between(p0, p1, -t, t), z0_m=ground, z1_m=ground + height,
        material=ptype.foliage_material, derived=True))
    proto = build_espalier(uid, ptype.tag, spread_m=spread, height_m=height,
                           wire_heights_m=[w.meters for w in trellis.wire_heights],
                           thickness_m=_ESPALIER_THICKNESS_M,
                           has_fruit=bool(ptype.fruit_material))
    model.plant_models[proto.ref] = proto
    model.plants.append(ResolvedPlant(
        tag=el.tag, type_ref=ptype.tag, position=(x, y), ground_z_m=ground,
        height_m=height, spread_m=spread, source_ref=el.tag, training="espalier", uid=uid,
        storey=storey, model_ref=proto.ref, rotation_rad=math.atan2(uy, ux),
        material_by_role=tuple(role_materials(ptype).items())))


def _basin_under(bed: PlantingBed, basins) -> RainGarden | None:
    """The rain garden whose rim holds the whole bed, if any."""
    ring = Polygon([p.xy_m for p in bed.outline])
    for basin in basins:
        rim = Polygon([p.xy_m for p in basin.outline])
        if ring.is_valid and rim.is_valid and rim.buffer(_EPS).covers(ring):
            return basin
    return None


def _resolve_bed(model, bed: PlantingBed, storey: str, types, grade: float, basins) -> None:
    if bed.grid is not None:
        ground = bed.ground_elevation.meters if bed.ground_elevation is not None else grade
        basin = _basin_under(bed, basins)
        for i, j, x, y in grid_cells(bed.outline, bed.grid):
            accent = accent_type(bed.accents, i, j)
            ptype = types.get(accent or field_ref(bed, i, j))
            if ptype is None:
                continue
            # Inside a basin a plant stands on the basin's own surface, slope or floor.
            z = surface_z_m(basin, x, y) if basin is not None else None
            _add_plant(model, uid=f"{bed.uid}-G{i:03d}{j:03d}", tag=f"{bed.tag}-{i:02d}-{j:02d}",
                       storey=storey, ptype=ptype, x=x, y=y,
                       ground=ground if z is None else z, source=bed.tag,
                       accent=accent is not None)
    elif bed.pockets is not None:
        cycle = bed.pockets.type_refs or (bed.type_ref,)
        for n, (opening, x, y, top) in enumerate(pocket_centres(model, bed.pockets.slab_refs)):
            ptype = types.get(cycle[n % len(cycle)])
            if ptype is None:
                continue
            _add_plant(model, uid=f"{bed.uid}-P{n:03d}", tag=f"{bed.tag}-{opening}",
                       storey=storey, ptype=ptype, x=x, y=y, ground=top, source=bed.tag)


def trellis_post_stations(trellis: Trellis) -> list[tuple[float, float]]:
    """Post centres: evenly spaced along the path, no bay longer than ``post_spacing``."""
    path = [p.xy_m for p in trellis.path]
    spans = [math.dist(a, b) for a, b in zip(path[:-1], path[1:], strict=True)]
    total = sum(spans)
    if total <= 0.0:
        return path[:1]
    bays = max(1, math.ceil(total / trellis.post_spacing.meters - _EPS))
    return [_point_at(path, spans, total * k / bays) for k in range(bays + 1)]


def _point_at(path, spans, distance: float) -> tuple[float, float]:
    run = 0.0
    for (a, b), span in zip(zip(path[:-1], path[1:], strict=True), spans, strict=True):
        if run + span >= distance - _EPS and span > 0.0:
            ratio = min(max((distance - run) / span, 0.0), 1.0)
            return (a[0] + (b[0] - a[0]) * ratio, a[1] + (b[1] - a[1]) * ratio)
        run += span
    return path[-1]


def _dressed_m(nominal: str) -> float:
    """``"4x4"`` → 3.5" square. Lumber dresses 1/2" under nominal at these sizes."""
    try:
        size = float(nominal.lower().split("x")[0])
    except ValueError:
        size = 4.0
    return (size - 0.5) * 0.0254


def _resolve_trellis(model, el: Trellis, storey: str, grade: float) -> None:
    ground = el.ground_elevation.meters if el.ground_elevation is not None else grade
    half = _dressed_m(el.post) / 2.0
    for k, (x, y) in enumerate(trellis_post_stations(el)):
        model.solids.append(ResolvedSolid(
            uid=f"{el.uid}-P{k:02d}", tag=f"{el.tag}-P{k + 1}", storey=storey,
            category=TRELLIS_CATEGORY,
            outline=[(x - half, y - half), (x + half, y - half), (x + half, y + half),
                     (x - half, y + half)],
            z0_m=ground - el.post_embed.meters, z1_m=ground + el.post_height.meters,
            material=el.post_material, derived=True))
    path = [p.xy_m for p in el.path]
    w = _WIRE_SECTION_M / 2.0
    for n, height in enumerate(el.wire_heights):
        z = ground + height.meters
        for s, (a, b) in enumerate(zip(path[:-1], path[1:], strict=True)):
            if a == b:
                continue
            model.solids.append(ResolvedSolid(
                uid=f"{el.uid}-W{n}{s:02d}", tag=f"{el.tag}-W{n + 1}", storey=storey,
                category=TRELLIS_CATEGORY, outline=rect_between(a, b, -w, w),
                z0_m=z - w, z1_m=z + w, derived=True))


def _nearest_segment(trellis: Trellis, point) -> tuple[tuple[float, float], tuple[float, float]]:
    from shapely.geometry import LineString

    path = [p.xy_m for p in trellis.path]
    best = (path[0], path[-1])
    best_d = math.inf
    for a, b in zip(path[:-1], path[1:], strict=True):
        d = LineString([a, b]).distance(Point(point))
        if d < best_d and a != b:
            best, best_d = (a, b), d
    return best
