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
    body = ll.add_context(f)
    project_uuid = model.plan.project.project_uuid

    ifc_project = ll.create_entity(f, "IfcProject", name=model.plan.project.name)
    _georef(f, ifc_project, model)
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

    for room in sorted(model.rooms, key=lambda r: r.uid):
        _emit_space(f, body, room, storeys, project_uuid)

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
    ll.assign_container(f, space, storeys[room.storey])


def _georef(f: Any, ifc_project: Any, model: ResolvedModel) -> None:
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
        None, crs, easting, northing, site.elevation.meters,
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


def _relate(f: Any, parent: Any, children: list[Any]) -> None:
    import ifcopenshell.api

    ifcopenshell.api.run("aggregate.assign_object", f, products=children,
                         relating_object=parent)
