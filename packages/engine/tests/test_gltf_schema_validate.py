"""The local proxy for "will Revit/SketchUp accept this glTF" (→ plans/revit-sketchup-readiness.md):
run :mod:`typehaus.emit.gltf.validate` over the starter house's actual emitted output, both as
the in-memory dict :func:`emit_gltf_dict` returns and as the packed ``.glb`` bytes
:func:`emit_glb` writes to disk — the two are built differently (the dict keeps a data-URI
buffer; the ``.glb`` strips it for a BIN chunk) and a bug can live in either path.
"""

from __future__ import annotations

from pathlib import Path

from typehaus.emit.gltf import emit_glb, emit_gltf_dict
from typehaus.emit.gltf.validate import validate_glb_bytes, validate_gltf
from typehaus.resolve import resolve
from typehaus.source import load_plan


def test_emitted_gltf_dict_is_structurally_valid(starter_dir: Path) -> None:
    result = load_plan(starter_dir)
    model, _findings = resolve(result.plan)
    gltf, blob = emit_gltf_dict(model)
    errors = validate_gltf(gltf, buffer_lengths=[len(blob)])
    assert errors == []


def test_emitted_glb_file_is_structurally_valid(starter_dir: Path, tmp_path: Path) -> None:
    result = load_plan(starter_dir)
    model, _findings = resolve(result.plan)
    out_path = emit_glb(model, tmp_path / "model.glb")
    errors = validate_glb_bytes(out_path.read_bytes())
    assert errors == []


def test_validator_catches_a_truncated_buffer() -> None:
    """A validator that can't fail is not testing anything: corrupt one real document and
    confirm it is caught, so a future no-op refactor of ``validate_gltf`` is itself caught."""
    gltf = {
        "asset": {"version": "2.0"},
        "buffers": [{"byteLength": 100}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 100}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": 10, "type": "VEC3",
                       "min": [0, 0, 0], "max": [1, 1, 1]}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        "nodes": [{"mesh": 0}],
        "scenes": [{"nodes": [0]}],
        "scene": 0,
    }
    # Declares 100 bytes but the real buffer is only 40 — a truncated write.
    errors = validate_gltf(gltf, buffer_lengths=[40])
    assert any("byteLength" in e for e in errors)
