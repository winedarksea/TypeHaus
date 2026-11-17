"""Each alarm head's point and body — one record the viewer, the GLB and the IFC all read.

The plan point is ``resolve.alarms.alarm_xy``; z is the ceiling, or the finished floor for a
leak sensor. The body is the head's ``ElectricalDeviceType`` (a cylinder when its
``model_representation.primitive`` says so, else its footprint box), else a generic disc.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from typing import Any

from typehaus.findings import Finding, Result, Severity, advisory
from typehaus.model.enums import AlarmKind
from typehaus.model.refs import FollowRoof
from typehaus.resolve.alarms import alarm_xy
from typehaus.resolve.geometry_ir import GPart, GPrism, PartCatalogRef
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.roof_geometry import roof_height_at, roof_underside_depth_m
from typehaus.resolve.room_floor import room_finished_floor_elevation

GENERIC_DIAMETER_M = 0.127  # ~5"
GENERIC_HEIGHT_M = 0.038  # ~1.5"
_FACETS = 24


@dataclass(frozen=True)
class ResolvedAlarmHead:
    uid: str
    tag: str
    storey: str
    kind: str
    type_ref: str | None
    mount: str  # "ceiling" | "floor"
    x: float | None
    y: float | None
    z: float | None  # the mounting face
    body: GPart | None  # None when the point is underivable


def resolve_alarm_heads(model: ResolvedModel) -> list[Finding]:
    """Fill ``model.alarm_heads``; a ``type_ref`` naming no device type is an ERROR."""
    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    findings: list[Finding] = []
    heads: list[ResolvedAlarmHead] = []
    for storey in model.plan.storeys:
        for alarm in model.plan.storey_elements(storey.tag):
            if alarm.element_kind != "Alarm":
                continue
            product_type = types.get(alarm.type_ref) if alarm.type_ref else None
            if alarm.type_ref and product_type is None:
                findings.append(advisory(
                    "integrity.unknown_placeable_type",
                    f"alarm {alarm.tag} references missing type {alarm.type_ref!r}",
                    (alarm.tag,), Result.FAIL, severity=Severity.ERROR))
            heads.append(_head(model, alarm, storey.tag, product_type))
    model.alarm_heads = heads
    return findings


def _head(model: ResolvedModel, alarm: Any, storey_tag: str,
          product_type: Any | None) -> ResolvedAlarmHead:
    on_floor = alarm.kind is AlarmKind.LEAK
    mount = "floor" if on_floor else "ceiling"
    room_el = model.plan.by_tag(alarm.room) if alarm.room else None
    xy = alarm_xy(alarm, room_el)
    z = None
    if xy is not None:
        z = (_floor_z(model, alarm.room, storey_tag) if on_floor
             else _ceiling_z(model, room_el, alarm.room, storey_tag, xy))
    body = None if xy is None or z is None else _body(alarm, product_type, xy, z, on_floor)
    return ResolvedAlarmHead(
        uid=alarm.uid, tag=alarm.tag, storey=storey_tag, kind=alarm.kind.value,
        type_ref=alarm.type_ref if product_type is not None else None, mount=mount,
        x=None if xy is None else xy[0], y=None if xy is None else xy[1], z=z, body=body)


def _body(alarm: Any, product_type: Any | None, xy: tuple[float, float], z: float,
          on_floor: bool) -> GPart:
    x, y = xy
    if product_type is None:
        width = depth = GENERIC_DIAMETER_M
        height, round_ = GENERIC_HEIGHT_M, True
    else:
        width, depth = (d.meters for d in product_type.footprint)
        height = product_type.height.meters
        rep = product_type.model_representation
        round_ = rep is not None and rep.primitive == "cylinder"
    if round_:
        r = width / 2
        ring = tuple((x + r * cos(2 * pi * i / _FACETS), y + r * sin(2 * pi * i / _FACETS))
                     for i in range(_FACETS))
    else:
        w, d = width / 2, depth / 2
        ring = ((x - w, y - d), (x + w, y - d), (x + w, y + d), (x - w, y + d))
    z0, z1 = (z, z + height) if on_floor else (z - height, z)
    catalog = PartCatalogRef(name=getattr(product_type, "name", None))
    return GPart(key="alarm", material_key="alarm",
                 solids=(GPrism(ring=ring, z0_m=z0, z1_m=z1),), catalog=catalog)


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
