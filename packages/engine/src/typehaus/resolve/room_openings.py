"""Which windows belong to which room, and how much glass and openable sash that is.

This lives in ``resolve`` because it answers a question about the *building* — "what can
this room see out of" — and because two different layers need the answer. A check needs it
to grade R303.1; the server needs it to put a glazing table in front of a reader without
scraping numbers back out of a check message. Checks import resolve and never the reverse,
so the moment a second consumer appeared this had to come down out of ``checks/``.

It used to be ``checks/code/mn_residential/_common.py::_room_windows``, and that module
still re-exports it under the old name so the callers there read unchanged.
"""

from __future__ import annotations

from typing import Any

from typehaus.quantities import inch
from typehaus.resolve.geometry import opening_center

#: How far past a room's clear face a bounding wall's axis may lie. Generous enough to reach
#: an exterior wall's centreline through lining and junction resolution, tight enough not to
#: claim a window in the room on the far side of an interior partition.
_BOUNDARY_BAND_M = inch(12).meters

#: How far to either side of a wall axis to probe for modeled space. Past the wall's own half
#: thickness by enough to clear lining and junction resolution, and no further.
_WALL_SIDE_PROBE_M = 0.15


def rooms_by_storey(model: Any) -> dict[str, list]:
    """``{storey: [(room, polygon)]}`` — built once and passed down, never per opening."""
    from shapely.geometry import Polygon

    out: dict[str, list] = {}
    for room in model.rooms:
        if len(room.clear_face) >= 3:
            out.setdefault(room.storey, []).append((room, Polygon(room.clear_face)))
    return out


def wall_is_exterior(model: Any, wall, index: dict[str, list] | None = None) -> bool:
    """Does this wall have modeled space on one side only?

    Derived, never named: there is no ``Assembly.exterior`` flag, and a tag-prefix list is
    the exact mistake the energy check had to unwind — one house's naming convention
    compiled into the engine. A wall with a room on both sides is a partition; a wall with a
    room on one side is the envelope. Foundation walls count as exterior outright: what is
    on the other side of them is earth.
    """
    from shapely.geometry import Point

    if wall.is_foundation:
        return True
    rooms = (index if index is not None else rooms_by_storey(model)).get(wall.storey, ())
    if not rooms:
        return False
    (sx, sy), (ex, ey) = wall.axis
    run = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if run <= 1e-9:
        return False
    nx, ny = -(ey - sy) / run, (ex - sx) / run  # unit normal
    reach = wall.thickness_m / 2.0 + _WALL_SIDE_PROBE_M
    sides = [False, False]
    for t in (0.25, 0.5, 0.75):
        mx, my = sx + (ex - sx) * t, sy + (ey - sy) * t
        for position, sign in enumerate((1.0, -1.0)):
            probe = Point(mx + nx * reach * sign, my + ny * reach * sign)
            if any(poly.covers(probe) for _room, poly in rooms):
                sides[position] = True
    return sides[0] != sides[1]


def room_windows(model: Any, room, *, exterior_only: bool = False) -> list:
    """Windows on this room's bounding wall, not every window in the building.

    ``exterior_only`` decides whether an *interior* window counts, and the two callers
    genuinely want different answers — which is why it is a flag rather than a behaviour
    change.

    **R310 passes it True, and that is a safety fix, not a refinement.** The band below
    selects on proximity to the room boundary and nothing else, so before this flag existed
    an interior transom or a borrowed-light sash of adequate size was credited to a sleeping
    room as its *emergency escape opening*. R310.1's subject is an opening "opening directly
    into a public way, yard or court"; a window into the next room reaches none of those, and
    a false pass there is the one class of false pass this engine cannot afford.

    **R303.1 leaves it False, deliberately.** Borrowed light through an interior opening is
    not what R303.1's 8% is measured on either, but that rule already adjudicates its own
    Exception 1 and reports the shortfall in the finding text, so the conservative default
    there is to keep counting what the room can see and let the exception do the arguing. The
    day this house authors real borrowed-light glazing, that choice is worth revisiting on
    its own evidence — it is recorded here rather than left to be rediscovered.

    ``room`` may be a ``ResolvedRoom`` or anything else carrying ``clear_face`` and
    ``storey``: ``resolve_rooms`` calls this while building the very dataclass the checks
    later hand back, so it cannot require the finished object.
    """
    from shapely.geometry import Point, Polygon

    if room is None or not getattr(room, "clear_face", None):
        return []
    face = Polygon(room.clear_face)
    boundary_band = face.boundary.buffer(_BOUNDARY_BAND_M)
    # Built once per call, not once per opening: `wall_is_exterior` rebuilds every room
    # polygon in the house when it is handed no index, and this loop asks it 80 times.
    index = rooms_by_storey(model) if exterior_only else None
    windows = []
    for opening in model.openings:
        if opening.is_door or opening.type_ref is None:
            continue
        wall = model.wall(opening.host_wall)
        if wall is None or wall.storey != room.storey:
            continue
        if exterior_only and not wall_is_exterior(model, wall, index):
            continue
        point = opening_center(wall, opening)
        if point is None:
            continue
        if boundary_band.covers(Point(*point)):
            windows.append(opening)
    return windows


def room_glazing_areas(plan: Any, model: Any, room) -> tuple[float, float] | None:
    """``(glazed_m2, operable_glazed_m2)`` for a room, or ``None`` if a type won't resolve.

    **Two areas, not a ratio, and neither is an R303.1 number.** R303.1 states two
    independent tests — 8% of the floor in glazing and 4% of it openable, with an operable
    unit credited at half its area — and both have to stay expressible from what is stored.
    A single "glazing fraction" would collapse them, and applying the halving here would bake
    a code rule into the geometry. So this reports what the *building* has: the total glass,
    and how much of that glass is in an operable unit. The halving belongs to the check.

    ``None`` rather than zero when a window's type does not resolve. A room whose glazing
    cannot be totalled is not a room with no glazing, and the caller reports UNKNOWN — the
    distinction R303.1's own check already drew and which a 0.0 here would erase.
    """
    types = {item.tag: item for item in plan.library.window_types}
    glazed = 0.0
    operable = 0.0
    for opening in room_windows(model, room):
        window_type = types.get(opening.type_ref)
        if window_type is None:
            return None
        operation = getattr(window_type, "operation", None)
        if operation is None:
            return None
        area = opening.width_m * opening.height_m
        glazed += area
        if getattr(operation, "value", operation) != "fixed":
            operable += area
    return glazed, operable
