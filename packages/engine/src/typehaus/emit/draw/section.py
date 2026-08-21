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

from typehaus.emit.draw.palette import aia_layer, detail_hatch
from typehaus.emit.draw.scene import Frame, Hatch, Polyline, Scene, SceneBuilder, Text
from typehaus.emit.draw.section_cavity import (
    emit_roof_cavity,
    emit_wall_cavity,
    opening_splits,
)
from typehaus.emit.draw.section_clip import (
    clip_polygon,
    clip_rect,
    profile_band,
    quad_nodes,
    rect_nodes,
)
from typehaus.emit.draw.section_labels import (
    DrawnBand,
    emit_ladders,
    roof_layer_ladder,
    wall_layer_ladder,
)
from typehaus.emit.draw.section_members import _emit_member_cuts, emit_framing_cuts
from typehaus.model.enums import SliceKind
from typehaus.model.views import Slice
from typehaus.quantities import M_PER_IN, m, pt
from typehaus.resolve.geometry_slice import CutPlane, ring_intervals, slice_part
from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.resolve.roof_geometry import roof_plane_z

# ``section.py`` is the name every caller — the CLI, the server, the detail package and the
# tests — imports a cut from, so the pieces split out of it stay reachable here.
__all__ = [
    "build_center_section",
    "build_section",
]


def build_section(model: ResolvedModel, view: Slice, joints=None,
                  frame: Frame | None = None) -> Scene:
    """Build the section/detail IR scene for one authored Slice.

    ``joints`` (a :class:`~typehaus.emit.draw.joints.JointPlan`) is detail-mode only; when
    given, per-layer terminations, sloped roof bands, cut framing members, and treatment
    fills are honored. ``None`` preserves plain-section behaviour (existing callers/goldens).

    ``frame`` is the paper the drawing will be laid out on. It reaches the cut for one
    reason: annotation is sized in *points*, and turning a printed size into the model
    inches a ladder places in needs the scale. ``None`` keeps the frameless convention, so a
    plain building section letters exactly as it did.
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
    scale = frame.scale if frame is not None else None

    # Layer-label ladders are collected per wall and emitted once, after every wall has
    # been cut, so ladders from different walls (and later the seed-callout column) can be
    # dodged against each other instead of overprinting.
    plane = CutPlane(axis=direction, station_m=station)
    ladder_labels: list = []
    for wall in model.walls:
        _emit_wall_cut(b, model, wall, plane, crop, is_detail, min_draw,
                       joints, ladder_labels, scale)

    for solid in model.solids:
        _emit_solid_cut(b, model, solid, plane, crop)

    for roof in model.roofs:
        _emit_roof_cut(b, model, roof, plane, crop, joints, ladder_labels, scale)

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

    emit_ladders(b, ladder_labels, scale)

    if crop is not None:
        (cu0, cz0), (cu1, cz1) = crop
        b.add(Text(anchor=((cu0 / M_PER_IN), (cz1 / M_PER_IN) + 6.0),
                   content=view.tag, height=4.0, align="left"))
    return b.build().model_copy(update={"frame": frame})


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
                   is_detail, min_draw, joints=None, ladder_labels=None,
                   scale=None) -> None:
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
        aia = aia_layer(function)
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

    emit_wall_cavity(b, model, wall, plane, crop, is_detail, min_draw, wall_top, joints)
    _emit_glazing_lines(b, model, wall, plane, crop, is_detail)
    wall_layer_ladder(wall, label_entries, wall_top, crop, ladder_labels, scale)


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
        for (u0, u1) in ring_intervals(layer.polygon, plane):
            rect = clip_rect(u0, u1, band_z0, band_z1, crop)
            if rect is None:
                continue
            ru0, ru1, rz0, rz1 = rect
            for (z0, z1, void) in opening_splits(wall, openings, plane.axis,
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


def _emit_roof_cut(b, model, roof, plane: CutPlane, crop, joints=None,
                   ladder_labels=None, scale=None) -> None:
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
    bands: list[DrawnBand] = []
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
            b.add(Polyline(points=pts, layer="A-ROOF", closed=True,
                           lineweight=0.18 if detail else 0.35,
                           uid=roof.uid, tag=f"{roof.tag}/{catalog.name}"))
            b.add(Hatch(boundary=pts, pattern=pattern, layer="A-WALL-PATT",
                        uid=roof.uid, material=catalog.material_ref))
            bands.append(DrawnBand(catalog.name,
                                   (catalog.thickness_m or 0.0) / M_PER_IN, pts))

    if asm is None:
        return
    bands += emit_roof_cavity(b, roof, asm, plane, crop)
    # No band of this roof reached the sheet: naming its layers would point at nothing.
    # Half the derived details are cut at a wall a long way from any roof.
    if detail and bands:
        # The ladder names every band that was drawn, the cavity fill included, and aims
        # each leader by measuring that band's own outline — see ``roof_layer_ladder``.
        roof_layer_ladder(roof, bands, crop,
                          lambda u: roof_plane_z(roof, u), ladder_labels, scale)
