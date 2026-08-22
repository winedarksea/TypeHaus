"""A minimal structural validator for glTF 2.0 output — the local proxy for "will a real
importer accept this file" that this package didn't have (→ plans/revit-sketchup-readiness.md).

No dependency on a schema library: :mod:`.emitter` already writes glTF with zero external
packages (its own docstring says so), so verifying its output the same way keeps the whole
round trip dependency-free. This checks the load-bearing structural rules a strict importer
(the Khronos reference validator, and reportedly Revit/SketchUp's own importers) enforces —
buffer/accessor bounds, componentType byte-alignment, POSITION accessors carrying min/max,
and triangle-count divisibility — not the full JSON Schema. It is a proxy for "an importer
will accept this," not a certification; passing it is necessary, not sufficient.
"""

from __future__ import annotations

import base64
import struct

#: Byte size of each accessor componentType (glTF 2.0 §5.31.1 accessor.componentType).
_COMPONENT_SIZE = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}

#: Component count per accessor.type (glTF 2.0 §5.31.1 accessor.type).
_TYPE_COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4,
                    "MAT2": 4, "MAT3": 9, "MAT4": 16}

_GLB_MAGIC = 0x46546C67
_CHUNK_JSON = 0x4E4F534A
_CHUNK_BIN = 0x004E4942


def validate_gltf(gltf: dict, buffer_lengths: list[int] | None = None) -> list[str]:
    """Structural errors in a glTF JSON document, or ``[]`` if none are found.

    ``buffer_lengths`` overrides each ``buffers[i].byteLength`` with the actual length of the
    bytes that will back it (the ``.glb`` BIN chunk has none embedded to check against — its
    ``uri`` is stripped in :func:`.emitter.emit_glb`). Without it, only a data-URI buffer's own
    declared length is checked for internal consistency (base64-decoded length vs. byteLength).
    """
    errors: list[str] = []

    def err(msg: str) -> None:
        errors.append(msg)

    asset = gltf.get("asset")
    if not isinstance(asset, dict) or asset.get("version") != "2.0":
        err("asset.version must be the literal string '2.0'")

    buffers = gltf.get("buffers") or []
    actual_lengths: list[int] = []
    for i, buf in enumerate(buffers):
        declared = buf.get("byteLength")
        if buffer_lengths is not None and i < len(buffer_lengths):
            actual = buffer_lengths[i]
        elif isinstance(buf.get("uri"), str) and buf["uri"].startswith("data:"):
            _, _, encoded = buf["uri"].partition(",")
            actual = len(base64.b64decode(encoded))
        else:
            actual = declared
        actual_lengths.append(actual if isinstance(actual, int) else 0)
        if declared != actual:
            err(f"buffers[{i}].byteLength={declared} does not match actual data length {actual}")

    buffer_views = gltf.get("bufferViews") or []
    for i, view in enumerate(buffer_views):
        buf_index = view.get("buffer")
        if not isinstance(buf_index, int) or not (0 <= buf_index < len(buffers)):
            err(f"bufferViews[{i}].buffer={buf_index!r} is out of range")
            continue
        end = view.get("byteOffset", 0) + view.get("byteLength", 0)
        if end > actual_lengths[buf_index]:
            err(f"bufferViews[{i}] spans byte {end} past buffer {buf_index}'s "
                f"{actual_lengths[buf_index]} bytes")

    accessors = gltf.get("accessors") or []
    for i, acc in enumerate(accessors):
        component_type = acc.get("componentType")
        acc_type = acc.get("type")
        count = acc.get("count")
        if component_type not in _COMPONENT_SIZE:
            err(f"accessors[{i}].componentType={component_type!r} is not a valid glTF enum")
            continue
        if acc_type not in _TYPE_COMPONENTS:
            err(f"accessors[{i}].type={acc_type!r} is not a valid glTF enum")
            continue
        if not isinstance(count, int) or count < 1:
            err(f"accessors[{i}].count must be a positive integer, got {count!r}")
        view_index = acc.get("bufferView")
        if view_index is not None:
            if not (0 <= view_index < len(buffer_views)):
                err(f"accessors[{i}].bufferView={view_index!r} is out of range")
            else:
                element_size = _COMPONENT_SIZE[component_type] * _TYPE_COMPONENTS[acc_type]
                total_offset = (buffer_views[view_index].get("byteOffset", 0)
                                + acc.get("byteOffset", 0))
                # Every strict importer (and the Khronos reference validator) rejects an
                # accessor whose element does not start on a componentType-sized boundary —
                # the historic "misaligned accessor" class of bug.
                if total_offset % _COMPONENT_SIZE[component_type] != 0:
                    err(f"accessors[{i}] starts at byte {total_offset}, not a multiple of "
                        f"componentType size {_COMPONENT_SIZE[component_type]}")
                needed = element_size * (count or 0)
                view_len = buffer_views[view_index].get("byteLength", 0)
                if acc.get("byteOffset", 0) + needed > view_len:
                    err(f"accessors[{i}] needs {needed} bytes but its bufferView only has "
                        f"{view_len}")

    meshes = gltf.get("meshes") or []
    materials = gltf.get("materials") or []
    position_accessors: set[int] = set()
    for i, mesh in enumerate(meshes):
        primitives = mesh.get("primitives") or []
        if not primitives:
            err(f"meshes[{i}] has no primitives")
        for j, prim in enumerate(primitives):
            attributes = prim.get("attributes") or {}
            if "POSITION" not in attributes:
                err(f"meshes[{i}].primitives[{j}] has no POSITION attribute")
            else:
                pos_acc = attributes["POSITION"]
                position_accessors.add(pos_acc)
                # A non-indexed triangle-mode primitive (no "indices", the default "mode" 4)
                # must supply a whole number of triangles — Revit and SketchUp both silently
                # drop or misdraw the trailing partial face rather than erroring.
                if ("indices" not in prim and prim.get("mode", 4) == 4
                        and 0 <= pos_acc < len(accessors)):
                    pos_count = accessors[pos_acc].get("count", 0)
                    if pos_count % 3 != 0:
                        err(f"meshes[{i}].primitives[{j}] is non-indexed TRIANGLES with "
                            f"{pos_count} positions, not a multiple of 3")
            material_index = prim.get("material")
            if material_index is not None and not (0 <= material_index < len(materials)):
                err(f"meshes[{i}].primitives[{j}].material={material_index!r} is out of range")

    for acc_index in position_accessors:
        if not (0 <= acc_index < len(accessors)):
            continue
        acc = accessors[acc_index]
        # glTF 2.0 §5.31.1: POSITION accessors are the one case min/max is mandatory, because
        # importers use it to size the scene/bounding volume before touching the buffer.
        if "min" not in acc or "max" not in acc:
            err(f"accessors[{acc_index}] backs a POSITION attribute but has no min/max")

    nodes = gltf.get("nodes") or []
    for i, node in enumerate(nodes):
        mesh_index = node.get("mesh")
        if mesh_index is not None and not (0 <= mesh_index < len(meshes)):
            err(f"nodes[{i}].mesh={mesh_index!r} is out of range")

    scenes = gltf.get("scenes") or []
    for i, scene in enumerate(scenes):
        for node_index in scene.get("nodes", []):
            if not (0 <= node_index < len(nodes)):
                err(f"scenes[{i}].nodes contains out-of-range node {node_index!r}")

    scene_index = gltf.get("scene")
    if scene_index is not None and not (0 <= scene_index < len(scenes)):
        err(f"root 'scene'={scene_index!r} is out of range")

    return errors


def validate_glb_bytes(data: bytes) -> list[str]:
    """Structural errors in a packed ``.glb`` container, or ``[]`` if none are found.

    Parses the 12-byte header and each chunk itself (independent of :mod:`.emitter`'s writer,
    so a header/length/padding bug in the writer is exactly what this catches — the "opens in
    our own viewer but not in anyone else's" failure mode a round-trip test through our own
    parser cannot see), then hands the JSON chunk to :func:`validate_gltf` with the real BIN
    chunk length substituted for the (deliberately absent) buffer URI.
    """
    if len(data) < 12:
        return [f"glb too short for a header: {len(data)} bytes"]
    magic, version, length = struct.unpack_from("<III", data, 0)
    errors: list[str] = []
    if magic != _GLB_MAGIC:
        errors.append(f"bad glb magic {magic:#x}, expected {_GLB_MAGIC:#x}")
    if version != 2:
        errors.append(f"unsupported glb version {version}, expected 2")
    if length != len(data):
        errors.append(f"header length {length} does not match actual file size {len(data)}")
    offset = 12
    json_bytes: bytes | None = None
    bin_length: int | None = None
    while offset + 8 <= len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        chunk_start = offset + 8
        if chunk_start + chunk_length > len(data):
            errors.append(f"chunk at offset {offset} claims {chunk_length} bytes past EOF")
            break
        if chunk_type == _CHUNK_JSON:
            json_bytes = data[chunk_start:chunk_start + chunk_length]
        elif chunk_type == _CHUNK_BIN:
            bin_length = chunk_length
        offset = chunk_start + chunk_length
    if json_bytes is None:
        errors.append("glb has no JSON chunk")
        return errors
    import json

    try:
        gltf = json.loads(json_bytes)
    except json.JSONDecodeError as exc:
        errors.append(f"glb JSON chunk is not valid JSON: {exc}")
        return errors
    buffer_lengths = [bin_length] if bin_length is not None else None
    errors.extend(validate_gltf(gltf, buffer_lengths))
    return errors
