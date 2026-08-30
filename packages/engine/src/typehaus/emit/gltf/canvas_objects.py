"""Canvas objects (furniture, fixtures, appliances, equipment): a placeable's parts, an
imported .glb sidecar, or a plain massing box, routed to the trade its domain belongs to."""

from __future__ import annotations

from pathlib import Path

from typehaus.emit.gltf.geometry import _to_gltf
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _color
from typehaus.emit.gltf.scene import _SceneBuilder
from typehaus.model.canvas import canvas_object_types
from typehaus.model.placeable_symbols import PART_COLORS, lamp_role, model_parts, place_local
from typehaus.resolve.model import ResolvedCanvasObject, ResolvedModel

_CANVAS_TRADES = {"plumbing": "plumbing", "electrical": "electrical", "mechanical": "mechanical"}


def _canvas_trade(domain: str) -> str:
    """Route a resolved canvas object to its visibility trade, mirroring Panel3D.setModel:
    plumbing/electrical/mechanical keep their discipline; everything else (furniture,
    appliances, ...) lands in the furniture trade."""
    return _CANVAS_TRADES.get(domain, "furniture")


_PLACEABLE_TYPE_COLLECTIONS = ("furniture_types", "fixture_types", "appliance_types",
                               "equipment_types", "register_types", "electrical_device_types")


def _add_canvas_objects(scene: _SceneBuilder, model: ResolvedModel) -> None:
    """Emit one node per ResolvedCanvasObject (furniture, fixtures, MEP devices).

    Precedence, highest first: an imported GLB sidecar keeps its mesh; a type naming a
    ``plan_symbol`` emits its generated multi-part massing (``_MeshBuilder`` already buckets
    triangles by colour, so several materials fall out of one node for free); everything else
    extrudes its resolved footprint to the type's height, matching Panel3D's fallback box.
    ``domain=="opening"`` objects are skipped — they are already drawn as wall cuts +
    fillings — so they never produce an unclassifiable node.
    """
    types = {item.tag: item for name in _PLACEABLE_TYPE_COLLECTIONS
             for item in getattr(model.plan.library, name)}
    heights = {t["tag"]: t.get("height_m") for t in canvas_object_types(model.plan)}
    root = Path(model.plan.source_root or ".")
    for item in sorted(model.canvas_objects, key=lambda co: co.uid):
        if item.domain == "opening":
            continue
        mb = _MeshBuilder()
        product_type = types.get(item.type_ref)
        drawn = False
        if product_type is not None and getattr(product_type, "mesh", None) is not None:
            drawn = _add_mesh_sidecar(mb, root / product_type.mesh.path, item.position, item.z_m)
        if not drawn:
            drawn = _add_canvas_parts(mb, item, product_type)
        if not drawn:
            _add_canvas_box(mb, item, heights.get(item.type_ref))
        scene.add_object(mb, trade=_canvas_trade(item.domain),
                         kind="canvas_object", uid=item.uid)


def _add_mesh_sidecar(mb: _MeshBuilder, path: Path, position: tuple[float, float],
                      z0: float) -> bool:
    try:
        import trimesh

        loaded = trimesh.load(path, force="mesh")
        mesh = loaded.dump(concatenate=True) if isinstance(loaded, trimesh.Scene) else loaded
        vertices, faces = mesh.vertices, mesh.faces
        if len(vertices) == 0 or len(faces) == 0:
            return False
        minimum = vertices.min(axis=0)
        maximum = vertices.max(axis=0)
        center_x = (minimum[0] + maximum[0]) / 2
        center_y = (minimum[1] + maximum[1]) / 2
        triangles = [
            tuple(_to_gltf(float(vertices[index][0] - center_x + position[0]),
                           float(vertices[index][1] - center_y + position[1]),
                           float(vertices[index][2] - minimum[2] + z0)) for index in face)
            for face in faces
        ]
        mb.add_triangles(triangles, _color("furniture"))
        return True
    except (ImportError, OSError, ValueError, AttributeError):
        return False


def _add_canvas_parts(mb: _MeshBuilder, item: ResolvedCanvasObject,
                      product_type: object | None) -> bool:
    """Extrude a type's generated massing parts, one prism each. False when it has no symbol.

    The parts are in the symbol's **local** frame: the resolver bakes rotation into
    ``footprint`` but not into symbol geometry, so each box ring goes through the same
    ``place_local`` the canvas and the sheet writers use. Colours come from ``PART_COLORS``
    directly — the viewer reads the hex the serializer derives from those same numbers, so
    the two cannot disagree.
    """
    symbol = getattr(product_type, "plan_symbol", None)
    footprint = getattr(product_type, "footprint", None)
    height = getattr(product_type, "height", None)
    if symbol is None or footprint is None or height is None:
        return False
    width_m, depth_m = (part.meters for part in footprint)
    parts = model_parts(symbol, width_m, depth_m, height.meters)
    # Mirrors model/canvas._lamp: the generic ``lamp`` role becomes the type's CCT bin, so
    # a 4000K can exports the same shade the viewer draws.
    lamp = lamp_role(getattr(product_type, "cct_k", None))
    for part in parts:
        (cx, cy, cz), (sx, sy, sz) = part["center"], part["size"]
        ring = [(cx - sx / 2, cy - sy / 2), (cx + sx / 2, cy - sy / 2),
                (cx + sx / 2, cy + sy / 2), (cx - sx / 2, cy + sy / 2)]
        mb.add_prism(place_local(ring, item.position, item.rotation_degrees),
                     item.z_m + cz - sz / 2, item.z_m + cz + sz / 2,
                     PART_COLORS[lamp if part["color"] == "lamp" else part["color"]])
    return bool(parts)


def _add_canvas_box(mb: _MeshBuilder, item: ResolvedCanvasObject, height_m: float | None) -> None:
    """Extrude a canvas object's resolved footprint into a box (Panel3D's fallback shape)."""
    ring = [tuple(point) for point in item.footprint]
    if len(ring) < 3:
        return
    height = height_m if height_m else 0.25  # Panel3D uses type.height_m ?? 0.25
    mb.add_prism(ring, item.z_m, item.z_m + height, _color("furniture"))
