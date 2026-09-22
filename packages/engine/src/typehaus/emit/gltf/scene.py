"""Scene assembly: per-object nodes, the deduplicated material list, and the shared binary
buffer they all index into."""

from __future__ import annotations

import base64

from typehaus.emit.gltf.buffers import (
    _append_colors,
    _append_indices,
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
        self._shared: dict[str, int] = {}

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

    def add_object(self, mb: _MeshBuilder, trades: tuple[str, ...] | str,
                   kind: str | None = None, uid: str | None = None,
                   facet: str | None = None) -> None:
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
        # ``trades`` is the element's trade SET (a wall body is every trade its layers
        # belong to); extras carry both the set and its first member as ``trade`` for the
        # readers keyed on one. A typo has to fail here rather than ship a node the UI
        # has nowhere to put.
        trade_set = (trades,) if isinstance(trades, str) else tuple(trades)
        if not trade_set or any(trade not in TRADES for trade in trade_set):
            raise ValueError(f"unknown trade in {trade_set!r}; expected {sorted(TRADES)}")
        trade = trade_set[0]
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
        extras: dict[str, object] = {"trade": trade, "trades": list(trade_set)}
        if kind is not None:
            extras["kind"] = kind
        if uid is not None:
            extras["uid"] = uid
        # A sub-trade the viewer toggles on its own (``concrete:rebar``): same trade, its own chip.
        if facet is not None:
            extras["facet"] = facet
        # A "<trade>|<kind|>|<uid|>" name is a belt-and-suspenders fallback; extras is primary.
        name = "|".join((trade, kind or "", uid or ""))
        self._nodes.append({"mesh": mesh_index, "name": name, "extras": extras})

    def has_shared_mesh(self, key: str) -> bool:
        return key in self._shared

    def add_shared_mesh(self, key: str, primitives) -> bool:
        """One glTF mesh many nodes reuse — native glTF instancing (the plant prototypes).

        ``primitives`` is ``(color, positions, normals, colors, indices)`` per primitive, in
        glTF frame. Unlike :meth:`add_object` it stays INDEXED with the normals it is given:
        smooth, not de-indexed flat. Returns whether the mesh exists (``key`` already added
        counts). An empty mesh is not emitted.
        """
        if key in self._shared:
            return True
        out = []
        for color, positions, normals, colors, indices in primitives:
            if not indices:
                continue
            args = (self._blob, self._buffer_views, self._accessors)
            attributes = {"POSITION": _append_positions(*args, positions),
                          "NORMAL": _append_normals(*args, normals)}
            if colors:
                attributes["COLOR_0"] = _append_colors(*args, colors)
            out.append({"attributes": attributes, "indices": _append_indices(*args, indices),
                        "material": self._material(color)})
        if not out:
            return False
        self._shared[key] = len(self._meshes)
        self._meshes.append({"primitives": out, "name": key})
        return True

    def add_instance(self, mesh_key: str, translation, rotation, scale,
                     trades: tuple[str, ...], kind: str, uid: str) -> None:
        """A node placing a shared mesh with a TRS, carrying the usual extras."""
        if kind not in _SELECTION_KINDS:
            raise ValueError(f"unknown selection kind {kind!r}")
        if not trades or any(trade not in TRADES for trade in trades):
            raise ValueError(f"unknown trade in {trades!r}; expected {sorted(TRADES)}")
        self._nodes.append({
            "mesh": self._shared[mesh_key], "name": "|".join((trades[0], kind, uid)),
            "translation": list(translation), "rotation": list(rotation),
            "scale": list(scale),
            "extras": {"trade": trades[0], "trades": list(trades), "kind": kind, "uid": uid},
        })

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
