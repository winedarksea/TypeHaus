"""The IFC4 structural analysis view: nodes, members, supports and their claims.

The physical IFC says *this beam is a 3-1/2" x 11-7/8" glulam here*. This says *this member
spans between these two nodes, released at both ends, on columns fixed at their bases*.
An engineer re-running the calculation in SAP2000, ETABS or Bonsai loads it instead of
re-modelling the building from the drawings — and every hand re-model is a chance to model
it differently from what was built.

Everything here is a read of ``analytical/graph.AnalyticalModel`` and nothing else, so the
IFC, the DXF, the CSV and the PyNite script cannot disagree about which node a beam lands
on. The claims (a base fixity, an end release) carry their ``basis`` into
``Pset_TH_Analytical``, where a reviewer can disagree with the words rather than reverse-
engineer the number.

**The profile set is shared with the physical member.** Two section definitions for one
member is how the analytical and physical models drift apart, so a curve member is
registered as a *companion* of its physical element on the one ``ProfileCollector``
(``profiles.py``) and lands in the same ``IfcRelAssociatesMaterial``. Standalone — the
fixture test, ``haus analysis`` — there is no physical element, and the member gets its own
set built from the graph's own ``CrossSection``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from typehaus._meta import IFC_APP_NAME
from typehaus.analytical.graph import AnalyticalModel, Member, Node
from typehaus.emit.ifc import lowlevel as ll
from typehaus.emit.ifc.lowlevel_units import assign_structural_units
from typehaus.emit.ifc.profiles import ProfileCollector
from typehaus.model.ids import derive_child_guid

#: The property set every analytical entity carries. ``Pset_``-prefixed because a name
#: outside that space is dropped by strict importers; ``_TH_`` because nobody else uses it.
PSET_ANALYTICAL = "Pset_TH_Analytical"

#: ``IfcStructuralAnalysisModel`` is a group, not a product: it has no uid of its own in the
#: model, so its GUID is derived from this role string under the project's namespace.
_ANALYTICAL_NS = "analytical"


@dataclass
class AnalyticalEntities:
    """What the loads emitter needs to hang an action on."""

    analysis_model: Any
    connections: dict[str, Any] = field(default_factory=dict)   # node id -> point connection
    members: dict[str, Any] = field(default_factory=dict)       # member id -> curve member


def emit_analytical(f: Any, project: Any, building: Any, model: AnalyticalModel,
                    project_uuid: UUID, element_entities: dict[str, Any],
                    profiles: ProfileCollector | None = None,
                    body_context: Any = None) -> AnalyticalEntities:
    """Write the analysis model, its connections and its curve members. Loads follow."""
    # ``id()`` is reused by the allocator, so an entry stranded by an emit that raised
    # would hand this file another file's profile sets (→ lowlevel._PENDING_CONTAINMENT).
    _STANDALONE_CACHE.pop(id(f), None)
    analysis = _analysis_model(f, project, building, model, project_uuid)
    entities = AnalyticalEntities(analysis_model=analysis)

    vertices: dict[str, Any] = {}
    for node in sorted(model.nodes, key=lambda n: n.id):
        entities.connections[node.id] = _point_connection(
            f, node, model, project_uuid, body_context, vertices)
    for member in sorted(model.members, key=lambda m: m.id):
        entities.members[member.id] = _curve_member(
            f, member, model, project_uuid, element_entities, profiles, body_context,
            entities.connections, vertices)

    grouped = [entities.connections[key] for key in sorted(entities.connections)]
    grouped += [entities.members[key] for key in sorted(entities.members)]
    ll.assign_to_group(f, analysis, grouped)
    return entities


def _analysis_model(f: Any, project: Any, building: Any, model: AnalyticalModel,
                    project_uuid: UUID) -> Any:
    analysis = ll.create_entity(f, "IfcStructuralAnalysisModel",
                                name="Type:Haus analytical model")
    analysis.GlobalId = derive_child_guid(project_uuid, _ANALYTICAL_NS, "model")
    analysis.PredefinedType = "LOADING_3D"
    if building is not None:
        # The group has to hang off the spatial tree or an importer walking the building
        # never reaches it — the same reason the distribution systems get one.
        ll.serves_building(f, analysis, building)
    if project is not None:
        # And declared in the project context: IFC4's way of saying a non-spatial group
        # belongs to this project (``IfcRelDeclares``), which is what makes it show up in
        # Bonsai's project browser rather than only through the building.
        f.create_entity("IfcRelDeclares", GlobalId=ll.new_guid(), RelatingContext=project,
                        RelatedDefinitions=[analysis])
    ll.ensure_pset(f, analysis, PSET_ANALYTICAL, {
        "scope": ";".join(model.scope),
        "assumptions": " | ".join(model.assumptions),
        "gaps": " | ".join(model.gaps),
    })
    return analysis


# --- connections ---------------------------------------------------------------------

#: ``IfcBoundaryNodeCondition`` reads TRUE as *restrained* and FALSE as *free*; a stiffness
#: measure would be a spring, which is not a claim this engine makes about a footing.
#: Translations are restrained under both fixities — a support that let the node move is
#: not a support. The rotations come from ``Support.restrained_rotations()``, not from the
#: fixity: a beam end pinned for bending on a wall still cannot ROLL about its own axis,
#: and a model that releases that roll too is a mechanism every solver refuses.
_DOF_NAMES = ("TranslationalStiffnessX", "TranslationalStiffnessY",
              "TranslationalStiffnessZ", "RotationalStiffnessX",
              "RotationalStiffnessY", "RotationalStiffnessZ")


def _boundary_condition(f: Any, name: str, dofs: tuple[bool, ...]) -> Any:
    condition = f.create_entity("IfcBoundaryNodeCondition", Name=name)
    for attribute, restrained in zip(_DOF_NAMES, dofs, strict=True):
        setattr(condition, attribute, f.create_entity("IfcBoolean", bool(restrained)))
    return condition


def _point_connection(f: Any, node: Node, model: AnalyticalModel, project_uuid: UUID,
                      body_context: Any, vertices: dict[str, Any]) -> Any:
    connection = ll.create_entity(f, "IfcStructuralPointConnection", name=node.id)
    connection.GlobalId = derive_child_guid(project_uuid, _ANALYTICAL_NS,
                                            f"node:{node.id}")
    point = f.createIfcCartesianPoint(tuple(float(v) for v in node.xyz))
    vertices[node.id] = f.create_entity("IfcVertexPoint", VertexGeometry=point)
    if body_context is not None:
        # Topology, not geometry: a node is a point in the analysis model's own frame, and
        # the IFC4 SAM convention is an IfcVertexPoint. SAP2000 ignores it and reads the
        # placement; Bonsai draws it.
        rep = f.create_entity("IfcTopologyRepresentation", ContextOfItems=body_context,
                              RepresentationIdentifier="Reference",
                              RepresentationType="Vertex",
                              Items=[vertices[node.id]])
        ll.assign_representation(f, connection, rep)
    else:
        ll.ensure_local_placement(f, connection)

    supports = model.supports_at(node.id)
    if supports:
        # One support per node; a second would be two claims about one base, and the graph
        # does not produce them. Taking the first in authored order keeps that visible.
        support = supports[0]
        rotations = support.restrained_rotations()
        connection.AppliedCondition = _boundary_condition(
            f, support.fixity.value, (True, True, True, *rotations))
        properties = {"fixity": support.fixity.value, "basis": support.basis,
                      "item_id": support.item_id or "", "element_tag": support.element_tag,
                      "restrained_rotations": ";".join(
                          axis for axis, held in zip("XYZ", rotations, strict=True) if held)
                      or "none"}
    else:
        # No condition at all — a free node. NOT six FALSEs, which would say "this engine
        # examined the node and released every degree of freedom".
        properties = {"fixity": "free (no support derived)", "basis": "",
                      "item_id": "", "element_tag": ""}
    properties["node"] = node.id
    ll.ensure_pset(f, connection, PSET_ANALYTICAL, properties)
    return connection


# --- curve members -------------------------------------------------------------------


def _curve_member(f: Any, member: Member, model: AnalyticalModel, project_uuid: UUID,
                  element_entities: dict[str, Any], profiles: ProfileCollector | None,
                  body_context: Any, connections: dict[str, Any],
                  vertices: dict[str, Any]) -> Any:
    releases = member.releases
    both_released = releases.i_moment and releases.j_moment
    entity = ll.create_entity(f, "IfcStructuralCurveMember", name=member.id)
    entity.GlobalId = derive_child_guid(project_uuid, member.physical_uid,
                                        f"analytical:{member.id}")
    entity.PredefinedType = "PIN_JOINED_MEMBER" if both_released else "RIGID_JOINED_MEMBER"
    _set_axis(f, entity, member)
    _representation(f, entity, member, model, body_context, vertices)
    _connect_ends(f, entity, member, connections, project_uuid)
    _assign_section(f, entity, member, element_entities, profiles)
    _assign_physical(f, entity, member, element_entities)
    ll.ensure_pset(f, entity, PSET_ANALYTICAL, {
        "member": member.id,
        "category": member.category,
        "item_ids": ";".join(member.item_ids),
        "youngs_modulus_pa": float(member.e_pa),
        "e_basis": member.e_basis,
        "releases": _release_text(member),
        "length_m": float(model.length_m(member)),
    })
    return entity


def _release_text(member: Member) -> str:
    ends = [name for name, released in (("i", member.releases.i_moment),
                                        ("j", member.releases.j_moment)) if released]
    return ("moment released at " + " and ".join(ends)) if ends else "rigidly joined"


def _set_axis(f: Any, entity: Any, member: Member) -> None:
    """``Axis`` is the member's local z — the reference for its section orientation.

    Global Z for a horizontal member (its section stands up), global X for a vertical one,
    because a column's local z cannot be parallel to its own axis.
    """
    import ifcopenshell.api.structural

    axis = (1.0, 0.0, 0.0) if member.is_vertical else (0.0, 0.0, 1.0)
    # The api's edit dereferences the existing Axis, which ``root.create_entity`` leaves
    # unset, so the attribute is seeded first and then edited through the api.
    entity.Axis = f.create_entity("IfcDirection", (0.0, 0.0, 1.0))
    ifcopenshell.api.structural.edit_structural_item_axis(f, structural_item=entity,
                                                          axis=axis)


def _representation(f: Any, entity: Any, member: Member, model: AnalyticalModel,
                    body_context: Any, vertices: dict[str, Any]) -> None:
    """An 'Axis'/'Curve3D' polyline AND the SAM's 'Reference'/'Edge' topology.

    SAP2000 and ETABS do not import ``IfcTopologyRepresentation``, so the centreline has to
    exist as real geometry or the member arrives without one. The edge is written too,
    because it is what the IFC4 structural analysis view defines and what Bonsai draws.
    """
    if body_context is None:
        ll.ensure_local_placement(f, entity)
        return
    a, b = model.node(member.n0), model.node(member.n1)
    polyline = f.createIfcPolyline([
        f.createIfcCartesianPoint(tuple(float(v) for v in a.xyz)),
        f.createIfcCartesianPoint(tuple(float(v) for v in b.xyz)),
    ])
    axis = f.createIfcShapeRepresentation(body_context, "Axis", "Curve3D", [polyline])
    representations = [axis]
    if member.n0 in vertices and member.n1 in vertices:
        edge = f.create_entity("IfcEdge", EdgeStart=vertices[member.n0],
                               EdgeEnd=vertices[member.n1])
        representations.append(f.create_entity(
            "IfcTopologyRepresentation", ContextOfItems=body_context,
            RepresentationIdentifier="Reference", RepresentationType="Edge", Items=[edge]))
    ll.assign_representations(f, entity, representations)


def _connect_ends(f: Any, entity: Any, member: Member, connections: dict[str, Any],
                  project_uuid: UUID) -> None:
    """One ``IfcRelConnectsStructuralMember`` per end; a release rides on the relationship.

    IFC4 puts ``AppliedCondition`` on the relationship precisely so a member end can be
    released against a connection that other members reach rigidly — the alternative,
    a second node at the same coordinates, would say the frame comes apart there.
    A condition is written only where the graph says released: writing six TRUEs on every
    rigid end would be a claim about ends nobody examined.
    """
    import ifcopenshell.api.structural

    for end, node_id, released in (("i", member.n0, member.releases.i_moment),
                                   ("j", member.n1, member.releases.j_moment)):
        connection = connections.get(node_id)
        if connection is None:
            continue
        rel = ifcopenshell.api.structural.add_structural_member_connection(
            f, relating_structural_member=entity, related_structural_connection=connection)
        rel.Name = f"{member.id}:{end}"
        if released:
            rel.AppliedCondition = _boundary_condition(
                f, f"{member.id} end {end}: moment released",
                (True, True, True, False, False, False))


def _assign_section(f: Any, entity: Any, member: Member,
                    element_entities: dict[str, Any],
                    profiles: ProfileCollector | None) -> None:
    host = element_entities.get(member.physical_ifc_tag or member.tag)
    if profiles is not None and host is not None:
        profiles.add_companion(host, entity)
        return
    _standalone_profile_set(f, entity, member)


#: One profile set per (section, material, E) in a standalone write — the same reason
#: ``ProfileCollector`` shares them: a set per member is entities for no information.
_STANDALONE_CACHE: dict[int, dict[tuple, Any]] = {}


def _standalone_profile_set(f: Any, entity: Any, member: Member) -> None:
    section = member.section
    key = (section.shape, round(section.width_m, 9), round(section.depth_m, 9),
           member.material, round(member.e_pa, 3))
    cache = _STANDALONE_CACHE.setdefault(id(f), {})
    profile_set = cache.get(key)
    if profile_set is None:
        name = _section_name(member)
        if section.shape == "round":
            shape = f.create_entity("IfcCircleProfileDef", ProfileType="AREA",
                                    ProfileName=name, Radius=float(section.width_m) / 2.0)
        else:
            shape = f.create_entity("IfcRectangleProfileDef", ProfileType="AREA",
                                    ProfileName=name, XDim=float(section.width_m),
                                    YDim=float(section.depth_m))
        material = f.create_entity("IfcMaterial", Name=member.material)
        if member.e_pa:
            prop = f.create_entity(
                "IfcPropertySingleValue", Name="YoungModulus",
                NominalValue=f.create_entity("IfcModulusOfElasticityMeasure",
                                             float(member.e_pa)))
            f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical",
                            Properties=[prop], Material=material)
        material_profile = f.create_entity("IfcMaterialProfile", Name=name,
                                           Material=material, Profile=shape)
        profile_set = f.create_entity("IfcMaterialProfileSet", Name=name,
                                      MaterialProfiles=[material_profile])
        cache[key] = profile_set
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=ll.new_guid(),
                    RelatedObjects=[entity], RelatingMaterial=profile_set)


def attach_orphan_sections(f: Any, model: AnalyticalModel,
                           entities: AnalyticalEntities) -> int:
    """Give a section to every curve member the profile pass left without one.

    A companion only inherits a profile set where its physical element got one, and an
    element already carrying a layer set (a finish assembly) or an unparseable size gets
    none. The analytical member still has to state its section — an analysis model with a
    member of no section is not loadable — so it falls back to the graph's own
    ``CrossSection``. Run AFTER ``attach_profiles``; returns how many fell back.
    """
    import ifcopenshell.util.element as ue

    written = 0
    for member in sorted(model.members, key=lambda m: m.id):
        entity = entities.members.get(member.id)
        if entity is None or ue.get_material(entity) is not None:
            continue
        _standalone_profile_set(f, entity, member)
        written += 1
    return written


_M_TO_IN = 1.0 / 0.0254


def _section_name(member: Member) -> str:
    """The section in the inches a US reviewer reads, from the graph's own metres."""
    section = member.section
    if section.shape == "round":
        return f'{section.width_m * _M_TO_IN:g}" round'
    return f"{section.width_m * _M_TO_IN:g}x{section.depth_m * _M_TO_IN:g}"


def _assign_physical(f: Any, entity: Any, member: Member,
                     element_entities: dict[str, Any]) -> None:
    """``IfcRelAssignsToProduct`` back to the physical element, where there is one.

    SAP2000 and ETABS do not import it. Bonsai does, and so does a reviewer selecting a
    member in one model and asking where it is in the other — which is the whole point of
    shipping both views in one file. Absent silently when the tag has no entity: a member
    scoped in for its load path may draw nothing (an Equipment placeable, a deferred roof).
    """
    import ifcopenshell.api.structural

    host = element_entities.get(member.physical_ifc_tag or member.tag)
    if host is None:
        return
    ifcopenshell.api.structural.assign_product(f, relating_product=entity,
                                               related_object=host)


# --- standalone -----------------------------------------------------------------------


def write_standalone(model: AnalyticalModel, path: Path, project_uuid: UUID,
                     project_name: str = "Type:Haus analysis",
                     building_name: str = "Building") -> Path:
    """Write JUST the analysis view to ``path`` — no physical model, no geometry.

    What ``haus analysis`` hands a PE who wants the frame and nothing else, and what the
    fixture test writes. The physical export is unaffected: ``emit_ifc(analytical=...)``
    is the path that puts both views in one file.
    """
    from typehaus.emit.ifc.analytical_loads import emit_analytical_loads
    from typehaus.emit.ifc.lowlevel_guids import (
        pin_header_timestamp,
        pin_project_guid,
        pin_relation_member_order,
        pin_relationship_guids,
        pin_spatial_guids,
        pin_unit_order,
    )

    f = ll.new_file(IFC_APP_NAME)
    project = ll.create_entity(f, "IfcProject", name=project_name)
    ll.assign_project_units(f)
    assign_structural_units(f)
    body = ll.add_context(f)
    site = ll.create_entity(f, "IfcSite", name="Site")
    building = ll.create_entity(f, "IfcBuilding", name=building_name)
    ll.aggregate(f, project, [site])
    ll.aggregate(f, site, [building])

    entities = emit_analytical(f, project, building, model, project_uuid, {},
                               profiles=None, body_context=body)
    emit_analytical_loads(f, model, entities, project_uuid)
    ll.flush_containers(f)
    _STANDALONE_CACHE.pop(id(f), None)

    pin_project_guid(project, project_uuid)
    pin_spatial_guids(f, project_uuid)
    pin_relation_member_order(f)
    pin_relationship_guids(f, project_uuid)
    pin_unit_order(f)
    pin_header_timestamp(f)
    f.write(str(path))
    return path
