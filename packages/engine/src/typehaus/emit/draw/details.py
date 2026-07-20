"""Transition details — live-cut junction drawings + editable annotations (→ 11b).

A transition detail is a DETAIL ``Slice`` cutting the live ResolvedModel through
``build_section`` with a derived ``JointPlan`` (per-layer laps + treatment fills), overlaid
with authored ``DetailAnnotation`` elements. One detail is scaffolded per distinct bound
condition key; authored ``Slice.condition_key`` suppresses that key's auto-scaffold.

Annotations are anchored ``(element uid, face role) + 2D slice-frame offset``; an unresolvable
anchor degrades to a ``detail.anchor_unresolved`` finding + error marker, never silent staleness.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from typehaus.emit.draw.joints import build_joint_plan
from typehaus.emit.draw.scene import Leader, Scene, Text
from typehaus.emit.draw.section import build_section
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import SliceKind
from typehaus.model.patterns import matches
from typehaus.model.views import Slice
from typehaus.quantities import m, pt
from typehaus.resolve.model import BoundaryCondition, ResolvedModel

M_TO_IN = 39.37007874015748


@dataclass(frozen=True)
class DerivedDetail:
    """One scaffolded transition detail: a cut slice + its bound condition/transition."""

    key: str
    condition: BoundaryCondition
    transition: object | None  # model.views.Transition, if a binding matched
    view: Slice
    direction: str
    station: float


def _matched_transition(model: ResolvedModel, cond: BoundaryCondition):
    for tr in model.plan.library.transitions:
        if matches(tr.condition_pattern, cond.key):
            return tr
    return None


def _host_wall(model: ResolvedModel, cond: BoundaryCondition):
    for tag in cond.element_tags:
        w = model.wall(tag)
        if w is not None:
            return w
    return None


def derive_detail_slices(model: ResolvedModel) -> list[DerivedDetail]:
    """One derived DETAIL slice per distinct bound condition key (skip authored-claimed keys).

    The cut plane runs perpendicular to the host wall at its midpoint; the crop is a junction
    z-window × u-window sized to the junction kind.
    """
    claimed = {
        s.condition_key for s in model.plan.elements_of_kind("Slice")
        if getattr(s, "condition_key", None)
    }
    out: list[DerivedDetail] = []
    seen: set[str] = set()
    for cond in model.conditions:
        if cond.key in seen or cond.key in claimed:
            continue
        tr = _matched_transition(model, cond)
        if tr is None:
            continue  # unbound conditions are the coverage check's concern, not a detail
        wall = _host_wall(model, cond)
        if wall is None:
            continue
        seen.add(cond.key)
        derived = _build_derived(model, cond, tr, wall)
        if derived is not None:
            out.append(derived)
    out.sort(key=lambda d: d.key)
    return out


def _build_derived(model, cond, tr, wall) -> DerivedDetail | None:
    (x0, y0), (x1, y1) = wall.axis
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    if dx >= dy:
        # wall runs along x → cut perpendicular is a plane at x=const (u = world y).
        direction, station, center_u = "y", mx, my
    else:
        direction, station, center_u = "x", my, mx
    top = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    kind = cond.kind.value
    if kind == "wall_roof":
        z0, z1 = top - 1.0, top + 0.5
    elif kind in ("wall_foundation", "wall_slab"):
        z0, z1 = wall.z0_m - 0.6, wall.z0_m + 0.9
    else:
        z0, z1 = wall.z0_m - 0.3, top + 0.3
    half_u = 0.9  # ~3 ft window around the wall line
    view = Slice(
        uid="", tag=f"D-{_key_slug(cond.key)}", kind=SliceKind.DETAIL,
        title=(tr.tag if tr is not None else cond.key),
        cut_origin=pt(m(station if direction == "y" else center_u),
                      m(center_u if direction == "y" else station)),
        cut_direction=direction,
        crop=(pt(m(center_u - half_u), m(z0)), pt(m(center_u + half_u), m(z1))),
    )
    return DerivedDetail(key=cond.key, condition=cond, transition=tr, view=view,
                         direction=direction, station=station)


def _key_slug(key: str) -> str:
    return key.replace(":", "-").replace("|", "-").replace("*", "x")[:40]


def detail_index(model: ResolvedModel) -> list[dict]:
    """Pure-data index of scaffolded details (server ``/details`` + Pyodide, offline-safe)."""
    out = []
    for d in derive_detail_slices(model):
        tr = d.transition
        authored = any(
            getattr(a, "condition_key", None) == d.key
            for a in model.plan.elements_of_kind("DetailAnnotation")
        )
        out.append({
            "key": d.key,
            "kind": d.condition.kind.value,
            "title": d.view.title or d.key,
            "transition": tr.tag if tr is not None else None,
            "overlay": getattr(tr, "overlay", None) if tr is not None else None,
            "elements": list(d.condition.element_tags),
            "state": "authored" if authored else "seed",
        })
    return out


def detail_payload(model: ResolvedModel, key: str) -> dict | None:
    """Scene + annotations + notes for one detail key (server ``/detail`` + Pyodide)."""
    derived = next((d for d in derive_detail_slices(model) if d.key == key), None)
    if derived is None:
        return None
    scene, findings = build_detail(model, derived)
    tr = derived.transition
    return {
        "key": key,
        "scene": scene.model_dump(mode="json"),
        "annotations": _annotation_specs(model, derived),
        "notes": getattr(tr, "notes", None) if tr is not None else None,
        "findings": [{"check_id": f.check_id, "message": f.message} for f in findings],
    }


def _annotation_specs(model: ResolvedModel, derived: DerivedDetail) -> list[dict]:
    authored = [a for a in model.plan.elements_of_kind("DetailAnnotation")
                if getattr(a, "condition_key", None) == derived.key]
    specs = []
    for a in authored:
        specs.append({
            "uid": a.uid or None, "kind": a.kind, "anchor_uid": a.anchor_uid,
            "anchor_face": a.anchor_face, "text": a.text,
            "offset": [a.offset.x.meters, a.offset.y.meters] if a.offset is not None else None,
            "state": "authored",
        })
    return specs


def build_detail(model: ResolvedModel, derived: DerivedDetail) -> tuple[Scene, list[Finding]]:
    """Build the detail scene: model cut + joint treatments + annotation nodes.

    Returns the scene and any anchor-resolution findings.
    """
    joints = build_joint_plan(model, derived.condition, derived.transition,
                              derived.direction, derived.station)
    scene = build_section(model, derived.view, joints=joints)
    nodes, findings = _annotation_nodes(model, derived)
    if nodes:
        scene = scene.model_copy(update={"nodes": scene.nodes + tuple(nodes)})
    return scene, findings


def _frame(derived: DerivedDetail):
    """Return a (world_xy) -> (u_in, z_in) mapper for the detail's cut frame."""
    direction = derived.direction

    def to_uz(x: float, y: float, z: float) -> tuple[float, float]:
        u = x if direction == "y" else y
        return (u * M_TO_IN, z * M_TO_IN)

    return to_uz


def _annotation_nodes(model: ResolvedModel, derived: DerivedDetail):
    """Authored DetailAnnotations for this key, else seed nodes from overlay + notes."""
    authored = [a for a in model.plan.elements_of_kind("DetailAnnotation")
                if getattr(a, "condition_key", None) == derived.key]
    findings: list[Finding] = []
    nodes: list = []
    frame = _frame(derived)
    if authored:
        for ann in authored:
            point, err = resolve_anchor(model, frame, ann.anchor_uid, ann.anchor_face)
            if err is not None:
                findings.append(err)
            ox = ann.offset.x.meters * M_TO_IN if ann.offset is not None else 0.0
            oy = ann.offset.y.meters * M_TO_IN if ann.offset is not None else 0.0
            at = (point[0] + ox, point[1] + oy)
            if ann.kind == "leader":
                nodes.append(Leader(anchor=_point_anchor(point), at=at, to=point,
                                    text=ann.text, uid=ann.uid or None))
            else:
                nodes.append(Text(anchor=at, content=ann.text, height=1.5,
                                  layer="A-ANNO-TEXT", uid=ann.uid or None))
            if err is not None:
                nodes.append(Text(anchor=at, content="⚠ anchor?", height=1.5,
                                  layer="A-ANNO-TEXT", uid=ann.uid or None))
    else:
        nodes.extend(_seed_nodes(model, derived))
    return nodes, findings


def _point_anchor(point):
    from typehaus.emit.draw.scene import NamedPoint

    return NamedPoint(xy=point)


def _seed_nodes(model: ResolvedModel, derived: DerivedDetail) -> list:
    """Read-only seed annotations (uid=None) from the transition overlay id + continuity."""
    tr = derived.transition
    if tr is None:
        return []
    crop = derived.view.crop
    (cu0, _), (cu1, cz1) = (crop[0].xy_m, crop[1].xy_m)
    x = cu1 * M_TO_IN + 6.0
    y = cz1 * M_TO_IN
    nodes: list = []
    lines = []
    if getattr(tr, "overlay", None):
        lines.append(f"[{tr.overlay}]")
    for cont in getattr(tr, "continuity", ()):
        lines.append(f"{cont.control}: {cont.from_face}→{cont.to_face}")
    if getattr(tr, "notes", None):
        lines.append(str(tr.notes))
    for i, line in enumerate(lines):
        nodes.append(Text(anchor=(x, y - i * 3.0), content=line, height=1.5,
                          layer="A-ANNO-TEXT", uid=None))
    return nodes


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
        layer = next((l for l in wall.layers if l.name == name), None)
        if layer is None:
            return frame(mx, my, top), _unresolved(wall.uid, face)
        return _layer_point(layer, wall, frame, side), None
    return frame(mx, my, top), _unresolved(wall.uid, face)


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
