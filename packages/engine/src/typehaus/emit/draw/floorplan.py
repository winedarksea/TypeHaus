"""Floorplan slice → drawing IR (→ 20 §Drawing IR, → 11b §Slices).

Every 2D view is a ``Slice``; a floorplan is the auto-scaffolded plan slice cut 4' above a
storey floor. This builder projects the *resolved* geometry — per-layer wall polygons, real
framing member sections, insulation hatch, openings, room labels — into the pure-data 2D IR.
It never redraws from scalar specs (the old failure mode) and never re-measures: all numbers
come from the ``ResolvedModel`` (→ 20 "the UI never re-measures" rule, applied engine-side).
"""

from __future__ import annotations

from typehaus.emit.draw._shared import (
    emit_bbox_dimension_chain,
    emit_facade_dimension_strings,
    emit_fixtures,
    emit_wall,
)
from typehaus.emit.draw._shared import (
    to_in as _in,
)
from typehaus.emit.draw.door_symbols import (
    door_symbol_params,
    symbol_is_centre_anchored,
    symbol_name_for_operation,
)
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Symbol, Text
from typehaus.model.enums import DoorOperation
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import opening_center, rect_between, wall_frame
from typehaus.resolve.model import ResolvedModel


def build_floorplan(model: ResolvedModel, storey: str) -> Scene:
    """Build the plan-slice IR scene for one storey tag."""
    b = SceneBuilder(name=f"plan-{storey}", units="in")
    walls = [w for w in model.walls if w.storey == storey]

    for wall in walls:
        emit_wall(b, wall)
    _emit_slabs(b, model, storey)
    _emit_openings(b, model, {w.tag for w in walls})
    _emit_stairs(b, model, storey)
    _emit_railings(b, model, storey)
    _emit_rooms(b, model, storey)
    _emit_floor_heat(b, model, storey)
    _emit_alarms(b, model, storey)
    emit_fixtures(b, model, storey)
    # Two dimension tiers: the per-facade strings sit 14" off each facade, the overall
    # bbox chain stacks outside them at 24" (auto-dimensioner v2).
    emit_facade_dimension_strings(b, model, walls, offset=14.0)
    emit_bbox_dimension_chain(b, walls, offset=-24.0)
    return b.build()


def _door_operation(model: ResolvedModel, type_ref: str | None) -> DoorOperation:
    """The authored operation of a door opening's product type (default: a hinged leaf)."""
    if type_ref is None:
        return DoorOperation.SWING
    door_type = next((t for t in model.plan.library.door_types if t.tag == type_ref), None)
    return door_type.operation if door_type is not None else DoorOperation.SWING


def _emit_openings(b: SceneBuilder, model: ResolvedModel, wall_tags: set[str]) -> None:
    for op in model.openings:
        if op.host_wall not in wall_tags:
            continue
        wall = model.wall(op.host_wall)
        if wall is None:
            continue
        (sx, sy), (ex, ey) = wall.axis
        _origin, _tangent, (normal_x, normal_y), axis_length = wall_frame(wall)
        length = axis_length or 1.0
        cx, cy = opening_center(wall, op) or (sx, sy)
        angle = _angle(sx, sy, ex, ey)
        if op.is_door:
            _emit_door_symbol(b, model, op, (cx, cy), (ex - sx, ey - sy), length, angle,
                              wall.thickness_m / M_PER_IN)
            continue
        b.add(Symbol(
            name="window-mark", insert=_in((cx, cy)), rotation=angle,
            scale=op.width_m / M_PER_IN, layer="A-GLAZ", uid=op.uid,
            params={"width_in": op.width_m / M_PER_IN},
        ))
        # Keep labels clear of the glazed opening while retaining the wall orientation.
        b.add(Text(anchor=_in((cx + normal_x * 0.18, cy + normal_y * 0.18)),
                   content=op.tag, height=2.2, layer="A-GLAZ", align="center"))


def _emit_door_symbol(b: SceneBuilder, model: ResolvedModel, op, center: tuple[float, float],
                      axis_delta: tuple[float, float], length: float, angle: float,
                      host_wall_thickness_in: float) -> None:
    """Emit the plan glyph matching the door's authored operation.

    A hinged leaf is anchored at its *hinge* so the drawn leaf and arc describe the
    authored handing; every other glyph is symmetric about the opening and anchors at the
    centre. Which of the two applies is the symbol's property, not the caller's — but the
    handed jamb reaches the params either way, because a sliding or pocket panel parks
    toward the same jamb a hinged leaf would hang from.
    """
    authored = model.plan.by_tag(op.tag)
    name = symbol_name_for_operation(_door_operation(model, op.type_ref))
    width_in = op.width_m / M_PER_IN
    hinge_jamb_sign = -1.0 if getattr(authored, "flip_hinge", False) else 1.0
    insert = center if symbol_is_centre_anchored(name) else (
        center[0] + hinge_jamb_sign * axis_delta[0] / length * op.width_m / 2,
        center[1] + hinge_jamb_sign * axis_delta[1] / length * op.width_m / 2)
    b.add(Symbol(
        name=name, insert=_in(insert), rotation=angle, scale=width_in, layer="A-DOOR",
        uid=op.uid,
        params=door_symbol_params(name, width_in, op.height_m / M_PER_IN,
                                  -1.0 if getattr(authored, "flip_swing", False) else 1.0,
                                  hinge_jamb_sign=hinge_jamb_sign,
                                  host_wall_thickness_in=host_wall_thickness_in),
    ))


def _emit_rooms(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    for room in model.rooms:
        if room.storey != storey or not room.clear_face:
            continue
        cx = sum(p[0] for p in room.clear_face) / len(room.clear_face)
        cy = sum(p[1] for p in room.clear_face) / len(room.clear_face)
        area_sf = room.area_m2 * 10.7639
        b.add(Text(anchor=_in((cx, cy)), content=room.tag, height=4.0,
                   layer="A-AREA-IDEN", align="center"))
        b.add(Text(anchor=_in((cx, cy - 0.3)), content=f"{area_sf:.0f} SF", height=3.0,
                   layer="A-AREA-IDEN", align="center"))


def _emit_slabs(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    """Draw every resolved slab outline on its storey's plan (decks included).

    The plan slice showed no slabs at all, so a walking surface with no enclosing walls —
    the porch's composite deck on main, the balcony's aluminum deck on second — was
    invisible in 2D. Same dedupe idiom as ``_emit_stairs``: sort for a stable draw order,
    then skip a slab whose outline coincides with one already drawn.
    """
    slabs = sorted((s for s in model.solids
                    if s.category == "slab" and s.storey == storey),
                   key=lambda s: s.uid)
    seen_outlines: set[tuple[tuple[float, float], ...]] = set()
    for slab in slabs:
        outline_key = tuple(sorted((round(x, 6), round(y, 6)) for x, y in slab.outline))
        if outline_key in seen_outlines:
            continue
        seen_outlines.add(outline_key)
        b.add(Polyline(points=tuple(_in(p) for p in slab.outline), layer="A-SLAB",
                       closed=True, lineweight=0.35, uid=slab.uid, tag=slab.tag))
        cx = sum(p[0] for p in slab.outline) / len(slab.outline)
        cy = sum(p[1] for p in slab.outline) / len(slab.outline)
        b.add(Text(anchor=_in((cx, cy)), content=slab.tag, height=2.2, layer="A-SLAB",
                   align="center"))


def _member_footprint(member) -> list[tuple[float, float]]:
    """A member's plan rectangle: its axis swept by its own cross-section width.

    The same construction every emitter builds a member's footprint from, so a landing
    drawn here covers exactly the plan area the 3D deck occupies.
    """
    half = cross_section(member.profile).width_m / 2.0
    return rect_between(member.p0, member.p1, -half, half)


def _emit_stairs(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    """Draw every stair on both connected plans, without duplicate coincident symbols."""
    candidates = [stair for stair in model.stairs
                  if len(stair.outline) >= 3 and storey in {stair.storey, stair.to_storey}]
    # At a shared footprint, the departing flight is more useful than the one below.
    candidates.sort(key=lambda stair: (stair.storey != storey, stair.uid))
    seen_outlines: set[tuple[tuple[float, float], ...]] = set()
    for stair in candidates:
        outline_key = tuple(sorted((round(x, 6), round(y, 6)) for x, y in stair.outline))
        if outline_key in seen_outlines:
            continue
        seen_outlines.add(outline_key)
        xs, ys = [point[0] for point in stair.outline], [point[1] for point in stair.outline]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        along_x = stair.run_direction == "x"
        for member in stair.members:
            # Walking surfaces only. The framing *under* a landing — joists on a 16" grid,
            # perimeter rims, posts — is category ``landing_framing`` and belongs on a
            # framing plan, not here: drawing it put ~14 stray polylines through every
            # landing zone, which read as uneven tread marks and a split down the middle.
            if member.category not in {"tread", "winder", "landing"}:
                continue
            if member.p0 == member.p1:
                continue  # a vertical member (post/newel) is a point in plan, not a line
            if member.plan_outline is not None:
                b.add(Polyline(points=tuple(_in(p) for p in member.plan_outline), closed=True,
                               layer="A-STAIR", lineweight=0.25, uid=stair.uid,
                               tag=member.child_key))
                continue
            if member.category == "landing":
                # A landing's symbol is its *outline*, not its axis: the deck member is a
                # board with a width, and one centreline down the middle of a platform is
                # the "weird split on the landing".
                b.add(Polyline(points=tuple(_in(p) for p in _member_footprint(member)),
                               closed=True, layer="A-STAIR", lineweight=0.25,
                               uid=stair.uid, tag=member.child_key))
                continue
            # A tread's mark is its riser face, not its board centreline: the centreline
            # sits half a going past the riser, which drew a (going - nosing)/2 sliver at
            # one end of every flight and (going + nosing)/2 at the other — uniform steps
            # that read as non-uniform.
            a, c = member.riser_line if member.riser_line is not None else (member.p0,
                                                                            member.p1)
            b.add(Polyline(points=(_in(a), _in(c)), layer="A-STAIR",
                           lineweight=0.25, uid=stair.uid, tag=member.child_key))
        start = (minx, (miny + maxy) / 2) if along_x else ((minx + maxx) / 2, miny)
        end = (maxx, (miny + maxy) / 2) if along_x else ((minx + maxx) / 2, maxy)
        if stair.run_reversed:
            start, end = end, start
        b.add(Polyline(points=(_in(start), _in(end)), layer="A-STAIR", lineweight=0.5,
                       uid=stair.uid, tag=f"{stair.tag}-direction"))
        label = f"UP {stair.riser_count} R"
        b.add(Text(anchor=_in(((minx + maxx) / 2, (miny + maxy) / 2)), content=label,
                   height=3.0, layer="A-STAIR", align="center"))


def _emit_railings(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    """Draw guards and handrails: the rail line, plus every post's true plan section.

    A guard is the one piece of a stair well a plan reader looks for, and the 3D view was
    the only place it existed — an open well edge and a guarded one drew identically. Each
    resolved railing solid is drawn as its own extruded outline, exactly as the 3D viewer
    builds it: a post reads as its true plan section (1 1/2" square for a 2x2 newel) and a
    rail as the 1 1/2" band it sweeps along the path, which is the line down the guard.

    Guards top out at 42", below the 4' plan cut, so this is *below-cut* linework — hence
    the light 0.25 lineweight rather than the cut-wall weights ``emit_wall`` uses.

    THE INFILL IS DELIBERATELY NOT DRAWN. The ``category == "railing"`` filter is the frame
    — posts and rails — and the pickets, cable and lites land on ``railing_infill`` /
    ``railing_glass`` (→ resolve/railings/parts.py), so they fall out of this pass with no
    code here to exclude them. That is the intended behaviour, not an oversight:

    * At 1/4"=1'-0" a 3/4" picket is 0.016" on paper and its pitch is 0.10". The balcony
      guard alone would put 92 near-coincident squares on the sheet, which reads as a smudge
      down the guard line and swamps the rail band that is actually saying something.
    * A-RAIL's job on a floor plan is to say *this edge is guarded*. The rail band already
      says it. What the infill **is** belongs on the section, and ``emit/draw/section.py``
      already cuts ``model.solids`` unfiltered, so a picket, a cable and a glass lite each
      appear there at their true section and with their own material hatch.

    Two alternatives were considered and rejected, so nobody has to re-litigate them: a tag
    substring test (``-BAL``/``-PANEL``) string-sniffs a naming format the resolver owns and
    breaks silently the day it changes; an outline-area threshold cannot separate them —
    a 3/4" picket and a 1-1/2" post are only 4.5x apart in area, which is inside the range
    one house's post sizes already span.
    """
    seen: set[tuple[tuple[float, float], ...]] = set()
    for solid in (s for s in model.solids
                  if s.category == "railing" and s.storey == storey and len(s.outline) >= 3):
        # ``rail_count`` rails share one plan footprint — they are stacked in Z, which plan
        # cannot show — so only the first of each coincident outline is drawn.
        key = tuple(sorted((round(x, 6), round(y, 6)) for x, y in solid.outline))
        if key in seen:
            continue
        seen.add(key)
        b.add(Polyline(points=tuple(_in(point) for point in solid.outline), closed=True,
                       layer="A-RAIL", lineweight=0.25, uid=solid.uid, tag=solid.tag))


def _emit_alarms(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    """Place code-life-safety symbols at their hosted room seed points."""
    rooms = {element.tag: element for element in model.plan.storey_elements(storey)
             if element.element_kind == "Room"}
    for alarm in (element for element in model.plan.storey_elements(storey)
                  if element.element_kind == "Alarm"):
        room = rooms.get(alarm.room)
        if room is None:
            continue
        # Every AlarmKind must appear here — this is a hard index, so a new member without a
        # label KeyErrors the whole plan sheet rather than drawing an unlabelled symbol.
        label = {"smoke": "SD", "co": "CO", "combo": "SD/CO", "heat": "HD"}[alarm.kind.value]
        # The room stays the host (it is what the check rules reconcile against); the seed is
        # only the default *drawing* point, so an alarm that names its own position draws
        # there — e.g. a hall lobe of a big open room rather than that room's centroid.
        at = alarm.position.xy_m if alarm.position is not None else room.seed.xy_m
        b.add(Symbol(name="alarm", insert=_in(at), layer="A-ANNO-SYMB"))
        b.add(Text(anchor=_in((at[0] + 0.08, at[1] + 0.08)),
                   content=label, height=2.0, layer="A-ANNO-TEXT"))


def _emit_floor_heat(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    """Draw a serpentine guide from the resolved zone, not a generic fixture icon."""
    for zone in (item for item in model.floor_heat if item.storey == storey):
        xs, ys = [point[0] for point in zone.zone], [point[1] for point in zone.zone]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        lines = max(1, int((maxy - miny) / zone.spacing_m))
        points: list[tuple[float, float]] = []
        for index in range(lines + 1):
            y = min(maxy, miny + index * zone.spacing_m)
            points.extend(((minx, y), (maxx, y)) if index % 2 == 0 else ((maxx, y), (minx, y)))
        b.add(Polyline(points=tuple(_in(point) for point in points), layer="A-FLR-HEAT",
                       lineweight=0.25, uid=zone.uid, tag=zone.tag))
        b.add(Text(anchor=_in(((minx + maxx) / 2, (miny + maxy) / 2)),
                   content=f"{zone.tag} {zone.wire_length_m / 0.3048:.0f} LF", height=2.5,
                   layer="A-ANNO-TEXT", align="center"))


def _angle(sx: float, sy: float, ex: float, ey: float) -> float:
    import math

    return math.degrees(math.atan2(ey - sy, ex - sx))
