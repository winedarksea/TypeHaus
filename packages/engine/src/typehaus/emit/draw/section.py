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
from typehaus.model.enums import SliceKind
from typehaus.quantities import m, pt
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


def _quad_nodes(u0, u1, z0, z1_left, z1_right, layer, pattern, uid, tag) -> list:
    """Like ``_rect_nodes`` but with a sloped top: left/right top elevations differ.

    Sibling of ``_rect_nodes`` for per-layer sloped terminations (Revit layer extension
    distances against a raked interface plane) — threads through detail cuts only.
    """
    pts = tuple((u * M_TO_IN, z * M_TO_IN) for u, z in
                ((u0, z0), (u1, z0), (u1, z1_right), (u0, z1_left)))
    nodes: list = [Polyline(points=pts, layer=layer, closed=True,
                            lineweight=0.35 if layer == "A-WALL" else 0.18,
                            uid=uid, tag=tag)]
    if pattern:
        nodes.append(Hatch(boundary=pts, pattern=pattern, layer="A-WALL-PATT"))
    return nodes


def build_section(model: ResolvedModel, view: Slice, joints=None) -> Scene:
    """Build the section/detail IR scene for one authored Slice.

    ``joints`` (a :class:`~typehaus.emit.draw.joints.JointPlan`) is detail-mode only; when
    given, per-layer terminations, sloped roof bands, cut framing members, and treatment
    fills are honored. ``None`` preserves plain-section behaviour (existing callers/goldens).
    """
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
        _emit_wall_cut(b, model, wall, direction, station, crop, is_detail, min_draw, joints)

    for solid in model.solids:
        for (u0, u1) in _ring_cut_intervals(solid.outline, direction, station):
            rect = _clip_rect(u0, u1, solid.z0_m, solid.z1_m, crop)
            if rect is None:
                continue
            b.extend(_rect_nodes(*rect, "S-FNDN" if solid.category != "slab" else "A-SLAB",
                                 "concrete", solid.uid, solid.tag))

    for roof in model.roofs:
        _emit_roof_cut(b, model, roof, direction, station, crop, joints)

    for floor in model.floors:
        _emit_floor_cut(b, floor, direction, station, crop)

    if joints is not None:
        _emit_member_cuts(b, model, direction, station, crop)
        b.extend(list(joints.treatments))

    if crop is not None:
        (cu0, cz0), (cu1, cz1) = crop
        b.add(Text(anchor=((cu0 * M_TO_IN), (cz1 * M_TO_IN) + 6.0),
                   content=view.tag, height=4.0, align="left"))
    return b.build()


def build_center_section(model: ResolvedModel) -> Scene:
    """Default north/south building section for headless rendering and A-301."""
    house_walls = [wall for wall in model.walls if wall.tag.startswith("W-")
                   and wall.storey in {"basement", "main", "second", "attic"}]
    stations = [coordinate for wall in house_walls for coordinate in (wall.axis[0][1], wall.axis[1][1])]
    station = (min(stations) + max(stations)) / 2.0 if stations else 0.0
    view = Slice(uid="RNDSEC00001", tag="SECTION-HOUSE-CENTER", kind=SliceKind.SECTION,
                 cut_origin=pt(m(0), m(station)), cut_direction="x")
    return build_section(model, view)


def _emit_wall_cut(b, model, wall: ResolvedWall, direction, station, crop,
                   is_detail, min_draw, joints=None) -> None:
    openings = [op for op in model.openings if op.host_wall == wall.tag]
    label_z = None
    wall_top = _wall_top_at_cut(wall, direction, station)
    for layer in wall.layers:
        term = joints.termination(wall.uid, layer.name) if joints is not None else None
        for (u0, u1) in _ring_cut_intervals(layer.polygon, direction, station):
            layer_top_l = term.z(u0) if term is not None else wall_top
            layer_top_r = term.z(u1) if term is not None else wall_top
            rect = _clip_rect(u0, u1, wall.z0_m, max(layer_top_l, layer_top_r), crop)
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
            sloped = term is not None and abs(layer_top_l - layer_top_r) > 1e-6
            if sloped:
                # Raked layer termination against the interface plane — single sloped quad,
                # clipped to the crop's z-window (rz0/rz1 already crop-clipped).
                tl = min(layer_top_l, rz1)
                tr = min(layer_top_r, rz1)
                b.extend(_quad_nodes(ru0, ru1, rz0, tl, tr,
                                     aia, pattern, wall.uid, f"{wall.tag}/{layer.name}"))
                continue
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


def _wall_top_at_cut(wall: ResolvedWall, direction: str, station: float) -> float:
    """Interpolate a ``ToRoof`` wall's raked top at the section intersection."""
    start_top = wall.top_z0_m if wall.top_z0_m is not None else wall.z1_m
    end_top = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    (x0, y0), (x1, y1) = wall.axis
    cross0, cross1 = (y0, y1) if direction == "x" else (x0, x1)
    if abs(cross1 - cross0) < 1e-9:
        return max(start_top, end_top)
    fraction = min(1.0, max(0.0, (station - cross0) / (cross1 - cross0)))
    return start_top + (end_top - start_top) * fraction


def _emit_roof_cut(b, model, roof, direction, station, crop, joints=None) -> None:
    intervals = _ring_cut_intervals(roof.footprint, direction, station)
    if not intervals:
        return
    asm = model.plan.library.resolve_assembly(roof.assembly)
    thickness = sum(l.thickness.meters for l in asm.layers) if asm is not None else 0.3
    detail_layers = None
    if joints is not None and asm is not None:
        # Per-layer sloped bands (cumulative offsets from the deck top downward).
        detail_layers = []
        depth = 0.0
        for layer in asm.layers:
            t = layer.thickness.meters
            detail_layers.append((layer, depth, depth + t))
            depth += t
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
        if detail_layers is not None:
            # Per-layer sloped bands: each band offset down from the deck top by its
            # cumulative depth, so the roof reads as its real assembly in the detail.
            for (layer, d0, d1) in detail_layers:
                band_top = [(u, z - d0) for (u, z) in top]
                band_bot = [(u, z - d1) for (u, z) in reversed(top)]
                pts = tuple((u * M_TO_IN, z * M_TO_IN) for (u, z) in band_top + band_bot)
                b.add(Polyline(points=pts, layer="A-ROOF", closed=True, lineweight=0.18,
                               uid=roof.uid, tag=f"{roof.tag}/{layer.name}"))
                pat = _HATCH_PATTERN.get(layer.function, "batt")
                b.add(Hatch(boundary=pts, pattern=pat, layer="A-WALL-PATT",
                            uid=roof.uid))
            continue
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


def _emit_member_cuts(b, model, direction, station, crop) -> None:
    """Detail-mode: draw wall + roof framing members crossing the cut (top plates, rafters).

    Generalizes the floor crossing math to raked members — a member with ``z0_end_m`` /
    ``z1_end_m`` set interpolates its elevation at the crossing station."""
    for wall in model.walls:
        for member in wall.members:
            _emit_one_member(b, member, direction, station, crop)
    for roof in model.roofs:
        for member in roof.members:
            _emit_one_member(b, member, direction, station, crop)


def _emit_one_member(b, member, direction, station, crop) -> None:
    (x0, y0), (x1, y1) = member.p0, member.p1
    a0, a1 = (y0, y1) if direction == "x" else (x0, x1)
    u0, u1 = (x0, x1) if direction == "x" else (y0, y1)
    z0_a, z1_a = member.z0_m, member.z1_m
    z0_b = member.z0_end_m if member.z0_end_m is not None else member.z0_m
    z1_b = member.z1_end_m if member.z1_end_m is not None else member.z1_m
    if abs(a0 - a1) < 1e-12:
        # member runs along the cut axis at a station (e.g. a top plate parallel to the cut)
        if abs(a0 - station) > 1e-9:
            return
        rect = _clip_rect(min(u0, u1), max(u0, u1), min(z0_a, z0_b), max(z1_a, z1_b), crop)
        if rect is not None:
            b.extend(_rect_nodes(*rect, "S-FRAM", "lumber", member.parent_uid,
                                 member.child_key))
        return
    if (a0 - station) * (a1 - station) > 0:
        return
    t = (station - a0) / ((a1 - a0) or 1e-12)
    u = u0 + t * (u1 - u0)
    z0 = z0_a + t * (z0_b - z0_a)
    z1 = z1_a + t * (z1_b - z1_a)
    half = 0.75 * 0.0254
    rect = _clip_rect(u - half, u + half, min(z0, z1), max(z0, z1), crop)
    if rect is not None:
        b.extend(_rect_nodes(*rect, "S-FRAM", "lumber", member.parent_uid,
                             member.child_key))
