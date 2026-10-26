"""Finish-specific glTF nodes retain their wall identity and siding visibility."""

from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _layer_color, _material_finish_color
from typehaus.emit.trade_rules import layer_trade

PAINTED_METAL_SURFACE = (0.45, 0.05)  # roughness, metallic factor; PVDF is a dielectric paint


def add_profiled_wall_surfaces(scene, wall, closures, authored, lod):
    items = []
    if not (lod == "framed" and wall.members):
        for layer in wall.body_layers():
            if layer.surface_mesh is not None:
                items.append(
                    (
                        layer.surface_mesh,
                        _layer_color(layer, authored),
                        layer_trade(layer.function, "wall", layer.material_ref),
                        layer.material_ref,
                    )
                )
    for member in closures:
        if member.surface_mesh is not None:
            items.append(
                (
                    member.surface_mesh,
                    _material_finish_color(member.material, member.category, authored),
                    "siding",
                    member.material,
                )
            )
    for mesh, color, trade, ref in items:
        builder = _MeshBuilder()
        builder.add_mesh(mesh, color)
        scene.add_object(
            builder,
            (trade,),
            kind="wall",
            uid=wall.uid,
            material_ref=ref,
            category="cladding",
            material_surfaces={color: PAINTED_METAL_SURFACE},
        )
