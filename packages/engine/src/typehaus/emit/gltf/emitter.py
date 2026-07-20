"""glTF 2.0 binary writer over :class:`~typehaus.resolve.model.ResolvedModel` (#51).

No external dependency: geometry is built from the resolved layer polygons (already SI meters,
project-north frame) by vertical extrusion, and packed into a standard ``.glb`` container
(12-byte header + JSON chunk + BIN chunk). glTF is Y-up; our plan frame is (x east, y north,
z up), so we map model ``(x, y, z) → glTF (x, z, -y)`` once, here.

Triangles are grouped into materials by a small function-based palette so the massing reads
(sheathing gray, insulation amber, framing brown, floors muted). One mesh, one primitive per
color, one node — enough for the 3D panel and the agent-eyes snapshot.
"""

from __future__ import annotations

import base64
import json
import struct
from pathlib import Path

from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof, ResolvedWall

# function/category → RGBA color (linear, 0..1). Keys are lowercased layer functions and
# member categories; anything unmatched falls back to a neutral gray.
_PALETTE: dict[str, tuple[float, float, float, float]] = {
    "structure": (0.62, 0.45, 0.28, 1.0),
    "insulation": (0.93, 0.74, 0.36, 1.0),
    "sheathing": (0.72, 0.72, 0.70, 1.0),
    "cladding": (0.55, 0.58, 0.60, 1.0),
    "lining": (0.90, 0.89, 0.86, 1.0),
    "finish": (0.90, 0.89, 0.86, 1.0),
    "membrane": (0.30, 0.45, 0.55, 1.0),
    "air_gap": (0.80, 0.85, 0.90, 0.35),
    "furring": (0.68, 0.52, 0.34, 1.0),
    # framing member categories
    "stud": (0.70, 0.52, 0.33, 1.0),
    "plate": (0.66, 0.48, 0.30, 1.0),
    "header": (0.60, 0.42, 0.26, 1.0),
    "raked_plate": (0.66, 0.48, 0.30, 1.0),
    "corner": (0.64, 0.46, 0.29, 1.0),
    "stringer": (0.60, 0.42, 0.26, 1.0),
    "tread": (0.70, 0.52, 0.33, 1.0),
    "joist": (0.72, 0.55, 0.36, 1.0),
    "rim": (0.66, 0.48, 0.30, 1.0),
    "ridge_beam": (0.55, 0.38, 0.22, 1.0),
    "floor": (0.82, 0.80, 0.76, 1.0),
    "roof": (0.35, 0.37, 0.40, 1.0),
    "slab": (0.55, 0.56, 0.57, 1.0),
    "footing": (0.48, 0.49, 0.50, 1.0),
    "pad": (0.50, 0.51, 0.52, 1.0),
    "furniture": (0.46, 0.31, 0.20, 1.0),
}
_FALLBACK = (0.70, 0.70, 0.70, 1.0)

Vec3 = tuple[float, float, float]


class _MeshBuilder:
    """Accumulates triangles bucketed by color; emits interleaved position + index buffers."""

    def __init__(self) -> None:
        # color -> (positions: list[Vec3], indices: list[int])
        self._buckets: dict[tuple[float, float, float, float],
                            tuple[list[Vec3], list[int]]] = {}

    def _bucket(self, color: tuple[float, float, float, float]):
        return self._buckets.setdefault(color, ([], []))

    def add_prism(self, ring: list[tuple[float, float]], z0: float, z1: float,
                  color: tuple[float, float, float, float]) -> None:
        """Extrude a plan polygon ring between z0 and z1 into a closed solid."""
        ring = _dedupe_ring(ring)
        if len(ring) < 3:
            return
        positions, indices = self._bucket(color)
        base = len(positions)
        n = len(ring)
        for (x, y) in ring:  # bottom loop then top loop
            positions.append(_to_gltf(x, y, z0))
        for (x, y) in ring:
            positions.append(_to_gltf(x, y, z1))
        # side walls
        for i in range(n):
            j = (i + 1) % n
            b0, b1, t0, t1 = base + i, base + j, base + n + i, base + n + j
            indices += [b0, b1, t1, b0, t1, t0]
        # caps via fan triangulation (rings are convex-ish quads in practice)
        for i in range(1, n - 1):
            indices += [base, base + i + 1, base + i]                 # bottom (down)
            indices += [base + n, base + n + i, base + n + i + 1]     # top (up)

    def add_box(self, p0: Vec3, p1: Vec3, size: float,
                color: tuple[float, float, float, float]) -> None:
        """A member segment as a box of half-width ``size`` around the p0→p1 axis (xy)."""
        (ax, ay, az), (bx, by, bz) = p0, p1
        dx, dy = bx - ax, by - ay
        length = (dx * dx + dy * dy) ** 0.5
        if length == 0:
            return
        nx, ny = -dy / length * size, dx / length * size
        ring = [(ax + nx, ay + ny), (bx + nx, by + ny),
                (bx - nx, by - ny), (ax - nx, ay - ny)]
        self.add_prism(ring, az, bz, color)

    def add_member_box(self, p0: Vec3, p1: Vec3, half_width: float,
                       color: tuple[float, float, float, float],
                       z0_end: float | None = None, z1_end: float | None = None) -> None:
        """Add a real 3D member, including vertical studs and sloped top plates."""
        ax, ay, az0 = p0
        bx, by, az1 = p1
        lower_end = az0 if z0_end is None else z0_end
        upper_end = az1 if z1_end is None else z1_end
        dx, dy = bx - ax, by - ay
        run = (dx * dx + dy * dy) ** 0.5
        if run < 1e-9:
            ring = [(ax - half_width, ay - half_width), (ax + half_width, ay - half_width),
                    (ax + half_width, ay + half_width), (ax - half_width, ay + half_width)]
            self.add_prism(ring, az0, az1, color)
            return
        nx, ny = -dy / run * half_width, dx / run * half_width
        plan_vertices = [
            (ax + nx, ay + ny, az0), (bx + nx, by + ny, lower_end),
            (bx - nx, by - ny, lower_end), (ax - nx, ay - ny, az0),
            (ax + nx, ay + ny, az1), (bx + nx, by + ny, upper_end),
            (bx - nx, by - ny, upper_end), (ax - nx, ay - ny, az1),
        ]
        positions, indices = self._bucket(color)
        base = len(positions)
        positions.extend(_to_gltf(*point) for point in plan_vertices)
        for face in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
                     (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            a, b, c, d = (base + index for index in face)
            indices.extend((a, b, c, a, c, d))

    def add_triangles(self, triangles: list[tuple[Vec3, Vec3, Vec3]],
                      color: tuple[float, float, float, float]) -> None:
        positions, indices = self._bucket(color)
        for triangle in triangles:
            base = len(positions)
            positions.extend(triangle)
            indices.extend((base, base + 1, base + 2))

    def is_empty(self) -> bool:
        return not any(pos for pos, _ in self._buckets.values())

    def build(self) -> dict:
        """Assemble the glTF dict + embedded base64 buffer for all buckets."""
        blob = bytearray()
        buffer_views: list[dict] = []
        accessors: list[dict] = []
        materials: list[dict] = []
        primitives: list[dict] = []

        for color, (positions, indices) in self._buckets.items():
            if not positions:
                continue
            pos_acc = _append_positions(blob, buffer_views, accessors, positions)
            idx_acc = _append_indices(blob, buffer_views, accessors, indices)
            mat = len(materials)
            materials.append({
                "pbrMetallicRoughness": {
                    "baseColorFactor": list(color), "metallicFactor": 0.0,
                    "roughnessFactor": 0.9,
                },
                "alphaMode": "BLEND" if color[3] < 1.0 else "OPAQUE",
                "doubleSided": True,
            })
            primitives.append({
                "attributes": {"POSITION": pos_acc}, "indices": idx_acc, "material": mat,
            })

        uri = "data:application/octet-stream;base64," + base64.b64encode(bytes(blob)).decode()
        return {
            "asset": {"version": "2.0", "generator": "typehaus"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0, "name": "building"}],
            "meshes": [{"primitives": primitives}],
            "materials": materials,
            "accessors": accessors,
            "bufferViews": buffer_views,
            "buffers": [{"byteLength": len(blob), "uri": uri}],
        }, bytes(blob)


def _append_positions(blob: bytearray, views: list[dict], accessors: list[dict],
                      positions: list[Vec3]) -> int:
    _align(blob)
    offset = len(blob)
    for (x, y, z) in positions:
        blob += struct.pack("<fff", x, y, z)
    views.append({"buffer": 0, "byteOffset": offset,
                  "byteLength": len(positions) * 12, "target": 34962})
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    zs = [p[2] for p in positions]
    accessors.append({
        "bufferView": len(views) - 1, "componentType": 5126, "count": len(positions),
        "type": "VEC3", "min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)],
    })
    return len(accessors) - 1


def _append_indices(blob: bytearray, views: list[dict], accessors: list[dict],
                    indices: list[int]) -> int:
    _align(blob)
    offset = len(blob)
    for i in indices:
        blob += struct.pack("<I", i)
    views.append({"buffer": 0, "byteOffset": offset,
                  "byteLength": len(indices) * 4, "target": 34963})
    accessors.append({
        "bufferView": len(views) - 1, "componentType": 5125, "count": len(indices),
        "type": "SCALAR",
    })
    return len(accessors) - 1


def _align(blob: bytearray, boundary: int = 4) -> None:
    while len(blob) % boundary:
        blob.append(0)


def _to_gltf(x: float, y: float, z: float) -> Vec3:
    return (x, z, -y)  # (x east, y north, z up) → glTF Y-up


def _dedupe_ring(ring: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for pt in ring:
        if not out or (abs(pt[0] - out[-1][0]) > 1e-9 or abs(pt[1] - out[-1][1]) > 1e-9):
            out.append(pt)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    return out


def _color(key: str) -> tuple[float, float, float, float]:
    return _PALETTE.get(key.lower(), _FALLBACK)


def _add_wall(mb: _MeshBuilder, wall: ResolvedWall, lod: str) -> None:
    if lod == "framed" and wall.members:
        for member in wall.members:
            _add_member(mb, member)
        return
    for layer in wall.layers:
        if layer.polygon:
            mb.add_prism(layer.polygon, wall.z0_m, wall.z1_m, _color(layer.function))


def _add_envelope_band(mb: _MeshBuilder, band) -> None:
    for layer in band.layers:
        if layer.polygon:
            mb.add_prism(layer.polygon, band.z0_m, band.z1_m, _color(layer.function))


def _add_member(mb: _MeshBuilder, member: FramedMember) -> None:
    half = _member_half_width(member.profile)
    mb.add_member_box(
        (member.p0[0], member.p0[1], member.z0_m),
        (member.p1[0], member.p1[1], member.z1_m), half, _color(member.category),
        z0_end=member.z0_end_m, z1_end=member.z1_end_m,
    )


def _add_roof(mb: _MeshBuilder, roof: ResolvedRoof) -> None:
    """Render the resolved gable/shed planes rather than a misleading flat prism."""
    (minx, miny), (maxx, _), (_, maxy), _ = roof.footprint
    eave, ridge = roof.eave_z_m, roof.ridge_z_m
    if roof.ridge_direction == "x":
        mid = (miny + maxy) / 2
        ridge_a, ridge_b = (minx, mid, ridge), (maxx, mid, ridge)
        triangles = [
            ((minx, miny, eave), (maxx, miny, eave), ridge_b),
            ((minx, miny, eave), ridge_b, ridge_a),
            (ridge_a, ridge_b, (maxx, maxy, eave)),
            (ridge_a, (maxx, maxy, eave), (minx, maxy, eave)),
        ]
    else:
        mid = (minx + maxx) / 2
        ridge_a, ridge_b = (mid, miny, ridge), (mid, maxy, ridge)
        triangles = [
            ((minx, miny, eave), ridge_a, ridge_b),
            ((minx, miny, eave), ridge_b, (minx, maxy, eave)),
            (ridge_a, (maxx, miny, eave), (maxx, maxy, eave)),
            (ridge_a, (maxx, maxy, eave), ridge_b),
        ]
    if roof.form == "shed":
        if roof.ridge_direction == "x":
            triangles = [((minx, miny, eave), (maxx, miny, eave), (maxx, maxy, ridge)),
                         ((minx, miny, eave), (maxx, maxy, ridge), (minx, maxy, ridge))]
        else:
            triangles = [((minx, miny, eave), (maxx, miny, ridge), (maxx, maxy, ridge)),
                         ((minx, miny, eave), (maxx, maxy, ridge), (minx, maxy, eave))]
    mb.add_triangles([tuple(_to_gltf(*point) for point in triangle) for triangle in triangles],
                     _color("roof"))
    for member in roof.members:
        _add_member(mb, member)


def _add_furniture(mb: _MeshBuilder, model: ResolvedModel) -> None:
    """Add imported GLB geometry when available, with a truthful footprint fallback."""
    types = {item.tag: item for item in model.plan.library.furniture_types}
    root = Path(model.plan.source_root or ".")
    for storey in model.plan.storeys:
        z0 = storey.elevation.meters
        for item in model.plan.storey_elements(storey.tag):
            if item.element_kind != "Furniture":
                continue
            furniture_type = types.get(item.type_ref)
            if furniture_type is None:
                continue
            if furniture_type.mesh is not None and _add_mesh_sidecar(
                mb, root / furniture_type.mesh.path, item.position.xy_m, z0
            ):
                continue
            _add_furniture_box(mb, item.position.xy_m, z0, furniture_type)


def _add_mesh_sidecar(mb: _MeshBuilder, path: Path, position: tuple[float, float], z0: float) -> bool:
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


def _add_furniture_box(mb: _MeshBuilder, position: tuple[float, float], z0: float, furniture_type) -> None:
    width, depth = (value.meters for value in furniture_type.footprint)
    x, y = position
    mb.add_prism([(x - width / 2, y - depth / 2), (x + width / 2, y - depth / 2),
                  (x + width / 2, y + depth / 2), (x - width / 2, y + depth / 2)],
                 z0, z0 + furniture_type.height.meters, _color("furniture"))


def _member_half_width(profile: str) -> float:
    # "2x6" → nominal 1.5" actual thickness; half of that in meters.
    try:
        nominal = float(profile.lower().split("x")[0])
    except (ValueError, IndexError):
        nominal = 2.0
    actual_in = max(nominal - 0.5, 0.75)
    return actual_in * 0.0254 / 2.0


def emit_gltf_dict(model: ResolvedModel, lod: str = "core") -> tuple[dict, bytes]:
    """Build the glTF JSON dict + binary blob for ``model`` (no file written)."""
    mb = _MeshBuilder()
    for wall in sorted(model.walls, key=lambda w: w.uid):
        _add_wall(mb, wall, lod)
    for band in sorted(model.envelope_bands, key=lambda item: item.uid):
        _add_envelope_band(mb, band)
    for room in sorted(model.rooms, key=lambda r: r.uid):
        if room.clear_face:
            storey_z = _room_z(model, room.storey)
            mb.add_prism(room.clear_face, storey_z, storey_z + 0.02, _color("floor"))
    for solid in sorted(model.solids, key=lambda item: item.uid):
        if solid.outline:
            mb.add_prism(solid.outline, solid.z0_m, solid.z1_m, _color(solid.category))
    for roof in sorted(model.roofs, key=lambda item: item.uid):
        _add_roof(mb, roof)
    for stair in sorted(model.stairs, key=lambda item: item.uid):
        for member in stair.members:
            _add_member(mb, member)
    _add_furniture(mb, model)
    if mb.is_empty():  # keep the container valid even for an empty model
        mb.add_prism([(0, 0), (0.001, 0), (0.001, 0.001)], 0.0, 0.001, _FALLBACK)
    return mb.build()


def _room_z(model: ResolvedModel, storey_tag: str) -> float:
    for w in model.walls:
        if w.storey == storey_tag:
            return w.z0_m
    return 0.0


def emit_glb(model: ResolvedModel, out_path: Path, lod: str = "core") -> Path:
    """Write a binary glTF (``.glb``) file for ``model``. Returns the path."""
    gltf, blob = emit_gltf_dict(model, lod)
    # In a .glb the single buffer is the BIN chunk — it must not also carry a data URI.
    gltf["buffers"][0].pop("uri", None)
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode()
    json_bytes += b" " * ((4 - len(json_bytes) % 4) % 4)  # pad to 4 with spaces
    bin_pad = b"\x00" * ((4 - len(blob) % 4) % 4)
    bin_chunk = blob + bin_pad
    total = 12 + 8 + len(json_bytes) + 8 + len(bin_chunk)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, total))          # "glTF", version, length
        fh.write(struct.pack("<II", len(json_bytes), 0x4E4F534A))    # JSON chunk header
        fh.write(json_bytes)
        fh.write(struct.pack("<II", len(bin_chunk), 0x004E4942))     # BIN chunk header
        fh.write(bin_chunk)
    return out_path
