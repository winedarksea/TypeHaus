"""IFC roof emission: the faceted layer shell and its framing/trim children.

Split out of :mod:`typehaus.emit.ifc.emitter` because the roof is the one product whose
geometry is neither a plan prism nor a flat slab: it is a stack of pitched layers, each
clipped at its own plan setback, carrying members that rake with the plane.

Two things this module is responsible for getting right:

* **the shell.** Every above-structure layer is its own closed solid, clipped at its own
  plan setback (the deck at the wall sheathing face, the foam at the wall furring, the metal
  running proud). The bands come from the derived-geometry IR
  (``resolve/geometry_roofs.py``) rather than from a fourth private copy of the math, so
  IFC, the GLB and the viewer are the same roof by construction.
* **the children.** Rafters, truss chords, gable studs, the derived fascia/soffit/gutter and
  the closure bands each carry a swept solid on their own axis, and land in the IFC class
  their trade actually calls for.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.model.ids import derive_child_guid, derive_guid
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry_roofs import roof_parts
from typehaus.resolve.model import FramedMember, ResolvedRoof

# The no-layers-above-structure fallback skin lives once, in `resolve/geometry_roofs.py`.
# A degenerate member (a zero-height annotation record) still needs a sweepable section.
_MINIMUM_EXTENT_M = 1e-4

# Framing categories → IfcMemberTypeEnum (IFC4), shared by the roof, wall and stair member
# emitters (``member_class`` below). Anything unmapped stays MEMBER rather than guessing: a
# wrong PredefinedType is worse than none for structural schedules — that is deliberately
# where "header", "tread", "blocking", "landing" and "landing_framing" land, since IFC4's
# enum has no closer term for any of them.
_MEMBER_PREDEFINED_TYPE = {
    "rafter": "RAFTER", "barge_rafter": "RAFTER", "outlooker": "PURLIN",
    "top_chord": "CHORD", "bottom_chord": "CHORD", "truss_web": "STRUT",
    "stud": "STUD", "plate": "PLATE", "post": "POST",
    # Wall framing: the opening pack's verticals are studs by trade and by function; the
    # sill and the raked plate are plates laid on or under them.
    "king": "STUD", "jack": "STUD", "cripple": "STUD",
    "sill": "PLATE", "raked_plate": "PLATE",
    # Stair carriage: STRINGER is the enum's own word; a newel is a post that happens to
    # carry winders.
    "stringer": "STRINGER", "newel": "POST",
}
# Envelope skin and trim are finishes fastened over the framing, not members: IfcCovering is
# the class Revit/ArchiCAD file them under. The gutter is neither — it is a drainage
# accessory, and follows the proxy convention the authored trim runs already use.
_COVERING_PREDEFINED_TYPE = {
    "fascia": "MOLDING", "soffit": "CEILING", "cladding": "CLADDING",
    "sheathing": "CLADDING", "furring": "CLADDING", "airgap": "CLADDING",
    "membrane": "MEMBRANE", "insulation": "INSULATION",
    "ridge_cap": "MOLDING", "corner_trim": "MOLDING",
}
# The gutter is a drainage accessory rather than a member or a finish covering. The vented
# ridge cap is *not* here: it is formed trim over the roofing and files as an IfcCovering
# MOLDING above, same as the corner trim it meets.
_PROXY_CATEGORIES = frozenset({"gutter", "flashing"})


def emit_roof(f: Any, body: Any, roof: ResolvedRoof, storeys: dict[str, Any],
              project_uuid: Any, lod: str, model: Any) -> None:
    """One ``IfcRoof`` carrying its layered pitched shell, plus its members at framed LOD."""
    element = ll.create_entity(f, "IfcRoof", name=roof.tag)
    element.GlobalId = derive_guid(project_uuid, roof.uid)
    assembly = (model.plan.library.resolve_assembly(roof.assembly)
                if roof.assembly else None)
    shells = _shell_solids(roof, assembly)
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

def _shell_solids(roof: ResolvedRoof, assembly: Any) -> list[list[list[tuple[float, ...]]]]:
    """One closed polyhedron per above-structure layer, straight from the IR.

    This module used to build its own: quads split at the ridge, offset *vertically* by the
    running thickness times ``1/cos(theta)``, with vertical sides and the serialized setbacks
    used as authored. That is a defensible reading of the same inputs, and it was the fourth
    copy of this math — but it disagreed with the two the user actually looks at (the viewer
    and the GLB), which offset each layer perpendicular to the slope and compensate the eave
    drift that introduces. The plan blesses the perpendicular reading as canonical, so the
    shell IFC exports changes shape slightly here and the exported assembly finally matches
    what the viewer draws. A band is a triangle soup rather than six planar faces, which is
    what a mitered ridge costs; it is still a closed brep.
    """
    shells: list[list[list[tuple[float, ...]]]] = []
    for part in roof_parts(roof, assembly):
        for mesh in part.solids:
            shells.append([[mesh.positions[index] for index in triangle]
                           for triangle in mesh.triangles])
    return shells


def _closed_box(bottom: list[tuple[float, float, float]],
                top: list[tuple[float, float, float]]) -> list[list[tuple[float, ...]]]:
    """A closed shell over two matching rings — bottom reversed so every face faces out.

    Both rings must run counter-clockwise in plan; the bottom is reversed here so its normal
    points down, and the side quads then wind outward on their own. What is left of the old
    shell builder: a tapered member (a closure band growing from heel to ridge) is faceted
    rather than swept, and this is the shell it files as.
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
    ifc_class, predefined = member_class(member.category)
    child = ll.create_entity(f, ifc_class, name=f"{roof.tag}/{member.child_key}")
    child.GlobalId = derive_child_guid(project_uuid, roof.uid, member.child_key)
    if predefined is not None:
        child.PredefinedType = predefined
    representation = member_representation(f, body, member)
    if representation is not None:
        _assign(f, child, representation)
    ll.ensure_pset(f, child, PSET_SOURCE, {
        "uid": roof.uid, "tag": f"{roof.tag}/{member.child_key}",
        "category": member.category, "profile": member.profile,
        "material": member.material or "", "trade": member.trade or "",
    })
    return child


def member_class(category: str) -> tuple[str, str | None]:
    """(IFC class, PredefinedType) for a generated framing member's category.

    Shared by every member emitter (roof, wall, stair) so a stud files identically
    whichever parent generated it.
    """
    key = category.lower()
    if key in _PROXY_CATEGORIES:
        return "IfcBuildingElementProxy", None
    if key in _COVERING_PREDEFINED_TYPE:
        return "IfcCovering", _COVERING_PREDEFINED_TYPE[key]
    return "IfcMember", _MEMBER_PREDEFINED_TYPE.get(key, "MEMBER")


def member_representation(f: Any, body: Any, member: FramedMember) -> Any | None:
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
