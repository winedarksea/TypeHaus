"""Transition details — live-cut junction drawings + editable annotations (→ 11b).

A transition detail is a DETAIL ``Slice`` cutting the live ResolvedModel through
``build_section`` with a derived ``JointPlan`` (per-layer laps + treatment fills), overlaid
with authored ``DetailAnnotation`` elements. One detail is scaffolded per distinct bound
condition key; authored ``Slice.condition_key`` suppresses that key's auto-scaffold.

Annotations are anchored ``(element uid, face role) + 2D slice-frame offset``; an unresolvable
anchor degrades to a ``detail.anchor_unresolved`` finding + error marker, never silent staleness.
"""

from __future__ import annotations

import hashlib
import math
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
    """The wall the condition is about — named directly, or via its opening's host.

    ``opening_perimeter`` conditions carry the *opening's* tag, so the wall has to be
    reached through ``ResolvedOpening.host_wall``; without that hop every opening
    condition silently derived no detail at all.
    """
    from typehaus.emit.draw.detail_components.geometry import condition_walls

    walls = condition_walls(model, cond)
    return walls[0] if walls else None


def _condition_opening(model: ResolvedModel, cond: BoundaryCondition):
    from typehaus.emit.draw.detail_components.geometry import condition_opening

    return condition_opening(model, cond)


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
            # roof_ridge conditions carry a roof and a beam, never a wall — the cut frame
            # comes from the ridge member instead.
            if cond.kind.value == "roof_ridge":
                derived = _build_ridge_derived(model, cond, tr)
                if derived is not None:
                    seen.add(cond.key)
                    out.append(derived)
            continue
        seen.add(cond.key)
        derived = _build_derived(model, cond, tr, wall)
        if derived is not None:
            out.append(derived)
    out.sort(key=lambda d: d.key)
    return out


# Per junction kind: how far the crop reaches (metres) below/above the junction plane, and
# beyond the wall's inboard/outboard faces. A detail is a close-up — the window has to hold
# the junction and the things drawn around it (footing, drain and grade below a foundation;
# the overhang and gutter outboard of an eave) and nothing else, or it reads as a sliver
# floating in white space.
_CROP_WINDOWS = {
    #                     below,  above,  inboard, outboard
    # wall_roof reaches further above the junction (the plate top) since eave_z_m became
    # the deck plane: the rafter rises ~0.27 m above the plate before the roof stack starts.
    "wall_roof":         (0.75,   0.75,   0.30,    0.35),
    "wall_foundation":   (1.30,   0.90,   0.55,    0.90),
    "wall_slab":         (1.00,   0.70,   0.55,    0.70),
    "storey_stack":      (0.55,   0.55,   0.25,    0.25),
    "stack_width_change": (0.50,  0.50,   0.25,    0.25),
    "assembly_change":   (0.50,   0.50,   0.30,    0.30),
    # opening_perimeter measures below from the *sill* and above from the *head* (the crop
    # holds the whole opening); the u margins clear the frame's interior/exterior returns.
    "opening_perimeter": (0.45,   0.45,   0.25,    0.25),
    # roof_ridge has no wall faces: the u margins measure symmetrically off the ridge line,
    # wide enough to hold the beam, its hangers and the first stretch of rafter each side.
    "roof_ridge":        (0.90,   0.45,   0.75,    0.75),
}
_DEFAULT_WINDOW = (0.50, 0.50, 0.25, 0.25)


def _wall_u_extent(wall, direction: str, station: float,
                   fallback_center: float) -> tuple[float, float]:
    """The wall's inboard/outboard face positions in section coordinates."""
    from typehaus.emit.draw.section import _ring_cut_intervals

    bounds: list[float] = []
    for layer in wall.layers:
        for (u0, u1) in _ring_cut_intervals(layer.polygon, direction, station):
            bounds.extend((u0, u1))
    if not bounds:
        half = wall.thickness_m / 2.0
        return fallback_center - half, fallback_center + half
    return min(bounds), max(bounds)


def _junction_z(model, cond, wall) -> float:
    """The elevation the detail is *about* — what the crop's below/above measure from.

    For the stacked kinds that is the *shared* plane between the two elements, i.e. the top
    of the lower one. Using the host wall's own base instead put the foundation detail a
    storey below its own junction, showing the footing and nothing of the wall it carries.
    An opening's plane is its own mid-height (the crop then reaches past sill and head);
    a ridge's is the ridge elevation itself, wall or no wall.
    """
    kind = cond.kind.value
    if kind == "roof_ridge":
        roof = next((r for r in model.roofs if r.tag in cond.element_tags), None)
        if roof is not None:
            return roof.ridge_z_m
    if kind == "opening_perimeter" and wall is not None:
        opening = _condition_opening(model, cond)
        if opening is not None:
            return wall.z0_m + opening.sill_m + opening.height_m / 2.0
    top = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    if kind == "wall_roof":
        return top
    if kind in ("wall_foundation", "storey_stack", "stack_width_change", "assembly_change"):
        walls = [w for w in (model.wall(tag) for tag in cond.element_tags) if w is not None]
        if len(walls) >= 2:
            lower = min(walls, key=lambda w: w.z0_m)
            return lower.z1_m
        return top
    if kind == "wall_slab":
        return wall.z0_m
    return (wall.z0_m + top) / 2.0


def _build_derived(model, cond, tr, wall) -> DerivedDetail | None:
    (x0, y0), (x1, y1) = wall.axis
    opening = (_condition_opening(model, cond)
               if cond.kind.value == "opening_perimeter" else None)
    if opening is not None:
        # Cut through the opening, not the wall midpoint: the head and sill this detail is
        # about only exist in the plane that actually crosses the opening.
        length = math.hypot(x1 - x0, y1 - y0)
        t = opening.center_along_m / length if length > 1e-9 else 0.5
        mx, my = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
    else:
        mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    if dx >= dy:
        # wall runs along x → cut perpendicular is a plane at x=const (u = world y).
        direction, station, center_u = "y", mx, my
    else:
        direction, station, center_u = "x", my, mx

    below, above, inboard, outboard = _CROP_WINDOWS.get(cond.kind.value, _DEFAULT_WINDOW)
    if opening is not None:
        # The z-window holds the whole opening: below measures off the sill, above off the
        # head, so a full-height door and a high awning window both crop to their subject.
        sill_z = wall.z0_m + opening.sill_m
        z0, z1 = sill_z - below, sill_z + opening.height_m + above
    else:
        junction_z = _junction_z(model, cond, wall)
        z0, z1 = junction_z - below, junction_z + above

    # Measure the margins off the wall's real faces, not its axis: a wall aligned on its
    # sheathing plane is nowhere near centred on its axis, so an axis-centred window leaves
    # a wide empty band on one side and clips the drawing on the other.
    u_lo, u_hi = _wall_u_extent(wall, direction, station, center_u)
    view = Slice(
        uid="", tag=f"D-{_key_slug(cond.key)}", kind=SliceKind.DETAIL,
        title=(tr.tag if tr is not None else cond.key),
        cut_origin=pt(m(station if direction == "y" else center_u),
                      m(center_u if direction == "y" else station)),
        cut_direction=direction,
        crop=(pt(m(u_lo - inboard), m(z0)), pt(m(u_hi + outboard), m(z1))),
    )
    return DerivedDetail(key=cond.key, condition=cond, transition=tr, view=view,
                         direction=direction, station=station)


def _build_ridge_derived(model, cond, tr) -> DerivedDetail | None:
    """A ridge detail cut perpendicular to the ridge member at its midpoint.

    The frame comes from the resolved ridge-beam member (falling back to the roof's own
    ridge line), and the crop is a symmetric window about the ridge line at the ridge
    elevation — there are no wall faces to measure margins from.
    """
    from typehaus.emit.draw.detail_components.ridge import ridge_beam_member

    roof = next((r for r in model.roofs if r.tag in cond.element_tags), None)
    if roof is None:
        return None
    member = ridge_beam_member(roof)
    if member is not None:
        (x0, y0), (x1, y1) = member.p0, member.p1
    else:
        xs = [p[0] for p in roof.footprint]
        ys = [p[1] for p in roof.footprint]
        if roof.ridge_direction == "x":
            (x0, y0), (x1, y1) = ((min(xs), (min(ys) + max(ys)) / 2.0),
                                  (max(xs), (min(ys) + max(ys)) / 2.0))
        else:
            (x0, y0), (x1, y1) = (((min(xs) + max(xs)) / 2.0, min(ys)),
                                  ((min(xs) + max(xs)) / 2.0, max(ys)))
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    if dx >= dy:
        direction, station, center_u = "y", mx, my
    else:
        direction, station, center_u = "x", my, mx
    below, above, inboard, outboard = _CROP_WINDOWS.get("roof_ridge", _DEFAULT_WINDOW)
    ridge_z = roof.ridge_z_m
    view = Slice(
        uid="", tag=f"D-{_key_slug(cond.key)}", kind=SliceKind.DETAIL,
        title=(tr.tag if tr is not None else cond.key),
        cut_origin=pt(m(station if direction == "y" else center_u),
                      m(center_u if direction == "y" else station)),
        cut_direction=direction,
        crop=(pt(m(center_u - inboard), m(ridge_z - below)),
              pt(m(center_u + outboard), m(ridge_z + above))),
    )
    return DerivedDetail(key=cond.key, condition=cond, transition=tr, view=view,
                         direction=direction, station=station)


def _key_slug(key: str) -> str:
    slug = key.replace(":", "-").replace("|", "-").replace("*", "x")
    if len(slug) <= 40:
        return slug
    # Two long keys can share their first 40 characters (the PORCH_RAILING pair did),
    # and a shared slug means one render filename silently overwriting the other.
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:6]
    return f"{slug[:33]}-{digest}"


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
        bounds = (cu0 * M_TO_IN, cz0 * M_TO_IN, cu1 * M_TO_IN, cz1 * M_TO_IN)
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

    Must match the cutter's convention (``section._ring_cut_intervals``): for a cut plane at
    x = const (``direction == "y"``) the in-section coordinate is world **y**, and vice
    versa. Getting this backwards puts every annotation anchor on the wrong axis.
    """
    direction = derived.direction

    def to_uz(x: float, y: float, z: float) -> tuple[float, float]:
        u = y if direction == "y" else x
        return (u * M_TO_IN, z * M_TO_IN)

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
    text_x = wall_u_hi * M_TO_IN + 5.0
    top_y = cz1 * M_TO_IN - 2.0
    step = ANNOTATION_TEXT_H * 2.4

    # A layer anchor resolves at its wall's mid-height, which for a storey-tall wall is far
    # outside a junction crop. What the callout is about is the layer *at the junction*, so
    # pin the elevation there and only take the layer's position across the wall depth.
    junction_z = _junction_z(model, derived.condition, wall) * M_TO_IN if wall else None
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
        nodes.append(Text(anchor=(cu0 * M_TO_IN, cz0 * M_TO_IN - 4.0),
                          content=f"{tr.tag}  ·  {tr.overlay}", height=ANNOTATION_TEXT_H,
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
    exact = next((l for l in wall.layers if l.name == name), None)
    if exact is not None:
        return exact
    control = _ROLE_CONTROL.get(name)
    if control is None:
        return None
    # Outermost layer carrying that control: the plane a transition laps to.
    matching = [l for l in wall.layers if control in l.control]
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
