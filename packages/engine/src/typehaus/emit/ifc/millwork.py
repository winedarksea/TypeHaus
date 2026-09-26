"""IFC products for resolved interior millwork."""

from __future__ import annotations

from typing import Any

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.model.ids import derive_guid
from typehaus.resolve.geometry_millwork import window_stool_prism
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
