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
import math
import struct
from pathlib import Path

from typehaus.emit.draw.palette import material_color
from typehaus.model.canvas import canvas_object_types
from typehaus.resolve.model import (
    FramedMember,
    ResolvedCanvasObject,
    ResolvedModel,
    ResolvedRoof,
    ResolvedWall,
)

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
    # roof truss members + the birdsmouth seat cut
    "top_chord": (0.70, 0.52, 0.33, 1.0),
    "bottom_chord": (0.66, 0.48, 0.30, 1.0),
    "truss_web": (0.74, 0.57, 0.38, 1.0),
    "truss_heel": (0.60, 0.42, 0.26, 1.0),
    "seat_cut": (0.58, 0.40, 0.24, 1.0),
    "floor": (0.82, 0.80, 0.76, 1.0),
    "roof": (0.35, 0.37, 0.40, 1.0),
    "slab": (0.55, 0.56, 0.57, 1.0),
    "footing": (0.48, 0.49, 0.50, 1.0),
    "pad": (0.50, 0.51, 0.52, 1.0),
    "column": (0.60, 0.60, 0.62, 1.0),  # concrete/wood posts (sonotube, 6x6 pillars)
    "beam": (0.62, 0.46, 0.28, 1.0),  # PT / built-up wood beams
    "furniture": (0.46, 0.31, 0.20, 1.0),
    # opening fillings — frame/leaf/panel read as wood; glazing is translucent blue-grey
    # (0x8fb7c9 @ 0.48), matching ui/src/components/Panel3D.tsx buildOpening.
    "opening_frame": (0.60, 0.42, 0.26, 1.0),
    "glass": (0.561, 0.718, 0.788, 0.48),
    # accessories (→ resolve/accessories.py)
    "railing": (0.80, 0.81, 0.83, 1.0),   # aluminum guard
    "dowel": (0.20, 0.55, 0.35, 1.0),     # GFRP rebar (green)
    "thermal_break": (0.95, 0.55, 0.15, 1.0),  # XPS foam block (orange)
    "connector": (0.35, 0.36, 0.38, 1.0),  # galvanized hardware
    "sump": (0.30, 0.32, 0.34, 1.0),       # pit
    "vent": (0.88, 0.88, 0.86, 1.0),       # painted vent pipe
    "fascia": (0.92, 0.92, 0.90, 1.0),     # PVC fascia
    "gutter": (0.85, 0.86, 0.87, 1.0),     # metal gutter
    "flashing": (0.75, 0.77, 0.80, 1.0),   # metal flashing
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

    def add_prism_with_rectangular_voids(self, ring: list[tuple[float, float]],
                                         voids: tuple[tuple[tuple[float, float], ...], ...],
                                         z0: float, z1: float,
                                         color: tuple[float, float, float, float]) -> None:
        """Emit a rectangular slab as strips around rectangular voids.

        The floor-opening framing contract currently accepts orthogonal rectangles, so
        this produces a true hole without introducing a second polygon triangulator.
        Irregular solids intentionally retain their outer prism until they gain a general
        mesh path.
        """
        xs, ys = {p[0] for p in ring}, {p[1] for p in ring}
        if len(xs) != 2 or len(ys) != 2 or len(voids) != 1:
            self.add_prism(ring, z0, z1, color)
            return
        hole = voids[0]
        hx, hy = {p[0] for p in hole}, {p[1] for p in hole}
        if len(hx) != 2 or len(hy) != 2:
            self.add_prism(ring, z0, z1, color)
            return
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        hminx, hmaxx, hminy, hmaxy = min(hx), max(hx), min(hy), max(hy)
        for rect in (
            [(minx, miny), (maxx, miny), (maxx, hminy), (minx, hminy)],
            [(minx, hmaxy), (maxx, hmaxy), (maxx, maxy), (minx, maxy)],
            [(minx, hminy), (hminx, hminy), (hminx, hmaxy), (minx, hmaxy)],
            [(hmaxx, hminy), (maxx, hminy), (maxx, hmaxy), (hmaxx, hmaxy)],
        ):
            self.add_prism(rect, z0, z1, color)

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

    def add_arched_spandrel(self, edges, opening_start: float, opening_end: float,
                            z1: float, springline: float, radius: float,
                            color: tuple[float, float, float, float]) -> None:
        """Add one continuous curved concrete head, not a stack of prism strips."""
        positions, indices = self._bucket(color)
        base = len(positions)
        for segment in range(_ARCH_CURVE_SEGMENTS + 1):
            fraction = opening_start + (
                (opening_end - opening_start) * segment / _ARCH_CURVE_SEGMENTS
            )
            offset = ((segment / _ARCH_CURVE_SEGMENTS) - 0.5) * radius * 2.0
            soffit = min(z1, springline + math.sqrt(max(0.0, radius * radius - offset * offset)))
            front = _lerp(edges[0][0], edges[0][1], fraction)
            back = _lerp(edges[1][0], edges[1][1], fraction)
            positions.extend((_to_gltf(*front, soffit), _to_gltf(*back, soffit),
                              _to_gltf(*front, z1), _to_gltf(*back, z1)))
        for segment in range(_ARCH_CURVE_SEGMENTS):
            current, next_ = base + segment * 4, base + (segment + 1) * 4
            # Curved soffit and flat top.
            indices.extend((current, next_ + 1, next_, current, current + 1, next_ + 1))
            indices.extend((current + 2, next_ + 2, next_ + 3,
                            current + 2, next_ + 3, current + 3))
            # The two wall-depth faces are continuous across the full arch.
            indices.extend((current, next_, next_ + 2, current, next_ + 2, current + 2,
                            current + 1, current + 3, next_ + 3, current + 1, next_ + 3, next_ + 1))
        # Close the jamb faces at each springline.
        for section in (base, base + _ARCH_CURVE_SEGMENTS * 4):
            indices.extend((section, section + 2, section + 3, section, section + 3, section + 1))

    def is_empty(self) -> bool:
        return not any(pos for pos, _ in self._buckets.values())

    def buckets(self):
        """Non-empty (color, positions, indices) tuples for the scene assembler."""
        for color, (positions, indices) in self._buckets.items():
            if positions:
                yield color, positions, indices


class _SceneBuilder:
    """Assembles per-object glTF nodes into one document + shared binary buffer.

    Each source object contributes its own :class:`_MeshBuilder` (color-bucketed within that
    object) and becomes exactly one glTF node carrying ``extras`` (and a ``<trade>|<kind>|<uid>``
    name) so the 3D UI can promote the whole-house glb to the primary scene (see the emitter
    contract in ``ui/src/components/Panel3D.tsx``). Materials are deduplicated by color across
    every object, so the palette stays compact.
    """

    def __init__(self) -> None:
        self._blob = bytearray()
        self._buffer_views: list[dict] = []
        self._accessors: list[dict] = []
        self._materials: list[dict] = []
        self._material_index: dict[tuple[float, float, float, float], int] = {}
        self._meshes: list[dict] = []
        self._nodes: list[dict] = []

    def _material(self, color: tuple[float, float, float, float]) -> int:
        index = self._material_index.get(color)
        if index is None:
            index = len(self._materials)
            self._material_index[color] = index
            self._materials.append({
                "pbrMetallicRoughness": {
                    "baseColorFactor": list(color), "metallicFactor": 0.0,
                    "roughnessFactor": 0.9,
                },
                "alphaMode": "BLEND" if color[3] < 1.0 else "OPAQUE",
                "doubleSided": True,
            })
        return index

    def add_object(self, mb: "_MeshBuilder", trade: str,
                   kind: str | None = None, uid: str | None = None) -> None:
        """Emit one node for ``mb``'s geometry, tagged so the UI can classify it by trade.

        ``kind`` is only ever ``"wall"`` or ``"canvas_object"`` (the selectable kinds the UI
        honours); ``uid`` is only carried for those selectable nodes. Envelope geometry passes
        neither, so it lands in the right visibility group without becoming pickable. A node with
        no geometry is skipped entirely, so it can never become an unclassifiable renderable mesh.
        """
        primitives: list[dict] = []
        for color, positions, indices in mb.buckets():
            pos_acc = _append_positions(self._blob, self._buffer_views, self._accessors, positions)
            idx_acc = _append_indices(self._blob, self._buffer_views, self._accessors, indices)
            primitives.append({
                "attributes": {"POSITION": pos_acc}, "indices": idx_acc,
                "material": self._material(color),
            })
        if not primitives:
            return
        mesh_index = len(self._meshes)
        self._meshes.append({"primitives": primitives})
        extras: dict[str, str] = {"trade": trade}
        if kind is not None:
            extras["kind"] = kind
        if uid is not None:
            extras["uid"] = uid
        # A "<trade>|<kind|>|<uid|>" name is a belt-and-suspenders fallback; extras is primary.
        name = "|".join((trade, kind or "", uid or ""))
        self._nodes.append({"mesh": mesh_index, "name": name, "extras": extras})

    def is_empty(self) -> bool:
        return not self._nodes

    def build(self) -> tuple[dict, bytes]:
        """Assemble the glTF dict + embedded base64 buffer across all objects."""
        uri = "data:application/octet-stream;base64," + base64.b64encode(bytes(self._blob)).decode()
        return {
            "asset": {"version": "2.0", "generator": "typehaus"},
            "scene": 0,
            "scenes": [{"nodes": list(range(len(self._nodes)))}],
            "nodes": self._nodes,
            "meshes": self._meshes,
            "materials": self._materials,
            "accessors": self._accessors,
            "bufferViews": self._buffer_views,
            "buffers": [{"byteLength": len(self._blob), "uri": uri}],
        }, bytes(self._blob)


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


def _hex_rgba(hex_str: str) -> tuple[float, float, float, float]:
    h = hex_str.lstrip("#")
    if len(h) == 6:
        return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, 1.0)
    return _FALLBACK


def _solid_color(model: ResolvedModel, solid) -> tuple[float, float, float, float]:
    """A solid with an authored assembly (e.g. a composite/aluminum deck) reads with its
    material colour; otherwise it falls back to the per-category palette."""
    if solid.assembly:
        assembly = model.plan.library.resolve_assembly(solid.assembly)
        if assembly is not None and assembly.layers:
            idx = assembly.structure_index()
            layer = assembly.layers[idx if idx is not None else 0]
            material = next((m for m in model.plan.library.materials
                             if m.tag == layer.material_ref), None)
            if material is not None:
                return _hex_rgba(material_color(material.hatch, material.color))
    return _color(solid.category)


_ARCH_CURVE_SEGMENTS = 64  # smooth tessellation for the single curved arch mesh


def _thin_rect_edges(poly, axis):
    """The two long edges of a wall layer's thin-rectangle footprint, each oriented
    start→end along the wall axis, so a fractional slice maps to along-axis position."""
    (p0x, p0y), (p1x, p1y) = axis
    tx, ty = p1x - p0x, p1y - p0y
    length = math.hypot(tx, ty) or 1.0
    tx, ty = tx / length, ty / length
    nx, ny = -ty, tx
    along = lambda v: (v[0] - p0x) * tx + (v[1] - p0y) * ty
    perp = lambda v: (v[0] - p0x) * nx + (v[1] - p0y) * ny
    ordered = sorted(poly, key=along)
    starts = sorted(ordered[:2], key=perp)
    ends = sorted(ordered[2:], key=perp)
    return (starts[0], ends[0]), (starts[1], ends[1])


def _lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def _slice(edges, t0, t1):
    (a0, a1), (b0, b1) = edges
    return [_lerp(a0, a1, t0), _lerp(a0, a1, t1), _lerp(b0, b1, t1), _lerp(b0, b1, t0)]


def _add_wall_body(mb: _MeshBuilder, wall: ResolvedWall, lod: str, openings=()) -> None:
    """Draw a wall's selectable body (its depth-layer prisms). Framing members are emitted as a
    separate ``framing`` node by the caller, so the framed LOD leaves the body empty and lets the
    stud model stand on its own."""
    if lod == "framed" and wall.members:
        return
    # Core LOD draws one prism per depth-bearing layer, carved around any hosted openings so
    # windows/doors read as voids and the arched front wall reads as piers + an arched head.
    # Cavity fill shares the structure layer's polygon, so extruding it too would only z-fight.
    ops = sorted(openings, key=lambda o: o.center_along_m)
    length = math.hypot(wall.axis[1][0] - wall.axis[0][0],
                        wall.axis[1][1] - wall.axis[0][1]) or 1.0
    for layer in wall.depth_layers():
        if not layer.polygon:
            continue
        color = _color(layer.function)
        if not ops:
            mb.add_prism(layer.polygon, wall.z0_m, wall.z1_m, color)
            continue
        _add_layer_with_openings(mb, layer.polygon, wall.axis, wall.z0_m, wall.z1_m,
                                 length, ops, color)


def _add_layer_with_openings(mb, poly, axis, z0, z1, length, ops, color) -> None:
    edges = _thin_rect_edges(poly, axis)
    cursor = 0.0
    for op in ops:
        o0 = max(0.0, (op.center_along_m - op.width_m / 2) / length)
        o1 = min(1.0, (op.center_along_m + op.width_m / 2) / length)
        if o1 <= o0:
            continue
        if o0 > cursor + 1e-6:  # solid pier before this opening
            mb.add_prism(_slice(edges, cursor, o0), z0, z1, color)
        bottom = min(z0 + op.sill_m, z1)
        head = min(bottom + op.height_m, z1)
        if bottom > z0 + 1e-6:  # sill band under the opening
            mb.add_prism(_slice(edges, o0, o1), z0, bottom, color)
        if op.arch_rise_m > 1e-6:  # spandrel above a semicircular/segmental arch soffit
            springline = bottom + max(0.0, op.height_m - op.arch_rise_m)
            radius = op.width_m / 2.0
            if z1 > springline + 1e-6:
                mb.add_arched_spandrel(edges, o0, o1, z1, springline, radius, color)
        elif z1 > head + 1e-6:  # square-head header
            mb.add_prism(_slice(edges, o0, o1), head, z1, color)
        cursor = max(cursor, o1)
    if cursor < 1.0 - 1e-6:  # trailing pier
        mb.add_prism(_slice(edges, cursor, 1.0), z0, z1, color)


def _add_opening_filling(mb: _MeshBuilder, wall: ResolvedWall, opening,
                         is_double_swing: bool) -> None:
    """Draw the door/window product itself — frame + panel/leaf/glass — as boxes.

    A straight port of ui/src/components/Panel3D.tsx ``buildOpening`` into the plan frame:
    a four-piece frame, then either a single door panel, two leaves split at a center
    mullion (``double_swing``), or a translucent glass pane (window). Rough openings are a
    bare void with no product, so they draw nothing. Emitted regardless of LOD so the leaf
    geometry shows for both the core wall prism and the framed stud model.
    """
    if opening.kind == "rough_opening":
        return
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 1e-9:
        return
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    nx, ny = -uy, ux  # right-hand wall normal (across the wall depth)
    posx, posy = x0 + ux * opening.center_along_m, y0 + uy * opening.center_along_m
    z0, sill = wall.z0_m, opening.sill_m
    available_height = max(0.0, min(opening.height_m, wall.z1_m - z0 - sill))
    if available_height <= 1e-9:
        return
    width = opening.width_m
    frame_width = min(0.075, width / 4.0, available_height / 4.0)
    depth = 0.08
    frame_color = _color("opening_frame")

    def add_box(box_w: float, box_h: float, box_t: float, along: float,
                elevation: float, color) -> None:
        cx, cy = posx + ux * along, posy + uy * along
        hw, ht = box_w / 2.0, box_t / 2.0
        ring = [
            (cx + ux * hw + nx * ht, cy + uy * hw + ny * ht),
            (cx + ux * hw - nx * ht, cy + uy * hw - ny * ht),
            (cx - ux * hw - nx * ht, cy - uy * hw - ny * ht),
            (cx - ux * hw + nx * ht, cy - uy * hw + ny * ht),
        ]
        mb.add_prism(ring, elevation - box_h / 2.0, elevation + box_h / 2.0, color)

    mid_elev = z0 + sill + available_height / 2.0
    add_box(frame_width, available_height, depth, -width / 2.0 + frame_width / 2.0, mid_elev, frame_color)
    add_box(frame_width, available_height, depth, width / 2.0 - frame_width / 2.0, mid_elev, frame_color)
    add_box(width, frame_width, depth, 0.0, z0 + sill + available_height - frame_width / 2.0, frame_color)
    add_box(width, frame_width, depth, 0.0, z0 + sill + frame_width / 2.0, frame_color)
    panel_height = max(0.01, available_height - 2.0 * frame_width)
    panel_elev = z0 + sill + frame_width + panel_height / 2.0
    if opening.kind == "door" and is_double_swing:
        mullion_width = min(frame_width, (width - 2.0 * frame_width) / 6.0)
        leaf_width = max(0.01, (width - 2.0 * frame_width - mullion_width) / 2.0)
        add_box(mullion_width, available_height, depth, 0.0, mid_elev, frame_color)
        add_box(leaf_width, panel_height, 0.045, -mullion_width / 2.0 - leaf_width / 2.0, panel_elev, frame_color)
        add_box(leaf_width, panel_height, 0.045, mullion_width / 2.0 + leaf_width / 2.0, panel_elev, frame_color)
    elif opening.kind == "door":
        add_box(max(0.01, width - 2.0 * frame_width), panel_height, 0.045, 0.0, panel_elev, frame_color)
    else:
        add_box(max(0.01, width - 2.0 * frame_width), panel_height, 0.015, 0.0, panel_elev, _color("glass"))


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


_CANVAS_TRADES = {"plumbing": "plumbing", "electrical": "electrical", "mechanical": "mechanical"}


def _canvas_trade(domain: str) -> str:
    """Route a resolved canvas object to its visibility trade, mirroring Panel3D.setModel:
    plumbing/electrical/mechanical keep their discipline; everything else (furniture,
    appliances, ...) lands in the furniture trade."""
    return _CANVAS_TRADES.get(domain, "furniture")


def _add_canvas_objects(scene: _SceneBuilder, model: ResolvedModel) -> None:
    """Emit one node per ResolvedCanvasObject (furniture, fixtures, MEP devices).

    Imported GLB furniture keeps its sidecar mesh; everything else extrudes its resolved
    (already rotation-baked) footprint to the type's height, matching Panel3D's canvas-object
    fallback box. ``domain=="opening"`` objects are skipped — they are already drawn as wall
    cuts + fillings — so they never produce an unclassifiable node.
    """
    furniture_types = {item.tag: item for item in model.plan.library.furniture_types}
    heights = {t["tag"]: t.get("height_m") for t in canvas_object_types(model.plan)}
    root = Path(model.plan.source_root or ".")
    for item in sorted(model.canvas_objects, key=lambda co: co.uid):
        if item.domain == "opening":
            continue
        mb = _MeshBuilder()
        furniture_type = furniture_types.get(item.type_ref)
        drawn = False
        if furniture_type is not None and getattr(furniture_type, "mesh", None) is not None:
            drawn = _add_mesh_sidecar(mb, root / furniture_type.mesh.path, item.position, item.z_m)
        if not drawn:
            _add_canvas_box(mb, item, heights.get(item.type_ref))
        scene.add_object(mb, trade=_canvas_trade(item.domain),
                         kind="canvas_object", uid=item.uid)


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


def _add_canvas_box(mb: _MeshBuilder, item: ResolvedCanvasObject, height_m: float | None) -> None:
    """Extrude a canvas object's resolved footprint into a box (Panel3D's fallback shape)."""
    ring = [tuple(point) for point in item.footprint]
    if len(ring) < 3:
        return
    height = height_m if height_m else 0.25  # Panel3D uses type.height_m ?? 0.25
    mb.add_prism(ring, item.z_m, item.z_m + height, _color("furniture"))


def _member_half_width(profile: str) -> float:
    # "2x6" → nominal 1.5" actual thickness; half of that in meters.
    try:
        nominal = float(profile.lower().split("x")[0])
    except (ValueError, IndexError):
        nominal = 2.0
    actual_in = max(nominal - 0.5, 0.75)
    return actual_in * 0.0254 / 2.0


def emit_gltf_dict(model: ResolvedModel, lod: str = "core") -> tuple[dict, bytes]:
    """Build the glTF JSON dict + binary blob for ``model`` (no file written).

    Emits one glTF node per source object, each tagged with ``extras`` (trade / kind / uid) so
    the 3D UI can promote the whole-house glb to the primary scene. Trades mirror
    Panel3D.setModel: walls→walls, wall/roof/floor/stair framing members→framing, openings→
    openings, solids & footing beddings→concrete, rooms & floors→floors, roofs→roof,
    stairs→stairs, canvas objects routed by domain.
    """
    scene = _SceneBuilder()
    openings_by_wall: dict[str, list] = {}
    for op in model.openings:
        openings_by_wall.setdefault(op.host_wall, []).append(op)

    for wall in sorted(model.walls, key=lambda w: w.uid):
        # Wall layer prisms are the selectable "walls" body; its framing members are their own
        # "framing" node so the framing visibility toggle reaches the studs.
        body = _MeshBuilder()
        _add_wall_body(body, wall, lod, openings_by_wall.get(wall.tag, ()))
        scene.add_object(body, trade="walls", kind="wall", uid=wall.uid)
        if wall.members:
            framing = _MeshBuilder()
            for member in wall.members:
                _add_member(framing, member)
            scene.add_object(framing, trade="framing")

    door_operations = {dt.tag: dt.operation for dt in model.plan.library.door_types}
    walls_by_tag = {wall.tag: wall for wall in model.walls}
    for op in sorted(model.openings, key=lambda item: item.uid):
        host = walls_by_tag.get(op.host_wall)
        if host is None:
            continue
        mb = _MeshBuilder()
        is_double_swing = op.is_door and door_operations.get(op.type_ref) == "double_swing"
        _add_opening_filling(mb, host, op, is_double_swing)
        scene.add_object(mb, trade="openings")

    for room in sorted(model.rooms, key=lambda r: r.uid):
        if room.clear_face:
            storey_z = _room_z(model, room.storey)
            mb = _MeshBuilder()
            mb.add_prism(room.clear_face, storey_z, storey_z + 0.02, _color("floor"))
            scene.add_object(mb, trade="floors")

    for solid in sorted(model.solids, key=lambda item: item.uid):
        if solid.outline:
            mb = _MeshBuilder()
            mb.add_prism_with_rectangular_voids(solid.outline, solid.voids, solid.z0_m,
                                                solid.z1_m, _solid_color(model, solid))
            scene.add_object(mb, trade="concrete")

    for bedding in sorted(model.footing_beddings, key=lambda item: item.uid):
        if bedding.outline and bedding.z1_m > bedding.z0_m:
            mb = _MeshBuilder()
            mb.add_prism(bedding.outline, bedding.z0_m, bedding.z1_m, _color("pad"))
            scene.add_object(mb, trade="concrete")

    for roof in sorted(model.roofs, key=lambda item: item.uid):
        mb = _MeshBuilder()
        _add_roof(mb, roof)
        scene.add_object(mb, trade="roof")

    for floor in sorted(model.floors, key=lambda item: item.uid):
        mb = _MeshBuilder()
        for member in floor.members:
            _add_member(mb, member)
        scene.add_object(mb, trade="floors")

    for stair in sorted(model.stairs, key=lambda item: item.uid):
        mb = _MeshBuilder()
        for member in stair.members:
            _add_member(mb, member)
        scene.add_object(mb, trade="stairs")

    _add_canvas_objects(scene, model)

    if scene.is_empty():  # keep the container valid even for an empty model
        mb = _MeshBuilder()
        mb.add_prism([(0, 0), (0.001, 0), (0.001, 0.001)], 0.0, 0.001, _FALLBACK)
        scene.add_object(mb, trade="earth")
    return scene.build()


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
