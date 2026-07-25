"""glTF 2.0 binary writer over :class:`~typehaus.resolve.model.ResolvedModel` (#51).

No external dependency: geometry is built from the resolved layer polygons (already SI meters,
project-north frame) by vertical extrusion, and packed into a standard ``.glb`` container
(12-byte header + JSON chunk + BIN chunk). glTF is Y-up; our plan frame is (x east, y north,
z up), so we map model ``(x, y, z) -> glTF (x, z, -y)`` once, in :mod:`.geometry`.

This module is the entry point: it walks the resolved model, hands each source object to the
builder that knows its shape (:mod:`.walls`, :mod:`.openings`, :mod:`.members`, :mod:`.roofs`,
:mod:`.canvas_objects`, all over :mod:`.mesh` + :mod:`.palette`), and writes the container.
The names the rest of the tree already imports from ``typehaus.emit.gltf.emitter`` are
re-exported below, so splitting the builders out stayed internal to this package.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

from typehaus.emit.gltf.canvas_objects import _add_canvas_objects
from typehaus.emit.gltf.members import _add_member, is_roof_framing_member
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.openings import _add_opening_filling
from typehaus.emit.gltf.palette import _FALLBACK, _color, _solid_color
from typehaus.emit.gltf.roofs import _add_roof
from typehaus.emit.gltf.scene import _SceneBuilder
from typehaus.emit.gltf.walls import _add_wall_body
from typehaus.resolve.model import ResolvedModel

# Re-exported for callers that reach past the entry point (tests pinning palette parity, the
# arch-soffit tessellation, the wall/roof builders). Import them from their own modules in new
# code; this list keeps ``from typehaus.emit.gltf.emitter import ...`` working unchanged.
from typehaus.emit.gltf.buffers import _deindex_with_normals  # noqa: F401
from typehaus.emit.gltf.geometry import (  # noqa: F401
    _ARCH_SOFFIT_CHORD_TOLERANCE_M,
    _to_gltf,
    _ARCH_SOFFIT_MAX_SEGMENTS,
    _ARCH_SOFFIT_MIN_SEGMENTS,
    _arch_soffit_sample,
    _arch_soffit_segment_count,
    _thin_rect_edges,
    _without_collinear_vertices,
)
from typehaus.emit.gltf.openings import (  # noqa: F401
    _DOOR_LEAF_THICKNESS_M,
    _DOUBLE_SWING_LEAF_COUNT,
    _DOUBLE_SWING_MULLION_CLEAR_WIDTH_DIVISOR,
    _OPENING_FRAME_DEPTH_M,
    _OPENING_FRAME_FACE_WIDTH_M,
    _OPENING_FRAME_SPAN_DIVISOR,
    _OPENING_MIN_PANEL_DIMENSION_M,
    _WINDOW_GLAZING_THICKNESS_M,
)
from typehaus.emit.gltf.palette import (  # noqa: F401
    _CMU_BASE,
    _PALETTE,
    _SEAM_BASE,
    _hex_rgba,
    _material_finish_color,
)
from typehaus.emit.gltf.walls import _wall_top_at  # noqa: F401


def emit_gltf_dict(model: ResolvedModel, lod: str = "core") -> tuple[dict, bytes]:
    """Build the glTF JSON dict + binary blob for ``model`` (no file written).

    Emits one glTF node per source object, each tagged with ``extras`` (trade / kind / uid) so
    the 3D UI can promote the whole-house glb to the primary scene. Trades mirror
    Panel3D.setModel: walls→walls, wall/roof/floor/stair framing members→framing, openings→
    openings, solids & footing beddings→concrete, rooms & floors→floors, roofs→roof,
    stairs→stairs, canvas objects routed by domain. Every node carries a kind + uid so the
    export preserves the same per-element identity the viewer picks against; a framing node
    inherits the kind + uid of the wall / roof / floor / stair that owns it.
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
            scene.add_object(framing, trade="framing", kind="wall", uid=wall.uid)

    door_operations = {dt.tag: dt.operation for dt in model.plan.library.door_types}
    walls_by_tag = {wall.tag: wall for wall in model.walls}
    for op in sorted(model.openings, key=lambda item: item.uid):
        host = walls_by_tag.get(op.host_wall)
        if host is None:
            continue
        mb = _MeshBuilder()
        is_double_swing = op.is_door and door_operations.get(op.type_ref) == "double_swing"
        _add_opening_filling(mb, host, op, is_double_swing)
        scene.add_object(mb, trade="openings", kind="opening", uid=op.uid)

    for room in sorted(model.rooms, key=lambda r: r.uid):
        if room.clear_face:
            storey_z = _room_z(model, room.storey)
            mb = _MeshBuilder()
            mb.add_prism(room.clear_face, storey_z, storey_z + 0.02, _color("floor"))
            scene.add_object(mb, trade="floors", kind="room", uid=room.uid)

    for solid in sorted(model.solids, key=lambda item: item.uid):
        if solid.outline:
            mb = _MeshBuilder()
            mb.add_prism_with_rectangular_voids(solid.outline, solid.voids, solid.z0_m,
                                                solid.z1_m, _solid_color(model, solid))
            scene.add_object(mb, trade="concrete", kind="solid", uid=solid.uid)

    for bedding in sorted(model.footing_beddings, key=lambda item: item.uid):
        if bedding.outline and bedding.z1_m > bedding.z0_m:
            mb = _MeshBuilder()
            mb.add_prism(bedding.outline, bedding.z0_m, bedding.z1_m, _color("pad"))
            scene.add_object(mb, trade="concrete", kind="footing_bedding", uid=bedding.uid)

    for roof in sorted(model.roofs, key=lambda item: item.uid):
        mb = _MeshBuilder()
        _add_roof(mb, roof, model)
        scene.add_object(mb, trade="roof", kind="roof", uid=roof.uid)
        # Rafters, trusses and gable studs are framing, and belong in the framing trade with
        # every other stick in the building — not hidden behind the roof toggle. Same split
        # walls already use (body → walls, members → framing); selection still lands on the
        # roof because both nodes carry its uid.
        framing = _MeshBuilder()
        for member in roof.members:
            if is_roof_framing_member(member):
                _add_member(framing, member)
        scene.add_object(framing, trade="framing", kind="roof", uid=roof.uid)

    for panel in sorted(model.solar_panels, key=lambda item: item.uid):
        mb = _MeshBuilder()
        _add_solar_panel(mb, panel)
        scene.add_object(mb, trade="electrical", kind="solid", uid=panel.uid)

    for floor in sorted(model.floors, key=lambda item: item.uid):
        mb = _MeshBuilder()
        for member in floor.members:
            _add_member(mb, member)
        scene.add_object(mb, trade="floors", kind="floor", uid=floor.uid)

    for stair in sorted(model.stairs, key=lambda item: item.uid):
        mb = _MeshBuilder()
        for member in stair.members:
            _add_member(mb, member)
        scene.add_object(mb, trade="stairs", kind="stair", uid=stair.uid)

    for brace in sorted(model.braces, key=lambda item: item.uid):
        mb = _MeshBuilder()
        for member in brace.members:
            _add_member(mb, member)
        scene.add_object(mb, trade="framing", kind="brace", uid=brace.uid)

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


def _add_solar_panel(mb: _MeshBuilder, panel) -> None:
    """The resolver's tilted box as triangles — bottom, top, and four side quads."""
    bottom = [_to_gltf(*point) for point in panel.corners_bottom]
    top = [_to_gltf(*point) for point in panel.corners_top]
    color = _color("solar")
    triangles = [
        (bottom[2], bottom[1], bottom[0]), (bottom[3], bottom[2], bottom[0]),
        (top[0], top[1], top[2]), (top[0], top[2], top[3]),
    ]
    for index in range(len(bottom)):
        following = (index + 1) % len(bottom)
        quad = (bottom[index], bottom[following], top[following], top[index])
        triangles.append((quad[0], quad[1], quad[2]))
        triangles.append((quad[0], quad[2], quad[3]))
    mb.add_triangles(triangles, color)


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
