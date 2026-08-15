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

import math

from typehaus.emit.draw.annotate import LabelSpec, dodge, place_column
from typehaus.emit.draw.palette import detail_hatch
from typehaus.emit.draw.scene import (
    Hatch,
    Leader,
    NamedPoint,
    Polyline,
    Scene,
    SceneBuilder,
    Text,
)
from typehaus.model.enums import LayerFunction, SliceKind
from typehaus.model.views import Slice
from typehaus.quantities import M_PER_IN, m, pt
from typehaus.resolve.model import ResolvedModel, ResolvedWall

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

def ring_cut_intervals(ring, direction: str, station: float) -> list[tuple[float, float]]:
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


# Vertical step between successive layer labels in a detail, model inches.
_LABEL_RUNG_IN = 2.6


def _clip_segment(p0, p1, crop):
    """Liang–Barsky clip of a (u, z) segment to the crop rectangle, or None if outside."""
    if crop is None:
        return (p0, p1)
    (cu0, cz0), (cu1, cz1) = crop
    u_lo, u_hi = min(cu0, cu1), max(cu0, cu1)
    z_lo, z_hi = min(cz0, cz1), max(cz0, cz1)
    du, dz = p1[0] - p0[0], p1[1] - p0[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-du, p0[0] - u_lo), (du, u_hi - p0[0]),
                 (-dz, p0[1] - z_lo), (dz, z_hi - p0[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return None
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
    if t0 > t1:
        return None
    return ((p0[0] + t0 * du, p0[1] + t0 * dz),
            (p0[0] + t1 * du, p0[1] + t1 * dz))


def _clip_polygon(points, crop):
    """Sutherland–Hodgman clip of a (u, z) polygon to the crop rectangle.

    ``_clip_rect`` only handles axis-aligned bands; a sloped roof band needs a real
    polygon clip or it runs straight off the detail's crop window.
    """
    if crop is None:
        return list(points)
    (cu0, cz0), (cu1, cz1) = crop
    u_lo, u_hi = min(cu0, cu1), max(cu0, cu1)
    z_lo, z_hi = min(cz0, cz1), max(cz0, cz1)

    def clip(poly, inside, intersect):
        out = []
        for index, current in enumerate(poly):
            previous = poly[index - 1]
            cur_in, prev_in = inside(current), inside(previous)
            if cur_in:
                if not prev_in:
                    out.append(intersect(previous, current))
                out.append(current)
            elif prev_in:
                out.append(intersect(previous, current))
        return out

    def cut(poly, axis, bound, keep_greater):
        def inside(p):
            return p[axis] >= bound if keep_greater else p[axis] <= bound

        def intersect(a, b):
            span = b[axis] - a[axis]
            t = 0.0 if abs(span) < 1e-12 else (bound - a[axis]) / span
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

        return clip(poly, inside, intersect)

    poly = list(points)
    for axis, bound, keep_greater in (
        (0, u_lo, True), (0, u_hi, False), (1, z_lo, True), (1, z_hi, False),
    ):
        if not poly:
            return []
        poly = cut(poly, axis, bound, keep_greater)
    return poly


def _rect_nodes(u0, u1, z0, z1, layer, pattern, uid, tag, outline: bool = True,
                material: str | None = None) -> list:
    pts = tuple((u / M_PER_IN, z / M_PER_IN) for u, z in
                ((u0, z0), (u1, z0), (u1, z1), (u0, z1)))
    nodes: list = []
    if outline:
        nodes.append(Polyline(points=pts, layer=layer, closed=True,
                              lineweight=0.35 if layer == "A-WALL" else 0.18,
                              uid=uid, tag=tag))
    if pattern:
        nodes.append(Hatch(boundary=pts, pattern=pattern, layer="A-WALL-PATT",
                           material=material))
    return nodes


def _quad_nodes(u0, u1, z0, z1_left, z1_right, layer, pattern, uid, tag,
                material: str | None = None) -> list:
    """Like ``_rect_nodes`` but with a sloped top: left/right top elevations differ.

    Sibling of ``_rect_nodes`` for per-layer sloped terminations (Revit layer extension
    distances against a raked interface plane) — threads through detail cuts only.
    """
    pts = tuple((u / M_PER_IN, z / M_PER_IN) for u, z in
                ((u0, z0), (u1, z0), (u1, z1_right), (u0, z1_left)))
    nodes: list = [Polyline(points=pts, layer=layer, closed=True,
                            lineweight=0.35 if layer == "A-WALL" else 0.18,
                            uid=uid, tag=tag)]
    if pattern:
        nodes.append(Hatch(boundary=pts, pattern=pattern, layer="A-WALL-PATT",
                           material=material))
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

    # Layer-label ladders are collected per wall and emitted once, after every wall has
    # been cut, so ladders from different walls (and later the seed-callout column) can be
    # dodged against each other instead of overprinting.
    ladder_labels: list = []
    for wall in model.walls:
        _emit_wall_cut(b, model, wall, direction, station, crop, is_detail, min_draw,
                       joints, ladder_labels)

    for solid in model.solids:
        material = _solid_material(model, solid)
        for (u0, u1) in ring_cut_intervals(solid.outline, direction, station):
            rect = _clip_rect(u0, u1, solid.z0_m, solid.z1_m, crop)
            if rect is None:
                continue
            b.extend(_rect_nodes(*rect, "S-FNDN" if solid.category != "slab" else "A-SLAB",
                                 material, solid.uid, solid.tag, material=material))

    for roof in model.roofs:
        _emit_roof_cut(b, model, roof, direction, station, crop, joints)

    for floor in model.floors:
        _emit_floor_cut(b, floor, direction, station, crop)

    # Framing members are the whole content of some details — every post, beam, rafter and
    # joist of a freestanding structure. Gating them on a JointPlan meant an *authored*
    # detail (which is built with no joints) came out with the framing missing, drawing an
    # empty box where the frame should be. Joints add per-layer terminations and treatment
    # fills on top; they are not what makes a member visible.
    if joints is not None or is_detail:
        _emit_member_cuts(b, model, direction, station, crop)
    if joints is not None:
        b.extend(list(joints.treatments))

    # Emit the collected layer-label ladders last so they draw over the cut geometry,
    # dodged against each other (two walls' ladders share the text column at the crop's
    # left edge and would otherwise interleave).
    for placed in dodge(ladder_labels):
        mid_u = placed.spec.target[0]
        rung_z = placed.at[1]
        # Horizontal, leadered back to the layer at the rung's own height — the rung moves
        # with the label when dodged, so the leader line stays flat and never crosses text.
        b.add(Leader(anchor=NamedPoint(xy=(mid_u, rung_z)), at=placed.at,
                     to=(mid_u, rung_z), text=placed.spec.text,
                     height=placed.height, layer="A-ANNO-TEXT"))

    if crop is not None:
        (cu0, cz0), (cu1, cz1) = crop
        b.add(Text(anchor=((cu0 / M_PER_IN), (cz1 / M_PER_IN) + 6.0),
                   content=view.tag, height=4.0, align="left"))
    return b.build()


def _solid_material(model: ResolvedModel, solid) -> str:
    """A cut solid's material tag: its own material ref, else its assembly's structure layer.

    Every solid used to hatch as concrete, which is right for a footing and wrong for a
    composite deck, an aluminium extrusion or a polycarbonate sheet — all of which a detail
    exists to tell apart. This is the same material -> assembly -> structure layer walk
    ``emit/gltf/palette.py::_solid_color`` already does, so the drawn detail and the 3D model
    name the same material for the same solid.

    The direct ref is read first because the assembly cannot answer for a solid that has no
    business having one: a guard's glass lite and its aluminium posts share one
    ``Railing.assembly``, and the whole point of the per-part material refs is that they are
    not the same material. Reading only the assembly hatched a glass baluster panel as
    concrete in every section and detail.

    Without either the fallback reads the member's own *section*, because that is what
    actually says what it is made of: a "6x6" or a "2-2x8" is dressed lumber, a "12 round" is
    a sonotube-cast concrete pier. Slabs, footings and pads stay concrete — the case the old
    blanket rule was right about.
    """
    if solid.material:
        return solid.material
    if solid.assembly:
        assembly = model.plan.library.resolve_assembly(solid.assembly)
        if assembly is not None and assembly.layers:
            idx = assembly.structure_index()
            layer = assembly.layers[idx if idx is not None else 0]
            if layer.material_ref:
                return layer.material_ref
    if solid.category in ("beam", "column"):
        element = model.plan.by_tag(solid.tag)
        size = getattr(element, "size", "") or ""
        if not size.strip().endswith("round"):
            return "spf"
    return "concrete"


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
                   is_detail, min_draw, joints=None, ladder_labels=None) -> None:
    openings = [op for op in model.openings if op.host_wall == wall.tag]
    # One ladder entry per (wall, layer name) — a layer cut into several (u0, u1)
    # intervals used to re-emit its label per interval ("5.5 stud" twice), and each
    # interval's own crop-clipped top made the rungs interleave between layers. Labels
    # are collected here and laddered after the layer loop from a single anchor.
    label_entries: dict[str, tuple[str, float]] = {}
    wall_top = _wall_top_at_cut(wall, direction, station)
    for layer in wall.layers:
        term = joints.termination(wall.uid, layer.name) if joints is not None else None
        for (u0, u1) in ring_cut_intervals(layer.polygon, direction, station):
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
            pattern = detail_hatch(layer.material_ref, layer.function)
            if is_detail and not layer.is_cavity and layer.name not in label_entries:
                # True-dimension label per layer (exaggeration labels true size, #36).
                thickness_in = true_thickness / M_PER_IN
                label = f"{layer.name} {thickness_in:.3g}\""
                if exaggerated:
                    label += " (NTS)"
                label_entries[layer.name] = (label, ((ru0 + ru1) / 2) / M_PER_IN)
            sloped = term is not None and abs(layer_top_l - layer_top_r) > 1e-6
            if sloped:
                # Raked layer termination against the interface plane — single sloped quad,
                # clipped to the crop's z-window (rz0/rz1 already crop-clipped).
                tl = min(layer_top_l, rz1)
                tr = min(layer_top_r, rz1)
                b.extend(_quad_nodes(ru0, ru1, rz0, tl, tr,
                                     aia, pattern, wall.uid, f"{wall.tag}/{layer.name}",
                                     material=layer.material_ref))
                continue
            zs = _opening_splits(wall, openings, direction, station, rz0, rz1)
            for (z0, z1, void) in zs:
                if void:
                    # A full-height glazing line that spans the whole crop reads as a
                    # mistake in a junction detail — the cut is passing through pure
                    # glass with neither head nor sill in frame. Drop it and let the
                    # neighbouring solid bands' edges show the actual head/sill of the
                    # cut instead (#opening-void). Keep the line where a real jamb edge
                    # is in frame (an opening genuinely cut in a plan/elevation).
                    full_span = (crop is not None and z0 <= rz0 + 1e-9
                                 and z1 >= rz1 - 1e-9)
                    if is_detail and full_span:
                        continue
                    # glazing/void line at the opening
                    b.add(Polyline(points=(((ru0 + ru1) / 2 / M_PER_IN, z0 / M_PER_IN),
                                           ((ru0 + ru1) / 2 / M_PER_IN, z1 / M_PER_IN)),
                                   layer="A-GLAZ", lineweight=0.18,
                                   uid=wall.uid, tag=f"{wall.tag}-void"))
                    continue
                b.extend(_rect_nodes(ru0, ru1, z0, z1, aia, pattern, wall.uid,
                                     f"{wall.tag}/{layer.name}",
                                     outline=not layer.is_cavity,
                                     material=layer.material_ref))
    if not label_entries or ladder_labels is None:
        return
    # The whole ladder hangs from a single anchor: the wall's top as seen in the crop.
    # Rungs step down at a uniform _LABEL_RUNG_IN so a sloped/eave cut, where each layer
    # terminates at its own height, cannot interleave rungs from different layers.
    # Stacked vertically because at detail scale a membrane and its neighbours are
    # hundredths of an inch apart — labels sharing one baseline overprint into a smear.
    if crop is not None:
        (cu0, cz0), (cu1, cz1) = crop
        z_top = min(wall_top, max(cz0, cz1))
        text_u = min(cu0, cu1) / M_PER_IN - 1.0
    else:
        z_top = wall_top
        text_u = min(mid_u for (_lab, mid_u) in label_entries.values()) - 14.0
    # Sorted by mid_u (innermost layer first): the text column sits left of the cut, so
    # ascending targets top-to-bottom keep the horizontal leader lines nested, not crossed.
    entries = [LabelSpec(text=label, target=(mid_u, 0.0), key=(wall.uid, name))
               for name, (label, mid_u) in
               sorted(label_entries.items(), key=lambda item: item[1][1])]
    ladder_labels.extend(place_column(entries, x=text_u, z_top=z_top / M_PER_IN - 1.0,
                                      step=_LABEL_RUNG_IN, height=1.6, align="right"))


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


def _rafter_plan_span(roof, direction: str) -> tuple[float, float] | None:
    """The rafters' in-section (u) extent — where the framed structure actually ends.

    A zero-overhang roof's structure layer stops at the rafters' plumb-cut tails (the
    bearing wall's stud face), well inboard of a footprint edge that laps the wall
    cladding. ``None`` when the roof has no rafter members (truss roofs keep the
    uniform footprint band).
    """
    axis = 0 if direction == "x" else 1
    coords = [point[axis] for member in roof.members if member.category == "rafter"
              for point in (member.p0, member.p1)]
    if not coords:
        return None
    return min(coords), max(coords)


def _emit_roof_cut(b, model, roof, direction, station, crop, joints=None) -> None:
    intervals = ring_cut_intervals(roof.footprint, direction, station)
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
    # Per-layer eave/rake clips, mirroring the 3D emitters: the resolver's serialized
    # setbacks pull each above-structure band in to its own wall-stack face (deck at the
    # wall sheathing, foam at the furring, metal proud), and the structure band stops at
    # the rafters' plumb-cut tails instead of running out to the footprint edge — the
    # zero-overhang reference's stepped stack, in section.
    edge_lo, edge_hi = ("west", "east") if direction == "x" else ("south", "north")
    setbacks = {entry["layer"]: entry
                for entry in (getattr(roof, "layer_edge_setbacks", None) or ())}
    structure_span = _rafter_plan_span(roof, direction)

    def _top_line(a: float, b_: float) -> list[tuple[float, float]]:
        if slope_along_cut:
            stations_u = [a] + ([mid] if a < mid < b_ else []) + [b_]
            return [(u, z_at(u)) for u in stations_u]
        z = z_at(station)
        return [(a, z), (b_, z)]

    for (u0, u1) in intervals:
        u0c, u1c = u0, u1
        if crop is not None:
            (cu0, _), (cu1, _) = crop
            u0c, u1c = max(u0, min(cu0, cu1)), min(u1, max(cu0, cu1))
            if u0c >= u1c:
                continue
        if detail_layers is not None:
            # Per-layer sloped bands: each band offset down from the deck top by its
            # cumulative depth, so the roof reads as its real assembly in the detail.
            # Edge insets apply off the *footprint* interval (u0/u1), then the crop
            # clips — insetting an already-cropped edge would double-shift the band.
            for (layer, d0, d1) in detail_layers:
                a, b_ = u0, u1
                entry = setbacks.get(layer.name)
                if entry is not None:
                    a += float(entry.get(edge_lo, 0.0))
                    b_ -= float(entry.get(edge_hi, 0.0))
                elif (layer.function is LayerFunction.STRUCTURE
                      and structure_span is not None):
                    a, b_ = max(a, structure_span[0]), min(b_, structure_span[1])
                if b_ - a < 1e-9:
                    continue
                top = _top_line(a, b_)
                band_top = [(u, z - d0) for (u, z) in top]
                band_bot = [(u, z - d1) for (u, z) in reversed(top)]
                clipped = _clip_polygon(band_top + band_bot, crop)
                if len(clipped) < 3:
                    continue
                pts = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in clipped)
                b.add(Polyline(points=pts, layer="A-ROOF", closed=True, lineweight=0.18,
                               uid=roof.uid, tag=f"{roof.tag}/{layer.name}"))
                pat = detail_hatch(layer.material_ref, layer.function.value)
                b.add(Hatch(boundary=pts, pattern=pat or "batt", layer="A-WALL-PATT",
                            uid=roof.uid, material=layer.material_ref))
            continue
        top = _top_line(u0c, u1c)
        bottom = [(u, z - thickness) for (u, z) in reversed(top)]
        clipped = _clip_polygon(top + bottom, crop)
        if len(clipped) < 3:
            continue
        pts = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in clipped)
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
            b.extend(_member_flange_nodes(*rect, member.profile, member.parent_uid,
                                          member.child_key))
            continue
        if (a0 - station) * (a1 - station) > 0:
            continue
        # member crosses the cut: draw its section (1.5" wide x depth)
        t = (station - a0) / ((a1 - a0) or 1e-12)
        u = u0 + t * (u1 - u0)
        half = 0.75 * M_PER_IN
        rect = _clip_rect(u - half, u + half, member.z0_m, member.z1_m, crop)
        if rect is None:
            continue
        b.extend(_rect_nodes(*rect, "S-FRAM", "lumber", member.parent_uid,
                             member.child_key))
        b.extend(_member_flange_nodes(*rect, member.profile, member.parent_uid,
                                      member.child_key))


def _emit_member_cuts(b, model, direction, station, crop) -> None:
    """Detail-mode: draw wall + roof framing members crossing the cut (top plates, rafters).

    Generalizes the floor crossing math to raked members — a member with ``z0_end_m`` /
    ``z1_end_m`` set interpolates its elevation at the crossing station."""
    for wall in model.walls:
        for member in wall.members:
            _emit_one_member(b, member, direction, station, crop)
    for roof in model.roofs:
        # A birdsmouth rafter runs *along* the cut plane, so it only draws when a rafter
        # lands exactly on the station — which a wall-midpoint cut rarely does. Show the
        # single nearest one as the representative rafter so the eave detail carries its
        # seat cut, and let all other members follow the ordinary crossing/parallel rules.
        parallel_rafters = []
        for member in roof.members:
            if (_birdsmouth_depth_in(member.connection) is not None
                    and _member_is_parallel(member, direction)
                    and _member_u_overlaps_crop(member, direction, crop)):
                parallel_rafters.append(member)
            else:
                _emit_one_member(b, member, direction, station, crop)
        if parallel_rafters and not any(
                abs(_member_perp(m, direction) - station) < 1e-9 for m in parallel_rafters):
            nearest = min(parallel_rafters,
                          key=lambda m: abs(_member_perp(m, direction) - station))
            _emit_one_member(b, nearest, direction, _member_perp(nearest, direction), crop)


def _member_u_overlaps_crop(member, direction: str, crop) -> bool:
    """Whether the member's in-section (u) span overlaps the crop's u-window.

    Two rafters share every y at a gable (one per roof plane); only the one whose run is
    actually under the crop is the eave the detail is about.
    """
    if crop is None:
        return True
    (x0, y0), (x1, y1) = member.p0, member.p1
    u0, u1 = (x0, x1) if direction == "x" else (y0, y1)
    (cu0, _), (cu1, _) = crop
    lo, hi = min(cu0, cu1), max(cu0, cu1)
    return min(u0, u1) <= hi and max(u0, u1) >= lo


def _member_is_parallel(member, direction: str) -> bool:
    (x0, y0), (x1, y1) = member.p0, member.p1
    a0, a1 = (y0, y1) if direction == "x" else (x0, x1)
    return abs(a0 - a1) < 1e-12


def _member_perp(member, direction: str) -> float:
    """The member's coordinate perpendicular to the cut (its station if parallel)."""
    (x0, y0), _ = member.p0, member.p1
    return y0 if direction == "x" else x0


def _birdsmouth_depth_in(connection: str | None) -> float | None:
    """Seat-cut depth (inches) parsed off a rafter's ``eave:birdsmouth-<d>in`` tag.

    The connection string is the only carrier of the notch depth (``resolve.model`` keeps
    the member a plain box — no seat cut in the solid), so the 2D section is where the
    birdsmouth becomes drawn linework.
    """
    if not connection:
        return None
    for token in connection.split(";"):
        token = token.strip()
        if "birdsmouth-" in token:
            tail = token.split("birdsmouth-", 1)[1]
            digits = tail[:-2] if tail.endswith("in") else tail
            try:
                return float(digits)
            except ValueError:
                return None
    return None


def _member_flange_nodes(u0, u1, z0, z1, profile, uid, tag) -> list:
    """Two thin flange-delineation lines so an I-joist reads as an I, not a solid bar.

    A cut I-joist member is otherwise a plain rectangle; the flange lines (offset from the
    top and bottom edges by the real flange thickness) are what tell it apart from sawn
    lumber at detail scale. Coordinates in metres, converted to inches like ``_rect_nodes``.
    """
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    if section.shape != "i_joist" or section.flange_thickness_m is None:
        return []
    ft = section.flange_thickness_m
    if (z1 - z0) <= 2.2 * ft:
        return []
    nodes: list = []
    for z in (z0 + ft, z1 - ft):
        nodes.append(Polyline(points=((u0 / M_PER_IN, z / M_PER_IN), (u1 / M_PER_IN, z / M_PER_IN)),
                              layer="S-FRAM", lineweight=0.13, uid=uid,
                              tag=f"{tag}/flange"))
    return nodes


def _emit_raked_rafter(b, member, u0, u1, z0_a, z0_b, z1_a, z1_b, crop,
                       depth_in) -> None:
    """A raked rafter drawn as its true sloped profile with a birdsmouth seat-cut notch.

    Replaces the bounding-box rectangle the parallel-member path would draw (which loses the
    rake entirely) with the actual parallelogram, then notches the underside at the eave
    (low) end so the rafter reads as a seated, notched member. The notch is a plumb heel cut
    of ``depth_in`` plus a horizontal seat bearing on the plate.
    """
    d = depth_in * M_PER_IN
    eave_at_u0 = z1_a <= z1_b  # eave = lower-top end (zero-overhang tail bears here)
    span_u = abs(u1 - u0) or 1e-9
    slope_bot = (z0_b - z0_a) / (u1 - u0)
    run = min(3.5 * M_PER_IN, span_u * 0.35)  # seat run ~ a 2x4 plate bearing
    # The seat runs *inboard* (toward the ridge end) from the eave's plumb cut. The
    # endpoints carry no ordering guarantee — an east-half rafter's eave end is the
    # larger u — so the step direction comes from where the ridge end actually is.
    if eave_at_u0:
        step = math.copysign(run, u1 - u0)
        heel = (u0, z0_a + d)
        toe = (u0 + step, z0_a + slope_bot * step + d)
        poly = [(u0, z1_a), (u1, z1_b), (u1, z0_b), toe, heel]
    else:
        step = math.copysign(run, u0 - u1)
        heel = (u1, z0_b + d)
        toe = (u1 + step, z0_b + slope_bot * step + d)
        poly = [(u1, z1_b), (u0, z1_a), (u0, z0_a), toe, heel]
    clipped = _clip_polygon(poly, crop)
    if len(clipped) < 3:
        return
    pts = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in clipped)
    b.add(Polyline(points=pts, layer="S-FRAM", closed=True, lineweight=0.35,
                   uid=member.parent_uid, tag=member.child_key))
    b.add(Hatch(boundary=pts, pattern="lumber", layer="A-WALL-PATT",
                uid=member.parent_uid, material="spf"))
    # An I-joist rafter carries flange lines along its raked top/bottom edges so it reads
    # as an I-joist, not a solid rafter — offset inward from each edge by the flange depth.
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(member.profile)
    if section.shape == "i_joist" and section.flange_thickness_m is not None:
        ft = section.flange_thickness_m
        for (za, zb) in ((z0_a + ft, z0_b + ft), (z1_a - ft, z1_b - ft)):
            seg = _clip_segment((u0, za), (u1, zb), crop)
            if seg is not None:
                (su0, sz0), (su1, sz1) = seg
                b.add(Polyline(points=((su0 / M_PER_IN, sz0 / M_PER_IN),
                                       (su1 / M_PER_IN, sz1 / M_PER_IN)),
                               layer="S-FRAM", lineweight=0.13,
                               uid=member.parent_uid, tag=f"{member.child_key}/flange"))


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
        raked = member.z0_end_m is not None or member.z1_end_m is not None
        birdsmouth = _birdsmouth_depth_in(member.connection)
        if raked and birdsmouth is not None and abs(u1 - u0) > 1e-9:
            _emit_raked_rafter(b, member, u0, u1, z0_a, z0_b, z1_a, z1_b, crop,
                               birdsmouth)
            return
        rect = _clip_rect(min(u0, u1), max(u0, u1), min(z0_a, z0_b), max(z1_a, z1_b), crop)
        if rect is not None:
            b.extend(_member_rect_nodes(rect, member))
            b.extend(_member_flange_nodes(*rect, member.profile, member.parent_uid,
                                          member.child_key))
        return
    if (a0 - station) * (a1 - station) > 0:
        return
    t = (station - a0) / ((a1 - a0) or 1e-12)
    u = u0 + t * (u1 - u0)
    z0 = z0_a + t * (z0_b - z0_a)
    z1 = z1_a + t * (z1_b - z1_a)
    # The cut is across the member's run, so it shows the section face the plan shows: the
    # wide `depth_m` for a flat-laid plate/sill/block, the thin `width_m` for one on edge.
    # A flat 1.5" was drawn here regardless of profile, which was right only by accident for
    # the on-edge 2x sticks and drew every plate a quarter of its real width.
    from typehaus.resolve.framing.profiles import cross_section, plan_cross_section_m

    half = plan_cross_section_m(cross_section(member.profile), z1_a - z0_a) / 2.0
    rect = _clip_rect(u - half, u + half, min(z0, z1), max(z0, z1), crop)
    if rect is not None:
        b.extend(_member_rect_nodes(rect, member))
        b.extend(_member_flange_nodes(*rect, member.profile, member.parent_uid,
                                      member.child_key))


def _member_rect_nodes(rect, member) -> list:
    """A cut member's rectangle, hatched as what it is made of.

    A member that names a material is a *skin* band (the wall→roof closure, roof-edge
    cladding, derived trim), not lumber — hatch and fill it like the layer stacks hatch
    the same material, so a closure EPS band reads as foam, not as a stack of studs.
    Plain framing keeps the lumber hatch.
    """
    if member.material:
        pattern = detail_hatch(member.material) or "metal"
        return _rect_nodes(*rect, "S-FRAM", pattern, member.parent_uid,
                           member.child_key, material=member.material)
    return _rect_nodes(*rect, "S-FRAM", "lumber", member.parent_uid, member.child_key)
