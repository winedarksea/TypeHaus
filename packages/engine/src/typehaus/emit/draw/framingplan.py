"""S-101 floor-framing sheet → drawing IR (→ 20 §Drawing IR, → 30 §Sheets).

One framed deck per sheet: the resolved joists with their span direction and spacing, the
floor openings and their headers/trimmers, the walls below (declared bearing heavy, the
rest ghosted), the beams and posts the deck bears on, the headers in the walls below, and
the keyed member schedules. What the model cannot supply — braced-wall lines above all — is
listed by ``framing_sheet_findings`` rather than drawn.
"""

from __future__ import annotations

from typehaus.emit.draw._shared import emit_bbox_dimension_chain, emit_wall
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.framing_schedule import (
    FramedLevel,
    bearing_wall_labels,
    build_framing_schedules,
    framed_level,
    framing_general_notes,
    framing_sheet_findings,
    joist_label,
)
from typehaus.emit.draw.scene import Leader, NamedPoint, Polyline, Scene, SceneBuilder, Symbol, Text
from typehaus.emit.draw.schedule_block import (
    BlockMetrics,
    block_origin_right_of,
    emit_mark,
    emit_note_block,
    emit_schedule_table,
    metrics_for,
)
from typehaus.emit.draw.structural_common import feet_inches, outline_center
from typehaus.resolve.model import ResolvedModel

# Label offsets in metres so a callout clears the member it names.
_SPAN_LABEL_OFFSET_M = 1.0
_LEADER_DROP_M = 0.8
_BEARING_LABEL_OFFSET_M = 0.1
_POST_HALF_WIDTH_M = 0.0254
_SPAN_ARROW_SCALE_IN = 24.0
_MEMBER_LABEL_HEIGHT_IN = 3.0
_BEARING_LABEL_HEIGHT_IN = 2.0


def build_framing_plan(model: ResolvedModel, floor_tag: str) -> Scene:
    """Build the S-101 IR scene for the ``ResolvedFloor`` with tag ``floor_tag``."""
    b = SceneBuilder(name=f"framing-{floor_tag}", units="in")
    level = framed_level(model, floor_tag)
    if level is None:
        return b.build()

    _emit_walls_below(b, model, level)
    for member in level.floor.members:
        b.add(Polyline(points=(_in(member.p0), _in(member.p1)), layer="S-FRAM",
                       lineweight=0.4, uid=level.floor.uid, tag=member.child_key))

    plan_points = _drawn_plan_points(model, level)
    metrics = metrics_for(plan_points)
    _emit_span_callout(b, level)
    _emit_floor_openings(b, model, level)
    _emit_beams_and_posts(b, model, level, metrics)
    _emit_headers(b, level, metrics)
    _emit_bearing_labels(b, level)
    if level.declared_bearing_walls:
        emit_bbox_dimension_chain(b, list(level.declared_bearing_walls))
    _emit_schedule_column(b, model, level, plan_points, metrics)
    return b.build()


def _drawn_plan_points(model: ResolvedModel, level: FramedLevel) -> list[tuple[float, float]]:
    points = [_in(point) for member in level.floor.members for point in (member.p0, member.p1)]
    for wall in (*level.declared_bearing_walls, *level.role_bearing_walls):
        points.extend(_in(point) for point in wall.axis)
    if level.bearing_storey is not None:
        points.extend(_in(point) for wall in model.walls
                      if wall.storey == level.bearing_storey for point in wall.axis)
    return points


def _emit_walls_below(b: SceneBuilder, model: ResolvedModel, level: FramedLevel) -> None:
    """Walls of the storey below: bearing walls heavy, everything else ghosted.

    Bearing is read two ways because the model carries it two ways — the deck's declared
    ``bearing_refs`` (what carries *this* deck) and the authored ``structural_role`` (what
    the designer marked bearing at all). Both are drawn heavy; the schedule keeps them apart.
    """
    if level.bearing_storey is None:
        return
    heavy = {wall.tag for wall in (*level.declared_bearing_walls, *level.role_bearing_walls)}
    for wall in model.walls:
        if wall.storey != level.bearing_storey:
            continue
        if wall.tag in heavy:
            emit_wall(b, wall, layer_override="S-WALL", weight_override=0.5, members=False)
        else:
            emit_wall(b, wall, layer_override="S-WALL-BELW", weight_override=0.13,
                      hatch=False, members=False)


def _emit_span_callout(b: SceneBuilder, level: FramedLevel) -> None:
    """The span arrow, the joist mark, and the size/spacing note at the deck's centre."""
    if not level.floor.members:
        return
    xs = [p[0] for m in level.floor.members for p in (m.p0, m.p1)]
    ys = [p[1] for m in level.floor.members for p in (m.p0, m.p1)]
    cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    rotation = 0.0 if level.floor.direction == "x" else 90.0
    b.add(Symbol(name="span-arrow", insert=_in((cx, cy)), rotation=rotation,
                 scale=_SPAN_ARROW_SCALE_IN, layer="S-FRAM"))
    mark = level.marks.get("category:joist", "")
    b.add(Text(anchor=_in((cx, cy + _SPAN_LABEL_OFFSET_M)),
               content=f"{mark} · {joist_label(level.system)}",
               height=_MEMBER_LABEL_HEIGHT_IN, layer="S-FRAM", align="center"))
    joists = [m for m in level.floor.members if m.category == "joist"]
    if joists:
        b.add(Text(anchor=_in((cx, cy - _SPAN_LABEL_OFFSET_M)),
                   content=f"MAX SPAN {feet_inches(max(m.length_m for m in joists))}",
                   height=_MEMBER_LABEL_HEIGHT_IN, layer="S-FRAM", align="center"))


def _emit_floor_openings(b: SceneBuilder, model: ResolvedModel, level: FramedLevel) -> None:
    """Floor openings, keyed to the header/trimmer marks the resolver actually generated."""
    header_mark = level.marks.get("category:header", "")
    trimmer_mark = level.marks.get("category:trimmer", "")
    keyed = " / ".join(part for part in (header_mark, trimmer_mark) if part)
    for tag in level.system.openings:
        opening = model.plan.by_tag(tag)
        if opening is None or len(opening.outline) < 3:
            continue
        outline = [point.xy_m for point in opening.outline]
        b.add(Polyline(points=tuple(_in(point) for point in outline), layer="S-FRAM-OPEN",
                       closed=True, lineweight=0.3, uid=opening.uid, tag=opening.tag))
        cx, cy = outline_center(outline)
        label = f"{opening.tag}\nHEADER / TRIMMER {keyed}" if keyed else \
            f"{opening.tag}\nHEADER / TRIMMER BY SUPPLIER"
        b.add(Text(anchor=_in((cx, cy)), content=label, height=_BEARING_LABEL_HEIGHT_IN,
                   layer="S-FRAM-OPEN", align="center"))


def _emit_beams_and_posts(b: SceneBuilder, model: ResolvedModel, level: FramedLevel,
                          metrics: BlockMetrics) -> None:
    """Draw the load path under the deck: beams with their span, posts with their support."""
    for beam, span in level.beams:
        start, end = model.plan.by_tag(beam.start_node), model.plan.by_tag(beam.end_node)
        if start is None or end is None:
            continue
        p0, p1 = start.position.xy_m, end.position.xy_m
        b.add(Polyline(points=(_in(p0), _in(p1)), layer="S-BEAM", lineweight=0.6,
                       uid=beam.uid, tag=beam.tag))
        midpoint = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
        emit_mark(b, _in(midpoint), level.marks[beam.tag], metrics, layer="S-BEAM")
        b.add(Leader(anchor=NamedPoint(xy=_in(midpoint), name=beam.tag),
                     at=_in(midpoint), to=_in((midpoint[0], midpoint[1] - _LEADER_DROP_M)),
                     text=f"{level.marks[beam.tag]} {beam.size} — SPAN {feet_inches(span)}",
                     layer="S-BEAM"))
    for post in level.posts:
        x, y = post.position.xy_m
        outline = ((x - _POST_HALF_WIDTH_M, y - _POST_HALF_WIDTH_M),
                   (x + _POST_HALF_WIDTH_M, y - _POST_HALF_WIDTH_M),
                   (x + _POST_HALF_WIDTH_M, y + _POST_HALF_WIDTH_M),
                   (x - _POST_HALF_WIDTH_M, y + _POST_HALF_WIDTH_M))
        b.add(Polyline(points=tuple(_in(point) for point in outline), layer="S-COLS",
                       closed=True, lineweight=0.4, uid=post.uid, tag=post.tag))
        b.add(Symbol(name="post", insert=_in((x, y)), layer="S-COLS"))
        emit_mark(b, _in((x, y)), level.marks[post.tag], metrics, layer="S-COLS")


def _emit_headers(b: SceneBuilder, level: FramedLevel, metrics: BlockMetrics) -> None:
    """Key every header in the walls below to its schedule row, at the opening it spans."""
    for wall, member, _opening in level.headers:
        midpoint = ((member.p0[0] + member.p1[0]) / 2.0, (member.p0[1] + member.p1[1]) / 2.0)
        b.add(Polyline(points=(_in(member.p0), _in(member.p1)), layer="S-BEAM",
                       lineweight=0.45, uid=wall.uid, tag=member.child_key))
        emit_mark(b, _in(midpoint), level.marks[f"{wall.tag}/{member.child_key}"], metrics,
                  layer="S-BEAM")


def _emit_bearing_labels(b: SceneBuilder, level: FramedLevel) -> None:
    for (cx, cy), label in bearing_wall_labels(level):
        b.add(Text(anchor=_in((cx, cy + _BEARING_LABEL_OFFSET_M)), content=label,
                   height=_BEARING_LABEL_HEIGHT_IN, layer="A-ANNO-TEXT", align="center"))


def _emit_schedule_column(b: SceneBuilder, model: ResolvedModel, level: FramedLevel,
                          plan_points: list[tuple[float, float]],
                          metrics: BlockMetrics) -> None:
    cursor = block_origin_right_of(plan_points, metrics)
    for table in build_framing_schedules(level):
        bottom = emit_schedule_table(b, table, cursor, metrics)
        cursor = (cursor[0], bottom - metrics.block_gap)
    bottom = emit_note_block(b, "FRAMING NOTES", framing_general_notes(model, level), cursor,
                             metrics)
    cursor = (cursor[0], bottom - metrics.block_gap)
    missing = [f"{finding.check_id}: {finding.message}"
               for finding in framing_sheet_findings(model, level)]
    emit_note_block(b, "NOT SHOWN — MISSING MODEL INPUTS", missing, cursor, metrics)
