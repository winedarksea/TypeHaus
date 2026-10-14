"""Resolve finite clear volumes against the same finished floor as placeable mounts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from shapely.geometry import Polygon

from typehaus.findings import Finding, element_error
from typehaus.model.clear_zones import ClearZone
from typehaus.resolve.room_floor import room_finished_floor_elevation

if TYPE_CHECKING:
    from typehaus.resolve.model import ResolvedModel

FLOOR_PLANE_TOLERANCE_M = 1e-6


@dataclass(frozen=True)
class ResolvedClearZone:
    uid: str
    tag: str
    storey: str
    outline: tuple[tuple[float, float], ...]
    z0_m: float
    z1_m: float
    purpose: str
    policy: Literal["required", "recommended"]
    except_tags: tuple[str, ...] = ()


def resolve_clear_zones(model: ResolvedModel) -> list[Finding]:
    findings = []
    for storey in model.plan.storeys:
        for element in model.plan.elements.get(storey.tag, ()):
            if not isinstance(element, ClearZone):
                continue
            outline = tuple(point.xy_m for point in element.outline)
            polygon = Polygon(outline)
            if not polygon.is_valid or polygon.area <= 0:
                findings.append(element_error("resolve.clear_zone",
                    "clear zone requires a valid, nonempty outline", element.tag))
                continue
            floors = [room_finished_floor_elevation(model, room) for room in model.rooms
                      if room.storey == storey.tag and len(room.clear_face) >= 3
                      and Polygon(room.clear_face).intersection(polygon).area > 0]
            if floors and max(floors) - min(floors) > FLOOR_PLANE_TOLERANCE_M:
                findings.append(element_error("resolve.clear_zone",
                    "clear zone spans different finished floor elevations; split the zone",
                    element.tag))
                continue
            # Without modeled rooms, the authored storey datum is the only floor plane.
            floor = floors[0] if floors else storey.elevation.meters
            model.clear_zones.append(ResolvedClearZone(
                uid=element.uid, tag=element.tag, storey=storey.tag, outline=outline,
                z0_m=floor + element.bottom.meters, z1_m=floor + element.top.meters,
                purpose=element.purpose, policy=element.policy, except_tags=element.except_tags))
    return findings
