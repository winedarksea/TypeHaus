"""IFC roof emission: the faceted layer shell and its framing/trim children.

Split out of :mod:`typehaus.emit.ifc.emitter` because the roof is the one product whose
geometry is neither a plan prism nor a flat slab: it is a stack of pitched layers, each
clipped at its own plan setback, carrying members that rake with the plane.

Two things this module is responsible for getting right, both of which used to be missing:

* **the shell.** ``ResolvedRoof.layer_edge_setbacks`` gives every above-structure layer its
  own plan clip (the deck at the wall sheathing face, the foam at the wall furring, the
  metal running proud) — the same per-layer inset the glTF export and the three.js viewer
  build. The IFC roof used to be one flat 1" plate at the eave elevation, so it agreed with
  no other emitter and no roof detail.
* **the children.** Rafters, truss chords, gable studs, the derived fascia/soffit/gutter and
  the closure bands were emitted as bare ``IfcMember`` identities with no representation at
  all — present in the aggregation, invisible in any viewer. Each now carries a swept solid
  on its own axis, and lands in the IFC class its trade actually calls for.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.model.ids import derive_child_guid, derive_guid
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedRoof
from typehaus.resolve.roof_layer_setbacks import above_structure_layers

# A roof with no authored layers above its structure still has to be a solid: one nominal
# roofing skin, matching the glTF/viewer fallback so the three paths keep showing the same
# building rather than diverging on unlayered test fixtures.
_FALLBACK_SKIN_M = 0.05
# A degenerate member (a zero-height annotation record) still needs a sweepable section.
_MINIMUM_EXTENT_M = 1e-4

# Roof framing categories → IfcMemberTypeEnum (IFC4). Anything unmapped stays MEMBER rather
# than guessing: a wrong PredefinedType is worse than none for structural schedules.
_MEMBER_PREDEFINED_TYPE = {
    "rafter": "RAFTER", "barge_rafter": "RAFTER", "outlooker": "PURLIN",
    "top_chord": "CHORD", "bottom_chord": "CHORD", "truss_web": "STRUT",
    "stud": "STUD", "plate": "PLATE", "post": "POST",
}
# Envelope skin and trim are finishes fastened over the framing, not members: IfcCovering is
# the class Revit/ArchiCAD file them under. The gutter is neither — it is a drainage
# accessory, and follows the proxy convention the authored trim runs already use.
_COVERING_PREDEFINED_TYPE = {
    "fascia": "MOLDING", "soffit": "CEILING", "cladding": "CLADDING",
    "sheathing": "CLADDING", "furring": "CLADDING", "airgap": "CLADDING",
    "membrane": "MEMBRANE", "insulation": "INSULATION",
}
_PROXY_CATEGORIES = frozenset({"gutter", "flashing"})


def emit_roof(f: Any, body: Any, roof: ResolvedRoof, storeys: dict[str, Any],
              project_uuid: Any, lod: str, model: Any) -> None:
    """One ``IfcRoof`` carrying its layered pitched shell, plus its members at framed LOD."""
    element = ll.create_entity(f, "IfcRoof", name=roof.tag)
    element.GlobalId = derive_guid(project_uuid, roof.uid)
    assembly = (model.plan.library.resolve_assembly(roof.assembly)
                if roof.assembly else None)
    layers = above_structure_layers(assembly)
    shells = _shell_solids(roof, layers)
    if shells:
        _assign(f, element, ll.add_faceted_solids(f, body, shells))
    if assembly is not None and assembly.layers:
        # Same treatment a layered slab gets, so the receiving application reads the roof's
        # build-up instead of an untyped solid.
        ll.assign_material_layer_set(
            f, element,
            [{"name": layer.name, "material_ref": layer.material_ref,
              "thickness_m": layer.thickness.meters, "category": layer.function.value}
             for layer in assembly.layers],
            name=roof.assembly,
        )
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": roof.uid, "tag": roof.tag,
                                                   "assembly": roof.assembly})
    ll.assign_container(f, element, storeys[roof.storey])
    if lod == "framed" and roof.members:
        children = [_emit_member(f, body, roof, member, project_uuid)
                    for member in sorted(roof.members, key=lambda item: item.child_key)]
        ll.aggregate(f, element, children)


# --- the layered pitched shell -----------------------------------------------------------

def _plane_z(roof: ResolvedRoof, x: float, y: float) -> float:
    """Roof-plane elevation at a plan point, *unclamped*.

    Unclamped so a layer that runs proud of the footprint (the metal roofing's drip lap)
    lands just below the eave plane instead of being flattened onto it.
    """
    xs = [point[0] for point in roof.footprint]
    ys = [point[1] for point in roof.footprint]
    coordinate = y if roof.ridge_direction == "x" else x
    low, high = (min(ys), max(ys)) if roof.ridge_direction == "x" else (min(xs), max(xs))
    span = high - low
    if span <= 1e-9:
        return roof.eave_z_m
    if roof.form == "shed":
        return roof.eave_z_m + (coordinate - low) / span * (roof.ridge_z_m - roof.eave_z_m)
    midpoint = (low + high) / 2.0
    ratio = 1.0 - abs(coordinate - midpoint) / (span / 2.0)
    return roof.eave_z_m + ratio * (roof.ridge_z_m - roof.eave_z_m)


def _slope_factor(roof: ResolvedRoof) -> float:
    """``1/cos(theta)``: the vertical rise that a unit perpendicular layer offset costs."""
    xs = [point[0] for point in roof.footprint]
    ys = [point[1] for point in roof.footprint]
    span = ((max(ys) - min(ys)) if roof.ridge_direction == "x"
            else (max(xs) - min(xs)))
    run = span if roof.form == "shed" else span / 2.0
    if run <= 1e-9:
        return 1.0
    return math.hypot(1.0, (roof.ridge_z_m - roof.eave_z_m) / run)


def _layer_rect(roof: ResolvedRoof, entry: dict | None) -> tuple[float, float, float, float]:
    """The layer's plan rectangle from its serialized edge setbacks (positive inward).

    No drift compensation, unlike the glTF path: that correction exists because the mesh
    offsets each layer *perpendicular* to the slope, which walks the eave edge down-slope.
    The shell here is built between two sloped planes with vertical sides, so a plan setback
    is already a plan position and the serialized number is used as authored.
    """
    xs = [point[0] for point in roof.footprint]
    ys = [point[1] for point in roof.footprint]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    if entry is None:
        return minx, maxx, miny, maxy
    return (minx + float(entry.get("west", 0.0)), maxx - float(entry.get("east", 0.0)),
            miny + float(entry.get("south", 0.0)), maxy - float(entry.get("north", 0.0)))


def _plane_quads(roof: ResolvedRoof,
                 rect: tuple[float, float, float, float]) -> list[list[tuple[float, float]]]:
    """One counter-clockwise plan quad per roof plane, split at the footprint's ridge line."""
    minx, maxx, miny, maxy = rect
    if maxx - minx <= 1e-9 or maxy - miny <= 1e-9:
        return []
    xs = [point[0] for point in roof.footprint]
    ys = [point[1] for point in roof.footprint]
    if roof.form == "shed":
        return [[(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)]]
    if roof.ridge_direction == "x":
        ridge = min(max((min(ys) + max(ys)) / 2.0, miny), maxy)
        return [[(minx, miny), (maxx, miny), (maxx, ridge), (minx, ridge)],
                [(minx, ridge), (maxx, ridge), (maxx, maxy), (minx, maxy)]]
    ridge = min(max((min(xs) + max(xs)) / 2.0, minx), maxx)
    return [[(minx, miny), (ridge, miny), (ridge, maxy), (minx, maxy)],
            [(ridge, miny), (maxx, miny), (maxx, maxy), (ridge, maxy)]]


def _shell_solids(roof: ResolvedRoof, layers: list) -> list[list[list[tuple[float, ...]]]]:
    """A closed polyhedron per (layer x roof plane), stacked up the slope.

    Each is bounded below and above by the roof plane offset perpendicular by the running
    layer thickness, and by vertical sides. At the ridge the two planes' quads share the
    ridge line in plan, so their vertical joint *is* the miter plane of a symmetric gable —
    the layers close on each other with no wedge and no overlap.
    """
    setbacks = {entry["layer"]: entry for entry in (roof.layer_edge_setbacks or ())}
    factor = _slope_factor(roof)
    shells: list[list[list[tuple[float, ...]]]] = []
    base = 0.0
    for layer in (layers if layers else [None]):
        thickness = _FALLBACK_SKIN_M if layer is None else layer.thickness.meters
        entry = setbacks.get(layer.name) if layer is not None else None
        low, high = base * factor, (base + thickness) * factor
        for quad in _plane_quads(roof, _layer_rect(roof, entry)):
            shells.append(_prism_faces(roof, quad, low, high))
        base += thickness
    return shells


def _prism_faces(roof: ResolvedRoof, quad: list[tuple[float, float]],
                 low_m: float, high_m: float) -> list[list[tuple[float, float, float]]]:
    """Faces of one plane's layer prism: sloped bottom, sloped top, vertical sides."""
    return _closed_box([(x, y, _plane_z(roof, x, y) + low_m) for x, y in quad],
                       [(x, y, _plane_z(roof, x, y) + high_m) for x, y in quad])


def _closed_box(bottom: list[tuple[float, float, float]],
                top: list[tuple[float, float, float]]) -> list[list[tuple[float, ...]]]:
    """A closed shell over two matching rings — bottom reversed so every face faces out.

    Both rings must run counter-clockwise in plan; the bottom is reversed here so its normal
    points down, and the side quads then wind outward on their own.
    """
    faces: list[list[tuple[float, ...]]] = [list(reversed(bottom)), list(top)]
    for index in range(len(bottom)):
        following = (index + 1) % len(bottom)
        faces.append([bottom[index], bottom[following], top[following], top[index]])
    return faces


# --- members -----------------------------------------------------------------------------

def _emit_member(f: Any, body: Any, roof: ResolvedRoof, member: FramedMember,
                 project_uuid: Any) -> Any:
    """One roof member as a real product: right IFC class, swept solid on its own axis."""
    ifc_class, predefined = _member_class(member.category)
    child = ll.create_entity(f, ifc_class, name=f"{roof.tag}/{member.child_key}")
    child.GlobalId = derive_child_guid(project_uuid, roof.uid, member.child_key)
    if predefined is not None:
        child.PredefinedType = predefined
    representation = _member_representation(f, body, member)
    if representation is not None:
        _assign(f, child, representation)
    ll.ensure_pset(f, child, PSET_SOURCE, {
        "uid": roof.uid, "tag": f"{roof.tag}/{member.child_key}",
        "category": member.category, "profile": member.profile,
        "material": member.material or "", "trade": member.trade or "",
    })
    return child


def _member_class(category: str) -> tuple[str, str | None]:
    key = category.lower()
    if key in _PROXY_CATEGORIES:
        return "IfcBuildingElementProxy", None
    if key in _COVERING_PREDEFINED_TYPE:
        return "IfcCovering", _COVERING_PREDEFINED_TYPE[key]
    return "IfcMember", _MEMBER_PREDEFINED_TYPE.get(key, "MEMBER")


def _member_representation(f: Any, body: Any, member: FramedMember) -> Any | None:
    """Sweep the member's rectangular section along its true 3D axis.

    The section rides the axis through its own centroid, so the solid's top and bottom faces
    land on exactly the planes the member IR names (``z1``/``z0`` at each end) — the same
    surfaces every other emitter draws — while the ends are cut square to the member, which
    is how the stick is actually cut. A vertical member (``p0 == p1``) sweeps straight up.

    A member whose *height* changes end to end is not a sweep at all — the gable closure
    bands grow from the heel to the ridge — and gets a faceted solid instead of a section
    stretched to a wrong constant depth.
    """
    section = cross_section(member.profile)
    width = max(section.width_m, _MINIMUM_EXTENT_M)
    height = max(member.z1_m - member.z0_m, _MINIMUM_EXTENT_M)
    dx, dy = member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]
    run = math.hypot(dx, dy)
    if run >= 1e-9 and _is_tapered(member):
        return ll.add_faceted_solids(f, body, [_tapered_box(member, width, dx, dy, run)])
    if run < 1e-9:
        orient = member.orient or (1.0, 0.0)
        norm = math.hypot(orient[0], orient[1]) or 1.0
        return ll.add_swept_member(
            f, body, origin_m=(member.p0[0], member.p0[1], member.z0_m),
            axis=(0.0, 0.0, 1.0), ref_direction=(orient[0] / norm, orient[1] / norm, 0.0),
            length_m=height, width_m=width,
            depth_m=max(section.depth_m, _MINIMUM_EXTENT_M),
        )
    start_mid = (member.z0_m + member.z1_m) / 2.0
    end_mid = ((member.z0_m if member.z0_end_m is None else member.z0_end_m)
               + (member.z1_m if member.z1_end_m is None else member.z1_end_m)) / 2.0
    length = math.hypot(dx, dy, end_mid - start_mid)
    if length < _MINIMUM_EXTENT_M:
        return None
    # ``height`` is the member's *vertical* extent; the swept section is perpendicular to the
    # axis, so its depth is that extent foreshortened by the rake — which puts the two faces
    # back on the sloped planes the IR describes.
    return ll.add_swept_member(
        f, body, origin_m=(member.p0[0], member.p0[1], start_mid),
        axis=(dx / length, dy / length, (end_mid - start_mid) / length),
        ref_direction=(-dy / run, dx / run, 0.0),
        length_m=length, width_m=width, depth_m=max(height * run / length,
                                                    _MINIMUM_EXTENT_M),
    )


def _is_tapered(member: FramedMember) -> bool:
    """Whether the member's vertical extent differs end to end (no constant section)."""
    if member.z0_end_m is None and member.z1_end_m is None:
        return False
    end_height = ((member.z1_m if member.z1_end_m is None else member.z1_end_m)
                  - (member.z0_m if member.z0_end_m is None else member.z0_end_m))
    return abs(end_height - (member.z1_m - member.z0_m)) > _MINIMUM_EXTENT_M


def _tapered_box(member: FramedMember, width_m: float,
                 dx: float, dy: float, run: float) -> list[list[tuple[float, ...]]]:
    """The member as a vertical-sided solid whose top and bottom follow its own end
    elevations — the same eight corners the glTF and viewer member boxes use."""
    half_x, half_y = -dy / run * width_m / 2.0, dx / run * width_m / 2.0
    (ax, ay), (bx, by) = member.p0, member.p1
    z0_end = member.z0_m if member.z0_end_m is None else member.z0_end_m
    z1_end = member.z1_m if member.z1_end_m is None else member.z1_end_m
    # A band that runs out to nothing at one end (a gable closure springing off the eave)
    # would close the shell on a zero-area face, which no importer can tessellate.
    z1_start = max(member.z1_m, member.z0_m + _MINIMUM_EXTENT_M)
    z1_end = max(z1_end, z0_end + _MINIMUM_EXTENT_M)
    ring = ((ax - half_x, ay - half_y, member.z0_m, z1_start),
            (bx - half_x, by - half_y, z0_end, z1_end),
            (bx + half_x, by + half_y, z0_end, z1_end),
            (ax + half_x, ay + half_y, member.z0_m, z1_start))
    return _closed_box([(x, y, low) for x, y, low, _high in ring],
                       [(x, y, high) for x, y, _low, high in ring])


def _assign(f: Any, element: Any, representation: Any) -> None:
    element.Representation = f.createIfcProductDefinitionShape(None, None, [representation])
    ll.ensure_local_placement(f, element)
