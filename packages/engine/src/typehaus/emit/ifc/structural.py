"""IFC emission for structure: framing members, resolved solids, floors, braces, stairs.

Split out of :mod:`typehaus.emit.ifc.emitter` alongside the architectural, MEP and site
modules (→ AGENTS.md §1.1). What lands here is everything whose IFC class follows what
carries load rather than what encloses space: the generated members a framed parent
aggregates, the resolved-solid class table (the one place a category becomes an IFC class,
with ``IfcFooting`` as the deliberate pour fallback), a floor's deck and its joists, a
brace's raked sticks, and the stair those members hang off.

``_emit_framed_member`` sits here rather than with the walls because a wall and a stair
generate the same member pack from one class map (``roof.member_class``), and a stud has
to file identically whichever parent generated it.
"""

from __future__ import annotations

from typing import Any

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.emit.ifc.roof import member_class, member_representation
from typehaus.model.ids import derive_child_guid, derive_guid
from typehaus.resolve.framing.profiles import cross_section, plan_cross_section_m
from typehaus.resolve.geometry import rect_between
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.sweep import (
    clean_path,
    is_round_profile,
    profile_radius_m,
    sweep_leg_axes,
)

# Profiles that describe a board tapered *in plan* (the winder tread runs from a newel-face
# sliver to a full nosing): no constant cross-section swept along the axis can represent
# one, so its member keeps the bare pre-representation form instead of a wrong box.
_UNSWEEPABLE_PROFILES = frozenset({"tapered tread"})


def _member_body(f: Any, body: Any, member: Any) -> Any | None:
    """``member_representation`` with the graceful degradation the generated packs need.

    Wall and stair packs run through thousands of generated members; one profile the
    section catalog cannot honestly sweep must degrade to a bare (representation-
    free) member, never abort the whole export.
    """
    if member.plan_outline is not None:
        return ll.add_prisms_from_profiles(f, body, [member.plan_outline],
                                            member.z1_m - member.z0_m, member.z0_m)
    if member.profile in _UNSWEEPABLE_PROFILES:
        return None
    try:
        return member_representation(f, body, member)
    except Exception:  # noqa: BLE001 - a bare member beats a failed export
        return None


def _emit_framed_member(f: Any, body: Any, parent_tag: str, parent_uid: str,
                        member: Any, project_uuid: Any) -> Any:
    """One generated wall/stair member as a real product (roof-member precedent).

    Same class map and swept-solid path the roof and brace members use, so a stud files
    as ``IfcMember``/STUD with true geometry rather than a bare identity placeholder.
    """
    ifc_class, predefined = member_class(member.category)
    child = ll.create_entity(f, ifc_class, name=f"{parent_tag}/{member.child_key}")
    child.GlobalId = derive_child_guid(project_uuid, parent_uid, member.child_key)
    if predefined is not None:
        child.PredefinedType = predefined
    representation = _member_body(f, body, member)
    if representation is not None:
        ll.assign_representation(f, child, representation)
    ll.ensure_pset(f, child, PSET_SOURCE, {
        "uid": parent_uid, "tag": f"{parent_tag}/{member.child_key}",
        "category": member.category, "profile": member.profile,
    })
    return child


# What a resolved solid becomes in IFC: ``(class, PredefinedType | None)``. A category with
# no entry falls through to ``IfcFooting``, which is right for a pour and wrong for anything
# else — every category that is not a pour belongs in this table.
#
# The drainage rows are the ones IFC actually has homes for, and using them is what makes the
# export read as a stormwater system in Revit/Bonsai rather than as loose proxies:
# ``IfcPipeSegment`` for anything the water runs *through* (its PredefinedType separates the
# hung channel from the rigid leader from the flexible buried tile), and
# ``IfcDistributionChamberElement`` for anything it collects *in*. ``SOAKAWAY`` has no enum
# member, so the drywell is USERDEFINED with an ObjectType that names it.
_SOLID_IFC_CLASS: dict[str, tuple[str, str | None]] = {
    "slab": ("IfcSlab", None), "column": ("IfcColumn", None), "beam": ("IfcBeam", None),
    "railing": ("IfcRailing", None), "dowel": ("IfcReinforcingBar", None),
    # Guard infill exports as part of the railing it fills, not as ``IfcPlate``: ``diff/
    # semantic.py`` has no ``IfcPlate`` row, so a glass lite exported that way would vanish
    # from the ``haus diff`` census rather than round-trip.
    "railing_infill": ("IfcRailing", None), "railing_glass": ("IfcRailing", None),
    "connector": ("IfcMechanicalFastener", None),
    # Not fasteners in the IFC sense: a snow-retention rail and a seam clamp are accessories
    # mounted ON the roof skin, not hardware joining two structural members. ``diff/
    # semantic.py`` carries an ``IfcDiscreteAccessory`` row, so both still round-trip.
    "snow_guard": ("IfcDiscreteAccessory", None),
    "seam_clamp": ("IfcDiscreteAccessory", None),
    "panel_strap": ("IfcDiscreteAccessory", None),
    "vent": ("IfcBuildingElementProxy", None),
    "fascia": ("IfcCovering", None), "soffit": ("IfcCovering", None),
    "flashing": ("IfcCovering", None),
    "thermal_break": ("IfcBuildingElementProxy", None),
    # stormwater (→ emit/trades.py DRAINAGE_CATEGORIES)
    "gutter": ("IfcPipeSegment", "GUTTER"),
    "downspout": ("IfcPipeSegment", "RIGIDSEGMENT"),
    "drain_tile": ("IfcPipeSegment", "FLEXIBLESEGMENT"),
    "sump": ("IfcDistributionChamberElement", "SUMP"),
    "french_drain": ("IfcDistributionChamberElement", "TRENCH"),
    "drywell": ("IfcDistributionChamberElement", "USERDEFINED"),
}


#: Where the IFC4 enum has no member for what the thing is, ``ObjectType`` carries the name.
_SOLID_OBJECT_TYPE = {"drywell": "SOAKAWAY"}


def _emit_solid(f: Any, body: Any, solid: Any, storeys: dict[str, Any], project_uuid: Any,
                model: Any = None) -> Any:
    """One resolved solid as its IFC element. Returns it, so systems can group members."""
    ifc_class, predefined_type = _SOLID_IFC_CLASS.get(solid.category, ("IfcFooting", None))
    element = ll.create_entity(f, ifc_class, name=solid.tag)
    if predefined_type is not None:
        element.PredefinedType = predefined_type
    object_type = _SOLID_OBJECT_TYPE.get(solid.category)
    if object_type is not None:
        element.ObjectType = object_type
    element.GlobalId = derive_guid(project_uuid, solid.uid)
    representation = _solid_body(f, body, solid)
    if representation is not None:
        ll.assign_representation(f, element, representation)
    if model is not None:
        _assign_solid_material(f, element, solid, model)
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": solid.uid, "tag": solid.tag,
                                               "category": solid.category})
    ll.assign_container(f, element, storeys[solid.storey])
    return element


def _solid_body(f: Any, body: Any, solid: Any) -> Any:
    """A solid's Body representation: a swept run if it is one, else the plan prism.

    A run carries its own 3D centreline (→ ``resolve/sweep.py``), and IFC has the two idioms
    for it: a round section is one ``IfcSweptDiskSolid`` over an ``IfcPolyline`` directrix —
    what a pipe and a round handrail both are in IFC4 — and a shaped one is an extrusion per
    leg. Either way the run is *one* element with one representation, where a raked rail used
    to arrive as 292 separate ``IfcRailing``s, one per 1-1/2" of fall.
    """
    if solid.sweep is not None:
        profile = tuple(solid.sweep.profile)
        path = clean_path(solid.sweep.path)
        if len(path) < 2:
            return None
        if is_round_profile(profile):
            return ll.add_swept_disk(f, body, points_m=[tuple(p) for p in path],
                                     radius_m=profile_radius_m(profile))
        return ll.add_swept_run(f, body, profile_points=[tuple(p) for p in profile],
                                legs=sweep_leg_axes(solid.sweep))
    if not solid.outline:
        return None
    return ll.add_prism_from_profile(f, body, solid.outline, solid.z1_m - solid.z0_m,
                                     solid.z0_m, solid.voids)


def _assign_solid_material(f: Any, element: Any, solid: Any, model: Any) -> None:
    """Attach an IfcMaterialLayerSet to a slab that carries an authored assembly (e.g. the
    composite / aluminum deck surfaces) so Revit reads its material, like walls do."""
    if not solid.assembly:
        return
    assembly = model.plan.library.resolve_assembly(solid.assembly)
    if assembly is None or not assembly.layers:
        return
    ll.assign_material_layer_set(
        f, element,
        [{"name": ly.name, "material_ref": ly.material_ref,
          "thickness_m": ly.thickness.meters, "category": ly.function.value}
         for ly in assembly.layers],
        name=solid.assembly,
    )


def _emit_construction_return(f: Any, body: Any, ret: Any, storeys: dict[str, Any],
                              project_uuid: Any) -> None:
    """A ConstructionRule return (#45) as an ``IfcCovering``.

    The membrane / foam / liner / masonry lap that closes a resolved junction is a *finish*
    on the face it returns onto, not structure — so it never wanted a ``ResolvedSolid`` (the
    resolver emits none). The record's own outline/z carry the geometry; the overlay metadata
    (lap, sealant, flashing, continuity) rides along on the source pset.
    """
    element = ll.create_entity(f, "IfcCovering", name=ret.tag)
    element.GlobalId = derive_guid(project_uuid, ret.uid)
    if ret.outline:
        ll.assign_representation(
            f, element, ll.add_prism_from_profile(
                f, body, ret.outline, ret.z1_m - ret.z0_m, ret.z0_m)
        )
    ll.ensure_pset(f, element, PSET_SOURCE, {
        "uid": ret.uid, "tag": ret.tag, "kind": ret.kind,
        "category": f"return:{ret.takeoff_category or ret.kind}",
        "material_ref": ret.material_ref,
        "element_tags": ",".join(ret.element_tags),
        "lap_m": f"{ret.lap_m:.6f}",
        "thermal_continuity": ret.thermal_continuity,
        "air_vapor_continuity": ret.air_vapor_continuity,
        "sealant": ret.sealant or "",
        "flashing": ret.flashing or "",
        "returning_layer": ret.returning_layer or "",
        "condition_key": ret.condition_key or "",
    })
    ll.assign_container(f, element, storeys[ret.storey])


_BEAM_PREDEFINED_TYPE = {"joist": "JOIST", "rim": "BEAM", "blocking": "BEAM"}


def _emit_floor(f: Any, body: Any, floor: Any, storeys: dict[str, Any],
                project_uuid: Any, model: ResolvedModel) -> None:
    """Emit a floor's subfloor deck as an ``IfcSlab``, and each joist/rim as an ``IfcBeam``.

    House decks and the porch/balcony deck both resolve to ``FramedMember`` joists.
    Emitting them here as IfcBeam (JOIST-predefined) gives BIM consumers the structural
    members with stable child GUIDs, following the standalone-beam pattern (``_emit_solid``
    for category ``beam``)."""
    container = storeys.get(floor.storey)
    if container is None:
        return
    _emit_deck(f, body, floor, container, project_uuid, model)
    for member in sorted(floor.members, key=lambda item: item.child_key):
        if (member.p0[0] - member.p1[0]) ** 2 + (member.p0[1] - member.p1[1]) ** 2 < 1e-12:
            continue  # a zero-length record has no sweepable footprint
        # The prism below is z1-z0 tall, so its plan half-width is the face that is not
        # standing up — see ``plan_cross_section_m``. Floor members are all on edge today,
        # but reading the rule keeps this from drifting if a flat one ever lands here.
        half = plan_cross_section_m(cross_section(member.profile),
                                    member.z1_m - member.z0_m) / 2.0
        profile = rect_between(member.p0, member.p1, -half, half)
        beam = ll.create_entity(f, "IfcBeam", name=f"{floor.tag}/{member.child_key}")
        beam.GlobalId = derive_child_guid(project_uuid, floor.uid, member.child_key)
        beam.PredefinedType = _BEAM_PREDEFINED_TYPE.get(member.category, "BEAM")
        ll.assign_representation(f, beam, ll.add_prism_from_profile(
            f, body, profile, max(member.z1_m - member.z0_m, 1e-4), member.z0_m,
        ))
        ll.ensure_pset(f, beam, PSET_SOURCE, {
            "uid": floor.uid, "tag": f"{floor.tag}/{member.child_key}",
            "category": member.category, "profile": member.profile,
        })
        ll.assign_container(f, beam, container)


def _emit_deck(f: Any, body: Any, floor: Any, container: Any, project_uuid: Any,
               model: ResolvedModel) -> None:
    """The subfloor sheet over a floor's joists, as an ``IfcSlab``/FLOOR.

    One of the plan's blessed diffs: *no* emitter drew a deck, so a floor exported as a field
    of beams with nothing on them — joists hanging in space in Revit exactly as they did in
    the viewer. The outline, its openings and its elevations come from the IR, so the slab
    the exporter writes and the sheet the viewer draws are the same sheet.
    """
    geometry = getattr(model, "geometry", None)
    element = geometry.by_uid(floor.uid) if geometry is not None else None
    part = next((p for p in element.parts if p.key == "deck"), None) if element else None
    if part is None:
        return
    prism = part.solids[0]
    slab = ll.create_entity(f, "IfcSlab", name=f"{floor.tag}/deck")
    slab.GlobalId = derive_child_guid(project_uuid, floor.uid, "deck")
    slab.PredefinedType = "FLOOR"
    ll.assign_representation(f, slab, ll.add_prism_from_profile(
        f, body, list(prism.ring), prism.z1_m - prism.z0_m, prism.z0_m, prism.voids))
    ll.ensure_pset(f, slab, PSET_SOURCE, {
        "uid": floor.uid, "tag": f"{floor.tag}/deck",
        "material": getattr(floor, "deck_material_ref", None) or "",
    })
    ll.assign_container(f, slab, container)


def _emit_brace(f: Any, body: Any, brace: Any, storeys: dict[str, Any],
                project_uuid: Any) -> None:
    """Each diagonal brace member as an ``IfcMember``/BRACE swept along its true 3D axis.

    A brace is raked by construction, and ``_emit_floor``'s vertical prism would flatten it
    to a box between its two end elevations. ``member_representation`` already sweeps a
    section along the real axis for raked roof sticks, so reuse it rather than growing a
    second rake path here."""
    container = storeys.get(brace.storey)
    if container is None:
        return
    materials: dict[str, Any] = {}
    for member in sorted(brace.members, key=lambda item: item.child_key):
        child = ll.create_entity(f, "IfcMember", name=f"{brace.tag}/{member.child_key}")
        child.GlobalId = derive_child_guid(project_uuid, brace.uid, member.child_key)
        child.PredefinedType = "BRACE"
        representation = member_representation(f, body, member)
        if representation is not None:
            ll.assign_representation(f, child, representation)
        # The member's resolved finish material (a knee brace's POST_WHITE_PAINT reduces to
        # its structure layer's ref at resolve). The association follows the
        # ``_assign_solid_material`` pattern, but as a single ``IfcMaterial`` rather than a
        # layer set: a stick has one body, not a stack of thicknesses. Without it the BRACE
        # exported with no material at all while the pillars beside it carried theirs.
        if member.material:
            material = materials.get(member.material)
            if material is None:
                # IfcMaterial is unrooted (no GlobalId/OwnerHistory) — bypass create_entity.
                material = f.create_entity("IfcMaterial", Name=member.material)
                materials[member.material] = material
            f.create_entity("IfcRelAssociatesMaterial", GlobalId=ll.new_guid(),
                            RelatedObjects=[child], RelatingMaterial=material)
        ll.ensure_pset(f, child, PSET_SOURCE, {
            "uid": brace.uid, "tag": f"{brace.tag}/{member.child_key}",
            "category": member.category, "profile": member.profile,
            "connection": member.connection or "",
        })
        ll.assign_container(f, child, container)


def _emit_stair(f: Any, body: Any, stair: Any, storeys: dict[str, Any], project_uuid: Any,
                lod: str) -> None:
    element = ll.create_entity(f, "IfcStair", name=stair.tag)
    element.GlobalId = derive_guid(project_uuid, stair.uid)
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": stair.uid, "tag": stair.tag})
    ll.assign_container(f, element, storeys[stair.storey])
    if lod != "framed":
        return
    members = [_emit_framed_member(f, body, stair.tag, stair.uid, member, project_uuid)
               for member in sorted(stair.members, key=lambda item: item.child_key)]
    if members:
        ll.aggregate(f, element, members)
