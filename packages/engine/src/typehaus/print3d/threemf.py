"""A stdlib, byte-deterministic writer for core-spec 3MF (and binary STL as a fallback).

Each piece is its own ``<object>`` and its own build ``<item>``, laid out in a row for the
slicer to auto-arrange. Plates and filament assignments are Bambu/Orca project features
(``Metadata/model_settings.config``), not core 3MF, so none is written: Bambu Studio imports
the objects and arranges them itself. Fixed zip timestamps and sorted entries keep two runs
byte-identical.
"""

from __future__ import annotations

import struct
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

import numpy as np

from typehaus.print3d.pieces import Piece

_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
_GAP_MM = 5.0
_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" '
    'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" '
    'ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    "</Types>\n")
_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
    "</Relationships>\n")


def write_3mf(path: Path, pieces: list[Piece], title: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    objects, items = [], []
    x = 0.0
    for number, piece in enumerate(pieces, start=1):
        vertices, triangles = _mesh(piece.solid)
        vertices = vertices + np.array([x + piece.dims_mm[0] / 2, piece.dims_mm[1] / 2, 0.0])
        x += piece.dims_mm[0] + _GAP_MM
        lines = [f'<object id="{number}" type="model" name={quoteattr(piece.name)}><mesh>'
                 "<vertices>"]
        lines += [f'<vertex x="{_num(a)}" y="{_num(b)}" z="{_num(c)}"/>' for a, b, c in vertices]
        lines.append("</vertices><triangles>")
        lines += [f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in triangles]
        lines.append("</triangles></mesh></object>")
        objects.append("".join(lines))
        items.append(f'<item objectid="{number}"/>')
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        f'<metadata name="Title">{_text(title)}</metadata>'
        '<metadata name="Application">Type:Haus print3d</metadata>'
        f'<resources>{"".join(objects)}</resources><build>{"".join(items)}</build>'
        "</model>\n")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, text in (("[Content_Types].xml", _CONTENT_TYPES), ("_rels/.rels", _RELS),
                           ("3D/3dmodel.model", model)):
            info = zipfile.ZipInfo(name, date_time=_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, text.encode("utf-8"))
    return path


def write_stl(path: Path, piece: Piece) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    vertices, triangles = _mesh(piece.solid)
    out = [struct.pack("<80sI", piece.name.encode("ascii", "replace")[:80], len(triangles))]
    for a, b, c in triangles:
        p, q, r = vertices[a], vertices[b], vertices[c]
        normal = np.cross(q - p, r - p)
        length = float(np.linalg.norm(normal))
        normal = normal / length if length > 0 else normal
        out.append(struct.pack("<12fH", *normal, *p, *q, *r, 0))
    path.write_bytes(b"".join(out))
    return path


def _mesh(solid) -> tuple[np.ndarray, np.ndarray]:
    mesh = solid.to_mesh()
    return (np.asarray(mesh.vert_properties, dtype=float)[:, :3],
            np.asarray(mesh.tri_verts, dtype=int))


def _num(value: float) -> str:
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _text(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
