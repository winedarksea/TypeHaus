"""A transition detail's notes and annotation layer: the notes column, keyed bubbles, seed callouts.

Split out of ``details.py`` (500-line limit); ``details`` re-exports what callers import.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_anchors import (
    _wall_anchor,
    dimension_box,
    into_crop,
    resolve_anchor,
)
from typehaus.emit.draw.detail_derive import (
    DerivedDetail,
    _host_wall,
    _junction_z,
    _wall_u_extent,
)
from typehaus.emit.draw.scene import ArchDimension, Leader, Scene, Text
from typehaus.emit.draw.sheet_notes import parse_sheet_notes
from typehaus.emit.draw.typography import TEXT_PT
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel


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


def _sheet_note_set(model: ResolvedModel, derived: DerivedDetail):
    """This detail's parsed notes file, or an empty set when it names none.

    One parse feeds both consumers — the notes column takes ``sheet_lines()`` and the keyed
    bubbles take ``keyed``. Parsing twice would let the legend and the drawing disagree
    about a key, which is the one failure mode a keynote system has.
    """
    from typehaus.emit.draw.sheet_notes import SheetNoteSet

    path = _notes_path(model, derived)
    if path is None:
        return SheetNoteSet()
    return parse_sheet_notes(path.read_text(encoding="utf-8"),
                             source=path.name).for_condition(derived.key)


def _notes_lines(model: ResolvedModel, derived: DerivedDetail) -> list[str]:
    """Logical note lines for ``Scene.notes`` — outside the drawing's coordinate space."""
    return _sheet_note_set(model, derived).sheet_lines()


def _load_markdown_notes(path) -> list[str]:
    """Front-matter-stripped, sanitized note lines — **one string per logical bullet**.

    Deliberately *not* wrapped. Wrapping here meant guessing a column count (42) that no
    writer actually prints into, and then every writer re-joined the pieces and re-wrapped
    them to its own width — ``pdf_writer._rewrap_notes`` existed for exactly that. Wrapping
    once, at the writer, from the band it is printing into, is the whole of B6.

    The *content* now comes from :mod:`typehaus.emit.draw.sheet_notes`: a file carrying a
    ``## Sheet notes`` section prints that section and nothing else, and a file without one
    falls back to its whole body, sanitized. Both paths go through the same sanitizer, so
    markdown, repository paths and pytest ids no longer reach a sheet either way.

    The name and signature are unchanged on purpose — G-002, ``detail_payload`` and
    ``schedules/architectural.py`` all import this function, and ``list[str]`` keeps the
    ``Scene`` IR exactly as it was.
    """
    return parse_sheet_notes(path.read_text(encoding="utf-8"),
                             source=getattr(path, "name", "")).sheet_lines()


def _frame(derived: DerivedDetail):
    """Return a (world_xy) -> (u_in, z_in) mapper for the detail's cut frame.

    Must match the cutter's convention (``geometry_slice.CutPlane``): for a cut plane at
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
    # OUTSIDE the branch, deliberately. Keyed notes come from the transition's markdown, not
    # from a DetailAnnotation, so hanging them off the ``else`` would mean one authored
    # annotation on a detail silently deleted every bubble on it.
    key_nodes, key_findings = _keyed_note_nodes(model, derived, scene, nodes)
    nodes.extend(key_nodes)
    findings.extend(key_findings)
    return nodes, findings


def _keyed_note_nodes(model: ResolvedModel, derived: DerivedDetail,
                      scene: Scene = None, placed: list | None = None,
                      ) -> tuple[list, list[Finding]]:
    """A bubble per anchored keyed note, dodged clear of what is already in the scene.

    Only a note that names an anchor gets a bubble; ``[K1] text`` with no ``@ uid`` is a
    legend entry and nothing else. That is not a limitation to be fixed — one notes file
    reaches six details (``basement_to_framed_wall_detail.md`` does), and a uid that exists
    on one junction may be nowhere near another. An anchor that will not resolve *on this
    detail* is silently skipped rather than reported: it is a note about a different cut of
    the same wall, not an authoring error.
    """
    from typehaus.emit.draw.annotate import dodge, leader_box
    from typehaus.emit.draw.keyed_notes import bubble_extent, bubble_nodes, standoff

    notes = _sheet_note_set(model, derived)
    anchored = [n for n in notes.keyed if n.anchored]
    if not anchored:
        return ([], [])

    frame = _frame(derived)
    scale = scene.frame.scale if scene is not None and scene.frame is not None else None
    # ``placed`` is what THIS call just built — the seed callout column, which does not
    # exist in ``scene.nodes`` yet. Dodging only against the scene put every bubble
    # straight through the continuity column it is supposed to be avoiding.
    reserved = [*(scene.nodes if scene is not None else ()), *(placed or [])]
    fixed = [leader_box(n, scale) for n in reserved if isinstance(n, Leader) and n.text]
    fixed += [dimension_box(n, scale) for n in reserved if isinstance(n, ArchDimension)]
    nodes: list = []
    for note in anchored:
        point = _keyed_anchor(model, derived, frame, note)
        # An enlarged part bubbles only what it shows; a junction slides a layer anchor in.
        point = (into_crop(point, derived.view.crop, clamp=derived.part is None)
                 if point is not None else None)
        if point is None:
            continue  # the note's subject is not in this cut
        at = standoff(point, scale)
        # The continuity column already occupies the strip outboard of the wall. Push the
        # bubble down until it clears every leader box in it, the way the seed callouts do.
        at = _dodge_point(at, fixed, bubble_extent(at, scale), dodge)
        # A bubble already placed is as much an obstacle as a leader box: two notes
        # anchored on adjacent layer faces resolve within a few model inches of each other.
        fixed.append(bubble_extent(at, scale))
        nodes.extend(bubble_nodes(note.key, at, scale))
        nodes.append(Leader(anchor=_point_anchor(point), at=at, to=point, text="",
                            height_pt=ANNOTATION_TEXT_PT, uid=None))
    return (nodes, [])


#: The anchor target that means "whichever wall *this* detail is cutting". A notes file is
#: bound by an assembly pattern, so one file reaches several junctions with different walls
#: in them; ``host`` is what lets a keyed note follow the binding instead of naming one of
#: them and rendering nowhere on the other five.
HOST_ANCHOR = "host"


def _keyed_anchor(model: ResolvedModel, derived: DerivedDetail, frame, note):
    """The keyed note's anchor point, or ``None`` when it does not land on this detail.

    ``None`` rather than a ``Finding``, because it is not an error. One notes file is bound
    by an assembly pattern and reaches several junctions; a note about the spray foam has
    nothing to say on the interior partition that shares the file, and reporting that would
    be reporting the binding working correctly.

    Accepts an element **tag** as well as a uid.

    Uids are minted by ``haus fmt`` and a note file must never hand-write one — that is a
    house rule, and it applies to a reference as much as to a declaration, because a
    reference to a uid that is regenerated points at nothing. Tags are the stable name a
    person writes. ``host`` (:data:`HOST_ANCHOR`) is stabler still: it takes whichever wall
    the condition names on the detail being drawn.
    """
    from typehaus.emit.draw.detail_components.geometry import condition_walls

    target = note.anchor_uid
    if target == HOST_ANCHOR:
        walls = condition_walls(model, derived.condition) or []
        host = _host_wall(model, derived.condition)
        if host is not None and host not in walls:
            walls = [*walls, host]
        for wall in walls:
            point, err = _wall_anchor(wall, note.anchor_face, frame)
            if err is None:
                return point
        return None
    by_tag = next((e for e in (*model.walls, *model.roofs, *model.solids)
                   if getattr(e, "tag", None) == target), None)
    if by_tag is not None:
        target = by_tag.uid
    point, err = resolve_anchor(model, frame, target, note.anchor_face)
    return None if err is not None else point


#: How far a bubble may be pushed off its anchor to clear an obstacle, in bubble heights.
#: The dodge was unbounded and it showed: on the eave detail K3 and K4 slid clean off the
#: bottom of the drawing into the legend band, pointing at nothing — which is worse than a
#: bubble that grazes a leader box.
_MAX_DODGE_HEIGHTS = 7.0


def _dodge_point(at, fixed, extent, _dodge) -> tuple[float, float]:
    """Slide ``at`` clear of every reserved box in ``fixed`` — down first, then up.

    ``annotate.dodge`` works on ``LabelSpec`` placements, which a bubble is not: it has no
    text width and no row height, it is a circle. Rather than force a bubble into a label
    shape, the one thing ``dodge`` does that matters here is done directly.

    **Bounded, and it returns the ORIGINAL position when it cannot find a clear one inside
    the bound.** A leader still points at the right place from a bubble that grazes a label;
    it points at nothing from a bubble that has left the drawing.
    """
    u0, z0, u1, z1 = extent
    height = z1 - z0
    limit = _MAX_DODGE_HEIGHTS * height

    def clash_at(dz: float):
        return next((box for box in fixed
                     if not (u1 < box[0] or u0 > box[2]
                             or z1 + dz < box[1] or z0 + dz > box[3])), None)

    for direction in (-1.0, 1.0):
        dz = 0.0
        for _ in range(24):
            clash = clash_at(dz)
            if clash is None:
                return (at[0], at[1] + dz)
            dz += direction * (height + (clash[3] - clash[1]) * 0.05)
            if abs(dz) > limit:
                break
    return at


def _point_anchor(point):
    from typehaus.emit.draw.scene import NamedPoint

    return NamedPoint(xy=point)


#: Seed-callout lettering, **points**. It was 1.6 model inches, which is this size at the
#: frameless conversion — the number stopped meaning "1.6 inches of building" the moment the
#: drawing knew what paper it was on.
ANNOTATION_TEXT_PT = TEXT_PT


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
    scale = scene.frame.scale if scene is not None and scene.frame is not None else None
    step_pt = ANNOTATION_TEXT_PT * 2.4

    # A layer anchor resolves at its wall's mid-height, which for a storey-tall wall is far
    # outside a junction crop. What the callout is about is the layer *at the junction*, so
    # pin the elevation there and only take the layer's position across the wall depth.
    junction_z = (_junction_z(model, derived.condition, wall, derived.direction,
                              derived.station) / M_PER_IN if wall else None)
    if derived.part is not None:  # an enlarged part's junction is the middle of its crop
        junction_z = (cz0 + cz1) / 2.0 / M_PER_IN
    # Either side of a junction may own the layer being claimed — at a foundation detail the
    # sheathing and WRB belong to the framed wall above, not the concrete below. An opening
    # condition names no wall at all, so its host carries every claim.
    # ``condition_walls`` rather than the raw tags: a condition may NAME an element that
    # carries none of the faces it is keyed on — the story-and-a-half eave names its rafter
    # plate, whose only layer is 1 1/2" of framing, while the sheathing/CI/cladding faces the
    # continuity claims are about belong to the wall it stands on. Anchoring on the plate
    # resolved every face to None and the callouts vanished from the one detail that exists
    # to show that handoff.
    from typehaus.emit.draw.detail_components.geometry import condition_walls

    candidates = condition_walls(model, derived.condition)
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
        target = _anchor(cont.from_face) or _anchor(cont.to_face)
        if target is None:  # neither face is in this cut (an interior rim band): no claim
            continue
        content = wrap_label(
            f"{cont.control} continuity — {cont.from_face} → {cont.to_face}")
        entries.append(LabelSpec(text=content, target=target))
    placed = place_column(entries, x=text_x, z_top=top_y, step_pt=step_pt,
                          height_pt=ANNOTATION_TEXT_PT, align="left", scale=scale)
    fixed = tuple(leader_box(n, scale) for n in (scene.nodes if scene is not None else ())
                  if isinstance(n, Leader))
    nodes: list = []
    for label in dodge(placed, fixed=fixed, scale=scale):
        if label.spec.target is None:
            nodes.append(Text(anchor=label.at, content=label.spec.text,
                              height_pt=label.height_pt, layer="A-ANNO-TEXT", uid=None))
        else:
            nodes.append(Leader(anchor=_point_anchor(label.spec.target), at=label.at,
                                to=label.spec.target, text=label.spec.text,
                                height_pt=label.height_pt, uid=None))
    if getattr(tr, "overlay", None):
        nodes.append(Text(anchor=(cu0 / M_PER_IN, cz0 / M_PER_IN - 4.0),
                          content=f"{tr.tag}  ·  {tr.overlay}",
                          height_pt=ANNOTATION_TEXT_PT, layer="A-ANNO-TEXT", uid=None))
    return nodes
