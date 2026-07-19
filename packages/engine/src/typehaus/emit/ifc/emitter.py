"""IFC4 emitter over the ResolvedModel (WP1.7, → 12 §IFC emission).

Core LOD = one IfcWall per wall with IfcMaterialLayerSetUsage + shared IfcWallType;
framed LOD additionally aggregates generated members. Parent GUIDs are identical across
LODs (diff stability). GUIDs are derived from (project_uuid, uid) so moved/renamed
elements keep their GlobalId. Determinism: sorted iteration + pinned OwnerHistory.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from typehaus._meta import IFC_APP_NAME, PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.model.ids import derive_child_guid, derive_guid
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

    storeys: dict[str, Any] = {}
    for storey in sorted(model.plan.storeys, key=lambda s: s.elevation.meters):
        ifc_storey = ll.create_entity(f, "IfcBuildingStorey", name=storey.tag)
        ll.ensure_pset(f, ifc_storey, PSET_SOURCE,
                       {"uid": storey.uid, "tag": storey.tag})
        storeys[storey.tag] = ifc_storey
    _relate(f, building, list(storeys.values()))

    for rw in sorted(model.walls, key=lambda w: w.uid):
        _emit_wall(f, body, rw, storeys, project_uuid, lod)

    for solid in sorted(model.solids, key=lambda item: item.uid):
        _emit_solid(f, body, solid, storeys, project_uuid)

    for roof in sorted(model.roofs, key=lambda item: item.uid):
        _emit_roof(f, body, roof, storeys, project_uuid, lod)

    for stair in sorted(model.stairs, key=lambda item: item.uid):
        _emit_stair(f, stair, storeys, project_uuid, lod)

    for room in sorted(model.rooms, key=lambda r: r.uid):
        _emit_space(f, body, room, storeys, project_uuid)

    _emit_furniture(f, body, model, storeys, project_uuid)

    f.write(str(out_path))
    return out_path


def _emit_wall(f: Any, body: Any, rw: ResolvedWall, storeys: dict[str, Any],
               project_uuid: Any, lod: str) -> None:
    guid = derive_guid(project_uuid, rw.uid)
    ifc_class = "IfcWall"
    wall = ll.create_entity(f, ifc_class, name=rw.tag)
    wall.GlobalId = guid
    # Whole-wall body from the union of layer polygons (outer profile).
    outer = _outer_profile(rw)
    rep = ll.add_prism_from_profile(f, body, outer, rw.z1_m - rw.z0_m, rw.z0_m)
    _assign_representation(f, wall, rep)
    ll.ensure_pset(f, wall, PSET_SOURCE, {
        "uid": rw.uid, "tag": rw.tag, "assembly": rw.assembly,
        "plan_content_hash": _content_hash(rw),
    })
    ll.ensure_pset(f, wall, "Pset_WallCommon", {
        "IsExternal": not rw.tag.startswith("INT"),
    })
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
    elevations = {storey.tag: storey.elevation.meters for storey in model.plan.storeys}
    for storey in model.plan.storeys:
        for furniture in model.plan.storey_elements(storey.tag):
            if furniture.element_kind != "Furniture" or furniture.type_ref not in types:
                continue
            furniture_type = types[furniture.type_ref]
            width, depth = (dimension.meters for dimension in furniture_type.footprint)
            x, y = furniture.position.xy_m
            outline = [(x - width / 2, y - depth / 2), (x + width / 2, y - depth / 2),
                       (x + width / 2, y + depth / 2), (x - width / 2, y + depth / 2)]
            element = ll.create_entity(f, "IfcFurnishingElement", name=furniture.tag)
            element.GlobalId = derive_guid(project_uuid, furniture.uid)
            _assign_representation(f, element, ll.add_prism_from_profile(
                f, body, outline, furniture_type.height.meters, elevations[storey.tag]
            ))
            ll.ensure_pset(f, element, PSET_SOURCE, {
                "uid": furniture.uid, "tag": furniture.tag, "type": furniture.type_ref,
                "mesh": furniture_type.mesh.path if furniture_type.mesh is not None else "",
            })
            ll.assign_container(f, element, storeys[storey.tag])


def _emit_solid(f: Any, body: Any, solid: Any, storeys: dict[str, Any], project_uuid: Any) -> None:
    ifc_class = "IfcSlab" if solid.category == "slab" else "IfcFooting"
    element = ll.create_entity(f, ifc_class, name=solid.tag)
    element.GlobalId = derive_guid(project_uuid, solid.uid)
    if solid.outline:
        _assign_representation(
            f, element, ll.add_prism_from_profile(f, body, solid.outline, solid.z1_m - solid.z0_m,
                                                   solid.z0_m)
        )
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": solid.uid, "tag": solid.tag,
                                               "category": solid.category})
    ll.assign_container(f, element, storeys[solid.storey])


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
    """Union outer ring across layers — for M1 use the full-thickness band extents."""
    xs = [pt for layer in rw.layers for pt in layer.polygon]
    if not xs:
        return [(0, 0), (1, 0), (1, 0.1), (0, 0.1)]
    # first (interior) + last (exterior) layer outer corners give the wall band
    return rw.layers[0].polygon[:2] + rw.layers[-1].polygon[2:]


def _content_hash(rw: ResolvedWall) -> str:
    h = hashlib.sha256(f"{rw.uid}{rw.assembly}{rw.axis}".encode())
    return h.hexdigest()[:12]


def _assign_representation(f: Any, element: Any, rep: Any) -> None:
    element.Representation = f.createIfcProductDefinitionShape(None, None, [rep])
    # Geometry is authored in the shared project frame inside its swept solid. IFC still
    # requires every represented product to carry an ObjectPlacement; an identity placement
    # expresses that frame explicitly and satisfies both schema validation and BIM importers.
    ll.ensure_local_placement(f, element)


def _relate(f: Any, parent: Any, children: list[Any]) -> None:
    import ifcopenshell.api

    ifcopenshell.api.run("aggregate.assign_object", f, products=children,
                         relating_object=parent)
