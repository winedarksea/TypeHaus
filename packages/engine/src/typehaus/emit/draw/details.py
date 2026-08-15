"""Transition details — live-cut junction drawings + editable annotations (→ 11b).

A transition detail is a DETAIL ``Slice`` cutting the live ResolvedModel through
``build_section`` with a derived ``JointPlan`` (per-layer laps + treatment fills), overlaid
with authored ``DetailAnnotation`` elements. One detail is scaffolded per distinct bound
condition key; authored ``Slice.condition_key`` suppresses that key's auto-scaffold.

Annotations are anchored ``(element uid, face role) + 2D slice-frame offset``; an unresolvable
anchor degrades to a ``detail.anchor_unresolved`` finding + error marker, never silent staleness.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_anchors import _wall_anchor, resolve_anchor
from typehaus.emit.draw.detail_derive import (
    DerivedDetail,
    _host_wall,
    _junction_z,
    _wall_u_extent,
    derive_detail_slices,
    detail_index,
)
from typehaus.emit.draw.joints import build_joint_plan
from typehaus.emit.draw.scene import Leader, Scene, Text
from typehaus.emit.draw.section import build_section
from typehaus.findings import Finding
from typehaus.model.views import Slice
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

# ``derive_detail_slices`` / ``detail_index`` moved to ``detail_derive`` and
# ``resolve_anchor`` to ``detail_anchors``; they are re-exported here (alongside
# ``detail_payload``, defined below) because this module is the name the server, the CLI
# and the tests import a detail from.
__all__ = [
    "DerivedDetail",
    "build_authored_detail_scene",
    "build_detail",
    "derive_detail_slices",
    "detail_index",
    "detail_payload",
    "resolve_anchor",
]

def _annotation_specs(model: ResolvedModel, derived: DerivedDetail) -> list[dict]:
    authored = [a for a in model.plan.elements_of_kind("DetailAnnotation")
                if getattr(a, "condition_key", None) == derived.key]
    specs = []
    for a in authored:
        specs.append({
            "uid": a.uid or None, "tag": a.tag, "kind": a.kind, "anchor_uid": a.anchor_uid,
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

    # ``build_section`` stamps an oversized slice tag above the crop; the derived
    # detail's own title block (below) carries the identity, so drop the duplicate
    # rather than let a 40-character tag sprawl across the top of the drawing.
    tag_text = derived.view.tag
    scene = scene.model_copy(update={"nodes": tuple(
        n for n in scene.nodes
        if not (isinstance(n, Text) and n.content == tag_text))})

    # Detail components (grade, soil, perimeter drain) go in *behind* the cut geometry —
    # they are the context the junction sits in, not something drawn over it.
    context = _detail_components(model, derived)
    if context:
        scene = scene.model_copy(update={"nodes": tuple(context) + scene.nodes})

    # Overlay-driven flashings/gutter/gaskets go *over* the cut — they are sheet metal
    # and sealant applied at the junction, not context behind it.
    overlay = _overlay_components(model, derived)
    if overlay:
        scene = scene.model_copy(update={"nodes": scene.nodes + tuple(overlay)})

    nodes, findings = _annotation_nodes(model, derived, scene)
    if nodes:
        scene = scene.model_copy(update={"nodes": scene.nodes + tuple(nodes)})

    # Dimension strings live *in* the drawing, measured off the resolved layers.
    dims = _dimension_nodes(model, derived)
    if dims:
        scene = scene.model_copy(update={"nodes": scene.nodes + tuple(dims)})

    # Legend / title block sit *around* the drawing — each placed on a clear side of
    # the current scene bounds so nothing overprints the cut or its callouts.
    chrome = _chrome(model, derived, scene)
    if chrome:
        scene = scene.model_copy(update={"nodes": scene.nodes + tuple(chrome)})

    notes = _notes_lines(model, derived)
    if notes:
        scene = scene.model_copy(update={"notes": tuple(notes)})
    return scene, findings


def build_authored_detail_scene(model: ResolvedModel, view: Slice) -> Scene:
    """Authored DETAIL Slice → scene, with the authored-slice detail vocabulary over the cut.

    Authored Slices go straight through ``build_section``, which bypasses the derived
    detail-component machinery. A hand-authored sauna floor section still wants the liner
    base, thermal break and room-scale vocabulary the derived path dispatches; a breezeway
    cross section wants its drainage wedges, weeping channels and gasketed fixings. Each
    overlay self-gates on its own subject being in the cut, so a detail that is neither is
    byte-identical to the plain ``build_section`` output and nothing here mutates
    construction geometry.
    """
    from typehaus.emit.draw.detail_components import (
        breezeway_overlay_for_slice,
        ridge_overlay_for_slice,
        sauna_overlay_for_slice,
        shower_overlay_for_slice,
    )

    scene = build_section(model, view)
    for recipe in (sauna_overlay_for_slice, breezeway_overlay_for_slice,
                   shower_overlay_for_slice, ridge_overlay_for_slice):
        overlay = recipe(model, view)
        if overlay:
            scene = scene.model_copy(update={"nodes": scene.nodes + tuple(overlay)})
    return scene


def _detail_components(model: ResolvedModel, derived: DerivedDetail) -> list:
    """Derived 2D detail components for this junction, or nothing if it has none."""
    from typehaus.emit.draw.detail_components import build_below_grade_components
    from typehaus.emit.draw.detail_components.geometry import condition_walls

    crop = derived.view.crop
    if crop is None:
        return []
    window = (crop[0].xy_m, crop[1].xy_m)
    out: list = []
    for wall in condition_walls(model, derived.condition):
        if not wall.is_foundation:
            continue
        out.extend(build_below_grade_components(model, wall, window,
                                                derived.direction, derived.station))
    return out


def _overlay_components(model: ResolvedModel, derived: DerivedDetail) -> list:
    """Per-detail vocabulary dispatched off ``Transition.overlay`` (recipe id)."""
    from typehaus.emit.draw.detail_components import build_overlay_components

    return build_overlay_components(model, derived)


def _dimension_nodes(model: ResolvedModel, derived: DerivedDetail) -> list:
    from typehaus.emit.draw.detail_components import dimension_strings

    crop = derived.view.crop
    if crop is None:
        return []
    return dimension_strings(model, derived, (crop[0].xy_m, crop[1].xy_m),
                             derived.direction, derived.station)


def _chrome(model: ResolvedModel, derived: DerivedDetail, scene: Scene) -> list:
    """Material legend (below), notes column (right), title block (above).

    Placement is measured off the current scene bounds — including the width text
    occupies — so the legend, notes and title each clear the cut and its callouts
    instead of overprinting them.
    """
    from typehaus.emit.draw.detail_components import material_legend
    from typehaus.emit.draw.pdf_writer import _scene_bounds

    crop = derived.view.crop
    if crop is None:
        return []
    bounds = _scene_bounds(scene)
    if bounds is None:
        (cu0, cz0), (cu1, cz1) = (crop[0].xy_m, crop[1].xy_m)
        bounds = (cu0 / M_PER_IN, cz0 / M_PER_IN, cu1 / M_PER_IN, cz1 / M_PER_IN)
    min_u, min_z, max_u, max_z = bounds
    span = max(max_u - min_u, max_z - min_z)
    margin = max(4.0, span * 0.03)

    out: list = []
    out.extend(_title_block(model, derived, min_u, max_z + margin))
    out.extend(material_legend(model, derived, min_u, min_z - margin))
    return out


def _title_block(model: ResolvedModel, derived: DerivedDetail, u: float,
                 z: float) -> list:
    """Project/attribution title, stacked upward from ``z`` so it clears the drawing."""
    project = model.plan.project
    tr = derived.transition
    title = (tr.tag if tr is not None else derived.view.title) or derived.key
    overlay = getattr(tr, "overlay", "") or ""
    # bottom → top; anchors advance upward so every line sits above the cut.
    lines = [
        ("Type:Haus — derived transition detail", 1.4),
        (f"{title}  ·  {overlay}".strip().rstrip(" ·"), 2.0),
        (project.name, 3.2),
    ]
    out: list = []
    y = z
    for content, height in lines:
        out.append(Text(anchor=(u, y), content=content, height=height,
                        layer="A-ANNO-TEXT"))
        y += height * 2.4
    return out


_NOTES_WRAP = 42


def _notes_path(model: ResolvedModel, derived: DerivedDetail):
    """Absolute path of the detail's ``Transition.notes`` markdown, or None."""
    tr = derived.transition
    rel = getattr(tr, "notes", None) if tr is not None else None
    if not rel:
        return None
    root = getattr(model.plan, "source_root", None)
    if not root:
        return None
    from pathlib import Path

    path = Path(root) / rel
    return path if path.exists() else None


def _notes_lines(model: ResolvedModel, derived: DerivedDetail) -> list[str]:
    """Wrapped note lines for ``Scene.notes`` — outside the drawing's coordinate space."""
    path = _notes_path(model, derived)
    return _load_markdown_notes(path) if path is not None else []


def _load_markdown_notes(path) -> list[str]:
    """Front-matter-stripped, bulleted, wrapped note lines (port of detail_utils)."""
    import textwrap

    raw = path.read_text(encoding="utf-8").splitlines()
    i = 0
    if raw and raw[0].strip() == "---":
        i = 1
        while i < len(raw) and raw[i].strip() != "---":
            i += 1
        i = min(i + 1, len(raw))

    out: list[str] = ["NOTES:"]
    for line in raw[i:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            # The column already carries a "NOTES:" header; markdown headings would
            # only duplicate it.
            continue
        if stripped.startswith(("- ", "* ")):
            body = stripped[2:].strip()
            wrapped = textwrap.wrap(body, width=_NOTES_WRAP) or [body]
            out.append(f"• {wrapped[0]}")
            out.extend(f"  {w}" for w in wrapped[1:])
            continue
        out.extend(textwrap.wrap(stripped, width=_NOTES_WRAP) or [stripped])
    return out


def _frame(derived: DerivedDetail):
    """Return a (world_xy) -> (u_in, z_in) mapper for the detail's cut frame.

    Must match the cutter's convention (``section.ring_cut_intervals``): for a cut plane at
    x = const (``direction == "y"``) the in-section coordinate is world **y**, and vice
    versa. Getting this backwards puts every annotation anchor on the wrong axis.
    """
    direction = derived.direction

    def to_uz(x: float, y: float, z: float) -> tuple[float, float]:
        u = y if direction == "y" else x
        return (u / M_PER_IN, z / M_PER_IN)

    return to_uz


def _annotation_nodes(model: ResolvedModel, derived: DerivedDetail, scene: Scene = None):
    """Authored DetailAnnotations for this key, else seed nodes from overlay + notes.

    ``scene`` is the cut so far — seed callouts dodge against the labels already in it
    (the layer-label ladders) so the two stacks never overprint each other.
    """
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
            ox = ann.offset.x.meters / M_PER_IN if ann.offset is not None else 0.0
            oy = ann.offset.y.meters / M_PER_IN if ann.offset is not None else 0.0
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
        nodes.extend(_seed_nodes(model, derived, scene))
    return nodes, findings


def _point_anchor(point):
    from typehaus.emit.draw.scene import NamedPoint

    return NamedPoint(xy=point)


ANNOTATION_TEXT_H = 1.6  # model inches; the writer converts to points at the drawn scale


def _face_role(face: str) -> str:
    """``Continuity`` face names (``"sheathing-ext"``) → an anchor role (``layer:sheathing:out``).

    Continuity claims are authored against a face — layer name plus which side of it — while
    the anchor vocabulary spells the side separately. Without this translation every seed
    callout degrades to unanchored text.
    """
    for suffix, side in (("-ext", "out"), ("-int", "in")):
        if face.endswith(suffix):
            return f"layer:{face[:-len(suffix)]}:{side}"
    return f"layer:{face}:out"


def _seed_nodes(model: ResolvedModel, derived: DerivedDetail,
                scene: Scene = None) -> list:
    """Read-only seed annotations (uid=None) leadered to the layers they describe.

    A continuity claim is *about* a named face, so the seed points at that face rather than
    stacking raw text beside the drawing. The markdown behind ``Transition.notes`` belongs in
    the notes column, not in a callout — only its title is worth a leader.

    Layout goes through :mod:`~typehaus.emit.draw.annotate`: long single-line claims wrap
    at ``LEADER_WRAP_COLUMNS``, the column placer grows rows to fit the wrapped text, and
    the whole stack dodges the layer-label ladders already in ``scene``.
    """
    from typehaus.emit.draw.annotate import (
        LabelSpec,
        dodge,
        leader_box,
        place_column,
        wrap_label,
    )

    tr = derived.transition
    if tr is None:
        return []
    crop = derived.view.crop
    (cu0, cz0), (cu1, cz1) = (crop[0].xy_m, crop[1].xy_m)
    frame = _frame(derived)
    wall = _host_wall(model, derived.condition)

    # Callouts stack down a column just outboard of the *wall*, not of the crop: the crop's
    # outboard margin is reserved for what gets drawn there (overhang, grade, drainage), and
    # hanging text off its far edge strands the notes in empty space.
    if wall is not None:
        _, wall_u_hi = _wall_u_extent(wall, derived.direction, derived.station,
                                      (cu0 + cu1) / 2.0)
    else:
        wall_u_hi = (cu0 + cu1) / 2.0
    text_x = wall_u_hi / M_PER_IN + 5.0
    top_y = cz1 / M_PER_IN - 2.0
    step = ANNOTATION_TEXT_H * 2.4

    # A layer anchor resolves at its wall's mid-height, which for a storey-tall wall is far
    # outside a junction crop. What the callout is about is the layer *at the junction*, so
    # pin the elevation there and only take the layer's position across the wall depth.
    junction_z = _junction_z(model, derived.condition, wall) / M_PER_IN if wall else None
    # Either side of a junction may own the layer being claimed — at a foundation detail the
    # sheathing and WRB belong to the framed wall above, not the concrete below. An opening
    # condition names no wall at all, so its host carries every claim.
    candidates = [w for w in (model.wall(t) for t in derived.condition.element_tags)
                  if w is not None]
    if not candidates and wall is not None:
        candidates = [wall]

    def _anchor(face_name):
        for candidate in candidates:
            point, err = _wall_anchor(candidate, _face_role(face_name), frame)
            if err is None:
                return (point[0], junction_z if junction_z is not None else point[1])
        return None

    entries: list = []
    for cont in getattr(tr, "continuity", ()):
        content = wrap_label(
            f"{cont.control} continuity — {cont.from_face} → {cont.to_face}")
        entries.append(LabelSpec(text=content, target=_anchor(cont.from_face)))
    placed = place_column(entries, x=text_x, z_top=top_y, step=step,
                          height=ANNOTATION_TEXT_H, align="left")
    fixed = tuple(leader_box(n) for n in (scene.nodes if scene is not None else ())
                  if isinstance(n, Leader))
    nodes: list = []
    for label in dodge(placed, fixed=fixed):
        if label.spec.target is None:
            nodes.append(Text(anchor=label.at, content=label.spec.text,
                              height=label.height, layer="A-ANNO-TEXT", uid=None))
        else:
            nodes.append(Leader(anchor=_point_anchor(label.spec.target), at=label.at,
                                to=label.spec.target, text=label.spec.text,
                                height=label.height, uid=None))
    if getattr(tr, "overlay", None):
        nodes.append(Text(anchor=(cu0 / M_PER_IN, cz0 / M_PER_IN - 4.0),
                          content=f"{tr.tag}  ·  {tr.overlay}", height=ANNOTATION_TEXT_H,
                          layer="A-ANNO-TEXT", uid=None))
    return nodes


def detail_payload(model: ResolvedModel, key: str) -> dict | None:
    """Scene + annotations + notes for one detail key (server ``/detail`` + Pyodide)."""
    derived = next((d for d in derive_detail_slices(model) if d.key == key), None)
    if derived is None:
        return None
    scene, findings = build_detail(model, derived)
    tr = derived.transition
    notes_path = _notes_path(model, derived)
    return {
        "key": key,
        "scene": scene.model_dump(mode="json"),
        "annotations": _annotation_specs(model, derived),
        "notes": getattr(tr, "notes", None) if tr is not None else None,
        "notes_markdown": (notes_path.read_text(encoding="utf-8")
                          if notes_path is not None else None),
        "findings": [{"check_id": f.check_id, "message": f.message} for f in findings],
    }
