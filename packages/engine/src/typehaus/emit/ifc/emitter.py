"""IFC4 emitter over the ResolvedModel (WP1.7, → 12 §IFC emission).

Core LOD = one IfcWall per wall with IfcMaterialLayerSetUsage + shared IfcWallType;
framed LOD additionally aggregates generated members. Parent GUIDs are identical across
LODs (diff stability). GUIDs are derived from (project_uuid, uid) so moved/renamed
elements keep their GlobalId. Determinism: sorted iteration + pinned OwnerHistory.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from shapely.geometry import Polygon
from shapely.ops import unary_union

from typehaus._meta import IFC_APP_NAME, PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.model.ids import derive_child_guid, derive_guid
from typehaus.resolve.geometry import polygon_area, rect_between
from typehaus.resolve.model import ResolvedModel, ResolvedWall


def emit_ifc(model: ResolvedModel, out_path: Path, lod: str = "framed") -> Path:
    """Emit the resolved model to an IFC4 file at ``out_path``. Returns the path."""
    f = ll.new_file(IFC_APP_NAME)
    project_uuid = model.plan.project.project_uuid
    ifc_project = ll.create_entity(f, "IfcProject", name=model.plan.project.name)
    # IfcOpenShell attaches representation contexts to IfcProject; creating this first is
    # required by current 0.8.x APIs and keeps the output portable to Blender/Bonsai.
    body = ll.add_context(f)
    _georef(f, ifc_project, model, body.ParentContext)
    site = ll.create_entity(f, "IfcSite", name="Site")
    building = ll.create_entity(f, "IfcBuilding", name=model.plan.project.building.name)
    _relate(f, ifc_project, [site])
    _relate(f, site, [building])
    _emit_site_representation(f, body, site, model)

    storeys: dict[str, Any] = {}
    for storey in sorted(model.plan.storeys, key=lambda s: s.elevation.meters):
        ifc_storey = ll.create_entity(f, "IfcBuildingStorey", name=storey.tag)
        ll.ensure_pset(f, ifc_storey, PSET_SOURCE,
                       {"uid": storey.uid, "tag": storey.tag})
        storeys[storey.tag] = ifc_storey
    _relate(f, building, list(storeys.values()))

    wall_types = _emit_wall_types(f, model, project_uuid)
    wall_entities: dict[str, Any] = {}
    for rw in sorted(model.walls, key=lambda w: w.uid):
        wall_entities[rw.tag] = _emit_wall(
            f, body, rw, storeys, project_uuid, lod, wall_types
        )

    opening_types = _emit_opening_types(f, model, project_uuid)

    for opening in sorted(model.openings, key=lambda o: o.uid):
        _emit_opening(f, body, opening, model, wall_entities, storeys, project_uuid, opening_types)

    for solid in sorted(model.solids, key=lambda item: item.uid):
        _emit_solid(f, body, solid, storeys, project_uuid, model)

    for roof in sorted(model.roofs, key=lambda item: item.uid):
        _emit_roof(f, body, roof, storeys, project_uuid, lod)

    for stair in sorted(model.stairs, key=lambda item: item.uid):
        _emit_stair(f, stair, storeys, project_uuid, lod)

    for room in sorted(model.rooms, key=lambda r: r.uid):
        _emit_space(f, body, room, storeys, project_uuid)

    _emit_furniture(f, body, model, storeys, project_uuid)
    _emit_resolved_placeables(f, body, model, storeys, project_uuid)

    for run in sorted(model.pipe_runs, key=lambda item: item.uid):
        _emit_pipe_run(f, body, run, storeys, project_uuid)

    for sleeve in sorted(model.sleeves, key=lambda item: item.uid):
        _emit_sleeve(f, body, sleeve, storeys, project_uuid)

    for duct in sorted(model.ducts, key=lambda item: item.uid):
        _emit_duct_run(f, body, model, duct, storeys, project_uuid)

    _emit_registers_equipment_devices(f, body, model, storeys, project_uuid)
    _emit_utilities(f, body, model, project_uuid)

    for bedding in sorted(model.footing_beddings, key=lambda item: item.uid):
        _emit_footing_bedding(f, body, bedding, storeys, project_uuid)

    f.write(str(out_path))
    return out_path


def _emit_site_representation(f: Any, body: Any, ifc_site: Any, model: ResolvedModel) -> None:
    """A 5cm pad prism of the parcel ring at grade — imports as a lot slab (Phase 4)."""
    site = model.plan.project.site
    parcel = [p.xy_m for p in site.parcel]
    if len(parcel) < 3:
        return
    grade_z = site.grade.meters if site.grade is not None else 0.0
    _assign_representation(f, ifc_site, ll.add_prism_from_profile(f, body, parcel, 0.05, grade_z))
    props = {"parcel_area_m2": abs(polygon_area(parcel))}
    for spec in site.setbacks:
        key = f"setback_edge{spec.edge}_{spec.label or 'UNLABELED'}_ft"
        props[key] = spec.distance.inches / 12.0
    ll.ensure_pset(f, ifc_site, "TypeHaus_Site", props)


def _emit_utilities(f: Any, body: Any, model: ResolvedModel, project_uuid: Any) -> None:
    site = model.plan.project.site
    grade_z = site.grade.meters if site.grade is not None else 0.0
    for line in site.utilities:
        path = [p.xy_m for p in line.path]
        if len(path) < 2:
            continue
        depth_m = line.depth.meters if line.depth is not None else 1.0
        z0 = grade_z - depth_m
        for index in range(len(path) - 1):
            profile = rect_between(path[index], path[index + 1], -0.05, 0.05)
            child_key = f"seg-{index:02d}"
            uid = f"{line.kind.value}/{line.entry.xy_m}/{child_key}"
            element = ll.create_entity(f, "IfcBuildingElementProxy",
                                       name=f"UTIL-{line.kind.value}/{child_key}")
            element.GlobalId = derive_child_guid(project_uuid, "site-utilities", uid)
            _assign_representation(f, element, ll.add_prism_from_profile(f, body, profile, 0.1, z0))
            ll.ensure_pset(f, element, "TypeHaus_Utility", {
                "kind": line.kind.value, "entry_x_m": line.entry.xy_m[0],
                "entry_y_m": line.entry.xy_m[1],
            })


def _emit_wall_types(f: Any, model: ResolvedModel,
                     project_uuid: Any) -> dict[str, tuple[Any, Any]]:
    result: dict[str, tuple[Any, Any]] = {}
    representatives = {
        wall.assembly: wall for wall in sorted(model.walls, key=lambda item: item.uid)
    }
    for assembly_tag, representative in sorted(representatives.items()):
        wall_type = ll.create_entity(f, "IfcWallType", name=assembly_tag)
        wall_type.GlobalId = derive_child_guid(project_uuid, "wall-types", assembly_tag)
        layer_set = ll.assign_material_layer_set(
            f, wall_type,
            [{"name": layer.name, "material_ref": layer.material_ref,
              "thickness_m": layer.thickness_m, "category": layer.function}
             for layer in representative.depth_layers()],
            name=assembly_tag,
        )
        result[assembly_tag] = (wall_type, layer_set)
    return result


def _emit_wall(f: Any, body: Any, rw: ResolvedWall, storeys: dict[str, Any],
               project_uuid: Any, lod: str,
               wall_types: dict[str, tuple[Any, Any]]) -> Any:
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
    _assign_representations(f, wall, [axis_representation, body_representation])
    ll.ensure_pset(f, wall, PSET_SOURCE, {
        "uid": rw.uid, "tag": rw.tag, "assembly": rw.assembly,
        "plan_content_hash": _content_hash(rw),
    })
    ll.ensure_pset(f, wall, "Pset_WallCommon", {
        "IsExternal": not rw.tag.startswith("INT"),
    })
    wall_type, layer_set = wall_types[rw.assembly]
    ll.assign_type(f, wall, wall_type)
    _assign_wall_material(f, wall, rw, layer_set)
    if rw.is_foundation:
        ll.ensure_pset(f, wall, "Pset_HF_FoundationWall", {"IsFoundation": True})
    ll.assign_container(f, wall, storeys[rw.storey])

    if lod == "framed" and rw.members:
        members = []
        for m in sorted(rw.members, key=lambda x: x.child_key):
            member = ll.create_entity(f, "IfcMember", name=f"{rw.tag}/{m.child_key}")
            member.GlobalId = derive_child_guid(project_uuid, rw.uid, m.child_key)
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


def _emit_opening_types(f: Any, model: ResolvedModel, project_uuid: Any) -> dict[str, Any]:
    """Create one stable IFC type per authored door/window product type."""
    result: dict[str, Any] = {}
    for kind, items in (("door", model.plan.library.door_types),
                        ("window", model.plan.library.window_types)):
        for item in items:
            entity = ll.create_entity(f, "IfcDoorType" if kind == "door" else "IfcWindowType", name=item.tag)
            entity.GlobalId = derive_child_guid(project_uuid, f"{kind}-types", item.tag)
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
    opening_profile = _opening_profile(rw, opening)
    z0 = rw.z0_m + opening.sill_m
    # Void: full wall thickness prism from sill to head.
    void = ll.create_entity(f, "IfcOpeningElement", name=f"{opening.tag}/void")
    void.GlobalId = derive_child_guid(project_uuid, opening.uid, "void")
    _assign_representation(f, void, ll.add_prism_from_profile(
        f, body, opening_profile, opening.height_m, z0))
    ll.ensure_pset(f, void, PSET_SOURCE, {
        "uid": opening.uid, "tag": opening.tag, "type": opening.type_ref or "",
        "host_wall": opening.host_wall,
    })
    ll.add_opening(f, wall, void)

    # A RoughOpening is intentionally only a void. Emitting it as IfcWindow used to
    # destroy the distinction required by round-trip authoring applications.
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
    _assign_representation(f, filling, ll.add_prism_from_profile(
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
                project_uuid: Any) -> None:
    space = ll.create_entity(f, "IfcSpace", name=room.tag)
    space.GlobalId = derive_guid(project_uuid, room.uid)
    if room.clear_face:
        rep = ll.add_prism_from_profile(f, body, room.clear_face, 2.7, 0.0)
        _assign_representation(f, space, rep)
    ll.ensure_pset(f, space, PSET_SOURCE, {"uid": room.uid, "tag": room.tag})
    ll.ensure_pset(f, space, "Pset_SpaceCommon", {
        "IsExternal": False, "PubliclyAccessible": False,
    })
    # IfcSpace is itself a spatial structure, so it belongs in the storey aggregation
    # rather than an IfcRelContainedInSpatialStructure product relationship.
    _relate(f, storeys[room.storey], [space])


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
            _assign_representation(f, element, ll.add_prism_from_profile(
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
        _assign_representation(f, element, ll.add_prism_from_profile(
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


def _emit_solid(f: Any, body: Any, solid: Any, storeys: dict[str, Any], project_uuid: Any,
                model: Any = None) -> None:
    ifc_class = {"slab": "IfcSlab", "column": "IfcColumn",
                 "beam": "IfcBeam"}.get(solid.category, "IfcFooting")
    element = ll.create_entity(f, ifc_class, name=solid.tag)
    element.GlobalId = derive_guid(project_uuid, solid.uid)
    if solid.outline:
        _assign_representation(
            f, element, ll.add_prism_from_profile(f, body, solid.outline, solid.z1_m - solid.z0_m,
                                                   solid.z0_m, solid.voids)
        )
    if model is not None:
        _assign_solid_material(f, element, solid, model)
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": solid.uid, "tag": solid.tag,
                                               "category": solid.category})
    ll.assign_container(f, element, storeys[solid.storey])


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


def _emit_roof(f: Any, body: Any, roof: Any, storeys: dict[str, Any], project_uuid: Any,
               lod: str) -> None:
    element = ll.create_entity(f, "IfcRoof", name=roof.tag)
    element.GlobalId = derive_guid(project_uuid, roof.uid)
    # IFC consumers still receive a stable roof object at core LOD.  The glTF path preserves
    # the pitched surface for interactive viewing; M3 can replace this core envelope with
    # faceted IFC roof-plane geometry without changing identity.
    _assign_representation(f, element, ll.add_prism_from_profile(
        f, body, roof.footprint, 0.0254, roof.eave_z_m
    ))
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": roof.uid, "tag": roof.tag,
                                               "assembly": roof.assembly})
    ll.assign_container(f, element, storeys[roof.storey])
    if lod == "framed" and roof.members:
        members = []
        for member in sorted(roof.members, key=lambda item: item.child_key):
            child = ll.create_entity(f, "IfcMember", name=f"{roof.tag}/{member.child_key}")
            child.GlobalId = derive_child_guid(project_uuid, roof.uid, member.child_key)
            members.append(child)
        ll.aggregate(f, element, members)


def _emit_stair(f: Any, stair: Any, storeys: dict[str, Any], project_uuid: Any, lod: str) -> None:
    element = ll.create_entity(f, "IfcStair", name=stair.tag)
    element.GlobalId = derive_guid(project_uuid, stair.uid)
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": stair.uid, "tag": stair.tag})
    ll.assign_container(f, element, storeys[stair.storey])
    if lod != "framed":
        return
    members = []
    for member in sorted(stair.members, key=lambda item: item.child_key):
        child = ll.create_entity(f, "IfcMember", name=f"{stair.tag}/{member.child_key}")
        child.GlobalId = derive_child_guid(project_uuid, stair.uid, member.child_key)
        members.append(child)
    if members:
        ll.aggregate(f, element, members)


def _emit_pipe_run(f: Any, body: Any, run: Any, storeys: dict[str, Any], project_uuid: Any) -> None:
    """One IfcPipeSegment per path segment — a plan rectangle of width ``diameter_m``
    around the centerline, extruded ``diameter_m`` tall at the segment's interpolated
    invert (a boxy placeholder profile, not a true cylindrical sweep, → Phase 2 spec)."""
    half = run.diameter_m / 2.0
    cumulative = 0.0
    for index in range(len(run.path) - 1):
        p0, p1 = run.path[index], run.path[index + 1]
        seg_len = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
        z0 = _interpolated_invert(run, cumulative, cumulative + seg_len)
        cumulative += seg_len
        profile = rect_between(p0, p1, -half, half)
        child_key = f"seg-{index:02d}"
        element = ll.create_entity(f, "IfcPipeSegment", name=f"{run.tag}/{child_key}")
        element.GlobalId = derive_child_guid(project_uuid, run.uid, child_key)
        _assign_representation(f, element, ll.add_prism_from_profile(
            f, body, profile, run.diameter_m, z0 - half,
        ))
        ll.ensure_pset(f, element, PSET_SOURCE, {"uid": run.uid, "tag": run.tag})
        ll.ensure_pset(f, element, "TypeHaus_Pipe", {
            "system": run.system, "diameter_m": run.diameter_m,
            "slope": _slope_text(run),
        })
        ll.assign_container(f, element, storeys[run.storey])


def _interpolated_invert(run: Any, from_len: float, to_len: float) -> float:
    """Invert elevation at the segment midpoint, linearly interpolated along the run."""
    if run.z_start_m is None or run.z_end_m is None or run.length_m <= 1e-9:
        return run.z_start_m if run.z_start_m is not None else 0.0
    mid = (from_len + to_len) / 2.0
    t = mid / run.length_m
    return run.z_start_m + t * (run.z_end_m - run.z_start_m)


def _slope_text(run: Any) -> str:
    if run.z_start_m is None or run.z_end_m is None or run.length_m <= 1e-9:
        return "unknown"
    drop_in = (run.z_start_m - run.z_end_m) * 39.37007874015748
    slope_in_per_ft = drop_in / (run.length_m * 3.280839895)
    return f"{slope_in_per_ft:.3f} in/ft"


def _emit_duct_run(f: Any, body: Any, model: ResolvedModel, duct: Any, storeys: dict[str, Any],
                   project_uuid: Any) -> None:
    """One IfcDuctSegment per path segment, a width x depth box at the floor's joist
    ``z0_m`` for JOIST_BAY routing (→ Phase 3 spec)."""
    half = duct.width_m / 2.0
    floor = next((item for item in model.floors if item.tag == duct.floor_ref), None)
    if duct.routing == "joist_bay" and floor is not None and floor.members:
        z0 = floor.members[0].z0_m
    else:
        z0 = next((s.elevation.meters for s in model.plan.storeys if s.tag == duct.storey), 0.0)
    for index in range(len(duct.path) - 1):
        p0, p1 = duct.path[index], duct.path[index + 1]
        profile = rect_between(p0, p1, -half, half)
        child_key = f"seg-{index:02d}"
        element = ll.create_entity(f, "IfcDuctSegment", name=f"{duct.tag}/{child_key}")
        element.GlobalId = derive_child_guid(project_uuid, duct.uid, child_key)
        _assign_representation(f, element, ll.add_prism_from_profile(
            f, body, profile, duct.depth_m, z0,
        ))
        ll.ensure_pset(f, element, PSET_SOURCE, {"uid": duct.uid, "tag": duct.tag})
        ll.ensure_pset(f, element, "TypeHaus_Duct", {
            "system": duct.system, "width_in": duct.width_m * 39.37007874015748,
            "depth_in": duct.depth_m * 39.37007874015748, "routing": duct.routing,
        })
        ll.assign_container(f, element, storeys[duct.storey])


def _emit_registers_equipment_devices(f: Any, body: Any, model: ResolvedModel,
                                      storeys: dict[str, Any], project_uuid: Any) -> None:
    type_collections = {
        "Register": {item.tag: item for item in model.plan.library.register_types},
        "Equipment": {item.tag: item for item in model.plan.library.equipment_types},
        "ElectricalDevice": {item.tag: item for item in model.plan.library.electrical_device_types},
    }
    resolved = {item.uid: item for item in model.canvas_objects}
    type_cache: dict[tuple[str, str], Any] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            product_type = type_collections.get(element.element_kind, {}).get(getattr(element, "type_ref", None))
            resolved_item = resolved.get(element.uid)
            if element.element_kind == "Register":
                _emit_register(f, body, element, storey, storeys, project_uuid, product_type, resolved_item,
                               _placeable_ifc_type(f, type_cache, product_type, "IfcAirTerminal",
                                                   "IfcAirTerminalType", project_uuid))
            elif element.element_kind == "Equipment":
                _emit_equipment(f, body, element, storey, storeys, project_uuid, product_type, resolved_item,
                                _placeable_ifc_type(f, type_cache, product_type, "IfcBuildingElementProxy",
                                                    "IfcBuildingElementProxyType", project_uuid))
            elif element.element_kind == "ElectricalDevice":
                ifc_class, type_class = _device_ifc_classes(element.kind.value)
                _emit_device(f, body, element, storey, storeys, project_uuid, product_type, resolved_item,
                             _placeable_ifc_type(f, type_cache, product_type, ifc_class, type_class, project_uuid))


def _emit_register(f: Any, body: Any, register: Any, storey: Any, storeys: dict[str, Any],
                   project_uuid: Any, product_type: Any | None, resolved: Any | None,
                   type_object: Any | None) -> None:
    x, y = register.position.xy_m
    outline = resolved.footprint if resolved is not None else _rectangle(x, y, 0.10, 0.10)
    height = product_type.height.meters if product_type is not None else 0.05
    z0 = resolved.z_m if resolved is not None else storey.elevation.meters
    element = ll.create_entity(f, "IfcAirTerminal", name=register.tag)
    element.GlobalId = derive_guid(project_uuid, register.uid)
    _assign_representation(f, element, ll.add_prism_from_profile(
        f, body, outline, height, z0,
    ))
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": register.uid, "tag": register.tag,
                                               "rotation_degrees": _rotation_metadata(register, resolved)})
    ll.ensure_pset(f, element, "TypeHaus_Identity", {"uid": register.uid, "tag": register.tag,
                                                        "source_type": register.type_ref or ""})
    if product_type is not None:
        _emit_service_ports(f, element, product_type.ports, project_uuid, register.uid)
    if type_object is not None:
        ll.assign_type(f, element, type_object)
    ll.assign_container(f, element, storeys[storey.tag])


def _rotation_metadata(element: Any, resolved: Any | None) -> str:
    """Persist the resolved plan bearing so IFC reconciliation can name rotation edits."""
    degrees = resolved.rotation_degrees if resolved is not None else getattr(
        getattr(element, "rotation", None), "degrees", 0.0,
    )
    return f"{degrees:.6f}"


def _emit_equipment(f: Any, body: Any, equipment: Any, storey: Any, storeys: dict[str, Any],
                    project_uuid: Any, product_type: Any | None, resolved: Any | None,
                    type_object: Any | None) -> None:
    width, depth = (dim.meters for dim in equipment.footprint)
    x, y = equipment.position.xy_m
    outline = resolved.footprint if resolved is not None else _rectangle(x, y, width, depth)
    height = product_type.height.meters if product_type is not None else 1.5
    z0 = resolved.z_m if resolved is not None else storey.elevation.meters
    element = ll.create_entity(f, "IfcBuildingElementProxy", name=equipment.tag)
    element.GlobalId = derive_guid(project_uuid, equipment.uid)
    _assign_representation(f, element, ll.add_prism_from_profile(
        f, body, outline, height, z0,
    ))
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": equipment.uid, "tag": equipment.tag,
                                               "rotation_degrees": _rotation_metadata(equipment, resolved)})
    ll.ensure_pset(f, element, "TypeHaus_Identity", {"uid": equipment.uid, "tag": equipment.tag,
                                                        "source_type": equipment.type_ref or ""})
    ll.ensure_pset(f, element, "TypeHaus_Equipment", {"kind": equipment.kind.value})
    if product_type is not None:
        _emit_service_ports(f, element, product_type.ports, project_uuid, equipment.uid)
    if type_object is not None:
        ll.assign_type(f, element, type_object)
    ll.assign_container(f, element, storeys[storey.tag])


def _emit_device(f: Any, body: Any, device: Any, storey: Any, storeys: dict[str, Any],
                 project_uuid: Any, product_type: Any | None, resolved: Any | None,
                 type_object: Any | None) -> None:
    x, y = device.position.xy_m
    half = 0.05  # 4"x4" nominal device box
    outline = resolved.footprint if resolved is not None else _rectangle(x, y, half * 2, half * 2)
    outlet_kinds = ("receptacle", "gfci", "receptacle_240")
    mount_default = 1.219 if device.kind.value in outlet_kinds else 0.406
    mount = device.mount_height.meters if device.mount_height is not None else mount_default
    z0 = resolved.z_m if resolved is not None else storey.elevation.meters + mount
    ifc_class, _ = _device_ifc_classes(device.kind.value)
    element = ll.create_entity(f, ifc_class, name=device.tag)
    element.GlobalId = derive_guid(project_uuid, device.uid)
    _assign_representation(f, element, ll.add_prism_from_profile(
        f, body, outline, product_type.height.meters if product_type is not None else 0.05, z0))
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": device.uid, "tag": device.tag,
                                               "rotation_degrees": _rotation_metadata(device, resolved)})
    ll.ensure_pset(f, element, "TypeHaus_Identity", {"uid": device.uid, "tag": device.tag,
                                                        "source_type": device.type_ref or ""})
    ll.ensure_pset(f, element, "TypeHaus_Device", {
        "kind": device.kind.value, "circuit": device.circuit or "",
    })
    if product_type is not None:
        _emit_service_ports(f, element, product_type.ports, project_uuid, device.uid)
    if type_object is not None:
        ll.assign_type(f, element, type_object)
    ll.assign_container(f, element, storeys[storey.tag])


def _placeable_ifc_type(f: Any, cache: dict[tuple[str, str], Any], product_type: Any | None,
                        ifc_class: str, type_class: str, project_uuid: Any) -> Any | None:
    if product_type is None:
        return None
    key = (ifc_class, product_type.tag)
    if key not in cache:
        entity = ll.create_entity(f, type_class, name=product_type.name)
        entity.GlobalId = derive_child_guid(project_uuid, f"{ifc_class}-types", product_type.tag)
        ll.ensure_pset(f, entity, "TypeHaus_Identity", _type_identity(product_type))
        cache[key] = entity
    return cache[key]


def _device_ifc_classes(kind: str) -> tuple[str, str]:
    return {
        "receptacle": ("IfcOutlet", "IfcOutletType"), "gfci": ("IfcOutlet", "IfcOutletType"),
        "receptacle_240": ("IfcOutlet", "IfcOutletType"),
        "switch": ("IfcSwitchingDevice", "IfcSwitchingDeviceType"),
        "light": ("IfcLightFixture", "IfcLightFixtureType"),
        "panel": ("IfcElectricDistributionBoard", "IfcElectricDistributionBoardType"),
    }.get(kind, ("IfcBuildingElementProxy", "IfcBuildingElementProxyType"))


def _rectangle(x: float, y: float, width: float, depth: float) -> list[tuple[float, float]]:
    return [(x - width / 2, y - depth / 2), (x + width / 2, y - depth / 2),
            (x + width / 2, y + depth / 2), (x - width / 2, y + depth / 2)]


def _emit_sleeve(f: Any, body: Any, sleeve: Any, storeys: dict[str, Any],
                 project_uuid: Any) -> None:
    """A visible marker at the exact cast-in-place point (host slab's full z0..z1)."""
    half = sleeve.sleeve_d_m / 2.0
    cx, cy = sleeve.center
    outline = [(cx - half, cy - half), (cx + half, cy - half),
               (cx + half, cy + half), (cx - half, cy + half)]
    element = ll.create_entity(f, "IfcBuildingElementProxy", name=sleeve.tag)
    element.GlobalId = derive_guid(project_uuid, sleeve.uid)
    _assign_representation(f, element, ll.add_prism_from_profile(
        f, body, outline, sleeve.z1_m - sleeve.z0_m, sleeve.z0_m,
    ))
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": sleeve.uid, "tag": sleeve.tag,
                                               "host": sleeve.host_slab})
    ll.ensure_pset(f, element, "TypeHaus_Sleeve", {
        "host": sleeve.host_slab,
        "pipe_diameter_in": sleeve.pipe_d_m * 39.37007874015748,
        "sleeve_diameter_in": sleeve.sleeve_d_m * 39.37007874015748,
        "serves_fixture": sleeve.serves_fixture or "",
    })
    ll.assign_container(f, element, storeys[sleeve.storey])


def _emit_footing_bedding(f: Any, body: Any, bedding: Any, storeys: dict[str, Any],
                          project_uuid: Any) -> None:
    """Excavation/bedding prep as a proxy solid under the footing (its own outline,
    from the compacted-stone-bed underside up to the footing underside)."""
    element = ll.create_entity(f, "IfcBuildingElementProxy", name=bedding.tag)
    element.GlobalId = derive_guid(project_uuid, bedding.uid)
    _assign_representation(f, element, ll.add_prism_from_profile(
        f, body, bedding.outline, bedding.z1_m - bedding.z0_m, bedding.z0_m,
    ))
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": bedding.uid, "tag": bedding.tag,
                                               "host": bedding.host_footing})
    ll.ensure_pset(f, element, "TypeHaus_FootingBedding", {
        "host": bedding.host_footing,
        "aggregate": bedding.aggregate,
        "geotextile": bedding.geotextile,
        "drain_tile": bedding.drain_tile,
        "perimeter_insulation_in": (bedding.perimeter_insulation_m * 39.37007874015748
                                    if bedding.perimeter_insulation_m is not None else 0.0),
        "cast_foam_in_aggregate": bedding.cast_foam_in_aggregate,
    })
    ll.assign_container(f, element, storeys[bedding.storey])


def _georef(f: Any, ifc_project: Any, model: ResolvedModel, source_context: Any) -> None:
    """IfcProjectedCRS + IfcMapConversion from Site (pyproj transforms, → 12)."""
    site = model.plan.project.site
    crs = f.createIfcProjectedCRS(site.crs)
    try:
        import pyproj

        transformer = pyproj.Transformer.from_crs("EPSG:4326", site.crs, always_xy=True)
        easting, northing = transformer.transform(site.lon, site.lat)
    except Exception:  # noqa: BLE001 - georef is best-effort in M1
        easting, northing = 0.0, 0.0
    f.createIfcMapConversion(
        source_context, crs, easting, northing, site.elevation.meters,
        1.0, 0.0,  # XAxisAbscissa/Ordinate — true_north rotation applied here
        1.0,
    )


def _outer_profile(rw: ResolvedWall) -> list[tuple[float, float]]:
    """Exact union outer ring across resolved depth-bearing layer polygons."""
    polygons = [
        Polygon(layer.polygon) for layer in rw.depth_layers()
        if len(layer.polygon) >= 3
    ]
    if not polygons:
        return [(0, 0), (1, 0), (1, 0.1), (0, 0.1)]
    geometry = unary_union(polygons)
    candidates = [geometry] if isinstance(geometry, Polygon) else [
        item for item in geometry.geoms if isinstance(item, Polygon)
    ]
    polygon = max(candidates, key=lambda item: item.area)
    return [(float(x), float(y)) for x, y in list(polygon.exterior.coords)[:-1]]


def _content_hash(rw: ResolvedWall) -> str:
    geometry = tuple(
        (layer.name, layer.thickness_m, tuple(layer.polygon))
        for layer in rw.layers
    )
    h = hashlib.sha256(
        repr((rw.uid, rw.assembly, rw.axis, rw.z0_m, rw.z1_m, geometry)).encode()
    )
    return h.hexdigest()[:12]


def _assign_representation(f: Any, element: Any, rep: Any) -> None:
    _assign_representations(f, element, [rep])


def _assign_representations(f: Any, element: Any, representations: list[Any]) -> None:
    element.Representation = f.createIfcProductDefinitionShape(
        None, None, representations
    )
    # Geometry is authored in the shared project frame inside its swept solid. IFC still
    # requires every represented product to carry an ObjectPlacement; an identity placement
    # expresses that frame explicitly and satisfies both schema validation and BIM importers.
    ll.ensure_local_placement(f, element)


def _relate(f: Any, parent: Any, children: list[Any]) -> None:
    import ifcopenshell.api

    ifcopenshell.api.run("aggregate.assign_object", f, products=children,
                         relating_object=parent)
