"""model.json's one mesh encoding: flat integers of a quantum, decoded by ``ui/src/three/mesh.ts``.

Nested ``[[x, y, z]]`` full-precision floats were most of the payload. A position is an
integer count of ``MESH_QUANTUM`` (10 µm: a 24 ga sheet is ~0.6 mm thick, so the plants'
1 mm quantum would fold it flat), a unit normal an integer of ``1 / NORMAL_SCALE``, and a
triangle three flat indices. Same idea as ``model_json_plants``.

Every stream is then delta-coded — each value minus the previous one on the same axis
(``stride``): neighbouring vertices sit millimetres apart, normals repeat face by face and
fan indices climb by one, so the digits that go over the wire are mostly short. Still exact.
"""

from __future__ import annotations

from typing import Any

MESH_QUANTUM = 1e-5
POSITION_SCALE = 100_000  # 1 / MESH_QUANTUM, multiplied rather than divided
NORMAL_SCALE = 10_000


def _delta(values: list[int], stride: int) -> list[int]:
    return values[:stride] + [values[i] - values[i - stride] for i in range(stride, len(values))]


def _undelta(values: list[int], stride: int) -> list[int]:
    out = list(values)
    for i in range(stride, len(out)):
        out[i] += out[i - stride]
    return out


def mesh_json(positions, triangles, normals=None) -> dict[str, Any]:
    """A mesh on the wire; ``normals`` are omitted when there are none."""
    out: dict[str, Any] = {
        "quantum": MESH_QUANTUM,
        "positions": _delta([round(c * POSITION_SCALE) for p in positions for c in p], 3),
        "triangles": _delta([i for t in triangles for i in t], 1),
    }
    if normals:
        out["normals"] = _delta([round(c * NORMAL_SCALE) for n in normals for c in n], 3)
    return out


def decode_mesh(mesh: dict[str, Any]) -> dict[str, list]:
    """The nested form back, to the quantum — for tests and other Python readers."""
    q = mesh["quantum"]
    flat = _undelta(mesh["positions"], 3)
    tri = _undelta(mesh["triangles"], 1)
    normals = _undelta(mesh.get("normals") or [], 3)
    return {
        "positions": [(flat[i] * q, flat[i + 1] * q, flat[i + 2] * q)
                      for i in range(0, len(flat), 3)],
        "triangles": [tuple(tri[i:i + 3]) for i in range(0, len(tri), 3)],
        "normals": [(normals[i] / NORMAL_SCALE, normals[i + 1] / NORMAL_SCALE,
                     normals[i + 2] / NORMAL_SCALE) for i in range(0, len(normals), 3)],
    }
