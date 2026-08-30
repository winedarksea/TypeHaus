"""Annotation for the building section sheet — datums, ground, room names (→ 30 §Details).

``section.py`` draws the *cut*: layer poché, insulation, framing, footings. Until this
module existed that is all A-301 carried, and a picture of a cut with no datum, no ground
line and no room names is not a construction document — a reader cannot say how high
anything is, where the earth is, or which volume is which.

Nothing here is a second copy of the elevation's machinery. The level ladder
(:func:`~typehaus.emit.draw.elevation_annotate.merged_levels`,
:func:`~typehaus.emit.draw.elevation_annotate.emit_level_markers`,
:func:`~typehaus.emit.draw.elevation_annotate.emit_level_dimensions`) and the ground
profile (:func:`~typehaus.emit.draw.elevation_annotate.grade_profile_points`,
:func:`~typehaus.emit.draw.elevation_annotate.emit_grade_hatch`) are the elevations',
called here; the room naming rule is :func:`~typehaus.emit.draw.plan_labels.
room_display_name`, the floor plans'. A section that invented its own would be a second
place for "MAIN FLOOR EL. 0'-0"" to be computed, and the two would drift.

What this module *does* own is the difference between the two drawings:

* **The frame.** A section's (u, z) is the cut plane's, not a viewing direction's — but the
  two are the same shape, so one ``ElevationView`` maps the cut and the grade sampling
  reads real spot elevations within 10' of the cut line rather than of a facade.
* **Lettering.** The elevations letter in model inches; a section is drawn four times
  larger, so everything here is a printed size in points (``typography``) and only the
  *reservation* is converted to model inches — at the smaller of the two papers A-301
  prints on, so a column that clears on ARCH D cannot collide on ledger.
* **Room names in the cut volume**, which an elevation has no equivalent of.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.emit.draw.annotate import LabelSpec, PlacedLabel, dodge, label_box
from typehaus.emit.draw.elevation_annotate import (
    emit_grade_hatch,
    emit_level_dimensions,
    emit_level_markers,
    grade_profile_points,
    interpolate_profile,
    label_at,
    level_text,
    merged_levels,
)
from typehaus.emit.draw.elevation_project import ElevationView, view_for
from typehaus.emit.draw.plan_labels import room_display_name
from typehaus.emit.draw.scene import (
    IRNode,
    Leader,
    NamedPoint,
    Polyline,
    Scene,
    SceneBuilder,
    Text,
)
from typehaus.emit.draw.typography import (
    CHAR_ASPECT,
    TEXT_PT,
    model_in_per_pt,
)
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_slice import CutPlane, ring_intervals
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.room_floor import room_floor_elevation

__all__ = ["annotate_building_section"]

#: The paper inches per model foot annotation is *reserved* at. A-301 lands on 1/2" = 1'-0"
#: on ARCH D and 3/16" on ledger, and a reservation is only useful when it is at least as
#: large as the print: reserving at the **smaller** of the two leaves the ARCH D column with
#: air it does not need, while reserving at the larger one would let two datum labels that
#: clear on ARCH D print through each other on ledger. Same value and the same reasoning as
#: ``_shared.PLAN_RESERVATION_SCALE``.
SECTION_RESERVATION_SCALE = 0.1875

#: Printed size of every label on this sheet, points. The elevations author 4 model inches
#: because they were written before paper space existed; a section drawn at 1/2" = 1'-0"
#: would print that at 12 pt, which is a heading, not an annotation.
ANNO_PT = TEXT_PT

#: The same lettering as model inches at the reservation scale. Two things need it: the
#: ``dodge`` boxes, which place in model space, and ``Text``/``Leader.height``, which is
#: what ``pdf_writer._scene_bounds`` measures the sheet's fit with. Reserving at one size
#: and printing at another is exactly the mismatch ``height_pt`` exists to close.
ANNO_IN = ANNO_PT * model_in_per_pt(SECTION_RESERVATION_SCALE)

#: Air above and below a datum label's reservation. ``dodge`` separates boxes that
#: *overlap*, and two labels a hair apart do not overlap — they print as one smear.
_LABEL_PAD_IN = ANNO_IN * 0.7

#: Air before the datum column, and again between its dimension string and its labels.
#: Model inches. Wider than the elevation's proportionally-equivalent gap is *not* needed
#: here: the section is at four times the scale, so a foot of paper buys four times less
#: building, and the elevation's 3'-0" would push the column a quarter of the sheet away.
_COLUMN_GAP_IN = 12.0

#: How far above its finished floor a room's name sits, model inches. Clear of the floor
#: system's own poché and well under any ceiling the cut passes.
_ROOM_LABEL_RISE_IN = 24.0

#: The families the left-hand callout column names, outermost member of each. Deliberately
#: three and not "every assembly the cut crosses": this plane crosses eight distinct wall
#: assemblies on catlin, and eight leaders reaching into a drawing with about six feet of
#: spare margin at 1/2" = 1'-0" is the thicket, not the annotation. What a reader opens a
#: section for is the *envelope* — what the roof, the wall above grade and the wall below
#: it are built of — and each is named once, on the side the leaders are shortest.
_ENVELOPE_FAMILIES = ("roof", "wall", "foundation")


def annotate_building_section(scene: Scene, model: ResolvedModel,
                              plane: CutPlane) -> Scene:
    """Return ``scene`` with the sheet annotation added — datums, grade, room names.

    Takes a built :class:`Scene` rather than the builder because the annotation has to be
    placed against the *finished* cut: the datum column stands off the drawing's right
    edge and the ground line spans its width, and neither is known until every wall,
    footing and rafter has been cut.
    """
    bounds = _geometry_bounds(scene)
    if bounds is None:
        return scene  # nothing was cut — there is no drawing to annotate
    b = SceneBuilder(name=scene.name, units=scene.units)
    b.extend(list(scene.nodes))
    spans = _drawn_spans(scene.nodes)
    ground_u1, caption = _emit_grade(b, model, plane, bounds, spans)
    # The ground line is part of the *drawing*; the datum column starts clear of it, not of
    # the building. Without this the column stood in the middle of the hatched earth.
    _emit_level_column(b, model, max(bounds[2], ground_u1))
    _emit_room_names(b, model, plane)
    # The callout column keeps to the building's own edge — the ground line runs on past it
    # — but the "GRADE" caption sits in that band, so it is an obstacle to dodge, not a
    # thing to clear by moving the whole column a foot further out.
    _emit_envelope_callouts(b, model, spans, bounds[0], caption)
    return b.build().model_copy(update={"notes": scene.notes, "frame": scene.frame})


@dataclass(frozen=True)
class _DrawnExtent:
    """What one element actually put on the sheet, model inches.

    ``box`` bounds it; ``anchor`` is a point *on* it, at its left edge. The two are not
    interchangeable and the roof is why: a gable's bbox centre-left is thirteen feet above
    its eave, in open air, so a leader aimed at the bbox names nothing.
    """

    box: tuple[float, float, float, float]
    anchor: tuple[float, float]


#: Two drawn points this close in u are on the same left edge of an element, model inches.
_EDGE_TOLERANCE_IN = 0.5


def _drawn_spans(nodes: tuple[IRNode, ...]) -> dict[str, _DrawnExtent]:
    """Per-element extent of what actually reached the sheet, keyed by uid.

    "What the cut crosses" is answered off the drawing rather than off the model: a wall
    whose axis straddles the plane can still contribute nothing (cropped, or terminated
    below the cut), and a callout leader pointing at an element that was never drawn is a
    line to nowhere.
    """
    boxes: dict[str, tuple[float, float, float, float]] = {}
    edges: dict[str, tuple[float, list[float]]] = {}
    for node in nodes:
        uid = getattr(node, "uid", None)
        points = getattr(node, "points", None) or getattr(node, "boundary", None)
        if uid is None or not points:
            continue
        us = [point[0] for point in points]
        zs = [point[1] for point in points]
        box = (min(us), min(zs), max(us), max(zs))
        current = boxes.get(uid)
        boxes[uid] = box if current is None else (
            min(current[0], box[0]), min(current[1], box[1]),
            max(current[2], box[2]), max(current[3], box[3]))
        for (u, z) in points:
            edge_u, edge_zs = edges.get(uid, (u, []))
            if u < edge_u - _EDGE_TOLERANCE_IN:
                edges[uid] = (u, [z])
            elif u <= edge_u + _EDGE_TOLERANCE_IN:
                edges[uid] = (min(edge_u, u), [*edge_zs, z])
    out: dict[str, _DrawnExtent] = {}
    for uid, box in boxes.items():
        edge_u, edge_zs = edges[uid]
        out[uid] = _DrawnExtent(box=box,
                                anchor=(edge_u, sum(edge_zs) / len(edge_zs)))
    return out


def _geometry_bounds(scene: Scene) -> tuple[float, float, float, float] | None:
    """Model-inch bbox of the drawn cut — points and hatch boundaries, nothing else.

    Deliberately not ``pdf_writer.geometry_bounds``: the IR must not depend on a writer,
    and this is the whole of what is needed.
    """
    us: list[float] = []
    zs: list[float] = []
    for node in scene.nodes:
        points = getattr(node, "points", None) or getattr(node, "boundary", None)
        if points:
            us.extend(point[0] for point in points)
            zs.extend(point[1] for point in points)
    if not us or not zs:
        return None
    return min(us), min(zs), max(us), max(zs)


def _view_of(plane: CutPlane) -> tuple[ElevationView, float]:
    """The ``ElevationView`` whose (u, depth) frame is this cut's, and the cut's depth.

    A section along x has u = world x and depth = world y, which is exactly the south
    view; a section along y has u = world y against the east view's depth of -x. Reusing
    the projector's own views is what lets the grade sampler — written for a facade —
    capture the spot elevations near a *cut line* without knowing it is doing so.
    """
    if plane.axis == "x":
        return view_for("south"), plane.station_m
    return view_for("east"), -plane.station_m


def _emit_grade(b: SceneBuilder, model: ResolvedModel, plane: CutPlane,
                bounds: tuple[float, float, float, float],
                spans: dict[str, _DrawnExtent]
                ) -> tuple[float, tuple[float, float, float, float] | None]:
    """The ground line either side of the building, hatched, captioned at its left end.

    The section draws a basement and its footings; without this nothing on the sheet says
    which of that is buried. Sampled from the same spot elevations the elevations read, in
    a capture band around the cut line rather than around a facade.

    Drawn **outboard of the building only**. A section's ground line stops where it meets
    the foundation; run straight through, it draws earth across the basement it is
    supposed to bound — which is what it looked like before this clipped. Returns the u the
    ground reached on the right and the caption's reserved box, model inches: the datum
    column has to stand clear of the one and the callouts have to dodge the other.
    """
    view, depth = _view_of(plane)
    lo_u, _z0, hi_u, _z1 = bounds
    points = grade_profile_points(model, view, depth,
                                  lo_u * M_PER_IN, hi_u * M_PER_IN)
    if len(points) < 2:
        return hi_u, None
    footprint = _footprint_at_grade(spans, points)
    segments = [segment for segment in _outboard_profiles(points, footprint) if segment]
    for segment in segments:
        poly = tuple((u / M_PER_IN, z / M_PER_IN) for u, z in segment)
        b.add(Polyline(points=poly, layer="L-SITE-GRAD", lineweight=0.7))
        emit_grade_hatch(b, segment)
    caption = None
    if segments:
        head = segments[0][0]
        at = (head[0] / M_PER_IN, head[1] / M_PER_IN - ANNO_IN)
        b.add(Text(anchor=at, content="GRADE", height=ANNO_IN, height_pt=ANNO_PT,
                   layer="L-SITE-GRAD"))
        caption = _padded(label_box(at, "GRADE", ANNO_PT, "left",
                                    SECTION_RESERVATION_SCALE))
    return points[-1][0] / M_PER_IN, caption


def _footprint_at_grade(spans: dict[str, _DrawnExtent],
                        points: list[tuple[float, float]]) -> tuple[float, float] | None:
    """The (u0, u1) the building occupies where the ground meets it, **metres**.

    An element counts as buried-and-drawn when the ground profile passes through its own
    z-range somewhere across its span — foundation walls, their insulation and the
    protection panel outboard of them. ``None`` when the ground clears everything, which
    is a slab-on-grade cut and wants an unbroken line.
    """
    lo: float | None = None
    hi: float | None = None
    for (u0, z0, u1, z1) in (extent.box for extent in spans.values()):
        grade_z = interpolate_profile(points, (u0 + u1) / 2.0 * M_PER_IN) / M_PER_IN
        if not z0 <= grade_z <= z1:
            continue
        lo = u0 if lo is None else min(lo, u0)
        hi = u1 if hi is None else max(hi, u1)
    if lo is None or hi is None:
        return None
    return lo * M_PER_IN, hi * M_PER_IN


def _outboard_profiles(points: list[tuple[float, float]],
                       footprint: tuple[float, float] | None
                       ) -> list[list[tuple[float, float]]]:
    """The ground profile split into the run left of the building and the run right of it."""
    if footprint is None:
        return [points]
    return [_clip_profile(points, points[0][0], footprint[0]),
            _clip_profile(points, footprint[1], points[-1][0])]


def _clip_profile(points: list[tuple[float, float]], u_lo: float,
                  u_hi: float) -> list[tuple[float, float]]:
    """``points`` restricted to [u_lo, u_hi], with the cut ends interpolated onto it."""
    u_lo = max(u_lo, points[0][0])
    u_hi = min(u_hi, points[-1][0])
    if u_hi - u_lo < 1e-9:
        return []
    inner = [(u, z) for (u, z) in points if u_lo < u < u_hi]
    return [(u_lo, interpolate_profile(points, u_lo)), *inner,
            (u_hi, interpolate_profile(points, u_hi))]


def _emit_level_column(b: SceneBuilder, model: ResolvedModel, edge_u: float) -> None:
    """The level datum ladder off the drawing's right edge — the sheet's missing half.

    Every storey floor and top-of-plate, grade and the ridge, coincident lines merged, each
    with its elevation and with the dimension between consecutive datums. Identical in
    substance to the elevations' ladder because it is the same ladder: only the column
    positions and the lettering size are the section's own.
    """
    levels = merged_levels(model)
    if not levels:
        return
    gap = _COLUMN_GAP_IN * M_PER_IN
    dim_u = edge_u * M_PER_IN + gap
    # The marker and the dimension string's own text both sit at ``dim_u``; a label
    # starting one gap away would print through both.
    label_u = dim_u + 3.0 * gap
    labels = [label_at(label_u, level.z_m, level_text(level), ANNO_PT,
                       target=(dim_u, level.z_m), key=("level", index),
                       scale=SECTION_RESERVATION_SCALE, pad_in=_LABEL_PAD_IN)
              for index, level in enumerate(levels)]
    emit_level_markers(b, levels, dodge(labels), dim_u,
                       height=ANNO_IN, height_pt=ANNO_PT)
    emit_level_dimensions(b, levels, dim_u)


def _emit_room_names(b: SceneBuilder, model: ResolvedModel, plane: CutPlane) -> None:
    """Name each volume the cut actually passes through, inside that volume.

    "Actually" is the load-bearing word and it is decided geometrically, not by storey or
    bbox: ``ring_intervals`` returns the inside spans where the cut line crosses the room's
    own clear-face polygon, so a room the plane misses gets no label and a re-entrant room
    the plane enters twice is named in its widest span. A room too narrow at the cut to
    hold its own name is skipped rather than labelled across its walls.
    """
    per_pt = model_in_per_pt(SECTION_RESERVATION_SCALE)
    for room in model.rooms:
        # ``tuple``: ``ResolvedRoom.clear_face`` is ``model.Ring`` (a list) while the
        # slicer declares ``geometry_ir.Ring`` (a tuple) — two aliases of the same ring.
        crossings = ring_intervals(tuple(room.clear_face), plane)
        if not crossings:
            continue
        u0, u1 = max(crossings, key=lambda span: span[1] - span[0])
        name = room_display_name(room.tag)
        # A room narrower at the cut than its own name gets none: the text would run
        # through the walls either side and read as the neighbour's. Nothing is lost — a
        # closet the cut clips the corner of is identified on its floor plan.
        width_in = len(name) * ANNO_PT * CHAR_ASPECT * per_pt
        if (u1 - u0) / M_PER_IN < width_in:
            continue
        z_in = room_floor_elevation(model, room) / M_PER_IN + _ROOM_LABEL_RISE_IN
        b.add(Text(anchor=((u0 + u1) / 2.0 / M_PER_IN, z_in), content=name,
                   height=ANNO_IN, height_pt=ANNO_PT, layer="A-AREA-IDEN",
                   align="center"))


def _emit_envelope_callouts(b: SceneBuilder, model: ResolvedModel,
                            spans: dict[str, _DrawnExtent], edge_u: float,
                            caption: tuple[float, float, float, float] | None) -> None:
    """Name the envelope assemblies the cut passes through, in a left-hand column.

    One callout per family in :data:`_ENVELOPE_FAMILIES`, taking the *outermost* member of
    each — the leftmost roof, the leftmost wall above grade, the leftmost wall below it —
    so every leader is short and lands on the near side of what it names. Two families
    that resolve to the same assembly are named once.
    """
    picks = _envelope_picks(model, spans)
    if not picks:
        return
    gap = _COLUMN_GAP_IN * M_PER_IN
    column_u = edge_u * M_PER_IN - gap
    labels: list[PlacedLabel] = []
    for assembly, anchor in picks:
        at = (column_u / M_PER_IN, anchor[1])
        labels.append(PlacedLabel(
            spec=LabelSpec(text=assembly, target=anchor, key=assembly), at=at,
            align="right", height_pt=ANNO_PT,
            box=_padded(label_box(at, assembly, ANNO_PT, "right",
                                  SECTION_RESERVATION_SCALE))))
    fixed = () if caption is None else (caption,)
    for placed in dodge(labels, fixed=fixed):
        anchor = placed.spec.target or placed.at
        b.add(Leader(anchor=NamedPoint(xy=anchor, name=str(placed.spec.key)),
                     at=placed.at, to=anchor, text=placed.spec.text,
                     height=ANNO_IN, height_pt=ANNO_PT, layer="A-ANNO-TEXT"))


def _padded(box: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    return (box[0], box[1] - _LABEL_PAD_IN, box[2], box[3] + _LABEL_PAD_IN)


def _envelope_picks(model: ResolvedModel, spans: dict[str, _DrawnExtent]
                    ) -> list[tuple[str, tuple[float, float]]]:
    """``(assembly, anchor)`` for each envelope family, outermost first, deduped.

    The anchor is the mid-height of the element's own left *edge* — the middle of a wall's
    outboard face, the eave of a roof — so the leader lands on the thing being named
    rather than in the air beside it (see :class:`_DrawnExtent`).
    """
    pools: dict[str, list[tuple[str, str]]] = {
        "roof": [(roof.uid, roof.assembly) for roof in model.roofs],
        "wall": [(wall.uid, wall.assembly) for wall in model.walls
                 if not wall.is_foundation],
        "foundation": [(wall.uid, wall.assembly) for wall in model.walls
                       if wall.is_foundation],
    }
    out: list[tuple[str, tuple[float, float]]] = []
    named: set[str] = set()
    for family in _ENVELOPE_FAMILIES:
        drawn = [(uid, assembly) for (uid, assembly) in pools[family] if uid in spans]
        if not drawn:
            continue
        uid, assembly = min(drawn, key=lambda item: (spans[item[0]].box[0], item[1]))
        if assembly in named:
            continue
        named.add(assembly)
        out.append((assembly, spans[uid].anchor))
    return out
