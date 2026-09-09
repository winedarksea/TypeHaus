"""S-101 floor-framing sheet → drawing IR (→ 20 §Drawing IR, → 30 §Sheets).

One STOREY per sheet, not one deck: every framed deck on the storey, the resolved joists
with their span direction and spacing, the floor openings and their headers/trimmers, the
walls below (declared bearing heavy, the rest ghosted), the beams and posts the decks bear
on, the headers in the walls below, and the keyed member schedules. What the model cannot
supply — braced-wall lines above all — is listed by ``storey_framing_findings`` rather than
drawn.

Catlin's main floor is six ``ResolvedFloor`` bays, which was six sheets of one floor. A
reviewer holding six sheets of one floor cannot see the floor, and no sheet in that pile
could show a beam that two of the bays share. The merge is only honest because the marks
are assigned storey-wide (``framing_schedule.assign_storey_marks``): a shared beam is one
mark, and every drawn element is emitted once behind a ``seen`` tag set — a duplicate
``Polyline`` uid/tag would break the DXF round-trip.
"""

from __future__ import annotations

from typehaus.emit.draw._shared import emit_bbox_dimension_chain, emit_wall
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.framing_schedule import (
    FramedLevel,
    bearing_wall_labels,
    build_storey_framing_schedules,
    framed_levels,
    joist_label,
    storey_framing_findings,
    storey_framing_notes,
)
from typehaus.emit.draw.lineweights import CUT, FAINT, PROFILE
from typehaus.emit.draw.scene import Leader, NamedPoint, Polyline, Scene, SceneBuilder, Symbol, Text
from typehaus.emit.draw.schedule_block import (
    BlockMetrics,
    NoteBlock,
    ScheduleBlock,
    emit_block_columns,
    emit_mark,
    metrics_for,
)
from typehaus.emit.draw.structural_common import feet_inches, outline_center
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

# Label offsets in metres so a callout clears the member it names.
_SPAN_LABEL_OFFSET_M = 1.0
_LEADER_DROP_M = 0.8
_BEARING_LABEL_OFFSET_M = 0.1
_POST_HALF_WIDTH_M = M_PER_IN
_SPAN_ARROW_SCALE_IN = 24.0
_MEMBER_LABEL_HEIGHT_IN = 3.0
_BEARING_LABEL_HEIGHT_IN = 2.0


def build_framing_plan(model: ResolvedModel, storey: str) -> Scene:
    """Build the S-101 IR scene for every framed deck on ``storey``."""
    b = SceneBuilder(name=f"framing-{storey}", units="in")
    levels = framed_levels(model, storey)
    if not levels:
        return b.build()

    # Walls below are a property of the STOREY, not of a deck: six bays over one basement
    # would otherwise draw the same wall six times, and six coincident polylines with the
    # same uid/tag is a broken DXF, not a heavier line.
    _emit_walls_below(b, model, levels)
    for level in levels:
        for member in level.floor.members:
            b.add(Polyline(points=(_in(member.p0), _in(member.p1)), layer="S-FRAM",
                           lineweight=PROFILE, uid=level.floor.uid, tag=member.child_key))

    plan_points = _drawn_plan_points(model, levels)
    metrics = metrics_for(plan_points)
    seen: set[str] = set()
    for level in levels:
        _emit_span_callout(b, level)
        _emit_floor_openings(b, model, level, seen)
        _emit_beams_and_posts(b, model, level, metrics, seen)
        _emit_headers(b, level, metrics, seen)
        _emit_bearing_labels(b, level, seen)
    bearing = [wall for level in levels for wall in level.declared_bearing_walls]
    if bearing:
        emit_bbox_dimension_chain(b, bearing)
    _emit_schedule_column(b, model, levels, plan_points, metrics)
    return b.build()


def _drawn_plan_points(model: ResolvedModel,
                       levels: tuple[FramedLevel, ...]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for level in levels:
        points.extend(_in(point) for member in level.floor.members
                      for point in (member.p0, member.p1))
        for wall in (*level.declared_bearing_walls, *level.role_bearing_walls):
            points.extend(_in(point) for point in wall.axis)
    for storey in _bearing_storeys(levels):
        points.extend(_in(point) for wall in model.walls
                      if wall.storey == storey for point in wall.axis)
    return points


def _bearing_storeys(levels: tuple[FramedLevel, ...]) -> list[str]:
    """The storeys below this one, in a stable order. Usually exactly one."""
    return sorted({level.bearing_storey for level in levels
                   if level.bearing_storey is not None})


def _emit_walls_below(b: SceneBuilder, model: ResolvedModel,
                      levels: tuple[FramedLevel, ...]) -> None:
    """Walls of the storey below: bearing walls heavy, everything else ghosted.

    Bearing is read two ways because the model carries it two ways — the deck's declared
    ``bearing_refs`` (what carries *this* deck) and the authored ``structural_role`` (what
    the designer marked bearing at all). Both are drawn heavy; the schedule keeps them
    apart. The heavy set is the UNION across the storey's decks: a wall that carries one
    bay is a bearing wall on the sheet, whichever bay it is under.
    """
    storeys = _bearing_storeys(levels)
    if not storeys:
        return
    heavy = {wall.tag for level in levels
             for wall in (*level.declared_bearing_walls, *level.role_bearing_walls)}
    for wall in model.walls:
        if wall.storey not in storeys:
            continue
        if wall.tag in heavy:
            emit_wall(b, wall, layer_override="S-WALL", weight_override=CUT, members=False)
        else:
            emit_wall(b, wall, layer_override="S-WALL-BELW", weight_override=FAINT,
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
    mark = level.marks.get(f"{level.floor.tag}/category:joist", "")
    b.add(Text(anchor=_in((cx, cy + _SPAN_LABEL_OFFSET_M)),
               content=f"{mark} · {joist_label(level.system)}",
               height=_MEMBER_LABEL_HEIGHT_IN, layer="S-FRAM", align="center"))
    joists = [m for m in level.floor.members if m.category == "joist"]
    if joists:
        b.add(Text(anchor=_in((cx, cy - _SPAN_LABEL_OFFSET_M)),
                   content=f"MAX SPAN {feet_inches(max(m.length_m for m in joists))}",
                   height=_MEMBER_LABEL_HEIGHT_IN, layer="S-FRAM", align="center"))


def _emit_floor_openings(b: SceneBuilder, model: ResolvedModel, level: FramedLevel,
                         seen: set[str]) -> None:
    """Floor openings, keyed to the header/trimmer marks the resolver actually generated."""
    deck = level.floor.tag
    header_mark = level.marks.get(f"{deck}/category:header", "")
    trimmer_mark = level.marks.get(f"{deck}/category:trimmer", "")
    keyed = " / ".join(part for part in (header_mark, trimmer_mark) if part)
    for tag in level.system.openings:
        opening = model.plan.by_tag(tag)
        if opening is None or len(opening.outline) < 3 or not _claim(seen, tag):
            continue
        outline = [point.xy_m for point in opening.outline]
        b.add(Polyline(points=tuple(_in(point) for point in outline), layer="S-FRAM-OPEN",
                       closed=True, lineweight=PROFILE, uid=opening.uid, tag=opening.tag))
        cx, cy = outline_center(outline)
        label = f"{opening.tag}\nHEADER / TRIMMER {keyed}" if keyed else \
            f"{opening.tag}\nHEADER / TRIMMER BY SUPPLIER"
        b.add(Text(anchor=_in((cx, cy)), content=label, height=_BEARING_LABEL_HEIGHT_IN,
                   layer="S-FRAM-OPEN", align="center"))


def _emit_beams_and_posts(b: SceneBuilder, model: ResolvedModel, level: FramedLevel,
                          metrics: BlockMetrics, seen: set[str]) -> None:
    """Draw the load path under the deck: beams with their span, posts with their support."""
    for beam, span in level.beams:
        start, end = model.plan.by_tag(beam.start_node), model.plan.by_tag(beam.end_node)
        if start is None or end is None or not _claim(seen, beam.tag):
            continue
        p0, p1 = start.position.xy_m, end.position.xy_m
        b.add(Polyline(points=(_in(p0), _in(p1)), layer="S-BEAM", lineweight=CUT,
                       uid=beam.uid, tag=beam.tag))
        midpoint = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
        emit_mark(b, _in(midpoint), level.marks[beam.tag], metrics, layer="S-BEAM")
        b.add(Leader(anchor=NamedPoint(xy=_in(midpoint), name=beam.tag),
                     at=_in(midpoint), to=_in((midpoint[0], midpoint[1] - _LEADER_DROP_M)),
                     text=f"{level.marks[beam.tag]} {beam.size} — SPAN {feet_inches(span)}",
                     layer="S-BEAM"))
    for post in level.posts:
        if not _claim(seen, post.tag):
            continue
        x, y = post.position.xy_m
        outline = ((x - _POST_HALF_WIDTH_M, y - _POST_HALF_WIDTH_M),
                   (x + _POST_HALF_WIDTH_M, y - _POST_HALF_WIDTH_M),
                   (x + _POST_HALF_WIDTH_M, y + _POST_HALF_WIDTH_M),
                   (x - _POST_HALF_WIDTH_M, y + _POST_HALF_WIDTH_M))
        b.add(Polyline(points=tuple(_in(point) for point in outline), layer="S-COLS",
                       closed=True, lineweight=PROFILE, uid=post.uid, tag=post.tag))
        b.add(Symbol(name="post", insert=_in((x, y)), layer="S-COLS"))
        emit_mark(b, _in((x, y)), level.marks[post.tag], metrics, layer="S-COLS")


def _emit_headers(b: SceneBuilder, level: FramedLevel, metrics: BlockMetrics,
                  seen: set[str]) -> None:
    """Key every header in the walls below to its schedule row, at the opening it spans."""
    for wall, member, _opening in level.headers:
        if not _claim(seen, f"{wall.tag}/{member.child_key}"):
            continue
        midpoint = ((member.p0[0] + member.p1[0]) / 2.0, (member.p0[1] + member.p1[1]) / 2.0)
        b.add(Polyline(points=(_in(member.p0), _in(member.p1)), layer="S-BEAM",
                       lineweight=CUT, uid=wall.uid, tag=member.child_key))
        emit_mark(b, _in(midpoint), level.marks[f"{wall.tag}/{member.child_key}"], metrics,
                  layer="S-BEAM")


def _emit_bearing_labels(b: SceneBuilder, level: FramedLevel, seen: set[str]) -> None:
    for (cx, cy), label in bearing_wall_labels(level):
        if not _claim(seen, f"brg:{label}"):
            continue
        b.add(Text(anchor=_in((cx, cy + _BEARING_LABEL_OFFSET_M)), content=label,
                   height=_BEARING_LABEL_HEIGHT_IN, layer="A-ANNO-TEXT", align="center"))


def _emit_schedule_column(b: SceneBuilder, model: ResolvedModel,
                          levels: tuple[FramedLevel, ...],
                          plan_points: list[tuple[float, float]],
                          metrics: BlockMetrics) -> None:
    """ONE schedule stack for the storey, reflowed into balanced columns.

    Not one column per deck stacked six deep, and not one tall column either: the sheet is
    fitted to the SCENE bounding box, so a stack taller than the plan is what
    ``select_scale`` ends up fitting and the building is drawn small to make room for its
    own tables. Merging six decks onto one sheet made that stack three times taller and
    dropped catlin's main storey to 1/16" = 1'-0" on ARCH D — the fix S-100 already had
    (``emit_block_columns``), applied here.
    """
    blocks: list[ScheduleBlock] = list(build_storey_framing_schedules(levels))
    blocks.append(NoteBlock(title="FRAMING NOTES",
                            notes=tuple(storey_framing_notes(model, levels))))
    blocks.append(NoteBlock(
        title="NOT SHOWN — MISSING MODEL INPUTS",
        notes=tuple(f"{finding.check_id}: {finding.message}"
                    for finding in storey_framing_findings(model, levels))))
    emit_block_columns(b, blocks, plan_points, metrics)


def _claim(seen: set[str], tag: str) -> bool:
    """True the first time ``tag`` is asked for; False after.

    Two decks on a storey routinely share a beam, a post, a header and a bearing wall.
    Drawing one twice is not a heavier line — the IR carries a uid/tag per element, and a
    duplicate breaks the DXF round-trip and ``test_writer_layer_coverage``.
    """
    if tag in seen:
        return False
    seen.add(tag)
    return True
