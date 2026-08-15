"""IFC emission for the built fabric: walls, openings, spaces and the things placed in them.

Split out of :mod:`typehaus.emit.ifc.emitter`, which had grown to four disciplines in one
1500-line file (→ AGENTS.md §1.1). What lands here is what an architect draws: the wall
carrying an ``IfcMaterialLayerSetUsage`` over a shared ``IfcWallType``, the
``IfcOpeningElement`` that voids it and the door or window filling it, the ``IfcSpace`` each
room becomes, and the furniture, fixtures and appliances standing inside them.

The seam is where it is because the wall type key, the layer reference offset and an
opening's station strip are one another's only callers — all three answer the same question
(what the wall's real footprint is at a station) and nothing outside this file asks it.
Framing members are the deliberate exception: a stud is structure, so ``_emit_framed_member``
lives in :mod:`typehaus.emit.ifc.structural` and is imported back for the wall's framed LOD.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from shapely.geometry import Polygon
from shapely.ops import unary_union

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.emit.ifc.structural import _emit_framed_member
from typehaus.model.enums import DoorOperation
from typehaus.model.ids import derive_child_guid, derive_guid
from typehaus.resolve.geometry import rect_between
from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.resolve.room_floor import room_floor_elevation
from typehaus.resolve.topology import _added_thicknesses


def _wall_type_key(wall: ResolvedWall) -> tuple:
    """What makes two walls the same IfcWallType: assembly AND resolved layer stack.

    Keying representatives by assembly alone was right until ``Room.wall_lining`` overrides
    became real: an accent-lined wall shares its assembly with its neighbours but not their
    layer set, and one representative would file both under one (wrong) IfcMaterialLayerSet.
    """
    return (wall.assembly, tuple((ly.name, ly.material_ref, round(ly.thickness_m, 6))
                                 for ly in wall.depth_layers()))


def _assembly_default_signature(model: ResolvedModel, assembly_tag: str) -> tuple | None:
    """The layer signature a wall of this assembly resolves to with NO lining override."""
    assembly = model.plan.library.resolve_assembly(assembly_tag)
    if assembly is None:
        return None
    stack = list(assembly.default_lining) + list(assembly.layers)
    return tuple((layer.name, layer.material_ref, round(layer.thickness.meters, 6))
                 for (layer, _added, cavity) in _added_thicknesses(stack) if not cavity)


def _emit_wall_types(f: Any, model: ResolvedModel,
                     project_uuid: Any) -> dict[tuple, tuple[Any, Any]]:
    result: dict[tuple, tuple[Any, Any]] = {}
    representatives: dict[tuple, ResolvedWall] = {}
    for wall in sorted(model.walls, key=lambda item: item.uid):
        representatives[_wall_type_key(wall)] = wall
    grouped: dict[str, list] = {}
    for key in representatives:
        grouped.setdefault(key[0], []).append(key)
    for assembly_tag in sorted(grouped):
        # The unoverridden stack keeps the bare assembly name (and so its GlobalId — a
        # pre-override export round-trips unchanged); lining variants suffix ``~lining<n>``.
        default_signature = _assembly_default_signature(model, assembly_tag)
        keys = sorted(grouped[assembly_tag],
                      key=lambda key: (key[1] != default_signature, key[1]))
        for index, key in enumerate(keys):
            name = assembly_tag if index == 0 and key[1] == default_signature \
                else f"{assembly_tag}~lining{index}"
            representative = representatives[key]
            wall_type = ll.create_entity(f, "IfcWallType", name=name)
            wall_type.GlobalId = derive_child_guid(project_uuid, "wall-types", name)
            layer_set = ll.assign_material_layer_set(
                f, wall_type,
                [{"name": layer.name, "material_ref": layer.material_ref,
                  "thickness_m": layer.thickness_m, "category": layer.function}
                 for layer in representative.depth_layers()],
                name=name,
            )
            result[key] = (wall_type, layer_set)
    return result


def _emit_wall(f: Any, body: Any, rw: ResolvedWall, storeys: dict[str, Any],
               project_uuid: Any, lod: str,
               wall_types: dict[tuple, tuple[Any, Any]]) -> Any:
    guid = derive_guid(project_uuid, rw.uid)
    ifc_class = "IfcWall"
    wall = ll.create_entity(f, ifc_class, name=rw.tag)
    wall.GlobalId = guid
    body_representation = ll.add_prisms_from_profiles(
        f, body,
        [layer.polygon for layer in rw.depth_layers() if len(layer.polygon) >= 3],
        rw.z1_m - rw.z0_m, rw.z0_m,
    )
    axis_representation = ll.add_axis_representation(f, body, rw.axis)
    ll.assign_representations(f, wall, [axis_representation, body_representation])
    ll.ensure_pset(f, wall, PSET_SOURCE, {
        "uid": rw.uid, "tag": rw.tag, "assembly": rw.assembly,
        "plan_content_hash": _content_hash(rw),
    })
    ll.ensure_pset(f, wall, "Pset_WallCommon", {
        "IsExternal": not rw.tag.startswith("INT"),
    })
    wall_type, layer_set = wall_types[_wall_type_key(rw)]
    ll.assign_type(f, wall, wall_type)
    _assign_wall_material(f, wall, rw, layer_set)
    if rw.is_foundation:
        ll.ensure_pset(f, wall, "Pset_HF_FoundationWall", {"IsFoundation": True})
    ll.assign_container(f, wall, storeys[rw.storey])

    if lod == "framed" and rw.members:
        members = []
        for m in sorted(rw.members, key=lambda x: x.child_key):
            member = _emit_framed_member(f, body, rw.tag, rw.uid, m, project_uuid)
            members.append(member)
        ll.aggregate(f, wall, members)
    return wall


def _assign_wall_material(f: Any, wall: Any, rw: ResolvedWall,
                          type_layer_set: Any) -> None:
    """IfcMaterialLayerSet from the depth-bearing layers + a pset per cavity fill.

    Cavity insulation is deliberately not a layer: IFC layer thicknesses must sum to the
    wall depth, and a batt between studs shares that depth with the framing. It rides along
    as ``TypeHaus_CavityFill`` so the information survives the round trip without lying
    about geometry.
    """
    depth_layers = rw.depth_layers()
    if not depth_layers:
        return
    ll.assign_material_layer_usage(
        f, wall, type_layer_set, _layer_reference_offset(rw)
    )
    for ly in rw.layers:
        if not ly.is_cavity:
            continue
        ll.ensure_pset(f, wall, "TypeHaus_CavityFill", {
            "HostLayer": ly.cavity_host or "",
            "Material": ly.material_ref,
            "Thickness": ly.thickness_m,
        })


def _layer_reference_offset(rw: ResolvedWall) -> float:
    if not rw.depth_layers():
        return 0.0
    (x0, y0), (x1, y1) = rw.axis
    wall_length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 or 1.0
    normal = (-(y1 - y0) / wall_length, (x1 - x0) / wall_length)
    return min(
        (point[0] - x0) * normal[0] + (point[1] - y0) * normal[1]
        for layer in rw.depth_layers()
        for point in layer.polygon
    )


def _content_hash(rw: ResolvedWall) -> str:
    geometry = tuple(
        (layer.name, layer.thickness_m, tuple(layer.polygon))
        for layer in rw.layers
    )
    h = hashlib.sha256(
        repr((rw.uid, rw.assembly, rw.axis, rw.z0_m, rw.z1_m, geometry)).encode()
    )
    return h.hexdigest()[:12]


def _opening_segment(rw: ResolvedWall, opening: Any) -> tuple[tuple[float, float],
                                                              tuple[float, float], float]:
    """The opening's plan sub-segment along the host axis + the wall thickness (meters)."""
    (sx, sy), (ex, ey) = rw.axis
    length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5 or 1.0
    ux, uy = (ex - sx) / length, (ey - sy) / length
    c0 = opening.center_along_m - opening.width_m / 2
    c1 = opening.center_along_m + opening.width_m / 2
    thickness = rw.thickness_m or 0.15
    return (sx + ux * c0, sy + uy * c0), (sx + ux * c1, sy + uy * c1), thickness


def _opening_profile(rw: ResolvedWall, opening: Any) -> list[tuple[float, float]]:
    """Intersect the real host footprint with the opening's jamb station strip."""
    (sx, sy), (ex, ey) = rw.axis
    wall_length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5 or 1.0
    direction = ((ex - sx) / wall_length, (ey - sy) / wall_length)
    normal = (-direction[1], direction[0])
    start = opening.center_along_m - opening.width_m / 2
    end = opening.center_along_m + opening.width_m / 2
    transverse_extent = max(rw.thickness_m * 4.0, 1.0)

    def point(along: float, across: float) -> tuple[float, float]:
        return (
            sx + direction[0] * along + normal[0] * across,
            sy + direction[1] * along + normal[1] * across,
        )

    station_strip = Polygon([
        point(start, -transverse_extent), point(end, -transverse_extent),
        point(end, transverse_extent), point(start, transverse_extent),
    ])
    host_footprint = unary_union([
        Polygon(layer.polygon) for layer in rw.depth_layers()
        if len(layer.polygon) >= 3
    ])
    clipped = host_footprint.intersection(station_strip)
    polygons = [clipped] if isinstance(clipped, Polygon) else [
        item for item in getattr(clipped, "geoms", ()) if isinstance(item, Polygon)
    ]
    if polygons:
        polygon = max(polygons, key=lambda item: item.area)
        return [(float(x), float(y)) for x, y in list(polygon.exterior.coords)[:-1]]
    a, b, thickness = _opening_segment(rw, opening)
    return rect_between(a, b, -thickness / 2, thickness / 2)


# DoorOperation → IfcDoorTypeOperationEnum (IFC4). Handing is authored per *instance*
# (``flip_hinge``), not per product type, so the handed members all take the LEFT variant —
# a type-level guess at RIGHT would be no more accurate and would churn the round-trip.
# Two of our operations have no exact IFC4 term: a pocket door is exported as sliding
# (IFC4 draws no pocket distinction), and a sectional overhead door as ROLLINGUP, which is
# the schema's only overhead-track category — there is no OVERHEAD_DOOR in IFC4.
_IFC_DOOR_OPERATION = {
    DoorOperation.SWING: "SINGLE_SWING_LEFT",
    DoorOperation.DOUBLE_SWING: "DOUBLE_DOOR_SINGLE_SWING",
    DoorOperation.SLIDE: "SLIDING_TO_LEFT",
    DoorOperation.POCKET: "SLIDING_TO_LEFT",
    DoorOperation.BIFOLD: "FOLDING_TO_LEFT",
    DoorOperation.OVERHEAD: "ROLLINGUP",
}


def _emit_opening_types(f: Any, model: ResolvedModel, project_uuid: Any) -> dict[str, Any]:
    """Create one stable IFC type per authored door/window product type."""
    result: dict[str, Any] = {}
    for kind, items in (("door", model.plan.library.door_types),
                        ("window", model.plan.library.window_types)):
        for item in items:
            entity = ll.create_entity(f, "IfcDoorType" if kind == "door" else "IfcWindowType", name=item.tag)
            entity.GlobalId = derive_child_guid(project_uuid, f"{kind}-types", item.tag)
            if kind == "door":
                # Without these the authored operation is lost on export and every door
                # reads as a plain swing in the receiving application.
                entity.PredefinedType = "DOOR"
                entity.OperationType = _IFC_DOOR_OPERATION[item.operation]
            ll.ensure_pset(f, entity, "TypeHaus_Identity", {"tag": item.tag, "source_type": item.tag})
            result[item.tag] = entity
    return result


def _emit_opening(f: Any, body: Any, opening: Any, model: ResolvedModel,
                  wall_entities: dict[str, Any], storeys: dict[str, Any],
                  project_uuid: Any, opening_types: dict[str, Any]) -> None:
    """One IfcOpeningElement voiding the host wall, with an optional product filling.

    Void GUID = derive_child_guid(uuid, opening.uid, "void"); the filling GUID =
    derive_guid(uuid, opening.uid) so it matches the diff adapter's prediction (round-trip
    closes). Headers stay generated-ephemeral (Revit parity)."""
    rw = model.wall(opening.host_wall)
    wall = wall_entities.get(opening.host_wall)
    if rw is None or wall is None:
        return
    z0 = rw.z0_m + opening.sill_m
    # Void: an arched profile is swept through the wall; ordinary openings retain the
    # footprint prism used by the established rectangular IFC representation.
    void = ll.create_entity(f, "IfcOpeningElement", name=f"{opening.tag}/void")
    void.GlobalId = derive_child_guid(project_uuid, opening.uid, "void")
    if opening.arch_rise_m > 1e-6:
        (sx, sy), (ex, ey) = rw.axis
        wall_length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5 or 1.0
        direction = ((ex - sx) / wall_length, (ey - sy) / wall_length)
        center = (sx + direction[0] * opening.center_along_m,
                  sy + direction[1] * opening.center_along_m)
        representation = ll.add_arched_opening_prism(
            f, body, center_m=center, wall_direction=direction,
            wall_thickness_m=rw.thickness_m or 0.15, width_m=opening.width_m,
            height_m=opening.height_m, arch_rise_m=opening.arch_rise_m, z0_m=z0,
        )
    else:
        representation = ll.add_prism_from_profile(
            f, body, _opening_profile(rw, opening), opening.height_m, z0,
        )
    ll.assign_representation(f, void, representation)
    ll.ensure_pset(f, void, PSET_SOURCE, {
        "uid": opening.uid, "tag": opening.tag, "type": opening.type_ref or "",
        "host_wall": opening.host_wall,
    })
    ll.add_opening(f, wall, void)

    # A RoughOpening is intentionally only a void. Emitting it as IfcWindow would destroy
    # the distinction required by round-trip authoring applications.
    if opening.kind == "rough_opening":
        return

    # Filling: a thin frame prism (a Revit-style panel), tagged for the round-trip.
    ifc_class = "IfcDoor" if opening.is_door else "IfcWindow"
    a, b, _thickness = _opening_segment(rw, opening)
    frame_profile = rect_between(a, b, -0.025, 0.025)
    filling = ll.create_entity(f, ifc_class, name=opening.tag)
    filling.GlobalId = derive_guid(project_uuid, opening.uid)
    filling.OverallWidth = opening.width_m
    filling.OverallHeight = opening.height_m
    ll.assign_representation(f, filling, ll.add_prism_from_profile(
        f, body, frame_profile, opening.height_m, z0))
    is_external = not rw.tag.startswith("INT")
    ll.ensure_pset(f, filling, PSET_SOURCE, {
        "uid": opening.uid, "tag": opening.tag, "type": opening.type_ref or "",
        "host_wall": opening.host_wall,
    })
    ll.ensure_pset(f, filling, "Pset_DoorCommon" if opening.is_door else "Pset_WindowCommon",
                   {"IsExternal": is_external})
    ll.assign_container(f, filling, storeys[rw.storey])
    if opening.type_ref in opening_types:
        ll.assign_type(f, filling, opening_types[opening.type_ref])
    ll.add_filling(f, void, filling)


def _emit_space(f: Any, body: Any, room: Any, storeys: dict[str, Any],
                project_uuid: Any, model: ResolvedModel) -> None:
    space = ll.create_entity(f, "IfcSpace", name=room.tag)
    space.GlobalId = derive_guid(project_uuid, room.uid)
    if room.clear_face:
        # Geometry is authored in the world frame (see ``ensure_local_placement``), so the
        # space's floor has to be given its real elevation here — it is not automatically
        # inherited from the containing IfcBuildingStorey's placement. Matches the glTF
        # viewer's floor mesh (``emit/gltf/emitter.py``): both read ``room_floor_elevation``
        # so a room whose slab is filed on a different storey than the room (the garage)
        # doesn't disagree between the two exports.
        rep = ll.add_prism_from_profile(f, body, room.clear_face, 2.7,
                                        room_floor_elevation(model, room))
        ll.assign_representation(f, space, rep)
    ll.ensure_pset(f, space, PSET_SOURCE, {"uid": room.uid, "tag": room.tag})
    ll.ensure_pset(f, space, "Pset_SpaceCommon", {
        "IsExternal": False, "PubliclyAccessible": False,
    })
    # IfcSpace is itself a spatial structure, so it belongs in the storey aggregation
    # rather than an IfcRelContainedInSpatialStructure product relationship.
    ll.aggregate(f, storeys[room.storey], [space])


def _emit_furniture(f: Any, body: Any, model: ResolvedModel, storeys: dict[str, Any],
                    project_uuid: Any) -> None:
    """Core-LOD furnishing elements use declared footprint and height, not mesh triangles."""
    types = {item.tag: item for item in model.plan.library.furniture_types}
    ifc_types: dict[str, Any] = {}
    for tag, furniture_type in types.items():
        type_object = ll.create_entity(f, "IfcFurnitureType", name=furniture_type.name)
        type_object.GlobalId = derive_child_guid(project_uuid, "furniture-types", tag)
        ll.ensure_pset(f, type_object, "TypeHaus_Identity", _type_identity(furniture_type))
        ifc_types[tag] = type_object
    resolved_furniture = {item.uid: item for item in model.canvas_objects if item.domain == "furniture"}
    for storey in model.plan.storeys:
        for furniture in model.plan.storey_elements(storey.tag):
            if furniture.element_kind != "Furniture" or furniture.type_ref not in types:
                continue
            furniture_type = types[furniture.type_ref]
            resolved = resolved_furniture.get(furniture.uid)
            if resolved is None:
                continue
            element = ll.create_entity(f, "IfcFurniture", name=furniture.tag)
            element.GlobalId = derive_guid(project_uuid, furniture.uid)
            ll.assign_representation(f, element, ll.add_prism_from_profile(
                f, body, resolved.footprint, furniture_type.height.meters, resolved.z_m
            ))
            ll.ensure_pset(f, element, PSET_SOURCE, {
                "uid": furniture.uid, "tag": furniture.tag, "type": furniture.type_ref,
                "mesh": furniture_type.mesh.path if furniture_type.mesh is not None else "",
                "rotation_degrees": f"{resolved.rotation_degrees:.6f}",
            })
            ll.ensure_pset(f, element, "TypeHaus_Identity", {
                "uid": furniture.uid, "tag": furniture.tag, "source_type": furniture.type_ref,
            })
            _emit_service_ports(f, element, furniture_type.ports, project_uuid, furniture.uid)
            ll.assign_type(f, element, ifc_types[furniture.type_ref])
            ll.assign_container(f, element, storeys[storey.tag])


def _emit_service_ports(f: Any, occurrence: Any, ports: tuple[Any, ...], project_uuid: Any,
                        occurrence_uid: str) -> None:
    """Attach stable IFC endpoint identities without prematurely inventing routing."""
    if not ports:
        return
    entities = []
    for port in ports:
        entity = ll.create_entity(f, "IfcDistributionPort", name=port.tag)
        entity.GlobalId = derive_child_guid(project_uuid, occurrence_uid, f"port/{port.tag}")
        ll.ensure_pset(f, entity, "TypeHaus_Port", {
            "tag": port.tag, "service": port.service.value,
            "x_m": port.position[0].meters, "y_m": port.position[1].meters,
            "z_m": port.position[2].meters, "notes": port.notes or "",
        })
        entities.append(entity)
    relation = f.create_entity("IfcRelNests", GlobalId=derive_child_guid(
        project_uuid, occurrence_uid, "ports"), RelatingObject=occurrence, RelatedObjects=entities)
    relation.Name = "Service ports"


def _type_identity(product_type: Any) -> dict[str, str]:
    """Keep import provenance on the semantic IFC type without inventing IFC properties.

    Import records are intentionally flat JSON.  A compact deterministic JSON value keeps
    arbitrary source facts (including future IFC GUIDs) available to BIM tools while the
    standard class and type relationship remain the primary interchange contract.
    """
    result = {"tag": product_type.tag, "source_type": product_type.tag}
    if product_type.import_provenance:
        result["import_provenance"] = json.dumps(product_type.import_provenance, sort_keys=True)
    return result


def _emit_resolved_placeables(f: Any, body: Any, model: ResolvedModel, storeys: dict[str, Any],
                              project_uuid: Any) -> None:
    """Export resolved plumbing fixtures and appliances with semantic, stable identities."""
    fixture_types = {item.tag: item for item in model.plan.library.fixture_types}
    appliance_types = {item.tag: item for item in model.plan.library.appliance_types}
    type_cache: dict[tuple[str, str], Any] = {}
    for item in model.canvas_objects:
        if item.domain not in {"plumbing", "appliance"}:
            continue
        product_type = (fixture_types if item.domain == "plumbing" else appliance_types).get(item.type_ref)
        if product_type is None:
            continue
        ifc_class = "IfcSanitaryTerminal" if item.domain == "plumbing" else "IfcBuildingElementProxy"
        type_class = "IfcSanitaryTerminalType" if item.domain == "plumbing" else "IfcBuildingElementProxyType"
        type_key = (ifc_class, product_type.tag)
        type_object = type_cache.get(type_key)
        if type_object is None:
            type_object = ll.create_entity(f, type_class, name=product_type.name)
            type_object.GlobalId = derive_child_guid(project_uuid, f"{item.domain}-types", product_type.tag)
            ll.ensure_pset(f, type_object, "TypeHaus_Identity", _type_identity(product_type))
            type_cache[type_key] = type_object
        element = ll.create_entity(f, ifc_class, name=item.tag)
        element.GlobalId = derive_guid(project_uuid, item.uid)
        ll.assign_representation(f, element, ll.add_prism_from_profile(
            f, body, item.footprint, product_type.height.meters, item.z_m,
        ))
        ll.ensure_pset(f, element, PSET_SOURCE, {"uid": item.uid, "tag": item.tag,
                                                   "type": product_type.tag,
                                                   "rotation_degrees": f"{item.rotation_degrees:.6f}"})
        ll.ensure_pset(f, element, "TypeHaus_Identity", {"uid": item.uid, "tag": item.tag,
                                                            "source_type": product_type.tag})
        _emit_service_ports(f, element, product_type.ports, project_uuid, item.uid)
        ll.assign_type(f, element, type_object)
        ll.assign_container(f, element, storeys[item.storey])
