"""Resolving an annotation anchor to a point in the detail's slice frame.

An annotation is anchored by ``(element uid, face role)`` plus a 2D offset, not by frozen
coordinates, so that moving the wall moves the note with it. An anchor that no longer
resolves degrades to a ``detail.anchor_unresolved`` finding and an error marker — never to
a note silently pointing at the wrong thing.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.resolve.model import ResolvedModel


def resolve_anchor(model: ResolvedModel, frame, uid: str, face: str):
    """Resolve an ``(uid, face)`` anchor to a section-frame point, or an error finding.

    v1 faces — walls: "top"/"bottom"/"ext-face"/"int-face"/"layer:<name>:out|in";
    roofs: "eave"/"deck-top"; solids: "top".
    """
    wall = next((w for w in model.walls if w.uid == uid), None)
    if wall is not None:
        return _wall_anchor(wall, face, frame)
    roof = next((r for r in model.roofs if r.uid == uid), None)
    if roof is not None:
        return _roof_anchor(roof, face, frame)
    solid = next((s for s in model.solids if s.uid == uid), None)
    if solid is not None:
        return _solid_anchor(solid, face, frame)
    return (0.0, 0.0), _unresolved(uid, face)


def _unresolved(uid: str, face: str) -> Finding:
    return Finding(severity=Severity.ERROR, check_id="detail.anchor_unresolved",
                   message=f"detail annotation anchor {uid!r} face {face!r} does not resolve",
                   element_tags=(uid,), result=Result.FAIL)


def _wall_anchor(wall, face: str, frame):
    (x0, y0), (x1, y1) = wall.axis
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    top = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    if face == "top":
        return frame(mx, my, top), None
    if face == "bottom":
        return frame(mx, my, wall.z0_m), None
    if face in ("ext-face", "int-face"):
        # first/last layer centroid at mid height
        layer = wall.layers[0] if face == "int-face" else wall.layers[-1]
        return _layer_point(layer, wall, frame, "in" if face == "int-face" else "out"), None
    if face.startswith("layer:"):
        _, name, side = (face.split(":") + ["out"])[:3]
        layer = _find_layer(wall, name)
        if layer is None:
            return frame(mx, my, top), _unresolved(wall.uid, face)
        return _layer_point(layer, wall, frame, side), None
    return frame(mx, my, top), _unresolved(wall.uid, face)


# Control-layer role → the ``ControlLayer`` value a layer must carry to realise it. A
# continuity claim names the role it is about ("ci-ext" = the continuous insulation plane),
# not the layer that happens to provide it, so a variant may re-spell its layers without
# invalidating the claim (#44).
_ROLE_CONTROL = {"ci": "thermal", "thermal": "thermal", "air": "air",
                 "water": "water", "vapor": "vapor"}


def _find_layer(wall, name: str):
    """Resolve a layer by name, then by the control-layer role it publishes."""
    exact = next((layer for layer in wall.layers if layer.name == name), None)
    if exact is not None:
        return exact
    control = _ROLE_CONTROL.get(name)
    if control is None:
        return None
    # Outermost layer carrying that control: the plane a transition laps to.
    matching = [layer for layer in wall.layers if control in layer.control]
    return matching[-1] if matching else None


def _layer_point(layer, wall, frame, side: str):
    xs = [p[0] for p in layer.polygon]
    ys = [p[1] for p in layer.polygon]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    zmid = (wall.z0_m + (wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m)) / 2.0
    return frame(cx, cy, zmid)


def _roof_anchor(roof, face: str, frame):
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    if face == "eave":
        return frame(cx, cy, roof.eave_z_m), None
    if face == "deck-top":
        return frame(cx, cy, roof.ridge_z_m), None
    return frame(cx, cy, roof.eave_z_m), _unresolved(roof.uid, face)


def _solid_anchor(solid, face: str, frame):
    xs = [p[0] for p in solid.outline]
    ys = [p[1] for p in solid.outline]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    if face == "top":
        return frame(cx, cy, solid.z1_m), None
    return frame(cx, cy, solid.z1_m), _unresolved(solid.uid, face)
