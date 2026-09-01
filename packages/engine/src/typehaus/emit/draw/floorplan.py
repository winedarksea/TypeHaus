"""Floorplan slice → drawing IR (→ 20 §Drawing IR, → 11b §Slices).

Every 2D view is a ``Slice``; a floorplan is the auto-scaffolded plan slice cut 4' above a
storey floor. This builder projects the *resolved* geometry — per-layer wall polygons, real
framing member sections, insulation hatch, openings, room labels — into the pure-data 2D IR.
It never redraws from scalar specs (the old failure mode) and never re-measures: all numbers
come from the ``ResolvedModel`` (→ 20 "the UI never re-measures" rule, applied engine-side).
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.emit.draw._shared import (
    PLAN_RESERVATION_SCALE,
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
from typehaus.emit.draw.plan_dimensions import emit_interior_dimension_chains
from typehaus.emit.draw.plan_labels import emit_room_blocks
from typehaus.emit.draw.plan_marks import (
    emit_opening_mark,
    opening_type_marks,
    preferred_normal,
)
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Symbol, Text
from typehaus.emit.draw.typography import (
    CHAR_ASPECT,
    DIM_TEXT_PT,
    TEXT_PT,
    model_in_per_pt,
)
from typehaus.model.enums import DoorOperation
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section, plan_cross_section_m
from typehaus.resolve.geometry import opening_center, rect_between, wall_frame
from typehaus.resolve.model import ResolvedModel

#: The placeable domains an ARCHITECTURAL plan draws. Electrical (``E-POWR``) and mechanical
#: (``M-EQPT``) devices are drawn here only because ``emit_fixtures`` used to be called with
#: no filter at all, and they have their own sheets — E-10x, E-20x and M-10x already build
#: from the same resolved objects. Leaving them on A-1xx put ~90 ``ED-T-LT-CAN4`` and
#: ``REG-T-ERV-SUP`` glyphs over catlin's main-floor room plan.
ARCHITECTURAL_DOMAINS = frozenset({"plumbing", "appliance", "furniture"})


def build_floorplan(model: ResolvedModel, storey: str) -> Scene:
    """Build the plan-slice IR scene for one storey tag."""
    b = SceneBuilder(name=f"plan-{storey}", units="in")
    walls = [w for w in model.walls if w.storey == storey]

    for wall in walls:
        emit_wall(b, wall)
    _emit_slabs(b, model, storey)
    mark_boxes = _emit_openings(b, model, {w.tag for w in walls}, storey)
    _emit_stairs(b, model, storey)
    _emit_railings(b, model, storey)
    # Order is the whole argument here. A mark bubble is pinned to its opening and an alarm
    # glyph to its device — neither can move — so the room block, which is the one thing on
    # the plan free to sit anywhere inside its own room, is placed last among the three and
    # told where the other two already are. Its caption then goes back the other way: the
    # block is fixed by the time the alarm's SD/CO label picks a side.
    room_boxes = emit_room_blocks(b, model, storey,
                                  avoid=mark_boxes + _alarm_glyph_boxes(model, storey),
                                  prefer=_placeable_boxes(model, storey))
    # Floor heat is MECHANICAL and now lives in ``_shared.emit_floor_heat`` for the HVAC
    # plan to adopt; the smoke/CO alarms stay, because A-1xx is where a plan reviewer looks
    # for them and ``code.R314``/``R315`` reconcile against the same elements.
    _emit_alarms(b, model, storey, room_boxes)
    emit_fixtures(b, model, storey, domains=ARCHITECTURAL_DOMAINS, labels=False)
    # Three dimension tiers, inner to outer: per-facade opening strings at 14", the
    # face-to-face interior partition chains at 44", the overall bbox chain at 76". Each
    # sits outside the last so a reader walks from the detail to the extent, and the two
    # exterior tiers now measure to the sheathing face rather than to a wall centreline.
    # The 30" of pitch between tiers is what ``_shared.STAGGER_ROWS`` costs: a crowded
    # string steps out up to two rows (~20") and must not land on the tier outside it.
    emit_facade_dimension_strings(b, model, walls, offset=14.0)
    emit_interior_dimension_chains(b, walls, offset=44.0)
    emit_bbox_dimension_chain(b, walls, offset=-76.0, reference="face")
    return b.build()


def _placeable_boxes(model: ResolvedModel,
                     storey: str) -> list[tuple[float, float, float, float]]:
    """Plan boxes of everything ``emit_fixtures`` will draw on this sheet, in metres.

    Handed to the room block as a *preference*, not a constraint — see
    ``plan_labels._place_block``. The same ``ARCHITECTURAL_DOMAINS`` filter the drawing
    itself uses, so the block is told about exactly what will be on the paper beside it and
    nothing that will not.
    """
    boxes: list[tuple[float, float, float, float]] = []
    for item in model.canvas_objects:
        if item.storey != storey or item.domain not in ARCHITECTURAL_DOMAINS:
            continue
        if len(item.footprint) < 3:
            continue
        xs = [point[0] for point in item.footprint]
        ys = [point[1] for point in item.footprint]
        boxes.append((min(xs), min(ys), max(xs), max(ys)))
    return boxes


def _door_operation(model: ResolvedModel, type_ref: str | None) -> DoorOperation:
    """The authored operation of a door opening's product type (default: a hinged leaf)."""
    if type_ref is None:
        return DoorOperation.SWING
    door_type = next((t for t in model.plan.library.door_types if t.tag == type_ref), None)
    return door_type.operation if door_type is not None else DoorOperation.SWING


def _emit_openings(b: SceneBuilder, model: ResolvedModel, wall_tags: set[str],
                   storey: str) -> list[tuple[float, float, float, float]]:
    """Draw every opening's plan glyph and its A-601 schedule mark.

    The mark replaced ``op.tag``. A tag is what the plan source calls the element and it is
    the wrong thing to print on a drawing: ``WIN-M-EAST-MID`` is thirteen characters of
    authoring vocabulary next to a 27" unit, and the plan carried one for every window in
    the house. What a reader needs is the schedule row — see ``plan_marks``.
    """
    marks = opening_type_marks(model)
    boxes: list[tuple[float, float, float, float]] = []
    rooms = [Polygon(room.clear_face) for room in model.rooms
             if room.storey == storey and len(room.clear_face) >= 3]
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
        mark = marks.get(op.type_ref or "")
        if op.is_door:
            _emit_door_symbol(b, model, op, (cx, cy), (ex - sx, ey - sy), length, angle,
                              wall.thickness_m / M_PER_IN)
        else:
            b.add(Symbol(
                name="window-mark", insert=_in((cx, cy)), rotation=angle,
                scale=op.width_m / M_PER_IN, layer="A-GLAZ", uid=op.uid,
                params={"width_in": op.width_m / M_PER_IN},
            ))
        if mark is not None:
            boxes.append(emit_opening_mark(
                b, mark, (cx, cy),
                preferred_normal((cx, cy), (normal_x, normal_y), rooms),
                op.is_door, op.uid))
    return boxes


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


def _emit_slabs(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    """Draw every walking surface's outline on its storey's plan.

    The plan slice showed no slabs at all, so a surface with no enclosing walls — the
    porch's composite deck on main, the balcony's aluminum deck on second — was invisible
    in 2D. Same dedupe idiom as ``_emit_stairs``: sort for a stable draw order, then skip
    an outline that coincides with one already drawn.

    A FLOOR SYSTEM'S DECK SHEET COUNTS, not only a Slab. Both exterior decks used to be a
    ``datum="walking_surface"`` Slab sitting on top of a FloorSystem's joists, and both
    became that FloorSystem's ``subfloor`` instead (SL-SG-PORCH in 3bf2f48, SL-SG-DECK and
    SL-BW-DECK on 2026-08-22) — which is the right model and took the deck straight back
    out of this drawing, because a subfloor sheet is not a solid. Reading ``model.floors``
    beside ``model.solids`` is what keeps the conversion a modelling change rather than a
    silent regression in the 2D set.
    """
    seen_outlines: set[tuple[tuple[float, float], ...]] = set()
    rooms = [Polygon(room.clear_face) for room in model.rooms
             if room.storey == storey and len(room.clear_face) >= 3]

    def _draw(outline, uid: str, tag: str) -> None:
        outline_key = tuple(sorted((round(x, 6), round(y, 6)) for x, y in outline))
        if outline_key in seen_outlines:
            return
        seen_outlines.add(outline_key)
        b.add(Polyline(points=tuple(_in(p) for p in outline), layer="A-SLAB",
                       closed=True, lineweight=0.35, uid=uid, tag=tag))
        cx = sum(p[0] for p in outline) / len(outline)
        cy = sum(p[1] for p in outline) / len(outline)
        # ONLY A SURFACE NO ROOM ALREADY NAMES. A slab under a room is that room's floor,
        # and a second caption over ``LIVING / 748 SF`` saying ``SL-M-DECK`` names the same
        # ground twice — in authoring vocabulary the second time. What is left is what a
        # reader genuinely needs named because nothing else on the sheet does: the porch,
        # the balcony, the breezeway deck, a landing pad at a threshold.
        if any(room.contains(Point(cx, cy)) for room in rooms):
            return
        b.add(Text(anchor=_in((cx, cy)), content=_surface_name(tag), height_pt=TEXT_PT,
                   layer="A-SLAB", align="center"))

    for slab in sorted((s for s in model.solids
                        if s.category == "slab" and s.storey == storey),
                       key=lambda s: s.uid):
        _draw(slab.outline, slab.uid, slab.tag)
    # Only a deck with no walls around it: an interior floor's subfloor covers the whole
    # storey and drawing its rectangle would put a box over every room plan.
    walled = {wall.storey for wall in model.walls}
    for floor in sorted((f for f in model.floors
                         if f.storey == storey and len(f.deck_outline) >= 3),
                        key=lambda f: f.uid):
        if floor.storey in walled and _has_enclosing_walls(model, floor):
            continue
        _draw(floor.deck_outline, floor.uid, floor.tag)


def _surface_name(tag: str) -> str:
    """``FS-SG-PORCH`` → ``PORCH``; ``SL-G-STEP-0`` → ``STEP 0``.

    Same derivation ``plan_labels.room_display_name`` makes, and for the same reason: the
    element prefix and the storey/structure code are authoring vocabulary, and what belongs
    on the drawing is the surface's name.
    """
    parts = tag.split("-")
    if parts and parts[0] in {"SL", "FS"}:
        parts = parts[1:]
    if len(parts) > 1 and len(parts[0]) <= 2 and parts[0].isalpha():
        parts = parts[1:]
    return " ".join(parts) if parts else tag


def _has_enclosing_walls(model: ResolvedModel, floor) -> bool:
    """True when a wall on this floor's storey stands inside its deck footprint.

    The test for "this deck is part of the building" rather than a free-standing platform.
    An interior floor is walled and its outline is redundant with the room plan; a porch,
    a balcony and a breezeway deck are not, and they are the whole reason this draws.
    """
    xs = [p[0] for p in floor.deck_outline]
    ys = [p[1] for p in floor.deck_outline]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for wall in model.walls:
        if wall.storey != floor.storey:
            continue
        for point in wall.axis:
            if x0 - 1e-9 <= point[0] <= x1 + 1e-9 and y0 - 1e-9 <= point[1] <= y1 + 1e-9:
                return True
    return False


def _member_footprint(member) -> list[tuple[float, float]]:
    """A member's plan rectangle: its axis swept by the section face it shows in plan.

    The same construction every emitter builds a member's footprint from, so a landing
    drawn here covers exactly the plan area the 3D deck occupies — which means reading
    the flat-vs-on-edge rule from ``plan_cross_section_m`` rather than assuming either.
    """
    half = plan_cross_section_m(cross_section(member.profile),
                                member.z1_m - member.z0_m) / 2.0
    return rect_between(member.p0, member.p1, -half, half)


#: How far a descending flight's label sits below an ascending one sharing the same well,
#: metres. One line of plan lettering at the scale plan annotation reserves against.
_STAIR_LABEL_PITCH_M = TEXT_PT * model_in_per_pt(PLAN_RESERVATION_SCALE) * M_PER_IN * 1.6

#: Gap between the flight's travel line and the near edge of its label, metres. The line is
#: the heaviest thing drawn on the flight (0.5 mm against the treads' 0.25) and it ran
#: through the middle of the lettering. The label is CENTRED on its anchor, so clearing the
#: line means moving it half its own width plus this — a fixed offset only clears a label
#: of one particular length, and "DN 15 R" and "UP 6 R" are not that length.
_STAIR_LABEL_GAP_M = TEXT_PT * model_in_per_pt(PLAN_RESERVATION_SCALE) * M_PER_IN * 0.5


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
        # Which way the flight goes is a fact about the READER's storey, not about the
        # stair. A stair is authored departing ``storey`` and arriving ``to_storey``, and it
        # is drawn on both plans — so on the plan it arrives at, it descends. Both flights
        # through catlin's stair hall read "UP" until now: "UP 16 R" for the flight to the
        # second floor, and "UP 15 R" for the one down to the basement, printed on top of
        # each other in the middle of the same well.
        going_up = stair.storey == storey
        label = f"{'UP' if going_up else 'DN'} {stair.riser_count} R"
        # Placed on two axes, for two different reasons. ALONG the run, the descending
        # flight steps clear of the ascending one — two flights sharing a well share a bbox
        # centre, which is how "UP 16 R" and "UP 15 R" came to be printed on top of each
        # other. ACROSS it, both step off the travel line, which is the heaviest thing on
        # the flight and otherwise runs straight through the lettering.
        anchor = [(minx + maxx) / 2, (miny + maxy) / 2]
        run_axis = 0 if along_x else 1
        anchor[run_axis] -= _STAIR_LABEL_PITCH_M * (0 if going_up else 1)
        half_label = (len(label) * TEXT_PT * CHAR_ASPECT
                      * model_in_per_pt(PLAN_RESERVATION_SCALE) * M_PER_IN / 2.0)
        anchor[1 - run_axis] += half_label + _STAIR_LABEL_GAP_M
        b.add(Text(anchor=_in((anchor[0], anchor[1])), content=label,
                   height_pt=TEXT_PT, layer="A-STAIR", align="center"))


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


#: Candidate caption offsets around an alarm glyph, in glyph-radii, first that clears wins.
#: Right first because that is where a reader looks for a symbol's label; below-right last
#: because it is the direction a room block already occupies.
_ALARM_LABEL_SIDES = ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0))

#: How far off the glyph a caption sits, metres. The glyph is drawn by the writer at a fixed
#: printed size, so this is the model-space room that size takes at the scale plan annotation
#: reserves against — the same convention every other label on this sheet uses.
_ALARM_LABEL_GAP_M = 0.14


#: Half-width of the reserved box around an alarm glyph, metres. The symbol draws at a
#: fixed printed size, so this is the room it takes on the sheet at the scale plan
#: annotation reserves against — enough that a label block placed clear of it does not sit
#: on its shoulder either.
_ALARM_GLYPH_HALF_M = 0.11


def _alarm_positions(model: ResolvedModel, storey: str) -> list[tuple[float, float]]:
    """Where each alarm symbol will be drawn on ``storey`` — the same rule ``_emit_alarms`` uses.

    Read before the room blocks are placed and again when the symbols are drawn. The two
    must agree, which is why the seed-or-authored-position rule lives here once instead of
    being spelled out at both call sites.
    """
    rooms = {element.tag: element for element in model.plan.storey_elements(storey)
             if element.element_kind == "Room"}
    out: list[tuple[float, float]] = []
    for alarm in (element for element in model.plan.storey_elements(storey)
                  if element.element_kind == "Alarm"):
        room = rooms.get(alarm.room)
        if room is None:
            continue
        out.append(alarm.position.xy_m if alarm.position is not None else room.seed.xy_m)
    return out


def _alarm_glyph_boxes(model: ResolvedModel,
                       storey: str) -> list[tuple[float, float, float, float]]:
    """The boxes the alarm SYMBOLS will occupy, for the room block to place itself around.

    The caption dodges the block and the block dodges the glyph, which is not circular: a
    glyph cannot move at all, a block can move anywhere inside its room, and a caption can
    only pick a side. Ordering them by how much freedom each has is what stopped ``BED``
    and ``231 SF`` printing above and below a symbol sitting between them.
    """
    return [(x - _ALARM_GLYPH_HALF_M, y - _ALARM_GLYPH_HALF_M,
             x + _ALARM_GLYPH_HALF_M, y + _ALARM_GLYPH_HALF_M)
            for x, y in _alarm_positions(model, storey)]


def _emit_alarms(b: SceneBuilder, model: ResolvedModel, storey: str,
                 avoid: list[tuple[float, float, float, float]] = ()) -> None:
    """Place code-life-safety symbols at their hosted room seed points.

    ``avoid`` is the room label blocks' boxes (``plan_labels.emit_room_blocks`` returns
    them). A room's seed and its label block are both derived from the room, so on a small
    room they land on each other: ``SD/CO`` printed straight through ``CLOSET / 48 SF`` and
    through ``PLAY N``'s ceiling line. The SYMBOL stays where it is — its position is a
    statement about where the alarm goes — and only the caption steps aside.
    """
    rooms = {element.tag: element for element in model.plan.storey_elements(storey)
             if element.element_kind == "Room"}
    for alarm in (element for element in model.plan.storey_elements(storey)
                  if element.element_kind == "Alarm"):
        room = rooms.get(alarm.room)
        if room is None:
            continue
        # Every AlarmKind must appear here — this is a hard index, so a new member without a
        # label KeyErrors the whole plan sheet rather than drawing an unlabelled symbol.
        label = {"smoke": "SD", "co": "CO", "combo": "SD/CO", "heat": "HD",
                 "leak": "WD", "freeze": "FD"}[alarm.kind.value]
        # The room stays the host (it is what the check rules reconcile against); the seed is
        # only the default *drawing* point, so an alarm that names its own position draws
        # there — e.g. a hall lobe of a big open room rather than that room's centroid.
        at = alarm.position.xy_m if alarm.position is not None else room.seed.xy_m
        b.add(Symbol(name="alarm", insert=_in(at), layer="A-ANNO-SYMB"))
        b.add(Text(anchor=_in(_alarm_label_anchor(at, label, avoid)),
                   content=label, height_pt=DIM_TEXT_PT, layer="A-ANNO-TEXT"))


def _alarm_label_anchor(at: tuple[float, float], label: str,
                        avoid: list[tuple[float, float, float, float]]
                        ) -> tuple[float, float]:
    """The first side of the glyph whose caption clears every room block, else the right."""
    half_w = (len(label) * DIM_TEXT_PT * CHAR_ASPECT
              * model_in_per_pt(PLAN_RESERVATION_SCALE) * M_PER_IN / 2.0)
    half_h = _ALARM_LABEL_GAP_M / 2.0
    for dx, dy in _ALARM_LABEL_SIDES:
        cx = at[0] + dx * (_ALARM_LABEL_GAP_M + half_w)
        cy = at[1] + dy * (_ALARM_LABEL_GAP_M + half_h)
        if not any(cx + half_w > minx and cx - half_w < maxx
                   and cy + half_h > miny and cy - half_h < maxy
                   for minx, miny, maxx, maxy in avoid):
            return (cx - half_w, cy - half_h)
    return (at[0] + _ALARM_LABEL_GAP_M, at[1] + _ALARM_LABEL_GAP_M)


def _angle(sx: float, sy: float, ex: float, ey: float) -> float:
    import math

    return math.degrees(math.atan2(ey - sy, ex - sx))
