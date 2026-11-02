"""R304.1 habitable floor area, and R305.1 Exception 2's bathroom heights.

Both read the room's WALKABLE floor: its clear face less the storey's floor openings and
their walled pockets. A stair well is not floor, and counting it is how RM-A-STUDY once
showed 14 sf it did not have.
"""

from __future__ import annotations

import math
from typing import Any

from shapely.geometry import JOIN_STYLE, Polygon

from typehaus.checks.code.mn_residential._common import (
    HABITABLE_OCCUPANCIES,
    SF_PER_M2,
    _fail,
    _pass,
    _room_storey,
    _unknown,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import Occupancy
from typehaus.quantities import inch, m
from typehaus.resolve.overlay import difference, union_all
from typehaus.resolve.roof_geometry import (
    roof_headroom_region,
    roof_height_at,
    room_head_limited_area_m2,
)

_CID = "code.R304_1_floor_area"
_MIN_HABITABLE_AREA_M2 = 70.0 / SF_PER_M2
#: R305.1 Exception 2: 6'-8" at each fixture's front-clearance centre, and over 30"x30" at
#: the showerhead.
_MIN_BATH_HEAD_M = inch(80).meters
_SHOWER_HALF_SQUARE_M = inch(15).meters
_SHOWER_SYMBOLS = frozenset({"shower", "shower-neo-angle", "tub-shower"})


def floor_voids(ctx: CheckContext, storey_tag: str) -> list[Polygon]:
    """The storey's floor openings and walled pockets: plan area that is not floor."""
    from typehaus.model.floors import FloorOpening

    voids = [Polygon([point.xy_m for point in element.outline])
             for element in ctx.plan.storey_elements(storey_tag)
             if isinstance(element, FloorOpening) and len(element.outline) >= 3]
    voids += [Polygon(closure.pocket_outline)
              for closure in getattr(ctx.model, "floor_opening_pocket_closures", ())
              if closure.storey == storey_tag and len(closure.pocket_outline) >= 3]
    return [void for void in voids if void.is_valid and void.area > 1e-9]


def walkable_face(ctx: CheckContext, resolved_room: Any, storey_tag: str) -> Polygon:
    face = Polygon(resolved_room.clear_face)
    voids = [void for void in floor_voids(ctx, storey_tag) if void.intersects(face)]
    return difference(face, union_all(voids)) if voids else face


# --- R304.1 ---------------------------------------------------------------------------------

@check(Tier.CODE, _CID)
def habitable_floor_area(ctx: CheckContext) -> list[Finding]:
    """R304.1: a habitable room has at least 70 sf of floor; R304.3: only floor at 5'-0" counts.

    Kitchens are R304.1's own exception. R304.2's 7'-0" minimum dimension is not graded.
    """
    out: list[Finding] = []
    resolved = {room.tag: room for room in ctx.model.rooms}
    for room in ctx.plan.all_elements():
        if room.element_kind != "Room" or room.occupancy not in HABITABLE_OCCUPANCIES \
                or room.occupancy is Occupancy.KITCHEN:
            continue
        resolved_room = resolved.get(room.tag)
        storey = _room_storey(ctx, room.tag)
        countable = getattr(resolved_room, "head_limited_area_m2", None)
        if resolved_room is None or storey is None or countable is None:
            out.append(_unknown(_CID, "room does not resolve a countable floor area",
                                (room.tag,), "R304.1"))
            continue
        face = Polygon(resolved_room.clear_face)
        for void in floor_voids(ctx, storey.tag):
            piece = face.intersection(void)
            for part in getattr(piece, "geoms", (piece,)):
                if isinstance(part, Polygon) and part.area > 1e-9:
                    countable -= room_head_limited_area_m2(
                        ctx.model, list(part.exterior.coords)[:-1], storey.elevation.meters)
        detail = (f"{room.tag} has {countable * SF_PER_M2:.0f} sf of floor at or above "
                  f"5'-0\" (room is {resolved_room.area_m2 * SF_PER_M2:.0f} sf)")
        if countable + 1e-9 < _MIN_HABITABLE_AREA_M2:
            out.append(_fail(_CID, f"{detail}; R304.1 requires 70 sf of a habitable room",
                             (room.tag,), "R304.1"))
        else:
            out.append(_pass(_CID, f"{detail} >= 70 sf", "R304.1"))
    return out


# --- R305.1 Exception 2 ---------------------------------------------------------------------

def bath_exception_2(ctx: CheckContext, room_tag: str, roof: Any, depth_m: float,
                     floor_z_m: float) -> tuple[Result, str]:
    """``(verdict, detail)`` for R305.1 Exception 2 under a sloped ceiling.

    "6 feet 8 inches at the center of the front clearance area for fixtures as shown in
    Figure R307.1", and over a 30" x 30" area at the showerhead. The front clearance is
    the part of a fixture's REQUIRED zone in front of its body, or of its recommended zone
    where it has none (a lavatory's 21" is R307.1's figure, catalogued as a convention); a
    shower passes where a 30" square of its pan stands under 6'-8" of finished head.
    """
    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    fixtures = [item for item in getattr(ctx.model, "canvas_objects", ())
                if item.kind == "Fixture" and item.room == room_tag]
    if not fixtures:
        return Result.UNKNOWN, "no fixtures resolve in the room"
    notes: list[str] = []
    failing: list[str] = []
    for item in fixtures:
        symbol = getattr(types.get(item.type_ref), "plan_symbol", None)
        graded = False
        centre = _front_clearance_centre(item)
        if centre is not None:
            graded = True
            head = roof_height_at(roof, centre) - depth_m - floor_z_m
            notes.append(f"{item.tag} clearance centre {m(head).fmt()}")
            if head + 1e-6 < _MIN_BATH_HEAD_M:
                failing.append(item.tag)
        if symbol in _SHOWER_SYMBOLS:
            graded = True
            pan = Polygon(item.footprint).intersection(
                roof_headroom_region(roof, floor_z_m, _MIN_BATH_HEAD_M + depth_m))
            fits = not pan.buffer(-_SHOWER_HALF_SQUARE_M, join_style=JOIN_STYLE.mitre).is_empty
            notes.append(f"{item.tag} {'fits' if fits else 'has no'} 30\"x30\" at 6'-8\"")
            if not fits:
                failing.append(item.tag)
        if not graded:
            return Result.UNKNOWN, f"{item.tag} has no front clearance zone to measure at"
    detail = "; ".join(notes)
    return (Result.FAIL if failing else Result.PASS), (
        f"{', '.join(failing)} under 6'-8\" — {detail}" if failing else detail)


def _front_clearance_centre(item: Any) -> tuple[float, float] | None:
    """Centroid of the clearance zone in front of the body (local -y; +y is the back)."""
    rings = item.required_clearances or item.recommended_clearances
    if not rings:
        return None
    radians = math.radians(item.rotation_degrees)
    cos, sin = math.cos(radians), math.sin(radians)
    cx, cy = item.position

    def local(ring):
        return [((x - cx) * cos + (y - cy) * sin, -(x - cx) * sin + (y - cy) * cos)
                for x, y in ring]

    body = Polygon(local(item.footprint))
    zone = union_all([Polygon(local(ring)) for ring in rings])
    front_y = body.bounds[1]
    far = max(abs(v) for v in zone.bounds) + 1.0
    front = zone.intersection(Polygon([(-far, -far), (far, -far), (far, front_y),
                                       (-far, front_y)]))
    if front.is_empty or front.area <= 1e-9:
        front = difference(zone, body)
    if front.is_empty:
        return None
    lx, ly = front.centroid.x, front.centroid.y
    return cx + lx * cos - ly * sin, cy + lx * sin + ly * cos
