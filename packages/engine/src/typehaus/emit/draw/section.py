"""Section/detail slice → drawing IR (M3, → 30 §Details, → 11b §Slices).

A ``Slice(kind=SECTION|DETAIL)`` cuts the resolved model with a vertical plane:
``cut_direction="x"`` cuts along the x axis at ``cut_origin.y`` (section coords
u = world x), ``"y"`` cuts along y at ``cut_origin.x`` (u = world y); v is world z.
Cut geometry only (poché) — projection beyond the plane is the elevations' job
(→ 30 §Elevations). ``crop`` is interpreted in section coordinates: (u, z) pairs.

Everything drawn comes from the ResolvedModel: per-layer wall polygons intersected
with the cut line, slabs/footings/pads, sloped roof bands, joists crossing the cut,
and opening voids. Thin layers honor ``ExaggerationSpec`` with true-dimension labels.
"""

from __future__ import annotations

from typehaus.model.views import Slice
from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.emit.draw.scene import Hatch, Polyline, Scene, SceneBuilder, Text

M_TO_IN = 39.37007874015748

_FUNCTION_LAYER = {
    "structure": "A-WALL",
    "sheathing": "A-WALL",
    "cladding": "A-WALL",
    "finish": "A-WALL-FINI",
    "insulation": "A-WALL-INSU",
    "membrane": "A-WALL-PATT",
    "airgap": "A-WALL-PATT",
    "furring": "A-WALL",
}
_HATCH_PATTERN = {
    "insulation": "batt",
    "sheathing": "osb",
    "structure": "lumber",
    "cladding": "SOLID",
}


def _ring_cut_intervals(ring, direction: str, station: float) -> list[tuple[float, float]]:
    """Intersect a plan-frame ring with the cut line -> sorted u-intervals (even-odd)."""
    if len(ring) < 3:
        return []
    crossings: list[float] = []
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        # coordinate perpendicular to the cut line
        a0, a1 = (y0, y1) if direction == "x" else (x0, x1)
        u0, u1 = (x0, x1) if direction == "x" else (y0, y1)
        if (a0 - station) * (a1 - station) > 0 or a0 == a1:
            continue
        t = (station - a0) / (a1 - a0)
        crossings.append(u0 + t * (u1 - u0))
    crossings.sort()
    return [(crossings[i], crossings[i + 1]) for i in range(0, len(crossings) - 1, 2)]


def _clip_rect(u0, u1, z0, z1, crop) -> tuple[float, float, float, float] | None:
    if crop is None:
        return (u0, u1, z0, z1)
    (cu0, cz0), (cu1, cz1) = crop
    u0, u1 = max(u0, min(cu0, cu1)), min(u1, max(cu0, cu1))
    z0, z1 = max(z0, min(cz0, cz1)), min(z1, max(cz0, cz1))
    if u0 >= u1 or z0 >= z1:
        return None
    return (u0, u1, z0, z1)


def _rect_nodes(u0, u1, z0, z1, layer, pattern, uid, tag) -> list:
    pts = tuple((u * M_TO_IN, z * M_TO_IN) for u, z in
                ((u0, z0), (u1, z0), (u1, z1), (u0, z1)))
    nodes: list = [Polyline(points=pts, layer=layer, closed=True,
                            lineweight=0.35 if layer == "A-WALL" else 0.18,
                            uid=uid, tag=tag)]
    if pattern:
        nodes.append(Hatch(boundary=pts, pattern=pattern, layer="A-WALL-PATT"))
    return nodes


def build_section(model: ResolvedModel, view: Slice) -> Scene:
    """Build the section/detail IR scene for one authored Slice."""
    direction = view.cut_direction or "x"
    origin = view.cut_origin
    if origin is None:
        raise ValueError(f"slice {view.tag} has no cut_origin")
    station = origin.xy_m[1] if direction == "x" else origin.xy_m[0]
    crop = None
    if view.crop is not None:
        crop = (view.crop[0].xy_m, view.crop[1].xy_m)
    is_detail = view.kind.value == "detail"
    min_draw = (view.exaggeration.min_draw_thickness.meters
                if view.exaggeration is not None else 0.0)

    b = SceneBuilder(name=f"{view.kind.value}-{view.tag}", units="in")

    for wall in model.walls:
        _emit_wall_cut(b, model, wall, direction, station, crop, is_detail, min_draw)

    for solid in model.solids:
        for (u0, u1) in _ring_cut_intervals(solid.outline, direction, station):
            rect = _clip_rect(u0, u1, solid.z0_m, solid.z1_m, crop)
            if rect is None:
                continue
            b.extend(_rect_nodes(*rect, "S-FNDN" if solid.category != "slab" else "A-SLAB",
                                 "concrete", solid.uid, solid.tag))

    for roof in model.roofs:
        _emit_roof_cut(b, model, roof, direction, station, crop)

    for floor in model.floors:
        _emit_floor_cut(b, floor, direction, station, crop)

    if crop is not None:
        (cu0, cz0), (cu1, cz1) = crop
        b.add(Text(anchor=((cu0 * M_TO_IN), (cz1 * M_TO_IN) + 6.0),
                   content=view.tag, height=4.0, align="left"))
    return b.build()


def _emit_wall_cut(b, model, wall: ResolvedWall, direction, station, crop,
                   is_detail, min_draw) -> None:
    openings = [op for op in model.openings if op.host_wall == wall.tag]
    label_z = None
    for layer in wall.layers:
        for (u0, u1) in _ring_cut_intervals(layer.polygon, direction, station):
            rect = _clip_rect(u0, u1, wall.z0_m, wall.z1_m, crop)
            if rect is None:
                continue
            ru0, ru1, rz0, rz1 = rect
            true_thickness = ru1 - ru0
            exaggerated = False
            if is_detail and 0 < true_thickness < min_draw:
                grow = (min_draw - true_thickness) / 2.0
                ru0, ru1 = ru0 - grow, ru1 + grow
                exaggerated = True
            aia = _FUNCTION_LAYER.get(layer.function, "A-WALL")
            pattern = _HATCH_PATTERN.get(layer.function)
            zs = _opening_splits(wall, openings, direction, station, rz0, rz1)
            for (z0, z1, void) in zs:
                if void:
                    # glazing/void line at the opening
                    b.add(Polyline(points=(((ru0 + ru1) / 2 * M_TO_IN, z0 * M_TO_IN),
                                           ((ru0 + ru1) / 2 * M_TO_IN, z1 * M_TO_IN)),
                                   layer="A-GLAZ", lineweight=0.18,
                                   uid=wall.uid, tag=f"{wall.tag}-void"))
                    continue
                b.extend(_rect_nodes(ru0, ru1, z0, z1, aia, pattern, wall.uid,
                                     f"{wall.tag}/{layer.name}"))
            if is_detail:
                # true-dimension label per layer (exaggeration labels true size, #36)
                thickness_in = true_thickness * M_TO_IN
                label = f"{layer.name} {thickness_in:.3g}\""
                if exaggerated:
                    label += " (NTS)"
                z_lab = label_z if label_z is not None else rz1
                b.add(Text(anchor=(((ru0 + ru1) / 2) * M_TO_IN, (z_lab * M_TO_IN) + 2.0),
                           content=label, height=1.5, rotation=90.0, align="left",
                           layer="A-ANNO-TEXT"))


def _opening_splits(wall, openings, direction, station, z0, z1):
    """Split a wall's z-band where the cut passes through an opening."""
    (sx, sy), (ex, ey) = wall.axis
    length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if length < 1e-9:
        return [(z0, z1, False)]
    # Station of the cut along the wall axis (only meaningful when the cut crosses it).
    a0, a1 = (sy, ey) if direction == "x" else (sx, ex)
    if (a0 - station) * (a1 - station) > 0:
        return [(z0, z1, False)]
    denominator = (a1 - a0) or 1e-12
    t = (station - a0) / denominator
    s = t * length
    bands: list[tuple[float, float, bool]] = []
    cut_openings = [
        op for op in openings
        if op.center_along_m - op.width_m / 2 <= s <= op.center_along_m + op.width_m / 2
    ]
    if not cut_openings:
        return [(z0, z1, False)]
    op = cut_openings[0]
    sill_z = wall.z0_m + op.sill_m
    head_z = sill_z + op.height_m
    if sill_z > z0:
        bands.append((z0, min(sill_z, z1), False))
    v0, v1 = max(sill_z, z0), min(head_z, z1)
    if v1 > v0:
        bands.append((v0, v1, True))
    if head_z < z1:
        bands.append((max(head_z, z0), z1, False))
    return bands or [(z0, z1, False)]


def _emit_roof_cut(b, model, roof, direction, station, crop) -> None:
    intervals = _ring_cut_intervals(roof.footprint, direction, station)
    if not intervals:
        return
    asm = model.plan.library.resolve_assembly(roof.assembly)
    thickness = sum(l.thickness.meters for l in asm.layers) if asm is not None else 0.3
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    lo, hi = (min(xs), max(xs)) if roof.ridge_direction == "y" else (min(ys), max(ys))
    mid = (lo + hi) / 2.0

    def z_at(u: float) -> float:
        # Slope runs perpendicular to the ridge.
        span = (hi - lo) / 2.0 or 1e-9
        if roof.form == "shed":
            return roof.eave_z_m + (u - lo) / (hi - lo) * (roof.ridge_z_m - roof.eave_z_m)
        frac = 1.0 - abs(u - mid) / span
        return roof.eave_z_m + frac * (roof.ridge_z_m - roof.eave_z_m)

    slope_along_cut = (
        (roof.ridge_direction == "y" and direction == "x")
        or (roof.ridge_direction == "x" and direction == "y")
    )
    for (u0, u1) in intervals:
        if crop is not None:
            (cu0, _), (cu1, _) = crop
            u0, u1 = max(u0, min(cu0, cu1)), min(u1, max(cu0, cu1))
            if u0 >= u1:
                continue
        if slope_along_cut:
            stations_u = [u0] + ([mid] if u0 < mid < u1 else []) + [u1]
            top = [(u, z_at(u)) for u in stations_u]
        else:
            z = z_at(station)
            top = [(u0, z), (u1, z)]
        bottom = [(u, z - thickness) for (u, z) in reversed(top)]
        pts = tuple((u * M_TO_IN, z * M_TO_IN) for (u, z) in top + bottom)
        b.add(Polyline(points=pts, layer="A-ROOF", closed=True, lineweight=0.35,
                       uid=roof.uid, tag=roof.tag))
        b.add(Hatch(boundary=pts, pattern="batt", layer="A-WALL-PATT"))


def _emit_floor_cut(b, floor, direction, station, crop) -> None:
    for member in floor.members:
        (x0, y0), (x1, y1) = member.p0, member.p1
        a0, a1 = (y0, y1) if direction == "x" else (x0, x1)
        u0, u1 = (x0, x1) if direction == "x" else (y0, y1)
        if a0 == a1:
            # member perpendicular to cut? p runs along the cut axis at a station
            if abs(a0 - station) > 1e-9:
                continue
            rect = _clip_rect(min(u0, u1), max(u0, u1), member.z0_m, member.z1_m, crop)
            if rect is None:
                continue
            b.extend(_rect_nodes(*rect, "S-FRAM", None, member.parent_uid,
                                 member.child_key))
            continue
        if (a0 - station) * (a1 - station) > 0:
            continue
        # member crosses the cut: draw its section (1.5" wide x depth)
        t = (station - a0) / ((a1 - a0) or 1e-12)
        u = u0 + t * (u1 - u0)
        half = 0.75 * 0.0254
        rect = _clip_rect(u - half, u + half, member.z0_m, member.z1_m, crop)
        if rect is None:
            continue
        b.extend(_rect_nodes(*rect, "S-FRAM", "lumber", member.parent_uid,
                             member.child_key))
