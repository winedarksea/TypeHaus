"""Where each alarm head goes — plan point from ``resolve.alarms.alarm_xy``; z on the ceiling,
or on the finished floor for a leak sensor."""

from __future__ import annotations

from typing import Any

from typehaus.model.enums import AlarmKind
from typehaus.model.refs import FollowRoof
from typehaus.resolve.alarms import alarm_xy
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.roof_geometry import roof_height_at, roof_underside_depth_m
from typehaus.resolve.room_floor import room_finished_floor_elevation


def alarm_points(model: ResolvedModel, alarm: Any, storey_tag: str) -> dict[str, Any]:
    """``x``/``y``/``z``/``mount`` of one alarm; a point is ``None`` when underivable."""
    on_floor = alarm.kind is AlarmKind.LEAK
    mount = "floor" if on_floor else "ceiling"
    room_el = model.plan.by_tag(alarm.room) if alarm.room else None
    xy = alarm_xy(alarm, room_el)
    if xy is None:
        return {"x": None, "y": None, "z": None, "mount": mount}
    z = (_floor_z(model, alarm.room, storey_tag) if on_floor
         else _ceiling_z(model, room_el, alarm.room, storey_tag, xy))
    return {"x": xy[0], "y": xy[1], "z": z, "mount": mount}


def _resolved_room(model: ResolvedModel, room_tag: str | None, storey_tag: str) -> Any | None:
    return next((r for r in model.rooms if r.tag == room_tag and r.storey == storey_tag), None)


def _floor_z(model: ResolvedModel, room_tag: str | None, storey_tag: str) -> float | None:
    room = _resolved_room(model, room_tag, storey_tag)
    return None if room is None else room_finished_floor_elevation(model, room)


def _ceiling_z(model: ResolvedModel, room_el: Any, room_tag: str | None, storey_tag: str,
               xy: tuple[float, float]) -> float | None:
    if room_tag is None:
        return None
    if room_el is not None and isinstance(room_el.ceiling, FollowRoof):
        roof = next((r for r in model.roofs if r.tag == room_el.ceiling.roof_ref), None)
        depth = None if roof is None else roof_underside_depth_m(model, roof, room_tag)
        if depth is not None:
            return roof_height_at(roof, xy) - depth
    room = _resolved_room(model, room_tag, storey_tag)
    if room is None:
        return None
    if room.clear_height_m is not None:
        return room_finished_floor_elevation(model, room) + room.clear_height_m
    # No deck overhead (a trussed roof): the room's flat ceiling board's underside.
    ceiling = next((c for c in model.ceilings
                    if c.room_ref == room_tag and c.storey == storey_tag), None)
    return None if ceiling is None else ceiling.z0_m
