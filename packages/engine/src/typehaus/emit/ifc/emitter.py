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
from typehaus.emit.ifc.electrical import (emit_conduits, emit_light_runs,
                                          emit_solar_panels)
from typehaus.emit.ifc.roof import emit_roof, member_class, member_representation
from typehaus.emit.trades import DRAINAGE_CATEGORIES, PIPE_ACCESSORY_CATEGORIES
from typehaus.emit.room_floor import room_floor_elevation
from typehaus.model.enums import DoorOperation
from typehaus.model.ids import derive_child_guid, derive_guid
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import polygon_area, rect_between
from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.resolve.placeables import resolved_mount_elevation


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
        ll.set_storey_elevation(f, ifc_storey, storey.elevation.meters)
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

    drainage_elements = []
    for solid in sorted(model.solids, key=lambda item: item.uid):
        # Pipe accessories have a dedicated emitter (``_emit_pipe_accessories``) that knows
        # which IfcValve PredefinedType each kind is. Emitting the solid too would put a
        # second, untyped copy of every shutoff in the file — and, since none of these
        # categories is in ``_SOLID_IFC_CLASS``, that copy would be an ``IfcFooting``.
        if (solid.category or "").lower() in PIPE_ACCESSORY_CATEGORIES:
            continue
        element = _emit_solid(f, body, solid, storeys, project_uuid, model)
        if (solid.category or "").lower() in DRAINAGE_CATEGORIES:
            drainage_elements.append(element)
    drainage_elements.extend(_emit_sump_pumps(f, model, storeys, project_uuid))
    _emit_stormwater_system(f, building, drainage_elements)

    for ret in sorted(model.construction_returns, key=lambda item: item.uid):
        _emit_construction_return(f, body, ret, storeys, project_uuid)

    for roof in sorted(model.roofs, key=lambda item: item.uid):
        emit_roof(f, body, roof, storeys, project_uuid, lod, model)

    for floor in sorted(model.floors, key=lambda item: item.uid):
        _emit_floor(f, body, floor, storeys, project_uuid, model)

    for stair in sorted(model.stairs, key=lambda item: item.uid):
        _emit_stair(f, body, stair, storeys, project_uuid, lod)

    for brace in sorted(model.braces, key=lambda item: item.uid):
        _emit_brace(f, body, brace, storeys, project_uuid)

    for room in sorted(model.rooms, key=lambda r: r.uid):
        _emit_space(f, body, room, storeys, project_uuid, model)

    _emit_furniture(f, body, model, storeys, project_uuid)
    _emit_resolved_placeables(f, body, model, storeys, project_uuid)

    # The domestic-water systems, built the way the stormwater one above is: the segments
    # and the devices on them are collected as they are emitted, then grouped. Two systems
    # rather than one, because hot and cold are two systems in every tool that reads this —
    # a recirculation loop, an insulation requirement and a mixing valve all belong to one
    # of them and not the other.
    supply_elements: dict[str, list] = {"water_cold": [], "water_hot": []}
    for run in sorted(model.pipe_runs, key=lambda item: item.uid):
        segments = _emit_pipe_run(f, body, run, storeys, project_uuid)
        supply_elements.get(run.system, []).extend(segments)
    for accessory, entity in _emit_pipe_accessories(f, body, model, storeys, project_uuid):
        supply_elements.get(accessory.system or "", []).append(entity)
    for system_key, name in _SUPPLY_SYSTEM_NAMES.items():
        _emit_supply_system(f, building, name, supply_elements[system_key])

    for sleeve in sorted(model.sleeves, key=lambda item: item.uid):
        _emit_sleeve(f, body, sleeve, storeys, project_uuid)

    for duct in sorted(model.ducts, key=lambda item: item.uid):
        _emit_duct_run(f, body, model, duct, storeys, project_uuid)

    emit_conduits(f, body, model, storeys, project_uuid, _assign_representation)
    emit_light_runs(f, body, model, storeys, project_uuid, _assign_representation)
    emit_solar_panels(f, body, model, storeys, project_uuid, _assign_representation)

    _emit_registers_equipment_devices(f, body, model, storeys, project_uuid)
    _emit_utilities(f, body, model, project_uuid)

    for bedding in sorted(model.footing_beddings, key=lambda item: item.uid):
        _emit_footing_bedding(f, body, bedding, storeys, project_uuid)

    f.write(str(out_path))
    return out_path


def _earth_sheet(model: ResolvedModel):
    """The IR's site earth prism, or ``None`` when the model carries no derived geometry.

    ``resolve_preview`` skips the geometry stage deliberately, so every IR read in this
    emitter is optional rather than assumed.
    """
    geometry = getattr(model, "geometry", None)
    element = geometry.by_uid("site-earth") if geometry is not None else None
    if element is None or not element.parts:
        return None
    return element.parts[0].solids[0]


def _emit_site_representation(f: Any, body: Any, ifc_site: Any, model: ResolvedModel) -> None:
    """The earth sheet of the parcel ring — imports as a lot slab (Phase 4).

    The sheet is cut by every excavated footprint (house, garage, sunken garden — see
    ``resolve/site_earth.py``); without those voids the lot slab runs straight through the
    interior spaces that were dug out of it.

    Geometry comes from the IR, which puts the sheet's *top* face on the grade plane. IFC
    used to extrude the same ring 5cm **upward** from grade, so the ground the exporter
    handed Revit stood 5cm above the ground the viewer drew and every slab-on-grade sat that
    much proud of its own site. Soil is what is under grade; this is the reconciliation the
    earth's blessed diff called for.
    """
    site = model.plan.project.site
    parcel = [p.xy_m for p in site.parcel]
    if len(parcel) < 3:
        return
    sheet = _earth_sheet(model)
    if sheet is not None:
        _assign_representation(f, ifc_site, ll.add_prism_from_profile(
            f, body, list(sheet.ring), sheet.z1_m - sheet.z0_m, sheet.z0_m, sheet.voids))
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
            member = _emit_framed_member(f, body, rw.tag, rw.uid, m, project_uuid)
            members.append(member)
        ll.aggregate(f, wall, members)
    return wall


# Profiles that describe a board tapered *in plan* (the winder tread runs from a newel-face
# sliver to a full nosing): no constant cross-section swept along the axis can represent
# one, so its member keeps the bare pre-representation form instead of a wrong box.
_UNSWEEPABLE_PROFILES = frozenset({"tapered tread"})


def _member_body(f: Any, body: Any, member: Any) -> Any | None:
    """``member_representation`` with the graceful degradation the generated packs need.

    Wall and stair packs run through thousands of generated members; one profile the
    section catalog cannot honestly sweep must degrade to the old bare (representation-
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
    as ``IfcMember``/STUD with true geometry rather than the bare identity placeholder
    these packs used to emit.
    """
    ifc_class, predefined = member_class(member.category)
    child = ll.create_entity(f, ifc_class, name=f"{parent_tag}/{member.child_key}")
    child.GlobalId = derive_child_guid(project_uuid, parent_uid, member.child_key)
    if predefined is not None:
        child.PredefinedType = predefined
    representation = _member_body(f, body, member)
    if representation is not None:
        _assign_representation(f, child, representation)
    ll.ensure_pset(f, child, PSET_SOURCE, {
        "uid": parent_uid, "tag": f"{parent_tag}/{member.child_key}",
        "category": member.category, "profile": member.profile,
    })
    return child


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
    _assign_representation(f, void, representation)
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
    "connector": ("IfcMechanicalFastener", None),
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


STORMWATER_SYSTEM_NAME = "Stormwater"


def _emit_sump_pumps(f: Any, model: ResolvedModel, storeys: dict[str, Any],
                     project_uuid: Any) -> list:
    """An ``IfcPump/SUMPPUMP`` for every pit that carries one.

    The pump is a spec on the ``Sump``, not an element with a plan position of its own, so
    it has no solid and would otherwise never reach IFC — leaving the export with a pit and
    no way to say the water leaves it under power. No representation: what matters here is
    that the equipment exists, is on a named circuit, and belongs to the stormwater system.
    """
    pumps = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            pump = getattr(element, "pump", None)
            if pump is None or element.element_kind != "Sump":
                continue
            entity = ll.create_entity(f, "IfcPump", name=f"{element.tag}-PUMP")
            entity.PredefinedType = "SUMPPUMP"
            entity.GlobalId = derive_child_guid(project_uuid, element.uid, "pump")
            ll.ensure_pset(f, entity, PSET_SOURCE, {
                "uid": element.uid, "tag": element.tag, "category": "sump_pump"})
            ll.ensure_pset(f, entity, "TypeHaus_SumpPump", {
                "model": pump.model, "horsepower": pump.horsepower,
                "discharge": pump.discharge or "", "circuit_ref": pump.circuit_ref or ""})
            ll.assign_container(f, entity, storeys[storey.tag])
            pumps.append(entity)
    return pumps


def _emit_stormwater_system(f: Any, building: Any, elements: list) -> Any:
    """Group every drainage element into one ``IfcDistributionSystem/STORMWATER``.

    The gutter, the leader it drops into, the perimeter tile and the pit are one system in
    the building even though they resolve from four unrelated authored elements. Saying so in
    IFC is the difference between a BIM tool showing "Stormwater" in its system browser and
    showing four unrelated proxies that happen to be near each other.
    """
    if not elements:
        return None
    system = ll.create_system(f, STORMWATER_SYSTEM_NAME, "STORMWATER")
    ll.assign_to_group(f, system, elements)
    ll.serves_building(f, system, building)
    return system


#: ``PipeSystem`` value → the ``IfcDistributionSystem`` it belongs to, as
#: ``(system name, PredefinedType)``. Sanitary and rainwater stay deferred (plans/TODO.md);
#: these two are the ones the supply-protection work needs, and they are the two IFC has
#: unambiguous enum members for.
_SUPPLY_SYSTEM_TYPES = {
    "water_cold": ("DomesticColdWater", "DOMESTICCOLDWATER"),
    "water_hot": ("DomesticHotWater", "DOMESTICHOTWATER"),
}
_SUPPLY_SYSTEM_NAMES = {key: name for key, (name, _) in _SUPPLY_SYSTEM_TYPES.items()}

# What a ``PipeAccessoryKind`` becomes in IFC. The valves are ``IfcValve`` with the
# PredefinedType that says which valve it is — ISOLATING for a shutoff, DOUBLECHECK for a
# backflow assembly, ANTIVACUUM for a hose-bib vacuum breaker, DRAWOFFCOCK for the capped RO
# tee (a draw-off point that is not yet drawn off). The other two are not valves at all: an
# arrestor is a sealed chamber in the line and a penetration seal is a fitting around it, so
# both are ``IfcPipeFitting/USERDEFINED`` with an ObjectType naming what they are — inventing
# a valve type for either would put a device in a valve schedule that nobody can turn.
_ACCESSORY_IFC_CLASS: dict[str, tuple[str, str]] = {
    "main_shutoff": ("IfcValve", "ISOLATING"),
    "shutoff": ("IfcValve", "ISOLATING"),
    "backflow_preventer": ("IfcValve", "DOUBLECHECK"),
    "vacuum_breaker": ("IfcValve", "ANTIVACUUM"),
    "ro_stub": ("IfcValve", "DRAWOFFCOCK"),
    "water_hammer_arrestor": ("IfcPipeFitting", "USERDEFINED"),
    "penetration_seal": ("IfcPipeFitting", "USERDEFINED"),
}
_ACCESSORY_OBJECT_TYPE = {
    "water_hammer_arrestor": "WATERHAMMERARRESTOR",
    "penetration_seal": "PENETRATIONSEAL",
}


def _emit_pipe_accessories(f: Any, body: Any, model: ResolvedModel,
                           storeys: dict[str, Any], project_uuid: Any) -> list[tuple]:
    """Every in-line supply device as its own typed IFC element.

    Returns ``(accessory, entity)`` pairs so the caller can file each into the hot or cold
    system its host run belongs to. The box representation is the resolver's marker solid,
    rebuilt here rather than taken from ``model.solids`` because the generic solid loop
    deliberately skips this category — a device that fell through ``_SOLID_IFC_CLASS`` would
    export as an ``IfcFooting``, which is exactly the wart this emitter exists to avoid.
    """
    out: list[tuple] = []
    for accessory in sorted(model.pipe_accessories, key=lambda item: item.uid):
        ifc_class, predefined = _ACCESSORY_IFC_CLASS.get(
            accessory.kind, ("IfcPipeFitting", "USERDEFINED"))
        element = ll.create_entity(f, ifc_class, name=accessory.tag)
        element.PredefinedType = predefined
        object_type = _ACCESSORY_OBJECT_TYPE.get(accessory.kind)
        if object_type is not None:
            element.ObjectType = object_type
        element.GlobalId = derive_guid(project_uuid, accessory.uid)
        solid = next((s for s in model.solids
                      if s.tag == accessory.tag
                      and s.category in PIPE_ACCESSORY_CATEGORIES), None)
        if solid is not None and solid.outline:
            _assign_representation(f, element, ll.add_prism_from_profile(
                f, body, solid.outline, solid.z1_m - solid.z0_m, solid.z0_m))
        # The category is per-device (``emit/trades.py``), so it carries into the file as the
        # device rather than as the family — a downstream reader filtering PSET_SOURCE gets
        # "vacuum_breaker", the same string every other consumer of this solid sees.
        ll.ensure_pset(f, element, PSET_SOURCE, {
            "uid": accessory.uid, "tag": accessory.tag, "category": accessory.kind})
        ll.ensure_pset(f, element, "TypeHaus_PipeAccessory", {
            "kind": accessory.kind, "model": accessory.model,
            "pipe_ref": accessory.pipe_ref or "", "system": accessory.system or "",
            "accessible": accessory.accessible, "room": accessory.room or "",
            "serves": ", ".join(accessory.serves),
            "install_parts": ", ".join(accessory.install_parts)})
        ll.assign_container(f, element, storeys[accessory.storey])
        out.append((accessory, element))
    return out


def _emit_supply_system(f: Any, building: Any, name: str, elements: list) -> Any:
    """Group one temperature's segments and devices into an ``IfcDistributionSystem``.

    The same argument ``_emit_stormwater_system`` makes: without this the trunk, its
    branches and the shutoff on it are unrelated proxies that happen to be near each other,
    and a BIM tool's system browser shows nothing at all under domestic water.
    """
    if not elements:
        return None
    key = next(k for k, n in _SUPPLY_SYSTEM_NAMES.items() if n == name)
    system = ll.create_system(f, name, _SUPPLY_SYSTEM_TYPES[key][1])
    ll.assign_to_group(f, system, elements)
    ll.serves_building(f, system, building)
    return system


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
    return element


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
        _assign_representation(
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


_BEAM_PREDEFINED_TYPE = {"joist": "JOIST", "rim": "BEAM", "blocking": "BEAM"}


def _emit_floor(f: Any, body: Any, floor: Any, storeys: dict[str, Any],
                project_uuid: Any, model: ResolvedModel) -> None:
    """Emit a floor's subfloor deck as an ``IfcSlab``, and each joist/rim as an ``IfcBeam``.

    House decks and the porch/balcony deck both resolve to ``FramedMember`` joists that
    previously appeared only in the 2D framing plan and glTF. Emitting them here as IfcBeam
    (JOIST-predefined) gives BIM consumers the structural members with stable child GUIDs,
    following the standalone-beam pattern (``_emit_solid`` for category ``beam``)."""
    container = storeys.get(floor.storey)
    if container is None:
        return
    _emit_deck(f, body, floor, container, project_uuid, model)
    for member in sorted(floor.members, key=lambda item: item.child_key):
        if (member.p0[0] - member.p1[0]) ** 2 + (member.p0[1] - member.p1[1]) ** 2 < 1e-12:
            continue  # a zero-length record has no sweepable footprint
        half = cross_section(member.profile).width_m / 2.0
        profile = rect_between(member.p0, member.p1, -half, half)
        beam = ll.create_entity(f, "IfcBeam", name=f"{floor.tag}/{member.child_key}")
        beam.GlobalId = derive_child_guid(project_uuid, floor.uid, member.child_key)
        beam.PredefinedType = _BEAM_PREDEFINED_TYPE.get(member.category, "BEAM")
        _assign_representation(f, beam, ll.add_prism_from_profile(
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
    _assign_representation(f, slab, ll.add_prism_from_profile(
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
            _assign_representation(f, child, representation)
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


def _emit_pipe_run(f: Any, body: Any, run: Any, storeys: dict[str, Any],
                   project_uuid: Any) -> list:
    """One IfcPipeSegment per path segment — a plan rectangle of width ``diameter_m``
    around the centerline, extruded ``diameter_m`` tall at the segment's interpolated
    invert (a boxy placeholder profile, not a true cylindrical sweep, → Phase 2 spec).

    Returns the segments, so the caller can group a run's pieces into the
    ``IfcDistributionSystem`` its system belongs to."""
    segments: list = []
    half = run.diameter_m / 2.0
    cumulative = 0.0
    z_m = getattr(run, "z_m", None)
    for index in range(len(run.path) - 1):
        p0, p1 = run.path[index], run.path[index + 1]
        seg_len = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
        if z_m is not None:
            z0 = (z_m[index] + z_m[index + 1]) / 2.0
        else:
            z0 = _interpolated_invert(run, cumulative, cumulative + seg_len)
        cumulative += seg_len
        if seg_len < 1e-6:
            # Vertical drop (repeated plan point, different inverts): a square prism the
            # pipe's own section, spanning the drop.
            if z_m is None or abs(z_m[index + 1] - z_m[index]) < 1e-9:
                continue
            lo, hi = sorted((z_m[index], z_m[index + 1]))
            profile = [(p0[0] - half, p0[1] - half), (p0[0] + half, p0[1] - half),
                       (p0[0] + half, p0[1] + half), (p0[0] - half, p0[1] + half)]
            height, base = hi - lo, lo
        else:
            profile = rect_between(p0, p1, -half, half)
            height, base = run.diameter_m, z0 - half
        child_key = f"seg-{index:02d}"
        element = ll.create_entity(f, "IfcPipeSegment", name=f"{run.tag}/{child_key}")
        segments.append(element)
        element.GlobalId = derive_child_guid(project_uuid, run.uid, child_key)
        _assign_representation(f, element, ll.add_prism_from_profile(
            f, body, profile, height, base,
        ))
        ll.ensure_pset(f, element, PSET_SOURCE, {"uid": run.uid, "tag": run.tag})
        ll.ensure_pset(f, element, "TypeHaus_Pipe", {
            "system": run.system, "diameter_m": run.diameter_m,
            "slope": _slope_text(run),
            # Blank rather than absent where unset: a pset key that comes and goes makes a
            # schedule column that comes and goes.
            "material": run.material or "", "finish": run.finish or "",
            "insulation": run.insulation or "",
        })
        ll.assign_container(f, element, storeys[run.storey])
    return segments


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
                ifc_class, type_class = _equipment_ifc_classes(element.kind.value)
                _emit_equipment(f, body, element, storey, storeys, project_uuid, product_type, resolved_item,
                                _placeable_ifc_type(f, type_cache, product_type, ifc_class,
                                                    type_class, project_uuid),
                                ifc_class)
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
    # Which family of terminal this is: a continuous-flow ventilation diffuser on the ERV's
    # balanced trunks, or a conditioned-air register on a heat-pump duct. Same IfcAirTerminal
    # class either way — they are sized on different bases, not built differently.
    ll.ensure_pset(f, element, "TypeHaus_AirTerminal", {
        "system": register.kind.value,
        "terminal_style": ("ventilation"
                           if getattr(product_type, "ventilation_terminal", False)
                           else "conditioned_air"),
        "duct_ref": register.duct_ref or "",
    })
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


def _equipment_ifc_classes(kind: str) -> tuple[str, str]:
    """Map an ``EquipmentKind`` onto a real IFC class where one exists.

    Split systems are ``IfcUnitaryEquipment`` — the IFC4 class for a packaged
    heating/cooling unit, which is what a condenser, a wall head and a concealed ducted air
    handler each are — and an ERV is ``IfcAirToAirHeatRecovery``. Everything else (water
    heaters, sauna heaters, resistance space heaters) has no better fit than the proxy it
    already emitted as — including FURNACE and AIR_HANDLER, which are arguably unitary
    equipment too but which nothing models yet; re-classing an element nobody authors would
    churn the round-trip diff for no reader's benefit.

    GUIDs are unaffected: ``derive_guid`` keys on the element uid, not the class, so a unit
    that was a proxy in an earlier emit keeps its GlobalId across this change.

    Mirrored by ``diff/ifc_adapter.py`` (``class_for_kind`` plus the external read list) —
    change both together or the round-trip diff reads the class change as a deletion.
    """
    return {
        "heat_pump": ("IfcUnitaryEquipment", "IfcUnitaryEquipmentType"),
        "indoor_head": ("IfcUnitaryEquipment", "IfcUnitaryEquipmentType"),
        "ducted_air_handler": ("IfcUnitaryEquipment", "IfcUnitaryEquipmentType"),
        "erv": ("IfcAirToAirHeatRecovery", "IfcAirToAirHeatRecoveryType"),
    }.get(kind, ("IfcBuildingElementProxy", "IfcBuildingElementProxyType"))


def _emit_equipment(f: Any, body: Any, equipment: Any, storey: Any, storeys: dict[str, Any],
                    project_uuid: Any, product_type: Any | None, resolved: Any | None,
                    type_object: Any | None,
                    ifc_class: str = "IfcBuildingElementProxy") -> None:
    width, depth = (dim.meters for dim in equipment.footprint)
    x, y = equipment.position.xy_m
    outline = resolved.footprint if resolved is not None else _rectangle(x, y, width, depth)
    height = product_type.height.meters if product_type is not None else 1.5
    z0 = resolved.z_m if resolved is not None else storey.elevation.meters
    element = ll.create_entity(f, ifc_class, name=equipment.tag)
    element.GlobalId = derive_guid(project_uuid, equipment.uid)
    _assign_representation(f, element, ll.add_prism_from_profile(
        f, body, outline, height, z0,
    ))
    ll.ensure_pset(f, element, PSET_SOURCE, {"uid": equipment.uid, "tag": equipment.tag,
                                               "rotation_degrees": _rotation_metadata(equipment, resolved)})
    ll.ensure_pset(f, element, "TypeHaus_Identity", {"uid": equipment.uid, "tag": equipment.tag,
                                                        "source_type": equipment.type_ref or ""})
    # The HVAC facts a Revit/SketchUp reader needs to identify the unit and its zone: the
    # ratings from the type, and the two authored relations (which rooms it serves, which
    # condenser it pairs with) that no geometry can carry. Empty string / 0.0 where the
    # datasheet number is not authored — an absent property is indistinguishable from a
    # property this emitter forgot.
    ll.ensure_pset(f, element, "TypeHaus_Equipment", {
        "kind": equipment.kind.value, "circuit": equipment.circuit or "",
        "zone_rooms": ",".join(getattr(equipment, "zone_rooms", ()) or ()),
        "outdoor_ref": getattr(equipment, "outdoor_ref", None) or "",
        "heating_capacity_btuh": float(
            getattr(product_type, "heating_capacity_btuh", None) or 0.0),
        "heating_capacity_at_design_btuh": float(
            getattr(product_type, "heating_capacity_at_design_btuh", None) or 0.0),
        "cooling_capacity_btuh": float(
            getattr(product_type, "cooling_capacity_btuh", None) or 0.0),
        "min_operating_temp_f": float(
            getattr(product_type, "min_operating_temp_f", None) or 0.0),
        "ventilation_cfm": float(getattr(product_type, "ventilation_cfm", None) or 0.0),
        "sensible_recovery_effectiveness": float(
            getattr(product_type, "sensible_recovery_effectiveness", None) or 0.0),
    })
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
    # The placeable resolver owns the Mount contract, so IFC reads the same elevation as
    # glTF and the UI instead of carrying its own per-kind defaults (which used to diverge).
    z0 = resolved.z_m if resolved is not None else resolved_mount_elevation(storey, device)
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
        photometry = _luminaire_photometry(product_type)
        if photometry:
            ll.ensure_pset(f, entity, "TypeHaus_Lighting", photometry)
        cache[key] = entity
    return cache[key]


def _luminaire_photometry(product_type: Any) -> dict[str, Any]:
    """A luminaire type's photometric row, or empty for anything that is not a luminaire.

    Colour temperature is a *type* property in every tool that models it — Revit's Initial
    Color Temperature, IFC's own light source — which is exactly why it belongs on the
    ``IfcLightFixtureType`` and not on each placed can. Two marks that differ only in
    Kelvin are therefore two IFC types, and this pset is what tells them apart downstream.
    Keys mirror ``emit/ifc/electrical.emit_light_runs`` so the point fixtures and the tape
    runs read alike; ``0``/``""`` stand in for a missing value because IFC psets are typed
    and a null would need a different property class.
    """
    form = getattr(product_type, "form", None)
    if form is None or getattr(product_type, "cct_k", "missing") == "missing":
        return {}
    return {
        "form": getattr(form, "value", str(form)),
        "type_mark": getattr(product_type, "type_mark", None) or "",
        "lamp": getattr(product_type, "lamp", None) or "",
        "watts": getattr(product_type, "watts", None) or 0.0,
        "watts_per_ft": getattr(product_type, "watts_per_ft", None) or 0.0,
        "lumens": getattr(product_type, "lumens", None) or 0.0,
        "cct_k": getattr(product_type, "cct_k", None) or 0,
        "cri": getattr(product_type, "cri", None) or 0,
        "voltage": getattr(product_type, "voltage", 120),
        "dimmable": bool(getattr(product_type, "dimmable", False)),
        "damp_rated": bool(getattr(product_type, "damp_rated", False)),
        "wet_rated": bool(getattr(product_type, "wet_rated", False)),
    }


def _device_ifc_classes(kind: str) -> tuple[str, str]:
    # Mirrored by diff/ifc_adapter.py (electrical_classes + the external read list) —
    # change both together or the round-trip diff reads an edit as a deletion.
    return {
        "receptacle": ("IfcOutlet", "IfcOutletType"), "gfci": ("IfcOutlet", "IfcOutletType"),
        "receptacle_240": ("IfcOutlet", "IfcOutletType"),
        "switch": ("IfcSwitchingDevice", "IfcSwitchingDeviceType"),
        "light": ("IfcLightFixture", "IfcLightFixtureType"),
        "panel": ("IfcElectricDistributionBoard", "IfcElectricDistributionBoardType"),
        "junction_box": ("IfcJunctionBox", "IfcJunctionBoxType"),
        "meter": ("IfcFlowMeter", "IfcFlowMeterType"),
        "disconnect": ("IfcSwitchingDevice", "IfcSwitchingDeviceType"),
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
