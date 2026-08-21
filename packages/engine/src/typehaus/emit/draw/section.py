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

from typehaus.emit.draw.palette import detail_hatch
from typehaus.emit.draw.scene import Hatch, Polyline, Scene, SceneBuilder, Text
from typehaus.emit.draw.section_clip import (
    clip_polygon,
    clip_rect,
    profile_band,
    quad_nodes,
    rect_nodes,
)
from typehaus.emit.draw.section_labels import (
    emit_ladders,
    roof_layer_ladder,
    wall_layer_ladder,
)
from typehaus.emit.draw.section_members import _emit_member_cuts, emit_framing_cuts
from typehaus.model.enums import SliceKind
from typehaus.model.views import Slice
from typehaus.quantities import M_PER_IN, m, pt
from typehaus.resolve.geometry_slice import (
    CutPlane,
    ring_cut_intervals,
    ring_intervals,
    slice_part,
)
from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.resolve.roof_geometry import roof_plane_z, roof_ridge_coordinate
from typehaus.resolve.roof_layer_setbacks import (
    assembly_layer_spans,
    structure_datum_m,
)

# ``section.py`` is the name every caller — the CLI, the server, the detail package and the
# tests — imports a cut from, so the pieces split out of it stay reachable here.
__all__ = [
    "build_center_section",
    "build_section",
    "ring_cut_intervals",
]

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

# ``ring_cut_intervals`` is the pre-IR cut: a plan ring intersected with the cut line, even-odd
# paired. It now lives in the slice kernel (bug-for-bug, old crossing rule and all) and is
# re-exported here for the seven detail modules that import it from this name.


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
    plane = CutPlane(axis=direction, station_m=station)
    ladder_labels: list = []
    for wall in model.walls:
        _emit_wall_cut(b, model, wall, plane, crop, is_detail, min_draw,
                       joints, ladder_labels)

    for solid in model.solids:
        _emit_solid_cut(b, model, solid, plane, crop)

    for roof in model.roofs:
        _emit_roof_cut(b, model, roof, plane, crop, joints, ladder_labels)

    emit_framing_cuts(b, model, model.floors, plane, crop)

    # Framing members are the whole content of some details — every post, beam, rafter and
    # joist of a freestanding structure. Gating them on a JointPlan meant an *authored*
    # detail (which is built with no joints) came out with the framing missing, drawing an
    # empty box where the frame should be. Joints add per-layer terminations and treatment
    # fills on top; they are not what makes a member visible.
    #
    # A roof's members are drawn whatever the mode, because the roof's own bands no longer
    # carry its structure: ``roof_parts`` builds only the layers above it, exactly so the
    # structure is not drawn twice. Without the rafters a plain building section would show
    # a roof stack floating over nothing.
    _emit_member_cuts(b, model, plane, crop,
                      walls_and_floors=joints is not None or is_detail)
    if joints is not None:
        b.extend(list(joints.treatments))

    emit_ladders(b, ladder_labels)

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


def _emit_wall_cut(b, model, wall: ResolvedWall, plane: CutPlane, crop,
                   is_detail, min_draw, joints=None, ladder_labels=None) -> None:
    """One wall's cut, sliced out of the geometry IR.

    The IR's wall body is already jamb-split into piers, sill bands and headers, already
    banded (``Layer.extent``), already raked under a gable and already arched at a curved
    head — five things this function used to re-derive, each with its own idea of where a
    layer stops. What stays here is what genuinely belongs on the drawing side: the crop,
    thin-layer exaggeration (#36), the true-dimension label, the authored joint termination
    and the glazing line.
    """
    element = model.geometry.by_uid(wall.uid)
    # One ladder entry per (wall, layer name) — a layer cut into several profiles must not
    # re-emit its label per profile ("5.5 stud" twice), and each profile's own crop-clipped
    # top made the rungs interleave between layers. Labels are collected here and laddered
    # after the layer loop from a single anchor.
    label_entries: dict[str, tuple[str, float]] = {}
    wall_top = _wall_top_at_cut(wall, plane.axis, plane.station_m)

    for part in (element.parts if element is not None else ()):
        catalog = part.catalog
        if catalog is None:
            continue
        name, function = catalog.name, catalog.role
        term = joints.termination(wall.uid, name) if joints is not None else None
        aia = _FUNCTION_LAYER.get(function, "A-WALL")
        pattern = detail_hatch(catalog.material_ref, function)
        tag = f"{wall.tag}/{name}"
        for profile in slice_part(part, plane):
            band = profile_band(profile)
            if band is None:
                # An arch head's cut is a real polygon, not a band — draw it as one.
                clipped = clip_polygon(profile.outline, crop)
                if len(clipped) >= 3:
                    points = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in clipped)
                    b.add(Polyline(points=points, layer=aia, closed=True, lineweight=0.18,
                                   uid=wall.uid, tag=tag))
                    if pattern:
                        b.add(Hatch(boundary=points, pattern=pattern, layer="A-WALL-PATT",
                                    material=catalog.material_ref))
                continue
            u0, u1, z0, top_left, top_right = band
            if term is not None:
                # An authored ``LayerJoin`` is a drawing-only extension of a layer past the
                # wall top — the one thing on this path the model does not know about.
                top_left, top_right = term.z(u0), term.z(u1)
            rect = clip_rect(u0, u1, z0, max(top_left, top_right), crop)
            if rect is None:
                continue
            ru0, ru1, rz0, rz1 = rect
            true_thickness = ru1 - ru0
            exaggerated = False
            if is_detail and 0 < true_thickness < min_draw:
                grow = (min_draw - true_thickness) / 2.0
                ru0, ru1 = ru0 - grow, ru1 + grow
                exaggerated = True
            if is_detail and name not in label_entries:
                # True-dimension label per layer (exaggeration labels true size, #36).
                label = f'{name} {true_thickness / M_PER_IN:.3g}"'
                if exaggerated:
                    label += " (NTS)"
                label_entries[name] = (label, ((ru0 + ru1) / 2) / M_PER_IN)
            if abs(top_left - top_right) > 1e-6:
                # Raked termination against the interface plane — a single sloped quad,
                # clipped to the crop's z-window (rz0/rz1 are already crop-clipped).
                b.extend(quad_nodes(ru0, ru1, rz0, min(top_left, rz1), min(top_right, rz1),
                                    aia, pattern, wall.uid, tag,
                                    material=catalog.material_ref))
                continue
            b.extend(rect_nodes(ru0, ru1, rz0, rz1, aia, pattern, wall.uid, tag,
                                material=catalog.material_ref))

    _emit_cavity_cut(b, model, wall, plane, crop, is_detail, min_draw, wall_top, joints)
    _emit_glazing_lines(b, model, wall, plane, crop, is_detail)
    wall_layer_ladder(wall, label_entries, wall_top, crop, ladder_labels)


def _emit_cavity_cut(b, model, wall, plane: CutPlane, crop, is_detail, min_draw,
                     wall_top, joints=None) -> None:
    """The batt between the studs, which the IR deliberately does not carry.

    ``geometry_build._wall_geometry`` skips cavity layers because a second solid on the
    structure layer's own polygon would z-fight it in 3D. For a section that omission is
    wrong — a batt between studs is exactly what the drawing is cut to show — so the fill is
    drawn here from the resolved layer, **unoutlined**, the way the roof's ``_CavityBand``
    is. The real fix is to emit the cavity as a solid *inset to the framing bay*, which does
    not z-fight; that is its own geometry change with its own risk.
    """
    openings = [op for op in model.openings if op.host_wall == wall.tag]
    for layer in wall.layers:
        if not layer.is_cavity or not layer.polygon:
            continue
        term = joints.termination(wall.uid, layer.name) if joints is not None else None
        band_z0, band_z1 = layer.band(wall)
        pattern = detail_hatch(layer.material_ref, layer.function)
        aia = _FUNCTION_LAYER.get(layer.function, "A-WALL")
        tag = f"{wall.tag}/{layer.name}"
        for (u0, u1) in ring_cut_intervals(layer.polygon, plane.axis, plane.station_m):
            top_left = term.z(u0) if term is not None else min(wall_top, band_z1)
            top_right = term.z(u1) if term is not None else min(wall_top, band_z1)
            rect = clip_rect(u0, u1, band_z0, max(top_left, top_right), crop)
            if rect is None:
                continue
            ru0, ru1, rz0, rz1 = rect
            if is_detail and 0 < (ru1 - ru0) < min_draw:
                grow = (min_draw - (ru1 - ru0)) / 2.0
                ru0, ru1 = ru0 - grow, ru1 + grow
            if abs(top_left - top_right) > 1e-6:
                b.extend(quad_nodes(ru0, ru1, rz0, min(top_left, rz1), min(top_right, rz1),
                                    aia, pattern, wall.uid, tag,
                                    material=layer.material_ref, outline=False))
                continue
            # The IR jamb-splits every depth layer; a cavity has no IR solid, so the split
            # around an opening has to happen here or the batt draws across the window.
            for (z0, z1, void) in _opening_splits(wall, openings, plane.axis,
                                                  plane.station_m, rz0, rz1):
                if void:
                    continue
                b.extend(rect_nodes(ru0, ru1, z0, z1, aia, pattern, wall.uid, tag,
                                    outline=False, material=layer.material_ref))


def _emit_glazing_lines(b, model, wall, plane: CutPlane, crop, is_detail) -> None:
    """The A-GLAZ line where the cut passes through an opening.

    All the *solid* bands around an opening now come out of the IR's jamb split; what has no
    solid, and so has to be drawn, is the glazing plane itself.
    """
    openings = [op for op in model.openings if op.host_wall == wall.tag]
    if not openings:
        return
    for layer in wall.layers:
        if layer.is_cavity or not layer.polygon:
            continue
        band_z0, band_z1 = layer.band(wall)
        for (u0, u1) in ring_cut_intervals(layer.polygon, plane.axis, plane.station_m):
            rect = clip_rect(u0, u1, band_z0, band_z1, crop)
            if rect is None:
                continue
            ru0, ru1, rz0, rz1 = rect
            for (z0, z1, void) in _opening_splits(wall, openings, plane.axis,
                                                  plane.station_m, rz0, rz1):
                if not void:
                    continue
                # A full-height glazing line spanning the whole crop reads as a mistake in a
                # junction detail — the cut is passing through pure glass with neither head
                # nor sill in frame. Drop it and let the neighbouring bands' edges show the
                # head/sill instead (#opening-void). Keep it where a real jamb edge is in
                # frame (an opening genuinely cut in a plan/elevation).
                if is_detail and crop is not None and z0 <= rz0 + 1e-9 and z1 >= rz1 - 1e-9:
                    continue
                mid = (ru0 + ru1) / 2 / M_PER_IN
                b.add(Polyline(points=((mid, z0 / M_PER_IN), (mid, z1 / M_PER_IN)),
                               layer="A-GLAZ", lineweight=0.18,
                               uid=wall.uid, tag=f"{wall.tag}-void"))


def _emit_solid_cut(b, model, solid, plane: CutPlane, crop) -> None:
    """A pour, footing, pad, pipe run or trim run, sliced out of its IR prism.

    Two things come free with the IR that the hand-rolled cut never had: the solid's
    ``voids`` now *split* the cut span (a section across a stair well stops drawing a slab
    straight through it), and the material is the resolver's ``catalog.material_ref``
    instead of a blanket "concrete".
    """
    element = model.geometry.by_uid(solid.uid)
    if element is None:
        return
    layer = "S-FNDN" if solid.category != "slab" else "A-SLAB"
    for part in element.parts:
        material = part.catalog.material_ref if part.catalog is not None else None
        for profile in slice_part(part, plane):
            band = profile_band(profile)
            if band is None:
                clipped = clip_polygon(profile.outline, crop)
                if len(clipped) >= 3:
                    points = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in clipped)
                    b.add(Polyline(points=points, layer=layer, closed=True, lineweight=0.18,
                                   uid=solid.uid, tag=solid.tag))
                    if material:
                        b.add(Hatch(boundary=points, pattern=material,
                                    layer="A-WALL-PATT", material=material))
                continue
            u0, u1, z0, top_left, top_right = band
            rect = clip_rect(u0, u1, z0, max(top_left, top_right), crop)
            if rect is None:
                continue
            b.extend(rect_nodes(*rect, layer, material, solid.uid, solid.tag,
                                material=material))


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


def _roof_layer_offsets(asm):
    """``(layer, d0, d1)`` per assembly layer, measured *down* from the structure datum.

    Positive is below the datum (the structure and anything inboard of it); negative is
    above (the whole outboard stack). The datum is ``roof_height_at`` — the top of the
    structure, which is what ``eave_z_m`` means. This used to run one cumulative depth
    downward from the first layer, which drew the entire above-structure stack *under* the
    rafters: on catlin's nailbase roof the section showed metal, vent mat, underlayment, OSB
    and 6" of polyiso hanging below the I-joists and nothing at all above them. It read as a
    plausible drawing, which is why it survived — the bands were in the right order, just
    mirrored about the wrong plane.
    """
    datum = structure_datum_m(asm)
    return [(layer, datum - c1, datum - c0) for (layer, c0, c1) in assembly_layer_spans(asm)]


def _roof_cavity_bands(asm):
    """``(layer, d0, d1)`` for each cavity fill, in the same datum frame.

    The batt between the rafters is not a layer of its own — it shares the bay's depth — so
    ``geometry_build`` does not give it a solid (it would z-fight the structure) and the IR
    cannot answer for it. It is the difference between a roof that reads as 11-7/8" of solid
    timber and one that reads as a batt between rafters, which is what the section is cut to
    show, so it is drawn here from the assembly. Held to the ceiling side: the remaining bay
    depth stays open.
    """
    datum = structure_datum_m(asm)
    bands = []
    for (layer, c0, c1) in assembly_layer_spans(asm):
        cavity = getattr(layer, "cavity", None)
        if cavity is None:
            continue
        fill = cavity.thickness.meters if cavity.thickness is not None else c1 - c0
        bands.append((_CavityBand(layer, cavity), datum - (c0 + fill), datum - c0))
    return bands


class _CavityBand:
    """A cavity fill dressed as a ``Layer`` so one band loop draws both.

    It borrows the host structure layer's function on purpose: the fill is clipped by the
    rafter plan span, exactly as its bay is, and carries no edge setback of its own.
    """

    __slots__ = ("name", "material_ref", "function", "_cavity")

    def __init__(self, host, cavity) -> None:
        self.name = f"{host.name} fill"
        self.material_ref = cavity.material_ref
        self.function = host.function
        self._cavity = cavity


def _emit_roof_cut(b, model, roof, plane: CutPlane, crop, joints=None,
                   ladder_labels=None) -> None:
    """One roof's cut: the above-structure stack sliced out of the IR, plus the bay fill.

    ``geometry_roofs.roof_parts`` builds exactly the layers the sky sees, each already
    offset perpendicular to the slope with a mitered ridge and already clipped to its own
    edge setback. The structure is **not** among them, and must not be: it is framing, and
    ``_emit_member_cuts`` draws it as members. Drawing it here as well is what made the roof
    structure appear twice in every detail — once as an assembly band, once as rafters.
    """
    element = model.geometry.by_uid(roof.uid)
    if element is None:
        return
    asm = model.plan.library.resolve_assembly(roof.assembly)
    detail = joints is not None
    drawn = False
    for part in element.parts:
        catalog = part.catalog
        if catalog is None:
            continue
        pattern = detail_hatch(catalog.material_ref, catalog.role) or "batt"
        for profile in slice_part(part, plane):
            clipped = clip_polygon(profile.outline, crop)
            if len(clipped) < 3:
                continue
            pts = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in clipped)
            drawn = True
            b.add(Polyline(points=pts, layer="A-ROOF", closed=True,
                           lineweight=0.18 if detail else 0.35,
                           uid=roof.uid, tag=f"{roof.tag}/{catalog.name}"))
            b.add(Hatch(boundary=pts, pattern=pattern, layer="A-WALL-PATT",
                        uid=roof.uid, material=catalog.material_ref))

    if asm is None:
        return
    _emit_roof_cavity(b, roof, asm, plane, crop)
    # No band of this roof reached the sheet: naming its layers would point at nothing.
    # Half the derived details are cut at a wall a long way from any roof.
    if detail and drawn:
        # The ladder names every band of the assembly, the drawn cavity fill included —
        # sorted outboard-first so the column reads in the order the drawing stacks.
        rungs = sorted(_roof_layer_offsets(asm) + _roof_cavity_bands(asm),
                       key=lambda entry: entry[1])
        roof_layer_ladder(roof, rungs, crop,
                          lambda u: roof_plane_z(roof, u), ladder_labels)


def _emit_roof_cavity(b, roof, asm, plane: CutPlane, crop) -> None:
    """The bay fill, as a sloped band under the structure datum, clipped to the rafters."""
    bands = _roof_cavity_bands(asm)
    if not bands:
        return
    intervals = ring_intervals(tuple(roof.footprint), plane)
    if not intervals:
        return
    ridge_u = roof_ridge_coordinate(roof)
    slope_along_cut = (
        (roof.ridge_direction == "y" and plane.axis == "x")
        or (roof.ridge_direction == "x" and plane.axis == "y")
    )
    structure_span = _rafter_plan_span(roof, plane.axis)

    def top_line(a: float, b_: float) -> list[tuple[float, float]]:
        if slope_along_cut:
            fold = [ridge_u] if ridge_u is not None and a < ridge_u < b_ else []
            return [(u, roof_plane_z(roof, u)) for u in ([a] + fold + [b_])]
        z = roof_plane_z(roof, plane.station_m)
        return [(a, z), (b_, z)]

    for (u0, u1) in intervals:
        for (layer, d0, d1) in bands:
            a, b_ = u0, u1
            if structure_span is not None:
                a, b_ = max(a, structure_span[0]), min(b_, structure_span[1])
            if b_ - a < 1e-9:
                continue
            top = top_line(a, b_)
            polygon = ([(u, z - d0) for (u, z) in top]
                       + [(u, z - d1) for (u, z) in reversed(top)])
            clipped = clip_polygon(polygon, crop)
            if len(clipped) < 3:
                continue
            pts = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in clipped)
            b.add(Hatch(boundary=pts,
                        pattern=detail_hatch(layer.material_ref, layer.function.value)
                        or "batt",
                        layer="A-WALL-PATT", uid=roof.uid, material=layer.material_ref))


