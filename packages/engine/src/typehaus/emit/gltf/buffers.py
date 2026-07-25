"""glTF binary plumbing: accessors, buffer views, and the de-indexing that gives every face an
explicit normal (what Revit/SketchUp want on import)."""

from __future__ import annotations

import math
import struct

from typehaus.emit.gltf.geometry import Vec3


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


def _append_normals(blob: bytearray, views: list[dict], accessors: list[dict],
                    normals: list[Vec3]) -> int:
    _align(blob)
    offset = len(blob)
    for (x, y, z) in normals:
        blob += struct.pack("<fff", x, y, z)
    views.append({"buffer": 0, "byteOffset": offset,
                  "byteLength": len(normals) * 12, "target": 34962})
    accessors.append({
        "bufferView": len(views) - 1, "componentType": 5126, "count": len(normals),
        "type": "VEC3",
    })
    return len(accessors) - 1


def _face_normal(a: Vec3, b: Vec3, c: Vec3) -> Vec3 | None:
    """Unit outward normal of triangle a→b→c (right-hand rule), or ``None`` if degenerate."""
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length < 1e-12:
        return None
    return (nx / length, ny / length, nz / length)


def _deindex_with_normals(positions: list[Vec3],
                          indices: list[int]) -> tuple[list[Vec3], list[Vec3]]:
    """Expand an indexed triangle mesh into flat triangle soup with one geometric normal per
    face. Hard edges stay crisp (each face carries its own normal on unshared vertices) and
    degenerate zero-area triangles are dropped.

    A face listed in ``indices.smooth_face_normals`` (see :class:`_TriangleIndices`; today only
    the arch soffit, which lies on a true cylinder) ships the supplied analytic per-corner
    normals instead, so adjacent facets shade as one continuous curve.
    """
    smooth_faces = getattr(indices, "smooth_face_normals", {})
    out_pos: list[Vec3] = []
    out_nrm: list[Vec3] = []
    for i in range(0, len(indices) - 2, 3):
        a, b, c = positions[indices[i]], positions[indices[i + 1]], positions[indices[i + 2]]
        normal = _face_normal(a, b, c)
        if normal is None:
            continue
        out_pos.extend((a, b, c))
        smooth = smooth_faces.get(i // 3)
        if smooth is None:
            out_nrm.extend((normal, normal, normal))
            continue
        # Replace the facet's direction only. The outward sense stays whatever the triangle
        # winding established, so the single-sided-material contract is untouched; all three
        # corners flip together or not at all.
        agreement = sum(sum(s * f for s, f in zip(corner, normal)) for corner in smooth)
        sign = -1.0 if agreement < 0.0 else 1.0
        out_nrm.extend(tuple(sign * component for component in corner) for corner in smooth)
    return out_pos, out_nrm


def _align(blob: bytearray, boundary: int = 4) -> None:
    while len(blob) % boundary:
        blob.append(0)
