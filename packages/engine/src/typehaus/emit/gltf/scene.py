"""Scene assembly: per-object nodes, the deduplicated material list, and the shared binary
buffer they all index into."""

from __future__ import annotations

import base64

from typehaus.emit.gltf.buffers import (
    _append_normals,
    _append_positions,
    _deindex_with_normals,
)
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.trades import TRADES

# The selection-kind vocabulary the UI honours — mirrors ``SelectionKind`` in
# ui/src/state/store.ts and the ``kind`` accepted by Panel3D.wholeHouseGlbAssignment. Held as
# an explicit set so a typo raises here instead of silently shipping an unselectable node.
_SELECTION_KINDS = frozenset({
    "wall", "opening", "room", "solid", "footing_bedding", "floor", "roof", "stair",
    "canvas_object", "brace", "wedge", "paneling",
})


def _color_name(color: tuple[float, float, float, float]) -> str:
    """"color_rrggbbaa" — a stable, collision-free label for a deduplicated material."""
    r, g, b, a = (round(max(0.0, min(1.0, c)) * 255) for c in color)
    return f"color_{r:02x}{g:02x}{b:02x}{a:02x}"


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
            translucent = color[3] < 1.0
            self._materials.append({
                # A name gives Revit/SketchUp's material browser something other than an
                # anonymous "Material_0" to show — cosmetic, but it is what a human continuing
                # the import sees first (→ #48's "continue the model rather than redraw it").
                # Hex-of-the-colour rather than the semantic category name (e.g. "stud"): many
                # categories collapse onto the same RGBA (§_PALETTE), so a colour is the only
                # key this dedup table actually has.
                "name": _color_name(color),
                "pbrMetallicRoughness": {
                    "baseColorFactor": list(color), "metallicFactor": 0.0,
                    "roughnessFactor": 0.9,
                },
                "alphaMode": "BLEND" if translucent else "OPAQUE",
                # Opaque solids are single-sided with verified outward winding (what Revit/
                # SketchUp want — no blue back-faces); translucent glass stays double-sided so
                # both faces of a thin pane read.
                "doubleSided": translucent,
            })
        return index

    def add_object(self, mb: _MeshBuilder, trade: str,
                   kind: str | None = None, uid: str | None = None) -> None:
        """Emit one node for ``mb``'s geometry, tagged so the UI can classify and select it.

        ``kind`` is one of ``_SELECTION_KINDS`` — the same vocabulary the live viewer's pick
        handler emits — and ``uid`` is the model uid picking and highlight resolve against.
        Geometry that belongs to a parent element (a wall's studs, a floor's joists) passes its
        *parent's* kind + uid, matching the viewer: individual framing members are merged into
        shared draw calls and never carry an identity of their own. A node with no geometry is
        skipped entirely, so it can never become an unclassifiable renderable mesh.
        """
        if kind is not None and kind not in _SELECTION_KINDS:
            raise ValueError(f"unknown selection kind {kind!r}; "
                             f"expected one of {sorted(_SELECTION_KINDS)}")
        # Solids take their trade from a table (emit/trades.py); a typo there has to fail
        # here rather than ship a node whose group the UI has nowhere to put.
        if trade not in TRADES:
            raise ValueError(f"unknown trade {trade!r}; expected one of {sorted(TRADES)}")
        primitives: list[dict] = []
        for color, positions, indices in mb.buckets():
            # De-index into flat triangle soup with one geometric normal per face. Every builder
            # emits triangles into these buckets, so this single step gives all of them crisp
            # per-face normals (shared corners would round under averaged normals) and hands
            # Revit/SketchUp explicit normals. Non-indexed is smaller than re-emitting indices.
            tri_positions, tri_normals = _deindex_with_normals(positions, indices)
            if not tri_positions:
                continue
            pos_acc = _append_positions(self._blob, self._buffer_views, self._accessors,
                                        tri_positions)
            nrm_acc = _append_normals(self._blob, self._buffer_views, self._accessors,
                                      tri_normals)
            primitives.append({
                "attributes": {"POSITION": pos_acc, "NORMAL": nrm_acc},
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
