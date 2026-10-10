"""Derived interior trim in the GLB: base runs and door casings (viewer parity).

The same prisms the viewer draws (``resolve/geometry_millwork``), on the millwork trade. A
base run selects as its room and a casing as its door, as in ``builders/millwork.ts``.
"""

from __future__ import annotations

from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _material_finish_color
from typehaus.emit.gltf.scene import _SceneBuilder
from typehaus.resolve.geometry_millwork import base_run_prisms, door_casing_prisms
from typehaus.resolve.model import ResolvedModel


def _add_interior_trim(scene: _SceneBuilder, model: ResolvedModel, authored: dict) -> None:
    room_uids = {room.tag: room.uid for room in model.rooms}
    for run in sorted(model.base_runs, key=lambda item: item.uid):
        prisms = base_run_prisms(run)
        if not prisms or run.room not in room_uids:
            continue
        mb = _MeshBuilder()
        color = _material_finish_color(run.material_ref, "millwork", authored)
        for prism in prisms:
            mb.add_prism(list(prism.ring), prism.z0_m, prism.z1_m, color)
        scene.add_object(mb, ("millwork",), kind="room", uid=room_uids[run.room])
    for casing in sorted(model.door_casings, key=lambda item: item.uid):
        prisms = door_casing_prisms(casing)
        if not prisms:
            continue
        mb = _MeshBuilder()
        color = _material_finish_color(casing.material_ref, "millwork", authored)
        for prism in prisms:
            mb.add_prism(list(prism.ring), prism.z0_m, prism.z1_m, color)
        scene.add_object(mb, ("millwork",), kind="opening", uid=casing.opening_uid)
