"""Canvas objects (furniture, fixtures, appliances, equipment): a placeable's parts, an
imported .glb sidecar, or a plain massing box, routed to the trade its domain belongs to."""

from __future__ import annotations

import math
from pathlib import Path

from typehaus.emit.gltf.geometry import _to_gltf
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _color, _hex_rgba, _material_finish_color
from typehaus.emit.gltf.scene import _SceneBuilder
from typehaus.emit.gltf.triangulate import polygon_parts
from typehaus.emit.trade_rules import CANVAS_DOMAIN_TRADE
from typehaus.model.built_in_bookcase import built_in_bookcase_parts
from typehaus.model.canvas import canvas_object_types, model_symbol_for, wood_material
from typehaus.model.placeable_symbols import PART_COLORS, lamp_role, model_parts, place_local
from typehaus.resolve.geometry_countertops import countertop_prisms, slab_hosts
from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.model import ResolvedCanvasObject, ResolvedModel
from typehaus.resolve.suspension import suspension_draw


def _canvas_trade(domain: str) -> str:
    """Route a resolved canvas object to its viewer trade by domain (→ emit/trade_rules)."""
    return CANVAS_DOMAIN_TRADE.get(domain, "furniture")


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
    materials = {m.tag: m for m in model.plan.library.materials}
    root = Path(model.plan.source_root or ".")
    hosted = slab_hosts(model)
    for item in sorted(model.canvas_objects, key=lambda co: co.uid):
        if item.domain == "opening":
            continue
        mb = _MeshBuilder()
        product_type = types.get(item.type_ref)
        drawn = False
        if product_type is not None and getattr(product_type, "mesh", None) is not None:
            drawn = _add_mesh_sidecar(mb, root / product_type.mesh.path, item.position, item.z_m)
        if not drawn:
            drawn = _add_canvas_parts(mb, item, product_type, materials,
                                      skip_counter=item.tag in hosted)
        if not drawn:
            _add_canvas_box(mb, item, heights.get(item.type_ref))
        _add_suspension(mb, item, product_type)
        scene.add_object(mb, (_canvas_trade(item.domain),),
                         kind="canvas_object", uid=item.uid)


def _add_countertops(scene: _SceneBuilder, model: ResolvedModel, authored: dict) -> None:
    """Each countertop slab in its own material, on the millwork trade (viewer parity).

    A slab has no selection kind of its own: it selects its first host, as a stool selects
    its window.
    """
    uids = {obj.tag: obj.uid for obj in model.canvas_objects}
    for top in sorted(model.countertops, key=lambda item: item.uid):
        mb = _MeshBuilder()
        color = _material_finish_color(top.material_ref, "millwork", authored)
        for prism in countertop_prisms(model, top):
            if prism.voids:
                mb.add_polygon_prism(polygon_parts(prism.ring, prism.voids),
                                     prism.z0_m, prism.z1_m, color)
            else:
                mb.add_prism(list(prism.ring), prism.z0_m, prism.z1_m, color)
        if not mb.is_empty() and top.hosts[0] in uids:
            scene.add_object(mb, ("millwork",), kind="canvas_object", uid=uids[top.hosts[0]])


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
                      product_type: object | None, materials: dict[str, object],
                      skip_counter: bool = False) -> bool:
    """Emit a type's generated massing parts. False when it has no symbol.

    The parts are in the symbol's **local** frame: the resolver bakes rotation into
    ``footprint`` but not into symbol geometry, so each box ring goes through the same
    ``place_local`` the canvas and the sheet writers use. Colours come from ``PART_COLORS``
    directly — the viewer reads the hex the serializer derives from those same numbers, so
    the two cannot disagree.
    """
    # A type naming its wood takes that material's authored colour on its ``wood`` parts,
    # exactly as model/canvas._wood_part hands the viewer.
    wood = wood_material(product_type, materials)
    wood_color = _hex_rgba(wood.color) if wood is not None else None
    bookcase = getattr(product_type, "built_in_bookcase", None)
    if bookcase is not None:
        for part in built_in_bookcase_parts(bookcase):
            mb.add_prism(place_local(part.outline, item.position, item.rotation_degrees),
                         item.z_m + part.z0_m, item.z_m + part.z1_m,
                         wood_color or _color("furniture"))
        return True
    symbol = model_symbol_for(product_type)
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
        if skip_counter and part["color"] == "counter":
            continue  # the countertop slab draws it (→ _add_countertops)
        (cx, cy, cz), (sx, sy, sz) = part["center"], part["size"]
        color = (wood_color if wood_color and part["color"] == "wood"
                 else PART_COLORS[lamp if part["color"] == "lamp" else part["color"]])
        if "mesh" in part:
            mesh = part["mesh"]
            placed = place_local([(x, y) for x, y, _ in mesh["positions"]],
                                 item.position, item.rotation_degrees)
            rotated_normals = place_local([(x, y) for x, y, _ in mesh["normals"]],
                                         (0.0, 0.0), item.rotation_degrees)
            mb.add_mesh(GMesh(
                positions=tuple((x, y, item.z_m + point[2])
                                for (x, y), point in zip(placed, mesh["positions"], strict=True)),
                triangles=mesh["triangles"],
                normals=tuple((x, y, normal[2]) for (x, y), normal in
                              zip(rotated_normals, mesh["normals"], strict=True)),
                curved_vertices=frozenset(range(len(mesh["positions"]))),
            ), color)
            continue
        if part["shape"] == "cylinder-depth":
            world_center = place_local([(cx, cy)], item.position, item.rotation_degrees)[0]
            angle = math.radians(item.rotation_degrees)
            mb.add_plan_depth_cylinder(
                (world_center[0], world_center[1], item.z_m + cz), sx / 2.0, sy,
                (-math.sin(angle), math.cos(angle)), color,
            )
            continue
        # A ringed part carries its own plan outline (a neo-angle pan is a pentagon); a box
        # part's ring is its bounding rectangle, which for a box is the same statement.
        ring = list(part["points"]) or [
            (cx - sx / 2, cy - sy / 2), (cx + sx / 2, cy - sy / 2),
            (cx + sx / 2, cy + sy / 2), (cx - sx / 2, cy + sy / 2)]
        mb.add_prism(place_local(ring, item.position, item.rotation_degrees),
                     item.z_m + cz - sz / 2, item.z_m + cz + sz / 2,
                     color)
    return bool(parts)


def _add_canvas_box(mb: _MeshBuilder, item: ResolvedCanvasObject, height_m: float | None) -> None:
    """Extrude a canvas object's resolved footprint into a box (Panel3D's fallback shape)."""
    ring = [tuple(point) for point in item.footprint]
    if len(ring) < 3:
        return
    height = height_m if height_m else 0.25  # Panel3D uses type.height_m ?? 0.25
    bottom = item.body_z0_m if item.body_z0_m is not None else item.z_m
    top = item.body_z1_m if item.body_z1_m is not None else bottom + height
    mb.add_prism(ring, bottom, top, _color("furniture"))


def _add_suspension(mb: _MeshBuilder, item: ResolvedCanvasObject,
                    product_type: object | None) -> None:
    """A hung body's cable up to its ceiling and the canopy there; the viewer draws the same."""
    draw = suspension_draw(item, product_type)
    if draw is None:
        return
    x, y = item.position

    def square(side: float) -> list[tuple[float, float]]:
        h = side / 2
        return [(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)]

    mb.add_prism(square(draw.cable_m), draw.z0_m, draw.z1_m, PART_COLORS["metal"])
    mb.add_prism(square(draw.canopy_m), draw.z1_m - draw.canopy_thickness_m, draw.z1_m,
                 PART_COLORS["metal"])
