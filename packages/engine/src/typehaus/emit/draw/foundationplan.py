"""S-100 foundation sheet → drawing IR (→ 20 §Drawing IR, → 30 §Sheets).

A complete foundation sheet, not a re-render of a storey: footing/pad plan with sizes and
bearing elevations, foundation-wall runs and thicknesses, slab-on-grade extents, bedding /
drainage callouts, step-footing callouts, and the keyed foundation schedules. Every
geometric input already exists in the ``ResolvedModel``; this builder only projects it into
2D IR (→ 20 "the UI never re-measures"). What the model cannot supply is *named* by
``foundation_sheet_findings`` and listed on the sheet, never invented.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.emit.draw._shared import emit_bbox_dimension_chain, emit_wall
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.foundation_schedule import (
    FoundationMarks,
    bearing_solids,
    build_foundation_schedules,
    footing_steps,
    foundation_general_notes,
    foundation_marks,
    foundation_sheet_findings,
    foundation_walls,
    slabs_on_grade,
)
from typehaus.emit.draw.plumbingplan import storey_above
from typehaus.emit.draw.scene import (
    ArchDimension,
    FaceAnchor,
    Leader,
    NamedPoint,
    Polyline,
    Scene,
    SceneBuilder,
    Symbol,
    Text,
)
from typehaus.emit.draw.schedule_block import (
    BlockMetrics,
    NoteBlock,
    ScheduleBlock,
    emit_block_columns,
    emit_mark,
    metrics_for,
    wrap_leader_text,
)
from typehaus.emit.draw.structural_common import (
    elevation_feet,
    feet_inches,
    inches,
    inches_text,
    outline_center,
    wall_center,
)

if TYPE_CHECKING:
    from typehaus.checks.jurisdiction import JurisdictionProfile

from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel, ResolvedWall

# Leader drops in metres, so a callout clears the geometry it points at.
_LEADER_DROP_M = 1.0
_BEDDING_LEADER_DROP_M = 2.0
# Nominal post half-width used for the plan square when the Post carries only a size string.
_POST_HALF_WIDTH_M = M_PER_IN
_SLAB_LABEL_HEIGHT_IN = 3.0


def has_foundation_content(model: ResolvedModel) -> bool:
    """Whether S-100 has anything real to show (starter has none — sheet omitted)."""
    return (
        any(wall.is_foundation for wall in model.walls)
        or any(solid.category in {"footing", "pad", "slab"} for solid in model.solids)
    )


def _foundation_storey(model: ResolvedModel) -> str | None:
    storeys = {wall.storey for wall in model.walls if wall.is_foundation}
    if not storeys:
        return None
    elevation = {s.tag: s.elevation.meters for s in model.plan.storeys}
    return min(storeys, key=lambda tag: elevation.get(tag, 0.0))


def build_foundation_plan(model: ResolvedModel,
                          profile: JurisdictionProfile | None = None) -> Scene:
    """Build the S-100 IR scene: foundation plan plus its keyed schedules and notes."""
    b = SceneBuilder(name="foundation-plan", units="in")
    if not has_foundation_content(model):
        return b.build()

    marks = foundation_marks(model)
    walls = foundation_walls(model)
    storey = _foundation_storey(model)
    plan_points = _drawn_plan_points(model, walls)
    metrics = metrics_for(plan_points)

    for wall in walls:
        emit_wall(b, wall, layer_override="S-FNDN")
    _emit_wall_marks(b, walls, marks, metrics)
    _emit_footings_and_pads(b, model, marks, metrics)
    _emit_slabs(b, model, marks)
    _emit_posts_and_beams(b, model, storey)
    _emit_step_callouts(b, model)
    _emit_footing_bedding_note(b, model)
    _emit_sleeve_pour_dimensions(b, model, walls, storey)
    if walls:
        emit_bbox_dimension_chain(b, walls)
    _emit_schedule_column(b, model, plan_points, metrics, profile)
    return b.build()


def _drawn_plan_points(model: ResolvedModel,
                       walls: list[ResolvedWall]) -> list[tuple[float, float]]:
    """Every point the plan half of the sheet occupies, in inches — the schedule sits clear
    of it rather than overlapping the drawing at some assumed sheet size."""
    points = [_in(point) for wall in walls for point in wall.axis]
    for solid in (*bearing_solids(model), *slabs_on_grade(model)):
        points.extend(_in(point) for point in solid.outline)
    return points


def _emit_wall_marks(b: SceneBuilder, walls: list[ResolvedWall], marks: FoundationMarks,
                     metrics: BlockMetrics) -> None:
    """Key each foundation-wall run to its schedule row.

    The mark alone: thickness and top/bottom-of-wall elevations belong in the schedule, and
    repeating them on every run buries the plan under its own annotation.
    """
    for wall in walls:
        cx, cy = wall_center(wall)
        emit_mark(b, _in((cx, cy)), marks.wall[wall.tag], metrics)


def _emit_footings_and_pads(b: SceneBuilder, model: ResolvedModel, marks: FoundationMarks,
                            metrics: BlockMetrics) -> None:
    """Footing/pad outlines with their schedule mark, plus one sized leader per mark."""
    leadered: set[str] = set()
    for solid in bearing_solids(model):
        b.add(Polyline(
            points=tuple(_in(p) for p in solid.outline), layer="S-FNDN-FTNG",
            closed=True, lineweight=0.25, linetype="HIDDEN2",
            uid=solid.uid, tag=solid.tag,
        ))
        mark = marks.footing.get(solid.tag) or marks.pad.get(solid.tag, "")
        cx, cy = outline_center(solid.outline)
        emit_mark(b, _in((cx, cy)), mark, metrics, layer="S-FNDN-FTNG")
        authored = model.plan.by_tag(solid.tag)
        if authored is None or mark in leadered:
            continue  # one callout per scheduled type; the rest read from the mark
        leadered.add(mark)
        b.add(Leader(
            anchor=NamedPoint(xy=_in((cx, cy)), name=solid.tag),
            at=_in((cx, cy)), to=_in((cx, cy - _LEADER_DROP_M)),
            text=f"{mark} — {_bearing_size(solid, authored)} @ BEARING EL. "
                 f"{elevation_feet(solid.z0_m)}",
            layer="S-FNDN-FTNG",
        ))


def _bearing_size(solid, authored) -> str:
    if solid.category == "footing":
        return (f"{inches_text(authored.width.inches)} × "
                f"{inches_text(authored.depth.inches)} CONT. FTG.")
    return f"{inches_text(authored.thickness.inches)} THK PAD"


def _emit_slabs(b: SceneBuilder, model: ResolvedModel, marks: FoundationMarks) -> None:
    for solid in slabs_on_grade(model):
        b.add(Polyline(
            points=tuple(_in(p) for p in solid.outline), layer="A-SLAB",
            closed=True, lineweight=0.3, uid=solid.uid, tag=solid.tag,
        ))
        cx, cy = outline_center(solid.outline)
        b.add(Text(anchor=_in((cx, cy)),
                   content=f"{marks.slab[solid.tag]} · {solid.tag}\n"
                           f"{inches(solid.z1_m - solid.z0_m)} CONC. SLAB ON GRADE\n"
                           f"T.O.S. EL. {elevation_feet(solid.z1_m)}",
                   height=_SLAB_LABEL_HEIGHT_IN, layer="A-SLAB", align="center"))


def _emit_posts_and_beams(b: SceneBuilder, model: ResolvedModel, storey: str | None) -> None:
    """Posts standing on a scheduled footing/pad, and the beams of the foundation storey."""
    supports = {solid.tag for solid in bearing_solids(model)}
    for element in model.plan.all_elements():
        if element.element_kind == "Post" and element.supported_by in supports:
            x, y = element.position.xy_m
            outline = ((x - _POST_HALF_WIDTH_M, y - _POST_HALF_WIDTH_M),
                       (x + _POST_HALF_WIDTH_M, y - _POST_HALF_WIDTH_M),
                       (x + _POST_HALF_WIDTH_M, y + _POST_HALF_WIDTH_M),
                       (x - _POST_HALF_WIDTH_M, y + _POST_HALF_WIDTH_M))
            b.add(Polyline(points=tuple(_in(p) for p in outline), layer="S-COLS",
                           closed=True, lineweight=0.4, uid=element.uid, tag=element.tag))
            b.add(Symbol(name="post", insert=_in((x, y)), layer="S-COLS"))
            b.add(Leader(
                anchor=NamedPoint(xy=_in((x, y)), name=element.tag),
                at=_in((x, y)), to=_in((x, y - _LEADER_DROP_M)),
                text=f"{element.tag} {element.size} POST ON {element.supported_by}",
                layer="S-COLS",
            ))
    nodes = {n.tag: n for n in model.plan.storey_elements(storey)} if storey else {}
    for element in model.plan.storey_elements(storey) if storey else ():
        if element.element_kind != "Beam":
            continue
        start, end = nodes.get(element.start_node), nodes.get(element.end_node)
        if start is None or end is None:
            continue
        b.add(Polyline(points=(_in(start.position.xy_m), _in(end.position.xy_m)),
                       layer="S-BEAM", lineweight=0.5, uid=element.uid, tag=element.tag))


def _emit_step_callouts(b: SceneBuilder, model: ResolvedModel) -> None:
    """Call each measured step between two touching footing runs at its own location."""
    for lower, upper, at in footing_steps(model):
        b.add(Leader(
            anchor=NamedPoint(xy=_in(at), name=upper.tag),
            at=_in(at), to=_in((at[0], at[1] - _LEADER_DROP_M)),
            text=f"STEP FTG. {feet_inches(upper.z0_m - lower.z0_m)}: "
                 f"{elevation_feet(lower.z0_m)} → {elevation_feet(upper.z0_m)}",
            layer="S-FNDN-FTNG",
        ))


def _emit_sleeve_pour_dimensions(b: SceneBuilder, model: ResolvedModel,
                                 walls: list[ResolvedWall], storey: str | None) -> None:
    """Dimension each sleeve above from the nearest two perpendicular foundation-wall
    faces — the pour layout the concrete crew works from (Phase 2 hook)."""
    if storey is None:
        return
    above = storey_above(model, storey)
    sleeves = [s for s in model.sleeves if s.storey == above]
    if not sleeves or not walls:
        return
    horizontal = [w for w in walls if _is_horizontal(w)]
    vertical = [w for w in walls if not _is_horizontal(w)]
    for sleeve in sleeves:
        cx, cy = sleeve.center
        nearest_h = min(horizontal, key=lambda w: abs(_axis_y(w) - cy), default=None)
        nearest_v = min(vertical, key=lambda w: abs(_axis_x(w) - cx), default=None)
        if nearest_h is not None:
            wy = _axis_y(nearest_h)
            b.add(ArchDimension(
                kind="linear",
                ends=(FaceAnchor(uid=nearest_h.uid, face_role="start"),
                      NamedPoint(xy=_in((cx, cy)), name=sleeve.tag)),
                p0=_in((cx, wy)), p1=_in((cx, cy)), offset=6.0,
            ))
        if nearest_v is not None:
            wx = _axis_x(nearest_v)
            b.add(ArchDimension(
                kind="linear",
                ends=(FaceAnchor(uid=nearest_v.uid, face_role="start"),
                      NamedPoint(xy=_in((cx, cy)), name=sleeve.tag)),
                p0=_in((wx, cy)), p1=_in((cx, cy)), offset=6.0,
            ))


def _is_horizontal(wall: ResolvedWall) -> bool:
    (x0, y0), (x1, y1) = wall.axis
    return abs(y1 - y0) < abs(x1 - x0)


def _axis_y(wall: ResolvedWall) -> float:
    return (wall.axis[0][1] + wall.axis[1][1]) / 2.0


def _axis_x(wall: ResolvedWall) -> float:
    return (wall.axis[0][0] + wall.axis[1][0]) / 2.0


def _emit_footing_bedding_note(b: SceneBuilder, model: ResolvedModel) -> None:
    """One leader per unique bedding spec — never a blanket note the plan didn't author."""
    seen: set[tuple] = set()
    for bedding in sorted(model.footing_beddings, key=lambda item: item.tag):
        key = (bedding.aggregate, bedding.geotextile, bedding.drain_tile,
               bedding.perimeter_insulation_m, bedding.cast_foam_in_aggregate,
               round(bedding.z1_m - bedding.z0_m, 3))
        if key in seen:
            continue
        seen.add(key)
        # A bed hosted on a wall has no footing over it — the wall stands on the bed
        # itself (the SRW apron, params/raised_garden.py). Saying "BELOW FTG" there names
        # concrete that is not in the excavation.
        under = "WALL" if any(w.tag == bedding.host for w in model.walls) else "FTG"
        parts = [f"UNDERCUT {inches(bedding.z1_m - bedding.z0_m)} BELOW {under}, "
                 f"COMPACTED {bedding.aggregate.upper()}"]
        if bedding.geotextile:
            parts.append("NON-WOVEN GEOTEXTILE LINER")
        if bedding.drain_tile:
            parts.append("DRAIN TILE IN BED")
        if bedding.perimeter_insulation_m is not None:
            parts.append(f"{inches(bedding.perimeter_insulation_m)} RIGID FOAM PERIMETER "
                         "INSULATION")
        if bedding.cast_foam_in_aggregate:
            parts.append("CAST-IN-PLACE FOAM IN AGGREGATE")
        cx, cy = outline_center(bedding.outline)
        b.add(Leader(
            anchor=NamedPoint(xy=_in((cx, cy)), name=bedding.tag),
            at=_in((cx, cy)), to=_in((cx, cy - _BEDDING_LEADER_DROP_M)),
            text=wrap_leader_text(" — ".join(parts)), layer="S-FNDN-FTNG",
        ))


def _schedule_blocks(model: ResolvedModel,
                     profile: JurisdictionProfile | None = None) -> list[ScheduleBlock]:
    """The non-geometry half of the sheet, in reading order: keyed schedules, then the
    general notes, then what the model could not supply."""
    blocks: list[ScheduleBlock] = list(build_foundation_schedules(model))
    blocks.append(NoteBlock(title="FOUNDATION NOTES",
                            notes=tuple(foundation_general_notes(model, profile))))
    blocks.append(NoteBlock(
        title="NOT SHOWN — MISSING MODEL INPUTS",
        notes=tuple(f"{finding.check_id}: {finding.message}"
                    for finding in foundation_sheet_findings(model))))
    return blocks


def _emit_schedule_column(b: SceneBuilder, model: ResolvedModel,
                          plan_points: list[tuple[float, float]],
                          metrics: BlockMetrics,
                          profile: JurisdictionProfile | None = None) -> None:
    """Reflow the keyed schedules, the general notes and the missing-input list into
    balanced columns beside the plan.

    One tall column was the whole reason S-100 printed at 3/32" on a 24x36 sheet: the
    stack ran to twice the plan's height, and it is the *scene* box the sheet is fitted
    to, so the building paid for its own tables. ``emit_block_columns`` picks the split.
    """
    emit_block_columns(b, _schedule_blocks(model, profile), plan_points, metrics)


__all__ = ["build_foundation_plan", "has_foundation_content"]
