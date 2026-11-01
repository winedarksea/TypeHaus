"""Resolving an annotation anchor to a point in the detail's slice frame.

An annotation is anchored by ``(element uid, face role)`` plus a 2D offset, not by frozen
coordinates, so that moving the wall moves the note with it. An anchor that no longer
resolves degrades to a ``detail.anchor_unresolved`` finding and an error marker — never to
a note silently pointing at the wrong thing.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.quantities import M_PER_IN
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


# --- cut-local anchors (``SliceDimension``) -------------------------------------------------

#: Model collections an anchor tag may name; ownership is by uid (``uid`` or ``uid::part``).
_ANCHOR_COLLECTIONS = ("walls", "solids", "roofs", "floors", "stairs", "soffits",
                       "ceilings", "openings", "canvas_objects")


def cut_anchor(model: ResolvedModel, scene, view, ref) -> tuple[float, float] | None:
    """A ``SliceDimension`` anchor → ``(u, z)`` inches in the cut, or ``None``.

    A literal ``Point2D`` is already cut-local. ``storey:<tag>[:plate]`` is a datum (z only;
    u is 0). ``<TAG>:<face>`` reads the element's OWN cut — the scene nodes it drew, matched
    by uid — so the anchor is the geometry at this station, clipped to the crop, never the
    element's midpoint. A wall also answers ``exterior``/``interior`` (finish faces), a
    stair ``riser:<i>`` (z only), and a placeable its body where the plane crosses it.
    """
    if not isinstance(ref, str):
        u_m, z_m = ref.xy_m
        return (u_m / M_PER_IN, z_m / M_PER_IN)
    kind, _, face = ref.partition(":")
    if kind == "storey":
        return _storey_anchor(model, face)
    uids = {e.uid for name in _ANCHOR_COLLECTIONS for e in getattr(model, name, ())
            if getattr(e, "tag", None) == kind and getattr(e, "uid", None)}
    if not uids:
        return None
    stair = next((st for st in model.stairs if st.tag == kind), None)
    if stair is not None and face.startswith("riser:"):
        index = int(face.split(":")[1])
        return (0.0, (stair.base_elevation_m + index * stair.riser_height_m) / M_PER_IN)
    box = _cut_box(scene, uids) or _placeable_box(model, view, kind)
    if box is None:
        return None
    u0, z0, u1, z1 = box
    um, zm = (u0 + u1) / 2.0, (z0 + z1) / 2.0
    faces = {"top": (um, z1), "bottom": (um, z0), "left": (u0, zm), "right": (u1, zm)}
    if face in faces:
        return faces[face]
    wall = next((w for w in model.walls if w.tag == kind), None)
    if wall is not None and face in ("exterior", "interior"):
        from typehaus.emit.draw.detail_components.geometry import outboard_is_high

        direction, station = cut_frame(view)
        high = outboard_is_high(wall, direction, station)
        if high is None:
            return None
        return ((u1 if high == (face == "exterior") else u0), zm)
    return None


def cut_frame(view) -> tuple[str, float]:
    """``(direction, station_m)`` of an authored slice — the convention ``build_section`` cuts."""
    direction = view.cut_direction or "x"
    x_m, y_m = view.cut_origin.xy_m
    return direction, (y_m if direction == "x" else x_m)


def _storey_anchor(model: ResolvedModel, face: str):
    name, _, which = face.partition(":")
    for _primary, storeys in model.plan.levels():
        storey = next((s for s in storeys if s.tag == name), None)
        if storey is None:
            continue
        if which == "plate":
            plates = [w.plate_top_z_m for w in model.walls
                      if w.storey == name and w.plate_top_z_m is not None]
            return (0.0, max(plates) / M_PER_IN) if plates else None
        return (0.0, storey.elevation.meters / M_PER_IN)
    return None


def _placeable_box(model: ResolvedModel, view, tag: str):
    """A placeable's body where the plane crosses its footprint: a section draws no
    furniture, but a bench top is still a height worth dimensioning (I3-003)."""
    from typehaus.resolve.geometry_slice import CutPlane, ring_intervals

    obj = next((o for o in model.canvas_objects if o.tag == tag and o.footprint), None)
    if obj is None or obj.body_z1_m is None:
        return None
    direction, station = cut_frame(view)
    spans = ring_intervals(obj.footprint, CutPlane(axis=direction, station_m=station))
    if not spans:
        return None
    lo = min(min(span) for span in spans) / M_PER_IN
    hi = max(max(span) for span in spans) / M_PER_IN
    return (lo, obj.body_z0_m / M_PER_IN, hi, obj.body_z1_m / M_PER_IN)


def _cut_box(scene, uids: set[str]) -> tuple[float, float, float, float] | None:
    """Bounds of the cut linework/fill an element (or its ``uid::part`` children) drew."""
    us: list[float] = []
    zs: list[float] = []
    for node in scene.nodes:
        uid = getattr(node, "uid", None)
        if not uid or not (uid in uids or uid.split("::")[0] in uids):
            continue
        points = getattr(node, "points", None) or getattr(node, "boundary", None) or ()
        for u, z in points:
            us.append(u)
            zs.append(z)
    if not us:
        return None
    return (min(us), min(zs), max(us), max(zs))


# --- keyed-bubble placement ------------------------------------------------------

def dimension_box(node, scale) -> tuple[float, float, float, float]:
    """Estimated bbox of a dimension string's label, model inches (text above / left)."""
    from typehaus.emit.draw.annotate import text_extent
    from typehaus.emit.draw.typography import model_in_per_pt

    per_pt = model_in_per_pt(scale)
    width, height = (v * per_pt for v in text_extent(node.text or "", node.height_pt))
    (u0, z0), (u1, z1) = node.p0, node.p1
    if abs(z1 - z0) > abs(u1 - u0):  # vertical: rotated label left of the line
        u, z = u0 + node.offset, (z0 + z1) / 2.0 + node.text_along
        return (u - height, z - width / 2.0, u, z + width / 2.0)
    u, z = (u0 + u1) / 2.0 + node.text_along, z0 + node.offset
    return (u - width / 2.0, z, u + width / 2.0, z + height)


def into_crop(point, crop, clamp: bool = True):
    """A layer anchor resolves at its wall's mid-height, often far outside a junction crop;
    the layer runs the wall's height, so slide it into the crop. Off the crop across: None."""
    if crop is None:
        return point
    (cu0, cz0), (cu1, cz1) = (crop[0].xy_m, crop[1].xy_m)
    u, z = point[0] * M_PER_IN, point[1] * M_PER_IN
    if not min(cu0, cu1) <= u <= max(cu0, cu1):
        return None
    if min(cz0, cz1) <= z <= max(cz0, cz1):
        return point
    if not clamp:
        return None
    span = abs(cz1 - cz0)  # off the caption below and the ladder's head above
    lo, hi = min(cz0, cz1) + 0.3 * span, max(cz0, cz1) - 0.15 * span
    return (point[0], min(max(z, lo), hi) / M_PER_IN)
