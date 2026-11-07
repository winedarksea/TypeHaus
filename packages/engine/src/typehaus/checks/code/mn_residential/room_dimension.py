"""R304.2: a habitable room is not less than 7'-0" in any horizontal dimension.

IRC 2018 R304.2, unamended by Minn. R. 1309: "Habitable rooms shall be not less than 7 feet
in any horizontal dimension. Exception: Kitchens." Read here as R305.1 Exception 1 reads its
heights: against the REQUIRED floor area. R304.1's 70 sf (or the whole room, where it is
smaller) must be floor that is 7'-0" across in every direction — floor covered by a 7'x7'
square or a 7'-0" disk lying wholly on the room's walkable floor at 5'-0" of head (R304.3).
A nook or closet bay narrower than 7' does not disqualify the room; it just does not count,
and a 3'-wide ribbon of floor holds neither.

Squares are tried square to every edge direction of the floor (mod 90°), so an angled bay
neither tilts the rectilinear part nor goes unmeasured. The disk is what lets a round or
octagonal room count: one 10' across holds no 7' square at its rim but is 7' every way.
"""

from __future__ import annotations

import math
from itertools import pairwise
from typing import Any

from shapely.geometry import MultiPoint, Polygon

from typehaus.checks.code.mn_residential._common import (
    HABITABLE_OCCUPANCIES,
    SF_PER_M2,
    _fail,
    _pass,
    _room_storey,
    _unknown,
)
from typehaus.checks.code.mn_residential.room_area import countable_floor
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import Occupancy
from typehaus.quantities import ft
from typehaus.resolve.overlay import difference, intersection, union_all

_CID = "code.R304_2_min_dimension"
_MIN_HABITABLE_AREA_M2 = 70.0 / SF_PER_M2
#: Half of 7'-0", less 0.5 mm so a room drawn at exactly 7'-0" is not lost to noise.
_HALF_SIDE_M = ft(3.5).meters - 0.0005
_AREA_TOL_M2 = 0.5 / SF_PER_M2
#: Edge directions closer than this (mod 90°) share one square frame.
_ANGLE_TOL_RAD = math.radians(0.1)


@check(Tier.CODE, _CID)
def habitable_min_dimension(ctx: CheckContext) -> list[Finding]:
    """R304.2: R304.1's required floor area is 7'-0" across in every horizontal direction."""
    out: list[Finding] = []
    resolved = {room.tag: room for room in ctx.model.rooms}
    for room in ctx.plan.all_elements():
        if room.element_kind != "Room" or room.occupancy not in HABITABLE_OCCUPANCIES \
                or room.occupancy is Occupancy.KITCHEN:
            continue
        resolved_room = resolved.get(room.tag)
        storey = _room_storey(ctx, room.tag)
        if resolved_room is None or storey is None or len(resolved_room.clear_face) < 3:
            out.append(_unknown(_CID, "room does not resolve a floor to measure",
                                (room.tag,), "R304.2"))
            continue
        floor = countable_floor(ctx, resolved_room, storey)
        required = min(floor.area, _MIN_HABITABLE_AREA_M2)
        wide = seven_foot_floor(floor)
        detail = (f"{room.tag} has {wide.area * SF_PER_M2:.0f} sf of floor in a 7'-0\" square "
                  f"or disk, of {floor.area * SF_PER_M2:.0f} sf at 5'-0\"; R304.2 read "
                  f"against R304.1's required {required * SF_PER_M2:.0f} sf")
        if floor.area <= 1e-9 or wide.area + _AREA_TOL_M2 < required:
            out.append(_fail(_CID, f"{detail} — habitable rooms are not less than 7'-0\" in "
                             "any horizontal dimension", (room.tag,), "R304.2"))
        else:
            out.append(_pass(_CID, detail, "R304.2"))
    return out


def seven_foot_floor(floor: Any, half_side_m: float = _HALF_SIDE_M) -> Any:
    """Floor covered by a ``2 * half_side_m`` square (any edge's frame) or disk inside it.

    Morphological openings, the squares' done exactly: eroding removes the boundary swept by
    the square, dilating adds the eroded region's boundary swept by it.
    """
    if floor.is_empty or floor.area <= 1e-9:
        return Polygon()
    pieces = [_square_opening(floor, half_side_m, angle) for angle in _edge_angles(floor)]
    disk = floor.buffer(-half_side_m)
    if not disk.is_empty:
        pieces.append(disk.buffer(half_side_m))
    pieces = [piece for piece in pieces if not piece.is_empty]
    return intersection(union_all(pieces), floor) if pieces else Polygon()


def _square_opening(floor: Any, half_side_m: float, angle: float) -> Any:
    cos, sin = math.cos(angle), math.sin(angle)
    square = [(sx * half_side_m * cos - sy * half_side_m * sin,
               sx * half_side_m * sin + sy * half_side_m * cos)
              for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]

    def swept(geom: Any) -> Any:
        return union_all([MultiPoint([(px + dx, py + dy) for px, py in (a, b)
                                      for dx, dy in square]).convex_hull
                          for ring in _rings(geom) for a, b in pairwise(ring)])

    eroded = difference(floor, swept(floor))
    if eroded.is_empty or eroded.area <= 1e-12:
        return Polygon()
    return union_all([eroded, swept(eroded)])


def _rings(geom: Any) -> list[list[tuple[float, float]]]:
    out = []
    for part in getattr(geom, "geoms", (geom,)):
        if isinstance(part, Polygon) and not part.is_empty:
            out.append(list(part.exterior.coords))
            out.extend(list(hole.coords) for hole in part.interiors)
    return out


def _edge_angles(floor: Any) -> list[float]:
    """Each distinct edge direction of ``floor``, mod 90°."""
    angles: list[float] = []
    for ring in _rings(floor):
        for (ax, ay), (bx, by) in pairwise(ring):
            if math.hypot(bx - ax, by - ay) <= 1e-6:
                continue
            angle = math.atan2(by - ay, bx - ax) % (math.pi / 2)
            if not any(min(abs(angle - seen), math.pi / 2 - abs(angle - seen))
                       < _ANGLE_TOL_RAD for seen in angles):
                angles.append(angle)
    return angles
