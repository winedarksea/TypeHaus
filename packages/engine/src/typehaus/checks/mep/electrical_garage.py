"""CODE-tier electrical rule — NEC 210.52(G)(1), a receptacle in each garage vehicle bay.

2023 NEC 210.52(G)(1) (Minnesota's electrical code; IRC 2021 E3901.9 is the same rule): in
each attached garage, and each detached garage with power, at least one receptacle outlet
in each vehicle bay, not more than 5 1/2 ft above the floor.

The code does not define a bay, so it is derived from the overhead doors: a door counts
``floor(width / 8 ft)`` bays (at least one; 8 ft is the narrowest single-car door, so a 9-12
ft door is one bay and a 16 ft door two), and the room is split into that many equal strips
along the door wall. A receptacle serves the strip its plan point projects into.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import by_result
from typehaus.checks.mep.electrical_code import _room_of
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import Occupancy
from typehaus.resolve.placeables import placed_xy
from typehaus.resolve.room_lookup import axis_polygon, axis_ring

_CID, _CODE = "code.NEC_210_52_G_garage_receptacles", "NEC 210.52(G)(1)"
_SINGLE_BAY_DOOR_M = 8 * 0.3048
_MAX_COUNTING_HEIGHT_M = 5.5 * 0.3048
_DOOR_TO_ROOM_M = 0.5  # a door's centre sits in its host wall, just outside the clear face


@check(Tier.CODE, _CID)
def garage_bay_receptacles(ctx: CheckContext) -> list[Finding]:
    """Each vehicle bay of each powered garage has a counting receptacle."""
    from shapely.geometry import Point

    from typehaus.checks.mep.electrical import _counts_as_a_125v_receptacle

    garages = [room for room in ctx.model.rooms
               if room.occupancy == Occupancy.GARAGE.value and len(axis_ring(room)) >= 3]
    if not garages:
        return [by_result(_CID, Result.NOT_APPLICABLE, "no garage room in the plan", (),
                          _CODE)]
    door_types = {t.tag: t for t in ctx.plan.library.door_types}
    walls = {wall.tag: wall for wall in ctx.model.walls}
    by_tag = {room.tag: room for room in ctx.model.rooms}
    storey_rooms: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(axis_ring(room)) >= 3:
            storey_rooms.setdefault(room.storey, []).append((room, axis_polygon(room)))

    out: list[Finding] = []
    for garage in garages:
        poly = axis_polygon(garage)
        doors = []
        for opening in ctx.model.openings:
            door_type = door_types.get(opening.type_ref or "")
            wall = walls.get(opening.host_wall)
            if (door_type is None or wall is None or wall.storey != garage.storey
                    or getattr(door_type.operation, "value", door_type.operation) != "overhead"):
                continue
            (x0, y0), (x1, y1) = wall.axis
            length = math.hypot(x1 - x0, y1 - y0)
            u = ((x1 - x0) / length, (y1 - y0) / length)
            centre = Point(x0 + u[0] * opening.center_along_m, y0 + u[1] * opening.center_along_m)
            if poly.distance(centre) <= _DOOR_TO_ROOM_M:
                doors.append((opening, u))
        if not doors:
            out.append(by_result(_CID, Result.UNKNOWN,
                                 f"{garage.tag} has no overhead door, so its vehicle bays "
                                 "cannot be counted", (garage.tag,), _CODE))
            continue
        axes = {(round(abs(u[0]), 3), round(abs(u[1]), 3)) for _, u in doors}
        if len(axes) > 1:
            out.append(by_result(_CID, Result.UNKNOWN,
                                 f"{garage.tag} has overhead doors on crossing walls; bays "
                                 "are not derived for that layout", (garage.tag,), _CODE))
            continue
        u = doors[0][1]
        bays = sum(max(1, int(opening.width_m // _SINGLE_BAY_DOOR_M)) for opening, _ in doors)
        along = [x * u[0] + y * u[1] for x, y in axis_ring(garage)]
        lo, hi = min(along), max(along)
        served: dict[int, list[str]] = {}
        for element in ctx.plan.storey_elements(garage.storey):
            if (element.element_kind != "ElectricalDevice"
                    or not _counts_as_a_125v_receptacle(ctx, element)):
                continue
            xy = placed_xy(ctx.model, element)
            if xy is None:
                continue
            room = _room_of(element, Point(xy), storey_rooms.get(garage.storey, ()), by_tag)
            mount = element.mount
            height = mount.elevation.meters if mount.elevation is not None else 0.0
            if (room is None or room.tag != garage.tag or height > _MAX_COUNTING_HEIGHT_M
                    or getattr(mount.kind, "value", mount.kind) == "ceiling"):
                continue
            s = xy[0] * u[0] + xy[1] * u[1]
            bay = min(bays - 1, max(0, int((s - lo) / (hi - lo) * bays)))
            served.setdefault(bay, []).append(element.tag)
        for bay in range(bays):
            tags = served.get(bay)
            label = f"{garage.tag} bay {bay + 1} of {bays}"
            if tags:
                out.append(by_result(_CID, Result.PASS,
                                     f"{label}: {', '.join(sorted(tags))}", (), _CODE))
            else:
                out.append(by_result(_CID, Result.FAIL,
                                     f"{label} has no receptacle at or below 5 1/2 ft",
                                     (garage.tag,), _CODE,
                                     "add a 125 V receptacle in that bay, <= 5'-6\" AFF"))
    return out
