"""Transition details — live-cut junction drawings + editable annotations (→ 11b).

A transition detail is a DETAIL ``Slice`` cutting the live ResolvedModel through
``build_section`` with a derived ``JointPlan`` (per-layer laps + treatment fills), overlaid
with authored ``DetailAnnotation`` elements. One detail is scaffolded per distinct bound
condition key; authored ``Slice.condition_key`` suppresses that key's auto-scaffold.

Annotations are anchored ``(element uid, face role) + 2D slice-frame offset``; an unresolvable
anchor degrades to a ``detail.anchor_unresolved`` finding + error marker, never silent staleness.
"""

from __future__ import annotations

from functools import partial

from typehaus.emit.draw.detail_anchors import resolve_anchor
from typehaus.emit.draw.detail_annotations import (  # noqa: F401 — re-exported
    ANNOTATION_TEXT_PT,
    HOST_ANCHOR,
    _annotation_nodes,
    _dodge_point,
    _face_role,
    _frame,
    _keyed_anchor,
    _keyed_note_nodes,
    _load_markdown_notes,
    _notes_lines,
    _notes_path,
    _seed_nodes,
    _sheet_note_set,
)
from typehaus.emit.draw.detail_derive import (
    DerivedDetail,
    derive_detail_slices,
    detail_index,
)
from typehaus.emit.draw.joints import build_joint_plan
from typehaus.emit.draw.scene import Scene, Text
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
    frame = _detail_frame(model, derived, joints)
    scene = build_section(model, derived.view, joints=joints, frame=frame)

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
    overlay = _overlay_components(model, derived, scene.frame)
    if overlay:
        scene = scene.model_copy(update={"nodes": scene.nodes + tuple(overlay)})

    # Dimension strings live *in* the drawing, measured off the resolved layers; before the
    # keyed bubbles, which dodge them.
    dims = _dimension_nodes(model, derived)
    if dims:
        scene = scene.model_copy(update={"nodes": scene.nodes + tuple(dims)})

    nodes, findings = _annotation_nodes(model, derived, scene)
    if nodes:
        scene = scene.model_copy(update={"nodes": scene.nodes + tuple(nodes)})

    # Legend / title block sit *around* the drawing — each placed on a clear side of
    # the current scene bounds so nothing overprints the cut or its callouts.
    chrome = _chrome(model, derived, scene)
    if chrome:
        scene = scene.model_copy(update={"nodes": scene.nodes + tuple(chrome)})

    notes = _notes_lines(model, derived)
    if notes:
        scene = scene.model_copy(update={"notes": tuple(notes)})
    return scene, findings


def _detail_frame(model: ResolvedModel, derived: DerivedDetail, joints):
    """Choose the card before anything is cut, from ``derived.view.crop``.

    The crop is exactly what the geometry will be clipped to, so it is the drawing's size —
    known without drawing anything, which is what keeps this a single pass.

    A view with no crop has nothing to measure, so it takes the two-pass the module docstring
    describes: cut frameless, measure the *geometry* (never the lettering — that is the whole
    rule), choose, and the caller cuts again with the frame. Deliberate, not an oversight.
    """
    from typehaus.emit.draw.detail_card import card_for_crop
    from typehaus.emit.draw.pdf_writer import geometry_bounds

    crop = derived.view.crop
    if crop is not None:
        (cu0, cz0), (cu1, cz1) = (crop[0].xy_m, crop[1].xy_m)
        u0, z0 = min(cu0, cu1) / M_PER_IN, min(cz0, cz1) / M_PER_IN
        u1, z1 = max(cu0, cu1) / M_PER_IN, max(cz0, cz1) / M_PER_IN
    else:
        bounds = geometry_bounds(build_section(model, derived.view, joints=joints))
        if bounds is None:
            return None
        u0, z0, u1, z1 = bounds
    card = card_for_crop(u1 - u0, z1 - z0, ((u0 + u1) / 2.0, (z0 + z1) / 2.0))
    if derived.part is not None:  # an enlarged head/sill: the sheet's scale, not the card's
        from typehaus.emit.draw.detail_enlarged import enlarged_frame

        card = enlarged_frame(card, (u0 + u1) / 2.0, (z0 + z1) / 2.0)
    return card


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
        eave_overlay_for_slice,
        glazed_roof_overlay_for_slice,
        ridge_overlay_for_slice,
        sauna_overlay_for_slice,
        shower_overlay_for_slice,
    )

    frame = _authored_frame(view)
    scene = build_section(model, view, frame=frame)
    if frame is not None:  # the card is the drawing's identity; the cut's oversized tag is not
        scene = scene.model_copy(update={"nodes": tuple(
            n for n in scene.nodes if not (isinstance(n, Text) and n.content == view.tag))})
    eave = partial(eave_overlay_for_slice, scale=frame.scale if frame is not None else None)
    for recipe in (sauna_overlay_for_slice, glazed_roof_overlay_for_slice,
                   shower_overlay_for_slice, ridge_overlay_for_slice, eave):
        overlay = recipe(model, view)
        if overlay:
            scene = scene.model_copy(update={"nodes": scene.nodes + tuple(overlay)})
    # Strings last: authored anchors read the cut drawn above (C7-E4).
    from typehaus.emit.draw.detail_dimensions import authored_dimension_nodes

    dims = authored_dimension_nodes(model, view, scene)
    if dims:
        scene = scene.model_copy(update={"nodes": scene.nodes + tuple(dims)})
    return scene


def _authored_frame(view: Slice):
    """A true-scale card for an authored detail that states its scale, else ``None``.

    Only a slice that sets ``scale`` gets one, so every older authored detail keeps its
    frameless drawing; the card's ladder picks the scale the crop admits.
    """
    from typehaus.emit.draw.detail_card import card_for_crop

    if "scale" not in view.model_fields_set or view.crop is None:
        return None
    (cu0, cz0), (cu1, cz1) = (view.crop[0].xy_m, view.crop[1].xy_m)
    span_u, span_z = abs(cu1 - cu0) / M_PER_IN, abs(cz1 - cz0) / M_PER_IN
    center = ((cu0 + cu1) / 2.0 / M_PER_IN, (cz0 + cz1) / 2.0 / M_PER_IN)
    return card_for_crop(span_u, span_z, center, notes=False)


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


def _overlay_components(model: ResolvedModel, derived: DerivedDetail, frame=None) -> list:
    """Per-detail vocabulary dispatched off ``Transition.overlay`` (recipe id)."""
    from typehaus.emit.draw.detail_components import build_overlay_components

    return build_overlay_components(
        model, derived, frame.scale if frame is not None else None)


def _dimension_nodes(model: ResolvedModel, derived: DerivedDetail) -> list:
    from typehaus.emit.draw.detail_components import dimension_strings

    crop = derived.view.crop
    if crop is None:
        return []
    return dimension_strings(model, derived, (crop[0].xy_m, crop[1].xy_m),
                             derived.direction, derived.station, derived.part)


def _chrome(model: ResolvedModel, derived: DerivedDetail, scene: Scene) -> list:
    """Title block and material legend — in **paper space**, in the card's own bands.

    Measuring off scene bounds would import the private ``pdf_writer._scene_bounds`` and
    make the drawing's extent depend on its own annotation. Bands cut that loop — a title
    strip is 0.9 paper inches tall because the card says so.

    A frameless scene keeps the old model-space placement, because it has no bands to use.
    """
    from typehaus.emit.draw.detail_components import material_legend
    from typehaus.emit.draw.detail_components.chrome import drawn_materials

    frame = scene.frame
    if frame is not None:
        out: list = []
        title_band = frame.bands.get("title")
        if title_band is not None:
            out.extend(_paper_title_block(model, derived, title_band))
        legend_band = frame.bands.get("legend")
        if legend_band is not None:
            out.extend(material_legend(model, derived, 0.0, 0.0, band=legend_band,
                                       drawn=drawn_materials(scene)))
        return out

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

    out = []
    out.extend(_title_block(model, derived, min_u, max_z + margin))
    out.extend(material_legend(model, derived, min_u, min_z - margin))
    return out


def _detail_title(model: ResolvedModel, derived: DerivedDetail) -> tuple[str, str]:
    tr = derived.transition
    title = (tr.tag if tr is not None else derived.view.title) or derived.key
    overlay = getattr(tr, "overlay", "") or ""
    return title, overlay


def _paper_title_block(model: ResolvedModel, derived: DerivedDetail, band) -> list:
    """Project, detail identity, sheet number, scale and attribution, in the title strip.

    The sheet number and the scale are here because a detail has to be self-identifying:
    NCS puts the scale with the DRAWING and not only in the title block, since a sheet may
    carry several drawings at several scales and a block can state only one. And a detail
    pulled off a pile that cannot say which sheet it is has broken the cross-reference at
    the only end a reader is holding.
    """
    from typehaus.emit.draw.callouts import detail_sheet_numbers

    x, y, _w, h = band
    title, overlay = _detail_title(model, derived)
    sheet = detail_sheet_numbers(model).get(derived.key, "")
    lines = [
        (model.plan.project.name, 13.0),
        (f"{title}  ·  {overlay}".strip().rstrip(" ·"), 8.0),
        (f"SHEET {sheet}" if sheet else "", 7.0),
        ("Type:Haus — derived transition detail", 6.5),
    ]
    out: list = []
    z = y + h
    for content, size_pt in lines:
        if not content:
            continue
        z -= (size_pt + 4.0) / 72.0
        out.append(Text(anchor=(x, z), content=content, height_pt=size_pt,
                        layer="A-ANNO-TEXT", space="paper"))
    return out


def _title_block(model: ResolvedModel, derived: DerivedDetail, u: float,
                 z: float) -> list:
    """Project/attribution title, stacked upward from ``z`` so it clears the drawing."""
    title, overlay = _detail_title(model, derived)
    # bottom → top; anchors advance upward so every line sits above the cut.
    lines = [
        ("Type:Haus — derived transition detail", 1.4),
        (f"{title}  ·  {overlay}".strip().rstrip(" ·"), 2.0),
        (model.plan.project.name, 3.2),
    ]
    out: list = []
    y = z
    for content, height in lines:
        out.append(Text(anchor=(u, y), content=content, height=height,
                        layer="A-ANNO-TEXT"))
        y += height * 2.4
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
