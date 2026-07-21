"""Floorplan slice → drawing IR (→ 20 §Drawing IR, → 11b §Slices).

Every 2D view is a ``Slice``; a floorplan is the auto-scaffolded plan slice cut 4' above a
storey floor. This builder projects the *resolved* geometry — per-layer wall polygons, real
framing member sections, insulation hatch, openings, room labels — into the pure-data 2D IR.
It never redraws from scalar specs (the old failure mode) and never re-measures: all numbers
come from the ``ResolvedModel`` (→ 20 "the UI never re-measures" rule, applied engine-side).
"""

from __future__ import annotations

from typehaus.emit.draw._shared import (
    M_TO_IN,
    emit_bbox_dimension_chain,
    emit_fixtures,
    emit_wall,
    to_in as _in,
)
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Symbol, Text
from typehaus.resolve.model import ResolvedModel


def build_floorplan(model: ResolvedModel, storey: str) -> Scene:
    """Build the plan-slice IR scene for one storey tag."""
    b = SceneBuilder(name=f"plan-{storey}", units="in")
    walls = [w for w in model.walls if w.storey == storey]

    for wall in walls:
        emit_wall(b, wall)
    _emit_openings(b, model, {w.tag for w in walls})
    _emit_stairs(b, model, storey)
    _emit_rooms(b, model, storey)
    _emit_floor_heat(b, model, storey)
    _emit_alarms(b, model, storey)
    emit_fixtures(b, model, storey)
    emit_bbox_dimension_chain(b, walls)
    return b.build()


def _door_operation(model: ResolvedModel, type_ref: str | None) -> str:
    if type_ref is None:
        return "swing"
    door_type = next((t for t in model.plan.library.door_types if t.tag == type_ref), None)
    return door_type.operation if door_type is not None else "swing"


def _emit_openings(b: SceneBuilder, model: ResolvedModel, wall_tags: set[str]) -> None:
    for op in model.openings:
        if op.host_wall not in wall_tags:
            continue
        wall = model.wall(op.host_wall)
        if wall is None:
            continue
        (sx, sy), (ex, ey) = wall.axis
        length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5 or 1.0
        t = op.center_along_m / length
        cx, cy = sx + (ex - sx) * t, sy + (ey - sy) * t
        layer = "A-DOOR" if op.is_door else "A-GLAZ"
        authored = model.plan.by_tag(op.tag)
        flip_hinge = bool(getattr(authored, "flip_hinge", False))
        flip_swing = bool(getattr(authored, "flip_swing", False))
        angle = _angle(sx, sy, ex, ey)
        is_double = op.is_door and _door_operation(model, op.type_ref) == "double_swing"
        if is_double:
            # Two leaves hinged at the jambs, meeting at a centre mullion — the insert
            # point is the opening centre rather than a single hinge.
            b.add(Symbol(
                name="door-swing-double",
                insert=_in((cx, cy)),
                rotation=angle,
                scale=op.width_m * M_TO_IN,
                layer=layer,
                params={"width_in": op.width_m * M_TO_IN,
                        "swing_sign": -1 if flip_swing else 1},
            ))
            continue
        # The symbol is anchored at the hinge, not the opening centre.  This makes the
        # rendered leaf and arc describe the authored handing instead of a generic glyph.
        hinge_direction = -1.0 if flip_hinge else 1.0
        hinge_x = cx + hinge_direction * (ex - sx) / length * op.width_m / 2
        hinge_y = cy + hinge_direction * (ey - sy) / length * op.width_m / 2
        b.add(Symbol(
            name="door-swing" if op.is_door else "window-mark",
            insert=_in((hinge_x, hinge_y) if op.is_door else (cx, cy)),
            rotation=angle,
            scale=op.width_m * M_TO_IN,
            layer=layer,
            params={"width_in": op.width_m * M_TO_IN,
                    "swing_sign": -1 if flip_swing else 1},
        ))
        if not op.is_door:
            # Keep labels clear of the glazed opening while retaining the wall orientation.
            normal_x, normal_y = -(ey - sy) / length, (ex - sx) / length
            b.add(Text(anchor=_in((cx + normal_x * 0.18, cy + normal_y * 0.18)),
                       content=op.tag, height=2.2, layer="A-GLAZ", align="center"))


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
            if member.category not in {"tread", "winder", "landing"}:
                continue
            b.add(Polyline(points=(_in(member.p0), _in(member.p1)), layer="A-STAIR",
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


def _emit_alarms(b: SceneBuilder, model: ResolvedModel, storey: str) -> None:
    """Place code-life-safety symbols at their hosted room seed points."""
    rooms = {element.tag: element for element in model.plan.storey_elements(storey)
             if element.element_kind == "Room"}
    for alarm in (element for element in model.plan.storey_elements(storey)
                  if element.element_kind == "Alarm"):
        room = rooms.get(alarm.room)
        if room is None:
            continue
        label = {"smoke": "SD", "co": "CO", "combo": "SD/CO"}[alarm.kind.value]
        b.add(Symbol(name="alarm", insert=_in(room.seed.xy_m), layer="A-ANNO-SYMB"))
        b.add(Text(anchor=_in((room.seed.xy_m[0] + 0.08, room.seed.xy_m[1] + 0.08)),
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
