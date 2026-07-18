"""Binary glTF (``.glb``) emission over the ResolvedModel (#51, → 20 §Agent eyes).

Feeds the UI 3D panel and ``haus render --view 3d`` (offscreen). Self-contained — no
ifcopenshell, no geometry kernel — so it runs in a clean install as part of the cold-start
gate (→ 21b M2 acceptance). Walls extrude their resolved layer polygons; framing members and
room floors become boxes; colors come from a small function palette.
"""

from __future__ import annotations

from typehaus.emit.gltf.emitter import emit_glb, emit_gltf_dict

__all__ = ["emit_glb", "emit_gltf_dict"]
