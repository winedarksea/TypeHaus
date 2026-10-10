"""IFC products for resolved interior millwork: stools, base runs and door casings."""

from __future__ import annotations

from typing import Any

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.model.ids import derive_guid
from typehaus.resolve.geometry_millwork import (
    base_run_prisms,
    door_casing_prisms,
    window_stool_prism,
)
from typehaus.resolve.model import ResolvedModel


def emit_window_stools(f: Any, body: Any, model: ResolvedModel,
                       storeys: dict[str, Any], project_uuid: Any) -> dict[str, Any]:
    """One oak molding per window, using the same board prism as model.json and GLB."""
    walls = {wall.tag: wall for wall in model.walls}
    openings = {opening.tag: opening for opening in model.openings}
    entities: dict[str, Any] = {}
    for stool in sorted(model.window_stools, key=lambda item: item.uid):
        opening = openings.get(stool.window_ref)
        wall = walls.get(stool.wall_tag)
        if opening is None or wall is None or stool.storey not in storeys:
            continue
        prism = window_stool_prism(wall, opening, stool)
        if prism is None:
            continue
        element = ll.create_entity(f, "IfcCovering", name=stool.tag)
        element.GlobalId = derive_guid(project_uuid, stool.uid)
        element.PredefinedType = "MOLDING"
        ll.assign_representation(f, element, ll.add_prism_from_profile(
            f, body, list(prism.ring), prism.z1_m - prism.z0_m, prism.z0_m))
        material = f.create_entity("IfcMaterial", Name=stool.material_ref)
        f.create_entity("IfcRelAssociatesMaterial", RelatedObjects=[element],
                        RelatingMaterial=material)
        ll.ensure_pset(f, element, PSET_SOURCE, {
            "uid": stool.uid, "tag": stool.tag, "window_ref": stool.window_ref,
            "host_wall": stool.wall_tag, "material_ref": stool.material_ref,
            "profile": stool.profile,
        })
        ll.assign_container(f, element, storeys[stool.storey])
        entities[stool.tag] = element
    return entities


def emit_interior_trim(f: Any, body: Any, model: ResolvedModel,
                       storeys: dict[str, Any], project_uuid: Any) -> dict[str, Any]:
    """One ``IfcCovering`` per base run (SKIRTINGBOARD) and per door casing (MOLDING).

    The same prisms model.json and the GLB draw. A tile base or a flash cove is not a board
    and carries no prism; it stays in the takeoff only.
    """
    entities: dict[str, Any] = {}
    records = ([(run, "SKIRTINGBOARD", base_run_prisms(run),
                 {"room": run.room, "host_wall": run.wall_tag, "kind": run.kind})
                for run in sorted(model.base_runs, key=lambda item: item.uid)]
               + [(casing, "MOLDING", door_casing_prisms(casing),
                   {"room": casing.room, "host_wall": casing.wall_tag,
                    "door_ref": casing.opening_ref})
                  for casing in sorted(model.door_casings, key=lambda item: item.uid)])
    for record, predefined, prisms, extra in records:
        if not prisms or record.storey not in storeys:
            continue
        element = ll.create_entity(f, "IfcCovering", name=record.tag)
        element.GlobalId = derive_guid(project_uuid, record.uid)
        element.PredefinedType = predefined
        ll.assign_representation(f, element, ll.add_prisms_at_elevations(
            f, body, [(list(p.ring), p.z0_m, p.z1_m) for p in prisms]))
        material = f.create_entity("IfcMaterial", Name=record.material_ref)
        f.create_entity("IfcRelAssociatesMaterial", RelatedObjects=[element],
                        RelatingMaterial=material)
        ll.ensure_pset(f, element, PSET_SOURCE, {
            "uid": record.uid, "tag": record.tag, "material_ref": record.material_ref,
            "profile": record.profile, **extra,
        })
        ll.assign_container(f, element, storeys[record.storey])
        entities[record.tag] = element
    return entities
